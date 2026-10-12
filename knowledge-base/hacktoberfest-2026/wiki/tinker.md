---
type: tool
title: "Tinker"
description: "Thinking Machines' hosted training API for fine-tuning and RL of open-weight models, with exportable weights; a Featured prize category."
tags: [tools, models]
timestamp: "2026-10-05T00:00:00Z"
---

## Definition

Tinker lets you write a training loop locally while remote GPUs run it, for SFT, RL (GRPO, PPO), DPO, distillation and LoRA on 28+ open models.

## Key Points

- Python SDK clients: ServiceClient, TrainingClient, SamplingClient, RestClient; sampling returns log-probabilities [docs].
- Weights can be saved and exported; cookbook utilities build Hugging Face models, create PEFT LoRA adapters and publish to the Hub; 15+ recipes [docs].
- No Gemma; LoRA only; Qwen3.5-4B about $0.74 per million training tokens; promo available [report].
- Unverified: whether a downloaded adapter can be served locally (Qwen3.5 in llama.cpp or LM Studio). Test serving before committing to an idea.
- Fits: sounds-like-my-friend writing assistants, small specialised classifiers, graders.

## Related Concepts

- [Gemma](gemma.md)
- [Partner tools catalog](partner-tools-catalog.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
