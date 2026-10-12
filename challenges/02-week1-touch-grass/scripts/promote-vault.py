#!/usr/bin/env python3
"""Copy the real content of a test vault into a clean second-brain vault.

What counts as real:
  - episode pages and their concept pages (everything that is not a note),
  - notes whose source is a walk or the phone app (voice-walk:*, voice-app),
  - notes sent by voice from Telegram on or after --since (before that date they were made by my test scripts).
Anything else is left behind. The source vault is not modified.

Usage: python scripts/promote-vault.py [--src data/test-vault] [--dst second-brain] [--since 2026-10-10] [--exclude SLUG ...] [--apply]
Without --apply it only prints the plan.
"""
import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from leash import wiki  # noqa: E402


def note_info(raw: Path):
    text = raw.read_text(errors="ignore")
    m = re.search(r"^Source: (.+)$", text, re.M)
    stamp = re.match(r"note-(\d{8})-(\d{6})", raw.name)
    when = datetime.strptime(stamp.group(1) + stamp.group(2), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc) if stamp else None
    body = text.split("\n\n", 2)[-1].strip().replace("\n", " ")
    return (m.group(1).strip() if m else "?"), when, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "data" / "test-vault"))
    ap.add_argument("--dst", default=str(ROOT / "second-brain"))
    ap.add_argument("--since", default="2026-10-10")
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    src, dst = Path(a.src), Path(a.dst)
    since = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc)

    keep, skip = [], []
    for raw in sorted((src / "raw").glob("note-*.md")):
        source, when, body = note_info(raw)
        slug = raw.stem
        real = (source.startswith("voice-walk:") or source == "voice-app" or (source == "voice" and when and when >= since))
        (keep if real and slug not in a.exclude else skip).append((slug, source, body[:70]))
    notes = {s for s, _, _ in keep + skip}
    print(f"notes kept ({len(keep)}):"); [print(f"  + {s[:38]:38} {src_:26} {b}") for s, src_, b in keep]
    print(f"notes left behind ({len(skip)}):"); [print(f"  - {s[:38]:38} {src_:26} {b}") for s, src_, b in skip]
    if not a.apply:
        print("\n(dry run: nothing written; add --apply)")
        return
    if dst.exists():
        sys.exit(f"{dst} already exists; refusing to overwrite it")
    left = {s for s, _, _ in skip}
    wiki.ensure_vault(dst)
    for sub in ("raw", "wiki"):
        for f in sorted((src / sub).rglob("*")):
            rel = f.relative_to(src)
            if f.is_dir() or f.name in ("index.md", "log.md", ".hashes.json"):
                continue   # rebuilt below
            if f.stem in left or f.name in ("AGENTS.md", "CLAUDE.md"):
                continue
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst / rel)
    wiki.refresh_bookkeeping(dst)
    log = dst / "wiki" / "log.md"
    srclog = (src / "wiki" / "log.md")
    header = log.read_text().rstrip("\n") if log.exists() else "# Log"
    log.write_text(header + f"\n\n## [{datetime.now():%Y-%m-%d}] promote | second-brain created from the test vault\n\n"
                   f"- Copied {len(keep)} notes and all episode pages from `{src.name}`; left {len(skip)} test notes behind "
                   f"({', '.join(s for s, _, _ in skip)}).\n- The test vault is kept unchanged as an archive.\n")
    # a copied note or page must not link to something that was left behind
    dangling = [(p.name, s) for p in dst.rglob("*.md") for s in left if s in p.read_text(errors="ignore")]
    print("\ncreated", dst, "| pages:", len(list((dst / "wiki").glob("*.md"))), "| raw files:", len(list((dst / "raw").glob("*.md"))),
          "| links to left-behind notes:", dangling or "none")


if __name__ == "__main__":
    main()
