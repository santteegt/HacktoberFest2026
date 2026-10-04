---
type: tool
title: "DevRelay"
description: "MCP gateway and skills for DEV Challenges, MLH events, sponsor offers, and DEV publishing; installing it is a Hacktoberfest sticker."
tags: [tools, program]
timestamp: "2026-10-04T00:00:00Z"
---

## Definition

DevRelay is an MCP gateway plus a set of agent skills that give an agent live access to DEV Challenges, MLH events, sponsor offers and promo codes, a knowledge base, and DEV publishing.

## Key Points

- Install: `curl -fsSL https://devrelay.com/install.sh | sh`, then `devrelay login` with the same MyMLH account as Hacktoberfest. `devrelay --doctor` diagnoses installs. Windows: `iwr -useb https://devrelay.com/install.ps1 | iex`.
- "Install and log in to DevRelay" is a Tools sticker ([Sticker milestones](sticker-milestones.md)). How it verifies the install is not documented, so check the dashboard.
- Key tools: `get_challenges`, `get_challenge_details` (reads `full_details`), `get_knowledge_document`, `create_article` (stage drafts with `published: false`), `list_event_offers`, `claim_promo_code`.
- Skills in this repo live in `.agents/skills/devrelay-*`. Publishing is the user's call, and claiming offers or installing sponsor skills needs a yes first.
- Agent sessions can be saved and embedded in DEV posts (`devrelay-sessions`); scrub secrets first.

## Related Concepts

- [Hacktoberfest 2026](hacktoberfest-2026.md)
- [Prize categories and partners](prize-categories-and-partners.md)
- [Open-source AI prompt](open-source-ai-prompt.md)

## Sources

- [DevRelay KB: Hacktoberfest 2026](sources/devrelay-kb-hacktoberfest.md)
