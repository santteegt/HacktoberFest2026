#!/usr/bin/env bash
# Install the "leash" agent as a Hermes profile on this machine (run it where Hermes runs, e.g. inside the VM).
#
#   agent/setup-profile.sh                      install or update the profile named "leash"
#   agent/setup-profile.sh --name mybot         use another profile name
#   agent/setup-profile.sh --reset-config       also overwrite the profile's config.yaml with this folder's
#                                               (updates normally keep a config you tuned on that machine)
#   agent/setup-profile.sh --env-file ./.env    also write the profile's .env from these KEY=VALUE lines
#                                               (only keys listed in distribution.yaml env_requires are copied)
#
# Expects this folder and ../skills to sit side by side (the challenge folder, or a copy of it).
# It builds a staging directory (agent files + the project skills) and installs it with
# "hermes profile install <dir>", which is the same path a git distribution would take.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/.." && pwd)"
NAME="leash"; ENVFILE=""; RESET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --env-file) ENVFILE="$2"; shift 2;;
    --reset-config) RESET=1; shift;;
    -h|--help) sed -n '2,13p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac
done

command -v hermes >/dev/null 2>&1 || { echo "hermes not found on PATH. Install Hermes first (scripts/vm/install-hermes.sh)." >&2; exit 1; }
[ -d "$PROJECT/skills" ] || { echo "no skills/ folder next to agent/ ($PROJECT)" >&2; exit 1; }

STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
for f in distribution.yaml config.yaml SOUL.md README.md; do [ -f "$HERE/$f" ] && cp "$HERE/$f" "$STAGE/$f"; done
[ -f "$HERE/mcp.json" ] && cp "$HERE/mcp.json" "$STAGE/mcp.json"
[ -d "$HERE/cron" ] && cp -R "$HERE/cron" "$STAGE/cron"
mkdir -p "$STAGE/skills"
for d in "$PROJECT"/skills/*/; do
  n="$(basename "$d")"; cp -R "$d" "$STAGE/skills/$n"; rm -rf "$STAGE/skills/$n/evals" "$STAGE/skills/$n/__pycache__"
done
echo "staged distribution in $STAGE: $(ls "$STAGE" | tr '\n' ' ')"

if hermes profile list 2>/dev/null | grep -qE "(^|[[:space:]◆])$NAME([[:space:]]|$)"; then
  echo "profile '$NAME' exists: updating from the staged files"
  hermes profile install "$STAGE" --name "$NAME" --yes --force 2>&1 || hermes profile install "$STAGE" --name "$NAME" --yes
else
  hermes profile install "$STAGE" --name "$NAME" --alias --yes
fi

# helper commands that skills call (leashctl) go on PATH
mkdir -p "$HOME/.local/bin"
for sc in "$PROJECT"/skills/*/scripts/leashctl; do [ -f "$sc" ] && install -m 0755 "$sc" "$HOME/.local/bin/leashctl" && echo "installed leashctl in $HOME/.local/bin"; done

PROFILE_DIR="${HERMES_ROOT:-$HOME/.hermes}/profiles/$NAME"
if [ "$RESET" = 1 ]; then cp "$HERE/config.yaml" "$PROFILE_DIR/config.yaml"; echo "config.yaml reset from $HERE"; fi
if [ -n "$ENVFILE" ]; then
  [ -f "$ENVFILE" ] || { echo "env file not found: $ENVFILE" >&2; exit 1; }
  keys="$(grep -E '^\s*-\s*name:' "$HERE/distribution.yaml" | sed -E 's/.*name:\s*//')"
  : > "$PROFILE_DIR/.env"; chmod 600 "$PROFILE_DIR/.env"
  for k in $keys; do grep -E "^$k=" "$ENVFILE" >> "$PROFILE_DIR/.env" || true; done
  echo "wrote $(wc -l < "$PROFILE_DIR/.env" | tr -d ' ') value(s) to $PROFILE_DIR/.env (names only shown: $(cut -d= -f1 "$PROFILE_DIR/.env" | tr '\n' ' '))"
fi
echo
echo "Done. Try:  $NAME chat      (or: hermes -p $NAME chat)"
