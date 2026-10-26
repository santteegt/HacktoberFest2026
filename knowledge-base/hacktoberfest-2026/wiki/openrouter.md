---
type: "tool"
title: "OpenRouter"
description: "Hosted API for many models, including open-weight ones; used to serve Gemma 4 26B A4B in the Week 2 build."
tags: "[tools, models]"
timestamp: "2026-10-25T00:00:00Z"
---

## Definition

OpenRouter is a hosted, OpenAI-compatible API that routes requests to many model providers, including open-weight models, with per-token prices and some free `:free` variants. Hermes Agent supports it as a provider (`OPENROUTER_API_KEY`).

## Key Points

- First-hand (2026-10-17/18): the free `google/gemma-4-26b-a4b-it:free` shared pool was rate-limited upstream during the build; the paid id of the same weights answered at once at $0.0675 / $0.225 per 1M input/output tokens.
- First-hand: about 20.5k prompt tokens per Hermes model call (mostly the harness's own instructions and tool schemas), about $0.0014 per call; a listing turn well under one cent.
- An earlier key was rejected with "401 User not found" because of a mis-pasted value; check `/api/v1/auth/key` directly before debugging the harness.
- Hosting open weights keeps the swap-out option (same model on Ollama) but is not local or offline; say so in the post.
- First-hand (Week 3): `google/gemma-4-26b-a4b-it` as a Hermes Worker built a prototype in 4.9 min for $0.1113 (3.22M input tokens, 2.78M of them cache reads); an earlier fixture run cost about $0.03. Cache reads from re-reading a growing context, not box length, drive agent cost.

## Related Concepts

- [Gemma](gemma.md)
- [Hermes Agent](hermes-agent.md)
- [Ollama](ollama.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)
- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)

## Sources

- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
