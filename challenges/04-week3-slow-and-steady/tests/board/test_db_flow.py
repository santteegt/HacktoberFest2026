"""End to end on Postgres in a throwaway schema. Skipped unless SLOTH_DATABASE_URL points at a lane schema."""

import os
import re
from datetime import date

import psycopg
import pytest
from psycopg.rows import dict_row

from sloth.core.db import SCHEMA

URL = os.environ.get("SLOTH_DATABASE_URL", "")
pytestmark = pytest.mark.skipif("search_path%3Dlane_" not in URL, reason="needs a lane-schema database URL")
TEST_SCHEMA = "lane_board_test"


@pytest.fixture
def conn(monkeypatch, tmp_path):
    from sloth.board import brain, github, markdown
    url = re.sub(r"search_path%3D\w+", f"search_path%3D{TEST_SCHEMA}", URL)
    with psycopg.connect(url, row_factory=dict_row) as c:
        c.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        c.execute(f"CREATE SCHEMA {TEST_SCHEMA}")
        c.execute(SCHEMA.read_text())
        c.commit()
        monkeypatch.setattr(markdown, "BOARD_DIR", tmp_path / "board")
        monkeypatch.setattr(brain, "BRAIN_DIR", tmp_path / "brain")
        monkeypatch.setattr(github, "configured", lambda: False)
        monkeypatch.setenv("SLOTH_DRY_RUN", "1")
        yield c
        c.rollback()
        c.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        c.commit()


def test_seed_build_pick_run_brain(conn, tmp_path):
    from sloth.board import brain, cards, fixtures, focus, pick, store

    assert fixtures.seed(conn)["links"] == 42
    conn.commit()
    made = cards.build(conn, use_model=False)
    assert len(made) == 4 and all(t["fallback"] for _, t in made)
    assert cards.build(conn, use_model=False) == []  # links on live cards are not reused
    assert len(list((tmp_path / "board" / "backlog").glob("*.md"))) == 4

    focus.set_focus(conn, text="security", weights=None, use_model=False, today=date(2026, 10, 24))
    payload = pick.options_payload(conn, n=4, use_model=False, today=date(2026, 10, 24))
    assert payload["ok"] and len(payload["choices"]) == 4
    top = payload["options"][0]
    assert store.get_card(conn, top["card_id"])["vertical"] == "security-privacy"

    result = pick.choose(conn, payload["choices"][1] + " (Recommended)", today=date(2026, 10, 24))
    assert result["ok"] and result["card_id"] == payload["options"][1]["card_id"]
    picked = result["card_id"]
    assert (tmp_path / "board" / "today" / f"{picked}.md").exists()
    assert pick.show_payload(conn)["card"]["id"] == picked
    # picking another card sends the unstarted one back
    again = pick.choose(conn, top["card_id"], today=date(2026, 10, 24))
    assert again["returned_to_backlog"] == [picked]

    conn.execute("INSERT INTO runs (card_id, model_id, outcome) VALUES (%s, 'm/x', 'building')", (top["card_id"],))
    conn.commit()
    out = cards.refresh(conn)
    assert out["moves_from_runs"] == [(top["card_id"], "today", "building")]
    assert pick.show_payload(conn)["card"] is None
    conn.execute("UPDATE runs SET outcome = 'done', approved = true, cost_usd = 0.05, ended_at = now(), "
                 "repo_url = 'https://github.com/u/r' WHERE card_id = %s", (top["card_id"],))
    conn.commit()
    out = cards.refresh(conn)
    assert out["moves_from_runs"] == [(top["card_id"], "building", "built")]
    assert out["project"] == "not configured (markdown only)"
    title = store.get_card(conn, top["card_id"])["title"]
    assert (tmp_path / "brain" / "prototypes" / f"{brain.safe_name(title + ' (prototype)')}.md").exists()
    assert brain.render(conn)["new_pages"] == []
    assert store.last_touched(conn)["security-privacy"] == date(2026, 10, 24)
    assert pick.choose(conn, "no such card")["ok"] is False
