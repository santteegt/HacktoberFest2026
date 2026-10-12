"""Speech to text for short voice notes (Telegram voice messages sent through Hermes).

Uses whisper.cpp with the same model as podcast ingest, on the Mac's GPU. English only.
Never use -nt (no timestamps): it silently drops most of the text (see docs/CHALLENGE-MEMORY.md).
"""
import subprocess
import tempfile
from pathlib import Path

from .ingest import WHISPER_CPP, WHISPER_MODEL

MAX_BYTES = 25 * 1024 * 1024
# A short vocabulary hint: whisper spells names from it ("Lume", "OpenClaw") instead of guessing.
# Tested 2026-10-09 on four synthetic clips: fixes two proper nouns, no regression, same output on silence.
PROMPT = ("Voice message to Leash, a walking companion. Words that may appear: quiz me, second brain, podcast, "
          "Bankless, The DeFi Report, TDR, In The Loop, OpenClaw, Hermes, Gemma, Ollama, Lume, Tailscale, SerpApi, "
          "Raid Guild, Telegram, dog walk.")


def transcribe_bytes(data: bytes, timeout: int = 120) -> str:
    if not data:
        raise ValueError("empty audio")
    if len(data) > MAX_BYTES:
        raise ValueError("audio larger than 25 MB")
    if not WHISPER_CPP.exists() or not WHISPER_MODEL.exists():
        raise RuntimeError("whisper.cpp or its model is missing; see README setup")
    with tempfile.TemporaryDirectory(prefix="leash-stt-") as d:
        src, wav, out = Path(d, "in.audio"), Path(d, "in.wav"), Path(d, "out")
        src.write_bytes(data)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)],
                       check=True, timeout=timeout)
        subprocess.run([str(WHISPER_CPP), "-m", str(WHISPER_MODEL), "-f", str(wav), "-l", "en", "--prompt", PROMPT, "-otxt", "-of", str(out)],
                       check=True, timeout=timeout, capture_output=True)
        txt = Path(str(out) + ".txt")
        return " ".join(txt.read_text(encoding="utf-8", errors="replace").split()) if txt.exists() else ""
