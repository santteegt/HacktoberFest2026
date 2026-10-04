# AGENTS.md: Weekend Challenge "Build for a Friend"

Challenge-specific instructions. They add to the repo-level `../../AGENTS.md`, which still applies. `CLAUDE.md` here is a symlink to this file.

- **DEV event:** 78 · **Page:** https://dev.to/challenges/hacktoberfest-weekend-2026-10-01
- **Launch post (questions go here):** https://dev.to/devteam/join-the-hacktoberfest-weekend-challenge-build-for-a-friend-2450-in-prizes-across-17-winners-1aj5
- **Window (UTC):** Oct 2, 2026 02:00 → **Oct 5, 2026 06:59** (= Sun Oct 4, 11:59 PM PDT; Oct 5 2:59 AM EDT; Oct 5 8:59 AM CEST)
- **Required tag:** `#hf26challenge` (the official template's front matter also lists `devchallenge, weekendchallenge`)
- **Winners:** announced the week of Oct 5
- Full rules snapshot: [CHALLENGE.md](CHALLENGE.md) · Post draft: [SUBMISSION.md](SUBMISSION.md) · Partner analysis: [PARTNER-REPORT.md](PARTNER-REPORT.md) · Idea research: `ideas/` (local only, gitignored)

Re-fetch live details with `get_challenge_details` (id 78) if anything below looks stale. The challenge page wins over this file.

## The brief

Build something with **open-source AI at its core** that solves a **real problem for one real friend or loved one**. "Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or a combination. The open pieces must be what makes the project work.

Theme: *Build for a Friend.* Pick one real person. It doesn't have to be big, but it has to matter to them. Bonus points for actually handing it over and reporting what they said.

Hard requirements:
1. **New project, started inside the window.** Note any commits after the deadline in the README.
2. **Open-source AI is the core**, not decoration around a closed API.
3. **The post explains why open matters:** offline use, data staying off servers you don't control, fine-tuning or swapping models, zero running cost, or where it beat a closed approach.
4. One submission per person. Teams up to four: one member publishes and lists teammates' DEV usernames in the post body.
5. Written in English (non-English entries are not prize-eligible).

## Chosen project: RC Pit Companion

Decided 2026-10-04. Project code lives in this folder (`src/`, `data/`, `kb/`); see [README.md](README.md). Idea research is in `ideas/` on the author's machine only (gitignored).

**The friend (persona):** races a 1/10 touring car, a Yokomo BD12, and goes to practice sessions. He wants practices to be worth the effort: tell the agent how the car feels, get setup recommendations, and **store the best setups together with track conditions** so he can retrieve what worked when a championship race comes. He prefers his **phone**, but the on-device phone test failed (`docs/PHONE-SPIKE.md`), so v1 runs on his consumer laptop: a **2019 MacBook Pro, Intel Core i7 (6-core, 2.6 GHz), 16 GB RAM, AMD Radeon Pro 5300M 4 GB + Intel UHD 630**. Ollama's docs only promise CPU inference on Intel Macs (macOS 14+ required), so plan for CPU-only; latency is the main constraint. Benchmarks on his machine are deferred until he is reachable.

**His stated need (paraphrase of his words, full quote in `docs/CHALLENGE-MEMORY.md`):** quickly store his settings on practice days and get feedback on what works and what might have affected his run. The setup vault and run-feedback are as central as the symptom coach.

**Requirements derived from the persona**
1. Laptop-first PWA (large touch/click targets, usable in a pit area); voice in/out so hands stay free. Phone is out of scope for v1.
2. Coach: symptom from the driver's words, then one change at a time with expected effect and how to verify.
3. Setup vault: sessions, change log with outcomes, saved setups with track conditions, retrievable by similar conditions.
4. Works offline once set up. Claim only what was tested, on which device.
5. Open model served by a local **Ollama** install on the laptop (Gemma 4 E2B QAT is the likely choice for the Intel MacBook; E4B QAT on Apple Silicon; decide from a measurement on his machine), behind `src/llm/provider.ts`. Use Ollama's JSON-schema `format` for structured output. Agent framework (Mastra or plain) and the local store are still to decide.

**Hard rules for this project**
- **New work only.** Code is written in the window. Knowledge comes from a frozen, credited snapshot of the author's earlier notes, imported in its own commit (`kb/PROVENANCE.md`). Do **not** reuse the author's earlier 3D dynamics-guide app, its BD12 model, or its setup-sheet app. Do not edit the snapshot; put corrections in new files.
- **Latency budget (CPU-only laptop).** Keep prompts tiny and stable, set `num_ctx` to 4096, stream tokens to the UI and speech, and call the model only for the two language steps. Everything else (lever lookup, clamping, logging, vault queries) must be plain code. Never put more than a couple of retrieved chunks in a prompt.
- **The model never invents numbers.** It maps speech to a symptom id and phrases explanations. Values come from `data/levers.json`, which the author reviews row by row. Every answer cites a valid chunk id; unsupported topics get a canned refusal.
- **Decided:** laptop-only for v1 after the phone spike (`docs/PHONE-SPIKE.md`). Do not re-open the phone path unless the user asks.
- Do not claim phone support, offline voice, or any partner technology that was not actually tested or used.

## Judging (use this to prioritize effort)

| Criterion | Weight / note |
| --- | --- |
| **Writing Quality** | **Weighted most heavily.** Clear and engaging; says what you built, who it's for, why open matters |
| Relevance to prompt and theme | Is open-source AI at the core? Does it fit "Build for a Friend"? |
| Creativity | Original idea or fresh take on a familiar problem |
| Technical Execution | It works and is well built |
| Use of partner technology | Optional; only if entering a category, and it must be meaningful |

Budget at least a quarter of the remaining time for the post, the demo, and the README.

## Prizes ($2,450, 17 winners)

- Overall winner: $250 + DEV++ membership + badge
- 6 featured categories: $200 + badge each
- 10 categories: $100 + badge each
- Every valid submission: completion badge. A participant can win only once, but one project may qualify for several categories.

### Partner list (prize categories)

| Tier | Partners |
| --- | --- |
| Featured ($200) | **Render** · **TabPFN** (Prior Labs) · **Tinker** (Thinking Machines) · **Arduino** · **DigitalOcean** · **Gemma** |
| Standard ($100) | **Backboard** · **ElevenLabs** · **Entire** · **GitHub Copilot** · **Mastra** · **MongoDB Atlas** · **SerpApi** · **Sentry Agent Tracing** · **Temporal** · **Tiger Data** |

Free credits and promo codes (Tinker, Render, Backboard, ElevenLabs confirmed) are at https://hacktoberfest.com/my/promos/ and require login. **Ask the user before claiming any code** (claims consume inventory). Use the `devrelay-sponsor-skills` skill for current partner API usage, and **ask before installing** any skill it returns.

Enter only categories the project **meaningfully** uses; list each in the post's "Prize Categories" section.

## How to submit

1. Build in this folder (code, `LICENSE`, `.env.example`, `README.md` using `../_template/README.md`).
2. Fill `SUBMISSION.md` using the official template below. Keep every heading.
3. Optional but encouraged: save the agent session with DevRelay (`devrelay-sessions`), make it **public** (uploads are unlisted by default), scrub keys first, and embed it in "My Agent Session".
4. Stage with `create_article` (`published: false`; leave `ai_disclosure_level` at the default). Give the user the draft link.
5. **Publish only after the user explicitly says yes in the current session**, and before the deadline above. After it's live, update `../README.md`, `../../README.md`, and `../../STICKERS.md`.

### Official submission template (verbatim from the challenge page)

```
---
title: 
published: 
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend]*

## What I Built
<!-- What does it do, and who is the friend or loved one you built it for? What problem does it solve for them? -->

## Demo
<!-- Share a deployed link or a video demo. -->

## Code
<!-- Show us the code! You can embed a GitHub repo directly into your post. -->

## How I Built It
<!-- Which open-source AI did you use (open-weight models, agent harnesses, frameworks, local inference), and how is your project built around it? -->

## Why Does Open Innovation Matter?
<!-- Why does open innovation matter for what you built? What did it make possible that a closed API wouldn't? -->

## My Agent Session
<!-- Optional, but judges love it. Save your session with DevRelay and embed it with the agent_session tag, or link to it. -->

## Prize Categories
<!-- Which partner categories are you entering? List every one that applies, or remove this section. -->

<!-- Team Submissions: Please pick one member to publish and credit teammates by listing their DEV usernames directly in the body of the post. -->

<!-- Thanks for participating! -->
```

(In the first line, link the challenge title to the challenge page.)

## Working conventions for this folder

- **Keep [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md) current** (root `AGENTS.md` rule 8). Log decisions, findings, measurements, failures and honest limits as they happen. The final report and post are written from it, and its "may claim / must NOT claim" table is binding.

- The project lives here. Put source in `src/` (or the framework's convention), not in the repo root.
- Run the `hf26-challenge` skill's **audit** step before drafting the post.
- Write the post in plain, concrete language: name the friend's problem, show one real moment of use, and give honest numbers (latency, model size, memory, cost). Run the `humanizer` skill on the draft if it's available.
- Do not claim a partner technology the code doesn't actually use.
- Record reusable lessons (what worked, tool gotchas) as a markdown file in `../../knowledge-base/hacktoberfest-2026/raw/` and run `/okf-wiki`.
- Read `PARTNER-REPORT.md` and the knowledge base's `wiki/index.md` before brainstorming. Don't redo partner research the report already covers.

## Status

- [x] Friend and problem chosen (RC Pit Companion, see above)
- [ ] Open-source AI core chosen (model / framework / where it runs)
- [ ] Prize categories chosen (and credits claimed, with the user's OK)
- [ ] MVP working
- [ ] Demo recorded or deployed
- [ ] README, LICENSE, `.env.example` done; audit passed
- [ ] DEV draft staged
- [ ] Published by the user before the deadline
