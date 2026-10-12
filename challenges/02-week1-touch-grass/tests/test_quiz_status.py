"""Run: PYTHONPATH=src .venv/bin/python tests/test_quiz_status.py"""
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "podcast-quiz" / "scripts"))
from leash import quiz
import shuffle_choices

L = "in Q1, Q3, Q4 the correct choice is the longest; rewrite the three wrong choices in those questions"
# the real failure of 2026-10-10: only spoken-length and guessability checks left after three attempts
assert quiz.quiz_status({"q": 1}, [{"errors": []}]) == "ok"
assert quiz.quiz_status({"q": 1}, [{"errors": ["Q5: question is 28 words (max 25), too long to hear", L]}]) == "partial"
assert quiz.quiz_status({"q": 1}, [{"errors": ["Q2: quote not found in transcript (best match 0.61); copy it word for word"]}]) == "failed"
assert quiz.quiz_status({"q": 1}, [{"errors": ["not valid JSON: x"]}]) == "failed"
assert quiz.quiz_status({"q": 1}, [{"errors": [L, "Q3: same quote as an earlier question"]}]) == "failed"   # one hard error is enough
assert quiz.quiz_status(None, [{"errors": []}]) == "failed" and quiz.quiz_status({"q": 1}, []) == "failed"

# an unverified quiz must not keep every correct answer in the first position
base = {"questions": [{"kind": "mc", "question": f"Q{i}?", "choices": ["right", "b", "c", "d"], "answer_index": 0,
                       "reference_answer": "x", "quote": "y"} for i in range(4)]}
positions = set()
for seed in range(40):
    z = copy.deepcopy(base); shuffle_choices.shuffle_quiz(z, seed)
    for q in z["questions"]:
        assert q["choices"][q["answer_index"]] == "right"     # the answer travels with its text
    positions.update(q["answer_index"] for q in z["questions"])
assert len(positions) == 4, positions
print("quiz status tests passed")
