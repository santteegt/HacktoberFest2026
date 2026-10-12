"""Run the podcast-quiz evals against a local model and write skill-creator style results.

Layout: <workspace>/iteration-N/eval-<name>/{with_skill,without_skill}/{outputs/, timing.json, grading.json}
Programmatic grading only: every expectation is checked by code, with evidence.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from . import quiz as Q

V = Q.verify_quiz
ATTRIB = re.compile(r"\b(host|guest|speaker|according to|argued|argues|says|said|describes|described|suggests|suggested|thinks|believes)\b", re.I)
ADVICE = re.compile(r"\b(should (i|you|they) (buy|sell|invest|hold)|invest in|price (will|would)|predict|where will the price|how high will)\b", re.I)
WALK = re.compile(r"\b(walk|outside|outdoors|saw|see|seen|heard|hear|felt|feel|noticed|notice|dog|park|today|around you)\b", re.I)
TIME = re.compile(r"\d{1,2}:\d{2}:\d{2}|-->")


def check(text, quiz, errors, warnings, twords):
    qs = (quiz or {}).get("questions") or []
    mcs = [q for q in qs if q.get("kind") == "mc"]
    fls = [q for q in qs if q.get("kind") == "field_link"]
    if text.startswith("Quiz has exactly 4"):
        ok = len(qs) == 5 and len(mcs) == 4 and len(fls) == 1 and qs[-1].get("kind") == "field_link"
        return ok, f"{len(mcs)} mc, {len(fls)} field_link, last kind = {qs[-1].get('kind') if qs else None}"
    if "quote is found" in text:
        bad = [e for e in errors if "quote" in e]
        return not bad, "all quotes found" if not bad else "; ".join(bad[:3])
    if text.startswith("Questions are short"):
        bad = [e for e in errors if "too long" in e or "choice is" in e]
        return not bad, "within limits" if not bad else "; ".join(bad[:3])
    if text.startswith("Quotes are spread"):
        bad = [w for w in warnings if "one part of the episode" in w]
        return not bad and len(qs) >= 4, "quotes come from several parts" if not bad else bad[0]
    if text.startswith("Each multiple-choice question has 4 distinct"):
        bad = [e for e in errors if "choices" in e or "above" in e]
        return not bad and len(mcs) > 0, "choices valid" if not bad else "; ".join(bad[:3])
    if text.startswith("The field-link question lists"):
        if not fls:
            return False, "no field_link question"
        f = fls[0]
        terms = [t for t in (f.get("concept_terms") or []) if str(t).strip()]
        return 3 <= len(terms) <= 6 and bool(WALK.search(f.get("question", ""))), f"{len(terms)} terms; question: {f.get('question', '')[:90]}"
    if text.startswith("The correct choice is not the longest"):
        bad = [w for w in warnings if "longest" in w]
        return not bad, "no length bias" if not bad else bad[0]
    if text.startswith("The correct answers are spread"):
        pos = {q.get("answer_index") for q in mcs}
        return len(pos) >= 3, f"positions used: {sorted(p for p in pos if p is not None)}"
    if text.startswith("No question asks for investment advice"):
        hit = [q["question"] for q in qs if ADVICE.search(q.get("question", ""))]
        return not hit, "none found" if not hit else hit[0][:100]
    if text.startswith("At least three questions attribute"):
        n = sum(1 for q in qs if ATTRIB.search(q.get("question", "")))
        return n >= 3, f"{n} of {len(qs)} questions attribute a view"
    if text.startswith("No timestamps or cue numbers"):
        hit = [q.get("question", "") + " | " + q.get("quote", "") for q in qs if TIME.search(q.get("question", "") + q.get("quote", ""))]
        return not hit, "clean" if not hit else hit[0][:100]
    return False, "no checker for this expectation"


def run(skill_dir: Path, workspace: Path, iteration: int, model: str, only=None, configs=("with_skill", "without_skill")):
    spec = json.loads((skill_dir / "evals" / "evals.json").read_text())
    it_dir = workspace / f"iteration-{iteration}"
    for ev in spec["evals"]:
        if only and ev["name"] not in only:
            continue
        raw = (skill_dir / ev["files"][0]).read_text()
        twords = V.transcript_words(raw)
        ev_dir = it_dir / f"eval-{ev['name']}"
        ev_dir.mkdir(parents=True, exist_ok=True)
        (ev_dir / "eval_metadata.json").write_text(json.dumps(
            {"eval_id": ev["id"], "eval_name": ev["name"], "prompt": ev["prompt"], "assertions": ev["expectations"]}, indent=2))
        for config, use_skill in (("with_skill", True), ("without_skill", False)):
            if config not in configs:
                continue
            out = ev_dir / config / "run-1"
            (out / "outputs").mkdir(parents=True, exist_ok=True)
            print(f"[{ev['name']}] {config} ...", flush=True)
            res = Q.generate(raw, model, use_skill=use_skill)
            quiz = res["quiz"] or {}
            errors, warnings, info = V.verify(quiz, twords) if res["quiz"] else (["no valid JSON produced"], [], {})
            (out / "outputs" / "quiz.json").write_text(json.dumps(quiz, indent=2, ensure_ascii=False))
            (out / "outputs" / "verification.json").write_text(json.dumps(
                {"final": {"errors": errors, "warnings": warnings}, "attempts": res["attempts"]}, indent=2))
            (out / "timing.json").write_text(json.dumps(
                {"total_tokens": res["total_tokens"], "duration_ms": int(res["duration_s"] * 1000), "total_duration_seconds": res["duration_s"]}, indent=2))
            exps = []
            for t in ev["expectations"]:
                ok, evidence = check(t, quiz, errors, warnings, twords)
                exps.append({"text": t, "passed": bool(ok), "evidence": evidence})
            passed = sum(1 for e in exps if e["passed"])
            first = res["attempts"][0] if res["attempts"] else {}
            grading = {"expectations": exps,
                       "summary": {"passed": passed, "failed": len(exps) - passed, "total": len(exps), "pass_rate": round(passed / len(exps), 2)},
                       "execution_metrics": {"total_steps": len(res["attempts"]), "errors_encountered": len(errors),
                                             "output_chars": len(json.dumps(quiz))},
                       "timing": {"total_duration_seconds": res["duration_s"]},
                       "user_notes_summary": {"uncertainties": [], "needs_review": [],
                                              "workarounds": [f"first attempt errors: {first.get('errors')}"] if use_skill else []}}
            (out / "grading.json").write_text(json.dumps(grading, indent=2))
            print(f"    {passed}/{len(exps)} passed, {len(res['attempts'])} attempt(s), {res['duration_s']} s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--model", default="gemma4:12b-it-qat")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--configs", nargs="*", default=["with_skill", "without_skill"])
    ap.add_argument("--workspace", default=str(Path(__file__).resolve().parents[2] / "data" / "skill-eval" / "podcast-quiz-workspace"))
    a = ap.parse_args()
    run(Q.SKILL_DIR, Path(a.workspace), a.iteration, a.model, a.only, a.configs)
