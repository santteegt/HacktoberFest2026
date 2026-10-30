---
type: "concept"
title: "Fact-grounded generation"
description: "Code decides every fact and the model only writes the words; a lexical verifier checks that each claim exists in the facts, with one repair call."
tags: "[models, frameworks, challenges]"
timestamp: "2026-10-30T00:00:00Z"
---

## Definition

A pattern from the Week 4 build: code gathers the facts and makes every decision (dates, kinds, vulnerabilities, fixed code), a small local model writes prose from those facts, and a verifier rejects any sentence whose checkable tokens are not in the facts.

## Key Points

- The lexical verifier checks every year, date, number, ETH amount, multi-word name, identifier and quote against the facts. A failing sentence gets one repair call, then is dropped.
- Result on the final Week 4 runs (Gemma 4 12B, thinking off): 540 sentences on 18 ghosts, 536 grounded, 4 repaired, 0 dropped. Its first catch was "eleven other scars" on a contract with one.
- Blind spots: it is lexical only. A number that is present in the facts passes even if the fact is wrong (a zero from an indexer counter made stories say "last call on the day it was born"), and semantic errors (an invented feature, "for" versus "by") get through. Treat an indexer's zero as unknown and check it against the raw list.
- Fixes as recipes, not generation: the model only picks names from the source; code renames a hand-written recipe, checks role, arity and job, verifies the cure pattern and compiles. Where no recipe fits, the output says so and the fix is null.
- Turn thinking off: one schema-constrained sentence took 20.1 s with thinking on, while a whole story took 14-41 s with it off.
- Do not call the verifier proof; claim only that sentences were checked against the facts.

## Related Concepts

- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Gemma](gemma.md)
- [Week 4 challenge: Ghost in the Machine](week4-challenge-ghost-in-the-machine.md)
- [Challenge playbook](challenge-playbook.md)

## Sources

- [Retrospective: Week 4 Ghost in the Machine (Eth Ghosts)](sources/retrospective-week4-ghost-in-the-machine.md)
