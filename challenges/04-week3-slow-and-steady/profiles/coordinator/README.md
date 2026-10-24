# Coordinator profile pieces (Lane 2: Board)

Files here are the Coordinator's skill text, versioned with the code. The coordinator session
installs them into `~/.hermes/profiles/sloth-coordinator/` (lanes never edit `~/.hermes/`).

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
