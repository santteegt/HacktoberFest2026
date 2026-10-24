"""`sloth doctor`: wiring checks that never post to Discord."""

from __future__ import annotations

import httpx
from rich import print

from .core import secrets
from .core.config import CONFIG_PATH, settings


def run() -> None:
    s = settings()
    print(f"config: {CONFIG_PATH} {'ok' if CONFIG_PATH.exists() else 'MISSING (copy config.example.toml)'}")
    print(f"bookmarks: {s.bookmarks_path} {'ok' if s.bookmarks_path.exists() else 'MISSING'}")
    try:
        from .core.db import connect
        with connect() as conn:
            n = conn.execute("SELECT count(*) AS n FROM links").fetchone()["n"]
        print(f"database: ok ({n} links)")
    except Exception as e:  # noqa: BLE001 - a doctor reports, it does not crash
        print(f"database: FAIL {type(e).__name__}: {e}")
    try:
        tags = {m["name"] for m in httpx.get(f"{s.ollama_url}/api/tags", timeout=5).json()["models"]}
        ok = s.ollama_model in tags or f"{s.ollama_model}:latest" in tags
        print(f"ollama: {'ok' if ok else 'MODEL MISSING'} ({s.ollama_model})")
    except Exception as e:  # noqa: BLE001
        print(f"ollama: FAIL {e}")
    for ch, cid in s.channels.items():
        print(f"discord #{ch}: {'set' if cid else 'MISSING'}")
    for p in ("sloth-curator", "sloth-coordinator", "sloth-worker"):
        try:
            secrets.get(p, "DISCORD_BOT_TOKEN")
            print(f"{p}: token set")
        except KeyError as e:
            print(f"{p}: {e}")
