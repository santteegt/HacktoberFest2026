---
type: tool
title: "TabPFN"
description: "Prior Labs' pretrained model for classification and regression on small tabular data; a Featured prize category."
tags: [tools, models]
timestamp: "2026-10-05T00:00:00Z"
---

## Definition

TabPFN predicts on tabular data with no training loop and handles categorical, text and missing values automatically.

## Key Points

- Local package `tabpfn` (TabPFN-3.5) or API client `tabpfn-client` (TabPFN-3.5-Plus); you must accept the license and download weights before first use [docs].
- Docs: up to 1,000,000 rows subject to limits, GPU recommended past about 1,000 rows. Report: CPU fine to about 5k rows. Treat CPU use as a test.
- Newer weights are non-commercial [report]; API free tier has daily limits [report].
- Fits: a friend's small spreadsheet (health, habits, small business) with predictions and top factors; likely a small prize pool.

## Related Concepts

- [Tiger Data](tiger-data.md)
- [Gemma](gemma.md)
- [Partner tools catalog](partner-tools-catalog.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
