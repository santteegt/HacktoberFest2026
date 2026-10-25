#!/bin/bash
# Skunkworks Sloth: 08:00 daily reading (Hermes cron in sloth-coordinator, script only).
# Picks one never-recommended link from the Curator's `reading` bucket for the week's focus,
# posts it to #sk-daily-reading as the Coordinator bot, records it and renders its brain page.
# If today's reading was already posted (e.g. on demand), it does nothing. Silent stdout.
set -euo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export SLOTH_DRY_RUN=0
cd /Users/santteegt/GitRepositories/HacktoberFest2026/challenges/04-week3-slow-and-steady
uv run sloth reading today --post --json >> .sloth/reading-daily.log 2>&1
