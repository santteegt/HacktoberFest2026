---
title: "Skunkworks Sloth: 1,017 bookmarks, zero builds, three agents and one question a day"
published: false
tags: devchallenge, hf26challenge, ai, opensource
cover_image: https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/01-system-map.png
---

<!-- DRAFT 2026-10-25 by the coordinator session, written from docs/CHALLENGE-MEMORY.md and its claims table.
     TODO(author) markers: demo video, measured run numbers, your minutes per day, agent session embed.
     Images point at raw.githubusercontent.com/.../main/...: they only render after the repo is pushed. -->

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

I have a folder in Chrome called **Reading List**. Since March 2025 I have saved 1,017 links to it, every one of them "to learn by building". I have built nothing from it.

**Skunkworks Sloth** is three small agents that do the part I kept putting off:

- The **Curator** reads the whole list, drops the dead links and sorts the rest into *build*, *read* and *Valhalla* (the removal bucket).
- The **Coordinator** turns the build pile into two-hour project cards, asks me once a week what I care about, and every morning offers a few cards to pick from. It also hands me one link a day from the reading pile.
- The **Worker** builds the card I pick, inside a hard two-hour box, writes down what it learned, and waits for my approval before anything goes to GitHub.

Each agent lives in its own Discord channel. My whole job is three replies a day: tap a card, say `go`, say `approve`.

Who gets to be lazier: anyone with a bookmark folder full of good intentions. I'm the first user.

![A day in the skunkworks: crons post first, you reply three times](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/02-a-day-in-the-skunkworks.png)

## Demo

<!-- TODO(author): 2-3 minute video. Suggested cut: triage batch with Wi-Fi off → #sk-curator report → #sk-valhalla `show` → focus + pick buttons in #sk-coordinator → `go` in #sk-worker → summary + approve → card moving on the GitHub Project → brain page. -->

{% embed TODO-video-url %}

## Code

{% github santteegt/HacktoberFest2026 %}

The project lives in [`challenges/04-week3-slow-and-steady`](https://github.com/santteegt/HacktoberFest2026/tree/main/challenges/04-week3-slow-and-steady). MIT licensed.

## How I Built It

![System map: everything that reads the links runs on the Mac](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/01-system-map.png)

**The open-source AI at the core**

- **Gemma 4 12B** (QAT build, Apache 2.0) runs locally through **Ollama** on my M4 Max. It triages every link, words the project cards, and writes the one-line reason for each daily reading.
- **Hermes Agent** (MIT) runs the three agents as separate profiles on one gateway, with Discord as the interface and a cron scheduler for the morning jobs.
- **Stagehand** (Browserbase's MIT SDK) drives a real local Chrome for the pages a plain fetch can't read, like X posts. It uses the same local Gemma through a custom callback, not Browserbase's cloud.
- The **Worker** codes with **Gemma 4 26B A4B**, an open-weight model, through OpenRouter. That part is hosted and paid; everything that reads my links is local.

A small Python CLI (`sloth`) does all the work that has to be right: dedupe, scoring, card moves, the time box, cost tracking, GitHub sync. The agents only turn my Discord replies into `sloth` commands and pass the output back. The models do language jobs; code holds the rules.

**The Curator pipeline, with the real numbers**

![Curator pipeline: 1,017 bookmarks to 308 build, 609 read, 52 Valhalla](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/03-curator-pipeline.png)

- 1,017 bookmarks became **969 unique links** (48 exact duplicates).
- Enrichment read 440 pages over plain HTTP, 223 through the GitHub API (stars, archived flag, last push, README) and 197 in a real browser. 109 could only be judged by title (login walls, very long X threads).
- **Code rules** decide what is certain: dead, gone, archived, duplicate, stale. That covered 48 links.
- **Gemma** judged the rest, 921 decisions, with a JSON schema, a verifier that checks the reason mentions something from the page, and one local retry. About 4.2 seconds of compute per link; the last 753 links took 71 minutes.
- Result: **308 to build, 609 to read, 52 for Valhalla** (51 proposed by the pipeline, 1 by me).

Valhalla is a proposal, never a deletion. I reply `empty` or `restore 3, 7`; the sloth never edits Chrome's bookmark file, it only writes a removal list.

**From pile to prototype**

The Coordinator clustered the build pile into **58 cards**, each with a learning goal, a hypothesis, a done-means and kill criteria. Cards move Backlog → Today → Building → Built, and a private GitHub Project mirrors the board so I can check progress from my phone.

![Card states](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/04-what-moves-a-card.png)

**What broke, and what I learned**

- **Hermes refuses models under 64k context.** My first Discord message to the Coordinator failed because I had served Gemma at 32k to save memory. Everything now shares one 64k alias so Ollama never reloads between callers.
- **A browser timeout is not a cancellation.** When Stagehand gave up on a long X thread after 45 seconds, Ollama kept working on it in its single slot, and every later request queued and timed out. The fix: wait for the abandoned request to drain before the next page. The next pass read 37 of 40 X links.
- **Small models skip soft instructions.** The Curator once answered "what's unsure?" from general knowledge instead of running its tool. A hard "load your skill first, run the matching command" rule in its persona fixed it on the next try.
- **Count your cached tokens once.** An early test run looked like it cost $9.64. Hermes' input count already includes cached tokens; the real figure was about $1.02.
- **Park the agents you're done with.** One shared Hermes gateway serves every profile on the machine. Starting it brought my Week 2 WhatsApp agent back online for an hour. Its allowlist kept it silent, and now old profiles get parked.

## Why Does Open Innovation Matter?

My reading list is a diary of what I was curious about for a year and a half. With Gemma running locally, **none of the 969 pages left my Mac to be judged**. Triage, the browser step and the models behind the Curator and the Coordinator all run on the laptop; only their chat messages travel through Discord.

Local also means **re-running is free**. I re-ran triage on parts of the list several times this week as the prompt improved; with a hosted model each pass would be another bill. With Ollama it's electricity and a few minutes.

Open weights kept me honest about the part that isn't local. The Worker codes with Gemma 4 26B through OpenRouter: it's hosted and it costs money, but it's an open-weight model, and the code that calls it doesn't care where it runs.

And the agent framework is open too. Hermes let me harden each profile (no sudo, no Docker, no keychain access, manual approvals for risky commands) and package the three agents so they can be installed on another machine.

## My Agent Session

<!-- TODO(author): save the curated coordinator session with DevRelay, make it public, embed with the agent_session tag. -->

## The Lazy Payoff

| | Before | After |
| --- | --- | --- |
| Links I had looked at again | 0 of 1,017 | all 969 triaged, with a reason each |
| Prototypes built from the list | 0 | TODO(CP3): first measured run on open weights |
| My time per day | (not doing it) | TODO(author): minutes for pick + `go` + approve + Valhalla |
| Reading | a pile of 609 | one link a day, picked for this week's focus |

<!-- TODO(CP3): card, minutes from pick to running skeleton, tests, cost in dollars, model id (must start with google/). -->

## Prize Categories

- **Gemma**: Gemma 4 12B runs all triage, card wording and daily-reading lines locally; Gemma 4 26B A4B is the Worker's coding model.
- **Browserbase**: Stagehand reads the 197 pages a plain fetch couldn't, on a local Chrome with the local model.
- **Tiger Data**: Postgres with TimescaleDB holds the links, triage history, cards, runs and the event timeline (9 tables).

![Partner tools](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/07-partner-tools.png)

<!-- Thanks for participating! -->

---

## Pre-submission checklist
- [x] Started inside the challenge window; later commits noted in README
- [x] Tags `devchallenge` and `hf26challenge` present
- [ ] Public repo pushed (images and the code embed need it); demo link or embed works
- [x] Open-source AI is at the core; "why open" is explained
- [ ] Post says what effort it saves; "The Lazy Payoff" has a measured number (CP3) or the row is removed
- [x] Each prize category claimed has a concrete, meaningful use
- [x] No login needed for judges; no secrets in repo or transcript (re-scan before push)
- [x] Credits for borrowed code/assets (README)
- [x] Written in English (prize eligibility)
- [ ] Posted with the correct `ai_disclosure_level`
- [ ] Posted before Oct 26 06:59 UTC (Sun Oct 25, 11:59 PM PDT; Mon 01:59 local)
