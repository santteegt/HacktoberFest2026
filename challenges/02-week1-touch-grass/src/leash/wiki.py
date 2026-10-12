"""Write episode notes into an OKF vault (the "second brain").

Layout follows the repo's okf-wiki skill: raw/ holds immutable sources, wiki/ holds pages, index.md,
log.md and .hashes.json. A concept page that already exists is extended, never replaced.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

CONFIG = {
    "okf_version": "0.1",
    "vault_name": "Idea Leash second brain",
    "type_vocabulary": ["concept", "source", "idea", "note", "session"],
    "domain_tags": [],
    "subtopic_tags": [],
    "link_style": "okf-path",
    "strict_lint": False,
}
AGENTS = """# Idea Leash second brain

An OKF vault (https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) of notes from podcasts and voice ideas.

- `raw/` holds the immutable sources (episode transcripts). Never edit them; they are gitignored because they are other people's words.
- `wiki/` holds the pages. `wiki/sources/` has one page per episode; concept pages sit in `wiki/`.
- `wiki/index.md` and `wiki/log.md` are maintained by the ingest pipeline (`python -m leash ingest`) following the okf-wiki skill. Do not hand-edit them.
"""


def slugify(s: str, n: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (s[:n].rstrip("-")) or "untitled"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_vault(root: Path):
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "wiki" / "sources").mkdir(parents=True, exist_ok=True)
    cfg = root / "wiki" / ".wiki-config.json"
    if not cfg.exists():
        cfg.write_text(json.dumps(CONFIG, indent=2))
    ag = root / "AGENTS.md"
    if not ag.exists():
        ag.write_text(AGENTS)
        link = root / "CLAUDE.md"
        if not link.exists():
            link.symlink_to("AGENTS.md")
    gi = root / ".gitignore"
    if not gi.exists():
        gi.write_text("raw/\n")


def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', "'").replace("\n", " ").strip() + '"'


def _front(d: dict) -> str:
    lines = ["---"]
    for k, v in d.items():
        lines.append(f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v if k == 'type' else _q(str(v))}")
    lines.append("---\n")
    return "\n".join(lines) + "\n"


def _read_front(path: Path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm, text[m.end():] if m else text


def add_episode(root: Path, meta: dict, transcript: str, notes: dict, quiz_questions: int = 0):
    ensure_vault(root)
    wiki = root / "wiki"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stamp = f"{today}T00:00:00Z"
    slug = meta["slug"]
    title = meta.get("title") or slug
    # raw source (immutable)
    raw = root / "raw" / f"{slug}.md"
    raw.write_text(f"# {title}\n\nSource: {meta.get('url', 'local file')}\nChannel: {meta.get('channel', '')}\n"
                   f"Duration: {meta.get('duration_min', '?')} min\nIngested: {today}\n\n{transcript}\n")
    h = _sha(raw)
    already = (wiki / "sources" / f"{slug}.md").exists() and f'"{h}"' in (wiki / "sources" / f"{slug}.md").read_text()

    # concept pages
    created, updated, concept_links = [], [], []
    concepts = [(x["title"], x["explanation"], "idea", x.get("quote", "")) for x in notes.get("main_ideas", [])] + \
               [(x["term"], x["definition"], "concept", x.get("quote", "")) for x in notes.get("definitions", [])]
    tags = notes.get("topics", [])[:4]
    for name, text, kind, quote in concepts:
        cs = slugify(name)
        page = wiki / f"{cs}.md"
        concept_links.append((name, cs))
        if page.exists():
            fm, body = _read_front(page)
            if f"sources/{slug}.md" not in body:
                body = body.replace("## Related Concepts", f"- {text} (from [{title}](sources/{slug}.md))\n  - \"{quote}\"\n\n## Related Concepts", 1) \
                    if "## Related Concepts" in body else body + f"\n- {text}\n"
                body = body.rstrip() + f"\n- [{title}](sources/{slug}.md)\n"
                page.write_text(_front({k: (v if k != "tags" else tags) for k, v in fm.items()}) + body)
                updated.append(cs)
        else:
            created.append(cs)
            page.write_text(_front({"type": kind, "title": name, "description": text.split(". ")[0].rstrip(".") + ".",
                                    "tags": tags, "timestamp": stamp})
                            + f"## Definition\n\n{text}\n\n## Key Points\n\n- In the speakers' words: \"{quote}\"\n\n## Related Concepts\n\n@@RELATED@@\n\n## Sources\n\n- [{title}](sources/{slug}.md)\n")
    # fill Related Concepts for the newly created pages
    for name, cs in concept_links:
        page = wiki / f"{cs}.md"
        if "@@RELATED@@" in page.read_text():
            others = [f"- [{n}]({c}.md)" for n, c in concept_links if c != cs][:4]
            page.write_text(page.read_text().replace("@@RELATED@@", "\n".join(others) or "- (none yet)"))

    # source page
    def bullets(items, key, lead=""):
        return "\n".join(f"- {lead}{x[key]}" for x in items) or "- (none)"
    key_concepts = "\n".join(f"- [{n}]({c}.md)" for n, c in concept_links) or "- (none)"
    notable = "\n".join(f"- \"{x['quote']}\" ({x.get('title', x.get('term', x.get('insight', '')))[:60]})" for x in (notes.get("main_ideas", [])[:3]))
    (wiki / "sources" / f"{slug}.md").write_text(
        _front({"type": "source", "title": title,
                "description": (notes.get("summary", "").split(". ")[0].rstrip(".") + ".") if notes.get("summary") else f"Notes from {title}.",
                "resource": f"raw/{slug}.md", "tags": tags, "timestamp": stamp, "source_hash": h})
        + f"## Summary\n\n{notes.get('summary', '')}\n\n## Key Concepts\n\n{key_concepts}\n\n"
          f"## Facts\n\n{bullets(notes.get('facts', []), 'statement', 'Per the speakers: ')}\n\n"
          f"## Insights\n\n{bullets(notes.get('insights', []), 'insight')}\n\n"
          f"## Notable Points\n\n{notable or '- (none)'}\n\n"
          f"## Open Questions\n\n{bullets([{'q': q} for q in notes.get('open_questions', [])], 'q')}\n\n"
          f"## Quiz\n\n{quiz_questions} questions prepared for this episode (4 recall, 1 field link).\n")

    _rebuild_index(wiki, today)
    # hashes for all raw files
    (wiki / ".hashes.json").write_text(json.dumps({f"raw/{p.name}": _sha(p) for p in sorted((root / "raw").glob("*.md"))}, indent=2))
    # log (append-only, oldest first)
    log = wiki / "log.md"
    if already:
        return {"source_page": f"wiki/sources/{slug}.md", "created": created, "updated": updated, "raw": f"raw/{slug}.md"}
    if not log.exists():
        log.write_text("# Log\n")
    with log.open("a") as f:
        f.write(f"\n## [{today}] ingest | {title}\n\n- **Ingest**: {title} processed from `raw/{slug}.md`\n- Source: `raw/{slug}.md`\n- Hash: `{h}`\n"
                f"- Pages created/updated: {1 + len(created) + len(updated)}\n- New concepts: {', '.join(created) or 'none'}\n")
    return {"source_page": f"wiki/sources/{slug}.md", "created": created, "updated": updated, "raw": f"raw/{slug}.md"}


def _rebuild_index(wiki: Path, today: str):
    srcs, cons, notes = [], [], []
    for p in sorted(wiki.glob("*.md")):
        if p.name in ("index.md", "log.md"):
            continue
        fm, _ = _read_front(p)
        row = (fm.get("title", p.stem), p.name, fm.get("description", ""))
        (notes if fm.get("type") == "note" else cons).append(row)
    for p in sorted((wiki / "sources").glob("*.md")):
        fm, _ = _read_front(p)
        srcs.append((fm.get("title", p.stem), f"sources/{p.name}", fm.get("description", "")))
    out = ['---\nokf_version: "0.1"\n---\n', "# Idea Leash second brain: Wiki Index\n",
           f"_Last updated: {today}: {len(srcs) + len(cons) + len(notes)} pages_\n", "## Sources"]
    out += [f"- [{t}]({u}): {d}" for t, u, d in srcs] or ["- (none yet)"]
    out += ["", "## Concepts"] + ([f"- [{t}]({u}): {d}" for t, u, d in cons] or ["- (none yet)"])
    out += ["", "## Notes (voice ideas)"] + ([f"- [{t}]({u}): {d}" for t, u, d in notes] or ["- (none yet)"])
    (wiki / "index.md").write_text("\n".join(out) + "\n")


def refresh_bookkeeping(root: Path):
    """Rebuild index and hashes after pages were added outside add_episode."""
    wiki = root / "wiki"
    _rebuild_index(wiki, datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    (wiki / ".hashes.json").write_text(json.dumps({f"raw/{p.name}": _sha(p) for p in sorted((root / "raw").glob("*.md"))}, indent=2))
