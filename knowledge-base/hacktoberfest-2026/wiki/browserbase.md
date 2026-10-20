---
type: tool
title: "Browserbase"
description: "Stagehand, Browserbase's MIT browser-automation SDK (act, extract, observe), runs on local Chrome or Browserbase cloud; a $100 Week 3 category; local models only through a custom callback."
tags: [tools, frameworks]
timestamp: "2026-10-20T00:00:00Z"
---

## Definition

Browserbase sells hosted headless browsers and publishes Stagehand, an open-source (MIT) SDK in TypeScript, Python and Go that lets an agent drive a real browser with natural-language primitives, each of which asks a model for JSON-schema structured output.

## Key Points

- Primitives: `act`, `extract`, `observe`; every call needs a model that returns structured output. Quickstart: https://docs.stagehand.dev/v4/first-steps/quickstart
- Local mode: `localBrowser.launch()` opens the user's Chrome with no Browserbase key; you must pass a model with your own provider key or a custom LLM callback. Cloud mode (`browserbase.launch()`) adds stealth, proxies, session recordings and the Model Gateway (automatic model choice), which only works on Browserbase-hosted browsers.
- Known providers in v4: OpenAI, Anthropic, Google, Groq, Cerebras. [Ollama](ollama.md) is not first class; it goes through a custom callback (older docs showed an OpenAI-compatible client at `http://localhost:11434/v1`) or the Vercel AI SDK route (TypeScript only). The docs warn that small local models give inconsistent structured output and are not recommended.
- Week 3 category text: drive a live site end to end with Stagehand, pull the context an open-weight model reasons over, or turn a one-off agent run into a repeatable workflow.
- Fit for the lazy theme: web chores (forms, portals, scraping into a local model's context). Risk: whether [Gemma](gemma.md) through a callback is reliable enough; run that feasibility check on day one and keep a hosted open-weight fallback (Groq) ready.

## Related Concepts

- [Partner tools catalog](partner-tools-catalog.md)
- [Prize categories and partners](prize-categories-and-partners.md)
- [Ollama](ollama.md)
- [Gemma](gemma.md)
- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Auth0 for AI Agents](auth0-for-ai-agents.md)

## Sources

- [Week 3 new partners: Auth0, Browserbase, Ultramarine](sources/week3-new-partners-auth0-browserbase-ultramarine.md)
