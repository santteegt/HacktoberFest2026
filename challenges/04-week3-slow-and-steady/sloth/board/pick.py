"""Daily pick: code scores and selects, the model only words the options.

score = 0.5 · focus weight + 0.3 · freshness of the newest link + 0.2 · vertical novelty
(no focus set → every vertical weighs 0.5). Options are the top cards with distinct verticals
first. The offered options are stored as an `events` row so a tapped label maps back to its
card without asking the model.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

from pydantic import BaseModel, Field

from ..core.llm import local_json
from ..core.models import Column, PickOption
from . import store
from .focus import NAMES, current_focus

W_FOCUS, W_FRESH, W_NOVEL = 0.5, 0.3, 0.2
FRESH_HALF_LIFE_DAYS = 120
NOVEL_FULL_DAYS = 7
QUESTION = "What are you in the mood for today?"
RECOMMENDED = re.compile(r"\s*\((recommended|recomendado)\)\s*$", re.I)


@dataclass
class Scored:
    card: dict
    score: float
    focus: float
    fresh: float
    novel: float
    newest: date | None
    last_touched: date | None

    def reasons(self) -> str:
        bits = []
        if self.focus >= 0.75:
            bits.append(f"matches this week's focus ({NAMES.get(self.card['vertical'], self.card['vertical'])})")
        if self.newest:
            bits.append(f"newest link saved {self.newest:%b %d, %Y}")
        bits.append("vertical never picked yet" if self.last_touched is None
                    else f"vertical last picked {self.last_touched:%b %d}")
        return "; ".join(bits)


def score_card(card: dict, newest: date | None, weights: dict[str, float] | None,
               last_touched: date | None, today: date) -> Scored:
    focus = weights.get(card["vertical"], 0.0) if weights else 0.5
    fresh = 0.5 ** (max(0, (today - newest).days) / FRESH_HALF_LIFE_DAYS) if newest else 0.0
    novel = 1.0 if last_touched is None else min(1.0, max(0, (today - last_touched).days) / NOVEL_FULL_DAYS)
    total = W_FOCUS * focus + W_FRESH * fresh + W_NOVEL * novel
    return Scored(card, round(total, 4), focus, round(fresh, 3), round(novel, 3), newest, last_touched)


def select(scored: list[Scored], n: int) -> list[Scored]:
    ranked = sorted(scored, key=lambda s: (-s.score, s.card["id"]))
    out, seen = [], set()
    for s in ranked:  # one per vertical first
        if s.card["vertical"] not in seen:
            out.append(s)
            seen.add(s.card["vertical"])
    out = out[:n]
    for s in ranked:  # then fill with the best remaining
        if len(out) >= n:
            break
        if s not in out:
            out.append(s)
    return sorted(out, key=lambda s: (-s.score, s.card["id"]))


class _Worded(BaseModel):
    card_id: str
    label: str = Field(max_length=80)
    why: str = Field(max_length=200)


class _Wording(BaseModel):
    options: list[_Worded]


def word_options(chosen: list[Scored], *, use_model: bool = True) -> tuple[list[PickOption], dict]:
    fallback = [PickOption(card_id=s.card["id"], label=_clip(s.card["title"], 60),
                           why=_clip(s.reasons(), 200)) for s in chosen]
    trace = {"fallback": True, "ms": 0}
    if not use_model:
        return fallback, trace
    cards = "\n".join(
        f'- card_id "{s.card["id"]}": {s.card["title"]}. Goal: {s.card.get("learning_goal") or ""} '
        f"Facts: {s.reasons()}." for s in chosen)
    prompt = (f"Write one tappable button per card for today's prototype pick.\n\n{cards}\n\n"
              'Return {"options": [{"card_id", "label", "why"}]} with the same card_ids in the same order. '
              '"label": what you would build today, at most 55 characters, inviting and plain, no emojis, no quotes. '
              '"why": one sentence, at most 160 characters, using only the facts given for that card.')
    try:
        res = local_json(prompt, _Wording)
    except Exception as e:  # noqa: BLE001
        return fallback, {**trace, "error": str(e)[:200]}
    got = {o.card_id: o for o in res.value.options}
    out = []
    for s, fb in zip(chosen, fallback):
        o = got.get(s.card["id"])
        ok = o and 5 <= len(o.label.strip()) <= 60 and 10 <= len(o.why.strip()) <= 200 and '"' not in o.label
        out.append(PickOption(card_id=s.card["id"], label=_clip(o.label.strip(), 60), why=o.why.strip())
                   if ok else fb)
    labels = [o.label.lower() for o in out]
    if len(set(labels)) != len(labels):  # buttons must be unique to map a tap back to a card
        out = [o.model_copy(update={"label": _clip(f"{o.label} ({o.card_id})", 80)}) for o in out]
    return out, {"fallback": out == fallback, "ms": res.ms, "tokens_out": res.tokens_out}


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def scored_backlog(conn, today: date) -> list[Scored]:
    cards = store.all_cards(conn, (Column.backlog.value,))
    links = store.links_by_id(conn, sorted({i for c in cards for i in c["link_ids"]}))
    focus = current_focus(conn, today)
    weights = focus["weights"] if focus and focus["weights"] else None
    touched = store.last_touched(conn)
    out = []
    for c in cards:
        saved = [links[i]["saved_at"] for i in c["link_ids"] if i in links and links[i]["saved_at"]]
        newest = max(saved).astimezone(UTC).date() if saved else None
        out.append(score_card(c, newest, weights, touched.get(c["vertical"]), today))
    return out


def _today() -> date:
    return datetime.now().astimezone().date()


def options_payload(conn, *, n: int = 4, use_model: bool = True, today: date | None = None) -> dict:
    today = today or _today()
    chosen = select(scored_backlog(conn, today), n)
    if not chosen:
        return {"ok": False, "reply": "The backlog is empty: nothing to pick today. The Curator's next batch will add cards.",
                "action": "Send `reply` as is."}
    options, trace = word_options(chosen, use_model=use_model)
    conn.execute(
        "INSERT INTO events (agent, kind, text, data) VALUES ('coordinator', 'pick_options', %s, %s)",
        (f"{len(options)} pick options offered", json.dumps({
            "options": [o.model_dump() for o in options],
            "scores": {s.card["id"]: {"score": s.score, "focus": s.focus, "fresh": s.fresh, "novel": s.novel}
                       for s in chosen}})))
    conn.commit()
    return {"ok": True, "question": QUESTION, "choices": [o.label for o in options],
            "options": [o.model_dump() for o in options], "wording": trace,
            "reply": pick_text(options),
            "action": ("Send `reply`, then call clarify with `question` and `choices` exactly as given. "
                       "When the author taps or types an answer, run "
                       "`uv run sloth pick choose --json \"<the answer, verbatim>\"` and send its `reply`.")}


def resolve(conn, choice: str) -> str | None:
    """Card id from a card id, a tapped label (with or without '(Recommended)') or text with an id."""
    text = RECOMMENDED.sub("", choice.strip())
    if store.get_card(conn, text):
        return text
    row = conn.execute("SELECT data FROM events WHERE kind = 'pick_options' ORDER BY at DESC, id DESC LIMIT 1").fetchone()
    for o in (row["data"]["options"] if row else []):
        if o["label"].strip().lower() == text.lower():
            return o["card_id"]
    for token in re.findall(r"\bk[0-9a-f]{4,}\b", text.lower()):
        if store.get_card(conn, token):
            return token
    return None


def choose(conn, choice: str, *, today: date | None = None) -> dict:
    from ..core import notify
    from .cards import pick as move_to_today
    today = today or _today()
    card_id = resolve(conn, choice)
    if not card_id:
        return {"ok": False, "reply": "I couldn't match that to a card. Tap one of the buttons, or send its card id (like k7f3a).",
                "action": "Send `reply` as is and wait for the author."}
    try:
        returned = move_to_today(conn, card_id, today=today)
    except (KeyError, ValueError) as e:
        return {"ok": False, "reply": f"Can't pick that card: {e}.", "action": "Send `reply` as is."}
    card = store.get_card(conn, card_id)
    notify.log("coordinator", "move", f"card {card_id} → Today", {"card_id": card_id, "returned": returned})
    notify.post("worker", worker_ping_text(card), as_agent="coordinator")
    return {"ok": True, "card_id": card_id, "returned_to_backlog": returned,
            "reply": picked_text(card), "action": "Send `reply` as is. The Worker takes it from here."}


# ------------------------------------------------------------------ Discord texts (pure)

def pick_text(options: list[PickOption]) -> str:
    lines = [f"**{QUESTION}** Today's options from the skunkworks board:", ""]
    for i, o in enumerate(options, 1):
        lines.append(f"{i}. **{o.label}** (`{o.card_id}`): {o.why}")
    lines += ["", "Tap one below. Nothing gets built until you do."]
    return "\n".join(lines)


def picked_text(card: dict) -> str:
    return (f"Picked **{card['title']}** (`{card['id']}`) for today. It's in Today on the board; "
            f"the Worker gets a {card['box_minutes']}-minute box.\n"
            f"Done means: {card.get('done_means') or '-'}")


def worker_ping_text(card: dict) -> str:
    return (f"Card `{card['id']}` moved to Today: **{card['title']}** "
            f"({card['box_minutes']}-minute box). Start with `sloth work {card['id']}`.")
