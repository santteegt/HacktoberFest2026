#!/bin/bash
# Refresh the Hermes profile distributions in profiles/<agent>/ from the live profiles, so changes
# made in Hermes (SOUL, config, skills, cron definitions, cron scripts) flow back into git.
#
#   scripts/export-profiles.sh [--prefix sloth]      # reads ~/.hermes/profiles/<prefix>-<agent>
#
# Copies an allow-list only: SOUL.md, config.yaml, the Sloth skills, cron/jobs.json (definitions,
# no state) and scripts/*.sh. It never reads .env, auth.json or any other credential store, strips
# this machine's paths (challenge folder → __SLOTH_HOME__, prototypes folder → __SLOTH_PROTOTYPES__;
# scripts/install.sh fills them back in), and refuses to finish if anything secret-looking or an
# absolute home path is left. distribution.yaml, .gitignore and README.md are authored in git.
set -euo pipefail

PREFIX=sloth
while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")/.." && pwd)"
LIVE_ROOT="${HERMES_HOME:-$HOME/.hermes}/profiles"

python3 - "$HERE" "$LIVE_ROOT" "$PREFIX" <<'PY'
import json, re, shutil, sys
from pathlib import Path

here, live_root, prefix = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
AGENTS = {  # agent → the Sloth skills it ships (Hermes' bundled skills come with Hermes itself)
    "curator": ["sloth-curator"],
    "coordinator": ["skunkworks-board"],
    "worker": ["prototype-box", "worker-desk"],
}
FORBIDDEN = re.compile(r"^(\.env.*|auth\.json.*|.*\.pem|.*\.key)$")
SECRET = re.compile(r"(sk-or-v1-|sk-ant-|ghp_|github_pat_|xox[bp]-|[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27})")
JOB_KEYS = ("id", "name", "prompt", "skills", "skill", "model", "provider", "base_url", "script",
            "no_agent", "context_from", "schedule", "schedule_display", "deliver", "enabled_toolsets", "workdir")


def cwd_of(profile: Path) -> str | None:
    m = re.search(r"^\s+cwd:\s*(\S+)\s*$", (profile / "config.yaml").read_text(), re.M)
    return m.group(1) if m else None


paths = {}  # absolute path on this machine → placeholder
for agent, placeholder in (("curator", "__SLOTH_HOME__"), ("worker", "__SLOTH_PROTOTYPES__")):
    cwd = cwd_of(live_root / f"{prefix}-{agent}")
    if cwd and cwd.startswith("/"):
        paths[cwd] = placeholder
        if cwd.startswith(str(Path.home()) + "/"):  # the ~/... spelling skills use
            paths["~" + cwd[len(str(Path.home())):]] = placeholder


def scrub(text: str) -> str:
    for path, placeholder in sorted(paths.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(path, placeholder)
    return text


def copy_text(src: Path, dst: Path) -> None:
    if FORBIDDEN.match(src.name):
        sys.exit(f"refusing to copy {src.name}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(scrub(src.read_text()))
    shutil.copymode(src, dst)


for agent, skills in AGENTS.items():
    src, out = live_root / f"{prefix}-{agent}", here / "profiles" / agent
    if not src.is_dir():
        sys.exit(f"no live profile {src}")
    for name in ("SOUL.md", "config.yaml"):
        copy_text(src / name, out / name)
    for skill in skills:
        if (out / "skills" / skill).exists():
            shutil.rmtree(out / "skills" / skill)
        for f in sorted((src / "skills" / skill).rglob("*")):
            if f.is_file():
                copy_text(f, out / "skills" / skill / f.relative_to(src / "skills" / skill))
    jobs_src = src / "cron" / "jobs.json"
    if jobs_src.exists() and json.loads(jobs_src.read_text()).get("jobs"):
        jobs = [{k: j[k] for k in JOB_KEYS if j.get(k) is not None} | {"repeat": {"times": None}}
                for j in json.loads(jobs_src.read_text())["jobs"]]
        (out / "cron").mkdir(exist_ok=True)
        (out / "cron" / "jobs.json").write_text(scrub(json.dumps({"jobs": jobs}, indent=2)) + "\n")
    if (src / "scripts").is_dir():
        if (out / "scripts").exists():
            shutil.rmtree(out / "scripts")
        for f in sorted((src / "scripts").glob("*.sh")):
            copy_text(f, out / "scripts" / f.name)
    print(f"exported {src.name} → profiles/{agent}/")

# Last line of defence: nothing secret-looking, no credential files, no home paths left.
home = str(Path.home())
for f in (here / "profiles").rglob("*"):
    if not f.is_file():
        continue
    if FORBIDDEN.match(f.name):
        sys.exit(f"credential-looking file in the export: {f}")
    text = f.read_text(errors="replace")
    if SECRET.search(text):
        sys.exit(f"secret-looking value in {f}; nothing should hold keys")
    if home in text:
        sys.exit(f"absolute home path left in {f}; add it to the placeholders")
print("export clean: no credential files, no secrets, no home paths")
PY
