# AGENTS.md: Week 2 Challenge "Side Hustle"

Challenge-specific instructions. They add to the repo-level `../../AGENTS.md`, which still applies. `CLAUDE.md` here is a symlink to this file.

- **DEV event:** 80 · **Page:** https://dev.to/challenges/hacktoberfest-week2-2026-10-12
- **Window (UTC):** Oct 12, 2026 19:00 (DEV API) → **Oct 19, 2026 06:59** (= Sun Oct 18, 11:59 PM PDT; Oct 19 1:59 AM at UTC-5, the author's local time)
- **Required tags:** `#hf26challenge` and `devchallenge` (both in the official template's front matter)
- **Winners:** announced the week of Oct 19
- Full rules snapshot and official template: [CHALLENGE.md](CHALLENGE.md) · Plan: [docs/SPEC.md](docs/SPEC.md) · Post draft: [SUBMISSION.md](SUBMISSION.md) · Memory: [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md)

Re-fetch live details with `get_challenge_details` (id 80) if anything below looks stale. The challenge page wins over this file.

## The brief

Theme: **Side Hustle.** Build something with **open-weight models or open-source AI** that **someone would actually pay for**. "Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or a combination. The open pieces must be what makes the project work. Think small, specific and useful: one real problem for one real person (a freelancer, a small business owner, a niche hobby community, a friend with a tedious recurring task).

Hard requirements:
1. **New project, started inside the window.** It must not reuse code from `../01-weekend-build-for-a-friend` or `../02-week1-touch-grass`. Note any commits after the deadline in the README.
2. **Open-source AI is the core**, not decoration around a closed API.
3. **The post says who would pay for it** and what problem it solves for them.
4. **The post explains why open innovation matters** (costs low enough for the business to work, customer data kept private, fine-tuning for a niche, no lock-in to someone else's pricing, where it beat a closed approach).
5. One submission per person. Teams: one member publishes and lists teammates' DEV usernames in the body.
6. Written in English (non-English entries are not prize-eligible).

**Bonus:** land a first user. Put it in front of a real person, let them use it, and report what happened: did they pay, would they, what did they ask for next. The template has an optional "My First User" section for this. Plan the user session early and log it in the challenge memory with date, who (with permission), what they did and what they said (`QUOTE` entries need permission).

## Judging (use this to prioritize effort)

| Criterion | Weight / note |
| --- | --- |
| **Writing Quality** | **Weighted most heavily.** Clear, engaging, explains what, who for, and why open matters |
| Relevance to prompt and theme | Open-source AI at the core; something someone would actually pay for |
| Creativity | Original idea or fresh take |
| Technical Execution | It works and is well built |
| Use of partner technology | Optional; only if entering a category, and it must be meaningful |

Budget at least a quarter of the time for the post, the demo, and the README. Follow [the playbook](../../knowledge-base/hacktoberfest-2026/wiki/challenge-playbook.md) and the [small local model patterns](../../knowledge-base/hacktoberfest-2026/wiki/small-local-model-agent-patterns.md).

## Prizes ($2,550, 18 winners)

Overall $250 + DEV++ + badge; 6 featured categories $200 + badge; 11 partner categories $100 + badge; every valid submission gets a completion badge. One win per participant, but one project may enter every category it genuinely uses.

| Tier | Partners |
| --- | --- |
| Featured ($200) | **Render** · **TabPFN** · **Tinker** · **Arduino** · **DigitalOcean** · **Gemma** |
| Partner ($100) | **Backboard** · **ElevenLabs** · **Entire** · **GitHub Copilot** · **Mastra** · **MongoDB Atlas** · **Sentry Agent Tracing** · **SerpApi** · **Temporal** · **Tiger Data** · **.tech Domain** (new this week) |

What each category asks for is in [CHALLENGE.md](CHALLENGE.md). Credits and promo codes (Tinker, Render, Backboard, a free first-year .tech domain) are at https://hacktoberfest.com/my/promos. **Ask the user before claiming any code.** Use `devrelay-sponsor-skills` for current partner API usage and **ask before installing** any skill it returns. Partner notes live in the knowledge base (`wiki/partner-tools-catalog.md` and the per-partner pages).

## How to submit

1. Build in this folder (code, `LICENSE`, `.env.example`, `README.md`).
2. Fill `SUBMISSION.md` using the official template (verbatim in [CHALLENGE.md](CHALLENGE.md)). Keep every heading; remove "My First User" only if no one used it.
3. Optional but encouraged: save the agent session with DevRelay (`devrelay-sessions`), make it **public**, scrub keys first, embed it in "My Agent Session".
4. Stage with `create_article` (`published: false`; leave `ai_disclosure_level` at the default). Give the user the draft link.
5. **Publish only after the user explicitly says yes in the current session**, before the deadline. After it's live, update `../README.md`, `../../README.md` and `../../STICKERS.md`, then add a retrospective to the knowledge base `raw/` and run `/okf-wiki`.

## Chosen project: RC Parts Finder agent

Decided 2026-10-18 00:05 UTC (memory entry of the same time has the rejected options). An agent that lives in an RC club's WhatsApp group and connects members who have spare imported parts with members who need them; when nobody has the part, it quotes an import from a whitelisted US hobby shop. The paying customer is the club member who takes the import quote; the maintainer (the author) runs the import service and charges a weight-based fee plus an optional 12% processing fee.

**MVP, in build order (stop anywhere after step 4 and there is still a submission)**
1. Hermes Agent profile in `agent/` (persona, config, skills, cron) using OpenRouter as provider (Gemma 4 26B A4B, free tier, paid fallback) and the Baileys WhatsApp gateway on the spare SIM. One test club group with two members. Group allowlist by JID, `WHATSAPP_REQUIRE_MENTION=true`, DM allowlist.
2. Listing parser: HAVE / NEED messages → JSON listing (type, brand, chassis, part number, description, condition, price, qty) with a code validator; bad parses get one clarifying question.
3. Store and matcher in code: SQLite (`clubs`, `members`, `listings`, `quotes`); match on exact part number, then normalized brand + chassis + keyword overlap; DM both parties.
4. Quote path: Michael's RC Hobbies search and product JSON (`?format=json`) → price + stock + weight → `price + weight × fee_per_kg (+ 12%)` in code, parameters in `.env`. "Reply YES to add to today's order."
5. Daily batch: Hermes cron groups accepted quotes by store and DMs the maintainer a summary.
6. Demo video in the real test group, README, post.

**Rules for this project**
- The model only parses messages and phrases replies. Matching, prices, fees, totals and the daily batch are code. Every quote shown to a member is computed by code from store JSON, never by the model.
- New code only. Hermes is the harness; profile, skills and scripts are written fresh here. Nothing is imported from `../02-week1-touch-grass`.
- Use the spare SIM, never the author's number. Telegram is the hedge if the number is restricted; the post must say the PoC uses an unofficial WhatsApp client and that production needs the Cloud API.
- Confirm Michael's weight unit against one known part before any quote is shown in the demo. AMain is out of scope.
- Backlog, not this week: multi-tenancy beyond `club_id`, user-level RAG memory, order processing and payment, x402 settlement, AMain, hosting (the profile goes to the author's home Hermes instance after the challenge).
- Data lives on Tiger Cloud (service `tigerdata-demo`, `lpjy0yvp2m`, DEV). Never commit the connection string; the CLI keyring holds the password. The agent's Tiger MCP tools are read-only (`db_query`, `db_schema`); inserts run from skill code.

## Working conventions for this folder

- **Keep [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md) current** (root `AGENTS.md` rule 8). Its "may claim / must NOT claim" table is binding for the post.
- Source goes in `src/` (or the framework's convention), not the folder root.
- Run the `hf26-challenge` skill's **audit** step before drafting the post.
- Write plainly and concretely; run the `humanizer` skill on the draft.
- Do not claim a partner technology the code doesn't actually use, and do not claim a user, a payment or a willingness to pay that didn't happen.

## Status

- [x] Folder scaffolded (2026-10-12 21:07 UTC, inside the window)
- [x] Idea chosen: RC Parts Finder (2026-10-18); paying user = the club member taking an import quote
- [x] Open-source AI core tested (2026-10-18): Gemma 4 26B A4B on OpenRouter through Hermes; free pool was rate-limited, paid id in use
- [x] Prize categories chosen (2026-10-18): Gemma, Tiger Data; ElevenLabs decided at stage S4
- [~] MVP: CLI cycle passes on Tiger (S2-S5 code); WhatsApp bridge up and a DM delivered (S1); group test pending
- [ ] First-user session done and logged
- [ ] Demo recorded or deployed
- [ ] README, LICENSE, `.env.example` done; audit run
- [ ] DEV draft written and staged
- [ ] Published by the author before the deadline
