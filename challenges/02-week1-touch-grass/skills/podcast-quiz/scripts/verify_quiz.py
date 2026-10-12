#!/usr/bin/env python3
"""Check a podcast-quiz JSON file against its transcript.

Usage: verify_quiz.py quiz.json transcript.txt [--json] [--min-questions N]

Exit code 0 when there are no errors (warnings are allowed), 1 otherwise.
Standard library only, so it runs inside a sandbox or VM with no installs.
"""
import argparse
import difflib
import json
import re
import sys

MAX_QUESTION_WORDS = 25
MAX_CHOICE_WORDS = 12
QUOTE_MIN_WORDS, QUOTE_MAX_WORDS = 6, 45
FUZZY_OK = 0.90  # ratio at which a slightly different quote is accepted with a warning

TS_LINE = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->")
CUE_NUM = re.compile(r"^\s*\d+\s*$")
BAD_CHOICE = re.compile(r"\b(all|none) of the above\b", re.I)


def normalize_words(text):
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    return text.split()


def transcript_words(raw):
    keep = []
    for line in raw.splitlines():
        if TS_LINE.match(line) or CUE_NUM.match(line) or line.strip().upper() == "WEBVTT":
            continue
        keep.append(line)
    return normalize_words(" ".join(keep))


def find_quote(qwords, twords):
    """Return (start_index, ratio). Exact match gives ratio 1.0."""
    n = len(qwords)
    if n == 0 or n > len(twords):
        return None, 0.0
    # exact, via a first-word index
    first = qwords[0]
    for i in range(0, len(twords) - n + 1):
        if twords[i] == first and twords[i:i + n] == qwords:
            return i, 1.0
    best_i, best = None, 0.0
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(qwords)
    qset = set(qwords)
    for i in range(0, len(twords) - n + 1):
        window = twords[i:i + n]
        # cheap pre-filter: enough shared words to be worth scoring
        if sum(1 for w in window if w in qset) < 0.6 * n:
            continue
        sm.set_seq1(window)
        r = sm.ratio()
        if r > best:
            best, best_i = r, i
    return best_i, best


def verify(quiz, twords, min_questions=5):
    errors, warnings, info = [], [], {}
    qs = quiz.get("questions") if isinstance(quiz, dict) else None
    if not isinstance(qs, list):
        return ["top level must be an object with a 'questions' list"], warnings, info

    mcs = [q for q in qs if isinstance(q, dict) and q.get("kind") == "mc"]
    fls = [q for q in qs if isinstance(q, dict) and q.get("kind") == "field_link"]
    if len(qs) < min_questions:
        errors.append(f"need {min_questions} questions, got {len(qs)}")
    elif min_questions == 5 and (len(mcs) != 4 or len(fls) != 1):
        errors.append(f"need 4 mc + 1 field_link, got {len(mcs)} mc + {len(fls)} field_link")
    if qs and isinstance(qs[-1], dict) and qs[-1].get("kind") != "field_link" and fls:
        warnings.append("field_link question should come last")

    positions, seen_quotes = [], set()
    for idx, q in enumerate(qs, 1):
        tag = f"Q{idx}"
        if not isinstance(q, dict):
            errors.append(f"{tag}: not an object")
            continue
        kind = q.get("kind")
        if kind not in ("mc", "field_link"):
            errors.append(f"{tag}: kind must be 'mc' or 'field_link'")
        question = (q.get("question") or "").strip()
        if not question:
            errors.append(f"{tag}: missing question")
        elif len(question.split()) > MAX_QUESTION_WORDS:
            errors.append(f"{tag}: question is {len(question.split())} words (max {MAX_QUESTION_WORDS}), too long to hear")
        if not (q.get("reference_answer") or "").strip():
            errors.append(f"{tag}: missing reference_answer")

        quote = (q.get("quote") or "").strip()
        qw = normalize_words(quote)
        if not qw:
            errors.append(f"{tag}: missing quote")
        else:
            if len(qw) < QUOTE_MIN_WORDS or len(qw) > QUOTE_MAX_WORDS:
                warnings.append(f"{tag}: quote is {len(qw)} words (aim for 8 to 40)")
            key = " ".join(qw)
            if key in seen_quotes:
                errors.append(f"{tag}: same quote as an earlier question")
            seen_quotes.add(key)
            pos, ratio = find_quote(qw, twords)
            if pos is None or ratio < FUZZY_OK:
                errors.append(f"{tag}: quote not found in transcript (best match {ratio:.2f}); copy it word for word")
            else:
                if ratio < 1.0:
                    warnings.append(f"{tag}: quote only matches at {ratio:.2f}; check for a misquote")
                positions.append(pos / max(1, len(twords)))
                # reference answer should be supported by the text around the quote
                ref_words = [w for w in normalize_words(q.get("reference_answer") or "") if len(w) > 3]
                if ref_words:
                    lo, hi = max(0, pos - 120), min(len(twords), pos + len(qw) + 120)
                    around = set(twords[lo:hi])
                    support = sum(1 for w in ref_words if w in around) / len(ref_words)
                    if support < 0.5:
                        warnings.append(f"{tag}: reference_answer shares only {support:.0%} of its words with the text near the quote")

        if kind == "mc":
            ch = q.get("choices")
            if not isinstance(ch, list) or len(ch) != 4:
                errors.append(f"{tag}: needs exactly 4 choices")
            else:
                ch = [str(c).strip() for c in ch]
                if len(set(c.lower() for c in ch)) != 4 or any(not c for c in ch):
                    errors.append(f"{tag}: choices must be 4 distinct non-empty strings")
                for c in ch:
                    if len(c.split()) > MAX_CHOICE_WORDS:
                        errors.append(f"{tag}: a choice is {len(c.split())} words (max {MAX_CHOICE_WORDS})")
                        break
                if any(BAD_CHOICE.search(c) for c in ch):
                    errors.append(f"{tag}: no 'all/none of the above' choices")
                ai = q.get("answer_index")
                if not isinstance(ai, int) or not 0 <= ai <= 3:
                    errors.append(f"{tag}: answer_index must be an integer 0 to 3")
        elif kind == "field_link":
            terms = q.get("concept_terms")
            if not isinstance(terms, list) or not 3 <= len([t for t in terms if str(t).strip()]) <= 8:
                errors.append(f"{tag}: concept_terms needs 3 to 6 entries")

    # bias and coverage signals across the quiz
    answered = [q for q in mcs if isinstance(q.get("answer_index"), int) and isinstance(q.get("choices"), list)
                and len(q["choices"]) == 4 and 0 <= q["answer_index"] <= 3]
    if len(answered) >= 3:
        long_ids = [i for i, q in enumerate(qs, 1) if q in answered
                    and len(str(q["choices"][q["answer_index"]])) == max(len(str(c)) for c in q["choices"])]
        longest = len(long_ids)
        if longest >= 3:
            names = ", ".join(f"Q{i}" for i in long_ids)
            errors.append(f"in {names} the correct choice is the longest; rewrite the three wrong choices in those questions so each has about as many words as the right one, adding a specific detail from the transcript, so a listener cannot guess by length")
        if len({q["answer_index"] for q in answered}) == 1:
            warnings.append("every mc question has the correct answer in the same position")
    if len(positions) >= 4:
        thirds = {min(2, int(p * 3)) for p in positions}
        if len(thirds) < 2:
            warnings.append("all quotes come from one part of the episode; spread questions across it")
        info["quote_thirds"] = sorted(thirds)
    info["questions"] = len(qs)
    info["transcript_words"] = len(twords)
    return errors, warnings, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    ap.add_argument("transcript")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--min-questions", type=int, default=5)
    a = ap.parse_args()
    try:
        quiz = json.load(open(a.quiz, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"cannot read quiz JSON: {e}", file=sys.stderr)
        return 1
    twords = transcript_words(open(a.transcript, encoding="utf-8", errors="replace").read())
    errors, warnings, info = verify(quiz, twords, a.min_questions)
    if a.json:
        print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings, "info": info}, indent=2))
    else:
        for e in errors:
            print("ERROR  ", e)
        for w in warnings:
            print("warning", w)
        print("OK" if not errors else f"{len(errors)} error(s)", f"- {info.get('questions', 0)} questions, {info.get('transcript_words', 0)} transcript words")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
