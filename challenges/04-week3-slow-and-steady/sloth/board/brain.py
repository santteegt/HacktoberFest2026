"""`sloth brain`: render the second brain (OKF-style markdown) from cards, runs and NOTES.md.

brain/index.md, brain/verticals/<vertical>.md, brain/cards/<card-id>.md (built cards only),
brain/reading/<YYYY-MM-DD>.md per daily reading pick (`-2`, `-3` for extra picks that day) and
brain/reading/index.md, newest first. Every page has OKF frontmatter (type, title, description, tags, timestamp). Generated only.
"""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path

from ..core.config import ROOT
from ..core.models import Column
from . import store
from .focus import NAMES, current_focus, describe
from .markdown import card_markdown

BRAIN_DIR = Path(os.environ.get("SLOTH_BRAIN_DIR", ROOT / "brain"))
NOTES_MAX_CHARS = 12000
EXCERPT_CHARS = 600


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


def reading_picks(conn) -> list[dict]:
    """Every recorded reading pick with its link, oldest first, plus its page name."""
    rows = conn.execute(
        """
        WITH latest AS (SELECT DISTINCT ON (link_id) * FROM triage ORDER BY link_id, created_at DESC)
        SELECT r.id, r.link_id, r.picked_on, r.extra, coalesce(r.vertical, t.vertical, 'other') AS vertical,
               r.why, r.created_at, l.title, coalesce(e.final_url, l.url) AS url, l.saved_at,
               left(e.readable_text, 4000) AS readable_text, t.topic
        FROM reading_picks r JOIN links l ON l.id = r.link_id
        LEFT JOIN enrichment e ON e.link_id = l.id LEFT JOIN latest t ON t.link_id = l.id
        ORDER BY r.picked_on, r.extra, r.created_at, r.id
        """).fetchall()
    per_day: dict = {}
    for r in rows:
        n = per_day[r["picked_on"]] = per_day.get(r["picked_on"], 0) + 1
        r["page"] = f"{r['picked_on']:%Y-%m-%d}" + (f"-{n}" if n > 1 else "")
    return rows


def excerpt(text: str | None, n: int = EXCERPT_CHARS) -> str:
    """First n characters of the readable text, whitespace folded, cut at a word."""
    flat = re.sub(r"\s+", " ", text or "").strip()
    if len(flat) <= n:
        return flat
    cut = flat[:n].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def reading_page(r: dict, built_same_vertical: list[dict], stamp: str) -> str:
    v = r["vertical"]
    name = NAMES.get(v, v)
    title = r["title"] or r["url"]
    saved = f"{r['saved_at']:%Y-%m-%d}" if r.get("saved_at") else "?"
    out = [_fm("reading", title, (r["why"] or f"Daily reading for {r['picked_on']:%Y-%m-%d}.")[:200],
               [v, "reading", "daily"], stamp),
           f"# {title}", "",
           f"Daily reading for {r['picked_on']:%Y-%m-%d}" + (" (extra pick)" if r["extra"] else "")
           + f" · [{name}](../verticals/{v}.md) · [all readings](index.md) · [brain index](../index.md)", "",
           f"- Link: {r['url']}", f"- Vertical: {name}", f"- Saved: {saved}", "",
           "## Why today", "", (r["why"] or "_No reason recorded._").strip(), "",
           "## Excerpt", ""]
    text = excerpt(r.get("readable_text"))
    out.append(f"> {text}" if text else "_Only the title was readable for this link._")
    out += ["", f"## Built in {name}", ""]
    out += [f"- [{c['title']}](../cards/{c['id']}.md)" for c in built_same_vertical] or [
        "_Nothing built in this vertical yet._"]
    return "\n".join(out).rstrip() + "\n"


def render_reading(conn, brain_dir: Path, built: list[dict], stamp: str) -> tuple[list[dict], list[str]]:
    """Write brain/reading/*. Returns the picks and the pages that are new."""
    picks = reading_picks(conn)
    folder = brain_dir / "reading"
    folder.mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in folder.glob("*.md")} - {"index"}
    new = []
    for r in picks:
        same = [c for c in built if c["vertical"] == r["vertical"]]
        (folder / f"{r['page']}.md").write_text(reading_page(r, same, stamp))
        if r["page"] not in existing:
            new.append(f"{brain_dir.name}/reading/{r['page']}.md")
    for stale in existing - {r["page"] for r in picks}:
        (folder / f"{stale}.md").unlink()
    lines = [_fm("index", "Daily reading", "Every daily reading recommendation, newest first.",
                 ["reading", "index"], stamp), "# Daily reading", "", "[brain index](../index.md)", ""]
    lines += [f"- {r['picked_on']:%Y-%m-%d}: [{r['title'] or r['url']}]({r['page']}.md) "
              f"({NAMES.get(r['vertical'], r['vertical'])})" + (" · extra" if r["extra"] else "")
              for r in reversed(picks)] or ["_No readings recommended yet._"]
    (folder / "index.md").write_text("\n".join(lines).rstrip() + "\n")
    return picks, new


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

    picks, new_reading = render_reading(conn, brain_dir, built, stamp)
    new_pages += new_reading
    by_vertical: dict[str, list[dict]] = {}
    for c in cards:
        by_vertical.setdefault(c["vertical"], []).append(c)
    for r in picks:
        by_vertical.setdefault(r["vertical"], [])
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
        vreads = [r for r in reversed(picks) if r["vertical"] == v]
        if vreads:
            lines += ["## Daily reading", "", "[all readings](../reading/index.md)", ""]
            lines += [f"- {r['picked_on']:%Y-%m-%d}: [{r['title'] or r['url']}](../reading/{r['page']}.md)"
                      for r in vreads]
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
    idx += ["", "## Daily reading", "", f"[All {len(picks)} readings](reading/index.md)", ""]
    idx += [f"- {r['picked_on']:%Y-%m-%d}: [{r['title'] or r['url']}](reading/{r['page']}.md)"
            for r in list(reversed(picks))[:5]] or ["_No readings recommended yet._"]
    idx += ["", "## Verticals", ""]
    idx += [f"- [{NAMES.get(v, v)}](verticals/{v}.md): {len(vc)} card{'s' if len(vc) != 1 else ''}" for v, vc in sorted(by_vertical.items())]
    (brain_dir / "index.md").write_text("\n".join(idx).rstrip() + "\n")

    if new_pages:
        from ..core import notify
        for p in new_pages:
            notify.log("coordinator", "brain", f"new brain page {p}", {"page": p})
    pages = 1 + len(by_vertical) + len(built) + 1 + len(picks)
    return {"ok": True, "pages": pages, "new_pages": new_pages,
            "reply": f"Second brain updated: {pages} pages, {len(built)} built prototype{'s' if len(built) != 1 else ''}."}
