#!/bin/bash
# Skunkworks Sloth: daily Curator job (Hermes cron, script only, no model turn of its own).
# Installed to ~/.hermes/profiles/sloth-curator/scripts/curate-daily.sh by the coordinator.
# Quiet unless the Reading List has new links: then `sloth curate` triages them with local
# Gemma and posts its own report to #sk-curator, Valhalla proposals to #sk-valhalla, and a
# line to #sk-logs. Empty stdout keeps the cron silent.
set -euo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export SLOTH_DRY_RUN=0
cd __SLOTH_HOME__
LOG=.sloth/curate-daily.log
new=$(uv run sloth curator collect 2>>"$LOG" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("new", 0))')
echo "$(date -u +%FT%TZ) new=$new" >> "$LOG"
if [ "${new:-0}" -gt 0 ]; then
  uv run sloth curate --batch 200 >> "$LOG" 2>&1
fi
