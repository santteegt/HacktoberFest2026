---
type: framework
title: "Mastra"
description: "TypeScript agent framework (agents, tools, workflows, memory, evals); Apache 2.0 core; a $100 prize category used for the coach workflow in the weekend build."
tags: [frameworks, tools]
timestamp: "2026-10-05T00:00:00Z"
---

## Definition

Mastra is a TypeScript framework for building agents and workflows, with tools defined through `createTool()` and Zod schemas.

## Key Points

- Docs [docs]: `Agent` class with `provider/model` strings, `createTool()` (plain-object tools silently fail), integrations with Next.js, React, Astro, Express, SvelteKit and Hono, `npm create mastra@latest`. Docs state Node 22.18+; package engines declare >=22.13.
- Also [report]: workflows, memory, RAG, evals, MCP; works with any OpenAI-compatible endpoint. Sentry integration needs `@mastra/observability`, Sentry Node SDK v11+ and Mastra core 1.63.2+ [docs].
- First-hand (core 1.74.0, libsql 1.25.0): a workflow with two suspend points was suspended and resumed across three processes using LibSQL snapshots.
- First-hand traps: a Workflow has a `.then()` method, so returning it bare from an async function hangs `await` and Node exits silently (wrap it); telemetry is on by default (`MASTRA_TELEMETRY_DISABLED=1`); using Mastra means a Node process.
- Fits: human-in-the-loop flows and persistent agent workflows in TypeScript.

## Related Concepts

- [Ollama](ollama.md)
- [Sentry Agent Tracing](sentry-agent-tracing.md)
- [Temporal](temporal.md)
- [Partner tools catalog](partner-tools-catalog.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
