---
type: framework
title: "Temporal"
description: "Durable-execution workflows for agents that must survive crashes; server is MIT; a $100 prize category."
tags: [frameworks, tools]
timestamp: "2026-10-05T00:00:00Z"
---

## Definition

Temporal runs long-lived workflows whose activities (model calls, I/O) retry automatically and are not repeated on replay.

## Key Points

- Signals and human-in-the-loop approvals, continue-as-new, streaming, MCP integration and sandboxes; `temporalio-openai-agents` plugin; SDKs for Python, Go, Java, TypeScript; local dev server [docs].
- Server is MIT and `temporal server start-dev` runs locally; Cloud $150 for 90 days [report].
- Gotcha: workflow code must be deterministic; model calls must be activities.
- Fits: scheduled or multi-day agents that must not lose state.

## Related Concepts

- [Mastra](mastra.md)
- [Partner tools catalog](partner-tools-catalog.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
