---
type: concept
title: "Minimum Detectable Lap-Time Difference"
description: "The statistical formula that determines the smallest setup-change effect that can be reliably distinguished from ordinary lap-time noise, given a lap-time standard deviation and a sample size."
tags: [fusion]
timestamp: "2026-08-26T00:00:00Z"
---

## Definition

The minimum detectable lap-time difference is the smallest true effect size a setup-versus-outcome comparison can reliably distinguish from ordinary run-to-run noise, given the driver's own lap-time variability and how many laps were run per configuration.

## Key Points

```
δ ≈ 2.8 · σ · √(2/n)     smallest reliably-detectable lap-time difference

worked example — σ = 0.15 s, n = 10 laps per configuration:
δ ≈ 2.8 × 0.15 × 0.447 ≈ 0.19 s
```

- With a typical lap-time standard deviation and a 10-lap-per-configuration comparison, a genuine 0.05 s setup effect is simply invisible — it would take roughly 140 laps per configuration to detect it reliably.
- A paired, back-to-back testing design (same session, same tyres, one variable changed, order randomized or alternated) removes most of the confounding variance rather than requiring more laps to overcome it — this is usually the more practical fix than brute-force sample size.
- Any setup-comparison tool should report an effect size with a confidence interval and explicitly refuse to declare a winner when that interval spans zero, rather than reporting a bare "faster" or "slower."
- [Vehicle Dynamics Fundamentals](vehicle-dynamics-fundamentals.md)'s track-evolution point is the main real-world source of the variance this formula has to contend with — grip climbing through a race day can dwarf the setup effect being tested for.
- Laps within a single run are not independent samples — they share a driver, a battery, and a track state — so treating them as independent observations understates uncertainty and overstates confidence.

## Related Concepts

- [Vehicle Dynamics Fundamentals](vehicle-dynamics-fundamentals.md)
- [OpenGrid Canonical Data Schema](opengrid-canonical-data-schema.md)

## Sources

- [Reference Extracts from the Study Guide: Vehicle Dynamics, Gearing Math, Statistics, and Circuit Design](sources/opengrid-study-guide-reference.md)
- [OpenGrid's Own Design Decisions: Schema, Fabrication Ladder, and Logger Target](sources/opengrid-roadmap-decisions.md)
