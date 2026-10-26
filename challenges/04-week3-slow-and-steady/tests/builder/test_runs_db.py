"""DB round trip for runs and the approval flow. Needs a scratch schema: SLOTH_TEST_DB=1 and
SLOTH_DATABASE_URL pointing at it (the lane uses search_path=lane_builder)."""

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from sloth.core.models import Card, Column, Outcome

pytestmark = pytest.mark.skipif(os.environ.get("SLOTH_TEST_DB") != "1", reason="needs SLOTH_TEST_DB=1")

FIX = Path(__file__).parents[1] / "fixtures"

FAKE_GH = """#!{python}
import sys
args = sys.argv[1:]
open({log!r}, "a").write(" ".join(args) + "\\n")
if args[:2] == ["repo", "create"]:
    print("https://github.com/someone/" + args[2])
"""


def test_run_lifecycle_and_approval(tmp_path, monkeypatch):
    from sloth.board import brain, github, markdown
    from sloth.builder import runs
    from sloth.core.db import connect

    # Lane 2's refresh() owns the columns; keep its side effects out of the repo and off GitHub.
    monkeypatch.setattr(github, "configured", lambda: False)
    monkeypatch.setattr(markdown, "BOARD_DIR", tmp_path / "board")
    monkeypatch.setattr(brain, "BRAIN_DIR", tmp_path / "brain")

    card = Card.model_validate_json((FIX / "card.json").read_text()).model_copy(update={"id": "tst1"})
    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE card_id = 'tst1'")
        conn.execute("DELETE FROM cards WHERE id = 'tst1'")
    runs.upsert_card(card)
    repo = tmp_path / "tst1-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    run_id = runs.start_run(card.id, "test/model")
    assert runs.load_card(card.id).column == Column.building
    with pytest.raises(RuntimeError, match="still building"):
        runs.approve(run_id)

    runs.finish_run(run_id, outcome=Outcome.done, cost_usd=0.0123, tokens_in=10, tokens_out=2,
                    repo_dir=str(repo), notes_path=str(repo / "NOTES.md"))
    assert runs.load_card(card.id).column == Column.building  # done, waits for the author's tap
    assert (tmp_path / "board").exists()  # refresh() ran and rendered the board files

    log = tmp_path / "gh.log"
    gh = tmp_path / "gh"
    gh.write_text(FAKE_GH.format(python=sys.executable, log=str(log)))
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)

    with pytest.raises(RuntimeError, match="approve it first"):
        runs.approve(run_id, make_public=True, gh=str(gh))
    url = runs.approve(run_id, gh=str(gh))
    assert url == "https://github.com/someone/sloth-tst1-repo"
    assert "--private" in log.read_text() and "--public" not in log.read_text()
    run = runs.get_run(run_id)
    assert run["approved"] and run["repo_url"] == url and float(run["cost_usd"]) == pytest.approx(0.0123)
    assert runs.load_card(card.id).column == Column.built
    assert runs.approve(run_id, gh=str(gh)) == url  # idempotent: no second repo
    assert log.read_text().count("repo create") == 1

    runs.approve(run_id, make_public=True, gh=str(gh))
    assert "--visibility public" in log.read_text()

    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE card_id = 'tst1'")
        conn.execute("DELETE FROM cards WHERE id = 'tst1'")


def test_failed_box_is_killed_by_refresh(tmp_path, monkeypatch):
    from sloth.board import brain, github, markdown
    from sloth.builder import runs
    from sloth.core.db import connect

    monkeypatch.setattr(github, "configured", lambda: False)
    monkeypatch.setattr(markdown, "BOARD_DIR", tmp_path / "board")
    monkeypatch.setattr(brain, "BRAIN_DIR", tmp_path / "brain")
    card = Card.model_validate_json((FIX / "card.json").read_text()).model_copy(update={"id": "tst2"})
    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE card_id = 'tst2'")
        conn.execute("DELETE FROM cards WHERE id = 'tst2'")
    runs.upsert_card(card)
    run_id = runs.start_run(card.id, "test/model")
    runs.finish_run(run_id, outcome=Outcome.boxed_out, cost_usd=None, tokens_in=None, tokens_out=None,
                    repo_dir=str(tmp_path), notes_path="")
    assert runs.load_card(card.id).column == Column.killed
    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE card_id = 'tst2'")
        conn.execute("DELETE FROM cards WHERE id = 'tst2'")


def test_reverify_updates_outcome_and_notes(tmp_path, monkeypatch):
    from sloth.board import brain, github, markdown
    from sloth.builder import runs, worker
    from sloth.core.db import connect

    monkeypatch.setattr(github, "configured", lambda: False)
    monkeypatch.setattr(markdown, "BOARD_DIR", tmp_path / "board")
    monkeypatch.setattr(brain, "BRAIN_DIR", tmp_path / "brain")
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "sloth-fake-toolchain").write_text("#!/bin/sh\necho ok\n")
    (tools / "sloth-fake-toolchain").chmod(0o755)
    monkeypatch.setattr(worker, "login_shell_path", lambda: f"{tools}:/usr/bin:/bin")
    repo = tmp_path / "tst3-repo"
    repo.mkdir()
    (repo / "Makefile").write_text("test:\n\tsloth-fake-toolchain\n\ndemo:\n\tsloth-fake-toolchain\n")
    (repo / "NOTES.md").write_text("# Notes\n\n## Learned\n\nkeep me\n\n## Run (written by the runner)\n\n- Outcome: **killed**\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    card = Card.model_validate_json((FIX / "card.json").read_text()).model_copy(update={"id": "tst3"})
    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE card_id = 'tst3'")
        conn.execute("DELETE FROM cards WHERE id = 'tst3'")
    runs.upsert_card(card)
    run_id = runs.start_run(card.id, "test/model")
    runs.finish_run(run_id, outcome=Outcome.killed, cost_usd=0.1, tokens_in=1, tokens_out=1,
                    repo_dir=str(repo), notes_path=str(repo / "NOTES.md"))
    assert runs.load_card(card.id).column == Column.killed

    res = runs.reverify(run_id, note="Tests run in a simulator, not a live node.")
    assert res["outcome"] == "done" and res["before"] == "killed" and res["tests_passed"]
    run = runs.get_run(run_id)
    assert run["outcome"] == "done" and float(run["cost_usd"]) == pytest.approx(0.1)  # only outcome changed
    notes = (repo / "NOTES.md").read_text()
    assert "keep me" in notes and "Re-verified" in notes and "(outcome killed → done)" in notes
    assert notes.rstrip().endswith("Tests run in a simulator, not a live node.")
    assert runs.load_card(card.id).column == Column.building  # done, unapproved: refresh() maps it back
    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE card_id = 'tst3'")
        conn.execute("DELETE FROM cards WHERE id = 'tst3'")
