"""Speak the quiz with Piper (open voice), so it can be heard with no screen."""
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
VOICE = PROJECT / "models" / "piper" / "en_US-lessac-medium.onnx"
LETTERS = "ABCD"


def speak(text: str, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = out.with_suffix(".wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", str(VOICE), "-f", str(wav)], input=text.encode(), check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-c:a", "libopus", "-b:a", "32k", str(out)], check=True)
    wav.unlink(missing_ok=True)
    return out


def render_quiz(quiz: dict, out_dir: Path):
    """One Opus file per question: the question, then the choices read as A to D."""
    files = []
    for i, q in enumerate(quiz["questions"], 1):
        if q["kind"] == "mc":
            text = f"Question {i}. {q['question']} " + " ".join(f"{LETTERS[j]}. {c}." for j, c in enumerate(q["choices"]))
        else:
            text = f"Last question. {q['question']}"
        files.append(str(speak(text, out_dir / f"q{i}.ogg")))
    return files
