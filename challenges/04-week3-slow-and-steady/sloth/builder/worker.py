"""The prototype box: a repo from the template, the Worker profile on the card, a hard timer.

Code holds the clock and the verdict. The Hermes Worker (`sloth-worker` profile, open-weight
model on OpenRouter) builds inside the repo; this module kills it at the box, runs
`make test` itself, measures cost from the OpenRouter key's usage, and completes NOTES.md.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from ..core import secrets
from ..core.config import ROOT, settings
from ..core.models import Card, Outcome

PROFILE = "sloth-worker"
TEMPLATE = ROOT / "templates" / "prototype"
SKILL = ROOT / "profiles" / "worker" / "skills" / "prototype-box" / "SKILL.md"
GRACE_S = 120          # after the box: time for the wrap-up answer before the process is killed
TEST_TIMEOUT_S = 300
RENDERED = {".md", ".toml", ".py", ""}  # template files whose {{placeholders}} are filled


@dataclass
class BoxResult:
    card_id: str
    repo_dir: str
    model: str
    outcome: Outcome
    tests_passed: bool
    test_output: str
    minutes: float
    cost_usd: float | None
    tokens_in: int | None = None
    tokens_out: int | None = None
    agent_status: str | None = None
    summary: str | None = None
    learned: str | None = None
    session_id: str | None = None
    log_path: str | None = None
    timed_out: bool = False
    extra: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str, indent=1)


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "prototype"


def links_markdown(links: list[dict]) -> str:
    if not links:
        return "- (no source links recorded)"
    out = []
    for link in links:
        title = link.get("title") or link["url"]
        saved = f" (saved {link['saved_at']:%Y-%m-%d})" if link.get("saved_at") else ""
        out.append(f"- [{title}]({link['url']}){saved}")
    return "\n".join(out)


def _render(text: str, values: dict[str, str]) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), text)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True, text=True)


def prepare_repo(card: Card, *, model: str, links: list[dict], base_dir: Path | None = None,
                 suffix: str = "") -> Path:
    """Copy the template to `<prototypes_dir>/<card-id>-<slug>`, fill placeholders, git init."""
    base = base_dir or settings().prototypes_dir
    base.mkdir(parents=True, exist_ok=True)
    name = f"{card.id}-{slugify(card.title)}{f'-{suffix}' if suffix else ''}"
    repo, n = base / name, 2
    while True:
        try:
            repo.mkdir()  # atomic: two runs of the same card never share a directory
            break
        except FileExistsError:
            repo, n = base / f"{name}-{n}", n + 1
    shutil.copytree(TEMPLATE, repo, dirs_exist_ok=True)
    values = {
        "title": card.title, "card_id": card.id, "vertical": str(card.vertical),
        "learning_goal": card.learning_goal, "hypothesis": card.hypothesis,
        "done_means": card.done_means, "kill_criteria": card.kill_criteria,
        "box_minutes": str(card.box_minutes), "model": model, "links": links_markdown(links),
        "slug": slugify(card.title), "year": str(datetime.now(UTC).year),
    }
    for path in repo.rglob("*"):
        if path.is_file() and (path.suffix in RENDERED or path.name == "Makefile"):
            path.write_text(_render(path.read_text(), values))
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=Skunkworks Sloth", "-c", "user.email=sloth@localhost",
         "commit", "-q", "-m", f"chore: scaffold card {card.id} from the Skunkworks Sloth template")
    return repo


def skill_text() -> str:
    text = SKILL.read_text()
    return text.split("---", 2)[2].strip() if text.startswith("---") else text


def build_prompt(card: Card, repo: Path, box_minutes: int, *, start: datetime | None = None) -> str:
    start = start or datetime.now(UTC)
    wrap = start + timedelta(minutes=box_minutes * 0.8)
    end = start + timedelta(minutes=box_minutes)
    return (
        f"Skunkworks Sloth card {card.id}: {card.title}\n\n"
        f"Repo: {repo}\nBox: {box_minutes} minutes, from {start:%H:%M} to {end:%H:%M} UTC. "
        f"The runner kills the session at {end:%H:%M} UTC. Check `date -u` as you go; at {wrap:%H:%M} UTC "
        f"stop building, finish NOTES.md, commit and answer.\n"
        f"Start by reading {repo}/TASK.md. Follow the prototype-box instructions below.\n\n"
        f"---\n\n{skill_text()}\n"
    )


def openrouter_usage() -> float | None:
    """Cumulative spend on the Worker's OpenRouter key (dollars); the delta is a run's cost."""
    try:
        key = secrets.get(PROFILE, "OPENROUTER_API_KEY")
        r = httpx.get("https://openrouter.ai/api/v1/key", timeout=15,
                      headers={"Authorization": f"Bearer {key}"})
        r.raise_for_status()
        return float(r.json()["data"]["usage"])
    except Exception:  # noqa: BLE001 - cost unknown is reported as None, never guessed
        return None


def settled_usage(before: float | None, *, wait_s: float = 90, step_s: float = 10) -> float | None:
    """OpenRouter's key usage lags the last call; read until two reads agree (or wait_s passes)."""
    last = openrouter_usage()
    deadline = time.monotonic() + wait_s
    while last is not None and time.monotonic() < deadline:
        time.sleep(step_s)
        now = openrouter_usage()
        if now is not None and abs(now - last) < 1e-6 and (before is None or now > before):
            return now
        last = now
    return last


def _child_env() -> dict[str, str]:
    """The prototype has its own uv project; do not leak this package's virtualenv into it."""
    return {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}


def run_tests(repo: Path) -> tuple[bool, str]:
    try:
        p = subprocess.run(["make", "test"], cwd=repo, capture_output=True, text=True,
                           timeout=TEST_TIMEOUT_S, env=_child_env())
    except subprocess.TimeoutExpired:
        return False, f"make test timed out after {TEST_TIMEOUT_S}s"
    tail = (p.stdout + p.stderr).strip().splitlines()[-15:]
    return p.returncode == 0, "\n".join(tail)


def _parse_stream(log_path: Path) -> dict:
    """Pull the final result event (tokens, text, session) out of Hermes' stream-json log."""
    out: dict = {}
    for line in log_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            out = ev
    return out


def _parse_answer(text: str) -> dict:
    for candidate in reversed(re.findall(r"\{.*?\}", text or "", flags=re.S)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return {}


def _notes_built_filled(repo: Path) -> bool:
    notes = repo / "NOTES.md"
    if not notes.exists():
        return False
    m = re.search(r"## Built\s*(.*?)(?=\n## |\Z)", notes.read_text(), flags=re.S)
    body = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip() if m else ""
    return bool(body)


def finish_notes(repo: Path, r: BoxResult) -> Path:
    """Append the runner's facts to NOTES.md; fill Built/Learned if the Worker left them empty."""
    notes = repo / "NOTES.md"
    text = notes.read_text() if notes.exists() else f"# Notes\n\n## Built\n\n## Learned\n\n## Next\n\n## Links used\n"
    if not _notes_built_filled(repo):
        text = re.sub(r"(## Built\s*)(<!--.*?-->)?", lambda m: m.group(1) + (
            f"The Worker did not fill this section. Its last summary: {r.summary or 'none'}\n\n"), text,
            count=1, flags=re.S)
        if r.learned:
            text = re.sub(r"(## Learned\s*)(<!--.*?-->)?", lambda m: m.group(1) + r.learned + "\n\n",
                          text, count=1, flags=re.S)
    cost = f"${r.cost_usd:.4f}" if r.cost_usd is not None else "unknown"
    text = text.rstrip() + (
        "\n\n## Run (written by the runner)\n\n"
        f"- Outcome: **{r.outcome}** · tests {'pass' if r.tests_passed else 'fail'} (checked by `make test` after the box)\n"
        f"- Model: `{r.model}` on OpenRouter · cost {cost} · tokens in/out {r.tokens_in}/{r.tokens_out}\n"
        f"- Wall time: {r.minutes:.1f} min of a {r.extra.get('box_minutes')}-minute box"
        f"{' (stopped by the timer)' if r.timed_out else ''}\n"
    )
    notes.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=Skunkworks Sloth", "-c", "user.email=sloth@localhost",
         "commit", "-q", "-m", f"docs: runner notes for card {r.card_id} ({r.outcome})", check=False)
    return notes


def run_box(card: Card, *, links: list[dict] | None = None, model: str | None = None,
            box_minutes: int | None = None, base_dir: Path | None = None,
            suffix: str = "", hermes: str = "hermes") -> BoxResult:
    """Prepare the repo, run the Worker under the box timer, verify, write NOTES.md."""
    model = model or settings().openrouter_model
    if not model:
        raise RuntimeError("llm.openrouter_model is not set in .sloth/config.toml (and no --model given)")
    box = box_minutes if box_minutes is not None else (card.box_minutes or settings().box_minutes)
    repo = prepare_repo(card, model=model, links=links or [], base_dir=base_dir, suffix=suffix)
    runs_dir = repo.parent / ".runs"
    runs_dir.mkdir(exist_ok=True)
    log_path = runs_dir / f"{repo.name}.jsonl"
    prompt_path = runs_dir / f"{repo.name}.prompt.md"
    prompt_path.write_text(build_prompt(card, repo, box))

    usage_before = openrouter_usage()
    cmd = [hermes, "-p", PROFILE, "chat", "--query-file", str(prompt_path), "--format", "stream-json",
           "--source", "tool", "--in", str(repo), "--provider", "openrouter", "-m", model]
    # The box is enforced here (kill at box + grace). Hermes' 80% wrap-up notice needs
    # agent.run_budget_seconds in the profile config; `chat --run-budget` is refused here.
    t0 = time.monotonic()
    timed_out = False
    with log_path.open("w") as log:
        proc = subprocess.Popen(cmd, cwd=repo, stdout=log, stderr=subprocess.STDOUT, env=_child_env(),
                                stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            proc.wait(timeout=box * 60 + GRACE_S)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
    minutes = (time.monotonic() - t0) / 60
    usage_after = settled_usage(usage_before)
    cost = (round(usage_after - usage_before, 4)
            if usage_before is not None and usage_after is not None else None)

    result_ev = _parse_stream(log_path)
    answer = _parse_answer(result_ev.get("text", ""))
    tests_passed, test_output = run_tests(repo)
    if timed_out:
        outcome = Outcome.boxed_out
    elif tests_passed and answer.get("status") != "killed":
        outcome = Outcome.done
    else:
        outcome = Outcome.killed
    tokens = result_ev.get("tokens") or {}
    r = BoxResult(
        card_id=card.id, repo_dir=str(repo), model=model, outcome=outcome, tests_passed=tests_passed,
        test_output=test_output, minutes=round(minutes, 1), cost_usd=cost,
        tokens_in=tokens.get("input"), tokens_out=tokens.get("output"),
        agent_status=answer.get("status"), summary=answer.get("summary") or (result_ev.get("text") or "")[:300] or None,
        learned=answer.get("learned"), session_id=result_ev.get("session_id"), log_path=str(log_path),
        timed_out=timed_out, extra={"box_minutes": box, "exit_code": proc.returncode},
    )
    finish_notes(repo, r)
    return r


def summary_text(r: BoxResult, card: Card, run_id: int | None = None) -> str:
    """The #sk-worker message after a box (plain text, Discord markdown)."""
    cost = f"${r.cost_usd:.2f}" if r.cost_usd is not None else "cost unknown"
    verdict = {
        Outcome.done: "done, tests pass",
        Outcome.boxed_out: f"boxed out at {r.extra.get('box_minutes')} min, tests {'pass' if r.tests_passed else 'fail'}",
        Outcome.killed: "stopped without meeting done-means",
    }[r.outcome]
    lines = [
        f"🦥 **{card.title}** (card `{card.id}`{f', run {run_id}' if run_id else ''})",
        f"{verdict} · {r.minutes:.0f} min · {cost} · `{r.model}`",
    ]
    if r.summary:
        lines.append(f"**Built:** {r.summary}")
    if r.learned:
        lines.append(f"**Learned:** {r.learned}")
    lines.append(f"Repo is local only (`{Path(r.repo_dir).name}`), notes in NOTES.md. Nothing is on GitHub until you approve.")
    return "\n".join(lines)
