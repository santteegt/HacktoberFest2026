#!/bin/bash
# Skunkworks Sloth: 30-minute safety-net board sync (Hermes cron in sloth-coordinator, script only).
# Applies run rows, rewrites board/brain files and mirrors the GitHub Project. Silent.
set -euo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export SLOTH_DRY_RUN=0
cd __SLOTH_HOME__
uv run sloth board sync >> .sloth/board-sync.log 2>&1
