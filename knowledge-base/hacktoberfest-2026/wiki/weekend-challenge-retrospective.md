---
type: topic
title: "Weekend challenge retrospective"
description: "What happened in the Weekend Challenge build (RC Pit Companion): timeline, what worked, what failed and the numbers."
tags: [challenges]
timestamp: "2026-10-05T00:00:00Z"
---

## Definition

The Weekend Challenge entry, RC Pit Companion, was an offline-by-design setup coach and vault for one friend's 1/10 touring car, built with Gemma 4 via Ollama and a Mastra workflow, and published on 2026-10-05 about 1.5 h before the deadline. Outcome not yet known.

## Key Points

- **Entered categories:** Gemma and Mastra (both really used). Others skipped on purpose.
- **Worked:** one real person and a real quote; the model only does two small jobs while a reviewed table and plain code decide the numbers; a frozen credited knowledge snapshot; a running challenge memory with a may-claim table; parallel subagents with file ownership; a fresh-clone test; scripted screenshots; honest limits in the post.
- **Failed or surprised:** the phone spike (Gemma E2B in a phone browser lagged); evals only on E4B hid E2B's fallback-to-one-label behaviour; voice input defaulted to off; the only speed reading on the friend's laptop was about 9.2 tokens/s; clock mistakes in agent-written times; the getting-started guide was not linked; DEV update calls failed on first try with large bodies.
- **Numbers:** E4B 24/25 on the symptom test, E2B 21/25 alone and 23/25 with the gate; friend's five sentences E2B 5/5, E4B 4/5; 61 lever rows with 12 reviewed; 113 note chunks; held-out retrieval 9/10.
- **Open:** the app's own speed on the friend's laptop is unmeasured; 49 lever rows are still drafts; the friend has not used it at a real practice yet.

## Related Concepts

- [Weekend challenge: Build for a Friend](weekend-challenge-build-for-a-friend.md)
- [Challenge playbook](challenge-playbook.md)
- [Gemma](gemma.md)
- [Ollama](ollama.md)
- [Mastra](mastra.md)

## Sources

- [Retrospective: Build for a Friend](sources/retrospective-weekend-build-for-a-friend.md)
