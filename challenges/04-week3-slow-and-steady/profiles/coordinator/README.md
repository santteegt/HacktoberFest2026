# Coordinator profile pieces (Lane 2: Board)

> **Hermes profile distribution.** Install with `scripts/install.sh` (or `hermes profile install profiles/coordinator --name sloth-coordinator`, then fill `__SLOTH_HOME__` / `__SLOTH_PROTOTYPES__`). Refresh from the live profile with `scripts/export-profiles.sh`. `SOUL.md`, `config.yaml`, `skills/`, `cron/jobs.json` and `scripts/` here are exported from the live profile; edit them in Hermes and export, or edit here and re-run the install.

Files here are the Coordinator's distribution, versioned with the code.

| File | Install to |
| --- | --- |
| `skills/skunkworks-board/SKILL.md` | `~/.hermes/profiles/sloth-coordinator/skills/skunkworks-board/SKILL.md` |

After installing, send `/new` in `#coordinator` (a session keeps its creation-time prompt).

## What the gateway needs

- `terminal.cwd` = the merged `main` checkout of this challenge folder (already set), so `uv run sloth ...`
  reads `.sloth/config.toml` and `.sloth/github-project.json` from there.
- `SLOTH_DRY_RUN=0` in the Coordinator's environment (through `terminal.env_passthrough` or the
  profile `.env`) so `notify.log/post` really send; without it every Discord line prints to stdout.
- No `SLOTH_DATABASE_URL`: `sloth.core.secrets` asks the `tiger` CLI, which reads `public`.
- `gh` logged in with the `project` scope (the author's keyring login) for `sloth board sync`.

## Cron (suggested)

| When (local) | Prompt | Why a model turn |
| --- | --- | --- |
| daily 09:00 | "Run the daily pick." | the buttons come from clarify, which needs a turn |
| Sunday 18:00 | "Ask the weekly focus." | same |
| every 30 min, `--no-agent` | `uv run sloth board sync` | safety-net sync, script only |

## Persona lines (suggested for SOUL.md)

- You keep the skunkworks board. You never decide what gets built: the author taps, the `sloth` command moves cards.
- Send command replies as given. Keep your own words to one short line.
