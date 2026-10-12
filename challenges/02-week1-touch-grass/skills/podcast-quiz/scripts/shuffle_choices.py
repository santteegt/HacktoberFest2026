#!/usr/bin/env python3
"""Spread the correct answers of a verified quiz across all four positions.

Usage: shuffle_choices.py quiz.json [--seed N]

Language models put the right answer in the same slot far too often, and a listener who
notices will stop paying attention. This rewrites quiz.json in place: each of the four
multiple-choice questions gets a different correct position (a random permutation of 0..3),
and the wrong choices are shuffled. Run it after verify_quiz.py passes.
"""
import argparse
import json
import random


def shuffle_quiz(quiz, seed=0):
    rng = random.Random(seed)
    mcs = [q for q in quiz["questions"] if q.get("kind") == "mc" and len(q.get("choices", [])) == 4]
    targets = [0, 1, 2, 3]
    rng.shuffle(targets)
    for q, target in zip(mcs, targets * 2):
        correct = q["choices"][q["answer_index"]]
        wrong = [c for i, c in enumerate(q["choices"]) if i != q["answer_index"]]
        rng.shuffle(wrong)
        q["choices"] = wrong[:target] + [correct] + wrong[target:]
        q["answer_index"] = target
    return quiz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    quiz = json.load(open(a.quiz, encoding="utf-8"))
    shuffle_quiz(quiz, a.seed)
    json.dump(quiz, open(a.quiz, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("positions:", [q["answer_index"] for q in quiz["questions"] if q.get("kind") == "mc"])


if __name__ == "__main__":
    main()
