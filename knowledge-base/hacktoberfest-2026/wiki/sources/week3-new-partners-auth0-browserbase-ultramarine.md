---
type: "source"
title: "Week 3 new partners: Auth0, Browserbase, Ultramarine"
description: "Research note on the three partner categories new in the Week 3 challenge: what each asks for, how it works, free tiers, and how it fits an open-source AI project."
resource: "raw/week3-new-partners-auth0-browserbase-ultramarine.md"
tags: [challenges, tools, models]
timestamp: "2026-10-20T00:00:00Z"
source_hash: "sha256:fb24ff3cc185f13cfae8ceb966effeb71e17cf54f1700a920acad8b0169aee14"
---

## Summary

Written 2026-10-20 at the start of the Week 3 (Slow and Steady) challenge, DEV event 81, which added three $100 partner categories not present in Week 2. It records the category text from the challenge hub, the vendor docs and launch coverage for Auth0 for AI Agents, Browserbase's Stagehand SDK and Paper Instruments' Ultramarine 1 Flash, plus the free-tier and pricing facts needed to decide whether to use them. No sponsor Agent Skills were published for the Week 3 MLH event. The note ends with a fit assessment: all three are additive to an open core, not the core itself.

## Key Concepts

- [Auth0 for AI Agents](../auth0-for-ai-agents.md)
- [Browserbase](../browserbase.md)
- [Ultramarine](../ultramarine.md)
- [Prize categories and partners](../prize-categories-and-partners.md)
- [Partner tools catalog](../partner-tools-catalog.md)

## Notable Points

- Ultramarine's weights were "coming soon" as of 2026-10-15, so until they land it is a paid hosted model and must not be described as open-weight or local; its category also requires stating the run cost.
- Stagehand v4 runs against a local Chrome with no Browserbase key, but local models reach it only through a custom LLM callback and the docs warn that small models give inconsistent structured output.
- Auth0's free plan (25,000 MAU) includes two Token Vault connected apps and asynchronous authorization, enough for a one-person agent that acts on a Google or GitHub account and asks before risky actions.
