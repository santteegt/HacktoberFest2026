"""Card markdown: the `board/<column>/<id>.md` files and the GitHub Project item body."""

from __future__ import annotations

import os
from pathlib import Path

from ..core.config import ROOT
from ..core.models import Column

BOARD_DIR = Path(os.environ.get("SLOTH_BOARD_DIR", ROOT / "board"))


def _d(value) -> str:
    return value.strftime("%Y-%m-%d") if value else "?"


def card_markdown(card: dict, links: dict[int, dict], run: dict | None = None,
                  *, frontmatter: bool = True) -> str:
    lines = []
    if frontmatter:
        lines += ["---", f"id: {card['id']}", f"column: {card['column']}",
                  f"vertical: {card['vertical']}", f"box_minutes: {card['box_minutes']}",
                  f"picked_on: {_d(card.get('picked_on')) if card.get('picked_on') else ''}",
                  f"links: {len(card['link_ids'])}", "---", "", f"# {card['title']}", ""]
    lines += [
        f"**Card** `{card['id']}` · **Vertical** {card['vertical']} · **Box** {card['box_minutes']} min"
        + (f" · **Picked** {_d(card['picked_on'])}" if card.get("picked_on") else ""),
        "",
        f"**Learning goal.** {card.get('learning_goal') or ''}",
        "",
        f"**Hypothesis.** {card.get('hypothesis') or ''}",
        "",
        f"**Done means.** {card.get('done_means') or ''}",
        "",
        f"**Kill criteria.** {card.get('kill_criteria') or ''}",
        "",
        "## Links",
        "",
    ]
    for lid in card["link_ids"]:
        link = links.get(lid)
        if not link:
            lines.append(f"- link {lid} (missing)")
            continue
        idea = f" — {link['one_line_idea']}" if link.get("one_line_idea") else ""
        lines.append(f"- [{link.get('title') or link['url']}]({link['url']}) "
                     f"(saved {_d(link.get('saved_at'))}){idea}")
    if run:
        lines += ["", "## Run", ""]
        lines.append(f"- Outcome: {run['outcome']}" + (" (approved)" if run.get("approved") else ""))
        if run.get("model_id"):
            lines.append(f"- Model: `{run['model_id']}`")
        if run.get("cost_usd") is not None:
            lines.append(f"- Cost: ${float(run['cost_usd']):.2f}")
        if run.get("repo_url"):
            lines.append(f"- Repo: {run['repo_url']}")
        if run.get("notes_path"):
            notes = run["notes_path"]
            if run.get("repo_url") and not notes.startswith(("http", "/")):
                notes = f"{run['repo_url'].rstrip('/')}/blob/HEAD/{notes}"
            lines.append(f"- Notes: {notes}")
    return "\n".join(lines).rstrip() + "\n"


def write_card_file(card: dict, links: dict[int, dict], run: dict | None = None,
                    board_dir: Path | None = None) -> Path:
    """Write the card under its column and remove copies left in other columns."""
    board_dir = board_dir or BOARD_DIR
    target = board_dir / card["column"] / f"{card['id']}.md"
    for col in Column:
        stale = board_dir / col.value / f"{card['id']}.md"
        if stale != target and stale.exists():
            stale.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(card_markdown(card, links, run))
    return target
