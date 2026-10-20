---
type: tool
title: "Ultramarine"
description: "Paper Instruments' Ultramarine 1 Flash, a knowledge-work model post-trained from GLM-5.3 Flash, served through OpenAI- and Anthropic-compatible APIs; weights promised but not yet published; a $100 Week 3 category that requires stating the run cost."
tags: [tools, models]
timestamp: "2026-10-20T00:00:00Z"
---

## Definition

A hosted model from Paper Instruments, released 2026-10-14, tuned for memos, decks, spreadsheets and reasoning over piles of documents. It is post-trained from the open GLM-5.3 Flash (Z.ai), but its own weights were still "coming soon" as of 2026-10-15.

## Key Points

- API: model `ultramarine-1-flash`; base URL `https://api.paperinstruments.com/v1` for the OpenAI SDK, `https://api.paperinstruments.com` for the Anthropic SDK. Chat Completions, Responses and Messages endpoints; streaming, function tools, JSON schema. Docs: https://docs.paperinstruments.com/docs
- Reasoning is mandatory: effort `low`, `high` or `max` (no `medium`), default `max`; 32,768 output tokens including reasoning. Recommended temperature 1, top_p 0.95. An HTTP 200 can carry an incomplete result, so check `finish_reason`.
- No vision training; Responses rejects images, Messages rejects PDF blocks. Text in, text out.
- Pricing: $0.15 per million input tokens, $0.03 cached input, $0.50 output (reasoning billed as output). The vendor's "$0.13 per task" figure comes from its own suite and is unverified. $5 free credit at https://hacktoberfest.com/my/promos (ask before claiming).
- Open pieces that do exist: MIT "Feather" training code and the `paper-docx`, `paper-pptx`, `paper-xlsx` packages for editing Office files.
- Week 3 category text: research, analysis, drafting, or an agent that reasons over documents, called through the OpenAI or Anthropic SDKs, and the post must say what the run cost.
- Rule for the post: do not call it open-weight or local unless the weights are on Hugging Face by publish time; re-check before publishing. It must sit beside a real open core ([Gemma](gemma.md) through [Ollama](ollama.md), for example).

## Related Concepts

- [Partner tools catalog](partner-tools-catalog.md)
- [Prize categories and partners](prize-categories-and-partners.md)
- [OpenRouter](openrouter.md)
- [Gemma](gemma.md)

## Sources

- [Week 3 new partners: Auth0, Browserbase, Ultramarine](sources/week3-new-partners-auth0-browserbase-ultramarine.md)
