#!/usr/bin/env bash
# Install or update the "rc-parts" Hermes profile from this folder.
#
#   scripts/setup-profile.sh                       install or update the profile named "rc-parts"
#   scripts/setup-profile.sh --name mybot          another profile name
#   scripts/setup-profile.sh --env-file agent/.env also write the profile's .env from these KEY=VALUE lines
#                                                  (only keys listed in distribution.yaml env_requires are copied)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="rc-parts"; ENVFILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --env-file) ENVFILE="$2"; shift 2;;
    -h|--help) sed -n '2,8p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac
done

command -v hermes >/dev/null 2>&1 || { echo "hermes not found on PATH (official installer: https://hermes-agent.nousresearch.com)" >&2; exit 1; }

STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
for f in distribution.yaml config.yaml SOUL.md README.md; do cp "$HERE/agent/$f" "$STAGE/$f"; done
[ -f "$HERE/agent/cron/jobs.json" ] && { mkdir -p "$STAGE/cron"; cp "$HERE/agent/cron/jobs.json" "$STAGE/cron/jobs.json"; }
mkdir -p "$STAGE/skills"
for d in "$HERE"/skills/*/; do cp -R "$d" "$STAGE/skills/$(basename "$d")"; done
echo "staged: $(ls "$STAGE" | tr '\n' ' ')"

hermes profile install "$STAGE" --name "$NAME" --force -y

PROFILE_DIR="$HOME/.hermes/profiles/$NAME"
if [ -n "$ENVFILE" ]; then
  [ -f "$ENVFILE" ] || { echo "env file not found: $ENVFILE" >&2; exit 1; }
  allowed="$(grep -E '^\s*-\s*name:' "$HERE/agent/distribution.yaml" | sed -E 's/.*name:\s*//' | tr -d ' ')"
  touch "$PROFILE_DIR/.env"; chmod 600 "$PROFILE_DIR/.env"
  while IFS= read -r line; do
    case "$line" in ''|'#'*) continue;; esac
    key="${line%%=*}"
    echo "$allowed" | grep -qx "$key" || continue
    # replace or append the key
    if grep -q "^${key}=" "$PROFILE_DIR/.env"; then
      sed -i '' "s|^${key}=.*|${line}|" "$PROFILE_DIR/.env"
    else
      echo "$line" >> "$PROFILE_DIR/.env"
    fi
  done < "$ENVFILE"
  echo "wrote $(grep -c '=' "$PROFILE_DIR/.env") keys to $PROFILE_DIR/.env"
fi
# terminal.cwd is not env-expanded by the gateway, so pin the absolute path in the installed copy only.
home="$(grep '^RCPARTS_HOME=' "$PROFILE_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)"
if [ -n "$home" ]; then
  sed -i '' "s|\${RCPARTS_HOME}|$home|g" "$PROFILE_DIR/config.yaml"
  echo "terminal.cwd pinned to $home in the installed config"
fi
echo "profile '$NAME' installed at $PROFILE_DIR"
echo "next: hermes -p $NAME whatsapp   (pair the bot's phone), then hermes -p $NAME gateway"
