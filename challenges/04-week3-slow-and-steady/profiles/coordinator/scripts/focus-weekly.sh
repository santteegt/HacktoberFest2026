#!/bin/bash
# Skunkworks Sloth: Sunday 18:00 weekly focus question (Hermes cron in sloth-coordinator, script only).
# The author answers in their own words in #sk-coordinator; the Coordinator agent passes the
# answer verbatim to `sloth focus --json`.
set -euo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export SLOTH_DRY_RUN=0
cd __SLOTH_HOME__
uv run python - <<'PY'
import json, subprocess
from sloth.core import notify
out = json.loads(subprocess.run(["uv", "run", "sloth", "focus", "--question", "--json"], check=True, capture_output=True, text=True).stdout)
if out.get("ok"):
    notify.post("coordinator", "🗓️ " + out["question"] + "\nOptions: " + " · ".join(out.get("choices", [])) + "\nReply with one of them or in your own words, or `focus` for buttons.")
PY
