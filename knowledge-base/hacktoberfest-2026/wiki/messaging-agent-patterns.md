---
type: "concept"
title: "Messaging agent patterns"
description: "Patterns for a chat-app agent that handles money and many users, learned building a WhatsApp agent in the Week 2 build."
tags: "[frameworks, ideas, models]"
timestamp: "2026-10-18T00:00:00Z"
---

## Definition

Habits for building an agent that lives in a group chat and in private messages, serves several people and touches money, so that who is speaking, what matches and every number do not depend on the model.

## Key Points

- Take the sender's identity from the platform session (Hermes sets `HERMES_SESSION_USER_ID` and `HERMES_SESSION_CHAT_TYPE` for the shell), never from model arguments; the model invented phone numbers when asked to pass one. This also stops users acting as each other and makes owner-only commands real.
- One JSON contract per command (`ok`, `reply` sent verbatim, `action` as the next step); compute every price, total and quantity in code; accept the model's field-name drift in the validator instead of re-prompting.
- Keep money-moving steps behind a person: forward a deposit receipt to the maintainer and accept confirmation only from the maintainer's number; documents vary too much to trust a parser.
- In groups, answer only when mentioned, reply in one or two lines and move anything private (prices, addresses, contacts) to direct messages; hide tool progress and interim narration.
- Users mix languages and plurals; word search needs plural and accent folding and a small domain glossary, plus vetoes for opposites (front/rear, left/right) and a shared part concept, before a match counts.
- External store search can be literal and order-sensitive; try a few rewrites (filler removed, codes only, brand first) and pick the best title match.
- Start a new session after changing skills or persona: the harness keeps a session's creation-time prompt.

## Related Concepts

- [Small local model agent patterns](small-local-model-agent-patterns.md)
- [Hermes Agent](hermes-agent.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)
- [Challenge playbook](challenge-playbook.md)

## Sources

- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
