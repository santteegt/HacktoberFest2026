#!/bin/bash
# Install Skunkworks Sloth's three agents on this Hermes host from the profile distributions in
# profiles/<agent>/. Idempotent: run it again to update the profiles in place.
#
#   scripts/install.sh [--prefix sloth] [--prototypes DIR] [--no-alias] [--yes]
#
# What it does: checks prerequisites, `uv sync`, creates the `sloth-gemma4-12b` Ollama alias if it
# is missing, installs (or updates) the profiles <prefix>-curator, <prefix>-coordinator and
# <prefix>-worker, fills the path placeholders with this checkout and the prototypes folder,
# copies config.example.toml to .sloth/config.toml if there is none, and prints what is left to do.
# It never writes a secret, never starts the gateway and never resumes a cron job.
set -euo pipefail

PREFIX=sloth
PROTOTYPES="$HOME/GitRepositories/skunkworks-prototypes"
ALIAS=--alias
YES=""
while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    --prototypes) PROTOTYPES="$2"; shift 2 ;;
    --no-alias) ALIAS=""; shift ;;
    --yes|-y) YES=-y; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

SLOTH_HOME="$(cd "$(dirname "$0")/.." && pwd)"
PROFILES_ROOT="${HERMES_HOME:-$HOME/.hermes}/profiles"
AGENTS="curator coordinator worker"
step() { printf '\n==> %s\n' "$*"; }
warn() { printf '  ! %s\n' "$*"; }

step "Prerequisites"
for cmd in hermes uv ollama; do
  command -v "$cmd" >/dev/null || { echo "missing required command: $cmd" >&2; exit 1; }
done
ver=$( (hermes --version 2>/dev/null || true) | sed -nE 's/.*v([0-9]+)\.([0-9]+)\.[0-9]+.*/\1 \2/p' | head -1)
if [ -n "$ver" ]; then
  read -r major minor <<<"$ver"
  if [ "$major" -eq 0 ] && [ "$minor" -lt 22 ]; then
    echo "Hermes >= 0.22 required (found $major.$minor)" >&2; exit 1
  fi
  echo "  hermes $major.$minor, uv, ollama: ok"
else
  # A brand-new HERMES_HOME has no dependency env yet; `hermes profile install` sets it up and
  # enforces each manifest's hermes_requires (>=0.22.0) itself.
  warn "could not read the Hermes version here; the profile install checks hermes_requires"
fi
command -v gh >/dev/null || warn "gh not found: the GitHub Project board and \`sloth approve\` need it"
command -v tiger >/dev/null || warn "tiger not found: set SLOTH_DATABASE_URL to any Postgres instead"

step "Python environment (uv sync)"
(cd "$SLOTH_HOME" && uv sync --quiet)
echo "  ok"

step "Local model alias sloth-gemma4-12b (num_ctx 65536)"
if ollama show sloth-gemma4-12b >/dev/null 2>&1; then
  echo "  already present"
else
  ollama pull gemma4:12b-it-qat
  modelfile=$(mktemp)
  printf 'FROM gemma4:12b-it-qat\nPARAMETER num_ctx 65536\n' > "$modelfile"
  ollama create sloth-gemma4-12b -f "$modelfile"
  rm -f "$modelfile"
fi

step "Hermes profiles"
mkdir -p "$PROTOTYPES"
for agent in $AGENTS; do
  name="$PREFIX-$agent"
  if [ -f "$PROFILES_ROOT/$name/distribution.yaml" ]; then
    hermes profile update "$name" $YES        # keeps the profile's own config.yaml, .env, memories
  else
    hermes profile install "$SLOTH_HOME/profiles/$agent" --name "$name" $ALIAS $YES
  fi
  # Fill the path placeholders the distribution ships instead of this machine's paths.
  python3 - "$PROFILES_ROOT/$name" "$SLOTH_HOME" "$PROTOTYPES" <<'PY'
import sys
from pathlib import Path
profile, home, protos = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
files = [profile / "config.yaml", *(profile / "scripts").glob("*.sh"), *(profile / "skills").rglob("*.md")]
for f in files:
    if f.is_file():
        text = f.read_text()
        new = text.replace("__SLOTH_HOME__", home).replace("__SLOTH_PROTOTYPES__", protos)
        if new != text:
            f.write_text(new)
            print(f"  filled paths in {f.relative_to(profile)}")
PY
done

step "Sloth config"
mkdir -p "$SLOTH_HOME/.sloth"
if [ -f "$SLOTH_HOME/.sloth/config.toml" ]; then
  echo "  .sloth/config.toml already exists (left as is)"
else
  cp "$SLOTH_HOME/config.example.toml" "$SLOTH_HOME/.sloth/config.toml"
  echo "  wrote .sloth/config.toml from config.example.toml: fill in the channel ids, Tiger service id and models"
fi

step "Left for you (nothing below was done for you)"
for agent in $AGENTS; do
  name="$PREFIX-$agent"
  keys=$(sed -nE 's/^  - name: ([A-Z_]+)$/\1/p' "$SLOTH_HOME/profiles/$agent/distribution.yaml" | tr '\n' ' ')
  echo "  $name: cp $PROFILES_ROOT/$name/.env.EXAMPLE $PROFILES_ROOT/$name/.env, then set: $keys"
done
cat <<EOF
  Then, from $SLOTH_HOME:
    uv run sloth doctor
    uv run sloth apply-schema
  Crons arrive paused. Review and resume them per profile:
EOF
for agent in $AGENTS; do
  jobs="$SLOTH_HOME/profiles/$agent/cron/jobs.json"
  [ -f "$jobs" ] || continue
  python3 - "$jobs" "$PREFIX-$agent" <<'PY'
import json, sys
for j in json.load(open(sys.argv[1]))["jobs"]:
    print(f"    hermes -p {sys.argv[2]} cron resume {j['id']}    # {j['name']}: {j.get('schedule_display', '')}")
PY
done
echo "  Start the gateway yourself when the .env files are filled (see the Hermes docs); this script never does."
