# AGENTS.md: Week 3 Challenge "Slow and Steady"

Challenge-specific instructions. They add to the repo-level `../../AGENTS.md`, which still applies. `CLAUDE.md` here is a symlink to this file.

- **DEV event:** 81 · **Page:** https://dev.to/challenges/hacktoberfest-week3-2026-10-19
- **Window (UTC):** Oct 19, 2026 19:00 (DEV API) → **Oct 26, 2026 06:59** (= Sun Oct 25, 11:59 PM PDT; Oct 26 1:59 AM at UTC-5, the author's local time), per the challenge page and contest rules. The DEV API `ends_at` says Oct 25 06:59 UTC; the author chose to follow the page.
- **Required tags:** `#hf26challenge` and `devchallenge` (both in the official template's front matter)
- **Winners:** announced the week of Oct 26
- Full rules snapshot and official template: [CHALLENGE.md](CHALLENGE.md) · Post draft: [SUBMISSION.md](SUBMISSION.md) · Memory: [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md)

Re-fetch live details with `get_challenge_details` (id 81) if anything below looks stale. The challenge page wins over this file.

## The brief

Theme: **Slow and Steady** (International Sloth Day, Oct 20). Build something with **open-weight models or open-source AI** that **rewards laziness**: does the work so you don't have to, helps someone relax, automates a task they dread, or makes life a little easier. "Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or a combination. The open pieces must be what makes the project work.

Hard requirements:
1. **New project, started inside the window.** It must not reuse code from `../01-weekend-build-for-a-friend`, `../02-week1-touch-grass` or `../03-week2-side-hustle`. Note any commits after the deadline in the README.
2. **Open-source AI is the core**, not decoration around a closed API.
3. **The post says what effort it saves** and who gets to be lazier because of it.
4. **The post explains why open innovation matters** (works offline, keeps messages and files on your own machine, set up once and never pay again, where it beat a closed approach).
5. One submission per person. Teams: one member publishes and lists teammates' DEV usernames in the body.
6. Written in English (non-English entries are not prize-eligible).

**Bonus:** show the lazy payoff. Measure how much time or effort it saves, and have someone (the author or a friend) use it this week. The template's optional "The Lazy Payoff" section is where that goes. Log a before/after measurement in the challenge memory (date, machine, model, method) so the number in the post is backed.

## Judging (use this to prioritize effort)

| Criterion | Weight / note |
| --- | --- |
| **Writing Quality** | **Weighted most heavily.** Clear, engaging, explains what, the effort saved, and why open matters |
| Relevance to prompt and theme | Open-source AI at the core; rewards laziness |
| Creativity | Original idea or fresh take |
| Technical Execution | It works and is well built |
| Use of partner technology | Optional; only if entering a category, and it must be meaningful |

Budget at least a quarter of the time for the post, the demo, and the README. Follow [the playbook](../../knowledge-base/hacktoberfest-2026/wiki/challenge-playbook.md) and read `../../knowledge-base/hacktoberfest-2026/wiki/index.md` before brainstorming.

## Prizes ($2,850, 21 winners)

Overall $250 + DEV++ + badge; 6 featured categories $200 + badge; 14 partner categories $100 + badge; every valid submission gets a completion badge. One win per participant, but one project may enter every category it genuinely uses.

| Tier | Partners |
| --- | --- |
| Featured ($200) | **Render** · **TabPFN** · **Tinker** · **Arduino** · **DigitalOcean** · **Gemma** |
| Partner ($100) | **Auth0 for AI Agents** (new) · **Backboard** · **Browserbase** (new) · **ElevenLabs** · **Entire** · **GitHub Copilot** · **Mastra** · **MongoDB Atlas** · **Sentry Agent Tracing** · **SerpApi** · **Temporal** · **Tiger Data** · **Ultramarine (Paper Instruments)** (new) · **.tech Domain** |

What each category asks for is in [CHALLENGE.md](CHALLENGE.md). Credits and promo codes (Tinker, Render, Backboard, a free first-year .tech domain, $5 Ultramarine) are at https://hacktoberfest.com/my/promos. **Ask the user before claiming any code.** Use `devrelay-sponsor-skills` for current partner API usage and **ask before installing** any skill it returns. Partner notes live in the knowledge base (`wiki/partner-tools-catalog.md` and the per-partner pages).

## How to submit

1. Build in this folder (code, `LICENSE`, `.env.example`, `README.md`).
2. Fill `SUBMISSION.md` using the official template (verbatim in [CHALLENGE.md](CHALLENGE.md)). Keep every heading; remove "The Lazy Payoff" only if no one used it this week.
3. Optional but encouraged: save the agent session with DevRelay (`devrelay-sessions`), make it **public**, scrub keys first, embed it in "My Agent Session".
4. Stage with `create_article` (`published: false`; leave `ai_disclosure_level` at the default). Give the user the draft link.
5. **Publish only after the user explicitly says yes in the current session**, before the deadline. After it's live, update `../README.md`, `../../README.md` and `../../STICKERS.md`, then add a retrospective to the knowledge base `raw/` and run `/okf-wiki`.

## Chosen project: Skunkworks Sloth

Decided 2026-10-24 05:00 UTC (Fri Oct 23 night, local); scoped 05:30 UTC after the author's feedback. The author's Chrome "Reading List" folder holds 1,017 links saved in 2025-2026 "to learn by building", and nothing was built from them. Three Hermes agents on the author's Discord server do the work: the **Curator** (`#curator`) collects and enriches the links in daily batches (Stagehand on local Chrome where a plain fetch fails) and uses a local Gemma 4 model to keep the worthwhile ones and send the rest to **Valhalla**; the **Coordinator** (`#coordinator`) asks for a weekly focus, keeps the skunkworks board and posts one daily pick with buttons; the **Worker** (`#worker`) builds the picked prototype in a two-hour box with an open-weight model on OpenRouter, writes notes into a plain-markdown second brain and pushes the repo after an approval. Triage is local and private; the coding step is hosted open weights and the post says so with its cost.

- Parallel build: [docs/LANES.md](docs/LANES.md) (coordinator + three lanes: Curator, Board, Builder; owned paths, contracts, checkpoints CP1 Sat 16:00, CP2 Sat 20:00, CP3 Sun 12:00, freeze Sun 15:00, publish Sun 22:00 local). A lane session works only inside its owned paths and logs to `docs/lanes/<lane>.md`.
- Build contract: [docs/SPEC.md](docs/SPEC.md) (agents, data, workflows, milestones M0-M5, claims table). Clock and kill rules: [docs/PLAN.md](docs/PLAN.md). Feature freeze Sun Oct 25 15:00 local; publish target Sun 22:00 local.
- Partner categories: Gemma, Browserbase (Stagehand enrichment), Tiger Data, Entire if trivial. Runner-up after the first real prototype: Gmail source via Auth0 Token Vault (allowlisted senders, enforced in code). DigitalOcean, Temporal, SerpApi, Sentry, Ultramarine, Backboard, Render/.tech are out this week. X-bookmarks extraction is a stretch after M1.
- Rejected options and the author's design answers are in the memory (entries of 2026-10-20 to 2026-10-24). Idea notes live in `ideas/` on the author's machine only (gitignored).

## Working conventions for this folder

- **Keep [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md) current** (root `AGENTS.md` rule 8). Its "may claim / must NOT claim" table is binding for the post.
