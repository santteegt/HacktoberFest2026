"""Tiny .env loader (no dependency). Never prints values."""
import os
from pathlib import Path


def load_env(path: Path | None = None) -> None:
    path = path or Path(__file__).resolve().parents[2] / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
