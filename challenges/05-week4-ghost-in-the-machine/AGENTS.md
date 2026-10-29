# AGENTS.md: Week 4 Challenge "Ghost in the Machine"

Challenge-specific instructions. They add to the repo-level `../../AGENTS.md`, which still applies. `CLAUDE.md` here is a symlink to this file.

- **DEV event:** 82 · **Page:** https://dev.to/challenges/hacktoberfest-week4-2026-10-26
- **Window (UTC):** Oct 26, 2026 19:00 (DEV API) → **Nov 1, 2026 06:59** (= Sat Oct 31, 11:59 PM PDT; Nov 1 1:59 AM at UTC-5, the author's local time), per the challenge page and contest rules. The DEV API `ends_at` says Oct 31 06:59 UTC (a day earlier). **The author confirmed the page deadline, Sun Nov 1 01:59 local, as the deadline (2026-10-29)**; publish target Sat Oct 31 22:00 local.
- **Required tags:** `#hf26challenge` and `devchallenge` (both in the official template's front matter)
- **Winners:** announced the week of Nov 2
- Full rules snapshot and official template: [CHALLENGE.md](CHALLENGE.md) · Post draft: [SUBMISSION.md](SUBMISSION.md) · Memory: [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md)

Re-fetch live details with `get_challenge_details` (id 82) if anything below looks stale. The challenge page wins over this file.

## The brief

Theme: **Ghost in the Machine** (Halloween Oct 31, Día de los Muertos Nov 1-2). Build something **spooky**, or something that **honors the past in the spirit of Día de los Muertos**, with **open-weight models or open-source AI**. The theme is intentionally broad: things that go bump in the night, ofrendas, or the memories and stories we carry with us. "Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or a combination. The open pieces must be what makes the project work.

Hard requirements:
1. **New project, started inside the window.** It must not reuse code from `../01-weekend-build-for-a-friend`, `../02-week1-touch-grass`, `../03-week2-side-hustle` or `../04-week3-slow-and-steady`. Note any commits after the deadline in the README.
2. **Open-source AI is the core**, not decoration around a closed API.
3. **The post says how the theme was interpreted** and what inspired it.
4. **The post explains why open innovation matters** (works with the internet off, keeps family photos and stories on your own machine, isn't locked inside a service that might disappear, where it beat a closed approach).
5. **If the demo needs a login, give judges test credentials or testing instructions** (stated explicitly this week).
6. One submission per person. Teams: one member publishes and lists teammates' DEV usernames in the body.
7. Written in English (non-English entries get the badge but no prize). Credit any non-trivial prior work, including open-source code.

**Bonus:** "The Spirit of It". Show the moment it landed: chills, a memory brought back, a story kept alive. Log who, when and what they said (with permission) in the challenge memory as a `QUOTE` entry so the post can use it; remove the section if there is no moment.

## Judging (use this to prioritize effort)

| Criterion | Weight / note |
| --- | --- |
| **Writing Quality** | **Weighted most heavily.** Clear, engaging, explains what, how the theme was read, and why open matters |
| Relevance to prompt and theme | Open-source AI at the core; spooky or honoring the past |
| Creativity | Original idea or fresh take |
| Technical Execution | It works and is well built |
| Use of partner technology | Optional; only if entering a category, and it must be meaningful |

Budget at least a quarter of the time for the post, the demo, and the README. Follow [the playbook](../../knowledge-base/hacktoberfest-2026/wiki/challenge-playbook.md) and read `../../knowledge-base/hacktoberfest-2026/wiki/index.md` before brainstorming. Week 3's lessons that apply here: choose the idea within a day of opening, write the may-claim table in the first hour, freeze features with real margin (Week 3 missed its freeze and landed everything in the last 7.5 hours), and run the measured demo before the freeze.

## Prizes ($2,850, 21 winners)

Overall $250 + DEV++ + badge; 6 featured categories $200 + badge; 14 partner categories $100 + badge; every valid submission gets a completion badge. One win per participant, but one project may enter every category it genuinely uses.

| Tier | Partners |
| --- | --- |
| Featured ($200) | **Render** · **TabPFN** · **Tinker** · **Arduino** · **DigitalOcean** · **Gemma** |
| Partner ($100) | **Auth0 for AI Agents** · **Backboard** · **Browserbase** · **ElevenLabs** · **Entire** · **GitHub Copilot** · **Mastra** · **MongoDB Atlas** · **Sentry Agent Tracing** · **SerpApi** · **Temporal** · **Tiger Data** · **Ultramarine (Paper Instruments)** · **.tech Domain** |

Same 20 categories as Week 3. What each asks for is in [CHALLENGE.md](CHALLENGE.md). Credits and promo codes (Tinker, Render, Backboard, a free first-year .tech domain, $5 Ultramarine) are at https://hacktoberfest.com/my/promos. **Ask the user before claiming any code.** Use `devrelay-sponsor-skills` for current partner API usage and **ask before installing** any skill it returns. Partner notes live in the knowledge base (`wiki/partner-tools-catalog.md` and the per-partner pages).

## How to submit

1. Build in this folder (code, `LICENSE`, `.env.example`, `README.md`).
2. Fill `SUBMISSION.md` using the official template (verbatim in [CHALLENGE.md](CHALLENGE.md)). Keep every heading; remove "The Spirit of It" only if there is no moment to show.
3. Optional but encouraged: save the agent session with DevRelay (`devrelay-sessions`), make it **public**, scrub keys first, embed it in "My Agent Session".
4. Stage with `create_article` (`published: false`; leave `ai_disclosure_level` at the default). Give the user the draft link.
5. **Publish only after the user explicitly says yes in the current session**, before the deadline. After it's live, update `../README.md`, `../../README.md` and `../../STICKERS.md`, then add a retrospective to the knowledge base `raw/` and run `/okf-wiki`.

## Chosen project: A ghosts in the decentralized world computer

Decided 2026-10-29 04:00Z (Wed Oct 28, 23:00 local) by the author, from idea 1 of [docs/BRAINSTORM.md](docs/BRAINSTORM.md). Old Ethereum contracts (2015-2017, from the Ethereum History archive) whose dapps, teams and sites are gone but whose code still sits on the chain are the ghosts. For each one the tool gathers facts with code (Ethereum History API for birth, body, decompiled code and the documented story; Sourcify for verified source; Blockscout for the last state transition, counts and balance; the public RPC for whether the code is still there; Wayback CDX for the site's captures), classifies it in code (**friendly ghost**: simply stopped being used; **bad ghost**: a vulnerability confirmed by Slither on solc ≥ 0.4 source or suspected from a curated incident catalog; **banished**: selfdestructed), and has local Gemma 4 12B write the story from inception to the day it passed away, a scary tale plus the guilty snippet for bad ghosts, and a **ghost buster** tale with a fix in Solidity 0.8.38 that solc compiles before it is shown. A comic-like animated template (designed once with Claude Code) renders each ghost as an HTML artifact with a storyteller and a flying ghost. A Hermes profile on open weights uses the Ethereum History MCP server, a skill and a cron to pick a ghost each day and render it. Wayback screenshots of the dapp are the add-on.

- Assessment, gaps, feature verdicts, partner analysis, the author's feedback round and the clock: [docs/ASSESSMENT.md](docs/ASSESSMENT.md).
- Scope: **2015-2023**. Three pickers: the Ethereum History archive (2015-2017, historian stories), DeFiHackLabs incidents plus a hand-written 2017-2020 catalog (bad ghosts), and random-block sampling through dRPC (friendly ghosts of any year). Ages are hard-fork eras decided from the block number.
- Delivery: a framework-free static gallery in `web/`, deployed to Vercel on every new story (CLI deploy from the cron) at **eth-ghosts.decentraminds.tech** (the domain is already on Vercel DNS). Hermes `ghosts` profile with the Ethereum History MCP server, one skill, one cron (Discord bot token and channel to be provided by the author; cron-only until then); the three sloth profiles get **parked**, not deleted (`hermes -p <name> gateway stop`); `rc-parts` is already parked.
- Partner categories: Gemma (core), Tiger Data (if cheap), ".tech Domain" (the author confirmed `decentraminds.tech` was claimed through Hacktoberfest; the gallery subdomain is the entry), ElevenLabs **after V1**. Browserbase, Sentry, Entire, TabPFN, Temporal, Auth0, SerpApi, MongoDB, Mastra, Copilot, Ultramarine, Arduino, DigitalOcean, Tinker, Backboard, Render are out.
- First altar ghost chosen by the author: StandardBounties `0x2af47a65da8cd66729b4209c22017d6a5c2d2400` (The Bounties Network, Gitcoin).
- Clock: freeze **Sat Oct 31 15:00 local**, publish Sat 22:00 local, hard deadline Sun Nov 1 01:59 local. Milestones M0-M5 in the assessment, section 6.6.
- Honest lines the post must carry: template designed with a closed model at build time, stories by Gemma at runtime; online data sources, local model; frontier-era vulnerability verdicts are "suspected" unless cataloged; 2018-2023 ghosts have no historian prose; Hermes deny rules are not a sandbox.

## Working conventions for this folder

- **Keep [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md) current** (root `AGENTS.md` rule 8). Its "may claim / must NOT claim" table is binding for the post.
- Never commit a `.env`; commit `.env.example`. Idea notes that are private go in `ideas/` (gitignored).
