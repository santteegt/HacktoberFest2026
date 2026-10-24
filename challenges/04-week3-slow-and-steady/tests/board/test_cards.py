import json
from datetime import UTC, date, datetime
from pathlib import Path

from sloth.board import cluster, github, markdown, wording
from sloth.board.cards import column_from_run
from sloth.board.store import KeptLink

FIX = Path(__file__).parents[1] / "fixtures"


def fixture_links() -> list[KeptLink]:
    links = json.loads((FIX / "links.json").read_text())
    out = []
    for t in json.loads((FIX / "triage.json").read_text()):
        if not t["still_relevant"]:
            continue
        link = links[t["link_index"]]
        out.append(KeptLink(
            link_id=t["link_index"] + 1, url=link["url"], title=link["title"],
            saved_at=datetime.fromisoformat(link["saved_at"]), folder_path=link["folder_path"],
            topic=t["topic"], vertical=t["vertical"], kind=t["kind"], buildable=t["buildable"],
            one_line_idea=t["one_line_idea"]))
    return out


def test_clusters_respect_card_rules():
    groups = cluster.cluster(fixture_links())
    assert groups
    for g in groups:
        assert 2 <= len(g) <= 5
        assert all(link.buildable >= 2 for link in g)
        assert len({link.vertical for link in g}) == 1
    used = [link.link_id for g in groups for link in g]
    assert len(used) == len(set(used))
    # rust (buildable 0) and decentralized-ai (buildable 1) never become cards
    assert {g[0].vertical for g in groups} == {"ai-agents", "llms", "ai-engineering", "security-privacy"}


def test_clusters_are_deterministic_and_split_by_topic():
    def mk(i, topic, vertical="ai-agents"):
        return KeptLink(i, f"https://e.x/{i}", f"t{i}", datetime(2026, 1, i, tzinfo=UTC), None,
                        topic, vertical, "tool", 3, None)
    links = [mk(1, "agent memory sqlite"), mk(2, "agent memory vectors"), mk(3, "rust wasm runtime"),
             mk(4, "wasm runtime sandbox"), mk(5, "lonely topic")]
    a, b = cluster.cluster(links), cluster.cluster(list(reversed(links)))
    assert [[x.link_id for x in g] for g in a] == [[x.link_id for x in g] for g in b]
    sets = [{x.link_id for x in g} for g in a]
    assert {1, 2} <= sets[0] or {1, 2} <= sets[1]
    assert sum(len(s) for s in sets) == 5  # the singleton joined a group, not dropped


def test_single_link_vertical_waits():
    link = KeptLink(1, "u", "t", None, None, "x", "hardware", "tool", 3, None)
    assert cluster.cluster([link]) == []


def test_card_id_stable_and_collision_safe():
    a = cluster.card_id([3, 1, 2], set())
    assert a == cluster.card_id([1, 2, 3], set()) and a.startswith("k") and len(a) == 5
    assert cluster.card_id([1, 2, 3], {a}) != a


def test_verifier_and_fallback():
    links = fixture_links()[:3]
    good = wording.CardWording(
        title="Tiny RAG tracer with memory",
        learning_goal="Learn how a planner agent splits a task into steps.",
        hypothesis="I can build a planner loop with a local model within 2 hours.",
        done_means="`make demo` prints three planned steps; tests pass.")
    assert wording.verify(good, links) == []
    bad = good.model_copy(update={"title": "Card: \"x\"", "hypothesis": "Maybe."})
    problems = wording.verify(bad, links)
    assert any("title" in p for p in problems) and any("hypothesis" in p for p in problems)
    fb = wording.fallback(links, "ai-agents", 120)
    assert wording.verify(fb, links) == []
    w, trace = wording.word_card(links, "ai-agents", box=120, use_model=False)
    assert trace["fallback"] and w == fb


def test_kill_criteria_is_code():
    assert wording.kill_criteria(120) == (
        "Kill if there is no running skeleton after 40 minutes, "
        "or if done-means is not met when the 120-minute box ends.")


def test_column_follows_runs():
    assert column_from_run("today", None) == "today"
    assert column_from_run("today", {"outcome": "building"}) == "building"
    assert column_from_run("building", {"outcome": "done", "approved": False}) == "building"
    assert column_from_run("building", {"outcome": "done", "approved": True}) == "built"
    assert column_from_run("building", {"outcome": "boxed_out"}) == "killed"
    assert column_from_run("building", {"outcome": "killed"}) == "killed"
    assert column_from_run("archived", {"outcome": "building"}) == "archived"


CARD = {"id": "kabc1", "title": "Agent memory demo", "vertical": "ai-agents", "column": "today",
        "learning_goal": "Learn x.", "hypothesis": "I can y.", "done_means": "z", "box_minutes": 120,
        "kill_criteria": "k", "link_ids": [1, 2], "picked_on": date(2026, 10, 24)}


def test_markdown_and_files(tmp_path):
    links = {1: {"url": "https://a.example/1", "title": "A", "saved_at": datetime(2026, 1, 2),
                 "one_line_idea": "idea"}}
    run = {"outcome": "done", "approved": True, "model_id": "m/x", "cost_usd": 0.0412,
           "repo_url": "https://github.com/u/r", "notes_path": "NOTES.md"}
    md = markdown.card_markdown(CARD, links, run)
    assert "id: kabc1" in md and "(saved 2026-01-02) — idea" in md and "link 2 (missing)" in md
    assert "Cost: $0.04" in md and "https://github.com/u/r/blob/HEAD/NOTES.md" in md
    p = markdown.write_card_file(CARD, links, None, tmp_path)
    assert p == tmp_path / "today" / "kabc1.md"
    moved = {**CARD, "column": "building"}
    markdown.write_card_file(moved, links, None, tmp_path)
    assert not p.exists() and (tmp_path / "building" / "kabc1.md").exists()


IDS = {"project_id": "P", "fields": {
    "Status": {"id": "FS", "type": "SINGLE_SELECT", "options": {"Today": "o1", "Backlog": "o0"}},
    "Vertical": {"id": "FV", "type": "SINGLE_SELECT", "options": {"ai-agents": "v1"}},
    "Card ID": {"id": "FC", "type": "TEXT"}, "Box (min)": {"id": "FB", "type": "NUMBER"},
    "Picked": {"id": "FP", "type": "DATE"}, "Cost (USD)": {"id": "FX", "type": "NUMBER"},
    "Model": {"id": "FM", "type": "TEXT"}, "Repo URL": {"id": "FR", "type": "TEXT"},
    "Links": {"id": "FL", "type": "NUMBER"}}}


def test_project_diff_is_idempotent():
    want = github.desired(CARD, None)
    assert want["Status"] == "Today" and want["Picked"] == "2026-10-24" and want["Cost (USD)"] is None
    first = github.field_changes(want, {})
    assert set(first) == {"Status", "Vertical", "Card ID", "Box (min)", "Picked", "Links"}
    have = {**want, "Box (min)": 120.0, "Links": 2.0}  # the API returns numbers as floats
    assert github.field_changes(want, have) == {}
    muts = github.field_mutations(IDS, "I1", {"Status": "Today", "Model": None, "Box (min)": 120}, "f0")
    assert 'singleSelectOptionId: "o1"' in muts[0]
    assert muts[1].startswith("f0_1: clearProjectV2ItemFieldValue")
    assert "{number: 120.0}" in muts[2]


def test_readme_stamp_ignored():
    a = "x\n_Updated 2026-10-24 16:53 UTC by `sloth board sync`. y_"
    b = "x\n_Updated 2026-10-24 17:10 UTC by `sloth board sync`. y_"
    assert github._strip_stamp(a) == github._strip_stamp(b)
    assert github._strip_stamp(a) != github._strip_stamp(b.replace("y_", "z_"))
