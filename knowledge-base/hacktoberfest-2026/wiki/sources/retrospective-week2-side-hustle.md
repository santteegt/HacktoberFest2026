---
type: "source"
title: "Retrospective: Week 2 Side Hustle (PartsPaddock)"
description: "Post-publish retrospective of the Week 2 build: a WhatsApp parts desk agent for RC clubs, timeline, what worked, what went wrong, numbers and playbook additions."
resource: "raw/retrospective-week2-side-hustle.md"
tags: "[challenges, ideas, tools, models]"
timestamp: "2026-10-18T00:00:00Z"
source_hash: "sha256:c2db7afae8042c5d70e7c037d64c45b28c6d0c3f7c113f488e2cf68bd838d640"
---

## Summary

Written 2026-10-18 right after publishing the Week 2 submission. It covers PartsPaddock (a Hermes Agent profile on WhatsApp with Gemma 4 26B A4B via OpenRouter, a Python CLI and Postgres on Tiger Cloud that matches spare RC parts between club members for free and quotes paid imports with deposit-receipt and tracking checks), the timeline from a late start to publishing 2 h 38 min before the deadline, what worked, what went wrong and the numbers. The outcome is not known yet.

## Key Concepts

- [Week 2 challenge: Side Hustle](../week2-challenge-side-hustle.md)
- [Messaging agent patterns](../messaging-agent-patterns.md)
- [Hermes Agent](../hermes-agent.md)
- [Gemma](../gemma.md)
- [OpenRouter](../openrouter.md)
- [Tiger Data](../tiger-data.md)
- [Cognee](../cognee.md)
- [Challenge playbook](../challenge-playbook.md)

## Notable Points

- The model invented phone numbers when asked to pass the sender; identity moved to code, read from the Hermes session environment, which also made "only the maintainer confirms payments" enforceable.
- Live use found what tests did not: English vs Spanish listings, plurals and a literal, order-sensitive store search; a bilingual glossary with position vetoes and query rewrites fixed them.
- DEV's image proxy kept a 404 for URLs fetched before the first push; pointing images at a commit SHA fixed it.
