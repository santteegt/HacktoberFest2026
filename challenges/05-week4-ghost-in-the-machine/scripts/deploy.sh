#!/usr/bin/env bash
# Rebuild the gallery index and deploy web/ to Vercel production.
# Uses the CLI's existing login; passes --token only when VERCEL_TOKEN is set (cron).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
uv run ghosts gallery build || uv run python -m ghosts.gallery build  # fallback until the CLI wiring exists
cd "$ROOT/web"
args=(deploy --prod --yes)
if [ -n "${VERCEL_TOKEN:-}" ]; then
  args+=(--token "$VERCEL_TOKEN")
fi
# Vercel CLI 62 prints JSON on stdout when not attached to a terminal and plain URLs on older versions.
out="$(vercel "${args[@]}")"
url="$(printf '%s' "$out" | python3 -c '
import json, sys
raw = sys.stdin.read().strip()
try:
    d = json.loads(raw)
    print((d.get("deployment") or {}).get("url") or d.get("url") or "")
except ValueError:
    print(raw.splitlines()[-1] if raw else "")
')"
if [ -z "$url" ]; then
  echo "deploy failed: no deployment URL returned" >&2
  exit 1
fi
echo "deployed: $url"
echo "site:     https://eth-ghosts.decentraminds.tech"
