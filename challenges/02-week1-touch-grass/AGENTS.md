# AGENTS.md: Week 1 Challenge "Touch Grass"

Challenge-specific instructions. They add to the repo-level `../../AGENTS.md`, which still applies. `CLAUDE.md` here is a symlink to this file.

- **DEV event:** 79 · **Page:** https://dev.to/challenges/hacktoberfest-week1-2026-10-05
- **Window (UTC):** Oct 5, 2026 18:00 (DEV API; sources disagree, see [CHALLENGE.md](CHALLENGE.md)) → **Oct 12, 2026 06:59** (= Sun Oct 11, 11:59 PM PDT; Oct 12 1:59 AM at UTC-5, the author's local time)
- **Required tag:** `#hf26challenge` (the official template's front matter also lists `devchallenge`)
- **Winners:** announced the week of Oct 12
- Full rules snapshot and official template: [CHALLENGE.md](CHALLENGE.md) · Post draft: [SUBMISSION.md](SUBMISSION.md) · Memory: [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md)

Re-fetch live details with `get_challenge_details` (id 79) if anything below looks stale. The challenge page wins over this file.

## The brief

Theme: **Touch Grass.** Build something with **open-source AI at its core** that gets people **off the screen and into the world**. "Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or a combination. The open pieces must be what makes the project work. Anything that gets someone outside counts (hiking, gardening, birding, run clubs, fall foliage); the best builds make the screen the shortest part of the experience.

Hard requirements:
1. **New project, started inside the window.** It must not reuse the weekend project (`../01-weekend-build-for-a-friend`). Note any commits after the deadline in the README.
2. **Open-source AI is the core**, not decoration around a closed API.
3. **The post explains why open matters** (offline in the backcountry, location data off third-party servers, swappable or fine-tunable models, zero running cost, where it beat a closed approach).
4. One submission per person. Teams: one member publishes and lists teammates' DEV usernames in the body.
5. Written in English (non-English entries are not prize-eligible).

**Bonus:** take it outside, use it, and report how it went. Plan an outdoor test and record it; log results in the challenge memory with date, device and method.

## Judging (use this to prioritize effort)

| Criterion | Weight / note |
| --- | --- |
| **Writing Quality** | **Weighted most heavily** |
| Relevance to prompt and theme | Open-source AI at the core; the screen is the shortest part of the experience |
| Creativity | Original idea or fresh take |
| Technical Execution | It works and is well built |
| Use of partner technology | Optional; only if entering a category, and it must be meaningful |

Budget at least a quarter of the time for the post, the demo, and the README. Follow [the playbook](../../knowledge-base/hacktoberfest-2026/wiki/challenge-playbook.md): get the target hardware and test the smallest candidate model on day one, keep the model's job tiny, freeze features about three hours before the deadline, record the demo on the real device.

## Prizes ($2,450, 17 winners)

Overall $250 + DEV++ + badge; 6 featured categories $200 + badge; 10 categories $100 + badge; every valid submission gets a completion badge. One win per participant, but one project may enter every category it genuinely uses.

| Tier | Partners |
| --- | --- |
| Featured ($200) | **Render** · **TabPFN** · **Tinker** · **Arduino** · **DigitalOcean** · **Gemma** |
| Standard ($100) | **Backboard** · **ElevenLabs** · **Entire** · **GitHub Copilot** · **Mastra** · **MongoDB Atlas** · **SerpApi** · **Sentry Agent Tracing** · **Temporal** · **Tiger Data** |

Credits and promo codes (Tinker, Render, Backboard, ElevenLabs) are at https://hacktoberfest.com/my. **Ask the user before claiming any code.** Use `devrelay-sponsor-skills` for current partner API usage and **ask before installing** any skill it returns. Partner notes live in the knowledge base (`wiki/partner-tools-catalog.md` and the per-partner pages).

## How to submit

1. Build in this folder (code, `LICENSE`, `.env.example`, `README.md`).
2. Fill `SUBMISSION.md` using the official template (verbatim in [CHALLENGE.md](CHALLENGE.md)). Keep every heading.
3. Optional but encouraged: save the agent session with DevRelay (`devrelay-sessions`), make it **public**, scrub keys first, embed it in "My Agent Session".
4. Stage with `create_article` (`published: false`; leave `ai_disclosure_level` at the default). Give the user the draft link.
5. **Publish only after the user explicitly says yes in the current session**, before the deadline. After it's live, update `../README.md`, `../../README.md` and `../../STICKERS.md`, then add a retrospective to the knowledge base `raw/` and run `/okf-wiki`.

## Chosen project: Idea Leash v2

Decided 2026-10-07. The author walks the dog in the morning and does a dark 19:30 fast walk, in Cuenca, Ecuador (Parque de los Eucaliptos), and wants walks that are rewarded, that capture ideas by voice, and that turn podcast listening into learning.

**Loop**
1. **Before a night walk:** give the agent a podcast episode link. The Mac fetches the audio, transcribes it locally, extracts main ideas, definitions, facts and insights into the second-brain wiki (OKF format), and prepares a 5-question quiz.
2. **During the walk:** an offline-first PWA records the walk (distance, path as GPX for OSM). Ideas are captured by voice on the phone (tap and talk, or a Telegram voice note that waits until the phone is online). The author listens to the podcast in their own player.
3. **After the walk:** the agent quizzes the author, scores exercise time and correct answers, and stores everything as a session.
4. **Dog walks:** a walking-only session with no podcast; voice ideas still captured.
5. **Gamification:** achievements and medals for kilometers, time with the dog, and knowledge, computed by rules in code.
6. **Ambient agent (when online):** surfaces items from the second brain to prompt review and project ideas (notify, question, review).

**Rules for this project**
- The phone only captures (voice, GPS, taps). All AI work runs on the author's Mac (M4 Max, 64 GB) with open models served by Ollama; the author's earlier weekend project may not be reused as code.
- The model's jobs are language jobs (summaries, quiz questions, grading wording, follow-up prompts). Points, medals, distances, streaks, scheduling and file layout are plain code. Quiz questions and graded answers must cite transcript text; code checks the citation exists.
- Do not claim anything not tested on a real phone and a real walk. Do not claim partner technologies the code does not use.
- Phone-side constraints, tested on 2026-10-09 (details in docs/CHALLENGE-MEMORY.md): **a web page gets no GPS fixes while it is hidden** (screen off or another app in front), so the app keeps the screen on behind a black cover; screen-on tracking was reliable (4 to 5 m median accuracy, no gap over 5 s in two walks); a one-time location permission is lost when the page is backgrounded; voice clips were stored offline on the phone (7 clips across the four walks). The queued upload and the walk-resume logic were tested only in a desktop browser with fake GPS and microphone, not yet on the phone. The app is served by the tool server over Tailscale HTTPS.

## Working conventions for this folder

- **Keep [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md) current** (root `AGENTS.md` rule 8). Its "may claim / must NOT claim" table is binding for the post.
- Source goes in `src/` (or the framework's convention), not the folder root.
- **Skills** live in `skills/<name>/` in this folder (source of truth). Install them where an agent looks with `scripts/install-skills.sh --target agents` (relative symlink into `<repo>/.agents/skills`) or `--target hermes [--profile NAME]` (copy into that Hermes home's `skills/`). This overrides the repo-level rule that skills live only in `.agents/skills`, because they belong to this project.
- **The Hermes agent** (profile, SOUL, config, cron, MCP, setup script and instructions) will live in `agent/`, designed as a Hermes *profile* (see https://hermes-agent.nousresearch.com/docs/user-guide/profiles) that one script can set up on any Hermes instance. Written and deployed to the Lume VM; how to run the stack is in `ops/README.md`.
- Run the `hf26-challenge` skill's **audit** step before drafting the post.
- Write plainly and concretely; run the `humanizer` skill on the draft.
- Do not claim a partner technology the code doesn't actually use.

## Status

- [x] Folder scaffolded (2026-10-06 04:37 UTC, inside the window)
- [x] Idea chosen: Idea Leash v2 (decided 2026-10-07)
- [x] Open-source AI core chosen and tested on the target device (Gemma 4 12B on Ollama, Hermes, whisper.cpp; M4 Max)
- [x] Prize categories chosen: Gemma and SerpApi only
- [x] MVP working (ingest, quiz in Telegram, walk app, offline queue, after-walk message, voice search)
- [x] Outdoor tests done and logged (4 test walks, a 35 minute walk, an offline dog walk)
- [x] Demo recorded and published by the author: https://youtu.be/ikb7P_XMQAw (3 min 59 s)
- [x] README, LICENSE, `.env.example` done; audit run on 2026-10-10 (see memory); re-run after the last test walk
- [x] Podcast walk and quiz done (2026-10-10), work committed and pushed to `main` (2026-10-11)
- [x] DEV draft written and staged (article id 4835517, 2026-10-11)
- [x] Published by the author before the deadline: 2026-10-11 23:30 local (2026-10-12T04:30:20Z), https://dev.to/santteegt/idea-leash-an-open-source-walk-buddy-with-a-local-model-for-a-brain-499n
