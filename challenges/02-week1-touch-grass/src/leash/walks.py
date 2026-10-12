"""Walk sessions from the phone app, and the medals they earn.

Everything here is plain code: distances, durations, streaks and medals are computed from the
GPX track and the quiz session files, never by a language model.

Layout (all under data/walks/<walk_id>/): walk.json, track.gpx, clips/<n>.<ext>, clips/<n>.txt
"""
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
KINDS = ("podcast", "dog", "walk")
MIN_WALK_S = 300      # a session shorter than 5 minutes is not saved and does not count
MAX_ACC_M = 30        # ignore fixes the phone itself says are worse than this
MIN_STEP_M = 3        # ignore jitter smaller than this
MAX_SPEED_MS = 6      # ignore jumps above 21 km/h: this is a walking and jogging app
MAX_FIX_GAP_S = 15    # a longer silence between fixes counts as untracked time
MAX_STEP_GAP_S = 30   # a step across a longer silence is not counted as walked distance

TRKPT = re.compile(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"[^>]*>(.*?)</trkpt>', re.S)


def _hav(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def parse_gpx(text):
    """[(epoch_seconds, lat, lon, accuracy_m or None)] in file order."""
    pts = []
    for m in TRKPT.finditer(text):
        body = m.group(3)
        t = re.search(r"<time>([^<]+)</time>", body)
        if not t:
            continue
        try:
            ts = datetime.fromisoformat(t.group(1).replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        acc = re.search(r"<acc>([\d.]+)</acc>", body)
        pts.append((ts, float(m.group(1)), float(m.group(2)), float(acc.group(1)) if acc else None))
    return pts


def track_stats(pts):
    """Distance on usable fixes, seconds actually tracked, fix count, median accuracy."""
    good = [p for p in pts if p[3] is None or p[3] <= MAX_ACC_M]
    dist, anchor = 0.0, None
    for p in good:
        if anchor is None:
            anchor = p
            continue
        step = _hav(anchor[1:3], p[1:3])
        dt = max(p[0] - anchor[0], 0.001)
        if dt > MAX_STEP_GAP_S:
            anchor = p  # silence (screen off, app switched): do not credit distance nobody tracked
            continue
        if step < MIN_STEP_M:
            continue
        if step / dt > MAX_SPEED_MS:
            continue  # GPS jump
        dist += step
        anchor = p
    tracked = 0.0
    for a, b in zip(pts, pts[1:]):
        d = b[0] - a[0]
        if 0 < d <= MAX_FIX_GAP_S:
            tracked += d
    accs = sorted(p[3] for p in pts if p[3] is not None)
    return {
        "distance_m": round(dist),
        "tracked_s": round(tracked),
        "fixes": len(pts),
        "good_fixes": len(good),
        "median_acc_m": round(accs[len(accs) // 2]) if accs else None,
    }


def _walk_dir(root, walk_id):
    if not ID_RE.match(walk_id or ""):
        raise ValueError("bad walk id")
    return Path(root) / walk_id


def duration_of(body):
    start = datetime.fromisoformat(str(body["started_at"]).replace("Z", "+00:00"))
    end = datetime.fromisoformat(str(body["ended_at"]).replace("Z", "+00:00"))
    return max(0, round((end - start).total_seconds()))


def save_walk(root, body):
    """Store a walk sent by the phone. Idempotent: the same id overwrites the same folder.
    Distance and tracked time are recomputed here from the GPX; the phone's numbers are only kept as a claim."""
    wid = str(body.get("id", ""))
    d = _walk_dir(root, wid)
    kind = body.get("kind", "walk")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    gpx = str(body.get("gpx", ""))
    if len(gpx) > 5_000_000:
        raise ValueError("track too large")
    pts = parse_gpx(gpx)
    stats = track_stats(pts)
    start = datetime.fromisoformat(str(body["started_at"]).replace("Z", "+00:00"))
    end = datetime.fromisoformat(str(body["ended_at"]).replace("Z", "+00:00"))
    duration_s = max(0, round((end - start).total_seconds()))
    if duration_s < MIN_WALK_S:
        raise ValueError(f"a walk must last at least {MIN_WALK_S // 60} minutes to be saved")
    prev = {}
    if (d / "walk.json").exists():
        prev = json.loads((d / "walk.json").read_text())
    rec = {
        "id": wid, "kind": kind, "started_at": start.isoformat(), "ended_at": end.isoformat(),
        "tz_offset_min": int(body.get("tz_offset_min", 0)),
        "duration_s": duration_s, **stats,
        "untracked_s": max(0, duration_s - stats["tracked_s"]),
        "podcast_slug": body.get("podcast_slug") or None,
        "clip_count": max(0, int(body.get("clip_count", 0) or 0)),
        "notified_at": prev.get("notified_at"),
        "lookups": prev.get("lookups", []),
        "client": {k: body.get(k) for k in ("hidden_s", "gaps", "errors", "battery_start", "battery_end", "user_agent")},
        "clips": prev.get("clips", []),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    d.mkdir(parents=True, exist_ok=True)
    (d / "walk.json").write_text(json.dumps(rec, indent=2))
    (d / "track.gpx").write_text(gpx)
    return rec


def add_clip(root, walk_id, n, data, ext, text, page):
    d = _walk_dir(root, walk_id)
    if not (d / "walk.json").exists():
        raise ValueError("unknown walk; send the walk first")
    (d / "clips").mkdir(exist_ok=True)
    (d / "clips" / f"{n}.{ext}").write_bytes(data)
    (d / "clips" / f"{n}.txt").write_text(text)
    rec = json.loads((d / "walk.json").read_text())
    rec["clips"] = [c for c in rec["clips"] if c["n"] != n] + [{"n": n, "chars": len(text), "page": page}]
    rec["clips"].sort(key=lambda c: c["n"])
    (d / "walk.json").write_text(json.dumps(rec, indent=2))
    return rec


def mark_notified(root, walk_id, when_iso):
    d = _walk_dir(root, walk_id)
    rec = json.loads((d / "walk.json").read_text())
    rec["notified_at"] = when_iso
    (d / "walk.json").write_text(json.dumps(rec, indent=2))


def set_lookups(root, walk_id, lookups):
    d = _walk_dir(root, walk_id)
    rec = json.loads((d / "walk.json").read_text())
    rec["lookups"] = lookups
    (d / "walk.json").write_text(json.dumps(rec, indent=2))


def list_walks(root):
    """Saved walks that count, newest first. Files for walks shorter than MIN_WALK_S (made before the rule
    existed) stay on disk but are not listed, so they never reach totals, streaks, medals or messages."""
    out = []
    for p in Path(root).glob("*/walk.json") if Path(root).exists() else []:
        try:
            w = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        if w.get("duration_s", 0) >= MIN_WALK_S:
            out.append(w)
    return sorted(out, key=lambda w: w["started_at"], reverse=True)


# ---- medals -------------------------------------------------------------------------------------

def _local_day(w):
    t = datetime.fromisoformat(w["started_at"]) + timedelta(minutes=w.get("tz_offset_min", 0))
    return t.date()


def _best_streak(days):
    best = cur = 0
    prev = None
    for d in sorted(set(days)):
        cur = cur + 1 if prev and (d - prev).days == 1 else 1
        best = max(best, cur)
        prev = d
    return best


def totals(walks, sessions):
    """The numbers medals are decided from."""
    dog_s = sum(w["duration_s"] for w in walks if w["kind"] == "dog")
    answers = [a for s in sessions for a in s.get("answers", {}).values()]
    return {
        "walks": len(walks),
        "km": round(sum(w["distance_m"] for w in walks) / 1000, 2),
        "minutes": round(sum(w["duration_s"] for w in walks) / 60),
        "longest_m": max([w["distance_m"] for w in walks], default=0),
        "dog_min": round(dog_s / 60),
        "best_streak_days": _best_streak([_local_day(w) for w in walks]),
        "voice_ideas": sum(len(w.get("clips", [])) for w in walks),
        "quizzes_finished": sum(1 for s in sessions if len(s.get("answers", {})) >= 5),
        "perfect_quizzes": sum(1 for s in sessions if len(s.get("answers", {})) >= 5
                               and all(a["score"] == a["max"] for a in s["answers"].values())),
        "right_answers": sum(a["score"] for a in answers),
    }


# (id, label, how it is earned, test on the totals)
MEDALS = [
    ("first-walk", "First walk", "Finish one walk", lambda t: t["walks"] >= 1),
    ("km-5", "5 km", "Walk 5 km in total", lambda t: t["km"] >= 5),
    ("km-10", "10 km", "Walk 10 km in total", lambda t: t["km"] >= 10),
    ("km-25", "25 km", "Walk 25 km in total", lambda t: t["km"] >= 25),
    ("km-50", "50 km", "Walk 50 km in total", lambda t: t["km"] >= 50),
    ("long-walk", "Long walk", "One walk of 3 km or more", lambda t: t["longest_m"] >= 3000),
    ("dog-1h", "An hour with the dog", "60 minutes of dog walks", lambda t: t["dog_min"] >= 60),
    ("dog-5h", "Five hours with the dog", "300 minutes of dog walks", lambda t: t["dog_min"] >= 300),
    ("streak-3", "Three days running", "Walk on 3 days in a row", lambda t: t["best_streak_days"] >= 3),
    ("streak-7", "A week running", "Walk on 7 days in a row", lambda t: t["best_streak_days"] >= 7),
    ("ideas-5", "Five ideas aloud", "Capture 5 voice ideas on walks", lambda t: t["voice_ideas"] >= 5),
    ("ideas-25", "Twenty-five ideas aloud", "Capture 25 voice ideas on walks", lambda t: t["voice_ideas"] >= 25),
    ("quiz-first", "First quiz", "Finish a quiz", lambda t: t["quizzes_finished"] >= 1),
    ("quiz-perfect", "Perfect quiz", "Every answer right in one quiz", lambda t: t["perfect_quizzes"] >= 1),
    ("right-10", "Ten right answers", "10 correct quiz points in total", lambda t: t["right_answers"] >= 10),
    ("right-25", "Twenty-five right answers", "25 correct quiz points in total", lambda t: t["right_answers"] >= 25),
]


def medals(walks, sessions):
    t = totals(walks, sessions)
    earned = [{"id": i, "label": label, "how": how} for i, label, how, test in MEDALS if test(t)]
    todo = [{"id": i, "label": label, "how": how} for i, label, how, test in MEDALS if not test(t)]
    return {"totals": t, "earned": earned, "next": todo[:3]}


# ---- activity stats and medal progress (for the app's Activity and Badges views) --------------

# id -> (family, key in totals, divisor to display unit, target, unit)
PROGRESS = {
    "first-walk": ("first", "walks", 1, 1, "walks"),
    "km-5": ("distance", "km", 1, 5, "km"), "km-10": ("distance", "km", 1, 10, "km"),
    "km-25": ("distance", "km", 1, 25, "km"), "km-50": ("distance", "km", 1, 50, "km"),
    "long-walk": ("long", "longest_m", 1000, 3, "km"),
    "dog-1h": ("dog", "dog_min", 1, 60, "min"), "dog-5h": ("dog", "dog_min", 1, 300, "min"),
    "streak-3": ("streak", "best_streak_days", 1, 3, "days"), "streak-7": ("streak", "best_streak_days", 1, 7, "days"),
    "ideas-5": ("ideas", "voice_ideas", 1, 5, "ideas"), "ideas-25": ("ideas", "voice_ideas", 1, 25, "ideas"),
    "quiz-first": ("quiz", "quizzes_finished", 1, 1, "quizzes"),
    "quiz-perfect": ("quiz", "perfect_quizzes", 1, 1, "quizzes"),
    "right-10": ("answers", "right_answers", 1, 10, "points"), "right-25": ("answers", "right_answers", 1, 25, "points"),
}


def medal_progress(t):
    out = []
    for mid, label, how, test in MEDALS:
        family, key, div, target, unit = PROGRESS[mid]
        value = t[key] / div
        out.append({"id": mid, "label": label, "how": how, "family": family, "earned": bool(test(t)),
                    "progress": round(min(value, target), 2), "target": target, "unit": unit})
    return out


def _current_streak(days, today):
    have = set(days)
    d = today if today in have else today - timedelta(days=1)
    n = 0
    while d in have:
        n += 1
        d -= timedelta(days=1)
    return n


def stats(walks, sessions, today=None, weeks=8):
    """today: the walker's local date (default: this machine's local date)."""
    today = today or datetime.now().astimezone().date()
    monday = today - timedelta(days=today.weekday())
    starts = [monday - timedelta(weeks=weeks - 1 - i) for i in range(weeks)]
    buckets = {s: {"start": s.isoformat(), "km": 0.0, "minutes": 0, "walks": 0} for s in starts}
    by_kind = {k: {"walks": 0, "km": 0.0, "minutes": 0} for k in KINDS}
    for w in walks:
        day = _local_day(w)
        wk = day - timedelta(days=day.weekday())
        if wk in buckets:
            b = buckets[wk]
            b["km"] += w["distance_m"] / 1000
            b["minutes"] += w["duration_s"] / 60
            b["walks"] += 1
        k = by_kind.get(w["kind"])
        if k is not None:
            k["walks"] += 1
            k["km"] += w["distance_m"] / 1000
            k["minutes"] += w["duration_s"] / 60
    for b in buckets.values():
        b["km"], b["minutes"] = round(b["km"], 2), round(b["minutes"])
    for k in by_kind.values():
        k["km"], k["minutes"] = round(k["km"], 2), round(k["minutes"])
    t = totals(walks, sessions)
    return {
        "weeks": [buckets[s] for s in starts],
        "by_kind": by_kind,
        "current_streak_days": _current_streak([_local_day(w) for w in walks], today),
        "totals": t,
        "medals": medal_progress(t),
    }
