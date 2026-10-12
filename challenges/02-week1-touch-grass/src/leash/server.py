"""Local tool server for the Hermes agent (and later the PWA). Runs on the Mac, bound to loopback.

Every request needs  Authorization: Bearer $LEASH_UPLOAD_TOKEN. The VM reaches it through a reverse SSH tunnel.
Secrets such as the SerpApi key stay on this side; the agent only sees results.
"""
import hmac
import json
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import ideas, ingest, lookups, notify, quiz, search, stt, walks
from .envfile import load_env

PROJECT = Path(__file__).resolve().parents[2]
VAULT = Path(os.environ.get("LEASH_VAULT") or PROJECT / "second-brain")
EPISODES = PROJECT / "data" / "episodes"
SESSIONS = PROJECT / "data" / "sessions"
WALKS = PROJECT / "data" / "walks"
APP = PROJECT / "app"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".webmanifest": "application/manifest+json",
         ".png": "image/png", ".svg": "image/svg+xml", ".json": "application/json"}
JOBS: dict = {}
LETTERS = "ABCD"


def run_job(job_id, source, title):
    job = JOBS[job_id]
    try:
        res = ingest.run(source, vault=VAULT, title=title, log=lambda m: job["log"].append(str(m)))
        st = (res.get("quiz") or {}).get("status", "failed")
        say = {"ok": "The podcast is ready and the quiz passed all its checks.",
               "partial": "The podcast is ready. The quiz is usable and every question is backed by a quote from the episode, "
                          "but it did not pass every format check (some answers may be easier to guess).",
               }.get(st, "The notes are ready, but the quiz could not be made for this episode.")
        job.update(status="done", say=say, result={k: res[k] for k in ("meta", "words", "timings", "quiz", "pages")})
    except Exception as e:  # noqa: BLE001
        job.update(status="failed", error=str(e)[:400])
        notify.send_telegram(notify.failure_text(source, e))
    else:
        try:   # a problem with the message must never turn a finished podcast into a failed job
            ok, detail = notify.send_telegram(notify.podcast_text(res["meta"], res["timings"], st, res.get("notes_stats")))
            job["notified"] = bool(ok)
            print(f"{datetime.now():%H:%M:%S} podcast-ready message for job {job_id}: {'sent' if ok else 'NOT sent (' + detail + ')'}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{datetime.now():%H:%M:%S} podcast-ready message failed: {type(e).__name__}", flush=True)
    job["finished"] = time.time()


def episode_dirs():
    return sorted(EPISODES.glob("*/ingest.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def quiz_status(slug):
    """ok | partial | failed | none, from the episode's ingest record (older records only have `ok`)."""
    try:
        q = json.loads((EPISODES / slug / "ingest.json").read_text()).get("quiz") or {}
    except (OSError, ValueError):
        return "none"
    return q.get("status") or ("ok" if q.get("ok") else "failed" if q else "none")


def load_quiz(slug):
    if quiz_status(slug) in ("failed", "none"):
        return None   # a quiz that did not pass its hard checks is never served
    p = EPISODES / slug / "quiz.json"
    return json.loads(p.read_text()) if p.exists() else None


def _norm(s):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def pick_choice(choices, text):
    """Index of the choice a learner meant, or None when unclear. Accepts a tapped button
    (its exact text, "2", or "2. text"), a letter ("C", "c)", "my answer is C"), or a spoken
    phrase that shares words with exactly the best-matching choice."""
    t = text.strip()
    norm = [_norm(c) for c in choices]
    if _norm(t) in norm:
        return norm.index(_norm(t))
    m = re.match(r"^\s*([1-4a-dA-D])\s*[.):\-]?\s*(.*)$", t)
    if m:
        rest = _norm(m.group(2))
        if rest in norm:
            return norm.index(rest)
        if not rest:
            c = m.group(1).upper()
            return int(c) - 1 if c.isdigit() else LETTERS.index(c)
    m = re.search(r"\b(?:answer|option|choice)\s+(?:is\s+)?([a-dA-D])\b", t)
    if m:
        return LETTERS.index(m.group(1).upper())
    words = {w for w in _norm(t).split() if len(w) > 2}
    best = max(range(len(choices)), key=lambda i: len(words & set(norm[i].split())))
    return best if words & set(norm[best].split()) else None


def session_path(slug):
    return SESSIONS / f"{slug}-{datetime.now(timezone.utc):%Y%m%d}.json"


def load_sessions():
    out = []
    for p in sorted(SESSIONS.glob("*.json")) if SESSIONS.exists() else []:
        try:
            out.append(json.loads(p.read_text()))
        except (OSError, ValueError):
            continue
    return out


def walks_summary():
    ws = walks.list_walks(WALKS)
    return {"walks": [{k: w[k] for k in ("id", "kind", "started_at", "duration_s", "distance_m", "tracked_s",
                                          "untracked_s", "podcast_slug")} | {"clips": len(w.get("clips", []))}
                      for w in ws[:10]],
            **walks.medals(ws, load_sessions())}


NOTIFY_LOCK = threading.Lock()


MAX_LOOKUPS_PER_WALK = 3


def run_lookup(query):
    """One web search for a note that asked for it. Never raises; returns {"query", "results"|"error"}."""
    try:
        res = search.search(query, n=3)
    except Exception as e:  # noqa: BLE001
        return {"query": query, "error": "the search service did not answer"}
    if res.get("error"):
        return {"query": query, "error": str(res["error"])[:120]}
    return {"query": query, "results": [{"title": r["title"], "link": r["link"]} for r in res.get("results", [])],
            "left_today": res.get("searches_left_today")}


def walk_lookups(rec, walk_id):
    """Search requests found in this walk's voice notes, run at most once each (stored in walk.json, so a
    failed Telegram send that is retried never spends SerpApi quota twice)."""
    done = {l["n"]: l for l in rec.get("lookups", [])}
    changed = False
    for c in rec.get("clips", []):
        if c["n"] in done or len(done) >= MAX_LOOKUPS_PER_WALK:
            continue
        f = WALKS / walk_id / "clips" / f"{c['n']}.txt"
        q = lookups.extract_query(f.read_text()) if f.exists() else None
        if q:
            done[c["n"]] = {"n": c["n"], **run_lookup(q)}
            changed = True
    out = [done[k] for k in sorted(done)]
    if changed:
        walks.set_lookups(WALKS, walk_id, out)
    return out


def notify_walk(walk_id, force=False):
    """Tell the user on Telegram that a walk arrived. Sent once per walk, after its voice notes are in
    (or after a timeout if some never arrive). Plain code builds the text."""
    with NOTIFY_LOCK:
        wp = WALKS / walk_id / "walk.json"
        if not wp.exists():
            return None
        rec = json.loads(wp.read_text())
        if rec.get("notified_at"):
            return None
        if not force and len(rec.get("clips", [])) < rec.get("clip_count", 0):
            return None  # still waiting for voice notes
        all_walks, sessions = walks.list_walks(WALKS), load_sessions()
        before = walks.medals([w for w in all_walks if w["id"] != walk_id], sessions)
        after = walks.medals(all_walks, sessions)
        had = {m["id"] for m in before["earned"]}
        snippets = []
        for c in rec.get("clips", []):
            f = WALKS / walk_id / "clips" / f"{c['n']}.txt"
            if f.exists() and f.read_text().strip():
                snippets.append(notify.snippet(f.read_text()))
        quiz_info = None
        slug = rec.get("podcast_slug")
        if slug and load_quiz(slug):
            nq = next_question(slug)
            title = slug
            try:
                title = json.loads((EPISODES / slug / "ingest.json").read_text())["meta"]["title"]
            except (OSError, ValueError, KeyError):
                pass
            quiz_info = {"title": title[:60], "ready": not nq.get("done"), "done": bool(nq.get("done")),
                         "total": nq.get("session_total"), "max": nq.get("session_max")}
        text = notify.walk_text(rec, snippets, [m for m in after["earned"] if m["id"] not in had],
                                (after["next"] or [None])[0], quiz_info, walk_lookups(rec, walk_id))
        ok, detail = notify.send_telegram(text)
        print(f"{datetime.now():%H:%M:%S} notify walk {walk_id}: {'sent' if ok else 'NOT sent (' + detail + ')'}", flush=True)
        if ok:
            walks.mark_notified(WALKS, walk_id, datetime.now(timezone.utc).isoformat())
        return ok


def next_question(slug, restart=False):
    """The next unanswered question with an explicit instruction for the agent. The server keeps
    the cursor, so the model does not have to track question numbers or invent how to ask."""
    qz = load_quiz(slug)
    if not qz:
        return {"error": "no quiz for this episode"}
    sp = session_path(slug)
    if restart and sp.exists():
        # keep the previous attempt (a retake for a demo must not destroy a real result); the archive folder is not
        # read by the medals, so only the new attempt counts from here
        arch = SESSIONS / "archive"
        arch.mkdir(parents=True, exist_ok=True)
        sp.rename(arch / f"{sp.stem}-{datetime.now():%H%M%S}.json")
    sess = json.loads(sp.read_text()) if sp.exists() else {"slug": slug, "answers": {}}
    qs = qz["questions"]
    for n, q in enumerate(qs, 1):
        if str(n) in sess["answers"]:
            continue
        base = {"n": n, "total": len(qs), "kind": q["kind"], "question": q["question"]}
        if q["kind"] == "mc":
            return {**base, "choices": q["choices"],
                    "action": ("Call the clarify tool now, with this question and exactly these choices in this order, "
                               "so the user sees buttons. Do not write the question or the choices in your own reply. "
                               f"When they tap one, run: leashctl answer {slug} {n} <the choice they tapped>")}
        return {**base, "action": ("Send this question as a normal message, with no buttons, and wait for their answer "
                                   f"(typed or a voice note). Then run: leashctl answer {slug} {n} <their words>")}
    total = sum(a["score"] for a in sess["answers"].values())
    mx = sum(a["max"] for a in sess["answers"].values())
    if sess.get("summary_sent"):
        return {"done": True, "session_total": total, "session_max": mx,
                "action": "The quiz is finished and the Mac already sent the total. Do not write about the score. "
                          "Only if they ask, the total is " + f"{total} out of {mx}."}
    return {"done": True, "session_total": total, "session_max": mx,
            "action": f"The quiz is finished. Tell them the total ({total} out of {mx}) and one sentence on what they remembered best."}


def answer_question(slug, n, text):
    qz = load_quiz(slug)
    if not qz or not 1 <= n <= len(qz["questions"]):
        return {"error": "unknown episode or question number"}
    q = qz["questions"][n - 1]
    if q["kind"] == "mc":
        idx = pick_choice(q["choices"], text)
        if idx is None:
            return {"error": "could not tell which choice that is; ask for A, B, C or D"}
        ok = idx == q["answer_index"]
        res = {"kind": "mc", "score": 1 if ok else 0, "max": 1,
               "feedback": "Correct." if ok else f"Not quite. The answer was: {q['choices'][q['answer_index']]}.",
               "reference": q["reference_answer"]}
    else:
        g = quiz.grade_open(q, text)
        res = {"kind": "field_link", "score": g["score"], "max": 2, "feedback": g["feedback"], "reference": q["reference_answer"]}
    SESSIONS.mkdir(parents=True, exist_ok=True)
    sp = session_path(slug)
    sess = json.loads(sp.read_text()) if sp.exists() else {"slug": slug, "answers": {}}
    sess["answers"][str(n)] = {"score": res["score"], "max": res["max"]}
    sp.write_text(json.dumps(sess, indent=2))
    res["session_total"] = sum(a["score"] for a in sess["answers"].values())
    res["session_max"] = sum(a["max"] for a in sess["answers"].values())
    res["answered"] = len(sess["answers"])
    finished = res["answered"] >= len(qz["questions"])
    sent, detail = notify.send_telegram(notify.quiz_text(n, len(qz["questions"]), res["feedback"], finished,
                                                        res["session_total"], res["session_max"]))
    print(f"{datetime.now():%H:%M:%S} grade message for {slug} q{n}: {'sent' if sent else 'NOT sent (' + detail + ')'}", flush=True)
    res["delivered"] = bool(sent)
    if sent:
        if finished:
            sess["summary_sent"] = True
            sp.write_text(json.dumps(sess, indent=2))
        res.pop("feedback", None)       # nothing left for the model to rephrase or contradict
        res.pop("reference", None)
        res["action"] = (f"The result was already sent to the user by the Mac. Do not write anything about it: no praise, "
                         f"no comment. Run: leashctl next {slug}")
    else:
        res["say"] = res["feedback"]
        res["action"] = (f"Send the user exactly this text and nothing that contradicts it: \"{res['say']}\" "
                         f"Then run: leashctl next {slug}")
    return res


class Handler(BaseHTTPRequestHandler):
    server_version = "leash/0.1"

    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, obj, ctype="application/json"):
        print(f"{datetime.now():%H:%M:%S} {self.command} {self.path.split('?')[0]} -> {code}", flush=True)
        body = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(body)

    def _auth(self):
        tok = os.environ.get("LEASH_UPLOAD_TOKEN", "")
        got = self.headers.get("Authorization", "")
        return bool(tok) and hmac.compare_digest(got, f"Bearer {tok}")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True})
        path = self.path.split("?")[0]
        if path == "/app":
            self.send_response(301); self.send_header("Location", "/app/"); self.send_header("Content-Length", "0"); self.end_headers()
            return
        if path.startswith("/app/"):
            rel = path[len("/app"):].lstrip("/") or "index.html"
            f = (APP / rel).resolve()
            if APP.resolve() not in f.parents or not f.is_file():
                return self._send(404, {"error": "not found"})
            return self._send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))
        if not self._auth():
            return self._send(401, {"error": "unauthorized"})
        if path in ("/walks", "/medals"):
            return self._send(200, walks_summary())
        if path == "/stats":
            ws = walks.list_walks(WALKS)
            keep = ("id", "kind", "started_at", "duration_s", "distance_m", "tracked_s", "untracked_s", "podcast_slug", "notified_at")
            return self._send(200, {**walks.stats(ws, load_sessions()),
                                    "recent": [{k: w.get(k) for k in keep} | {"clips": len(w.get("clips", []))} for w in ws[:20]]})
        if path.startswith("/jobs/"):
            j = JOBS.get(path.split("/")[2])
            return self._send(200 if j else 404, {**(j or {"error": "unknown job"}), "log": (j or {}).get("log", [])[-6:]})
        if path == "/episodes":
            rows = []
            for p in episode_dirs()[:20]:
                d = json.loads(p.read_text())
                rows.append({"slug": p.parent.name, "title": d["meta"]["title"], "channel": d["meta"].get("channel"),
                             "minutes": d["meta"].get("duration_min"), "quiz_ready": quiz_status(p.parent.name) in ("ok", "partial"),
                             "quiz_status": quiz_status(p.parent.name)})
            return self._send(200, {"episodes": rows})
        m = re.fullmatch(r"/episodes/([\w-]+)/quiz", path)
        if m:
            qz = load_quiz(m.group(1))
            if not qz:
                return self._send(404, {"error": "no quiz for this episode"})
            qs = [{"n": i, "kind": q["kind"], "question": q["question"],
                   **({"choices": dict(zip(LETTERS, q["choices"]))} if q["kind"] == "mc" else {})} for i, q in enumerate(qz["questions"], 1)]
            return self._send(200, {"slug": m.group(1), "questions": qs, "note": "Answers are graded by POST /answer; they are not included here."})
        m = re.fullmatch(r"/episodes/([\w-]+)/next", path)
        if m:
            return self._send(200, next_question(m.group(1), restart="restart=1" in self.path))
        m = re.fullmatch(r"/episodes/([\w-]+)/audio/(\d)", path)
        if m:
            f = EPISODES / m.group(1) / "quiz-audio" / f"q{m.group(2)}.ogg"
            return self._send(200, f.read_bytes(), "audio/ogg") if f.exists() else self._send(404, {"error": "no audio"})
        if path == "/resurface":
            return self._send(200, ideas.resurface(VAULT))
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return self._send(401, {"error": "unauthorized"})
        try:
            if self.path.split("?")[0] == "/clips":   # a voice note from a walk that was too short to save
                n = int(self.headers.get("Content-Length") or 0)
                if n <= 0 or n > stt.MAX_BYTES:
                    return self._send(400, {"error": "send the clip as the request body (up to 25 MB)"})
                text = stt.transcribe_bytes(self.rfile.read(n))
                page = ideas.add_note(VAULT, text, source="voice-app").get("page") if len(text.strip()) >= 3 else None
                self._send(200, {"chars": len(text), "page": page, "text": text})
                q = lookups.extract_query(text)
                if q:   # a stand-alone note that asks for a search gets its answer as one short message
                    lk = run_lookup(q)
                    ok, detail = notify.send_telegram("\n".join(notify.lookup_lines(lk)))
                    print(f"{datetime.now():%H:%M:%S} lookup for stand-alone note: {'sent' if ok else 'NOT sent (' + detail + ')'}", flush=True)
                return
            m = re.fullmatch(r"/walks/([\w-]+)/clips", self.path.split("?")[0])
            if m:
                q = dict(x.split("=", 1) for x in (self.path.split("?", 1) + [""])[1].split("&") if "=" in x)
                n = int(self.headers.get("Content-Length") or 0)
                if n <= 0 or n > stt.MAX_BYTES:
                    return self._send(400, {"error": "send the clip as the request body (up to 25 MB)"})
                data = self.rfile.read(n)
                if not (WALKS / m.group(1) / "walk.json").exists():
                    return self._send(400, {"error": "unknown walk; send the walk first"})
                text = stt.transcribe_bytes(data)
                clip_n = int(q.get("n", "1"))
                page = None
                if len(text.strip()) >= 3:
                    page = ideas.add_note(VAULT, text, source=f"voice-walk:{m.group(1)}").get("page")
                ext = "mp4" if "mp4" in (self.headers.get("Content-Type") or "") else "webm"
                walks.add_clip(WALKS, m.group(1), clip_n, data, ext, text, page)
                self._send(200, {"n": clip_n, "chars": len(text), "page": page, "text": text})
                threading.Thread(target=notify_walk, args=(m.group(1),), daemon=True).start()
                return
            if self.path == "/walks":
                n = int(self.headers.get("Content-Length") or 0)
                if n <= 0 or n > 8_000_000:
                    return self._send(400, {"error": "walk too large"})
                body = json.loads(self.rfile.read(n))
                if walks.duration_of(body) < walks.MIN_WALK_S:   # acknowledge so the phone drops it; store nothing
                    return self._send(200, {"saved": False, "reason": "too_short", "min_s": walks.MIN_WALK_S})
                rec = walks.save_walk(WALKS, body)
                self._send(200, {"saved": rec["id"], **{k: rec[k] for k in ("distance_m", "tracked_s", "duration_s", "untracked_s")},
                                 **walks.medals(walks.list_walks(WALKS), load_sessions())})
                if not rec.get("notified_at"):
                    if rec["clip_count"] == 0:
                        threading.Thread(target=notify_walk, args=(rec["id"],), daemon=True).start()
                    else:  # wait for the voice notes, but never longer than 3 minutes
                        t = threading.Timer(180, notify_walk, args=(rec["id"], True)); t.daemon = True; t.start()
                return
            if self.path == "/transcribe":
                n = int(self.headers.get("Content-Length") or 0)
                if n <= 0 or n > stt.MAX_BYTES:
                    return self._send(400, {"error": "send the audio file as the request body (up to 25 MB)"})
                text = stt.transcribe_bytes(self.rfile.read(n))
                return self._send(200, {"text": text, "chars": len(text)})
            b = self._body()
            if self.path == "/ingest":
                src = (b.get("source") or "").strip()
                if not src.startswith(("http://", "https://")):
                    return self._send(400, {"error": "source must be an http(s) link"})
                jid = uuid.uuid4().hex[:8]
                JOBS[jid] = {"status": "running", "started": time.time(), "source": src, "log": []}
                threading.Thread(target=run_job, args=(jid, src, b.get("title")), daemon=True).start()
                return self._send(202, {"job_id": jid, "hint": "poll GET /jobs/<id>; it takes about a third of the episode length (30 min: 8 min, 57 min: 18 min, measured)"})
            if self.path == "/answer":
                return self._send(200, answer_question(str(b.get("slug", "")), int(b.get("n", 0)), str(b.get("answer", ""))))
            if self.path == "/ideas":
                text = str(b.get("text", "")).strip()
                if len(text) < 3:
                    return self._send(400, {"error": "empty idea"})
                return self._send(200, ideas.add_note(VAULT, text, source=str(b.get("source", "voice"))))
            if self.path == "/search":
                return self._send(200, search.search(str(b.get("query", "")).strip()))
        except Exception as e:  # noqa: BLE001
            return self._send(400 if isinstance(e, (ValueError, KeyError)) else 500, {"error": str(e)[:300]})
        self._send(404, {"error": "not found"})


def main():
    load_env()
    if not os.environ.get("LEASH_UPLOAD_TOKEN"):
        raise SystemExit("LEASH_UPLOAD_TOKEN is not set in .env; refusing to start an unauthenticated server")
    port = int(os.environ.get("LEASH_PORT", "8787"))
    print(f"leash server on 127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
