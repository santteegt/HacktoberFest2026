"""All Discord output goes through here (lanes never call Discord directly).

post() sends as the bot that owns the channel; log() writes one line to #sk-logs as the
acting agent and to the events table. With SLOTH_DRY_RUN=1 (the default in lanes) it
prints instead of sending.
"""

from __future__ import annotations

import json
import subprocess
from typing import Literal

from .config import CHANNEL_PROFILE, dry_run, settings

Channel = Literal["curator", "valhalla", "coordinator", "worker", "log"]
Agent = Literal["curator", "coordinator", "worker"]


def _send(profile: str, channel_id: str, text: str) -> None:
    subprocess.run(
        ["hermes", "-p", profile, "send", "--quiet", "--to", f"discord:{channel_id}", text],
        check=True, capture_output=True, text=True, timeout=30,
    )


def post(channel: Channel, text: str, *, as_agent: Agent | None = None) -> None:
    profile = f"sloth-{as_agent}" if as_agent else CHANNEL_PROFILE[channel]
    channel_id = settings().channels[channel]
    if dry_run() or not channel_id:
        print(f"[dry-run #{channel} as {profile}] {text}")
        return
    _send(profile, channel_id, text)


def log(agent: Agent, kind: str, text: str, data: dict | None = None, *, record: bool = True) -> None:
    """One timeline line: `[agent] text`. Also stored in the events table unless record=False."""
    post("log", f"[{agent}] {text}", as_agent=agent)
    if record and not dry_run():
        from .db import connect
        with connect() as conn:
            conn.execute(
                "INSERT INTO events (agent, kind, text, data) VALUES (%s, %s, %s, %s)",
                (agent, kind, text, json.dumps(data) if data else None),
            )
