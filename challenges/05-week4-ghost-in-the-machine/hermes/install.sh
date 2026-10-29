#!/usr/bin/env bash
# Install (or update) the `ghosts` Hermes profile from this folder.
#
#   hermes/install.sh [--yes] [--alias] [--dry-run] [--skip-sync] [--skip-model]
#
# What it does: checks the tools, syncs the project with uv, creates the Ollama alias
# ghosts-gemma4-12b (num_ctx 65536) if it is missing, installs the profile with
# `hermes profile install` (or `hermes profile update` when it is already there), and fills
# the path placeholders the distribution ships.
# What it never does: start the gateway, park or unpark a profile, write a token, resume a cron job.
# With HERMES_HOME set, everything lands under that folder instead of ~/.hermes (useful to test).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GHOSTS_HOME="$(cd "$HERE/.." && pwd)"
NAME=ghosts
ALIAS_MODEL=ghosts-gemma4-12b
BASE_MODEL=gemma4:12b-it-qat
PROFILES_ROOT="${HERMES_HOME:-$HOME/.hermes}/profiles"
PROFILE="$PROFILES_ROOT/$NAME"

YES=""; ALIAS=""; DRY=0; SKIP_SYNC=0; SKIP_MODEL=0
for a in "$@"; do
  case "$a" in
    -y|--yes) YES="--yes" ;;
    --alias) ALIAS="--alias" ;;
    --dry-run) DRY=1 ;;
    --skip-sync) SKIP_SYNC=1 ;;
    --skip-model) SKIP_MODEL=1 ;;
    -h|--help) sed -n 2,13p "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done

step() { printf '\n== %s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then printf '  [dry run] '; printf '%q ' "$@"; printf '\n'; else "$@"; fi; }

step "Tools"
for cmd in hermes uv ollama python3; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "  missing: $cmd" >&2; exit 1; }
done
ver="$(hermes --version 2>/dev/null | sed -nE 's/.*v([0-9]+)\.([0-9]+).*/\1 \2/p' | head -1)"
set -- $ver
if [ "${1:-0}" -eq 0 ] && [ "${2:-0}" -lt 22 ]; then echo "  Hermes >= 0.22 is required (found: ${ver:-unknown})" >&2; exit 1; fi
echo "  hermes ${1:-?}.${2:-?}, uv, ollama, python3: ok"
command -v vercel >/dev/null 2>&1 && echo "  vercel: $(command -v vercel)" || echo "  vercel: not found (deploys will fail until the Vercel CLI is installed)"

step "Project dependencies ($GHOSTS_HOME)"
if [ "$SKIP_SYNC" = 1 ]; then echo "  skipped"; else run bash -c "cd '$GHOSTS_HOME' && uv sync --quiet"; fi

step "Ollama alias $ALIAS_MODEL (num_ctx 65536; Hermes refuses a model under 64k context)"
if [ "$SKIP_MODEL" = 1 ]; then
  echo "  skipped"
elif ollama show "$ALIAS_MODEL" >/dev/null 2>&1; then
  echo "  already present"
else
  ollama show "$BASE_MODEL" >/dev/null 2>&1 || run ollama pull "$BASE_MODEL"
  if [ "$DRY" = 1 ]; then
    echo "  [dry run] ollama create $ALIAS_MODEL with: FROM $BASE_MODEL / PARAMETER num_ctx 65536"
  else
    mf="$(mktemp)"
    printf 'FROM %s\nPARAMETER num_ctx 65536\n' "$BASE_MODEL" > "$mf"
    ollama create "$ALIAS_MODEL" -f "$mf"
    rm -f "$mf"
  fi
fi
echo "  note: the pipeline keeps using $BASE_MODEL (8k); Ollama may reload the model when it switches to $ALIAS_MODEL, and back."

step "Hermes profile $NAME"
if [ -f "$PROFILE/distribution.yaml" ]; then
  run hermes profile update "$NAME" $YES        # keeps config.yaml, .env, memories, sessions
else
  run hermes profile install "$HERE" --name "$NAME" $ALIAS $YES
fi

step "Fill the path placeholders"
# PATH for cron scripts: the real directories of the tools, found now (nvm paths change with versions).
extra=""
for t in uv vercel node hermes python3; do
  p="$(command -v "$t" 2>/dev/null || true)"; [ -n "$p" ] || continue
  d="$(dirname "$p")"
  case ":$extra:" in *":$d:"*) ;; *) extra="${extra:+$extra:}$d" ;; esac
done
if [ "$DRY" = 1 ]; then
  echo "  [dry run] would replace __GHOSTS_HOME__=$GHOSTS_HOME  __PROFILE_HOME__=$PROFILE  __EXTRA_PATH__=$extra"
  echo "  in $PROFILE/config.yaml, scripts/*.sh and skills/**/SKILL.md"
else
  python3 - "$PROFILE" "$GHOSTS_HOME" "$extra" <<'PY'
import sys
from pathlib import Path
profile, home, extra = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
files = [profile / "config.yaml", *(profile / "scripts").glob("*.sh"), *(profile / "skills").rglob("*.md")]
for f in files:
    if f.is_file():
        text = f.read_text()
        new = (text.replace("__GHOSTS_HOME__", home)
                   .replace("__PROFILE_HOME__", str(profile))
                   .replace("__EXTRA_PATH__", extra))
        if new != text:
            f.write_text(new)
            print(f"  filled {f.relative_to(profile)}")
for f in (profile / "scripts").glob("*.sh"):
    f.chmod(0o755)
PY
fi

step "Left for you (nothing below was done for you)"
cat <<TXT
  1. Fill the profile env (names only; values are yours, never commit them):
       cp "$PROFILE/.env.EXAMPLE" "$PROFILE/.env"   # if .env does not exist yet
       \$EDITOR "$PROFILE/.env"
     DISCORD_BOT_TOKEN, DISCORD_ALLOWED_USERS, DISCORD_ALLOWED_CHANNELS, DISCORD_FREE_RESPONSE_CHANNELS, DISCORD_HOME_CHANNEL (optional: cron-only without them)
     VERCEL_TOKEN (optional: the Vercel CLI login is used when empty)
  2. Dry run of the haunt script (prints the commands, runs nothing):
       "$PROFILE/scripts/haunt.sh" --dry-run --source archive --seed daily --deploy
  3. Park the old profiles, start the host, resume the crons: see $GHOSTS_HOME/docs/HERMES.md
     Crons arrive paused:
       hermes -p $NAME cron list
TXT
