"""`sloth` command. Lanes add their sub-apps in sloth/cli/<lane>.py (coordinator wires them here)."""

from __future__ import annotations

import importlib

import typer

app = typer.Typer(no_args_is_help=True, help="Skunkworks Sloth: reading list in, prototypes out.")


@app.callback()
def main() -> None:
    """Keep `sloth` a command group even while only `doctor` exists."""

# Each lane module exposes `register(app)`; missing modules are skipped so lanes can land independently.
for _lane in ("curator", "board", "builder"):
    try:
        importlib.import_module(f"sloth.cli.{_lane}").register(app)
    except ModuleNotFoundError as e:
        if e.name != f"sloth.cli.{_lane}":
            raise


@app.command()
def doctor() -> None:
    """Check config, database, Ollama and Discord wiring (no messages sent)."""
    from .._doctor import run
    run()


@app.command("apply-schema")
def apply_schema_cmd() -> None:
    """Create or update the tables (coordinator only)."""
    from ..core.db import apply_schema
    apply_schema()
    print("schema applied")
