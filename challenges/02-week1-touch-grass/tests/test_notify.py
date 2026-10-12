"""Run: PYTHONPATH=src .venv/bin/python tests/test_notify.py"""
import os
import sys
from pathlib import Path
for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USERS", "LEASH_NOTIFY_DRY_RUN"):
    os.environ.pop(k, None)  # never let a test reach the real bot
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leash import notify

w = {"kind": "podcast", "distance_m": 3151, "duration_s": 2117, "untracked_s": 1}
t = notify.walk_text(w, ["Check out the 200 week average", "Check out TDR Pro"], [{"label": "First walk"}],
                     {"label": "5 km", "how": "Walk 5 km in total"}, {"title": "GPT-6 Astra", "ready": True, "done": False})
assert "3.15 km in 35 min" in t and "2 voice ideas saved" in t and "New medal: First walk." in t, t
assert 'quiz on "GPT-6 Astra" is ready' in t and "Next medal: 5 km (walk 5 km in total)." in t, t
assert "could not track" not in t
# untracked time is stated, a dog walk has no quiz line, no ideas means no idea lines
t2 = notify.walk_text({"kind": "dog", "distance_m": 420, "duration_s": 600, "untracked_s": 300}, [], [], None, None)
assert "Dog walk saved: 420 m in 10 min." in t2 and "could not track 5 min" in t2 and "quiz" not in t2.lower() and "voice" not in t2, t2
# finished quiz
t3 = notify.walk_text(w, [], [], None, {"title": "x", "ready": False, "done": True, "total": 5, "max": 6})
assert "Quiz finished: 5 out of 6." in t3
assert len(notify.snippet("word " * 50)) <= 70 and notify.snippet("short") == "short"
ok, why = notify.send_telegram("x", token="", chat_id="")
assert not ok and "not set" in why
print("notify tests passed")
print("--- sample message ---"); print(t)
