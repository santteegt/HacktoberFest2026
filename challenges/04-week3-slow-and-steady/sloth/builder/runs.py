"""`runs` rows. The Builder writes only runs; Lane 2's `sloth.board.cards.refresh(conn)` owns
`cards.column` and maps the latest run to a column (building → Building, done unapproved →
Building, done + approved → Built, boxed_out/killed → Killed), then rewrites the board files and
the brain and syncs the GitHub Project. It is called after every runs write.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..core.db import connect
from ..core.models import Card, Outcome


def load_card(card_id: str) -> Card:
    with connect() as conn:
        row = conn.execute('SELECT * FROM cards WHERE id = %s', (card_id,)).fetchone()
    if not row:
        raise KeyError(f"card {card_id} not found")
    return Card.model_validate({**row, "link_ids": list(row["link_ids"] or [])})


def upsert_card(card: Card) -> None:
    """Fixture and test helper: insert a card row if it is missing; never changes an existing card."""
    with connect() as conn:
        conn.execute(
            """INSERT INTO cards (id, title, vertical, learning_goal, hypothesis, done_means, box_minutes,
                                  link_ids, kill_criteria, "column")
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO NOTHING""",
            (card.id, card.title, str(card.vertical), card.learning_goal, card.hypothesis, card.done_means,
             card.box_minutes, card.link_ids, card.kill_criteria, str(card.column)),
        )


def card_links(card: Card) -> list[dict]:
    if not card.link_ids:
        return []
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, url, title, saved_at FROM links WHERE id = ANY(%s) ORDER BY saved_at NULLS LAST",
            (card.link_ids,)).fetchall()
    found = {r["id"] for r in rows}
    return list(rows) + [{"url": f"(link {i} not in the database)", "title": None}
                         for i in card.link_ids if i not in found]


def refresh_board(conn) -> dict:
    """Hand the move to Lane 2. A board/Project failure is reported, never loses the run row."""
    try:
        from ..board.cards import refresh
        return refresh(conn)
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {str(e)[:300]}"}


def start_run(card_id: str, model: str, repo_dir: str | None = None) -> int:
    with connect() as conn:
        run_id = conn.execute(
            "INSERT INTO runs (card_id, model_id, outcome, repo_dir) VALUES (%s, %s, 'building', %s) RETURNING id",
            (card_id, model, repo_dir)).fetchone()["id"]
        conn.commit()
        refresh_board(conn)
    return run_id


def finish_run(run_id: int, *, outcome: Outcome, cost_usd: float | None, tokens_in: int | None,
               tokens_out: int | None, repo_dir: str, notes_path: str) -> None:
    with connect() as conn:
        conn.execute(
            """UPDATE runs SET ended_at = now(), outcome = %s, cost_usd = %s, tokens_in = %s, tokens_out = %s,
                   repo_dir = %s, notes_path = %s WHERE id = %s""",
            (str(outcome), cost_usd, tokens_in, tokens_out, repo_dir, notes_path, run_id))
        conn.commit()
        refresh_board(conn)


def get_run(run_id: int) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = %s", (run_id,)).fetchone()
    if not row:
        raise KeyError(f"run {run_id} not found")
    return row


def status() -> dict:
    """Today's card(s) and the latest runs, for the Worker desk's `status` and `go`."""
    with connect() as conn:
        today = conn.execute(
            """SELECT id, title FROM cards WHERE "column" = 'today' ORDER BY moved_at DESC""").fetchall()
        latest = conn.execute(
            """SELECT r.id, r.card_id, c.title, r.outcome, r.approved, r.repo_url, r.cost_usd, r.model_id,
                      r.started_at, r.ended_at
               FROM runs r JOIN cards c ON c.id = r.card_id ORDER BY r.started_at DESC LIMIT 3""").fetchall()
    from .worker import allowlist_lines, model_tag, resolve_model
    models = {}
    for path, flag in (("go", False), ("go deep", True)):
        try:
            provider, _, model_id = resolve_model(complex_task=flag)
            models[path] = f"{model_id}{model_tag(provider, flag)}"
        except RuntimeError as e:
            models[path] = f"not configured ({e})"
    return {"today": today, "latest_runs": latest, "models": models, "allowed": allowlist_lines()}


def status_text(st: dict) -> str:
    lines = []
    if st.get("models"):
        lines.append("Models: " + " · ".join(f"`{k}` → `{v}`" for k, v in st["models"].items()))
    if st.get("allowed"):
        lines.append("`go with <model>` allows: " + ", ".join(st["allowed"]))
    if st["today"]:
        lines += [f"Today: `{c['id']}` {c['title']} (reply `go` to start its box)" for c in st["today"]]
    else:
        lines.append("No card in Today. The Coordinator's daily pick puts one there.")
    for r in st["latest_runs"]:
        cost = f"${float(r['cost_usd']):.2f}" if r["cost_usd"] is not None else "cost pending"
        state = r["outcome"] if r["outcome"] != "building" else f"building since {r['started_at']:%H:%M} UTC"
        pushed = f", repo {r['repo_url']}" if r["repo_url"] else (
            f", reply `approve {r['id']}` to push it" if r["outcome"] == "done" else "")
        lines.append(f"Run {r['id']}: `{r['card_id']}` {r['title']}: {state}, {cost}{pushed}")
    return "\n".join(lines)


def reverify(run_id: int, *, note: str | None = None) -> dict:
    """Re-run `make test` (and `make demo`) in the run's repo with the Worker terminal's PATH.

    Updates only `runs.outcome` (done | killed), appends a "Re-verified" line (and `note`, if given)
    to NOTES.md's Run section, then hands the move to the board's refresh().
    """
    from datetime import UTC, datetime
    from pathlib import Path

    from .worker import append_run_note, run_demo, run_tests

    run = get_run(run_id)
    if run["outcome"] == "building":
        raise RuntimeError(f"run {run_id} is still building")
    repo = Path(run["repo_dir"] or "")
    if not (repo / "Makefile").is_file():
        raise RuntimeError(f"run {run_id} has no local repo with a Makefile ({repo})")
    tests_ok, test_out = run_tests(repo)
    demo_ok, demo_out = run_demo(repo)
    outcome = Outcome.done if tests_ok else Outcome.killed
    when = datetime.now(UTC).strftime("%Y-%m-%d %H:%MZ")
    append_run_note(repo, (
        f"Re-verified {when} by `sloth work --verify {run_id}` with the Worker terminal's PATH: "
        f"tests {'pass' if tests_ok else 'fail'}, demo {'exit 0' if demo_ok else 'failed'} "
        f"(outcome {run['outcome']} → {outcome})."), message=f"docs: re-verify run {run_id} ({outcome})")
    if note:
        append_run_note(repo, note, message=f"docs: runner note for run {run_id}")
    with connect() as conn:
        conn.execute("UPDATE runs SET outcome = %s WHERE id = %s", (str(outcome), run_id))
        conn.commit()
        board = refresh_board(conn)
    return {"run_id": run_id, "card_id": run["card_id"], "before": run["outcome"], "outcome": str(outcome),
            "tests_passed": tests_ok, "demo_ok": demo_ok, "test_output": test_out, "demo_output": demo_out,
            "board": board}


def repo_name(repo_dir: str) -> str:
    return f"sloth-{Path(repo_dir).name}"


def approve(run_id: int, *, make_public: bool = False, gh: str = "gh") -> str:
    """The author's tap: push the run's repo to GitHub (private), or flip an approved repo public.

    Nothing reaches GitHub before this is called. `make_public` is a second, separate tap.
    """
    run = get_run(run_id)
    if run["outcome"] == "building":
        raise RuntimeError(f"run {run_id} is still building")
    repo_dir = run["repo_dir"]
    if not repo_dir or not Path(repo_dir).is_dir():
        raise RuntimeError(f"run {run_id} has no local repo ({repo_dir})")
    if make_public:
        if not run["repo_url"]:
            raise RuntimeError(f"run {run_id} is not pushed yet; approve it first")
        subprocess.run([gh, "repo", "edit", run["repo_url"], "--visibility", "public",
                        "--accept-visibility-change-consequences"], check=True, capture_output=True, text=True)
        with connect() as conn:
            refresh_board(conn)  # the Project's Repo field and README follow
        return run["repo_url"]
    if run["repo_url"]:
        return run["repo_url"]
    card = load_card(run["card_id"])
    p = subprocess.run(
        [gh, "repo", "create", repo_name(repo_dir), "--private", "--source", repo_dir, "--push",
         "--description", f"Skunkworks Sloth prototype: {card.title}"[:300]],
        check=True, capture_output=True, text=True)
    url = next((w for w in (p.stdout + p.stderr).split() if w.startswith("https://github.com/")), None)
    if not url:
        url = json.loads(subprocess.run([gh, "repo", "view", repo_name(repo_dir), "--json", "url"],
                                        check=True, capture_output=True, text=True).stdout)["url"]
    url = url.rstrip(".")
    with connect() as conn:
        conn.execute("UPDATE runs SET approved = true, repo_url = %s WHERE id = %s", (url, run_id))
        conn.commit()
        refresh_board(conn)
    return url
