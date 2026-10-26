---
type: concept
title: "Challenge playbook"
description: "Ten practical rules for the next Hacktoberfest challenges, learned from the weekend build."
tags: [challenges, ideas]
timestamp: "2026-10-25T00:00:00Z"
---

## Definition

A short list of habits that would have saved time or avoided bugs in the weekend build, to apply at the ideation and build stages of the next challenges.

## Key Points

- Day one: get the user's exact hardware and run the smallest candidate model on it with the real prompt; choose the model from that.
- Evaluate on the target model, including off-topic and gibberish inputs; gate refusals in code rather than trusting a small model.
- Keep the model's job tiny; put numbers, rules and safety in plain code.
- Start the challenge memory in the first hour, with a may-claim and must-not-claim table, and write the post from it.
- Freeze features about three hours before the deadline; use the rest for the clean-clone test, demo, screenshots, post and agent session (the post is judged most heavily).
- Record the demo on the real target device, with the network visibly off if that is the claim.
- Stage the DEV post early as unpublished, check for leftover TODO comments, and link every helper doc from the README and post.
- Capture screenshots by script against a clean database and label demo data.
- Curate the agent session (prompts and final replies, scrubbed) instead of uploading a raw multi-megabyte transcript.
- Enter partner categories only where the code really uses them, and say which parts are not open.
- Week 1 additions: test on the real device and a real outing on day one (a hidden web page gets no GPS); keep trusted messages (grades, readiness, distances) in code, not in the model.
- Put the next-step instruction in the tool's reply for small models, and write a verifier for anything the model generates.
- Fetch the live DEV draft before every update (the API replaces the whole body) and change the image URL when replacing an image DEV already shows.
- Publish with a margin: Week 1 went live about 2.5 h before the deadline, which left room for the author's last edits.
- Week 2 additions: brainstorm the day the challenge opens; run feasibility checks as parallel subagents in the first hour; never let the model pass identity; test bilingual input and plurals early; use placeholder phone numbers in tests from the start; push the repo before staging the post and point images at a commit SHA if DEV ever fetched them while missing; start a new agent session after changing skills; keep a restart script for long-running gateways.
- Week 2 published 2 h 38 min before the deadline after a late start; the author did the last edits directly on DEV, so sync the local post from the live draft before any API update.
- Week 3 additions: choose the idea within a day of opening; spend an hour on contracts before parallel agent lanes and keep one writer for shared config; set Hermes' local model to at least 64k context; drain a single-slot local model after browser timeouts; make skill-first a hard rule for small models; park old Hermes profiles; keep crons off the keychain; verify agent work in the agent's own environment; check cost math against the harness's estimate; run the measured demo before the freeze.
- Week 3 published about 2 h 27 min before the deadline; the 15:00 freeze was missed and the measured run, polish and post all landed in the last 7.5 hours. Screenshots replaced a demo video.

## Related Concepts

- [Weekend challenge retrospective](weekend-challenge-retrospective.md)
- [Partner tools catalog](partner-tools-catalog.md)
- [DEV Challenge rules](dev-challenge-rules.md)
- [Open-source AI prompt](open-source-ai-prompt.md)
- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Week 1 challenge: Touch Grass](week1-challenge-touch-grass.md)
- [Messaging agent patterns](messaging-agent-patterns.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)
- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)
- [Parallel agent lanes](parallel-agent-lanes.md)

## Sources

- [Retrospective: Build for a Friend](sources/retrospective-weekend-build-for-a-friend.md)
- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
