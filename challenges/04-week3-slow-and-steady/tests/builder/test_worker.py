import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from sloth.builder import approval, worker
from sloth.core.models import Card, Outcome

FIX = Path(__file__).parents[1] / "fixtures"


@pytest.fixture
def card() -> Card:
    return Card.model_validate_json((FIX / "card.json").read_text())


LINKS = [{"url": "https://example.com/a", "title": "Example A"}]


def test_prepare_repo_renders_template_and_commits(tmp_path, card):
    repo = worker.prepare_repo(card, model="test/model", links=LINKS, base_dir=tmp_path)
    assert repo.name.startswith("fx01-local-agent-memory")
    for name in ("README.md", "NOTES.md", "TASK.md", "pyproject.toml", "LICENSE", "Makefile"):
        assert "{{" not in (repo / name).read_text(), name
    assert card.done_means in (repo / "TASK.md").read_text()
    assert "[Example A](https://example.com/a)" in (repo / "NOTES.md").read_text()
    log = subprocess.run(["git", "-C", str(repo), "log", "--oneline"], capture_output=True, text=True).stdout
    assert "scaffold card fx01" in log
    # a second run of the same card gets its own directory
    assert worker.prepare_repo(card, model="m", links=[], base_dir=tmp_path) != repo


def test_parse_answer_takes_last_json_object():
    text = 'thinking {"x": 1}\n{"status": "done", "summary": "built it", "tests": "3 passed", "learned": "ok"}'
    assert worker._parse_answer(text)["status"] == "done"
    assert worker._parse_answer("no json here") == {}


FAKE_HERMES = r'''#!{python}
import json, sys, pathlib
repo = pathlib.Path(sys.argv[sys.argv.index("--in") + 1])
(repo / "tests" / "test_placeholder.py").unlink()
(repo / "tests" / "test_real.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n")
notes = (repo / "NOTES.md").read_text().replace("<!-- What exists now and how to run it. -->", "A thing that works.")
(repo / "NOTES.md").write_text(notes)
answer = json.dumps({{"status": "done", "summary": "built the thing", "tests": "1 passed", "learned": "it works"}})
print(json.dumps({{"type": "result", "session_id": "s1", "exit_code": 0, "text": answer,
                  "tokens": {{"input": 1000, "output": 200}}}}))
'''


def _fake_hermes(tmp_path: Path, body: str = FAKE_HERMES) -> str:
    path = tmp_path / "hermes"
    path.write_text(body.format(python=sys.executable))
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


def test_run_box_end_to_end_with_fake_hermes(tmp_path, card, monkeypatch):
    usage = iter([1.00, 1.05])
    monkeypatch.setattr(worker, "openrouter_usage", lambda: next(usage))
    monkeypatch.setattr(worker, "settled_usage", lambda before: next(usage))
    monkeypatch.setattr(worker, "run_tests", lambda repo: (
        not (repo / "tests" / "test_placeholder.py").exists(), "1 passed"))
    monkeypatch.setattr(worker.time, "sleep", lambda s: None)
    r = worker.run_box(card, links=LINKS, model="test/model", box_minutes=1,
                       base_dir=tmp_path / "protos", hermes=_fake_hermes(tmp_path))
    assert r.outcome == Outcome.done and r.tests_passed and not r.timed_out
    assert r.cost_usd == pytest.approx(0.05) and r.tokens_in == 1000
    notes = (Path(r.repo_dir) / "NOTES.md").read_text()
    assert "A thing that works." in notes and "Outcome: **done**" in notes
    text = worker.summary_text(r, card, run_id=7)
    assert "run 7" in text and "$0.05" in text and "Nothing is on GitHub until you approve" in text


def test_run_box_kills_at_the_box(tmp_path, card, monkeypatch):
    monkeypatch.setattr(worker, "GRACE_S", 1)
    monkeypatch.setattr(worker, "openrouter_usage", lambda: None)
    monkeypatch.setattr(worker, "settled_usage", lambda before: None)
    monkeypatch.setattr(worker, "run_tests", lambda repo: (False, "placeholder fails"))
    monkeypatch.setattr(worker.time, "sleep", lambda s: None)
    sleeper = "#!{python}\nimport time\ntime.sleep(120)\n"
    # box_minutes=0 → the timer fires after GRACE_S seconds
    card = card.model_copy(update={"box_minutes": 0})
    r = worker.run_box(card, links=[], model="test/model", box_minutes=0,
                       base_dir=tmp_path / "protos", hermes=_fake_hermes(tmp_path, sleeper))
    assert r.timed_out and r.outcome == Outcome.boxed_out and r.cost_usd is None
    notes = (Path(r.repo_dir) / "NOTES.md").read_text()
    assert "The Worker did not fill this section" in notes and "stopped by the timer" in notes


def test_approval_wording():
    req = approval.approval_request(3, "Card", "/x/fx01-card", tests_passed=False)
    assert "private" in req["text"] and "Tests did not pass" in req["text"]
    assert req["buttons"][0]["command"] == "sloth approve 3"
    pub = approval.publish_request(3, "Card", "https://github.com/u/r")
    assert pub["buttons"][0]["command"] == "sloth approve 3 --public"
