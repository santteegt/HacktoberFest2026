---
type: tool
title: "Sentry Agent Tracing"
description: "Sentry's tracing for agent runs, tool calls, model generations and tokens; a $100 prize category; hosted."
tags: [tools]
timestamp: "2026-10-05T00:00:00Z"
---

## Definition

Sentry traces agent and workflow invocations, LLM calls, tool executions, token usage and latency, and groups multi-turn chats into one conversation.

## Key Points

- Mastra integration needs Sentry Node SDK v11+ and `@mastra/observability`; prompts and outputs are sent by default and can be limited with `dataCollection`; sensitive keys are filtered [docs].
- Python auto-instrumentation for OpenAI SDK, LiteLLM, Pydantic AI and LangGraph; free Developer plan about 5M spans and one user [report].
- Prompts go to a hosted service: scrub PII; it undercuts a nothing-leaves-the-device claim. Tracing a local endpoint is expected to work but untested [report].

## Related Concepts

- [Mastra](mastra.md)
- [Partner tools catalog](partner-tools-catalog.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
