#!/usr/bin/env bash
# Ghosts in the Machine: run one haunt (pick -> summon -> wounds -> classify -> face -> story ->
# render -> gallery -> deploy) and report it. Used by the two cron jobs (through their wrappers)
# and by the ghost-stories skill. Code builds the report line; no model writes it.
#
#   haunt.sh [--source archive|incident|random] [--year YYYY] [--seed daily|STRING]
#            [--address 0x... [--site host]...] [--deploy] [--detach] [--no-post] [--dry-run]
#   haunt.sh --status | --list | --show 0x... | --verdict 0x...
#
# Works with bash 3.2 (macOS /bin/bash): no `set -u`, no mapfile.
# The two path tokens below are filled by install.sh; left unfilled (the repo copy) the script
# derives the project folder from its own location.
set -o pipefail

GHOSTS_HOME="__GHOSTS_HOME__"
EXTRA_PATH="__EXTRA_PATH__"
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$GHOSTS_HOME" in __*) GHOSTS_HOME="$(cd "$SELF_DIR/../.." && pwd)" ;; esac
case "$EXTRA_PATH" in __*) EXTRA_PATH="" ;; esac
# Cron runs with a sanitized environment: set PATH here (uv, node, vercel, hermes live under the user's home).
PATH="${EXTRA_PATH:+$EXTRA_PATH:}$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export PATH
PROFILE_HOME="$(cd "$SELF_DIR/.." && pwd)"
PROFILE_NAME="${GHOSTS_PROFILE:-ghosts}"
SITE_URL="https://eth-ghosts.decentraminds.tech"
STATE_DIR="$GHOSTS_HOME/data/cache/hermes"
LOG="$STATE_DIR/haunt.log"
LAST="$STATE_DIR/last-haunt.txt"
LOCK="$STATE_DIR/haunt.lock"

SOURCE=archive; YEAR=""; SEED=""; ADDRESS=""; SITES=(); DEPLOY=0; DETACH=0; DRY=0; NOPOST=0; MODE=haunt; TARGET=""
ARGS=("$@")
die() { echo "haunt.sh: $*" >&2; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --source)  SOURCE="${2:-}"; shift 2 ;;
    --year)    YEAR="${2:-}"; shift 2 ;;
    --seed)    SEED="${2:-}"; shift 2 ;;
    --address) ADDRESS="${2:-}"; shift 2 ;;
    --site)    SITES+=("${2:-}"); shift 2 ;;
    --deploy)  DEPLOY=1; shift ;;
    --detach)  DETACH=1; shift ;;
    --no-post) NOPOST=1; shift ;;
    --dry-run) DRY=1; shift ;;
    --status)  MODE=status; shift ;;
    --list)    MODE=list; shift ;;
    --show)    MODE=show; TARGET="${2:-}"; shift 2 ;;
    --verdict) MODE=verdict; TARGET="${2:-}"; shift 2 ;;
    -h|--help) sed -n 2,12p "${BASH_SOURCE[0]}"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

# The agent supplies these arguments: accept only plain shapes.
case "$SOURCE" in archive|incident|random) ;; *) die "bad --source: $SOURCE" ;; esac
[[ -z "$YEAR" || "$YEAR" =~ ^20[12][0-9]$ ]] || die "bad --year: $YEAR"
[[ -z "$SEED" || "$SEED" =~ ^[A-Za-z0-9._:-]+$ ]] || die "bad --seed: $SEED"
[[ -z "$ADDRESS" || "$ADDRESS" =~ ^0x[0-9a-fA-F]{40}$ ]] || die "bad --address: $ADDRESS"
[[ -z "$TARGET" || "$TARGET" =~ ^0x[0-9a-fA-F]{40}$ ]] || die "bad address: $TARGET"
for s in ${SITES[@]+"${SITES[@]}"}; do [[ "$s" =~ ^[A-Za-z0-9.-]+$ ]] || die "bad --site: $s"; done
ADDRESS="$(printf '%s' "$ADDRESS" | tr 'A-F' 'a-f')"
TARGET="$(printf '%s' "$TARGET" | tr 'A-F' 'a-f')"

# ---- helpers ---------------------------------------------------------------------------
envfile_has() { [ -f "$PROFILE_HOME/.env" ] && grep -Eq "^$1=[^[:space:]#]+" "$PROFILE_HOME/.env"; }
envfile_get() { [ -f "$PROFILE_HOME/.env" ] && sed -n "s/^$1=//p" "$PROFILE_HOME/.env" | tail -1 | sed -e "s/^[\"']//" -e "s/[\"']\$//"; }
discord_ready() { envfile_has DISCORD_BOT_TOKEN && { [ -n "${DISCORD_HOME_CHANNEL:-}" ] || envfile_has DISCORD_HOME_CHANNEL; }; }
lock_holder() { [ -f "$LOCK/pid" ] && kill -0 "$(cat "$LOCK/pid" 2>/dev/null)" 2>/dev/null && cat "$LOCK/pid"; }
say() { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }

# ---- read-only modes (no network, no model) ---------------------------------------------
case "$MODE" in
  status)
    [ -f "$LAST" ] && cat "$LAST" || echo "no haunt has finished yet"
    pid="$(lock_holder)"; [ -n "$pid" ] && echo "a haunt is running now (pid $pid)"
    [ -f "$LOG" ] && { echo "--- last log lines"; tail -n 6 "$LOG"; }
    exit 0 ;;
  list)
    python3 - "$GHOSTS_HOME/web/ghosts/index.json" <<'PY'
import json, sys
try:
    rows = json.load(open(sys.argv[1]))
except (OSError, ValueError):
    rows = []
if not rows:
    print("the gallery is empty")
for g in rows[:30]:
    print(f"{g.get('name')} | {g.get('kind')} | {g.get('age')} | {g.get('address')}")
PY
    exit 0 ;;
  show|verdict)
    [ -n "$TARGET" ] || die "--$MODE needs an address"
    d="$GHOSTS_HOME/data/ghosts/$TARGET"
    python3 - "$MODE" "$d" <<'PY'
import json, sys
mode, d = sys.argv[1], sys.argv[2]
def load(n):
    try:
        return json.load(open(f"{d}/{n}.json"))
    except (OSError, ValueError):
        return None
if mode == "verdict":
    v = load("verdict")
    if not v:
        print("no verdict.json for this address: run a haunt first"); sys.exit(0)
    print("kind:", v.get("kind"))
    for r in v.get("reasons", []):
        print("-", r)
    w = load("wounds") or {}
    for f in w.get("findings", []):
        print(f"- {'confirmed' if f.get('confirmed') else 'suspected'}: {f.get('title')} ({f.get('impact')}/{f.get('confidence')})")
else:
    s = load("story")
    if not s:
        print("no story.json for this address: run a haunt first"); sys.exit(0)
    print(s.get("title")); print(s.get("tagline"))
    n = 0
    for c in s.get("chapters", []):
        for p in c.get("paragraphs", []):
            if n < 2:
                print(p); n += 1
PY
    exit 0 ;;
esac

# ---- plan (also what --dry-run prints) --------------------------------------------------
HAUNT_CMD=(uv run ghosts haunt)
if [ -n "$ADDRESS" ]; then
  HAUNT_CMD+=("$ADDRESS")
  for s in ${SITES[@]+"${SITES[@]}"}; do HAUNT_CMD+=(--site "$s"); done
else
  HAUNT_CMD+=(--source "$SOURCE")
  [ -n "$YEAR" ] && HAUNT_CMD+=(--year "$YEAR")
  [ -n "$SEED" ] && HAUNT_CMD+=(--seed "$SEED")
fi
[ "$DEPLOY" = 1 ] && HAUNT_CMD+=(--deploy)
HAUNT_CMD+=(--json)  # progress to stderr, the record to stdout

show_cmd() { printf '+'; printf ' %q' "$@"; printf '\n'; }

if [ "$DRY" = 1 ]; then
  echo "# dry run: nothing is executed"
  echo "# project:  $GHOSTS_HOME"
  echo "# profile:  $PROFILE_HOME (name $PROFILE_NAME)"
  echo "# PATH:     $PATH"
  echo "# discord:  $(discord_ready && echo 'configured, would post to the home channel' || echo 'not configured, would only print')"
  echo "# vercel:   $(envfile_has VERCEL_TOKEN && echo 'VERCEL_TOKEN from the profile .env' || echo 'the Vercel CLI login')"
  echo "# primary (when \`ghosts haunt\` exists):"
  show_cmd "${HAUNT_CMD[@]}"
  echo "# fallback (when it does not):"
  if [ -n "$ADDRESS" ]; then A="$ADDRESS"; else
    P=(uv run ghosts pick --source "$SOURCE"); [ -n "$YEAR" ] && P+=(--year "$YEAR"); [ -n "$SEED" ] && P+=(--seed "$SEED"); P+=(--dry-run)
    show_cmd "${P[@]}"; A="ADDRESS_FROM_PICK"
  fi
  S=(uv run ghosts summon "$A"); for s in ${SITES[@]+"${SITES[@]}"}; do S+=(--site "$s"); done
  show_cmd "${S[@]}"
  for c in wounds classify face story render; do show_cmd uv run ghosts "$c" "$A"; done
  if [ "$DEPLOY" = 1 ]; then show_cmd bash scripts/deploy.sh; else show_cmd uv run ghosts gallery build; fi
  echo "# then: one summary line from story.json -> hermes -p $PROFILE_NAME send --to discord (or print)"
  exit 0
fi

# ---- detach for the chat agent: return in a second, finish in the background ---------------
mkdir -p "$STATE_DIR"
pid="$(lock_holder)"
if [ -n "$pid" ]; then echo "a haunt is already running (pid $pid); ask for the status"; exit 0; fi
if [ "$DETACH" = 1 ] && [ "${GHOSTS_HAUNT_CHILD:-0}" != 1 ]; then
  CHILD_ARGS=(); for a in ${ARGS[@]+"${ARGS[@]}"}; do [ "$a" = "--detach" ] || CHILD_ARGS+=("$a"); done
  GHOSTS_HAUNT_CHILD=1 nohup "$0" ${CHILD_ARGS[@]+"${CHILD_ARGS[@]}"} >>"$LOG" 2>&1 </dev/null &
  if discord_ready && [ "$NOPOST" = 0 ]; then where="The result will be posted in the Discord home channel."; else where="Discord is not configured: ask for the status to read the result."; fi
  echo "haunt started (pid $!). It takes a few minutes. $where"
  exit 0
fi

mkdir "$LOCK" 2>/dev/null || { rm -rf "$LOCK"; mkdir "$LOCK" || die "could not take the lock"; }
echo $$ > "$LOCK/pid"
MARK="$STATE_DIR/.mark.$$"
trap 'rm -rf "$LOCK" "$MARK"' EXIT
touch "$MARK"
T0=$(date +%s)

# Vercel: the token lives in the profile .env, read here and handed to deploy.sh only.
if [ "$DEPLOY" = 1 ] && [ -z "${VERCEL_TOKEN:-}" ] && envfile_has VERCEL_TOKEN; then
  VERCEL_TOKEN="$(envfile_get VERCEL_TOKEN)"; export VERCEL_TOKEN
fi

post() {
  [ "$NOPOST" = 0 ] && discord_ready || return 0
  hermes -p "$PROFILE_NAME" send --to discord -q "$1" >&2 || echo "(could not post to Discord)" >&2
}
finish() { # $1 = exit code, $2 = message
  printf '%s  (%ss)\n%s\n' "$(date -u +%FT%TZ)" "$(( $(date +%s) - T0 ))" "$2" > "$LAST"
  echo "$2"
  post "$2"
  exit "$1"
}

cd "$GHOSTS_HOME" || finish 1 "Haunt failed: project folder $GHOSTS_HOME not found."

# ---- run ---------------------------------------------------------------------------------
fail_step=""; haunt_err=""
if uv run ghosts haunt --help >/dev/null 2>&1; then
  say "ghosts haunt: ${HAUNT_CMD[*]}"
  out="$("${HAUNT_CMD[@]}")" || fail_step="haunt"
  printf '%s\n' "$out" >&2
  A="$(printf '%s' "$out" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("address") or "").lower())' 2>/dev/null)"
  if [ -n "$fail_step" ]; then
    haunt_err="$(printf '%s' "$out" | python3 -c 'import json,sys; print(" ".join(str(json.load(sys.stdin).get("error") or "").split())[:300])' 2>/dev/null)"
  fi
else
  say "ghosts haunt not available yet: running the individual commands"
  if [ -n "$ADDRESS" ]; then
    A="$ADDRESS"
  else
    P=(uv run ghosts pick --source "$SOURCE"); [ -n "$YEAR" ] && P+=(--year "$YEAR"); [ -n "$SEED" ] && P+=(--seed "$SEED"); P+=(--dry-run)
    say "${P[*]}"
    A="$("${P[@]}" 2>>"$LOG" | grep -Eo '0x[0-9a-fA-F]{40}' | tail -1 | tr 'A-F' 'a-f')"
    [ -n "$A" ] || fail_step="pick"
  fi
  if [ -z "$fail_step" ]; then
    S=(uv run ghosts summon "$A"); for s in ${SITES[@]+"${SITES[@]}"}; do S+=(--site "$s"); done
    say "${S[*]}"; "${S[@]}" >&2 || fail_step="summon"
  fi
  for c in wounds classify face story render; do
    [ -n "$fail_step" ] && break
    say "uv run ghosts $c $A"
    if ! uv run ghosts "$c" "$A" >&2; then
      # the Wayback face is decoration: a ghost without a screenshot is still a ghost
      if [ "$c" = face ]; then say "face failed, continuing without it"; else fail_step="$c"; fi
    fi
  done
  if [ -z "$fail_step" ]; then
    if [ "$DEPLOY" = 1 ]; then say "scripts/deploy.sh"; bash scripts/deploy.sh >&2 || fail_step="deploy"
    else say "gallery build"; uv run ghosts gallery build >&2 || fail_step="gallery"; fi
  fi
fi
if [ -n "$fail_step" ]; then
  finish 1 "Haunt failed at step: $fail_step.${haunt_err:+ $haunt_err} Details: data/cache/hermes/haunt.log"
fi

# ---- report -------------------------------------------------------------------------------
if [ -z "$ADDRESS" ] && [ -z "${A:-}" ]; then
  # the newest story written during this run
  A="$(find "$GHOSTS_HOME/data/ghosts" -name story.json -newer "$MARK" -exec ls -t {} + 2>/dev/null | head -1 | sed -E 's#.*/data/ghosts/([^/]+)/story.json#\1#')"
fi
[ -z "${A:-}" ] && A="$ADDRESS"
[ -n "$A" ] && [ -f "$GHOSTS_HOME/data/ghosts/$A/story.json" ] || finish 1 "Haunt ended but no story.json was found. Details: data/cache/hermes/haunt.log"

case "$SEED:$SOURCE" in daily:*) LABEL="Ghost of the day" ;; *:incident) LABEL="Incident ghost" ;; *) LABEL="New ghost" ;; esac
MSG="$(python3 - "$GHOSTS_HOME" "$A" "$DEPLOY" "$LABEL" "$SITE_URL" <<'PY'
import json, sys
home, addr, deployed, label, site = sys.argv[1:6]
def load(n):
    try:
        return json.load(open(f"{home}/data/ghosts/{addr}/{n}.json"))
    except (OSError, ValueError):
        return {}
s, f, v = load("story"), load("facts"), load("verdict")
name = s.get("name") or f.get("name") or addr
kind = s.get("kind") or v.get("kind") or "unknown"
era = (f.get("age") or {}).get("hardfork") or ""
bits = ", ".join(x for x in (kind, f"{era} era" if era else "") if x)
title = " ".join(str(s.get("title") or "").split())
tag = " ".join(str(s.get("tagline") or "").split())[:160]
where = f"{site}/ghosts/{addr}" if deployed == "1" else f"rendered locally, not published: web/ghosts/{addr}/index.html"
print(f'{label}: {name} ({bits}). "{title}" {tag} {where}'.replace("  ", " "))
PY
)"
[ -n "$MSG" ] || MSG="$LABEL: $A. Story written; could not read story.json for the summary."
finish 0 "$MSG"
