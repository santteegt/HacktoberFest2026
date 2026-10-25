"""Settings from .sloth/config.toml (gitignored); config.example.toml shows every key."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(os.environ.get("SLOTH_CONFIG", ROOT / ".sloth" / "config.toml"))
CHANNELS = ("curator", "valhalla", "coordinator", "worker", "log", "daily_reading")
# Which bot speaks in which channel (#sk-logs is shared: each agent posts as itself).
CHANNEL_PROFILE = {
    "curator": "sloth-curator",
    "valhalla": "sloth-curator",
    "coordinator": "sloth-coordinator",
    "worker": "sloth-worker",
    "daily_reading": "sloth-coordinator",
}


@dataclass(frozen=True)
class Settings:
    bookmarks_path: Path
    bookmarks_folder: str
    tiger_service_id: str
    db_url_env: str
    channels: dict[str, str]
    ollama_url: str
    ollama_model: str
    ollama_num_ctx: int
    openrouter_model: str
    worker_provider: str          # default Worker provider: "openrouter" (open weights)
    worker_model: str             # model id for worker_provider; empty = openrouter_model
    complex_provider: str         # provider for cards the author sends with `go deep`: "anthropic" (closed)
    complex_model: str            # model id for complex_provider
    box_minutes: int
    prototypes_dir: Path
    github_owner: str
    github_project_number: int | None
    extra: dict = field(default_factory=dict)


@cache
def settings() -> Settings:
    raw = tomllib.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    src = raw.get("sources", {})
    llm = raw.get("llm", {})
    gh = raw.get("github", {})
    disc = raw.get("discord", {})
    return Settings(
        bookmarks_path=Path(os.path.expanduser(src.get(
            "bookmarks_path", "~/Library/Application Support/Google/Chrome/Default/Bookmarks"))),
        bookmarks_folder=src.get("bookmarks_folder", "Reading List"),
        tiger_service_id=raw.get("db", {}).get("tiger_service_id", ""),
        db_url_env=raw.get("db", {}).get("url_env", "SLOTH_DATABASE_URL"),
        channels={k: str(disc.get(k, "")) for k in CHANNELS},
        ollama_url=llm.get("ollama_url", "http://localhost:11434"),
        ollama_model=llm.get("ollama_model", "sloth-gemma4-12b"),
        ollama_num_ctx=int(llm.get("ollama_num_ctx", 65536)),
        openrouter_model=llm.get("openrouter_model", ""),
        worker_provider=llm.get("worker_provider", "openrouter"),
        worker_model=llm.get("worker_model", "") or llm.get("openrouter_model", ""),
        complex_provider=llm.get("complex_provider", "anthropic"),
        complex_model=llm.get("complex_model", "claude-sonnet-5-5"),
        box_minutes=int(raw.get("worker", {}).get("box_minutes", 120)),
        prototypes_dir=Path(os.path.expanduser(raw.get("worker", {}).get(
            "prototypes_dir", "~/GitRepositories/skunkworks-prototypes"))),
        github_owner=gh.get("owner", "@me"),
        github_project_number=gh.get("project_number"),
        extra=raw,
    )


def dry_run() -> bool:
    """Lanes default to dry-run: Discord posts print to stdout instead of sending."""
    return os.environ.get("SLOTH_DRY_RUN", "1") != "0"
