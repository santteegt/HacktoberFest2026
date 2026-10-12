"""Generate and verify a podcast quiz with a local model.

The instructions sent to the model are the body of the podcast-quiz skill itself, so the
skill file is the single source of truth for any harness (Hermes, Claude Code, this CLI).
"""
import json
import re
import sys
import time
from pathlib import Path

from . import ollama

PROJECT = Path(__file__).resolve().parents[2]
SKILL_DIR = PROJECT / "skills" / "podcast-quiz"  # installed elsewhere with scripts/install-skills.sh
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import verify_quiz  # noqa: E402
import shuffle_choices  # noqa: E402

QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array", "minItems": 5, "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"enum": ["mc", "field_link"]},
                    "question": {"type": "string"},
                    "choices": {"type": "array", "items": {"type": "string"}},
                    "answer_index": {"type": "integer"},
                    "reference_answer": {"type": "string"},
                    "quote": {"type": "string"},
                    "concept_terms": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["kind", "question", "reference_answer", "quote"],
            },
        }
    },
    "required": ["questions"],
}

TS_LINE = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->")


def clean_transcript(raw: str) -> str:
    """Drop SRT/VTT timestamps and cue numbers but keep the original wording."""
    keep = []
    for line in raw.splitlines():
        if TS_LINE.match(line) or re.fullmatch(r"\s*\d+\s*", line) or line.strip().upper() == "WEBVTT":
            continue
        keep.append(line.strip())
    return "\n".join(l for l in keep if l)


def skill_prompt() -> str:
    text = (SKILL_DIR / "SKILL.md").read_text()
    text = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.S)
    ref = (SKILL_DIR / "references" / "schema.md").read_text()
    return text + "\n\n---\nReference: references/schema.md\n\n" + ref


BASELINE_SYSTEM = "You are a helpful assistant."
BASELINE_USER = ("Here is a podcast transcript. Make a 5-question quiz from it for someone who just listened while walking: "
                 "4 multiple-choice questions (kind \"mc\", 4 choices, answer_index) and a final open question (kind \"field_link\") "
                 "asking them to connect an idea from the episode to something they noticed on the walk, with a few concept_terms. "
                 "For every question include a supporting quote from the transcript and a reference_answer. Return JSON.\n\nTranscript:\n{t}")


def select_candidates(notes: dict, k: int = 6):
    """Pick k verified items spread over the sections of a long episode (ideas first, then insights, definitions, facts)."""
    order = [("main_ideas", "idea", "title", "explanation"), ("insights", "insight", "insight", None),
             ("definitions", "definition", "term", "definition"), ("facts", "fact", "statement", None)]
    pool = {}
    for key, kind, head, body in order:
        for it in notes.get(key, []):
            text = f"{it[head]}: {it[body]}" if body else it[head]
            pool.setdefault(it.get("section", 1), []).append({"kind": kind, "text": text, "quote": it["quote"], "section": it.get("section", 1)})
    picked, sections = [], sorted(pool)
    while len(picked) < k and any(pool.values()):
        for sec in sections:
            if pool[sec] and len(picked) < k:
                picked.append(pool[sec].pop(0))
    return sorted(picked, key=lambda c: c["section"])


def candidate_prompt(cands: list, title: str) -> str:
    lines = [f"[{i}] section {c['section']}, {c['kind']}: {c['text']}\n    quote: \"{c['quote']}\"" for i, c in enumerate(cands, 1)]
    return (f"Episode: {title}\nThis episode is long, so instead of the full transcript you get candidate ideas whose quotes were already "
            "checked against it. Use FIVE different candidates, one per question, preferring ones from different sections. "
            "Copy each question's quote exactly from its candidate. Use the other candidates as material for believable wrong choices.\n\n"
            + "\n".join(lines) + "\n\nWrite the quiz now (Mode 1). Return only the JSON.")


# Errors that make a quiz unusable are "hard" (a quote not in the transcript, wrong shape, broken JSON).
# These two are about how it sounds and how guessable it is; the questions are still grounded.
SOFT_ERROR = re.compile(r"too long to hear|correct choice is the longest|a choice is \d+ words")


def quiz_status(quiz, attempts):
    """"ok": every check passed. "partial": every quote is verified but spoken-length or guessability checks
    still fail after the repair attempts. "failed": anything else (do not serve)."""
    if quiz is None or not attempts:
        return "failed"
    errs = attempts[-1].get("errors") or []
    if not errs:
        return "ok"
    return "partial" if all(SOFT_ERROR.search(e) for e in errs) else "failed"


def generate(raw_transcript: str, model: str, use_skill: bool = True, repairs: int = 2, think: bool = False, num_ctx: int | None = None, candidates: list | None = None, title: str = ""):
    """Return a dict with the final quiz, per-attempt verification and timing."""
    text = clean_transcript(raw_transcript)
    twords = verify_quiz.transcript_words(raw_transcript)
    if use_skill:
        user = candidate_prompt(candidates, title) if candidates else f"Transcript:\n<<<\n{text}\n>>>\n\nWrite the quiz now (Mode 1). Return only the JSON."
        messages = [{"role": "system", "content": skill_prompt()}, {"role": "user", "content": user}]
    else:
        messages = [{"role": "system", "content": BASELINE_SYSTEM},
                    {"role": "user", "content": BASELINE_USER.format(t=text)}]
    attempts, tokens, t0 = [], 0, time.time()
    quiz = None
    seed = int(__import__("hashlib").sha1(text.encode()).hexdigest()[:8], 16)
    shuffled = False
    for attempt in range(1 + (repairs if use_skill else 0)):
        resp = ollama.chat(model, messages, schema=QUIZ_SCHEMA, think=think, **({'num_ctx': num_ctx} if num_ctx else {}))
        tokens += resp.get("prompt_eval_count", 0) + resp.get("eval_count", 0)
        content = resp["message"]["content"]
        try:
            quiz = json.loads(content)
        except json.JSONDecodeError as e:
            attempts.append({"errors": [f"not valid JSON: {e}"], "warnings": [], "wall_s": resp["_wall_s"]})
            messages += [{"role": "assistant", "content": content},
                         {"role": "user", "content": "That was not valid JSON. Return only the corrected JSON."}]
            continue
        errors, warnings, info = verify_quiz.verify(quiz, twords)
        attempts.append({"errors": errors, "warnings": warnings, "wall_s": round(resp["_wall_s"], 1)})
        if not errors:
            if use_skill:  # the skill's last step: spread correct answers over all positions
                shuffle_choices.shuffle_quiz(quiz, seed)
                shuffled = True
            break
        messages += [{"role": "assistant", "content": content},
                     {"role": "user", "content": "The verifier found these problems:\n- " + "\n- ".join(errors)
                      + "\nFix them (replace a question if its quote cannot be found; copy quotes word for word) and return the full corrected JSON."}]
    if quiz is not None and use_skill and not shuffled:
        # Shuffling is plain code and does not depend on the checks: never serve a quiz whose correct answer
        # is always the first choice (this happened on 2026-10-10 when all repair attempts failed).
        try:
            shuffle_choices.shuffle_quiz(quiz, seed)
        except Exception:  # noqa: BLE001  structure too broken to shuffle; it will be reported as failed
            pass
    return {"quiz": quiz, "attempts": attempts, "total_tokens": tokens, "duration_s": round(time.time() - t0, 1),
            "status": quiz_status(quiz, attempts)}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="leash-quiz")
    ap.add_argument("transcript")
    ap.add_argument("--model", default="gemma4:12b-it-qat")
    ap.add_argument("--no-skill", action="store_true")
    ap.add_argument("-o", "--out")
    a = ap.parse_args(argv)
    res = generate(Path(a.transcript).read_text(), a.model, use_skill=not a.no_skill)
    out = json.dumps(res["quiz"], indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(out)
    else:
        print(out)
    last = res["attempts"][-1] if res["attempts"] else {}
    print(f"attempts={len(res['attempts'])} errors={last.get('errors')} warnings={last.get('warnings')} "
          f"tokens={res['total_tokens']} seconds={res['duration_s']}", file=sys.stderr)
    return 0 if res["quiz"] and not last.get("errors") else 1


if __name__ == "__main__":
    sys.exit(main())


GRADE_SCHEMA = {"type": "object", "properties": {"score": {"type": "integer"}, "feedback": {"type": "string"}, "evidence": {"type": "string"}},
                "required": ["score", "feedback", "evidence"]}


def grade_open(q: dict, answer: str, model: str = ollama.DEFAULT_MODEL) -> dict:
    """Mode 2 of the podcast-quiz skill for a spoken open answer. Returns score 0 to 2."""
    if not answer or len(answer.split()) < 3:
        return {"score": 0, "feedback": "I did not catch an answer. Try again whenever you are ready.", "evidence": "empty or too short"}
    body = {k: q.get(k) for k in ("kind", "question", "reference_answer", "quote", "concept_terms") if q.get(k)}
    msgs = [{"role": "system", "content": skill_prompt()},
            {"role": "user", "content": "Mode 2: grade this answer. Return only the JSON.\n\n" + json.dumps({**body, "learner_answer": answer}, ensure_ascii=False)}]
    resp = ollama.chat(model, msgs, schema=GRADE_SCHEMA, num_ctx=16384)
    out = json.loads(resp["message"]["content"])
    out["score"] = max(0, min(2, int(out.get("score", 0))))
    return out
