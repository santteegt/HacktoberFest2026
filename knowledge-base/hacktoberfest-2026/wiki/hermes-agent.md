---
type: "tool"
title: "Hermes Agent"
description: "Open agent harness (MIT) with Telegram gateway, profiles, skills and cron; used for the Leash agent in the Week 1 build."
tags: "[tools, frameworks]"
timestamp: "2026-10-11T00:00:00Z"
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

## Related Concepts

- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Ollama](ollama.md)
- [Gemma](gemma.md)
- [Week 1 challenge: Touch Grass](week1-challenge-touch-grass.md)

## Sources

- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
