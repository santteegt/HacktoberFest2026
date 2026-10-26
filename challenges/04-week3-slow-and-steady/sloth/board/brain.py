"""`sloth brain`: render the second brain as an Obsidian vault (OKF-style frontmatter).

brain/ is the vault. Notes are named by human titles and linked with `[[wikilinks]]`, never
by paths outside the vault:

  index.md                     verticals, latest readings, built prototypes
  verticals/<Vertical>.md      → its subtopics
  topics/<Subtopic>.md         → its vertical, cards, readings, related subtopics
  cards/<Card title>.md        → its topic and vertical; source links as plain URLs; card id in
                                 frontmatter `card_id` and `aliases`, never in the filename
  prototypes/<Title> (prototype).md   built cards: repo, model, cost, runs, NOTES.md
  readings/<YYYY-MM-DD> <Title>.md    daily reading picks → topic and vertical

Tags are nested (`type/…`, `vertical/…`, `topic/…`, `status/…`) in frontmatter and inline, and
`.obsidian/graph.json` gets one colour group per note type. Generated only: every render
rewrites these folders.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from ..core.config import ROOT
from ..core.models import Column
from . import store, taxonomy
from .focus import NAMES, current_focus, describe

BRAIN_DIR = Path(os.environ.get("SLOTH_BRAIN_DIR", ROOT / "brain"))
NOTES_MAX_CHARS = 12000
EXCERPT_CHARS = 600
FOLDERS = ("verticals", "topics", "cards", "prototypes", "readings")
OLD_FOLDERS = ("reading",)  # earlier layout, removed on render
TYPE_COLORS = {  # graph colour groups (Obsidian stores RGB as an int)
    "vertical": 0xE8590C, "topic": 0x1971C2, "card": 0x2F9E44, "prototype": 0xF08C00, "reading": 0x9C36B5,
}
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


# ------------------------------------------------------------------ helpers (pure)

def safe_name(text: str, limit: int = 90) -> str:
    """A filename and wikilink target: no path or link characters, trimmed."""
    clean = re.sub(r'[\\/:*?"<>|#^\[\]]+', " ", text or "")
    clean = re.sub(r"\s+", " ", clean).strip(" .")
    if len(clean) > limit:
        clean = clean[:limit].rsplit(" ", 1)[0].rstrip(" .,;-")
    return clean or "Untitled"


class Names:
    """Unique note names across the whole vault (Obsidian resolves [[X]] by basename)."""

    def __init__(self):
        self.taken: set[str] = {"index"}

    def claim(self, wanted: str, qualifier: str = "") -> str:
        name = safe_name(wanted)
        if name.lower() in self.taken and qualifier:
            name = safe_name(f"{name} ({qualifier})")
        base, n = name, 2
        while name.lower() in self.taken:
            name, n = f"{base} ({n})", n + 1
        self.taken.add(name.lower())
        return name


def tag(kind: str, value: str) -> str:
    return f"{kind}/{taxonomy.slug(value)}"


def frontmatter(type_: str, title: str, description: str, tags: list[str], stamp: str, **extra) -> str:
    def q(s) -> str:
        return json.dumps(str(s), ensure_ascii=False)
    lines = ["---", f"type: {type_}", f"title: {q(title)}", f"description: {q((description or '')[:200])}",
             f"tags: [{', '.join(tags)}]", f"timestamp: {q(stamp)}"]
    for k, v in extra.items():
        lines.append(f"{k}: [{', '.join(q(x) for x in v)}]" if isinstance(v, list) else f"{k}: {q(v)}")
    return "\n".join(lines + ["---", ""])


def inline_tags(tags: list[str]) -> str:
    return " ".join(f"#{t}" for t in tags)


def wl(name: str) -> str:
    return f"[[{name}]]"


def excerpt(text: str | None, n: int = EXCERPT_CHARS) -> str:
    """First n characters of the readable text, whitespace folded, cut at a word."""
    flat = re.sub(r"\s+", " ", text or "").strip()
    if len(flat) <= n:
        return flat
    return flat[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


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
    """Push NOTES.md headings two levels down so they sit under the page's sections."""
    return "\n".join("##" + line if line.startswith("#") else line for line in md.splitlines())


def _d(value) -> str:
    return value.strftime("%Y-%m-%d") if value else "?"


# ------------------------------------------------------------------ data

def reading_picks(conn) -> list[dict]:
    return conn.execute(
        """
        WITH latest AS (SELECT DISTINCT ON (link_id) * FROM triage ORDER BY link_id, created_at DESC)
        SELECT r.id, r.link_id, r.picked_on, r.extra, coalesce(r.vertical, t.vertical, 'other') AS vertical,
               r.why, r.created_at, l.title, coalesce(e.final_url, l.url) AS url, l.saved_at,
               left(e.readable_text, 4000) AS readable_text, t.topic
        FROM reading_picks r JOIN links l ON l.id = r.link_id
        LEFT JOIN enrichment e ON e.link_id = l.id LEFT JOIN latest t ON t.link_id = l.id
        ORDER BY r.picked_on, r.extra, r.created_at, r.id
        """).fetchall()


def pile_counts(conn, tax: dict) -> dict[str, int]:
    """Reading-bucket links per subtopic (shown as a count, not as notes)."""
    rows = conn.execute("SELECT id FROM links WHERE status = 'reading'").fetchall()
    out: dict[str, int] = {}
    for r in rows:
        s = tax["links"].get(str(r["id"]))
        if s:
            out[s] = out.get(s, 0) + 1
    return out


# ------------------------------------------------------------------ render

def render(conn, brain_dir: Path | None = None, *, retaxonomy: bool = False,
           embed="default", namer=None) -> dict:
    brain_dir = brain_dir or BRAIN_DIR
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    tax = taxonomy.ensure(conn, retaxonomy=retaxonomy,
                          embed=taxonomy.embed_ollama if embed == "default" else embed,
                          namer=namer or taxonomy.name_subtopics)
    subs = taxonomy.subtopics(tax)
    cards = store.all_cards(conn)
    latest = store.latest_runs(conn)
    links = store.links_by_id(conn, sorted({i for c in cards for i in c["link_ids"]}))
    picks = reading_picks(conn)
    pile = pile_counts(conn, tax)
    rel = taxonomy.related(tax, cards)

    previous = {p.relative_to(brain_dir).as_posix() for f in FOLDERS if (brain_dir / f).is_dir()
                for p in (brain_dir / f).glob("*.md")}
    for f in FOLDERS + OLD_FOLDERS:
        shutil.rmtree(brain_dir / f, ignore_errors=True)
        if f in FOLDERS:
            (brain_dir / f).mkdir(parents=True, exist_ok=True)

    # names first, so every link can be written as a wikilink to a note that exists
    names = Names()
    verticals = sorted({s["vertical"] for s in subs.values()} | {c["vertical"] for c in cards}
                       | {r["vertical"] for r in picks})
    v_name = {v: names.claim(NAMES.get(v, v)) for v in verticals}
    t_name = {sl: names.claim(s["name"], NAMES.get(s["vertical"], s["vertical"])) for sl, s in sorted(subs.items())}
    card_topic = {c["id"]: taxonomy.card_subtopic(c, tax) for c in cards}
    c_name = {c["id"]: names.claim(c["title"]) for c in cards}
    built = [c for c in cards if c["column"] == Column.built]
    p_name = {c["id"]: names.claim(f"{c['title']} (prototype)") for c in built}
    pick_topic = {r["id"]: tax["links"].get(str(r["link_id"])) for r in picks}
    r_name = {r["id"]: names.claim(f"{_d(r['picked_on'])} {r['title'] or r['url']}") for r in picks}

    def topic_wl(sl: str | None) -> str:
        return wl(t_name[sl]) if sl in t_name else "_no topic yet_"

    def tags_for(type_: str, vertical: str | None = None, topic_slug: str | None = None,
                 status: str | None = None) -> list[str]:
        t = [f"type/{type_}"]
        if vertical:
            t.append(tag("vertical", vertical))
        if topic_slug:
            t.append(f"topic/{topic_slug}")
        if status:
            t.append(f"status/{status}")
        return t

    files: dict[str, str] = {}

    # verticals
    for v in verticals:
        vsubs = [sl for sl, s in subs.items() if s["vertical"] == v]
        vcards = [c for c in cards if c["vertical"] == v]
        t = tags_for("vertical", v)
        lines = [frontmatter("vertical", v_name[v], f"{len(vsubs)} subtopics, {len(vcards)} cards from the Reading List.", t, stamp),
                 f"# {v_name[v]}", "", "Back to [[index]].", "", "## Subtopics", ""]
        for sl in vsubs:
            n_cards = sum(card_topic[c["id"]] == sl for c in vcards)
            lines.append(f"- {wl(t_name[sl])}: {subs[sl]['description']} ({n_cards} cards, {pile.get(sl, 0)} to read)")
        protos = [c for c in built if c["vertical"] == v]
        if protos:
            lines += ["", "## Prototypes built", ""] + [f"- {wl(p_name[c['id']])}" for c in protos]
        lines += ["", inline_tags(t)]
        files[f"verticals/{v_name[v]}.md"] = "\n".join(lines) + "\n"

    # topics
    for sl, s in sorted(subs.items()):
        v = s["vertical"]
        t = tags_for("topic", v, sl)
        tcards = [c for c in cards if card_topic[c["id"]] == sl]
        treads = [r for r in reversed(picks) if pick_topic[r["id"]] == sl]
        lines = [frontmatter("topic", t_name[sl], s["description"], t, stamp, keywords=s.get("keywords", [])),
                 f"# {t_name[sl]}", "", f"Subtopic of {wl(v_name[v])}. {s['description']}", ""]
        if s.get("keywords"):
            lines += [f"Keywords: {', '.join(s['keywords'])}", ""]
        lines += ["## Cards", ""] + ([f"- {wl(c_name[c['id']])} ({c['column']})" for c in tcards] or ["_No cards yet._"])
        lines += ["", "## Readings", ""] + ([f"- {wl(r_name[r['id']])}" for r in treads] or ["_No daily reading picked here yet._"])
        lines += ["", f"{pile.get(sl, 0)} more links on this subtopic are in the reading pile.", ""]
        if rel.get(sl):
            lines += ["## Related topics", ""] + [f"- {wl(t_name[o])}" for o in rel[sl] if o in t_name] + [""]
        lines.append(inline_tags(t))
        files[f"topics/{t_name[sl]}.md"] = "\n".join(lines) + "\n"

    # cards
    for c in cards:
        sl = card_topic[c["id"]]
        t = tags_for("card", c["vertical"], sl, c["column"])
        lines = [frontmatter("card", c_name[c["id"]], c.get("learning_goal") or "", t, stamp,
                             card_id=c["id"], aliases=[c["id"]]),
                 f"# {c_name[c['id']]}", "",
                 f"Topic: {topic_wl(sl)} · Vertical: {wl(v_name[c['vertical']])} · Status: {c['column']} · "
                 f"Box: {c['box_minutes']} min" + (f" · Picked {_d(c['picked_on'])}" if c.get("picked_on") else ""), ""]
        if c["id"] in p_name:
            lines += [f"Prototype: {wl(p_name[c['id']])}", ""]
        for label, key in (("Learning goal", "learning_goal"), ("Hypothesis", "hypothesis"),
                           ("Done means", "done_means"), ("Kill criteria", "kill_criteria")):
            lines += [f"**{label}.** {c.get(key) or ''}", ""]
        lines += ["## Source links", ""]
        for lid in c["link_ids"]:
            link = links.get(lid)
            if link:
                lines.append(f"- {safe_name(link.get('title') or '', 120)} (saved {_d(link.get('saved_at'))}): {link['url']}")
        lines += ["", inline_tags(t)]
        files[f"cards/{c_name[c['id']]}.md"] = "\n".join(lines) + "\n"

    # prototypes
    for c in built:
        run = latest.get(c["id"])
        runs = store.runs_for(conn, c["id"])
        sl = card_topic[c["id"]]
        t = tags_for("prototype", c["vertical"], sl, "built")
        notes, _path = notes_for(run)
        total = sum(float(r["cost_usd"] or 0) for r in runs)
        lines = [frontmatter("prototype", p_name[c["id"]], f"Prototype built from {len(c['link_ids'])} saved links.", t, stamp,
                             card_id=c["id"]),
                 f"# {p_name[c['id']]}", "",
                 f"Card: {wl(c_name[c['id']])} · Topic: {topic_wl(sl)} · Vertical: {wl(v_name[c['vertical']])}", ""]
        if run:
            lines += [f"- Repo: {run.get('repo_url') or '-'}", f"- Model: `{run.get('model_id') or '-'}`",
                      f"- Cost: ${total:.2f} over {len(runs)} run{'s' if len(runs) != 1 else ''}", ""]
        lines += ["## Runs", ""]
        for r in runs:
            took = ""
            if r.get("ended_at") and r.get("started_at"):
                took = f", {int((r['ended_at'] - r['started_at']).total_seconds() // 60)} min"
            cost = f", ${float(r['cost_usd']):.2f}" if r.get("cost_usd") is not None else ""
            lines.append(f"- {r['started_at']:%Y-%m-%d %H:%M} UTC: {r['outcome']}{took}{cost}")
        lines += ["", "## Notes", "", _demote(notes).strip() if notes else "_No NOTES.md found for this run yet._", "",
                  inline_tags(t)]
        files[f"prototypes/{p_name[c['id']]}.md"] = "\n".join(lines) + "\n"

    # readings
    for r in picks:
        sl = pick_topic[r["id"]]
        t = tags_for("reading", r["vertical"], sl)
        same = [c for c in built if card_topic[c["id"]] == sl] or [c for c in built if c["vertical"] == r["vertical"]]
        text = excerpt(r.get("readable_text"))
        lines = [frontmatter("reading", r_name[r["id"]], r["why"] or "", t, stamp, picked_on=_d(r["picked_on"])),
                 f"# {r['title'] or r['url']}", "",
                 f"Daily reading for {_d(r['picked_on'])}" + (" (extra pick)" if r["extra"] else "")
                 + f" · Topic: {topic_wl(sl)} · Vertical: {wl(v_name[r['vertical']])}", "",
                 f"- Link: {r['url']}", f"- Saved: {_d(r.get('saved_at'))}", "",
                 "## Why today", "", (r["why"] or "_No reason recorded._").strip(), "",
                 "## Excerpt", "", f"> {text}" if text else "_Only the title was readable for this link._", "",
                 "## Built nearby", ""]
        lines += [f"- {wl(p_name[c['id']])}" for c in same] or ["_Nothing built on this topic yet._"]
        lines += ["", inline_tags(t)]
        files[f"readings/{r_name[r['id']]}.md"] = "\n".join(lines) + "\n"

    # index
    cost = conn.execute("SELECT coalesce(sum(cost_usd), 0) AS s FROM runs").fetchone()["s"]
    idx = [frontmatter("index", "Skunkworks Sloth second brain",
                       "What the Reading List turned into: verticals, topics, cards, prototypes, readings.",
                       ["type/index"], stamp),
           "# Skunkworks Sloth second brain", "",
           f"{len(cards)} cards · {len(built)} built · {len(subs)} topics · {len(picks)} readings · "
           f"Worker cost ${float(cost):.2f} · focus: {describe(current_focus(conn))}", "", "## Verticals", ""]
    idx += [f"- {wl(v_name[v])}: {sum(s['vertical'] == v for s in subs.values())} topics" for v in verticals]
    idx += ["", "## Latest readings", ""] + ([f"- {wl(r_name[r['id']])}" for r in list(reversed(picks))[:7]]
                                             or ["_No readings recommended yet._"])
    idx += ["", "## Prototypes", ""] + ([f"- {wl(p_name[c['id']])}" for c in built] or ["_Nothing built yet._"])
    files["index.md"] = "\n".join(idx) + "\n"

    for rel_path, text in files.items():
        (brain_dir / rel_path).write_text(text)
    write_graph_settings(brain_dir)

    new_pages = sorted(p for p in files if p.startswith(("prototypes/", "readings/")) and p not in previous)
    if new_pages:
        from ..core import notify
        for p in new_pages:
            notify.log("coordinator", "brain", f"new brain page {brain_dir.name}/{p}", {"page": p})
    counts = {f: sum(p.startswith(f + "/") for p in files) for f in FOLDERS}
    edges = sum(len(set(WIKILINK.findall(t))) for t in files.values())
    per_vertical = {v: sum(s["vertical"] == v for s in subs.values()) for v in verticals}
    return {"ok": True, "notes": counts, "edges": edges, "subtopics_per_vertical": per_vertical,
            "new_pages": new_pages, "pages": len(files),
            "reply": f"Second brain updated: {len(files)} notes, {edges} links, {len(subs)} topics."}


def write_graph_settings(brain_dir: Path) -> None:
    """Colour groups by note type in Obsidian's graph view; keep the author's other settings."""
    path = brain_dir / ".obsidian" / "graph.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cfg = json.loads(path.read_text()) if path.exists() else {}
    except json.JSONDecodeError:
        cfg = {}
    cfg["colorGroups"] = [{"query": f"tag:#type/{t}", "color": {"a": 1, "rgb": rgb}} for t, rgb in TYPE_COLORS.items()]
    cfg["showOrphans"] = True
    path.write_text(json.dumps(cfg, indent=2) + "\n")
