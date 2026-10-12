#!/usr/bin/env bash
# Install this project's skills where an agent can find them.
#
#   scripts/install-skills.sh --target agents            symlink into <repo>/.agents/skills (Claude Code, Codex, ...)
#   scripts/install-skills.sh --target hermes            copy into the default Hermes home (~/.hermes/skills)
#   scripts/install-skills.sh --target hermes --profile leash
#                                                        copy into ~/.hermes/profiles/leash/skills
#   scripts/install-skills.sh --target hermes --hermes-home /path/to/home   explicit Hermes home (HERMES_HOME)
#   add --link to symlink instead of copying (only useful when the repo is mounted where Hermes runs)
#   add a skill name to install just that one: scripts/install-skills.sh --target agents podcast-quiz
#
# Source of truth is always challenges/02-week1-touch-grass/skills/<name>/.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$HERE/skills"
TARGET=""; PROFILE=""; HOME_OVERRIDE=""; LINK=0; NAMES=()

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="$2"; shift 2;;
    --profile) PROFILE="$2"; shift 2;;
    --hermes-home) HOME_OVERRIDE="$2"; shift 2;;
    --link) LINK=1; shift;;
    -h|--help) sed -n '2,13p' "$0"; exit 0;;
    -*) echo "unknown option: $1" >&2; exit 2;;
    *) NAMES+=("$1"); shift;;
  esac
done
[ -n "$TARGET" ] || { echo "choose --target agents|hermes" >&2; exit 2; }
[ ${#NAMES[@]} -gt 0 ] || while IFS= read -r d; do NAMES+=("$(basename "$d")"); done < <(find "$SKILLS_SRC" -mindepth 1 -maxdepth 1 -type d | sort)

case "$TARGET" in
  agents) DEST="$(cd "$HERE/../.." && pwd)/.agents/skills";;
  hermes)
    if [ -n "$HOME_OVERRIDE" ]; then H="$HOME_OVERRIDE"
    elif [ -n "$PROFILE" ]; then H="${HERMES_ROOT:-$HOME/.hermes}/profiles/$PROFILE"
    else H="${HERMES_HOME:-$HOME/.hermes}"; fi
    DEST="$H/skills";;
  *) echo "target must be agents or hermes" >&2; exit 2;;
esac
mkdir -p "$DEST"

for n in "${NAMES[@]}"; do
  src="$SKILLS_SRC/$n"
  [ -f "$src/SKILL.md" ] || { echo "skip $n: no SKILL.md in $src" >&2; continue; }
  rm -rf "${DEST:?}/$n"
  if [ "$TARGET" = agents ] || [ "$LINK" = 1 ]; then
    # relative link, so the repo can move without breaking it
    rel="$(python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$src" "$DEST")"
    ln -s "$rel" "$DEST/$n"; echo "linked  $DEST/$n -> $rel"
  else
    cp -R "$src" "$DEST/$n"; rm -rf "$DEST/$n/evals" "$DEST/$n/__pycache__"
    echo "copied  $src -> $DEST/$n (evals left out)"
  fi
done
