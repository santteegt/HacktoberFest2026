---
type: "tool"
title: "Cognee"
description: "Open-source (Apache-2.0) agent memory layer with graph and vector storage; evaluated for the Week 2 build and kept as backlog."
tags: "[tools, frameworks]"
timestamp: "2026-10-18T00:00:00Z"
---

## Definition

Cognee is an open-source memory layer for agents: it turns text into a knowledge graph plus a vector index (`remember`, `recall`, `improve`, `forget`) and can be self-hosted with embedded defaults (SQLite, LanceDB, Kuzu).

## Key Points

- Self-hosts with `pip install cognee` or Docker; uses OpenRouter or other OpenAI-compatible LLMs through LiteLLM; open embeddings via fastembed or Ollama; pgvector can be the vector store; `cognee-mcp` (stdio or HTTP) can be loaded by an agent harness.
- Evaluated 2026-10-18 for member memory in a WhatsApp agent: the extraction step makes several model calls per chunk (free-tier rate limits trigger its own cooldown), small models are listed as unvalidated for extraction, and a working demo was estimated at 4 to 8 hours. Plain tables on Postgres covered the structured facts instead.
- Named in the Week 2 post as the open-source next step for memory and search on the same Postgres.

## Related Concepts

- [Tiger Data](tiger-data.md)
- [Messaging agent patterns](messaging-agent-patterns.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)

## Sources

- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
