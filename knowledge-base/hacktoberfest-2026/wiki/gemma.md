---
type: tool
title: "Gemma"
description: "Google's open-weight model family (Gemma 4: E2B, E4B, 12B, 26B A4B, 31B), Apache 2.0, runnable locally; a Featured prize category."
tags: [models, tools]
timestamp: "2026-10-11T00:00:00Z"
---

## Definition

Gemma 4 is a family of open-weight models released from 2026-03-31, with text, image and (on the small models) audio input, configurable thinking and function calling, under Apache 2.0.

## Key Points

- Sizes and dates [docs]: E2B, E4B, 26B A4B and 31B released 2026-03-31; 12B unified 2026-06-03; multi-token-prediction variants 2026-04-16. Context up to 256K (128K on E2B and E4B).
- Runs in Ollama, llama.cpp, MLX, Hugging Face Transformers and Google Cloud. Ollama tags: e2b (about 4.6 to 7.5 GB), e4b (6.6 to 9.5 GB), 12b, 26b, 31b, plus MLX builds.
- First-hand: QAT builds `gemma4:e4b-it-qat` (6.1 GB) on an M4 Max and `gemma4:e2b-it-qat` (4.3 GB) on a 2019 Intel MacBook Pro (CPU only: about 9.2 tokens/s writing, 38.7 tokens/s reading a prompt).
- First-hand: Ollama's JSON-schema `format` guarantees valid JSON but the schema is invisible to the model, so labels and meanings must be in the prompt; E2B falls back to one label on input it cannot place (E4B refused 12/12 off-topic sentences, E2B 6/12), so gate in code.
- Fits: private or offline assistants, structured extraction, tiny-prompt classifiers, document photos (E4B). Weak fit: fast generation on old CPUs. Likely the busiest category.
- First-hand (Week 1): Gemma 4 12B QAT through Ollama wrote notes, quizzes and grading wording on a 64 GB Mac, fast enough for chat turns (most 0.7 to 7 s), but it is an unreliable tool user: it skipped commands and described them as done, and praised a wrong answer.

## Related Concepts

- [Ollama](ollama.md)
- [Mastra](mastra.md)
- [Partner tools catalog](partner-tools-catalog.md)
- [Open-source AI prompt](open-source-ai-prompt.md)
- [Small local model agent patterns](small-local-model-agent-patterns.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)