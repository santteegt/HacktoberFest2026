---
type: "concept"
title: "Small local model agent patterns"
description: "Patterns that made a 12B local model usable inside a Telegram agent, learned in the Week 1 build."
tags: "[models, frameworks, ideas]"
timestamp: "2026-10-25T00:00:00Z"
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
- Week 3: make skill-first a hard rule in SOUL.md (load the skill, run the matching command, never answer from general knowledge) and list every request phrase in the skill description; the 12B answered from general knowledge until both changed.
- Week 3: let code decide what it can (dead links, redirects, archived repos, duplicates decided 48 of 51 removals) and cap the model's scale in code where it overrates; hide login-wall text from the model.
- Week 3: treat a model's report of its own success as unverified and re-run its checks in the same environment it used.
- Week 4: the model does language, code does facts. Run a lexical verifier with one repair call and a drop, turn thinking off for latency, and build fixes from hand-written recipes where the model only picks names. Details in [Fact-grounded generation](fact-grounded-generation.md). Expect only semantic errors to remain.

## Related Concepts

- [Hermes Agent](hermes-agent.md)
- [Gemma](gemma.md)
- [Ollama](ollama.md)
- [Challenge playbook](challenge-playbook.md)
- [Week 1 challenge: Touch Grass](week1-challenge-touch-grass.md)
- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)- [Week 4 challenge: Ghost in the Machine](week4-challenge-ghost-in-the-machine.md)
- [Fact-grounded generation](fact-grounded-generation.md)


## Sources

- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
- [Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)](sources/retrospective-week4-ghost-in-the-machine.md)
