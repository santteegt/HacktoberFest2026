"""Lane 3 commands: `sloth work`, `sloth approve`, `sloth browser test`."""

from __future__ import annotations

import json
from pathlib import Path

import typer

browser_app = typer.Typer(no_args_is_help=True, help="Stagehand on a local Chrome with the local Gemma model.")


def work(
    card_id: str = typer.Argument(..., help="Card to build (its column should be 'today')."),
    model: str = typer.Option(None, help="OpenRouter model id; default llm.openrouter_model."),
    box_minutes: int = typer.Option(None, help="Override the card's box (minutes)."),
    card_file: Path = typer.Option(None, help="Load the card from JSON and upsert it (fixtures, tests)."),
    as_json: bool = typer.Option(False, "--json", help="Print the full result as JSON."),
) -> None:
    """Build a card inside its box: repo from the template, Worker run, tests, NOTES.md, runs row."""
    from ..builder import approval, runs, worker
    from ..core import notify
    from ..core.config import settings
    from ..core.models import Card

    if card_file:
        card = Card.model_validate_json(card_file.read_text())
        if card.id != card_id:
            raise typer.BadParameter(f"{card_file} holds card {card.id}, not {card_id}")
        runs.upsert_card(card)
    card = runs.load_card(card_id)
    use_model = model or settings().openrouter_model
    if not use_model:
        raise typer.BadParameter("no model: set llm.openrouter_model or pass --model")
    box = box_minutes or card.box_minutes
    run_id = runs.start_run(card.id, use_model)
    notify.post("worker", f"🦥 Box started for **{card.title}** (card `{card.id}`, run {run_id}): "
                          f"{box} min, `{use_model}`.")
    notify.log("worker", "box_start", f"card {card.id} → Building, run {run_id}, {box} min, {use_model}",
               {"run_id": run_id, "card_id": card.id, "model": use_model})
    try:
        r = worker.run_box(card, links=runs.card_links(card), model=use_model, box_minutes=box)
    except BaseException:
        runs.finish_run(run_id, outcome=worker.Outcome.killed, cost_usd=None, tokens_in=None,
                        tokens_out=None, repo_dir="", notes_path="")
        raise
    runs.finish_run(run_id, outcome=r.outcome, cost_usd=r.cost_usd, tokens_in=r.tokens_in,
                    tokens_out=r.tokens_out, repo_dir=r.repo_dir, notes_path=str(Path(r.repo_dir) / "NOTES.md"))
    text = worker.summary_text(r, card, run_id)
    notify.post("worker", text)
    req = approval.approval_request(run_id, card.title, r.repo_dir, tests_passed=r.tests_passed)
    notify.post("worker", req["text"] + "\n" + " · ".join(
        f"[{b['label']}]" + (f" → `{b['command']}`" if b["command"] else "") for b in req["buttons"]))
    cost = f"${r.cost_usd:.4f}" if r.cost_usd is not None else "cost unknown"
    notify.log("worker", "box_end", f"card {card.id} run {run_id} {r.outcome}, tests "
               f"{'pass' if r.tests_passed else 'fail'}, {r.minutes:.0f} min, {cost}, {r.model}",
               {"run_id": run_id, "outcome": str(r.outcome), "cost_usd": r.cost_usd})
    print(r.to_json() if as_json else text)


def approve(
    run_id: int = typer.Argument(..., help="Run to publish."),
    public: bool = typer.Option(False, "--public", help="Second tap: flip an approved repo to public."),
) -> None:
    """The author's tap: push the run's repo to a private GitHub repo (or make it public)."""
    from ..builder import approval, runs
    from ..core import notify

    run = runs.get_run(run_id)
    card = runs.load_card(run["card_id"])
    url = runs.approve(run_id, make_public=public)
    if public:
        notify.post("worker", f"🌍 **{card.title}** is public: {url}")
        notify.log("worker", "repo_public", f"card {card.id} run {run_id} repo public {url}", {"run_id": run_id})
    else:
        req = approval.publish_request(run_id, card.title, url)
        notify.post("worker", req["text"])
        notify.log("worker", "repo_pushed", f"card {card.id} → Built, run {run_id}, private repo {url}",
                   {"run_id": run_id, "repo_url": url})
    print(url)


@browser_app.command("test")
def browser_test(url: str, timeout_s: int = typer.Option(45, help="Per-URL timeout."),
                 headless: bool = typer.Option(False, help="Headless (x.com refuses it).")) -> None:
    """Extract one URL with Stagehand + local Gemma and print the result."""
    import asyncio

    from ..builder import browser

    async def go():
        async with browser.session(headless=headless) as sh:
            return await browser.extract_with_reason(sh, url, timeout_s=timeout_s)

    result, why = asyncio.run(go())
    print(json.dumps({"ok": result is not None, "reason": why,
                      "extract": result.model_dump() if result else None}, indent=1, ensure_ascii=False))
    raise typer.Exit(0 if result else 1)


def register(app: typer.Typer) -> None:
    app.command("work")(work)
    app.command("approve")(approve)
    app.add_typer(browser_app, name="browser")
