"""Direct messages through Hermes (`hermes send`), so the bot's own WhatsApp session delivers them."""

from __future__ import annotations

import shlex
import subprocess


def whatsapp_target(phone: str) -> str:
    # A full JID is a native target for `hermes send`; a bare number may not resolve.
    return f"whatsapp:{phone}@s.whatsapp.net"


def send_dm(send_cmd: str, phone: str, text: str, timeout_s: float = 60) -> tuple[bool, str | None]:
    """Returns (sent, error). Never raises: a failed DM must not lose the listing or the quote."""
    if not phone:
        return False, "no phone number"
    # The message goes through stdin so text starting with '-' is never read as a flag.
    cmd = [*shlex.split(send_cmd), "--to", whatsapp_target(phone), "--quiet"]
    try:
        proc = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=timeout_s)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"{type(exc).__name__}: {exc}"
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        return False, f"exit {proc.returncode}: {err[-1] if err else 'no output'}"
    return True, None
