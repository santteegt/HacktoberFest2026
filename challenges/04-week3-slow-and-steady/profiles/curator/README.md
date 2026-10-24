# Curator profile files (Lane 1)

Source of truth for the `sloth-curator` Hermes profile's Skunkworks Sloth parts. The coordinator installs them into `~/.hermes/profiles/sloth-curator/` (lanes never edit `~/.hermes/`).

- `skills/sloth-curator/SKILL.md` → `~/.hermes/profiles/sloth-curator/skills/sloth-curator/SKILL.md`
- `SOUL.md` → suggested persona lines to merge into the profile's `SOUL.md`.

Expected profile settings (from `docs/SPEC.md`): model = the local Gemma alias through Ollama; `DISCORD_ALLOWED_CHANNELS` and `DISCORD_FREE_RESPONSE_CHANNELS` = `#sk-curator,#sk-valhalla`; terminal cwd = the merged `main` checkout of `challenges/04-week3-slow-and-steady`, with `SLOTH_DRY_RUN=0` in the profile env so the script's batch reports post for real.
