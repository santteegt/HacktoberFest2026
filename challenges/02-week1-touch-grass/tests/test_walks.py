"""Run: PYTHONPATH=src .venv/bin/python tests/test_walks.py (plain asserts, no test runner needed)."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leash import walks

# Anonymised copies of four real walks (scripts/make-fixtures.py): rotated, moved far away and re-timed.
# The originals contain the author's walking routes and stay out of the repository.
RESULTS = Path(__file__).resolve().parent / "fixtures"

# 1. real tracks from the 2026-10-09 walks: numbers must match what the recorded reports said (within jitter rules)
for i, (lo, hi, tracked_lo) in {1: (850, 1060, 540), 4: (700, 990, 1300)}.items():
    st = walks.track_stats(walks.parse_gpx((RESULTS / f"walk-test-{i}.gpx").read_text()))
    assert lo <= st["distance_m"] <= hi, (i, st)
    assert st["tracked_s"] >= tracked_lo, (i, st)
# walk 2 and 3 lost the GPS when the page was hidden: tracked time must be far below the walk length
st3 = walks.track_stats(walks.parse_gpx((RESULTS / "walk-test-3.gpx").read_text()))
assert st3["tracked_s"] < 200, st3   # 8m44s walk, GPS only while the screen was on

# 2. save / idempotence / clips / medals
with tempfile.TemporaryDirectory() as d:
    gpx = (RESULTS / "walk-test-4.gpx").read_text()
    body = {"id": "walk-0001-abcd", "kind": "dog", "started_at": "2026-10-09T16:36:57Z", "ended_at": "2026-10-09T16:59:37Z",
            "tz_offset_min": -300, "gpx": gpx}
    r1 = walks.save_walk(d, body); r2 = walks.save_walk(d, body)
    assert r1["distance_m"] == r2["distance_m"] and r1["duration_s"] == 1360
    walks.add_clip(d, "walk-0001-abcd", 1, b"x", "webm", "hello idea", "wiki/note-x.md")
    walks.add_clip(d, "walk-0001-abcd", 1, b"x", "webm", "hello idea", "wiki/note-x.md")  # same n replaces
    ws = walks.list_walks(d)
    assert len(ws) == 1 and len(ws[0]["clips"]) == 1
    m = walks.medals(ws, [{"answers": {str(n): {"score": 1, "max": 1} for n in range(1, 5)} | {"5": {"score": 2, "max": 2}}}])
    ids = {x["id"] for x in m["earned"]}
    assert {"first-walk", "quiz-first", "quiz-perfect"} <= ids and "km-10" not in ids, ids
    for bad in ("../x", "a", "x/y/z"):
        try: walks.save_walk(d, {**body, "id": bad}); raise SystemExit("bad id accepted")
        except ValueError: pass
    try: walks.save_walk(d, {**body, "kind": "run"}); raise SystemExit("bad kind accepted")
    except ValueError: pass

# 3. streaks use the walker's local day
from datetime import date
assert walks._best_streak([date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 4), date(2026, 10, 5), date(2026, 10, 6)]) == 3
print("walks tests passed")

# 4. stats: weekly buckets, kind split, current streak, medal progress (fixed "today" so it is deterministic)
from datetime import date
def _w(day_iso, kind, dist, dur, clips=0):
    return {"id": "w" + day_iso, "kind": kind, "started_at": day_iso + "T20:00:00+00:00", "tz_offset_min": 0,
            "duration_s": dur, "distance_m": dist, "tracked_s": dur, "untracked_s": 0, "clips": [{}] * clips}
ws = [_w("2026-10-09", "dog", 2000, 1800, 2), _w("2026-10-08", "podcast", 3200, 2400), _w("2026-10-02", "walk", 1000, 600),
      _w("2026-08-01", "walk", 9999, 600)]   # the last one is older than 8 weeks
st = walks.stats(ws, [], today=date(2026, 10, 10))
assert len(st["weeks"]) == 8 and st["weeks"][-1]["start"] == "2026-10-05" and st["weeks"][0]["start"] == "2026-08-17"
assert st["weeks"][-1]["walks"] == 2 and abs(st["weeks"][-1]["km"] - 5.2) < 0.01, st["weeks"][-1]
assert st["weeks"][-2]["walks"] == 1 and sum(b["walks"] for b in st["weeks"]) == 3   # old walk is outside
assert st["by_kind"]["dog"]["walks"] == 1 and st["by_kind"]["walk"]["walks"] == 2   # by_kind counts every walk
assert st["current_streak_days"] == 2                     # Oct 8 and Oct 9, today is Oct 10 (no walk yet today)
assert walks._current_streak([date(2026, 10, 10), date(2026, 10, 9)], date(2026, 10, 10)) == 2
assert walks._current_streak([date(2026, 10, 7)], date(2026, 10, 10)) == 0
m = {x["id"]: x for x in st["medals"]}
assert len(st["medals"]) == len(walks.MEDALS) == 16
# total 16.2 km over all four walks (medals count every walk, not just the last 8 weeks)
assert m["km-10"]["earned"] and m["km-10"]["progress"] == 10 and not m["km-25"]["earned"], m["km-25"]
assert abs(m["km-25"]["progress"] - 16.2) < 0.01, m["km-25"]
assert m["long-walk"]["unit"] == "km" and m["long-walk"]["progress"] == 3 and m["long-walk"]["earned"]   # 9999 m walk, capped at the target
assert m["dog-1h"]["progress"] == 30 and not m["dog-1h"]["earned"] and m["dog-1h"]["target"] == 60
assert m["ideas-5"]["progress"] == 2 and m["ideas-5"]["family"] == "ideas"
print("stats tests passed")

# 5. the phone app's offline medal list and sprites must match the server's medals
import re
app = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text()
badges = (Path(__file__).resolve().parents[1] / "app" / "assets" / "badges.svg").read_text()
for mid, label, how, _ in walks.MEDALS:
    assert f"['{mid}', '{label}', '{how}'," in app, f"app/index.html is missing or has a different copy of medal {mid}"
    assert f'id="b-{mid}"' in badges, f"badge art for {mid} is missing"
assert set(re.findall(r'id="b-([a-z0-9-]+)"', badges)) == {m[0] for m in walks.MEDALS}, "badges.svg has extra or missing symbols"
fams = {v[0] for v in walks.PROGRESS.values()}
sections = set(re.findall(r"'(\w+)'", re.search(r"const SECTIONS = (.*)", app).group(1)))
assert fams <= sections, f"medal families not shown in the app: {fams - sections}"
print("app sync tests passed")

# 6. minimum walk length (5 minutes): rejected on save, and old short files never count
import tempfile, json
with tempfile.TemporaryDirectory() as d:
    gpx = (RESULTS / "walk-test-4.gpx").read_text()
    base = {"id": "wshort-0001-x", "kind": "dog", "tz_offset_min": -300, "gpx": gpx}
    assert walks.MIN_WALK_S == 300
    short = {**base, "started_at": "2026-10-10T16:00:00Z", "ended_at": "2026-10-10T16:04:59Z"}
    assert walks.duration_of(short) == 299
    try: walks.save_walk(d, short); raise SystemExit("a 4m59s walk was saved")
    except ValueError as e: assert "5 minutes" in str(e)
    ok = {**base, "id": "wlong-0001-xyz", "started_at": "2026-10-10T16:00:00Z", "ended_at": "2026-10-10T16:05:00Z"}
    assert walks.save_walk(d, ok)["duration_s"] == 300          # exactly 5 minutes counts
    # a short walk file from before the rule exists on disk but is not listed
    old = Path(d, "wold-short-001"); old.mkdir()
    old.joinpath("walk.json").write_text(json.dumps({"id": "wold-short-001", "kind": "podcast", "started_at": "2026-10-09T04:32:11+00:00",
                                                     "duration_s": 5, "distance_m": 0, "clips": []}))
    ids = [w["id"] for w in walks.list_walks(d)]
    assert ids == ["wlong-0001-xyz"], ids
print("minimum walk tests passed")
