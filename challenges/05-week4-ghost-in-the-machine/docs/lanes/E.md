# Lane E log: Hermes profile (2026-10-29, M4 Max 64 GB, Hermes v0.22.5, Claude Sonnet 5.5)

Nothing committed, nothing installed into `~/.hermes`, no gateway started, no profile parked or unparked, no token written. Operational doc: [../HERMES.md](../HERMES.md).

## Built

- `hermes/distribution.yaml` (name `ghosts`, 0.1.0, `distribution_owned`: SOUL.md, config.yaml, skills/, cron/jobs.json, scripts/; six optional env names), `hermes/.gitignore` (the distribution one, keeps `.env.example`), `hermes/.env.example` (names only).
- `hermes/SOUL.md`: keeper of the altar; hard "skill first" rule; never invents chain facts; confirmed vs suspected as the files say; never publishes on its own.
- `hermes/skills/ghost-stories/SKILL.md`: description lists the phrases; two tables (haunting, looking) that call only `__PROFILE_HOME__/scripts/haunt.sh` with a plain argument set; failure rule.
- `hermes/config.yaml`: `model` custom Ollama `ghosts-gemma4-12b`; `mcp_servers.ethereum_history.url` with the five read-only tools included; `approvals` manual with a deny list (sudo, su, doas, osascript, launchctl, crontab, security, csrutil, spctl, tccutil, pmset, systemsetup, networksetup, defaults write, chown, setuid chmod, docker, rm -rf, git push, vercel, hermes gateway/profile/cron); eleven toolsets disabled; `terminal.cwd` the project; `display.platforms.discord` quiet.
- `hermes/cron/jobs.json`: `ghost-of-the-day` (`0 9 * * *`) and `weekly-incident` (`0 10 * * 1`), both `no_agent` script jobs, `deliver: local`, shipped `enabled: false`.
- `hermes/scripts/haunt.sh` (the work), `ghost-of-the-day.sh` and `weekly-incident.sh` (wrappers, because a cron job runs a script file with no arguments and the weekly one needs `--source incident --seed week-<ISO week>`).
- `hermes/install.sh` (`--yes --alias --dry-run --skip-sync --skip-model`).
- `docs/HERMES.md`, `tests/test_e_hermes.py` (23 tests, offline).

## Design decisions

- **Script-only crons, report built in code.** Sanitized cron environment means PATH is set inside the script; `install.sh` writes the real directories of uv, vercel, node, hermes, python3 (nvm path changes with versions) into `__EXTRA_PATH__`. The report line and the failure line are strings built by Python from `story.json`/`facts.json`; the model never writes them.
- **Tokens stay in the profile `.env`, read by the script** (`envfile_has`/`envfile_get`, never echoed) rather than `terminal.env_passthrough`, so the agent's terminal environment does not carry `VERCEL_TOKEN`. (The agent can still read the file; see the honest lines in HERMES.md.) Discord is "ready" when the profile `.env` has a bot token and a home channel; the post is `hermes -p ghosts send --to discord -q`, no model turn.
- **Interactive haunts detach.** A haunt takes minutes; the terminal tool has a command timeout (config default 180 s). `haunt.sh --detach` re-executes itself with `nohup` and returns in about a second; the result arrives through the Discord post, `--status` reads it.
- **No deploy unless asked.** The cron wrappers pass `--deploy`; a Discord request deploys only on "publish". AGENTS.md rule 4 spirit.
- **`ghosts haunt --json`.** After reading Lane G's `ghosts/haunt.py` (not wired into the CLI when I finished), the script takes the address and any error from the JSON record rather than from a story file's mtime (a resumed haunt skips steps, so no file is newer). With `haunt` missing it runs the individual commands; `face` failure is tolerated, any other step failure is the failure line.
- **Placeholders** `__GHOSTS_HOME__`, `__PROFILE_HOME__`, `__EXTRA_PATH__` are filled by `install.sh` in config.yaml, scripts and skill; the unfilled repo copy of `haunt.sh` derives the project from its own location, so `--dry-run` works straight from `hermes/scripts/`.
- bash 3.2 compatible (macOS `/bin/bash`): no `set -u`, no `mapfile`.

## Verified (and how)

- `bash -n` on `haunt.sh`, the two wrappers, `install.sh`.
- `haunt.sh --dry-run` for archive daily, incident with year and seed, an address with two sites; validation refuses a bad source, year, seed, address, site and unknown flag with exit 2; `--list`, `--show`, `--verdict`, `--status` against the four real ghosts on disk (StandardBounties verdict printed 5 confirmed scars, relayed from wounds.json).
- Stubbed `uv` and `hermes` programs on PATH (`tests/test_e_hermes.py`, `uv run pytest`: 23 passed; whole suite 198 passed on 2026-10-29 ~00:34 local): fallback order pick, summon, wounds, classify, face (failing, continues), story, render, deploy.sh; haunt-present path with `--json`; one Discord post whose text equals stdout; no post without token and channel; failure line and exit 1 (also posted); failing story names the step and stops before render; lock and mark file cleaned; detach returns at once and the child finishes.
- Distribution install into a **scratch `HERMES_HOME`** with Hermes' own `hermes_cli.profile_distribution.install_distribution` (venv python from `~/.hermes/installs`, `PYTHONPATH` the hermes-agent checkout; the `hermes` CLI itself refuses to run under a scratch home). Result: profile files copied, `.env.EXAMPLE` generated with the six names, both cron jobs `enabled: false`, `state: paused`, reason "Installed from a profile distribution; review it, then resume.", `next_run_at` null. Then the placeholder filler from `install.sh` ran on that copy: no placeholder left, installed `haunt.sh --dry-run` shows the filled PATH. `Hermes load_config_readonly` plus `validate_config_structure` on the filled config: 0 issues. `~/.hermes/profiles` listing unchanged afterwards.
- `hermes --help`, `hermes profile --help`, `hermes profile install --help`, `hermes cron create --help`, `hermes send --help`, `hermes gateway list`, per-profile `cron list` (read-only). Found: `sloth-curator` and `sloth-coordinator` have active overdue cron jobs, so parking must come before starting the host.
- Mistake along the way: I copied `~/.hermes/installs` (1.4 GB) into the scratch home trying to run the `hermes` CLI there; removed. The scratch folder under the session scratchpad still holds the test profile.

## Not verified

- No live Discord, no MCP connection, no real Gemma-driven skill selection, no real `ghosts haunt` run through the script, no `vercel deploy` from the cron environment, the Ollama alias was not created (the machine has `sloth-gemma4-12b` with the same recipe; `ghosts-gemma4-12b` is created by `install.sh`), `hermes send --to discord` not run (it posts), model reload cost between 8k and 64k not measured.
- `tools.include` for the MCP server uses the five tool names given in the brief; if the server renames one it silently disappears from the agent (the pipeline does not depend on it).

## Needs the coordinator (outside my paths)

- Wire `ghosts haunt` into `ghosts/cli.py` (Lane G) so the script's primary path is used; until then the fallback chain runs.
- `.gitignore` of the challenge folder: nothing needed (`.env` is already ignored; `hermes/.gitignore` handles the distribution). `data/cache/` (haunt log, lock) is already ignored.
- Memory entries worth logging: the host runs the cron of every unparked profile (the two overdue sloth jobs); the `hermes` CLI cannot run under a scratch `HERMES_HOME`; cron scripts get a sanitized env and must live under the profile's `scripts/`, so one wrapper per argument set.
