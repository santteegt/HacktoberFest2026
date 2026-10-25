import os
import re
from datetime import UTC, date, datetime

import psycopg
import pytest
from psycopg.rows import dict_row

from sloth.board import reading
from sloth.board.reading import Candidate
from sloth.core.db import SCHEMA

TODAY = date(2026, 10, 25)


def cand(i, vertical="ai-agents", chars=0, saved=datetime(2026, 10, 1, tzinfo=UTC), title="Agent memory",
         text=None):
    return Candidate(i, f"https://e.x/{i}", title, saved, vertical, "agent memory", "article",
                     "Explains agent memory stores.", None, chars, text)


def test_score_prefers_focus_then_readable_then_fresh():
    w = {"ai-agents": 1.0}
    focus_card = reading.score(cand(1, chars=0), w, set(), TODAY)
    other = reading.score(cand(2, "rust", chars=5000, title="Rust"), w, set(), TODAY)
    assert focus_card.score > other.score
    full = reading.score(cand(3, chars=5000), w, set(), TODAY)
    assert full.score > focus_card.score  # readable text beats title-only
    old = reading.score(cand(4, chars=5000, saved=datetime(2025, 3, 1, tzinfo=UTC)), w, set(), TODAY)
    assert full.score > old.score
    hit = reading.score(cand(5, chars=5000), w, {"memory"}, TODAY)
    assert hit.hits == ("memory",) and hit.score > full.score
    assert reading.score(cand(6, "rust"), None, set(), TODAY).score > 0.25  # no focus: all equal weight


def test_search_pages_are_not_readings():
    assert reading.SEARCH_PAGE.search("https://www.google.com/search?q=agent+memory")
    assert not reading.SEARCH_PAGE.search("https://github.com/google/search-tools")


def test_jitter_is_stable_per_day():
    a = reading.score(cand(7), None, set(), TODAY).score
    assert a == reading.score(cand(7), None, set(), TODAY).score
    assert a != reading.score(cand(7), None, set(), date(2026, 10, 26)).score


def test_why_verifier_and_fallback():
    c = cand(1, title="Memvid: photographic memory for agents", text="Memvid stores chunks in a video file.")
    assert reading.verify_why("A short look at how Memvid packs agent memory into a single file.", c) == []
    assert reading.verify_why("Great read!", c)
    assert any("mention" in p for p in reading.verify_why("A fantastic and inspiring piece worth everyone's time.", c))
    assert any("URL" in p for p in reading.verify_why("See https://e.x for how memvid stores memory chunks.", c))
    assert reading.fallback_why(c) == "Explains agent memory stores."
    assert reading.word_why(c, None, use_model=False) == ("Explains agent memory stores.", "code")


def test_reading_text_fits_and_keeps_url():
    url = "https://github.com/someone/a-very-long-repository-name-for-agents/blob/main/docs/README.md"
    text = reading.reading_text("T" * 500, url, "ai-agents", "W" * 300, left=608)
    assert len(text) <= reading.MAX_TEXT
    assert f"\n{url}\n" in text
    assert text.startswith("**Today’s reading** · AI agents")
    assert "_608 more in the reading pile._" in text
    assert reading.reading_text("x", url, "rust", "why", extra=True).startswith("**Another reading** · Rust")


# ------------------------------------------------------------------ database flow

URL = os.environ.get("SLOTH_DATABASE_URL", "")


def test_reading_page_and_excerpt():
    from sloth.board import brain
    r = {"page": "2026-10-25", "picked_on": TODAY, "extra": False, "vertical": "ai-agents",
         "title": "Agent memory frameworks", "url": "https://e.x/m", "saved_at": datetime(2026, 3, 2, tzinfo=UTC),
         "why": "Compares eight memory frameworks for agents.", "readable_text": "word " * 400}
    page = brain.reading_page(r, [{"id": "kab12", "title": "Memory scaffold"}], "2026-10-25T08:00:00Z")
    assert page.startswith("---\ntype: reading\n")
    assert "- Link: https://e.x/m" in page and "- Saved: 2026-03-02" in page
    assert "[AI agents](../verticals/ai-agents.md)" in page and "[all readings](index.md)" in page
    assert "## Why today\n\nCompares eight memory frameworks for agents." in page
    assert "- [Memory scaffold](../cards/kab12.md)" in page
    quote = page.split("## Excerpt\n\n> ")[1].split("\n")[0]
    assert len(quote) <= brain.EXCERPT_CHARS + 1 and quote.endswith("…")
    assert brain.excerpt("a  b\n\nc") == "a b c"
    empty = brain.reading_page({**r, "readable_text": None}, [], "t")
    assert "_Only the title was readable" in empty and "_Nothing built in this vertical yet._" in empty


@pytest.fixture
def conn(monkeypatch, tmp_path):
    if "search_path%3Dlane_" not in URL:
        pytest.skip("needs a lane-schema database URL")
    schema = "lane_board_reading_test"
    url = re.sub(r"search_path%3D\w+", f"search_path%3D{schema}", URL)
    from sloth.board import brain, fixtures, markdown
    from sloth.core import notify
    sent = []
    monkeypatch.setattr(notify, "post", lambda ch, text, **k: sent.append((ch, text)))
    monkeypatch.setattr(notify, "log", lambda *a, **k: sent.append(("log", a[2])))
    monkeypatch.setattr(brain, "BRAIN_DIR", tmp_path / "brain")
    monkeypatch.setattr(markdown, "BOARD_DIR", tmp_path / "board")
    with psycopg.connect(url, row_factory=dict_row) as c:
        c.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        c.execute(f"CREATE SCHEMA {schema}")
        c.execute(SCHEMA.read_text())
        fixtures.seed(c)
        ids = [r["id"] for r in c.execute("SELECT id FROM links WHERE status = 'reading' ORDER BY id").fetchall()]
        c.execute("INSERT INTO enrichment (link_id, readable_text, readable_chars, fetched_with) "
                  "VALUES (%s, 'Rust ownership explained with small examples.', 4000, 'http')", (ids[-1],))
        c.commit()
        c.sent = sent
        c.brain = tmp_path / "brain"
        yield c
        c.rollback()
        c.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        c.commit()


def test_daily_reading_flow(conn):
    readable = conn.execute("SELECT link_id FROM enrichment").fetchone()["link_id"]
    preview = reading.today_payload(conn, use_model=False, today=TODAY)
    assert preview["ok"] and preview["link_id"] == readable and not preview["recorded"]
    assert conn.sent == [] and not (conn.brain / "reading").exists()  # a preview never posts, logs or writes

    posted = reading.today_payload(conn, post=True, use_model=False, today=TODAY)
    assert posted["link_id"] == readable and posted["posted"] and posted["recorded"]
    assert conn.sent[0][0] == "daily_reading" and posted["url"] in conn.sent[0][1]
    page = (conn.brain / "reading" / "2026-10-25.md").read_text()
    v = posted["vertical"]
    assert posted["url"] in page and "Rust ownership explained" in page and f"(../verticals/{v}.md)" in page
    assert "(2026-10-25.md)" in (conn.brain / "reading" / "index.md").read_text()
    assert "(reading/2026-10-25.md)" in (conn.brain / "index.md").read_text()
    assert "(../reading/2026-10-25.md)" in (conn.brain / "verticals" / f"{v}.md").read_text()

    again_post = reading.today_payload(conn, post=True, use_model=False, today=TODAY)
    assert again_post.get("already") and len([s for s in conn.sent if s[0] == "daily_reading"]) == 1

    extra = reading.today_payload(conn, again=True, use_model=False, today=TODAY)
    assert extra["ok"] and extra["recorded"] and extra["link_id"] != readable
    assert (conn.brain / "reading" / "2026-10-25-2.md").exists()
    nxt = reading.today_payload(conn, again=True, use_model=False, today=TODAY)
    assert nxt["link_id"] not in (readable, extra["link_id"])
    index = (conn.brain / "reading" / "index.md").read_text()
    assert index.index("2026-10-25-3.md") < index.index("(2026-10-25.md)")  # newest first

    tomorrow = reading.today_payload(conn, use_model=False, today=date(2026, 10, 26))
    assert tomorrow["link_id"] != readable  # never recommended twice
