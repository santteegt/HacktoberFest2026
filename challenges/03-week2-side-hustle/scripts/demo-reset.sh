#!/usr/bin/env bash
# Wipe the rcparts data and seed the demo: two clubs in Cuenca, the maintainer and the second allowlisted
# member, and Xray X4 / X1 listings built from real Michael's RC Hobbies products. No DMs are sent.
#
#   scripts/demo-reset.sh                 asks before wiping; reuses data/demo_catalog.json if present
#   scripts/demo-reset.sh --yes           no prompt (scripts, CI)
#   scripts/demo-reset.sh --refresh       fetch the store again (6 searches, 2 s apart) instead of the cache
#   scripts/demo-reset.sh --keep-catalog  same as the default (reuse the cache), kept for readability
#
# Drops ONLY the tables listed in sql/schema.sql (`rcparts db reset`); other tables in the same
# database (e.g. the Tiger tutorial's `conditions` / `sensors`) are never touched.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"
export PATH="$HOME/.local/bin:$PATH"

yes=0; seed_args=()
for arg in "$@"; do
  case "$arg" in
    --yes|-y) yes=1 ;;
    --refresh) seed_args+=(--refresh) ;;
    --keep-catalog) ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

if [ "$yes" -ne 1 ]; then
  printf 'This deletes every club, member, listing, quote, order and deposit in the rcparts tables. Continue? [y/N] '
  read -r answer
  case "$answer" in y|Y|yes|si|sí) ;; *) echo "aborted"; exit 1 ;; esac
fi

check_ok() { python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("ok") else 1)'; }

reset="$(uv run rcparts db reset --yes)"
if ! printf '%s' "$reset" | check_ok; then echo "db reset failed: $reset" >&2; exit 1; fi
printf '%s' "$reset" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("dropped:", ", ".join(d["dropped"]) or "(none)")'

seed="$(uv run rcparts demo seed --no-notify ${seed_args[@]+"${seed_args[@]}"})"
if ! printf '%s' "$seed" | check_ok; then echo "demo seed failed: $seed" >&2; exit 1; fi
printf '%s' "$seed" | python3 -m json.tool --no-ensure-ascii
