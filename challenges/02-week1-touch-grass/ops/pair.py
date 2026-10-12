#!/usr/bin/env python3
"""Show a QR code that opens the Idea Leash app on the phone and hands it the token.

The token is in the URL *fragment* (#token=...), which browsers never send to a server; the app stores it
and removes it from the address bar. The token is never printed as text.
Usage: .venv/bin/python ops/pair.py [https://host.tailnet.ts.net]
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import segno

ROOT = Path(__file__).resolve().parents[1]


def env_value(key):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def tailnet_host():
    try:
        out = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=10).stdout
        name = json.loads(out)["Self"]["DNSName"].rstrip(".")
        if name:
            return name
    except Exception:  # noqa: BLE001
        pass
    return os.environ.get("LEASH_TAILNET_HOST", "")


def main():
    token = env_value("LEASH_UPLOAD_TOKEN")
    if not token:
        sys.exit("LEASH_UPLOAD_TOKEN is not set in .env")
    base = sys.argv[1] if len(sys.argv) > 1 else ("https://" + tailnet_host() if tailnet_host() else "")
    if not base:
        sys.exit("Tailscale is not running and LEASH_TAILNET_HOST is not set; pass the https://host.ts.net URL as an argument")
    url = f"{base.rstrip('/')}/app/#token={token}"
    print(f"\nScan with the phone camera (the phone must have Tailscale on). App address: {base.rstrip('/')}/app/\n")
    segno.make(url, error="m").terminal(compact=True)
    print("\nThe token is inside the code only. Close this terminal tab when done.")


if __name__ == "__main__":
    main()
