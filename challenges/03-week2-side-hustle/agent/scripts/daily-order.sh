#!/usr/bin/env bash
# Daily order batch, run by Hermes cron with --no-agent (no model turn): groups the accepted quotes by
# store, records the order and DMs the summary to MAINTAINER_PHONE through `hermes send`.
# Prints nothing on success so the cron delivery stays silent; errors go to stderr (cron failure notice).
set -euo pipefail
: "${RCPARTS_HOME:?set RCPARTS_HOME in the profile .env}"
cd "$RCPARTS_HOME"
out="$(uv run rcparts orders daily --send)"
if ! printf '%s' "$out" | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("ok") and not d.get("send_error") else 1)'; then
  printf 'daily order batch failed: %s\n' "$out" >&2
  exit 1
fi
