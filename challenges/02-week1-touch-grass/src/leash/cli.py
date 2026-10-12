import argparse
import json
import sys
from pathlib import Path

from . import ingest, quiz


def main(argv=None):
    ap = argparse.ArgumentParser(prog="leash")
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quiz", help="make a verified quiz from a transcript file")
    q.add_argument("transcript"); q.add_argument("--model", default="gemma4:12b-it-qat"); q.add_argument("--no-skill", action="store_true"); q.add_argument("-o", "--out")
    i = sub.add_parser("ingest", help="podcast URL, audio/video file or transcript -> notes, wiki pages, quiz")
    i.add_argument("source")
    i.add_argument("--model", default="gemma4:12b-it-qat")
    i.add_argument("--engine", choices=["graphify", "whispercpp"], default="graphify", help="transcription engine")
    i.add_argument("--whisper", default="small", help="graphify/faster-whisper model: tiny, base, small, medium")
    i.add_argument("--title"); i.add_argument("--vault"); i.add_argument("--max-minutes", type=int)
    i.add_argument("--no-quiz", action="store_true"); i.add_argument("--no-audio", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "quiz":
        return quiz.main([a.transcript, "--model", a.model] + (["--no-skill"] if a.no_skill else []) + (["-o", a.out] if a.out else []))
    res = ingest.run(a.source, vault=Path(a.vault) if a.vault else None, model=a.model, engine=a.engine, whisper=a.whisper,
                     title=a.title, with_quiz=not a.no_quiz, with_audio=not a.no_audio, max_minutes=a.max_minutes)
    print(json.dumps({k: res[k] for k in ("words", "timings", "quiz", "pages", "episode_dir")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
