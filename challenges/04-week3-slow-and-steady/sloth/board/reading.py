"""Daily reading (SPEC Workflow 5b): one never-recommended link from the Curator's `reading` bucket.

Code picks: 0.5 · focus weight (0.1 floor for other verticals; 0.5 for all with no focus)
+ 0.3 · readable text (full text > short text > title only) + 0.2 · freshness of the save
+ 0.15 when the title or topic uses a word of the focus answer, plus a tiny per-day jitter so
ties break the same way all day. The model only writes the one-line "why read this today",
checked against the input, with a code-written fallback.

One main pick per day (partial unique index on `reading_picks.picked_on WHERE NOT extra`);
`--again` adds extra picks (extra = true). Every recorded pick refreshes the second brain.
Without `--post` and `--again` nothing is recorded: the day's pick is deterministic, so a
preview in #sk-coordinator and the 08:00 post name the same link.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

from pydantic import BaseModel, Field

from ..core.llm import local_json
from .focus import NAMES, current_focus
from .pick import focus_terms, _words

W_FOCUS, W_READABLE, W_FRESH, W_TOPIC = 0.5, 0.3, 0.2, 0.15
OTHER_FLOOR = 0.1
FRESH_HALF_LIFE_DAYS = 180
MAX_TEXT = 600
# A saved search-results page is a query, not a reading.
SEARCH_PAGE = re.compile(r"^https?://(www\.)?(google\.[a-z.]+/search|bing\.com/search|duckduckgo\.com/\?|search\.brave\.com/search)", re.I)
TEXT_FOR_MODEL = 1500
_STOP = {"this", "that", "with", "from", "your", "about", "into", "what", "when", "will", "have",
         "here", "read", "today", "link", "article", "post", "page", "they", "their", "there", "which"}


@dataclass
class Candidate:
    link_id: int
    url: str
    title: str | None
    saved_at: datetime | None
    vertical: str
    topic: str | None
    kind: str | None
    reason: str | None
    one_line_idea: str | None
    readable_chars: int
    readable_text: str | None
    score: float = 0.0
    hits: tuple[str, ...] = ()


def candidates(conn) -> list[Candidate]:
    rows = conn.execute(
        """
        WITH latest AS (SELECT DISTINCT ON (link_id) * FROM triage ORDER BY link_id, created_at DESC)
        SELECT l.id AS link_id, coalesce(e.final_url, l.url) AS url, l.title, l.saved_at,
               coalesce(t.vertical, 'other') AS vertical, t.topic, t.kind, t.reason, t.one_line_idea,
               coalesce(e.readable_chars, 0) AS readable_chars, left(e.readable_text, %s) AS readable_text
        FROM links l
        LEFT JOIN latest t ON t.link_id = l.id
        LEFT JOIN enrichment e ON e.link_id = l.id
        WHERE l.status = 'reading'
          AND NOT EXISTS (SELECT 1 FROM reading_picks r WHERE r.link_id = l.id)
        ORDER BY l.id
        """, (TEXT_FOR_MODEL,)).fetchall()
    return [Candidate(**r) for r in rows if not SEARCH_PAGE.search(r["url"])]


def readable_score(chars: int) -> float:
    return 1.0 if chars >= 1000 else 0.6 if chars >= 200 else 0.0


def score(c: Candidate, weights: dict[str, float] | None, terms: set[str], today: date) -> Candidate:
    focus = (max(weights.get(c.vertical, 0.0), OTHER_FLOOR)) if weights else 0.5
    if c.saved_at:
        age = max(0, (today - c.saved_at.astimezone(UTC).date()).days)
        fresh = 0.5 ** (age / FRESH_HALF_LIFE_DAYS)
    else:
        fresh = 0.0
    hits = tuple(sorted(terms & _words(f"{c.title or ''} {c.topic or ''}")))
    jitter = random.Random(f"{today.isoformat()}:{c.link_id}").random() * 0.001
    c.score = round(W_FOCUS * focus + W_READABLE * readable_score(c.readable_chars)
                    + W_FRESH * fresh + (W_TOPIC if hits else 0.0) + jitter, 5)
    c.hits = hits
    return c


def ranked(conn, today: date) -> tuple[list[Candidate], dict | None]:
    focus = current_focus(conn, today)
    weights = focus["weights"] if focus and focus["weights"] else None
    terms = focus_terms(focus["text"]) if weights else set()
    out = [score(c, weights, terms, today) for c in candidates(conn)]
    return sorted(out, key=lambda c: (-c.score, c.link_id)), focus


# ------------------------------------------------------------------ wording

class _Why(BaseModel):
    why: str = Field(max_length=240)


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9-]+", text.lower()) if len(w) > 3 and w not in _STOP}


def verify_why(why: str, c: Candidate) -> list[str]:
    problems = []
    why = why.strip()
    if not 20 <= len(why) <= 200:
        problems.append("why must be 20-200 characters")
    if "http" in why or "www." in why:
        problems.append("no URLs in why")
    source = _content_words(f"{c.title or ''} {c.topic or ''} {(c.readable_text or '')[:TEXT_FOR_MODEL]}")
    if not (_content_words(why) & source):
        problems.append("why must mention something from the title or text")
    return problems


def fallback_why(c: Candidate) -> str:
    base = (c.reason or c.one_line_idea or c.topic or "Saved to read").strip().rstrip(".")
    return _clip(f"{base}.", 200)


def word_why(c: Candidate, focus_text: str | None, *, use_model: bool = True) -> tuple[str, str]:
    """Return (why, 'model' | 'code')."""
    if not use_model:
        return fallback_why(c), "code"
    text = (c.readable_text or "").strip()
    prompt = (
        "Recommend this saved link to its owner as today's reading. Write ONE sentence, at most "
        "180 characters, saying why it is worth reading today: name what it covers, using words "
        "from the title or text. Plain, no hype, no emojis, no URL.\n\n"
        f"Title: {c.title or '-'}\nTopic: {c.topic or '-'}\nVertical: {NAMES.get(c.vertical, c.vertical)}\n"
        + (f"This week's focus: {focus_text}\n" if focus_text else "")
        + (f"Text (start):\n{text}\n" if text else "Text: (only the title is known)\n")
        + '\nReturn {"why": "..."}.')
    for _ in range(2):
        try:
            res = local_json(prompt, _Why)
        except Exception:  # noqa: BLE001 - model down or invalid: the code line stands
            break
        problems = verify_why(res.value.why, c)
        if not problems:
            return res.value.why.strip(), "model"
        prompt += f"\n\nYour answer {res.value.why!r} had problems: {'; '.join(problems)}. Answer again."
    return fallback_why(c), "code"


# ------------------------------------------------------------------ Discord text (pure)

def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def reading_text(title: str | None, url: str, vertical: str, why: str, *, left: int | None = None,
                 extra: bool = False) -> str:
    """Discord message under MAX_TEXT characters. The URL sits alone on its line, never clipped."""
    head = f"**{'Another reading' if extra else 'Today’s reading'}** · {NAMES.get(vertical, vertical)}"
    foot = f"_{left} more in the reading pile._" if left is not None else ""
    budget = MAX_TEXT - len(head) - len(url) - len(foot) - 12
    why = _clip(why.strip(), max(40, min(200, budget // 2)))
    title_room = max(20, budget - len(why))
    lines = [head, f"**{_clip((title or url).strip(), title_room)}**", url, why] + ([foot] if foot else [])
    text = "\n".join(lines)
    return text if len(text) <= MAX_TEXT else "\n".join([head, url, _clip(why, 120)])


# ------------------------------------------------------------------ the command

def _today() -> date:
    return datetime.now().astimezone().date()


def todays_main(conn, today: date) -> dict | None:
    return conn.execute(
        """SELECT r.*, l.title, coalesce(e.final_url, l.url) AS url FROM reading_picks r
           JOIN links l ON l.id = r.link_id LEFT JOIN enrichment e ON e.link_id = l.id
           WHERE r.picked_on = %s AND NOT r.extra ORDER BY r.created_at, r.id LIMIT 1""", (today,)).fetchone()


def _focus_id(conn) -> int | None:
    row = conn.execute("SELECT id FROM focus ORDER BY created_at DESC LIMIT 1").fetchone()
    return row["id"] if row else None


def _record(conn, c: Candidate, today: date, why: str, extra: bool) -> None:
    conn.execute(
        """INSERT INTO reading_picks (link_id, picked_on, vertical, why, focus_id, extra)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (c.link_id, today, c.vertical, why, _focus_id(conn), extra))


def today_payload(conn, *, post: bool = False, again: bool = False, use_model: bool = True,
                  today: date | None = None) -> dict:
    from ..core import notify
    today = today or _today()
    main = todays_main(conn, today)
    if main and not again:
        text = reading_text(main["title"], main["url"], main["vertical"] or "other", main["why"] or "")
        return {"ok": True, "link_id": main["link_id"], "recorded": True, "posted": None,
                "already": True, "text": text,
                "reply": text if not post else f"Today's reading was already picked: {main['url']}",
                "action": "Send `reply` as is."}
    pool, focus = ranked(conn, today)
    if again and not main and pool:
        pool = pool[1:]  # the day's main pick stays for the 08:00 post
    if not pool:
        return {"ok": False, "reply": "The reading pile is empty: every saved reading link was already recommended.",
                "action": "Send `reply` as is."}
    c = pool[0]
    why, why_by = word_why(c, focus["text"] if focus else None, use_model=use_model)
    left = len(pool) - 1
    text = reading_text(c.title, c.url, c.vertical, why, left=left, extra=again)
    recorded = posted = False
    if post:
        notify.post("daily_reading", text)
        posted = True
    if post or again:
        _record(conn, c, today, why, extra=again)
        conn.commit()
        recorded = True
        from .brain import render  # the brain page exists the same day
        render(conn)
    if posted or recorded:
        notify.log("coordinator", "reading",
                   f"{'extra ' if again else ''}reading for {today}: link {c.link_id} ({c.vertical})",
                   {"link_id": c.link_id, "why_by": why_by, "posted": posted, "score": c.score})
    out = {"ok": True, "link_id": c.link_id, "url": c.url, "title": c.title, "vertical": c.vertical,
           "why": why, "why_by": why_by, "score": c.score, "left": left, "recorded": recorded,
           "posted": posted, "text": text, "reply": text, "action": "Send `reply` as is."}
    return out
