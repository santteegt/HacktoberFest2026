"""Turn a transcript into verified study notes with a local model.

Long episodes are cut into sections; every item the model returns carries a quote, and items whose
quote cannot be found in that section are dropped, so nothing in the notes is unsupported.
"""
import json
import re
import time

from . import ollama
from .quiz import verify_quiz

CHUNK_WORDS = 2400
FUZZY_OK = 0.90

ITEM_QUOTE = {"type": "string"}
CHUNK_SCHEMA = {
    "type": "object",
    "properties": {
        "main_ideas": {"type": "array", "maxItems": 3, "items": {"type": "object", "properties": {
            "title": {"type": "string"}, "explanation": {"type": "string"}, "quote": ITEM_QUOTE},
            "required": ["title", "explanation", "quote"]}},
        "definitions": {"type": "array", "maxItems": 2, "items": {"type": "object", "properties": {
            "term": {"type": "string"}, "definition": {"type": "string"}, "quote": ITEM_QUOTE},
            "required": ["term", "definition", "quote"]}},
        "facts": {"type": "array", "maxItems": 3, "items": {"type": "object", "properties": {
            "statement": {"type": "string"}, "quote": ITEM_QUOTE}, "required": ["statement", "quote"]}},
        "insights": {"type": "array", "maxItems": 2, "items": {"type": "object", "properties": {
            "insight": {"type": "string"}, "quote": ITEM_QUOTE}, "required": ["insight", "quote"]}},
    },
    "required": ["main_ideas", "definitions", "facts", "insights"],
}
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}, "topics": {"type": "array", "items": {"type": "string"}},
                   "open_questions": {"type": "array", "maxItems": 3, "items": {"type": "string"}}},
    "required": ["summary", "topics", "open_questions"],
}

CHUNK_SYSTEM = """You extract study notes from ONE SECTION of a podcast transcript for a listener who wants to remember it.

Rules:
- Use only what the speakers say in this section. Do not add outside knowledge.
- main_ideas: up to 3 claims, arguments or mechanisms the speakers actually explain. title is a short noun phrase (at most 8 words), explanation is one or two sentences in your own words.
- definitions: up to 2 terms the speakers define or explain. Skip terms they only mention.
- facts: up to 3 concrete statements of fact (events, numbers that matter, named things). Attribute opinions to the speakers ("The host argues ...") and never present an opinion as fact.
- insights: up to 2 non-obvious takeaways or trade-offs.
- Every item needs a quote: 8 to 40 words copied exactly, word for word, from this section. Never alter, merge or fix a quote.
- Skip sponsor reads, ads, greetings and housekeeping. If a list has nothing worth keeping, return an empty list.
- Finance, health and legal topics: report what was said and by whom; never advise anyone to buy, sell, take or do anything.
- Write in the language of the transcript."""

SUMMARY_SYSTEM = """You write the overview of a podcast episode from its extracted notes. Return JSON with:
- summary: 3 to 5 sentences, plain language, what the episode covers and its main argument.
- topics: 3 to 5 lowercase tags (one or two words each).
- open_questions: up to 3 questions the episode leaves open or that are worth thinking about.
Use only the notes provided. No advice."""


def chunk_transcript(text: str, max_words: int = CHUNK_WORDS):
    """Split on line breaks, then sentences, into sections of at most ~max_words words."""
    units = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line.split()) > 120:
            units += [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
        else:
            units.append(line)
    chunks, cur, n = [], [], 0
    for u in units:
        w = len(u.split())
        if cur and n + w > max_words:
            chunks.append("\n".join(cur)); cur, n = [], 0
        cur.append(u); n += w
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def _supported(item: dict, twords) -> bool:
    qw = verify_quiz.normalize_words(item.get("quote", ""))
    if len(qw) < 6:
        return False
    pos, ratio = verify_quiz.find_quote(qw, twords)
    return pos is not None and ratio >= FUZZY_OK


def _norm(s: str) -> set:
    return set(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def _dup(a: str, b: str) -> bool:
    x, y = _norm(a), _norm(b)
    return bool(x and y) and len(x & y) / len(x | y) >= 0.7


def build_notes(transcript: str, meta: dict, model: str, num_ctx: int = 16384, log=print):
    t0 = time.time()
    chunks = chunk_transcript(transcript)
    kept = {"main_ideas": [], "definitions": [], "facts": [], "insights": []}
    dropped = 0
    for i, chunk in enumerate(chunks, 1):
        log(f"  notes: section {i}/{len(chunks)} ({len(chunk.split())} words)")
        resp = ollama.chat(model, [{"role": "system", "content": CHUNK_SYSTEM},
                                   {"role": "user", "content": f"Episode: {meta.get('title', '')}\nSection {i} of {len(chunks)}:\n<<<\n{chunk}\n>>>"}],
                           schema=CHUNK_SCHEMA, num_ctx=num_ctx)
        try:
            data = json.loads(resp["message"]["content"])
        except json.JSONDecodeError:
            log("    (section skipped: model did not return valid JSON)")
            continue
        cwords = verify_quiz.normalize_words(chunk)
        for key, label in (("main_ideas", "title"), ("definitions", "term"), ("facts", "statement"), ("insights", "insight")):
            for item in data.get(key, []):
                if not _supported(item, cwords):
                    dropped += 1
                    continue
                if any(_dup(item.get(label, ""), k.get(label, "")) for k in kept[key]):
                    continue
                item["section"] = i
                kept[key].append(item)
    brief = "\n".join(
        [f"IDEA: {x['title']}: {x['explanation']}" for x in kept["main_ideas"]]
        + [f"TERM: {x['term']}: {x['definition']}" for x in kept["definitions"]]
        + [f"FACT: {x['statement']}" for x in kept["facts"]])
    overview = {"summary": "", "topics": [], "open_questions": []}
    if brief.strip():
        resp = ollama.chat(model, [{"role": "system", "content": SUMMARY_SYSTEM},
                                   {"role": "user", "content": f"Episode: {meta.get('title', '')}\nChannel: {meta.get('channel', '')}\n\nNotes:\n{brief}"}],
                           schema=SUMMARY_SCHEMA, num_ctx=num_ctx)
        try:
            overview = json.loads(resp["message"]["content"])
        except json.JSONDecodeError:
            pass
    overview["topics"] = [re.sub(r"[^a-z0-9 -]", "", t.lower()).strip().replace(" ", "-") for t in overview.get("topics", []) if t.strip()][:5]
    notes = {**overview, **kept}
    notes["stats"] = {"sections": len(chunks), "dropped_unsupported": dropped,
                      "kept": {k: len(v) for k, v in kept.items()}, "seconds": round(time.time() - t0, 1), "model": model}
    return notes
