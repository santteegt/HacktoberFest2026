---
type: source
title: "Retrospective: Build for a Friend"
description: "Post-publish retrospective of the weekend challenge build (RC Pit Companion): timeline, what worked, what failed, numbers and a playbook."
resource: "raw/retrospective-weekend-build-for-a-friend.md"
tags: [challenges, ideas]
timestamp: "2026-10-05T00:00:00Z"
source_hash: "sha256:fd27250e25a671042726fff6bb7e4cda7919e9ef965556099cb0c501426d8963"
---

## Summary

Written 2026-10-05 right after publishing the weekend submission. It summarises what was built (an offline setup coach for one friend's RC car using Gemma 4 via Ollama and Mastra), the timeline, what worked, what went wrong and what it cost, the key numbers, and a ten-point playbook for the next challenges. The outcome (winners) was not known when it was written.

## Key Concepts

- [Weekend challenge retrospective](../weekend-challenge-retrospective.md)
- [Challenge playbook](../challenge-playbook.md)
- [Gemma](../gemma.md)
- [Ollama](../ollama.md)
- [Mastra](../mastra.md)

## Notable Points

- The evals ran on the wrong model: all on E4B, while the friend's laptop runs E2B, which fell back to one label on anything it could not place. Found about 2 h before the deadline.
- A deterministic off-topic gate fixed refusals (E2B 21/25 alone, 23/25 with it); the gate's word list is partly tuned on the test set.
- Only speed reading from the friend's 2019 Intel MacBook Pro: about 9.2 tokens/s writing, 38.7 tokens/s reading a prompt (E2B).
- Linking helper docs (the getting-started guide) from the README and the post was forgotten until asked.
