"""Messages the Mac sends by itself: grades and 'podcast ready'. Run: PYTHONPATH=src .venv/bin/python tests/test_messages.py
Telegram is replaced by a recorder; nothing is sent anywhere."""
import json
import os
import sys
import tempfile
from pathlib import Path
for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USERS", "LEASH_NOTIFY_DRY_RUN", "LEASH_UPLOAD_TOKEN"):
    os.environ.pop(k, None)
os.environ["LEASH_UPLOAD_TOKEN"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leash import notify, server

# ---- text builders
t = notify.quiz_text(2, 5, "Not quite. The answer was: The pace is too fast.")
assert t == "Question 2 of 5: Not quite. The answer was: The pace is too fast."
t = notify.quiz_text(5, 5, "You named the idea but stayed abstract.", True, 3, 6)
assert t.endswith("Quiz finished: 3 out of 6.") and t.startswith("Question 5 of 5:")
meta = {"title": "AI Threatens Crypto Security", "channel": "Bankless", "duration_min": 56.7}
tm = {"total_s": 1090.6}
ns = {"kept": {"main_ideas": 11, "definitions": 4, "facts": 13, "insights": 6}, "dropped_unsupported": 4}
t = notify.podcast_text(meta, tm, "partial", ns)
assert 'Podcast ready: "AI Threatens Crypto Security" (Bankless, 57 min), prepared in 18 min.' in t, t
assert "34 ideas, facts and definitions" in t and "4 dropped" in t and "some format checks were not met" in t and "quiz me" in t, t
assert "could not be made" in notify.podcast_text(meta, tm, "failed", ns) and "quiz me" not in notify.podcast_text(meta, tm, "failed", ns)
assert "passed" not in notify.podcast_text(meta, tm, "ok", ns) and "Every question is backed" in notify.podcast_text(meta, tm, "ok", ns)
assert notify.failure_text("https://youtu.be/x", "boom").startswith("Could not prepare the podcast")

# ---- the grade is sent by the server, and the agent is told to stay quiet (or to relay exact text if sending failed)
sent = []
def good(text, **kw): sent.append(text); return True, "sent"
def bad(text, **kw): return False, "no network"
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    ep = d / "episodes" / "demo-ep"; ep.mkdir(parents=True)
    quiz = {"questions": [
        {"kind": "mc", "question": "Why jittery?", "choices": ["The pace is too fast", "Yields are low", "Oil is falling", "Data is missing"],
         "answer_index": 0, "reference_answer": "The pace of change feels too fast.", "quote": "q1 quote words here"},
        {"kind": "mc", "question": "Which risk?", "choices": ["Privacy is gone", "Oil drops", "Markets calm", "Faster chains"],
         "answer_index": 0, "reference_answer": "Privacy is gone.", "quote": "q2 quote words here"}]}
    (ep / "quiz.json").write_text(json.dumps(quiz))
    (ep / "ingest.json").write_text(json.dumps({"quiz": {"ok": True, "status": "ok"}, "meta": {"title": "demo"}}))
    server.EPISODES, server.SESSIONS = d / "episodes", d / "sessions"
    server.notify.send_telegram = good
    r = server.answer_question("demo-ep", 1, "Yields are low")          # a wrong tap
    assert r["score"] == 0 and r["delivered"] is True and "feedback" not in r and "reference" not in r
    assert sent[-1] == "Question 1 of 2: Not quite. The answer was: The pace is too fast.", sent
    assert "Do not write anything about it" in r["action"] and "leashctl next demo-ep" in r["action"], r["action"]
    r = server.answer_question("demo-ep", 2, "Privacy is gone")         # last answer: the total goes in the same message
    assert r["score"] == 1 and sent[-1] == "Question 2 of 2: Correct.\nQuiz finished: 1 out of 2.", sent[-1]
    nx = server.next_question("demo-ep")
    assert nx["done"] and "already sent the total" in nx["action"], nx
    # a retake: the finished attempt is archived (not deleted) and the quiz starts again at question 1
    before = list((d / "sessions").glob("*.json"))
    rt = server.next_question("demo-ep", restart=True)
    assert rt["n"] == 1 and rt["kind"] == "mc", rt
    assert len(list((d / "sessions" / "archive").glob("demo-ep-*.json"))) == 1 and before and not list((d / "sessions").glob("*.json"))
    # sending fails: the reply carries the exact text instead, so the agent can still say the right thing
    server.notify.send_telegram = bad
    r = server.answer_question("demo-ep", 1, "The pace is too fast")
    assert r["delivered"] is False and r["say"] == "Correct." and 'exactly this text' in r["action"], r

# ---- podcast ready message from a finished job; a message problem must not fail the job
sent.clear()
server.notify.send_telegram = good
server.ingest.run = lambda *a, **k: {"meta": meta, "words": 9778, "timings": tm, "quiz": {"status": "partial", "ok": False},
                                     "pages": ["x"], "notes_stats": ns}
server.JOBS["j1"] = {"status": "running", "log": []}
server.run_job("j1", "https://youtu.be/abc", None)
j = server.JOBS["j1"]
assert j["status"] == "done" and j["notified"] is True and "usable" in j["say"], j
assert sent and sent[-1].startswith('Podcast ready: "AI Threatens Crypto Security"'), sent
server.ingest.run = lambda *a, **k: {"meta": meta, "words": 1, "timings": {}, "quiz": None, "pages": [], "notes_stats": None}
server.JOBS["j2"] = {"status": "running", "log": []}
server.run_job("j2", "https://youtu.be/abc", None)
assert server.JOBS["j2"]["status"] == "done"
def boom(*a, **k): raise RuntimeError("download failed")
server.ingest.run = boom
server.JOBS["j3"] = {"status": "running", "log": []}
server.run_job("j3", "https://youtu.be/zzz", None)
assert server.JOBS["j3"]["status"] == "failed" and sent[-1].startswith("Could not prepare the podcast"), sent[-1]
print("message tests passed")
