---
type: "tool"
title: "Hermes Agent"
description: "Open agent harness (MIT) with Telegram gateway, profiles, skills and cron; used for the Leash agent in the Week 1 build."
tags: "[tools, frameworks]"
timestamp: "2026-10-18T00:00:00Z"
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

## Related Concepts

- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Ollama](ollama.md)
- [Gemma](gemma.md)
- [Week 1 challenge: Touch Grass](week1-challenge-touch-grass.md)
- [Messaging agent patterns](messaging-agent-patterns.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)

## Sources

- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
