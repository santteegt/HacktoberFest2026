"""Card wording by the local model; box and kill criteria by code.

The model only writes language (title, learning goal, hypothesis, done-means). A verifier
checks lengths and that the title is grounded in the links' words; one repair round, then a
code-written fallback so a card is never blocked on the model.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.llm import local_json
from .cluster import _STOP
from .store import KeptLink


class CardWording(BaseModel):
    title: str = Field(max_length=90)
    learning_goal: str = Field(max_length=300)
    hypothesis: str = Field(max_length=300)
    done_means: str = Field(max_length=300)


SYSTEM = (
    "You write cards for a personal skunkworks board. Each card turns a few saved links into "
    "one small prototype the author can build alone in a fixed time box. Be concrete and plain; "
    "no hype, no emojis. Answer with JSON only."
)

PROMPT = """Write one card for these saved links (vertical: {vertical}). The prototype must fit a {box}-minute box.

Links:
{links}

Fields:
- "title": what gets built, as a short noun phrase, at most 70 characters. Use words from the links. No quotes, no "Card:" prefix.
- "learning_goal": one sentence, starting with "Learn", saying what the author will understand after building it.
- "hypothesis": one sentence, starting with "I can", saying what will work within {hours} and with which tool or library from the links.
- "done_means": one or two checkable conditions a test or a command can show (for example "`make demo` prints ...; tests pass"). No vague words like "works well".
"""


def box_minutes() -> int:
    return settings().box_minutes


def kill_criteria(box: int) -> str:
    """Code-owned: the Worker stops on these, the model never sets them."""
    return (f"Kill if there is no running skeleton after {box // 3} minutes, "
            f"or if done-means is not met when the {box}-minute box ends.")


def _hours(box: int) -> str:
    return f"{box // 60} hours" if box % 60 == 0 and box >= 120 else f"{box} minutes"


def link_lines(links: list[KeptLink]) -> str:
    out = []
    for i, link in enumerate(links, 1):
        out.append(f"{i}. {link.title or link.url}\n   topic: {link.topic}; kind: {link.kind}; "
                   f"idea: {link.one_line_idea or '-'}\n   url: {link.url}")
    return "\n".join(out)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2 and t not in _STOP}


def verify(w: CardWording, links: list[KeptLink]) -> list[str]:
    problems = []
    if not 8 <= len(w.title) <= 70:
        problems.append("title must be 8-70 characters")
    if re.match(r"(?i)\s*card\b", w.title) or '"' in w.title:
        problems.append("title must not start with 'Card' or contain quotes")
    source = set().union(*(_tokens(f"{link.title or ''} {link.topic} {link.one_line_idea or ''}")
                           for link in links))
    title_words = _tokens(w.title)
    if source and not (title_words & source):
        problems.append("title must reuse at least one word from the links' titles or topics")
    if not w.learning_goal.lower().startswith("learn"):
        problems.append('learning_goal must start with "Learn"')
    if not w.hypothesis.lower().startswith("i can"):
        problems.append('hypothesis must start with "I can"')
    for name in ("learning_goal", "hypothesis", "done_means"):
        if len(getattr(w, name).strip()) < 15:
            problems.append(f"{name} is too short")
    return problems


def fallback(links: list[KeptLink], vertical: str, box: int) -> CardWording:
    lead = links[0]
    idea = (lead.one_line_idea or lead.topic).rstrip(".")
    return CardWording(
        title=idea[:70],
        learning_goal=f"Learn the core idea behind {lead.topic} by building it.",
        hypothesis=f"I can build a working {vertical} prototype from these links within {_hours(box)}.",
        done_means="`make demo` runs the prototype end to end; `make test` passes.",
    )


def word_card(links: list[KeptLink], vertical: str, *, box: int | None = None,
              use_model: bool = True) -> tuple[CardWording, dict]:
    """Return the wording and a small trace (model, tokens, ms, tries, fallback)."""
    box = box or box_minutes()
    trace = {"model": None, "tokens_in": 0, "tokens_out": 0, "ms": 0, "tries": 0, "fallback": False}
    if not use_model:
        trace["fallback"] = True
        return fallback(links, vertical, box), trace
    prompt = PROMPT.format(vertical=vertical, box=box, hours=_hours(box), links=link_lines(links))
    for _ in range(2):
        trace["tries"] += 1
        try:
            res = local_json(prompt, CardWording, system=SYSTEM)
        except Exception as e:  # noqa: BLE001 - model down or invalid twice: fall back
            trace["error"] = f"{type(e).__name__}: {e}"[:200]
            break
        trace["model"] = res.model
        trace["tokens_in"] += res.tokens_in
        trace["tokens_out"] += res.tokens_out
        trace["ms"] += res.ms
        problems = verify(res.value, links)
        if not problems:
            return res.value, trace
        trace["problems"] = problems
        prompt += (f"\n\nYour previous answer was {res.value.model_dump_json()}. Fix these problems "
                   f"and answer again: {'; '.join(problems)}.")
    trace["fallback"] = True
    return fallback(links, vertical, box), trace
