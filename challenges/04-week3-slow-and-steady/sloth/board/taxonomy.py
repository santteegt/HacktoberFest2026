"""Topic taxonomy for the second brain: vertical → 2-8 subtopics → links.

`triage.topic` is near-unique free text, so the brain needs a small, stable layer on top:
the local Gemma names the subtopics of each vertical once, from the list of its links' topics
(language job), and code assigns every link to its nearest subtopic with the local
`embeddinggemma` embedding model (cosine after centring both sides per vertical), falling back to keyword overlap when the embedder
is down. Everything is cached in `.sloth/brain-taxonomy.json`: re-renders only embed links
they have not seen, and the subtopics change only with `sloth brain --retaxonomy`.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from ..core.config import CONFIG_PATH, settings
from ..core.llm import local_json
from .focus import NAMES

CACHE_PATH = Path(os.environ.get("SLOTH_TAXONOMY_FILE", CONFIG_PATH.parent / "brain-taxonomy.json"))
EMBED_MODEL = os.environ.get("SLOTH_EMBED_MODEL", "embeddinggemma:300m")
MAX_TOPICS_IN_PROMPT = 400
RELATED_MAX, RELATED_MIN_SIM = 4, 0.55

Embedder = Callable[[list[str]], list[list[float]]]


class _Sub(BaseModel):
    name: str = Field(max_length=60)
    description: str = Field(max_length=200)
    keywords: list[str] = Field(max_length=10)


class _Subs(BaseModel):
    subtopics: list[_Sub] = Field(max_length=10)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def subtopic_count(n_links: int) -> int:
    if n_links < 5:
        return 1
    if n_links < 15:
        return 2
    return max(3, min(8, round(n_links / 25)))


# ------------------------------------------------------------------ model calls

def embed_ollama(texts: list[str]) -> list[list[float]]:
    out = []
    for i in range(0, len(texts), 64):
        r = httpx.post(f"{settings().ollama_url}/api/embed", timeout=120,
                       json={"model": EMBED_MODEL, "input": texts[i:i + 64]})
        r.raise_for_status()
        out += r.json()["embeddings"]
    return out


def name_subtopics(vertical: str, topics: list[str], k: int) -> list[dict]:
    """One Gemma call: k subtopic names for a vertical, from its links' topics. Verified; code fallback."""
    name = NAMES.get(vertical, vertical)
    if k == 1:
        return [{"name": name, "description": f"Everything saved about {name}.", "keywords": []}]
    listing = "\n".join(f"- {t}" for t in topics[:MAX_TOPICS_IN_PROMPT])
    prompt = (f"These are the topics of {len(topics)} saved links in the vertical \"{name}\":\n{listing}\n\n"
              f"Group them into exactly {k} subtopics that a person would browse. For each give:\n"
              '- "name": 1-4 words, sentence case, specific (e.g. "Agent memory", "Agent protocols (A2A, MCP)"), '
              f'never just "{name}" or "Other"\n'
              '- "description": one sentence on what the subtopic covers\n'
              '- "keywords": 4-8 lowercase words or short phrases taken from the topics above\n'
              'Return {"subtopics": [...]}. The subtopics together must cover most topics.')
    for _ in range(2):
        try:
            res = local_json(prompt, _Subs)
        except Exception:  # noqa: BLE001
            break
        subs = res.value.subtopics
        names = [s.name.strip() for s in subs]
        problems = []
        if not 2 <= len(subs) <= 8 or abs(len(subs) - k) > 1:
            problems.append(f"give {k} subtopics")
        if len({n.lower() for n in names}) != len(names):
            problems.append("names must be unique")
        if any(n.lower() in (name.lower(), "other", "misc", "miscellaneous", "general") or len(n) > 40 for n in names):
            problems.append(f"names must be specific, at most 40 characters, not '{name}' or 'Other'")
        if not problems:
            return [{"name": s.name.strip(), "description": s.description.strip(),
                     "keywords": [w.strip().lower() for w in s.keywords if w.strip()]} for s in subs]
        prompt += f"\n\nYour answer had problems: {'; '.join(problems)}. Answer again."
    return [{"name": name, "description": f"Everything saved about {name}.", "keywords": []}]


# ------------------------------------------------------------------ assignment (pure)

def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


def keyword_assign(text: str, subs: list[dict]) -> str:
    """Fallback: most shared words with name + keywords; ties → first subtopic."""
    words = _words(text)
    best = max(subs, key=lambda s: (len(words & _words(" ".join([s["name"], *s["keywords"]]))), -subs.index(s)))
    return best["slug"]


def sub_text(s: dict) -> str:
    return f"{s['name']}: {s['description']} Keywords: {', '.join(s['keywords'])}"


def link_text(link: dict) -> str:
    return f"{link.get('topic') or ''}. {link.get('title') or ''}. {link.get('one_line_idea') or ''}"[:500]


# ------------------------------------------------------------------ cache + build

VERSION = 2  # 2: centred embeddings (v1 assignments are redone, subtopic names kept)


def load() -> dict:
    if CACHE_PATH.exists():
        tax = json.loads(CACHE_PATH.read_text())
        if tax.get("version", 1) < VERSION:
            tax = {**tax, "version": VERSION, "links": {}}
            for entry in tax["verticals"].values():
                entry.pop("mean_link", None)
        return tax
    return {"version": VERSION, "verticals": {}, "links": {}}


def _mean(vecs: list[list[float]]) -> list[float]:
    return [sum(col) / len(vecs) for col in zip(*vecs)]


def _minus(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def save(tax: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(tax, indent=1) + "\n")


def topic_links(conn) -> list[dict]:
    """Kept and reading links with their latest triage, the material of the taxonomy."""
    return conn.execute(
        """
        WITH latest AS (SELECT DISTINCT ON (link_id) * FROM triage ORDER BY link_id, created_at DESC)
        SELECT l.id, l.title, l.url, l.status, coalesce(t.vertical, 'other') AS vertical, t.topic, t.one_line_idea
        FROM links l JOIN latest t ON t.link_id = l.id
        WHERE l.status IN ('kept', 'reading') OR EXISTS (SELECT 1 FROM reading_picks r WHERE r.link_id = l.id)
           OR EXISTS (SELECT 1 FROM cards c WHERE l.id = ANY(c.link_ids))
        ORDER BY l.id
        """).fetchall()


def ensure(conn, *, retaxonomy: bool = False, embed: Embedder | None = embed_ollama,
           namer: Callable[[str, list[str], int], list[dict]] = name_subtopics) -> dict:
    """Name missing verticals' subtopics and assign unseen links. Returns the taxonomy."""
    tax = {"version": VERSION, "verticals": {}, "links": {}} if retaxonomy else load()
    links = topic_links(conn)
    by_v: dict[str, list[dict]] = {}
    for link in links:
        by_v.setdefault(link["vertical"], []).append(link)
    used_slugs = {s["slug"] for v in tax["verticals"].values() for s in v["subtopics"]}
    changed = False
    for v, vlinks in sorted(by_v.items()):
        if v in tax["verticals"]:
            continue
        topics = sorted({(link["topic"] or "").strip() for link in vlinks if link.get("topic")})
        subs = namer(v, topics, subtopic_count(len(vlinks)))
        for s in subs:
            base = slug(s["name"])
            s["slug"] = base if base not in used_slugs else f"{base}-{slug(v)}"
            used_slugs.add(s["slug"])
        if embed:
            try:
                for s, vec in zip(subs, embed([sub_text(s) for s in subs])):
                    s["vec"] = [round(x, 5) for x in vec]
            except Exception:  # noqa: BLE001 - keyword fallback
                pass
        tax["verticals"][v] = {"subtopics": subs, "n_links": len(vlinks),
                               "built_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
        changed = True
    todo = [link for link in links if str(link["id"]) not in tax["links"] and link["vertical"] in tax["verticals"]]
    vecs = None
    if todo and embed:
        try:
            vecs = embed([link_text(link) for link in todo])
        except Exception:  # noqa: BLE001
            vecs = None
    # Centre both sides per vertical: raw cosine sends most links to the most generic subtopic
    # (151 of 321 AI-agent links went to "Agent frameworks and SDKs"); centred it spreads 27-48.
    if vecs is not None:
        for v, entry in tax["verticals"].items():
            mine = [vecs[i] for i, link in enumerate(todo) if link["vertical"] == v]
            if mine and "mean_link" not in entry:
                entry["mean_link"] = [round(x, 5) for x in _mean(mine)]
    for i, link in enumerate(todo):
        entry = tax["verticals"][link["vertical"]]
        subs = entry["subtopics"]
        if vecs is not None and all("vec" in s for s in subs) and len(subs) > 1:
            mean_s = _mean([s["vec"] for s in subs])
            lv = _minus(vecs[i], entry["mean_link"])
            best = max(subs, key=lambda s: (cosine(lv, _minus(s["vec"], mean_s)), -subs.index(s)))["slug"]
        else:
            best = keyword_assign(link_text(link), subs)
        tax["links"][str(link["id"])] = best
        changed = True
    if changed:
        tax["embed_model"] = EMBED_MODEL if embed else None
        save(tax)
    return tax


def subtopics(tax: dict) -> dict[str, dict]:
    """slug → subtopic (with its vertical)."""
    return {s["slug"]: {**s, "vertical": v} for v, entry in tax["verticals"].items() for s in entry["subtopics"]}


def card_subtopic(card: dict, tax: dict) -> str | None:
    """Majority subtopic of a card's links (ties → the earliest link's)."""
    votes: dict[str, int] = {}
    first: dict[str, int] = {}
    for i, lid in enumerate(card["link_ids"]):
        s = tax["links"].get(str(lid))
        if s:
            votes[s] = votes.get(s, 0) + 1
            first.setdefault(s, i)
    if not votes:
        subs = tax["verticals"].get(card["vertical"], {}).get("subtopics") or []
        return subs[0]["slug"] if subs else None
    return max(votes, key=lambda s: (votes[s], -first[s]))


def related(tax: dict, cards: list[dict]) -> dict[str, list[str]]:
    """Up to RELATED_MAX related subtopics each: cards whose links span both, then embedding similarity."""
    subs = subtopics(tax)
    co: dict[tuple[str, str], int] = {}
    for card in cards:
        spans = sorted({tax["links"].get(str(lid)) for lid in card["link_ids"]} - {None})
        for i, a in enumerate(spans):
            for b in spans[i + 1:]:
                co[(a, b)] = co.get((a, b), 0) + 1
                co[(b, a)] = co.get((b, a), 0) + 1
    out = {}
    for a, sa in subs.items():
        scored = []
        for b, sb in subs.items():
            if a == b:
                continue
            sim = cosine(sa["vec"], sb["vec"]) if "vec" in sa and "vec" in sb else 0.0
            n = co.get((a, b), 0)
            if n or sim >= RELATED_MIN_SIM:
                scored.append((n, sim, b))
        out[a] = [b for _, _, b in sorted(scored, key=lambda x: (-x[0], -x[1], x[2]))[:RELATED_MAX]]
    return out
