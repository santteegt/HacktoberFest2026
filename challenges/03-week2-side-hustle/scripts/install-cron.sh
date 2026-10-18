#!/usr/bin/env bash
# Install or update the order-batch cron job of the rc-parts profile from ORDER_BATCH_SCHEDULE.
#
#   scripts/install-cron.sh                   read ORDER_BATCH_SCHEDULE from .env (default "0 18 * * *", daily 18:00)
#   ORDER_BATCH_SCHEDULE="0 * * * *" scripts/install-cron.sh     hourly, for testing
#
# Accepts anything `hermes cron` accepts: cron expressions ("0 18 * * *") or intervals ("every 1h").
# The job runs agent/scripts/daily-order.sh with no model turn; re-running only changes the schedule.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${PROFILE:-rc-parts}"
NAME="daily-order"

if [ -z "${ORDER_BATCH_SCHEDULE:-}" ] && [ -f "$HERE/.env" ]; then
  ORDER_BATCH_SCHEDULE="$(grep -E '^ORDER_BATCH_SCHEDULE=' "$HERE/.env" | tail -1 | cut -d= -f2- | tr -d '"'"'" || true)"
fi
SCHEDULE="${ORDER_BATCH_SCHEDULE:-0 18 * * *}"

mkdir -p "$HOME/.hermes/profiles/$PROFILE/scripts"
cp "$HERE/agent/scripts/daily-order.sh" "$HOME/.hermes/profiles/$PROFILE/scripts/daily-order.sh"

job="$(hermes -p "$PROFILE" cron list 2>/dev/null | awk -v n="$NAME" '$0 ~ "Name: *"n"$" {print prev} {prev=$0}' | grep -oE '[0-9a-f]{12}' | head -1 || true)"
[ -z "$job" ] && job="$(hermes -p "$PROFILE" cron list 2>/dev/null | grep -B2 -E "\b$NAME\b" | grep -oE '\b[0-9a-f]{12}\b' | head -1 || true)"
if [ -n "$job" ]; then
  hermes -p "$PROFILE" cron edit "$job" --schedule "$SCHEDULE" >/dev/null
  echo "updated job $job ($NAME): $SCHEDULE"
else
  hermes -p "$PROFILE" cron create "$SCHEDULE" --name "$NAME" --no-agent --script daily-order.sh --deliver local >/dev/null
  echo "created job $NAME: $SCHEDULE"
fi
hermes -p "$PROFILE" cron list 2>/dev/null | grep -E 'Schedule|Next run' | head -2
