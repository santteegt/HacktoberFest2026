"""The second brain is an Obsidian vault: links stay inside, cards have topics, tags are nested."""

import json
import os
import re
from datetime import date

import psycopg
import pytest
from psycopg.rows import dict_row

from sloth.board import brain, taxonomy
from sloth.core.db import SCHEMA

URL = os.environ.get("SLOTH_DATABASE_URL", "")
CARD_ID = re.compile(r"\bk[0-9a-f]{4,}\b")


def test_safe_names_and_unique_names():
    assert brain.safe_name('A/B: "C" [x] #1?') == "A B C x 1"
    names = brain.Names()
    assert names.claim("Agent memory") == "Agent memory"
    assert names.claim("Agent memory", "AI engineering") == "Agent memory (AI engineering)"
    assert names.claim("Agent memory") == "Agent memory (2)"
    assert names.claim("index") == "index (2)"


def test_taxonomy_pure_parts():
    assert [taxonomy.subtopic_count(n) for n in (3, 10, 40, 318, 1000)] == [1, 2, 3, 8, 8]
    subs = [{"slug": "memory", "name": "Agent memory", "keywords": ["memory", "recall"]},
            {"slug": "wallets", "name": "Agent wallets", "keywords": ["wallet", "payments"]}]
    assert taxonomy.keyword_assign("A wallet for agent payments", subs) == "wallets"
    assert taxonomy.keyword_assign("nothing shared", subs) == "memory"
    tax = {"verticals": {"ai-agents": {"subtopics": subs}}, "links": {"1": "memory", "2": "wallets", "3": "wallets"}}
    assert taxonomy.card_subtopic({"vertical": "ai-agents", "link_ids": [1, 2, 3]}, tax) == "wallets"
    assert taxonomy.card_subtopic({"vertical": "ai-agents", "link_ids": [9]}, tax) == "memory"
    rel = taxonomy.related(tax, [{"link_ids": [1, 2]}])
    assert rel == {"memory": ["wallets"], "wallets": ["memory"]}
    assert abs(taxonomy.cosine([1, 0], [1, 0]) - 1) < 1e-9 and taxonomy.cosine([1, 0], [0, 1]) == 0


@pytest.fixture
def vault(monkeypatch, tmp_path):
    if "search_path%3Dlane_" not in URL:
        pytest.skip("needs a lane-schema database URL")
    schema = "lane_board_brain_test"
    url = re.sub(r"search_path%3D\w+", f"search_path%3D{schema}", URL)
    from sloth.board import cards, fixtures, markdown, reading
    from sloth.core import notify
    monkeypatch.setattr(notify, "post", lambda *a, **k: None)
    monkeypatch.setattr(notify, "log", lambda *a, **k: None)
    monkeypatch.setattr(markdown, "BOARD_DIR", tmp_path / "board")
    monkeypatch.setattr(brain, "BRAIN_DIR", tmp_path / "brain")
    monkeypatch.setattr(cards, "render_all", lambda conn: 0)
    with psycopg.connect(url, row_factory=dict_row) as c:
        c.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        c.execute(f"CREATE SCHEMA {schema}")
        c.execute(SCHEMA.read_text())
        fixtures.seed(c)
        c.commit()
        made = cards.build(c, use_model=False)
        cid = made[0][0].id
        c.execute("INSERT INTO runs (card_id, model_id, outcome, approved, cost_usd, repo_url) "
                  "VALUES (%s, 'm/x', 'done', true, 0.5, 'https://github.com/u/r')", (cid,))
        c.commit()
        cards.apply_runs(c)
        reading.today_payload(c, post=True, use_model=False, today=date(2026, 10, 25))  # renders the brain
        result = brain.render(c)
        yield tmp_path / "brain", result, c
        c.rollback()
        c.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        c.commit()


def _notes(root):
    return {p: p.read_text() for p in root.rglob("*.md") if ".obsidian" not in p.parts and p.name != "README.md"}


def test_no_link_leaves_the_vault(vault):
    root, result, _ = vault
    notes = _notes(root)
    names = {p.stem for p in notes}
    for path, text in notes.items():
        assert not re.search(r"\]\((?!https?://)", text), f"markdown path link in {path}"
        assert "../" not in text, f"relative path in {path}"
        for target in brain.WIKILINK.findall(text):
            assert target in names, f"[[{target}]] in {path.name} has no note"
    assert result["edges"] > 0 and result["notes"]["prototypes"] == 1 and result["notes"]["readings"] == 1


def test_every_card_note_links_a_topic(vault):
    root, _, _ = vault
    topics = {p.stem for p in (root / "topics").glob("*.md")}
    cards = list((root / "cards").glob("*.md"))
    assert cards
    for p in cards:
        text = p.read_text()
        linked = re.search(r"Topic: \[\[([^\]]+)\]\]", text)
        assert linked and linked.group(1) in topics, p.name
        assert re.search(r"^card_id: \"k[0-9a-f]+\"$", text, re.M) and "aliases: [" in text


def test_filenames_have_no_card_ids(vault):
    root, _, _ = vault
    for p in _notes(root):
        assert not CARD_ID.search(p.stem), p.name
        visible = re.sub(r"^---.*?---", "", p.read_text(), flags=re.S)
        for target in brain.WIKILINK.findall(visible):
            assert not CARD_ID.search(target)


def test_tags_are_nested_and_graph_is_coloured(vault):
    root, _, _ = vault
    for p, text in _notes(root).items():
        fm = re.search(r"^tags: \[(.*)\]$", text, re.M).group(1)
        tags = [t.strip() for t in fm.split(",") if t.strip()]
        assert tags and all("/" in t for t in tags), p.name
        assert tags[0].startswith("type/")
        for inline in re.findall(r"(?<![\w&])#([A-Za-z][\w/-]*)", text.split("---", 2)[2]):
            assert "/" in inline, f"#{inline} in {p.name}"
    cfg = json.loads((root / ".obsidian" / "graph.json").read_text())
    assert {g["query"] for g in cfg["colorGroups"]} >= {"tag:#type/card", "tag:#type/topic", "tag:#type/vertical"}
    assert cfg["showOrphans"] is True


def test_taxonomy_is_cached_and_stable(vault):
    _, first, conn = vault
    cached = json.loads(taxonomy.CACHE_PATH.read_text())
    again = brain.render(conn)
    assert json.loads(taxonomy.CACHE_PATH.read_text()) == cached
    assert again["subtopics_per_vertical"] == first["subtopics_per_vertical"]
