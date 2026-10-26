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
(repo.parent / "argv.json").write_text(json.dumps(sys.argv[1:]))
(repo / "tests" / "test_placeholder.py").unlink()
(repo / "tests" / "test_real.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n")
notes = (repo / "NOTES.md").read_text().replace("<!-- What exists now and how to run it. -->", "A thing that works.")
(repo / "NOTES.md").write_text(notes)
answer = json.dumps({{"status": "done", "summary": "built the thing", "tests": "1 passed", "learned": "it works"}})
print(json.dumps({{"type": "result", "session_id": "s1", "exit_code": 0, "text": answer,
                  "tokens": {{"input": 105000, "output": 200, "cache_read": 100000, "cache_write": 4000}}}}))
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
    r = worker.run_box(card, links=LINKS, model="test/model", provider="openrouter", box_minutes=1,
                       base_dir=tmp_path / "protos", hermes=_fake_hermes(tmp_path))
    assert r.outcome == Outcome.done and r.tests_passed and not r.timed_out
    assert r.cost_usd == pytest.approx(0.05) and r.tokens_in == 105000 and r.model == "test/model"
    argv = json.loads((tmp_path / "protos" / "argv.json").read_text())
    assert argv[argv.index("--provider") + 1] == "openrouter" and argv[argv.index("-m") + 1] == "test/model"
    notes = (Path(r.repo_dir) / "NOTES.md").read_text()
    assert "A thing that works." in notes and "Outcome: **done**" in notes
    text = worker.summary_text(r, card, run_id=7)
    assert "run 7" in text and "$0.05" in text and "Nothing is on GitHub until you approve" in text
    assert "closed model" not in text  # open weights carry no tag


def test_run_box_kills_at_the_box(tmp_path, card, monkeypatch):
    monkeypatch.setattr(worker, "GRACE_S", 1)
    monkeypatch.setattr(worker, "openrouter_usage", lambda: None)
    monkeypatch.setattr(worker, "settled_usage", lambda before: None)
    monkeypatch.setattr(worker, "run_tests", lambda repo: (False, "placeholder fails"))
    monkeypatch.setattr(worker.time, "sleep", lambda s: None)
    sleeper = "#!{python}\nimport time\ntime.sleep(120)\n"
    # box_minutes=0 → the timer fires after GRACE_S seconds
    card = card.model_copy(update={"box_minutes": 0})
    r = worker.run_box(card, links=[], model="test/model", provider="openrouter", box_minutes=0,
                       base_dir=tmp_path / "protos", hermes=_fake_hermes(tmp_path, sleeper))
    assert r.timed_out and r.outcome == Outcome.boxed_out and r.cost_usd is None
    notes = (Path(r.repo_dir) / "NOTES.md").read_text()
    assert "The Worker did not fill this section" in notes and "stopped by the timer" in notes


def test_approval_wording():
    req = approval.approval_request(3, "Card", "/x/fx01-card", tests_passed=False)
    assert "private" in req["text"] and "Tests did not pass" in req["text"] and "`approve 3`" in req["text"]
    assert req["buttons"][0]["command"] == "sloth approve 3"
    pub = approval.publish_request(3, "Card", "https://github.com/u/r")
    assert "`publish 3`" in pub["text"]
    assert pub["buttons"][0]["command"] == "sloth approve 3 --public"


def test_status_text_lists_today_and_runs():
    from datetime import datetime, UTC
    from sloth.builder import runs
    st = {"today": [{"id": "k5cbc", "title": "Spec CLI"}],
          "latest_runs": [{"id": 7, "card_id": "k5cbc", "title": "Spec CLI", "outcome": "done", "approved": False,
                           "repo_url": None, "cost_usd": 0.0467, "model_id": "m", "started_at": datetime.now(UTC),
                           "ended_at": None}]}
    text = runs.status_text(st)
    assert "Today: `k5cbc`" in text and "reply `approve 7`" in text and "$0.05" in text
    assert "No card in Today" in runs.status_text({"today": [], "latest_runs": []})


def test_run_box_anthropic_test_mode_costs_from_tokens(tmp_path, card, monkeypatch):
    def no_usage():
        raise AssertionError("OpenRouter usage must not be read for another provider")
    monkeypatch.setattr(worker, "openrouter_usage", no_usage)
    monkeypatch.setattr(worker, "settled_usage", lambda before: no_usage())
    monkeypatch.setattr(worker, "run_tests", lambda repo: (True, "1 passed"))
    r = worker.run_box(card, links=LINKS, model="claude-sonnet-5-5", provider="anthropic", box_minutes=1,
                       base_dir=tmp_path / "protos", hermes=_fake_hermes(tmp_path))
    argv = json.loads((tmp_path / "protos" / "argv.json").read_text())
    assert argv[argv.index("--provider") + 1] == "anthropic" and argv[argv.index("-m") + 1] == "claude-sonnet-5-5"
    assert r.model == "anthropic/claude-sonnet-5-5" and r.provider == "anthropic"
    # 1000 in x $2 + 200 out x $10 + 4000 cache writes x $2.50 + 100000 cache reads x $0.10, per million
    assert r.cost_usd == pytest.approx(0.024) and r.tokens_in == 105000 and r.tokens_out == 200
    assert worker.summary_text(r, card, run_id=8).count("(closed model)") == 1
    assert "via anthropic (closed model)" in (Path(r.repo_dir) / "NOTES.md").read_text()


def test_resolve_model_from_config(monkeypatch):
    import dataclasses
    from sloth.core import config
    base = config.settings()
    monkeypatch.setattr(worker, "settings", lambda: dataclasses.replace(
        base, worker_provider="anthropic", worker_model="claude-sonnet-5-5", openrouter_model="google/x"))
    assert worker.resolve_model() == ("anthropic", "claude-sonnet-5-5", "anthropic/claude-sonnet-5-5")
    assert worker.resolve_model(model="claude-other") == ("anthropic", "claude-other", "anthropic/claude-other")
    assert worker.resolve_model(provider="openrouter", model="google/x") == ("openrouter", "google/x", "google/x")
    monkeypatch.setattr(worker, "settings", lambda: dataclasses.replace(
        base, worker_provider="openrouter", worker_model="", openrouter_model="google/x"))
    assert worker.resolve_model() == ("openrouter", "google/x", "google/x")
    assert worker.token_cost("unknown-model", {"input": 1}) is None


def test_token_cost_run1_k05d2_exact_numbers():
    """Run 1 (k05d2, Sonnet 5.5): Hermes' gateway `input` already includes cache reads and writes."""
    tokens = {"input": 4_311_522, "output": 33_218, "cache_read": 4_203_979, "cache_write": 107_423}
    b = worker.split_tokens(tokens)
    assert b["input"] == 120 and b["prompt_total"] == 4_311_522
    # 120 x $2 + 4,203,979 x $0.10 + 107,423 x $2.50 + 33,218 x $10, per million
    assert worker.token_cost("claude-sonnet-5-5", tokens) == pytest.approx(1.0214, abs=1e-4)
    # the in-process shape (uncached input smaller than the cache buckets) is not subtracted twice
    assert worker.split_tokens({"input": 120, "cache_read": 4_203_979, "cache_write": 107_423})["input"] == 120


def _settings_with(**kw):
    import dataclasses
    from sloth.core import config
    return lambda: dataclasses.replace(config.settings(), **kw)


def test_resolve_model_complex_path(monkeypatch):
    monkeypatch.setattr(worker, "settings", _settings_with(
        worker_provider="openrouter", worker_model="", openrouter_model="google/gemma-4-26b-a4b-it",
        complex_provider="anthropic", complex_model="claude-sonnet-5-5"))
    assert worker.resolve_model() == ("openrouter", "google/gemma-4-26b-a4b-it", "google/gemma-4-26b-a4b-it")
    assert worker.resolve_model(complex_task=True) == ("anthropic", "claude-sonnet-5-5", "anthropic/claude-sonnet-5-5")
    # explicit flags still win over the complex settings
    assert worker.resolve_model("openrouter", "qwen/qwen3-coder-next", complex_task=True) == (
        "openrouter", "qwen/qwen3-coder-next", "qwen/qwen3-coder-next")
    assert worker.resolve_model(model="claude-opus-5-5", complex_task=True)[2] == "anthropic/claude-opus-5-5"


def test_model_tags():
    assert worker.model_tag("openrouter") == "" and worker.model_tag("openrouter", True) == ""
    assert worker.model_tag("anthropic") == " (closed model)"
    assert worker.model_tag("anthropic", True) == " (closed model, complex task)"


def test_run_box_complex_uses_complex_settings(tmp_path, card, monkeypatch):
    monkeypatch.setattr(worker, "settings", _settings_with(
        worker_provider="openrouter", worker_model="", openrouter_model="google/gemma-4-26b-a4b-it",
        complex_provider="anthropic", complex_model="claude-sonnet-5-5", prototypes_dir=tmp_path / "p"))
    monkeypatch.setattr(worker, "openrouter_usage", lambda: (_ for _ in ()).throw(AssertionError("no OpenRouter")))
    monkeypatch.setattr(worker, "run_tests", lambda repo: (True, "1 passed"))
    r = worker.run_box(card, links=LINKS, complex_task=True, box_minutes=1,
                       base_dir=tmp_path / "protos", hermes=_fake_hermes(tmp_path))
    argv = json.loads((tmp_path / "protos" / "argv.json").read_text())
    assert argv[argv.index("--provider") + 1] == "anthropic" and argv[argv.index("-m") + 1] == "claude-sonnet-5-5"
    assert r.model == "anthropic/claude-sonnet-5-5" and r.complex_task and r.cost_usd == pytest.approx(0.024)
    assert "(closed model, complex task)" in worker.summary_text(r, card, run_id=9)
    assert "via anthropic (closed model, complex task)" in (Path(r.repo_dir) / "NOTES.md").read_text()


def test_status_text_names_both_models():
    from sloth.builder import runs
    text = runs.status_text({"today": [], "latest_runs": [], "models": {
        "go": "google/gemma-4-26b-a4b-it", "go deep": "anthropic/claude-sonnet-5-5 (closed model, complex task)"}})
    assert text.startswith("Models: `go` → `google/gemma-4-26b-a4b-it` · `go deep` → `anthropic/claude-sonnet-5-5")


def _tool_repo(tmp_path: Path) -> tuple[Path, Path]:
    """A repo whose `make test` needs a tool that is only on the login shell's PATH."""
    tools = tmp_path / "tools"
    tools.mkdir()
    tool = tools / "sloth-fake-toolchain"
    tool.write_text("#!/bin/sh\necho toolchain ok\n")
    tool.chmod(0o755)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Makefile").write_text("test:\n\tsloth-fake-toolchain\n\ndemo:\n\tsloth-fake-toolchain\n")
    return repo, tools


def test_verification_uses_the_worker_terminal_path(tmp_path, monkeypatch):
    repo, tools = _tool_repo(tmp_path)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")  # the runner's own, stripped PATH
    monkeypatch.setattr(worker, "login_shell_path", lambda: f"{tools}:/usr/bin:/bin")
    ok, out = worker.run_tests(repo)
    assert ok and "toolchain ok" in out
    assert worker.run_demo(repo)[0]
    # and the same Makefile fails when verification falls back to the stripped PATH
    monkeypatch.setattr(worker, "login_shell_path", lambda: "/usr/bin:/bin")
    assert not worker.run_tests(repo)[0]


def test_login_shell_path_unions_interactive_shells(tmp_path, monkeypatch):
    fake_shell = tmp_path / "bash"
    fake_shell.write_text('#!/bin/sh\nprintf "noise __SLOTH_PATH__/from/rc:/usr/bin__SLOTH_PATH__ noise"\n')
    fake_shell.chmod(0o755)
    monkeypatch.setenv("SHELL", str(fake_shell))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    worker.login_shell_path.cache_clear()
    try:
        parts = worker.login_shell_path().split(":")
    finally:
        worker.login_shell_path.cache_clear()
    assert parts[0] == "/from/rc" and "/bin" in parts and len(parts) == len(set(parts))


ALLOW = ["openrouter:google/gemma-4-26b-a4b-it", "openrouter:qwen/qwen3-coder-next", "anthropic:claude-sonnet-5-5"]
AMBIG = ALLOW + ["openrouter:qwen/qwen3-coder-flash-next"]


def test_use_picks_from_the_allowlist(monkeypatch):
    monkeypatch.setattr(worker, "settings", _settings_with(
        worker_models=ALLOW, worker_provider="openrouter", worker_model="", openrouter_model="google/gemma-4-26b-a4b-it",
        complex_provider="anthropic", complex_model="claude-sonnet-5-5"))
    assert worker.resolve_model(use="qwen3-coder-next") == ("openrouter", "qwen/qwen3-coder-next", "qwen/qwen3-coder-next")
    assert worker.resolve_model(use="openrouter:qwen/qwen3-coder-next")[1] == "qwen/qwen3-coder-next"
    assert worker.resolve_model(use="Claude-Sonnet-5-5") == ("anthropic", "claude-sonnet-5-5", "anthropic/claude-sonnet-5-5")
    assert worker.resolve_model(use="gemma-4-26b-a4b-it")[0] == "openrouter"
    with pytest.raises(worker.ModelNotAllowed) as e:
        worker.resolve_model(use="gpt-5")
    msg = str(e.value)
    assert "not on the allowlist" in msg and "`anthropic:claude-sonnet-5-5` (closed model)" in msg
    assert "`openrouter:qwen/qwen3-coder-next` (open weights)" in msg
    monkeypatch.setattr(worker, "settings", _settings_with(worker_models=AMBIG))
    with pytest.raises(worker.ModelNotAllowed, match="matches several"):
        worker.resolve_model(use="-next")  # not unique once two entries end the same way
    # explicit CLI flags stay unrestricted
    assert worker.resolve_model("openrouter", "deepseek/deepseek-v4-flash")[2] == "deepseek/deepseek-v4-flash"


def test_use_tags_follow_the_provider():
    assert worker.model_tag("anthropic") == " (closed model)"
    assert worker.model_tag("anthropic", True) == " (closed model, complex task)"
    assert worker.model_tag("openrouter") == ""


def test_status_and_desk_text_show_the_allowlist(monkeypatch):
    from sloth.builder import runs
    monkeypatch.setattr(worker, "settings", _settings_with(worker_models=ALLOW))
    lines = worker.allowlist_lines()
    assert lines == ["`openrouter:google/gemma-4-26b-a4b-it` (open weights)",
                     "`openrouter:qwen/qwen3-coder-next` (open weights)",
                     "`anthropic:claude-sonnet-5-5` (closed model)"]
    text = runs.status_text({"today": [], "latest_runs": [], "allowed": lines})
    assert "`go with <model>` allows: `openrouter:google/gemma-4-26b-a4b-it` (open weights)" in text
    skill = (Path(__file__).parents[2] / "profiles/worker/skills/worker-desk/SKILL.md").read_text()
    assert "--use qwen3-coder-next" in skill and "$SLOTH work --models" in skill and "version: 0.3.0" in skill
