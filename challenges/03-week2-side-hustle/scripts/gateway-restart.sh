#!/usr/bin/env bash
# Restart the Hermes host gateway (it serves the rc-parts profile) without tripping over the old
# WhatsApp bridge: stop with SIGINT, wait until nothing answers on the bridge port, start in the
# background, and retry once if the new gateway still found a bridge it refuses to adopt.
#
#   scripts/gateway-restart.sh [LOGFILE]     default log: ~/.hermes/profiles/rc-parts/logs/gateway.out
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
LOG="${1:-$HOME/.hermes/profiles/rc-parts/logs/gateway.out}"
PORT="$(cat "$HOME/.hermes/profiles/rc-parts/whatsapp/bridge_port" 2>/dev/null || echo 3001)"
mkdir -p "$(dirname "$LOG")"

stop() {
  local pid; pid="$(hermes gateway status 2>/dev/null | grep -oE 'PID: [0-9]+' | grep -oE '[0-9]+')"
  [ -n "$pid" ] && kill -INT "$pid" 2>/dev/null
  for _ in $(seq 1 30); do [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null || break; sleep 1; done
  for _ in $(seq 1 30); do curl -s -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 || break; sleep 1; done
  sleep 5   # the bridge releases its session a few seconds after the port closes
}

start() {
  : > "$LOG"
  nohup hermes gateway >> "$LOG" 2>&1 &
  for _ in $(seq 1 60); do
    grep -q 'Bridge ready' "$LOG" && return 0
    grep -q -E 'failed to connect|No messaging platforms' "$LOG" && return 1
    sleep 2
  done
  return 1
}

for attempt in 1 2 3; do
  stop
  if start; then echo "gateway up, WhatsApp bridge connected (attempt $attempt); log: $LOG"; exit 0; fi
  echo "attempt $attempt: WhatsApp did not connect, retrying"
done
echo "gateway restart failed; see $LOG" >&2
exit 1
