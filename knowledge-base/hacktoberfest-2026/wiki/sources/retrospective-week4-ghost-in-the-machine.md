---
type: "source"
title: "Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)"
description: "Staging-time retrospective of the Week 4 build: a gallery of comic pages about dead Ethereum contracts, told by local Gemma and grounded by code, built by a coordinator and sixteen worker lanes; timeline, lessons applied, what went wrong, numbers and ten playbook additions."
resource: "raw/retrospective-week4-ghost-in-the-machine.md"
tags: "[challenges, ideas, tools, models, frameworks]"
timestamp: "2026-10-30T00:00:00Z"
source_hash: "sha256:f3b2c9b8c531647848f42c4e57578fb62208dc6954d386441aaacf059e95eae5"
---

## Summary

Written 2026-10-30 right after staging the DEV draft (not yet published; publish target Oct 31 22:00 local, deadline Nov 1 06:59 UTC). It covers Eth Ghosts: a Python pipeline that picks an old Ethereum contract, gathers keyless facts, finds its wounds (Slither, a cited incident catalog, regex), lets code decide its kind, and has Gemma 4 12B through Ollama write the story as a comic page narrated by Dona Gwei. Pages go to a static gallery on Vercel under a .tech domain, and a Hermes profile runs two crons and reports to Discord. The build used one coordinator session and sixteen worker lanes. The outcome is unknown.

## Key Concepts

- [Week 4 challenge: Ghost in the Machine](../week4-challenge-ghost-in-the-machine.md)
- [Fact-grounded generation](../fact-grounded-generation.md)
- [Browser autoplay first-visit gesture](../browser-autoplay-first-visit-gesture.md)
- [DEV draft image cache](../dev-draft-image-cache.md)
- [Parallel agent lanes](../parallel-agent-lanes.md)
- [Hermes Agent](../hermes-agent.md)
- [Gemma](../gemma.md)
- [Ollama](../ollama.md)
- [Small local model agent patterns](../small-local-model-agent-patterns.md)
- [Partner tools catalog](../partner-tools-catalog.md)
- [Challenge playbook](../challenge-playbook.md)

## Notable Points

- On the final runs the lexical verifier checked 540 sentences on 18 ghosts: 536 grounded, 4 repaired, 0 dropped; its remaining blind spot is semantic errors such as an invented feature.
- Blockscout's transaction counter returned 0 for contracts it never counted; 9 of 25 ghosts read as never called, and real calls existed for 6 of the 9. A number that is in the facts still passes the verifier.
- DEV cached each image at the first save, which came before the push; repinning the URLs to a new commit fixed the broken images.
