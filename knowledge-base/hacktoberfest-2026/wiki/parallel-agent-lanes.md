---
type: "concept"
title: "Parallel agent lanes"
description: "How one coordinator session and three parallel coding-agent sessions built the Week 3 project without merge conflicts."
tags: "[frameworks, challenges]"
timestamp: "2026-10-25T00:00:00Z"
---

## Definition

A way to split a short build across several coding-agent sessions: one coordinator owns shared state and merges, and each lane session works in its own git worktree on a disjoint set of paths, talking to the others only through contracts fixed at the start.

## Key Points

- Spend the first hour on contracts: database schema, shared types, config, a notify helper, an LLM helper and synthetic fixtures, committed to `main` before any lane starts, so no lane waits on another.
- Give each lane owned paths and one risky feasibility check (Week 3: triage quality, GitHub Project API, Stagehand plus the Worker model); a lane past a checkpoint takes its fallback instead of extending.
- Keep one writer for shared things: the coordinator alone edits the agent harness config, the dependency lock, the core package, the CLI root and the challenge memory. Lanes log to their own files; the coordinator folds results into the memory at each checkpoint.
- Split by component, not by milestone: lanes by milestone leave sessions idle on sequential dependencies. Two lanes overloaded one session; four would have cost more in merges than they saved.
- Week 3 result: every checkpoint merge was conflict-free, and CP1 landed hours early. The limit was not the lanes but the human loop: the measured run and the post still waited for the author.
- Side effect to watch: lane sessions running harness CLIs can start shared services (a Hermes gateway) that affect other projects on the host.

## Related Concepts

- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)
- [Challenge playbook](challenge-playbook.md)
- [Hermes Agent](hermes-agent.md)

## Sources

- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
