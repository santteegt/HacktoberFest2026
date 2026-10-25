"""Read secrets at runtime from the Hermes profile .env files; never copy them anywhere."""

from __future__ import annotations

import os
import subprocess
from functools import cache
from pathlib import Path

from .config import settings

HERMES_HOME = Path(os.environ.get("HERMES_HOME_ROOT", Path.home() / ".hermes"))


@cache
def profile_env(profile: str) -> dict[str, str]:
    path = HERMES_HOME / "profiles" / profile / ".env"
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip("'\"")
    return out


def get(profile: str, key: str) -> str:
    value = os.environ.get(key) or profile_env(profile).get(key, "")
    if not value or value.startswith("<"):
        raise KeyError(f"{key} is not set for profile {profile}")
    return value


@cache
def database_url() -> str:
    """SLOTH_DATABASE_URL wins (e.g. a local SQLite fallback); else ask the tiger CLI (keyring)."""
    s = settings()
    if url := os.environ.get(s.db_url_env):
        return url
    # Unattended runs (Hermes cron, screen locked) cannot read the keychain behind `tiger`,
    # so the sloth profiles' .env files (owner-only) may carry the URL too.
    for profile in ("sloth-coordinator", "sloth-curator", "sloth-worker"):
        if (url := profile_env(profile).get(s.db_url_env, "")) and not url.startswith("<"):
            return url
    if not s.tiger_service_id:
        raise KeyError("db.tiger_service_id missing in .sloth/config.toml")
    res = subprocess.run(
        ["tiger", "db", "uri", s.tiger_service_id, "--with-password"],
        check=True, capture_output=True, text=True,
    )
    return res.stdout.strip()
