"""Messages the Mac sends on its own (the first piece of the ambient agent).

The text is built from facts by plain code: no language model is involved, so a message can never
claim something that did not happen. Sending uses the Telegram Bot API directly; the bot token and the
user id come from .env and never leave the Mac except in the request to Telegram.
"""
import json
import os
import urllib.error
import urllib.request


def _km(m):
    return f"{m / 1000:.2f} km" if m >= 1000 else f"{int(m)} m"


def _mins(s):
    m = round(s / 60)
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


def lookup_lines(lk):
    """lk: {"query", "results": [{"title","link"}], "error"}. Plain facts, no model-written summary."""
    q = lk["query"]
    if lk.get("error"):
        return [f"Could not search for \"{q}\": {lk['error']}."]
    rows = lk.get("results") or []
    if not rows:
        return [f"Searched \"{q}\": no results."]
    out = [f"Searched \"{q}\":"]
    for i, r in enumerate(rows[:3], 1):
        title = " ".join((r.get("title") or r.get("link") or "").split())[:80]
        out += [f"  {i}. {title}", f"     {r.get('link', '')}"]
    return out


def walk_text(walk, snippets, new_medals, next_medal, quiz, lookups=None):
    """walk: the stored walk record; snippets: first words of each voice idea;
    new_medals / next_medal: dicts with `label` (and `how`); quiz: None or {"title", "ready", "done", "total", "max"}."""
    kind = {"podcast": "Podcast walk", "dog": "Dog walk"}.get(walk["kind"], "Walk")
    lines = [f"{kind} saved: {_km(walk['distance_m'])} in {_mins(walk['duration_s'])}."]
    if walk.get("untracked_s", 0) > 60:
        lines.append(f"The phone could not track {_mins(walk['untracked_s'])} of it (screen off or another app in front).")
    n = len(snippets)
    if n:
        lines.append(f"{n} voice idea{'s' if n != 1 else ''} saved:")
        lines += [f"  - {s}" for s in snippets[:3]]
        if n > 3:
            lines.append(f"  - and {n - 3} more")
    for lk in lookups or []:
        lines += lookup_lines(lk)
    if new_medals:
        lines.append("New medal: " + ", ".join(m["label"] for m in new_medals) + ".")
    if quiz and quiz.get("done"):
        lines.append(f"Quiz finished: {quiz['total']} out of {quiz['max']}.")
    elif quiz and quiz.get("ready"):
        lines.append(f"The quiz on \"{quiz['title']}\" is ready. When you have stopped and have a minute, say \"quiz me\".")
    if next_medal:
        lines.append(f"Next medal: {next_medal['label']} ({next_medal['how'].lower()}).")
    return "\n".join(lines)


def snippet(text, width=70):
    t = " ".join(text.split())
    return t if len(t) <= width else t[: width - 1].rstrip() + "…"


def send_telegram(text, token=None, chat_id=None, timeout=15):
    """Returns (ok, detail). detail never contains the token."""
    if os.environ.get("LEASH_NOTIFY_DRY_RUN"):  # tests: show the text instead of sending it
        print("[dry-run telegram message]\n" + text, flush=True)
        return True, "dry-run"
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("TELEGRAM_ALLOWED_USERS", "").split(",")[0].strip()
    if not token or not chat_id:
        return False, "TELEGRAM_BOT_TOKEN or TELEGRAM_ALLOWED_USERS is not set"
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "idea-leash/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ok = json.load(r).get("ok", False)
            return ok, "sent" if ok else "telegram said not ok"
    except urllib.error.HTTPError as e:
        return False, f"telegram HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__


def quiz_text(n, total, feedback, finished=False, score=None, maximum=None):
    """The grade for one answer, sent by the Mac itself. `feedback` comes from code (multiple choice) or the
    grading model (open question); the numbers always come from code."""
    t = f"Question {n} of {total}: {feedback}"
    if finished and score is not None:
        t += f"\nQuiz finished: {score} out of {maximum}."
    return t


def podcast_text(meta, timings, quiz_status, notes_stats=None):
    """Sent when a podcast has been prepared."""
    mins = meta.get("duration_min")
    head = f"Podcast ready: \"{meta.get('title', 'episode')[:90]}\""
    bits = [b for b in (meta.get("channel"), f"{round(mins)} min" if mins else None) if b]
    if bits:
        head += f" ({', '.join(bits)})"
    took = timings.get("total_s")
    lines = [head + (f", prepared in {max(1, round(took / 60))} min." if took else ".")]
    if notes_stats and notes_stats.get("kept"):
        kept = sum(notes_stats["kept"].values())
        dropped = notes_stats.get("dropped_unsupported", 0)
        lines.append(f"Notes: {kept} ideas, facts and definitions saved to your second brain"
                     + (f" ({dropped} dropped for lack of a supporting quote)." if dropped else "."))
    lines.append({
        "ok": "Quiz: ready. Every question is backed by a quote from the episode.",
        "partial": "Quiz: ready. Every question is backed by a quote from the episode, but some format checks were not met "
                   "(some answers may be easier to guess).",
    }.get(quiz_status, "Quiz: could not be made for this episode."))
    if quiz_status in ("ok", "partial"):
        lines.append("Pick it in the app's Podcast walk list, and say \"quiz me\" after your walk.")
    return "\n".join(lines)


def failure_text(source, error):
    return f"Could not prepare the podcast ({source[:80]}): {str(error)[:140]}"
