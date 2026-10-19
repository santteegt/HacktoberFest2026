---
type: "concept"
title: "Small local model agent patterns"
description: "Patterns that made a 12B local model usable inside a Telegram agent, learned in the Week 1 build."
tags: "[models, frameworks, ideas]"
timestamp: "2026-10-18T00:00:00Z"
---

## Definition

Habits for building an agent on a small open model (Gemma 4 12B through Ollama in the Week 1 build) so that what the user must be able to trust does not depend on the model following instructions.

## Key Points

- Give the model language jobs only (summaries, quiz questions, wording); distances, scores, grades, schedules and "ready" messages are code, and the Mac sends the messages that have to be true.
- Add a verifier and a repair loop around generated output (a quote must exist in the transcript, spoken length, answer-length bias); local calls are free, so a few retries are affordable. With the verifier a skill passed 27/27 checks on three transcripts against 20/27 for a plain prompt.
- Put the next-step instruction in the tool's reply (an `action` field), not in a paragraph of a skill; the 12B skipped the paragraph.
- Restrict the agent's tools in config and keep persona, skills and cron as files in a profile, versioned like code.
- Keep one model alias and one context size across callers, or the runtime reloads the model on every hand-off.
- Read the agent's real conversations from its own database and the runtime's logs, not the agent's summary of what it did.
- Shuffle answer positions in code; model-written positions were biased.
- Week 2 (26B on OpenRouter) confirmed the same rules at a larger size and added identity: see [Messaging agent patterns](messaging-agent-patterns.md).

## Related Concepts

- [Hermes Agent](hermes-agent.md)
- [Gemma](gemma.md)
- [Ollama](ollama.md)
- [Challenge playbook](challenge-playbook.md)
- [Week 1 challenge: Touch Grass](week1-challenge-touch-grass.md)

## Sources

- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
