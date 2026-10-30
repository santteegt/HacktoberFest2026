---
type: "tool"
title: "Hermes Agent"
description: "Open agent harness (MIT) with Telegram gateway, profiles, skills and cron; used for the Leash agent in the Week 1 build."
tags: "[tools, frameworks]"
timestamp: "2026-10-25T00:00:00Z"
---

## Definition

Hermes Agent is an open-source agent harness. A profile is a separate Hermes home that isolates config, persona (SOUL.md), skills, memories, sessions, cron jobs and gateway tokens, and can be installed from a folder (a profile distribution) with one command.

## Key Points

- First-hand (v0.21.6, run in a Lume macOS VM, model through an SSH reverse tunnel): the Telegram gateway shows `clarify` choices as tappable buttons; tools can be restricted per platform in config.
- First-hand: environment variables reach the shell tool only through `terminal.env_passthrough` and a skill's `required_environment_variables`.
- First-hand: the model replayed an old error from its own history until a fresh session; a persona rule helped.
- First-hand: the chat history is a local SQLite database, useful for reading what the model actually did.
- First-hand: a 12B local model skipped commands and described them as done; critical messages moved to code.
- It cannot start a conversation without a cron job and a model turn, so proactive messages were sent by the Mac directly through the Bot API.
- First-hand (v0.22.2, Week 2): one host gateway per machine serves every profile; `hermes -p <profile> gateway` refuses to start. The Baileys WhatsApp bridge pairs by QR, supports group allowlists by JID, `require_mention`, DM allowlists, voice notes and inbound PDFs (saved to the document cache; the user message carries the saved path).
- First-hand: the session environment exposes `HERMES_SESSION_USER_ID`, `HERMES_SESSION_CHAT_TYPE` ("group" or "dm") and `HERMES_SESSION_KEY` to the shell tool, so a CLI can read the sender itself.
- First-hand: a session keeps its creation-time prompt; after changing skills or SOUL, send `/new` in each chat. `display.platforms.whatsapp` turns off tool progress, reasoning and interim messages for members.
- First-hand: killing the gateway (closing its terminal) leaves the bridge on its port; a restart right after a clean stop fails about half the time while the old bridge releases the session. Stop with SIGINT, wait, then start, with retries.
- `terminal.cwd` is not env-expanded by the gateway; pin the absolute path at install. `hermes send --to whatsapp:<digits>@s.whatsapp.net` sends from scripts without a model turn; cron jobs with `--no-agent` run a script only.
- First-hand (v0.22.5, Week 3): Hermes refuses a model whose context is under 64,000 tokens; set the Ollama alias to 65,536.
- First-hand: the multiplexed gateway serves every unparked profile and can be auto-started by a CLI call (`hermes -p X chat -q`); it brought an old WhatsApp profile online for an hour. Park old profiles (`gateway.parked`, `hermes -p <name> gateway stop`).
- First-hand: Discord works multiplexed with one bot token per profile `.env` (a shared token parks the second adapter as `duplicate_credential`); `hermes -p <profile> send --to discord:<id>` posts as that profile's bot without a running gateway.
- First-hand: `display.platforms.discord` hides tool progress (it printed the command line, user text included); cron jobs run with a sanitized environment, so scripts set PATH themselves and cannot read a locked macOS keychain; `approvals.deny` rules block sudo, keychain and launchctl calls but are a command policy, not a sandbox.
- First-hand: the agents shipped as profile distributions (`hermes profile install <dir>`, crons installed paused, scripts via `distribution_owned`), with path placeholders filled at install; tested on a scratch `HERMES_HOME`.
- First-hand: `hermes chat` reports `input_tokens` including cache reads and writes; adding them again doubled a cost estimate. The terminal tool runs `$SHELL -lic`, so checks run outside Hermes need the login-shell PATH.
- First-hand (Week 4): a `ghosts` profile ran two crons (ghost of the day, weekly incident), read an MCP server for contract history and posted a report line to Discord; the first live haunt through the profile script took 28 s. `gateway stop` refused to park a profile with no host running, so the parked marker was written by hand. The bot connected, but its first post got Discord 403 "Missing Access" until channel permissions were fixed. The Discord chat path (Gemma choosing the skill) and the MCP call from inside Hermes were untested at staging.

## Related Concepts

- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Ollama](ollama.md)
- [Gemma](gemma.md)
- [Week 1 challenge: Touch Grass](week1-challenge-touch-grass.md)
- [Messaging agent patterns](messaging-agent-patterns.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)
- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)- [Week 4 challenge: Ghost in the Machine](week4-challenge-ghost-in-the-machine.md)

- [Parallel agent lanes](parallel-agent-lanes.md)

## Sources

- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
- [Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)](sources/retrospective-week4-ghost-in-the-machine.md)
