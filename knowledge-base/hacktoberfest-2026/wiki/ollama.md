---
type: tool
title: "Ollama"
description: "Local model runtime used to serve Gemma in the weekend build; not a prize partner, but the enabling tool and source of several first-hand findings."
tags: [tools, models]
timestamp: "2026-10-25T00:00:00Z"
---

## Definition

Ollama serves open-weight models on a laptop through a native HTTP API and a CLI, and was the runtime for the weekend project.

## Key Points

- Intel Macs run CPU only and need macOS 14 or newer [report]; Apple Silicon uses the GPU.
- `ollama run <tag> --verbose` prints prompt eval rate and eval rate in tokens per second; the most useful one-minute benchmark to ask a friend for.
- Native `/api/chat` accepts a JSON-schema `format`, `num_ctx`, `think:false` and `keep_alive`; the schema does not reach the model's context.
- First-hand: no prompt-prefix reuse when the user text changed between calls, so prompt length sets latency; `num_ctx` 4096 keeps memory down on small machines.
- First-hand: Mastra's model router could not set `num_ctx`, so the project called Ollama's native API directly.
- First-hand (Week 1): the runtime keeps one model loaded and reloads it when the model name or `num_ctx` changes between callers; `/api/ps` shows what is loaded and with what context. One derived alias and one context size removed the reloads.
- First-hand (Week 3): one slot serves every caller, so a long triage batch made Discord agent turns take minutes and an abandoned browser request blocked everything behind it. Hermes needs `num_ctx` of at least 64k; per-link compute was the same at 32k and 64k.

## Related Concepts

- [Gemma](gemma.md)
- [Mastra](mastra.md)
- [Challenge playbook](challenge-playbook.md)
- [Hermes Agent](hermes-agent.md)
- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
