---
type: concept
title: "Challenge playbook"
description: "Ten practical rules for the next Hacktoberfest challenges, learned from the weekend build."
tags: [challenges, ideas]
timestamp: "2026-10-11T00:00:00Z"
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

## Related Concepts

- [Weekend challenge retrospective](weekend-challenge-retrospective.md)
- [Partner tools catalog](partner-tools-catalog.md)
- [DEV Challenge rules](dev-challenge-rules.md)
- [Open-source AI prompt](open-source-ai-prompt.md)
- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Week 1 challenge: Touch Grass](week1-challenge-touch-grass.md)

## Sources

- [Retrospective: Build for a Friend](sources/retrospective-weekend-build-for-a-friend.md)
- [Retrospective: Week 1 Touch Grass (Idea Leash)](sources/retrospective-week1-touch-grass.md)