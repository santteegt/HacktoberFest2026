"""`sloth brain`: render the second brain (OKF-style markdown) from cards, runs and NOTES.md.

brain/index.md, brain/verticals/<vertical>.md, brain/cards/<card-id>.md (built cards only).
Every page has OKF frontmatter (type, title, description, tags, timestamp). Generated only.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from ..core.config import ROOT
from ..core.models import Column
from . import store
from .focus import NAMES, current_focus, describe
from .markdown import card_markdown

BRAIN_DIR = Path(os.environ.get("SLOTH_BRAIN_DIR", ROOT / "brain"))
NOTES_MAX_CHARS = 12000


def _fm(type_: str, title: str, description: str, tags: list[str], stamp: str) -> str:
    esc = lambda s: s.replace('"', "'")  # noqa: E731
    return "\n".join(["---", f"type: {type_}", f'title: "{esc(title)}"', f'description: "{esc(description)}"',
                      f"tags: [{', '.join(tags)}]", f'timestamp: "{stamp}"', "---", ""])


def notes_for(run: dict | None) -> tuple[str | None, Path | None]:
    """NOTES.md text from the run's notes_path (absolute, or relative to repo_dir)."""
    if not run:
        return None, None
    candidates = []
    if run.get("notes_path"):
        p = Path(os.path.expanduser(run["notes_path"]))
        candidates.append(p if p.is_absolute() else Path(run.get("repo_dir") or "") / p)
    if run.get("repo_dir"):
        candidates.append(Path(os.path.expanduser(run["repo_dir"])) / "NOTES.md")
    for p in candidates:
        if p.is_file():
            return p.read_text(errors="replace")[:NOTES_MAX_CHARS], p
    return None, None


def _demote(md: str) -> str:
    """Push NOTES.md headings one level down so they sit under the page's sections."""
    return "\n".join("#" + line if line.startswith("#") else line for line in md.splitlines())


def card_page(card: dict, links: dict, run: dict | None, all_runs: list[dict], stamp: str) -> str:
    notes, path = notes_for(run)
    total = sum(float(r["cost_usd"] or 0) for r in all_runs)
    desc = f"Prototype from {len(card['link_ids'])} saved links ({card['vertical']}); {card['column']}."
    out = [_fm("prototype", card["title"], desc, [card["vertical"], card["column"], "skunkworks"], stamp),
           f"# {card['title']}", "",
           f"Vertical: [{NAMES.get(card['vertical'], card['vertical'])}](../verticals/{card['vertical']}.md) · "
           f"[index](../index.md)", "",
           card_markdown(card, links, run, frontmatter=False).rstrip(), "",
           "## Runs", ""]
    for r in all_runs:
        took = ""
        if r.get("ended_at") and r.get("started_at"):
            took = f", {int((r['ended_at'] - r['started_at']).total_seconds() // 60)} min"
        cost = f", ${float(r['cost_usd']):.2f}" if r.get("cost_usd") is not None else ""
        out.append(f"- {r['started_at']:%Y-%m-%d %H:%M} UTC: {r['outcome']}{took}{cost}"
                   + (f", `{r['model_id']}`" if r.get("model_id") else ""))
    out.append(f"- Total cost: ${total:.2f}")
    out += ["", "## Notes", ""]
    out.append(_demote(notes).strip() if notes else "_No NOTES.md found for this run yet._")
    if path:
        out += ["", f"_From `{path}`._"]
    return "\n".join(out).rstrip() + "\n"


def render(conn, brain_dir: Path | None = None) -> dict:
    brain_dir = brain_dir or BRAIN_DIR
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    cards = store.all_cards(conn)
    latest = store.latest_runs(conn)
    links = store.links_by_id(conn, sorted({i for c in cards for i in c["link_ids"]}))
    built = [c for c in cards if c["column"] == Column.built]
    (brain_dir / "cards").mkdir(parents=True, exist_ok=True)
    (brain_dir / "verticals").mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in (brain_dir / "cards").glob("*.md")}
    new_pages = []
    for c in built:
        page = brain_dir / "cards" / f"{c['id']}.md"
        page.write_text(card_page(c, links, latest.get(c["id"]), store.runs_for(conn, c["id"]), stamp))
        if c["id"] not in existing:
            new_pages.append(str(page.relative_to(brain_dir.parent)))
    for stale in existing - {c["id"] for c in built}:
        (brain_dir / "cards" / f"{stale}.md").unlink()

    by_vertical: dict[str, list[dict]] = {}
    for c in cards:
        by_vertical.setdefault(c["vertical"], []).append(c)
    for v, vcards in sorted(by_vertical.items()):
        name = NAMES.get(v, v)
        n_built = sum(c["column"] == Column.built for c in vcards)
        lines = [_fm("topic", name, f"{len(vcards)} cards, {n_built} built, from the Reading List.",
                     [v, "vertical"], stamp), f"# {name}", "", "[index](../index.md)", ""]
        for col in Column:
            group = [c for c in vcards if c["column"] == col]
            if not group:
                continue
            lines += [f"## {col.value.capitalize()}", ""]
            for c in group:
                target = f"../cards/{c['id']}.md" if col == Column.built else f"../../board/{col.value}/{c['id']}.md"
                lines.append(f"- [{c['title']}]({target}) `{c['id']}`: {c.get('learning_goal') or ''}")
            lines.append("")
        (brain_dir / "verticals" / f"{v}.md").write_text("\n".join(lines).rstrip() + "\n")
    for stale in {p.stem for p in (brain_dir / "verticals").glob("*.md")} - set(by_vertical):
        (brain_dir / "verticals" / f"{stale}.md").unlink()

    cost = conn.execute("SELECT coalesce(sum(cost_usd), 0) AS s FROM runs").fetchone()["s"]
    idx = [_fm("index", "Skunkworks Sloth second brain",
               "What got built from the Reading List, by vertical. Generated by `sloth brain`.",
               ["index", "skunkworks"], stamp),
           "# Skunkworks Sloth second brain", "",
           f"{len(cards)} cards · {len(built)} built · Worker cost ${float(cost):.2f} · "
           f"focus: {describe(current_focus(conn))}", "", "## Built", ""]
    idx += [f"- [{c['title']}](cards/{c['id']}.md) ({NAMES.get(c['vertical'], c['vertical'])})"
            for c in built] or ["_Nothing built yet._"]
    idx += ["", "## Verticals", ""]
    idx += [f"- [{NAMES.get(v, v)}](verticals/{v}.md): {len(vc)} card{'s' if len(vc) != 1 else ''}" for v, vc in sorted(by_vertical.items())]
    (brain_dir / "index.md").write_text("\n".join(idx).rstrip() + "\n")

    if new_pages:
        from ..core import notify
        for p in new_pages:
            notify.log("coordinator", "brain", f"new brain page {p}", {"page": p})
    pages = 1 + len(by_vertical) + len(built)
    return {"ok": True, "pages": pages, "new_pages": new_pages,
            "reply": f"Second brain updated: {pages} pages, {len(built)} built prototype{'s' if len(built) != 1 else ''}."}
