"""Card builder and moves. Postgres is the source of truth; board files follow it."""

from __future__ import annotations

from datetime import date

from ..core.models import Card, Column, Vertical
from . import store
from .cluster import card_id, cluster
from .markdown import write_card_file
from .wording import box_minutes, kill_criteria, word_card


def build(conn, *, use_model: bool = True, limit: int | None = None,
          on_card=None) -> list[tuple[Card, dict]]:
    """Cluster kept links that are on no live card, word each cluster, insert as backlog."""
    links = store.kept_links(conn)
    clusters = cluster(links)
    if limit is not None:
        clusters = clusters[:limit]
    taken = store.card_ids(conn)
    box = box_minutes()
    made = []
    for group in clusters:
        vertical = group[0].vertical
        wording, trace = word_card(group, vertical, box=box, use_model=use_model)
        ids = [link.link_id for link in group]
        card = Card(id=card_id(ids, taken), title=wording.title, vertical=Vertical(vertical),
                    learning_goal=wording.learning_goal, hypothesis=wording.hypothesis,
                    done_means=wording.done_means, box_minutes=box, link_ids=ids,
                    kill_criteria=kill_criteria(box), column=Column.backlog)
        taken.add(card.id)
        store.insert_card(conn, card)
        conn.commit()
        made.append((card, trace))
        if on_card:
            on_card(card, trace)
    render_all(conn)
    return made


def column_from_run(current: str, run: dict | None) -> str:
    """Where the Builder's latest run puts a card. Archived cards stay archived."""
    if not run or current == Column.archived:
        return current
    outcome = run["outcome"]
    if outcome == "building":
        return Column.building if current in (Column.backlog, Column.today, Column.building) else current
    if outcome == "done":
        return Column.built if run.get("approved") else Column.building
    if outcome in ("boxed_out", "killed"):
        return Column.killed
    return current


def apply_runs(conn) -> list[tuple[str, str, str]]:
    """Move cards to follow their latest run. Returns (card_id, from, to) for each move."""
    runs = store.latest_runs(conn)
    moves = []
    for card in store.all_cards(conn):
        new = column_from_run(card["column"], runs.get(card["id"]))
        if new != card["column"]:
            store.move_card(conn, card["id"], Column(new))
            moves.append((card["id"], card["column"], str(new)))
    conn.commit()
    return moves


def pick(conn, card_id: str, *, today: date) -> list[str]:
    """Move one backlog card to `today`. A previous unstarted `today` card goes back to backlog."""
    card = store.get_card(conn, card_id)
    if not card:
        raise KeyError(f"no card {card_id}")
    if card["column"] not in (Column.backlog, Column.today):
        raise ValueError(f"card {card_id} is {card['column']}, only backlog cards can be picked")
    returned = []
    for other in store.all_cards(conn, (Column.today.value,)):
        if other["id"] != card_id:
            store.move_card(conn, other["id"], Column.backlog)
            returned.append(other["id"])
    store.move_card(conn, card_id, Column.today, picked_on=today)
    conn.commit()
    render_all(conn)
    return returned


def render_all(conn) -> int:
    cards = store.all_cards(conn)
    runs = store.latest_runs(conn)
    links = store.links_by_id(conn, sorted({i for c in cards for i in c["link_ids"]}))
    for card in cards:
        write_card_file(card, links, runs.get(card["id"]))
    return len(cards)


def refresh(conn, *, prune: bool = False, readme: bool = True) -> dict:
    """Everything that follows a move: run rows → columns, board files, brain, GitHub Project.

    The Project part is skipped (markdown-only fallback) when `sloth board init` never ran, and a
    GitHub failure is reported, not raised, so a move is never lost to the network.
    """
    from . import brain, github
    moves = apply_runs(conn)
    render_all(conn)
    out = {"moves_from_runs": moves, "files": True}
    if any(to == Column.built for _, _, to in moves) or brain.BRAIN_DIR.joinpath("index.md").exists():
        out["brain"] = brain.render(conn)["pages"]
    if github.configured():
        try:
            out["project"] = github.sync(prune=prune, readme=readme, conn=conn, apply=False)
        except Exception as e:  # noqa: BLE001
            out["project"] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}
    else:
        out["project"] = "not configured (markdown only)"
    return out
