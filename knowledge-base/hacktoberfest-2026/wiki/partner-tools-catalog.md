---
type: topic
title: "Partner tools catalog"
description: "Overview of the challenge partners by role (16 from the weekend, 3 added in Week 3), with pairing recipes and ideation questions; details are on each tool page."
tags: [tools, ideas]
timestamp: "2026-10-05T00:00:00Z"
---

## Definition

A map of the Weekend Challenge partners grouped by what they do, with links to one page per tool, recipes that combine them and questions to ask during ideation. Re-fetch the challenge details for later weeks, which may list other partners.

## Key Points

- **Models:** [Gemma](gemma.md) (open weights, runs locally), [Tinker](tinker.md) (hosted fine-tuning, exportable adapters), [TabPFN](tabpfn.md) (small tabular data). Local runtime used in the build: [Ollama](ollama.md).
- **Hosting and inference:** [DigitalOcean Gradient AI](digitalocean-gradient-ai.md), [Render](render.md).
- **Agent building blocks:** [Mastra](mastra.md) (TypeScript agents and workflows), [Temporal](temporal.md) (durable workflows), [Backboard](backboard.md) (memory and routing API).
- **Voice, search, data:** [ElevenLabs](elevenlabs.md), [SerpApi](serpapi.md), [MongoDB Atlas](mongodb-atlas.md), [Tiger Data](tiger-data.md).
- **Hardware:** [Arduino UNO Q](arduino-uno-q.md).
- **Added in Week 3 (2026-10-20):** [Browserbase](browserbase.md) (Stagehand, a real browser for the agent), [Auth0 for AI Agents](auth0-for-ai-agents.md) (login, Token Vault, approval of risky actions), [Ultramarine](ultramarine.md) (hosted document-reasoning model, weights pending, report the cost). All three are additive; the open core still has to be a local or open-weight model plus an open harness.
- **Used in Week 4:** [Gemma](gemma.md) for every story (Gemma category) and the .tech Domain category (a .tech domain claimed through Hacktoberfest, hosting a static gallery on Vercel). Tiger Data was not built and ElevenLabs deferred. See [Week 4 challenge: Ghost in the Machine](week4-challenge-ghost-in-the-machine.md).
- **Observability and process:** [Sentry Agent Tracing](sentry-agent-tracing.md), [Entire](entire.md), [GitHub Copilot](github-copilot.md).
- **Recipes:** grounded storyteller (local Gemma writes, code decides facts, a lexical verifier checks; see [Fact-grounded generation](fact-grounded-generation.md)); web chore agent (local Gemma via a Stagehand callback on local Chrome, hosted open-weight fallback); act-on-my-accounts agent (local model drafts, Auth0 Token Vault holds the token, CIBA approval before sending); document pile (Ultramarine drafts, local model triages, cost reported); local-first assistant (Gemma + Ollama + Mastra + local database); traced agent (Mastra + Sentry); personalised style (Tinker adapter served locally, test serving first); small-data predictor (TabPFN + Tiger Data + small Gemma); weak-machine fallback (local first, DigitalOcean inference opt-in); durable agent (Temporal activities calling a model); grounded answers (local model + SerpApi); memory-heavy companion (Backboard).
- **Ask during ideation:** can the demo run on the user's own hardware; which claim is the why-open answer and does each partner support it; which partners will the code really use; what can be plain code instead of a model call; which credits are worth claiming (ask first); what breaks without internet.
- **Unverified items** (promo amounts, Atlas M0 vector limits, Tiger Data agent features, Tinker adapter serving, Arduino AI bricks, SerpApi SDKs and others) are listed in the source page.

## Related Concepts

- [Prize categories and partners](prize-categories-and-partners.md)
- [Challenge playbook](challenge-playbook.md)
- [Weekend challenge: Build for a Friend](weekend-challenge-build-for-a-friend.md)- [Week 4 challenge: Ghost in the Machine](week4-challenge-ghost-in-the-machine.md)


## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
- [Week 3 new partners: Auth0, Browserbase, Ultramarine](sources/week3-new-partners-auth0-browserbase-ultramarine.md)
- [Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)](sources/retrospective-week4-ghost-in-the-machine.md)
