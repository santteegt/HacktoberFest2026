"""Model triage: one small JSON answer per link from the local Gemma, checked by a verifier.

The model only labels. Code already removed dead, archived, stale and duplicate links (rules.py),
code decides kept / Valhalla / unsure from the label, and code checks the label is grounded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sloth.core.llm import local_json
from sloth.core.models import Kind, Triage, Vertical

from .enrich import host_of

EXCERPT_CHARS = 1500

# Ollama's `format` constrains the output, but the model never sees the schema: say it all here.
SYSTEM = f"""You triage one saved link for a developer who bookmarks things "to learn by building" and never gets to them.
Answer with one JSON object and nothing else. Fields:
- topic: 2-5 words naming what the link is about (e.g. "MCP server for Postgres").
- vertical: exactly one of {", ".join(v.value for v in Vertical)}.
- kind: exactly one of {", ".join(k.value for k in Kind)}.
- still_relevant: false only if it is outdated or superseded (old versions, abandoned projects, events that are over), spam, or hype that has passed. A link with nothing to build is still relevant if it is worth reading: X threads, landing pages, explainers and dashboards the developer saved on purpose stay true unless outdated.
- reason: one sentence, at most 200 characters, that cites a concrete fact from the input (a word or phrase from the title or text, a star count, a date). No generic praise.
- buildable: how directly the link turns into a small hands-on prototype. Most links are 0 or 1.
  0 = nothing to build from it: product or landing pages, dashboards, announcements, opinion or X threads, protocol explainers, docs about one setting.
  1 = useful background or a big framework, research repo or awesome-list you would only skim.
  2 = it hands you runnable code or a precise method (a library or SDK with a quickstart, an example project, a skill or spec, exercises) and a weekend prototype is clear.
  3 = a step-by-step tutorial or tiny library where a 2-hour prototype is obvious.
- one_line_idea: if buildable is 2 or 3, one sentence (at most 160 characters) describing the small prototype to build from it; otherwise null.
Judge only from the input. If the page could not be read, judge the title; never call a link irrelevant just because its page was unreadable."""

_WORD = re.compile(r"[a-z0-9][a-z0-9.+#-]*[a-z0-9+#]|[a-z0-9]")
# Words a reason can use without citing anything.
_GENERIC = set("""
this that with from into about have has having been being were will would could should their there
which what when where while these those them they then than very more most much many some such only
also just like link page article post thread tweet repo repository project tool tools library useful
relevant still worth learning learn build building built idea ideas good great interesting nice
content provides offers describes explains discusses shows using used uses based simple small
developer developers outdated time today date input title text information details resource
""".split())


_WALL = ("sign in", "log in", "login", "create an account", "enable javascript", "verify you are human",
         "access denied", "just a moment", "cookies to continue", "subscribe to continue")


def looks_like_wall(text: str | None) -> bool:
    """A login wall, bot check or JS shell: short text dominated by gatekeeping phrases."""
    t = (text or "").lower()
    return len(t) < 1500 and any(w in t for w in _WALL)


def readable_text(enr: dict | None) -> str:
    """The page text worth showing the model; empty when the fetch only saw a wall."""
    text = (enr or {}).get("readable_text") or ""
    if len(text) < 200 and (enr or {}).get("content_kind") != "github" or looks_like_wall(text):
        return ""
    return text


def excerpt(text: str | None, n: int = EXCERPT_CHARS) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    return t[:n] + ("…" if len(t) > n else "")


def link_input(link: dict, enr: dict | None, *, today: datetime | None = None) -> str:
    """The facts the model sees, as short labelled lines. Everything in here may be cited."""
    today = today or datetime.now(UTC)
    enr = enr or {}
    lines = [f"Today: {today:%Y-%m-%d}",
             f"Title: {link.get('title') or '(none)'}",
             f"Site: {host_of(enr.get('final_url') or link['url'])}",
             f"Folder: {link.get('folder_path') or '-'}",
             f"Saved: {link['saved_at']:%Y-%m-%d}" if link.get("saved_at") else "Saved: unknown"]
    if enr.get("published_at"):
        lines.append(f"Published: {enr['published_at']:%Y-%m-%d}")
    if enr.get("content_kind") == "github":
        pushed = enr.get("github_pushed_at")
        lines.append(f"GitHub: {enr.get('github_stars') or 0} stars, last push "
                     f"{pushed:%Y-%m-%d}" if pushed else f"GitHub: {enr.get('github_stars') or 0} stars")
    text = excerpt(readable_text(enr))
    lines.append(f"Text: {text}" if text else "Text: (could not read the page; judge from the title)")
    return "\n".join(lines)


def content_words(s: str) -> set[str]:
    return {w for w in _WORD.findall(s.lower()) if (len(w) >= 4 or w.isdigit()) and w not in _GENERIC}


def verify(t: Triage, source: str) -> list[str]:
    """Problems with a label; empty means it passes. Enum values are already checked by pydantic."""
    problems = []
    cited = content_words(t.reason) & content_words(source)
    if not cited:
        problems.append("the reason does not cite any word, number or date from the input")
    if t.buildable >= 2 and not (t.one_line_idea or "").strip():
        problems.append("buildable is 2 or 3 but one_line_idea is empty")
    if not t.topic.strip():
        problems.append("topic is empty")
    return problems


# Kinds that are read, not built from: the author never rated one of these above 1 (M0.2 labels).
READ_ONLY_KINDS = {Kind.article, Kind.news, Kind.thread, Kind.other}


def normalize(t: Triage) -> Triage:
    """Code-side cleanup that needs no second model call."""
    if t.kind in READ_ONLY_KINDS and t.buildable > 1:
        t = t.model_copy(update={"buildable": 1})
    if t.buildable < 2:
        t = t.model_copy(update={"one_line_idea": None})
    return t


@dataclass
class Labelled:
    triage: Triage
    verified: bool
    problems: list[str]
    model: str
    tokens_in: int
    tokens_out: int
    ms: int
    tries: int


def label(link: dict, enr: dict | None, *, today: datetime | None = None) -> Labelled:
    """Ask the model, verify, retry once with the verifier's complaint, give up as unverified."""
    source = link_input(link, enr, today=today)
    prompt = f"Link:\n{source}"
    tin = tout = ms = 0
    res = None
    problems: list[str] = []
    for attempt in range(2):
        res = local_json(prompt, Triage, system=SYSTEM)
        tin, tout, ms = tin + res.tokens_in, tout + res.tokens_out, ms + res.ms
        t = normalize(res.value)
        problems = verify(t, source)
        if not problems:
            return Labelled(t, True, [], res.model, tin, tout, ms, attempt + 1)
        prompt = (f"Link:\n{source}\n\nYour previous answer was:\n{res.value.model_dump_json()}\n"
                  f"It was rejected because {'; '.join(problems)}. Answer again with corrected JSON.")
    assert res is not None
    return Labelled(normalize(res.value), False, problems, res.model, tin, tout, ms, 2)


def decide(lab: Labelled, link: dict, enr: dict | None) -> str:
    """kept (build candidate) | reading | valhalla | unsure, from the label.

    Valhalla needs evidence the model could see. Still-relevant links with buildable < 2 go to the
    reading bucket: worth reading, nothing to prototype (the author's ask after labelling M0.2).
    """
    if not lab.verified:
        return "unsure"
    if lab.triage.still_relevant:
        return "kept" if lab.triage.buildable >= 2 else "reading"
    if not readable_text(enr) and len(link.get("title") or "") < 40:
        return "unsure"  # nothing but a short title: the author decides, not the model
    return "valhalla"
