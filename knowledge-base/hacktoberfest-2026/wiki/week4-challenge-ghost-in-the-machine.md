---
type: "topic"
title: "Week 4 challenge: Ghost in the Machine"
description: "Week 4: open-source AI with a ghost theme; the Eth Ghosts entry and its state at staging."
tags: "[challenges, ideas]"
timestamp: "2026-10-30T00:00:00Z"
---

## Definition

The fourth weekly Open-Source AI challenge, "Ghost in the Machine" (DEV event 82, tags `devchallenge` and `#hf26challenge`; window opened Oct 26 14:00 local; the page deadline is Nov 1 06:59 UTC, one day later than what the DEV API reported). The entry is Eth Ghosts, "Ghosts in the Decentralized World Computer": an altar of old Ethereum contracts that still sit on chain after their dapps died.

## Key Points

- Pipeline: pick, summon, wounds, classify, face, story, render, og, gallery, deploy. Pickers: the Ethereum History archive (documented 2015-2017 contracts), DeFiHackLabs incidents and random blocks from dRPC. Facts come from five keyless, cached sources (Ethereum History, Sourcify, Blockscout, a public RPC, Wayback CDX).
- Code decides the kind (banished, bad, alive, lingering, friendly) from three wound tiers: Slither on verified source, a catalog of 10 cited incidents, and regex labelled "suspected". Medium findings are scars, not a death sentence.
- [Gemma](gemma.md) 4 12B QAT through [Ollama](ollama.md), thinking off, writes each story; a lexical verifier grounds it. See [Fact-grounded generation](fact-grounded-generation.md). Bad ghosts get a buster chapter and a fix from 14 hand-written recipes that compile with solc 0.8.38.
- Gallery: static pages on Vercel at a .tech domain claimed through Hacktoberfest; the first-click moment is described in [Browser autoplay first-visit gesture](browser-autoplay-first-visit-gesture.md). A [Hermes Agent](hermes-agent.md) profile runs two crons and reports to Discord; its deny rules are a command policy, not a sandbox.
- Built by a coordinator that wrote the lane contracts and never coded, plus sixteen worker lanes (Opus for design and correctness, Sonnet for plumbing); see [Parallel agent lanes](parallel-agent-lanes.md).
- Altar at staging: 26 ghosts (8 friendly, 5 lingering, 13 bad). Categories entered: Gemma and .tech Domain. Tiger Data not built, ElevenLabs deferred. Not open: Vercel, Discord, and Claude Code for the template; the data sources are online.
- State at writing: post staged as a draft (not published), session public, `main` pushed; outcome unknown. DEV staging lessons are in [DEV draft image cache](dev-draft-image-cache.md).
- Week 3 lessons: partly applied (idea chosen after two days, claims table filled at CP2), freeze and measured demo kept.

## Related Concepts

- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)
- [Challenge playbook](challenge-playbook.md)
- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Open-source AI prompt](open-source-ai-prompt.md)
- [Prize categories and partners](prize-categories-and-partners.md)
- [Partner tools catalog](partner-tools-catalog.md)

## Sources

- [Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)](sources/retrospective-week4-ghost-in-the-machine.md)
