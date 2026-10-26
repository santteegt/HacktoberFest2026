---
type: "topic"
title: "Week 3 challenge: Slow and Steady"
description: "DEV event 81: open-source AI that rewards laziness; the Skunkworks Sloth entry and its outcome."
tags: "[challenges, ideas]"
timestamp: "2026-10-25T00:00:00Z"
---

## Definition

The third weekly Open-Source AI challenge (DEV event 81, tags `devchallenge` and `#hf26challenge`, Oct 19 19:00 to Oct 26 06:59 UTC per the challenge page; the DEV API said a day earlier). The theme, for International Sloth Day, asks for something built on open-weight models or open-source AI that does the work so you don't have to, and replaces "My First User" with an optional "The Lazy Payoff" section. It added three $100 categories: [Auth0 for AI Agents](auth0-for-ai-agents.md), [Browserbase](browserbase.md) and [Ultramarine](ultramarine.md).

## Key Points

- Entry: Skunkworks Sloth. Three [Hermes Agent](hermes-agent.md) profiles on Discord work through the author's Chrome Reading List (1,017 links, 969 unique): the Curator triages into 308 build / 609 read / 52 Valhalla with local [Gemma](gemma.md) 4 12B, the Coordinator keeps a 58-card board (mirrored to a private GitHub Project), a daily pick, a daily reading link and an Obsidian-graph second brain, and the Worker builds the pick in a two-hour box.
- Stack: [Ollama](ollama.md), Stagehand from [Browserbase](browserbase.md) on a local Chrome with the local model, Postgres on [Tiger Data](tiger-data.md), Worker on open weights via [OpenRouter](openrouter.md) with Anthropic Sonnet 5.5 for `go deep` (closed, labelled).
- Categories entered: Gemma, Browserbase, Tiger Data. Auth0 (Gmail source) was moved to runner-up and never ran.
- Lazy payoff: one measured open-weights run, about 20 minutes from pick to an approved private repo (4.9-minute build, $0.11); the author estimates 30 to 120 minutes a day including review.
- Built by one coordinator session and three parallel lanes; see [Parallel agent lanes](parallel-agent-lanes.md).
- Published by 2026-10-25 23:32 local (about 2 h 27 min before the deadline): https://dev.to/santteegt/skunkworks-sloth-a-set-of-agents-automating-my-bookmarks-review-keeping-me-focused-and-growing-my-1168
- Outcome unknown at the time of writing; winners are announced the week of Oct 26.

## Related Concepts

- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)
- [Challenge playbook](challenge-playbook.md)
- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Open-source AI prompt](open-source-ai-prompt.md)
- [Prize categories and partners](prize-categories-and-partners.md)

## Sources

- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
