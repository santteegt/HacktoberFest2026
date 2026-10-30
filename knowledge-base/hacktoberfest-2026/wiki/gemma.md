---
type: tool
title: "Gemma"
description: "Google's open-weight model family (Gemma 4: E2B, E4B, 12B, 26B A4B, 31B), Apache 2.0, runnable locally; a Featured prize category."
tags: [models, tools]
timestamp: "2026-10-25T00:00:00Z"
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
- First-hand (Week 2): Gemma 4 26B A4B (MoE, about 4B active) through OpenRouter ran a WhatsApp agent in Spanish and English; it produced correct listing values but drifted field names (`type` for `kind`, `price` for `price_usd`) and invented phone numbers when asked to pass identity. The free `:free` pool was rate-limited; the paid id cost about $0.0014 per 20k-token call.
- First-hand (Week 3): Gemma 4 12B QAT on Ollama (64k context) triaged 969 links at about 4.2 s of compute per link on an M4 Max, after code capped article and thread kinds and the prompt spelled the scale out with the author's examples; it agreed with the author on 16 of 20 links the prompt was tuned on. It also skipped its Hermes skill until SOUL.md made skill-first a hard rule.
- First-hand: `embeddinggemma:300m` placed 917 links into 49 subtopics; raw cosine piled 151 of 321 into one subtopic until vectors were centred per vertical. Gemma 4 26B A4B on OpenRouter built a tested Noir contract in 4.9 min for $0.11, but its notes overstated where the tests ran.
- First-hand (Week 4): Gemma 4 12B QAT through Ollama with thinking off wrote a comic story per ghost in 14.1-40.5 s on an M4 Max (a full haunt 20-80 s in a batch); one schema-constrained sentence took 20.1 s with thinking on. A lexical verifier found 536 of 540 sentences grounded and repaired 4; the remaining errors are semantic (an invented feature, wrong deployer wording). Gemma picks names for fix recipes but never decides a fact. See [Fact-grounded generation](fact-grounded-generation.md). The project entered the Gemma category.

## Related Concepts

- [Ollama](ollama.md)
- [Mastra](mastra.md)
- [Partner tools catalog](partner-tools-catalog.md)
- [Open-source AI prompt](open-source-ai-prompt.md)
- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [OpenRouter](openrouter.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)
- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)- [Week 4 challenge: Ghost in the Machine](week4-challenge-ghost-in-the-machine.md)
- [Fact-grounded generation](fact-grounded-generation.md)


## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
- [Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)](sources/retrospective-week4-ghost-in-the-machine.md)
