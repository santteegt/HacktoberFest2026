"""Discord-ready text for #sk-curator, #sk-valhalla and #sk-logs (pure functions; notify posts them)."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sloth.core.config import ROOT

DISCORD_LIMIT = 1900  # Discord allows 2,000 characters; leave room for the bot's prefix


def _dur(seconds: float) -> str:
    m, s = divmod(int(round(seconds)), 60)
    return f"{m}m{s:02d}s" if m else f"{s}s"


def _clip(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def chunk(lines: list[str], limit: int = DISCORD_LIMIT) -> list[str]:
    """Pack lines into messages under the Discord limit, never splitting a line."""
    out, cur = [], ""
    for line in lines:
        line = _clip(line, limit)
        if cur and len(cur) + 1 + len(line) > limit:
            out.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        out.append(cur)
    return out


def log_line(r) -> str:
    """One #sk-logs line, e.g. `batch b20261024-2100: 200 in, 40 to build, 80 to read, 60 Valhalla, 20 unsure, 6m12s`."""
    return (f"batch {r.batch_id}: {len(r.items)} in, {len(r.by('kept'))} to build, {len(r.by('reading'))} to read, "
            f"{len(r.by('valhalla'))} Valhalla, "
            f"{len(r.by('unsure'))} unsure, {_dur(r.seconds)}")


def batch_summary(r, *, top: int = 5) -> str:
    """The #sk-curator report: counts, why things went to Valhalla, the best ideas, the open questions."""
    if not r.items:
        return f"**Curator batch {r.batch_id}**: nothing left to triage. The Reading List is done."
    kept, reading, val, unsure = r.by("kept"), r.by("reading"), r.by("valhalla"), r.by("unsure")
    rules = Counter(i.rule for i in val if i.rule)
    by_model = sum(1 for i in val if i.decided_by == "model")
    why = ", ".join(f"{n} {k}" for k, n in rules.most_common()) + (f", {by_model} by Gemma" if by_model else "")
    lines = [f"**Curator batch {r.batch_id}**: {len(r.items)} links in {_dur(r.seconds)}",
             f"🛠️ to build {len(kept)} · 📚 to read {len(reading)} · 🪦 Valhalla {len(val)}" + (f" ({why.strip(', ')})" if val else "")
             + f" · ❓ unsure {len(unsure)}"]
    if r.tokens_in or r.tokens_out:
        lines.append(f"Local model `{r.model}`: {r.tokens_in + r.tokens_out:,} tokens, "
                     f"{_dur(r.compute_seconds or r.model_seconds)} of compute; the links never left this Mac.")
    best = sorted((i for i in kept if i.one_line_idea), key=lambda i: -i.buildable)[:top]
    if best:
        lines.append("**Best build ideas**")
        lines += [f"• #{i.link_id} {_clip(i.title, 60)} → {_clip(i.one_line_idea or '', 140)}" for i in best]
    if unsure:
        lines.append("**Unsure, your call** (reply `keep 12, 40` or `valhalla 12`)")
        lines += [f"• #{i.link_id} {_clip(i.title, 70)}" for i in unsure[:10]]
        if len(unsure) > 10:
            lines.append(f"…and {len(unsure) - 10} more (ask me for the unsure list)")
    if val:
        lines.append("The Valhalla list is in #sk-valhalla: reply there with `restore 3, 7` or `empty`.")
    return "\n".join(chunk(lines, 10_000))  # one string; the caller splits with chunk() if needed


def valhalla_messages(rows: list[dict], *, header: str = "Valhalla") -> list[str]:
    """#sk-valhalla text: one line per link, numbered by link id so `restore 3, 7` is unambiguous."""
    if not rows:
        return [f"**{header}**: empty."]
    lines = [f"**{header}**: {len(rows)} link{'s' if len(rows) != 1 else ''}. Reply `restore <ids>` to keep some, or `empty` to confirm all "
             "(nothing is deleted from Chrome; you get a removal list)."]
    for r in rows:
        tag = "rule" if r.get("decided_by") == "code" else "Gemma"
        lines.append(f"`#{r['link_id']}` {_clip(r.get('title') or r.get('url', ''), 70)} · {tag}: "
                     f"{_clip(r.get('reason', ''), 110)}")
    return chunk(lines)


def reading_messages(rows: list[dict], *, header: str | None = None) -> list[str]:
    """The reading bucket, grouped by vertical (rows ordered by vertical already)."""
    lines = [header or f"**📚 Reading bucket**: {len(rows)} link{'s' if len(rows) != 1 else ''} worth reading, nothing to prototype."]
    current = None
    for r in rows:
        if r.get("vertical") != current:
            current = r.get("vertical")
            lines.append(f"__{current or 'unsorted'}__")
        lines.append(f"`#{r['link_id']}` {_clip(r.get('title') or r.get('url', ''), 90)}")
    return chunk(lines)


def export_dir() -> Path:
    return ROOT / ".sloth" / "valhalla"


def write_export(rows: list[dict], *, now: datetime | None = None, out_dir: Path | None = None) -> Path:
    """The removal list for the author to act on in Chrome (markdown + JSON). Never edits Bookmarks."""
    now = now or datetime.now(UTC)
    out = out_dir or export_dir()
    out.mkdir(parents=True, exist_ok=True)
    stem = out / f"removal-{now:%Y%m%d-%H%M%S}"
    md = [f"# Valhalla removal list, {now:%Y-%m-%d %H:%M} UTC", "",
          f"{len(rows)} links confirmed. Remove them from Chrome's Reading List by hand "
          "(Bookmark manager → search the title); Skunkworks Sloth never edits the Bookmarks file.", ""]
    for r in rows:
        md.append(f"- [ ] [{r.get('title') or r['url']}]({r['url']}) · {r.get('folder_path') or ''} · {r['reason']}")
    stem.with_suffix(".md").write_text("\n".join(md) + "\n")
    stem.with_suffix(".json").write_text(json.dumps(
        [{"link_id": r["link_id"], "url": r["url"], "title": r.get("title"), "folder_path": r.get("folder_path"),
          "reason": r["reason"]} for r in rows], indent=1))
    return stem.with_suffix(".md")
