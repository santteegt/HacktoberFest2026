#!/bin/bash
# Skunkworks Sloth: 09:00 daily pick prompt (Hermes cron in sloth-coordinator, script only).
# Posts today's options (scored by code, worded by local Gemma) to #sk-coordinator. The author
# answers with a number or a title (the Coordinator agent passes it verbatim to
# `sloth pick choose`), or replies `pick` to get the same options as buttons.
# Skips when a card is already in Today. Empty stdout keeps the cron silent.
set -euo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export SLOTH_DRY_RUN=0
cd /Users/santteegt/GitRepositories/HacktoberFest2026/challenges/04-week3-slow-and-steady
if uv run sloth pick show --json | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin).get("card") else 1)'; then exit 0; fi
uv run python - <<'PY'
import json, subprocess
from sloth.core import notify
out = json.loads(subprocess.run(["uv", "run", "sloth", "pick", "options", "--json"], check=True, capture_output=True, text=True).stdout)
if out.get("ok"):
    notify.post("coordinator", "☀️ " + out["reply"] + "\n\nReply with a number or a title, or `pick` for buttons.")
PY
