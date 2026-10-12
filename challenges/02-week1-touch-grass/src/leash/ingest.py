"""Podcast link (or file) in; transcript, verified notes, second-brain pages, quiz and spoken quiz out."""
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from . import notes as notes_mod
from . import ollama as ollama_mod
from . import quiz as quiz_mod
from . import tts as tts_mod
from . import wiki as wiki_mod
from .envfile import load_env

PROJECT = Path(__file__).resolve().parents[2]
DATA = PROJECT / "data"
TEXT_EXT = {".txt", ".srt", ".vtt", ".md"}
WHISPER_CPP = PROJECT / "vendor" / "whisper.cpp" / "build" / "bin" / "whisper-cli"
WHISPER_MODEL = PROJECT / "models" / "whisper" / "ggml-large-v3-turbo-q5_0.bin"


def is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))


def fetch_metadata(url: str) -> dict:
    """Title, channel and length from the page, without downloading anything."""
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True, "skip_download": True}) as y:
            info = y.extract_info(url, download=False)
        return {"title": info.get("title"), "channel": info.get("uploader") or info.get("channel"),
                "duration_min": round((info.get("duration") or 0) / 60, 1), "upload_date": info.get("upload_date"),
                "url": info.get("webpage_url") or url}
    except Exception as e:  # noqa: BLE001
        return {"title": None, "channel": None, "duration_min": None, "url": url, "metadata_error": str(e)[:200]}


def transcribe_audio(audio: Path, ep_dir: Path, engine: str, whisper: str, prompt: str, max_minutes, log) -> str:
    src = audio
    if max_minutes:
        cut = ep_dir / "audio" / f"first-{max_minutes}min.m4a"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(audio), "-t", str(int(max_minutes) * 60), "-c:a", "aac", str(cut)], check=True)
        src = cut
    if engine == "whispercpp":
        wav = ep_dir / "audio" / "16k.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)], check=True)
        out = ep_dir / "whispercpp"
        subprocess.run([str(WHISPER_CPP), "-m", str(WHISPER_MODEL), "-f", str(wav), "-l", "en", "-otxt", "-of", str(out)],
                       check=True, capture_output=True)  # timestamps stay on: -nt drops most of the text
        wav.unlink(missing_ok=True)
        return Path(str(out) + ".txt").read_text()
    os.environ["GRAPHIFY_WHISPER_MODEL"] = whisper
    os.environ.setdefault("GRAPHIFY_NO_AUTO_REFRESH", "1")
    from graphify import transcribe as gt
    path = gt.transcribe(src, output_dir=ep_dir / "graphify", initial_prompt=prompt, force=True)
    return Path(path).read_text()


def run(source: str, *, vault: Path | None = None, model: str = ollama_mod.DEFAULT_MODEL, engine: str = "graphify",
        whisper: str = "small", title: str | None = None, with_quiz: bool = True, with_audio: bool = True,
        max_minutes: int | None = None, log=print) -> dict:
    load_env()
    vault = vault or PROJECT / "second-brain"
    t_all = time.time(); timings = {}
    meta = {"source": source}
    ep_seed = hashlib.sha1(source.encode()).hexdigest()[:6]

    if is_url(source):
        meta.update(fetch_metadata(source))
    else:
        meta.update({"title": None, "channel": None, "url": None})
    meta["title"] = title or meta.get("title") or Path(source).stem.replace("-", " ").replace("_", " ")
    meta["slug"] = f"{wiki_mod.slugify(meta['title'], 48)}-{ep_seed}"
    ep_dir = DATA / "episodes" / meta["slug"]
    (ep_dir / "audio").mkdir(parents=True, exist_ok=True)
    log(f"episode: {meta['title']} ({meta.get('channel')}, {meta.get('duration_min')} min) -> {ep_dir}")

    # 1. transcript
    t = time.time()
    tpath = ep_dir / "transcript.txt"
    if tpath.exists():
        transcript = tpath.read_text(); log("  transcript: cached")
    else:
        if is_url(source) or Path(source).suffix.lower() not in TEXT_EXT:
            if is_url(source):
                from graphify import transcribe as gt
                log("  downloading audio ...")
                audio = gt.download_audio(source, ep_dir / "audio")
            else:
                audio = Path(source).expanduser()
            log(f"  transcribing with {engine}" + (f" ({whisper})" if engine == "graphify" else "") + " ...")
            prompt = f"{meta['title']}. {meta.get('channel') or ''}. Use proper punctuation and paragraph breaks."
            raw = transcribe_audio(audio, ep_dir, engine, whisper, prompt, max_minutes, log)
        else:
            raw = Path(source).expanduser().read_text()
        transcript = quiz_mod.clean_transcript(raw)
        tpath.write_text(transcript)
    words = len(transcript.split())
    timings["transcript_s"] = round(time.time() - t, 1)
    log(f"  transcript: {words} words in {timings['transcript_s']} s")

    # 2. notes
    t = time.time()
    npath = ep_dir / "notes.json"
    if npath.exists():
        notes = json.loads(npath.read_text()); log("  notes: cached")
    else:
        notes = notes_mod.build_notes(transcript, meta, model, log=log)
        npath.write_text(json.dumps(notes, indent=2, ensure_ascii=False))
    timings["notes_s"] = round(time.time() - t, 1)
    log(f"  notes: {notes['stats']['kept']} kept, {notes['stats']['dropped_unsupported']} dropped as unsupported, {timings['notes_s']} s")

    # 3. quiz (+ spoken)
    quiz_info = None
    if with_quiz:
        t = time.time()
        cands = quiz_mod.select_candidates(notes) if words > 2500 and len(notes.get("main_ideas", [])) >= 3 else None
        ctx = 16384 if cands else min(65536, max(16384, int(words * 1.6) + 5000))
        res = quiz_mod.generate(transcript, model, num_ctx=ctx, candidates=cands, title=meta["title"])
        last = res["attempts"][-1] if res["attempts"] else {}
        status = res.get("status", "failed")
        quiz_info = {"ok": status == "ok", "status": status, "attempts": len(res["attempts"]),
                     "errors": last.get("errors"), "warnings": last.get("warnings")}
        if res["quiz"]:
            (ep_dir / "quiz.json").write_text(json.dumps(res["quiz"], indent=2, ensure_ascii=False))
            if with_audio and quiz_info["status"] in ("ok", "partial"):
                tts_mod.render_quiz(res["quiz"], ep_dir / "quiz-audio")
        timings["quiz_s"] = round(time.time() - t, 1)
        log(f"  quiz: ok={quiz_info['ok']} attempts={quiz_info['attempts']} {timings['quiz_s']} s")

    # 4. second brain
    pages = wiki_mod.add_episode(vault, meta, transcript, notes, quiz_questions=5 if quiz_info and quiz_info["status"] in ("ok", "partial") else 0)
    log(f"  wiki: {pages['source_page']} (+{len(pages['created'])} new concept pages, {len(pages['updated'])} updated)")

    timings["total_s"] = round(time.time() - t_all, 1)
    result = {"meta": meta, "words": words, "timings": timings, "notes_stats": notes["stats"], "quiz": quiz_info,
              "pages": pages, "episode_dir": str(ep_dir)}
    (ep_dir / "ingest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result
