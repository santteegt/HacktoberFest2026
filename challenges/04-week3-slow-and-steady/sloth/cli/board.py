"""Board lane CLI: `sloth board ...`, `sloth focus`, `sloth pick ...`, `sloth brain`.

Commands the Coordinator agent runs take `--json` and print one object
`{"ok", "reply", "action", ...}`: `reply` is sent verbatim, `action` is the next step.
"""

from __future__ import annotations

import json
from typing import Annotated

import typer

board_app = typer.Typer(no_args_is_help=True, help="Skunkworks board: cards, files, GitHub Project.")
pick_app = typer.Typer(no_args_is_help=True, help="Daily pick: options and choice.")


def _out(obj: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, default=str, ensure_ascii=False))
    else:
        print(obj.get("reply") or json.dumps(obj, default=str, indent=1))


@board_app.command("seed-fixtures")
def seed_fixtures(allow_public: Annotated[bool, typer.Option(help="Seed into public (never in lanes).")] = False) -> None:
    """Load tests/fixtures/links.json + triage.json into the current schema."""
    from ..board.fixtures import seed
    from ..core.db import connect
    with connect() as conn:
        print(seed(conn, allow_public=allow_public))


@board_app.command("build")
def build(no_model: Annotated[bool, typer.Option("--no-model", help="Code wording only.")] = False,
          limit: Annotated[int | None, typer.Option(help="At most N new cards.")] = None,
          sync: Annotated[bool, typer.Option(help="Sync the GitHub Project afterwards.")] = True,
          as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Cluster kept links into new backlog cards (model words them), write board files."""
    from ..board import cards
    from ..core import notify
    from ..core.db import connect

    def show(card, trace):
        if not as_json:
            tag = "fallback" if trace["fallback"] else f"{trace['ms']}ms"
            print(f"+ {card.id} [{card.vertical}] {card.title} ({len(card.link_ids)} links, {tag})")

    with connect() as conn:
        made = cards.build(conn, use_model=not no_model, limit=limit, on_card=show)
    if made:
        notify.log("coordinator", "cards", f"{len(made)} new cards in backlog",
                   {"cards": [c.id for c, _ in made]})
    synced = _sync_quiet() if (sync and made) else None
    _out({"ok": True, "new_cards": [c.id for c, _ in made], "synced": synced,
          "fallbacks": sum(t["fallback"] for _, t in made),
          "reply": f"{len(made)} new cards in the backlog."}, as_json)


def _sync_quiet():
    """Refresh after a move; never fails the move (GitHub errors are reported in the result)."""
    from ..board.cards import refresh
    from ..core.db import connect
    with connect() as conn:
        return refresh(conn)


@board_app.command("show")
def show_board() -> None:
    """Print the board by column."""
    from ..board import store
    from ..core.db import connect
    with connect() as conn:
        for card in store.all_cards(conn):
            print(f"{card['column']:<9} {card['id']:<7} {card['vertical']:<17} {card['title']}")


@board_app.command("render")
def render() -> None:
    """Rewrite every board/<column>/<id>.md from the database."""
    from ..board.cards import render_all
    from ..core.db import connect
    with connect() as conn:
        print(f"{render_all(conn)} card files written")


@board_app.command("init")
def init() -> None:
    """Create the private GitHub Project "Skunkworks Sloth" with its fields (once)."""
    from ..board import github
    print(json.dumps(github.init(), indent=1))


@board_app.command("sync")
def sync(prune: Annotated[bool, typer.Option(help="Delete Project items whose Card ID is not in the DB.")] = False,
         readme: Annotated[bool, typer.Option(help="Refresh the Project README status block.")] = True) -> None:
    """Apply run rows, rewrite board files and brain, mirror to the GitHub Project (idempotent)."""
    from ..board.cards import refresh
    from ..core.db import connect
    with connect() as conn:
        print(json.dumps(refresh(conn, prune=prune, readme=readme), indent=1, default=str))


@pick_app.command("options")
def pick_options(n: Annotated[int, typer.Option(min=2, max=4)] = 4,
                 no_model: Annotated[bool, typer.Option("--no-model")] = False,
                 as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Score backlog cards (code) and word 3-4 options (model) for the daily pick."""
    from ..board import pick
    from ..core.db import connect
    with connect() as conn:
        _out(pick.options_payload(conn, n=n, use_model=not no_model), as_json)


@pick_app.command("choose")
def pick_choose(choice: Annotated[str, typer.Argument(help="Card id, or the tapped option label.")],
                as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Move the chosen card to Today, set picked_on, sync the Project, ping #worker."""
    from ..board import pick
    from ..core.db import connect
    with connect() as conn:
        result = pick.choose(conn, choice)
    if result["ok"]:
        result["synced"] = _sync_quiet()
    _out(result, as_json)


def focus(text: Annotated[str | None, typer.Argument(help="The author's answer, in their words.")] = None,
          weights: Annotated[str | None, typer.Option(help="Direct weights: ai-agents=1,rust=0.5")] = None,
          show: Annotated[bool, typer.Option(help="Print the current focus.")] = False,
          question: Annotated[bool, typer.Option(help="Print the weekly focus question.")] = False,
          no_model: Annotated[bool, typer.Option("--no-model")] = False,
          as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Store this week's focus as weights on verticals (or show it / the question)."""
    from ..board import focus as f
    from ..core.db import connect
    with connect() as conn:
        if question:
            _out(f.question_payload(conn), as_json)
        elif show or (text is None and weights is None):
            _out(f.show_payload(conn), as_json)
        else:
            _out(f.set_focus(conn, text=text, weights=weights, use_model=not no_model), as_json)


def brain(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Render brain/ (index, one page per vertical, one per built card) from the database."""
    from ..board import brain as b
    from ..core.db import connect
    with connect() as conn:
        _out(b.render(conn), as_json)


def register(app: typer.Typer) -> None:
    app.add_typer(board_app, name="board")
    app.add_typer(pick_app, name="pick")
    app.command("focus")(focus)
    app.command("brain")(brain)
