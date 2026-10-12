"""Voice ideas and notes into the second brain, and small resurfacing helpers."""
import random
import re
from datetime import datetime, timezone
from pathlib import Path

from . import wiki as W

STOP = set("about after again being could every first other should their there these thing think those through where which would your with that this have from what when they them then than into just like some more most over also very much".split())


def _words(s: str):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", s.lower()).split() if len(w) > 4 and w not in STOP}


def related(vault: Path, text: str, limit: int = 3):
    mine, out = _words(text), []
    for p in (vault / "wiki").glob("*.md"):
        if p.name in ("index.md", "log.md"):
            continue
        fm, _ = W._read_front(p)
        if fm.get("type") == "note":
            continue
        shared = len(mine & _words(fm.get("title", "") + " " + fm.get("description", "")))
        if shared:
            out.append((shared, fm.get("title", p.stem), p.name))
    return [(t, n) for _, t, n in sorted(out, reverse=True)[:limit]]


def add_note(vault: Path, text: str, source: str = "voice", when: datetime | None = None, tags=None) -> dict:
    W.ensure_vault(vault)
    when = when or datetime.now(timezone.utc)
    stamp = when.strftime("%Y%m%d-%H%M%S")
    title = (text.strip().split(".")[0][:70] or "Idea").strip()
    slug = f"note-{stamp}-{W.slugify(title, 30)}"
    raw = vault / "raw" / f"{slug}.md"
    raw.write_text(f"# Voice note {stamp}\n\nSource: {source}\n\n{text.strip()}\n")
    rel = related(vault, text)
    links = "\n".join(f"- [{t}]({n})" for t, n in rel) or "- (none yet)"
    (vault / "wiki" / f"{slug}.md").write_text(
        W._front({"type": "note", "title": title, "description": text.strip().replace("\n", " ")[:160],
                  "resource": f"raw/{slug}.md", "tags": tags or [source], "timestamp": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "source_hash": W._sha(raw)})
        + f"## Note\n\n{text.strip()}\n\n## Related Concepts\n\n{links}\n")
    W.refresh_bookkeeping(vault)
    with (vault / "wiki" / "log.md").open("a") as f:
        f.write(f"\n## [{when.strftime('%Y-%m-%d')}] note | {title}\n\n- Source: `raw/{slug}.md` ({source})\n- Related: {', '.join(t for t, _ in rel) or 'none'}\n")
    return {"page": f"wiki/{slug}.md", "related": [t for t, _ in rel]}


def resurface(vault: Path):
    """One concept and one older note to think about again."""
    wiki = vault / "wiki"
    pages = [p for p in wiki.glob("*.md") if p.name not in ("index.md", "log.md")]
    notes = [p for p in pages if p.name.startswith("note-")]
    concepts = [p for p in pages if not p.name.startswith("note-")]
    out = {}
    if concepts:
        fm, body = W._read_front(random.choice(concepts))
        out["concept"] = {"title": fm.get("title"), "description": fm.get("description")}
    if notes:
        fm, body = W._read_front(random.choice(notes))
        out["note"] = {"title": fm.get("title"), "description": fm.get("description")}
    if concepts and notes:
        out["prompt_hint"] = "Ask one question that connects the concept and the note, and ask for a spoken answer."
    return out
