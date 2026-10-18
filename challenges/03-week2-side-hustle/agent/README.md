# Hermes profile: rc-parts

The agent is a Hermes Agent **profile distribution** (`distribution.yaml` + `SOUL.md` + `config.yaml` + the project's `../skills`), so the same folder installs on the author's Mac for development and on the home Hermes server afterwards.

## Install or update the profile

```bash
# from the challenge folder; needs hermes on PATH (official installer) and uv
cp agent/.env.example agent/.env   # fill in the values; never commit agent/.env
scripts/setup-profile.sh --env-file agent/.env
```

The script stages `agent/` plus `../skills/` into a temporary distribution directory and runs `hermes profile install <dir> --name rc-parts --force -y`, then copies the allowed keys from the env file into the profile's `.env`. User data in the profile (memories, sessions, WhatsApp session) is preserved on reinstall.

## Pair WhatsApp and run

```bash
hermes -p rc-parts whatsapp        # scan the QR code from the bot's phone (Linked devices)
hermes gateway                     # ONE host gateway serves every profile (Hermes 0.22); `hermes gateway install` for a service
scripts/gateway-restart.sh         # restart without tripping over the old WhatsApp bridge (stop, wait, start, retry)
hermes gateway status
```

Group JID: after the bot is in the club group, read it from `~/.hermes/profiles/rc-parts/logs/gateway.log` (or ask the bot in a DM to print the group id) and put it in `WHATSAPP_GROUP_ALLOWED_USERS`.

## What is where

| Path | Role |
| --- | --- |
| `SOUL.md` | Persona and the rules the model follows |
| `config.yaml` | Model (Gemma 4 26B A4B on OpenRouter), restricted toolsets, Tiger MCP (read-only), local Whisper for voice notes |
| `distribution.yaml` | Manifest and the env vars the installer asks for |
| `../skills/rc-listings`, `../skills/rc-quote` | The two skills: how to call `rcparts` and what to do with its JSON |
| `scripts/daily-order.sh` | The order batch, run by Hermes cron with no model turn. Install or reschedule with `scripts/install-cron.sh` (reads `ORDER_BATCH_SCHEDULE` from `.env`; daily 18:00 by default, `0 * * * *` for hourly testing) |
