# Curator profile files (Lane 1)

> **Hermes profile distribution.** Install with `scripts/install.sh` (or `hermes profile install profiles/curator --name sloth-curator`, then fill `__SLOTH_HOME__` / `__SLOTH_PROTOTYPES__`). Refresh from the live profile with `scripts/export-profiles.sh`. `SOUL.md`, `config.yaml`, `skills/`, `cron/jobs.json` and `scripts/` here are exported from the live profile; edit them in Hermes and export, or edit here and re-run the install.

Source of truth for the `sloth-curator` Hermes profile's Skunkworks Sloth parts. Installed by `scripts/install.sh`.

- `skills/sloth-curator/SKILL.md` → `~/.hermes/profiles/sloth-curator/skills/sloth-curator/SKILL.md`
- `SOUL.md` → suggested persona lines to merge into the profile's `SOUL.md`.

Expected profile settings (from `docs/SPEC.md`): model = the local Gemma alias through Ollama; `DISCORD_ALLOWED_CHANNELS` and `DISCORD_FREE_RESPONSE_CHANNELS` = `#sk-curator,#sk-valhalla`; terminal cwd = the merged `main` checkout of `challenges/04-week3-slow-and-steady`, with `SLOTH_DRY_RUN=0` in the profile env so the script's batch reports post for real.
