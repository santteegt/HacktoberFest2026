---
title: "Skunkworks Sloth: 1,017 bookmarks, zero builds, three agents and one question a day"
published: false
tags: devchallenge, hf26challenge, ai, opensource
cover_image: https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/01-system-map.png
---

<!-- DRAFT v2 2026-10-25, written from docs/CHALLENGE-MEMORY.md and its claims table.
     TODO(author): demo video, measured run numbers (CP3), minutes per day, agent session embed.
     Images point at raw.githubusercontent.com/.../main/...: they render only after the repo is pushed. -->

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

My Chrome holds **8,130 bookmarks**. One folder, **Reading List**, is the honest one: since March 2025 I have saved 1,017 links to it, every one of them "to learn by building". I have built nothing from it.

That folder is the prototype's test bed: 1,017 of 8,130 bookmarks, about 12.5% of the pile. The other 7,113 are next.

**Skunkworks Sloth** is three small agents that do the part I kept putting off:

- The **Curator** reads the whole list, drops the dead links and sorts the rest into *build*, *read* and *Valhalla* (the removal bucket).
- The **Coordinator** turns the build pile into two-hour project cards, asks me once a week what I care about, offers a few cards every morning, and hands me one link a day from the reading pile.
- The **Worker** builds the card I pick inside a hard two-hour box, writes down what it learned, and waits for my approval before anything reaches GitHub.

Each agent has its own Discord channel. My whole job is three replies a day: tap a card, say `go`, say `approve`.

Who gets to be lazier: anyone with a bookmark folder full of good intentions. I'm the first user.

## Demo

<!-- TODO(author): 2-3 minute video. Suggested cut: triage batch with Wi-Fi off → #sk-curator report → #sk-valhalla `show` → focus + pick buttons in #sk-coordinator → `go` in #sk-worker → summary + approve → card moving on the GitHub Project → today's reading and its brain page. -->

{% embed TODO-video-url %}

## Code

{% github santteegt/HacktoberFest2026 %}

The project lives in [`challenges/04-week3-slow-and-steady`](https://github.com/santteegt/HacktoberFest2026/tree/main/challenges/04-week3-slow-and-steady), MIT licensed. The three agents ship as Hermes profile distributions, so `scripts/install.sh` sets them up on another Hermes host in one step (or next to agents you already run).

## How I Built It

### The architecture in one picture

![System map](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/01-system-map.png)

The green zone is my laptop, and everything that reads my links lives there:

1. **Chrome's bookmark file** is the input. The Curator only ever reads it.
2. **`sloth`**, a small Python CLI, does everything that has to be right: dedupe, rules, scoring, card moves, the time box, cost tracking, GitHub sync. It has four parts: `curator`, `board`, `builder` and `core`.
3. **Ollama** serves **Gemma 4 12B** locally. `sloth` calls it for language jobs only: triage verdicts, card wording, the one-line "why read this today".
4. **Stagehand** drives a real local Chrome for pages a plain fetch can't read, and asks the same local Gemma what's on the page.
5. **Hermes Agent** runs the three agents as separate profiles behind one gateway. Each agent has a skill that maps my Discord replies to `sloth` commands and passes the output back. The gateway also runs the cron jobs that start each morning.

The blue zone is hosted: the Worker's coding models, Postgres on Tiger Data, and GitHub. The purple zone is Discord, where I talk to the agents.

The rule I kept all week: **models do language, code does rules.** No agent decides what gets deleted, built or pushed; it runs a command, and the command checks.

### A day in the skunkworks

![A day in the skunkworks](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/02-a-day-in-the-skunkworks.png)

Crons post first: at 07:00 the Curator triages anything new, at 08:00 the Coordinator posts today's reading, and at 09:00 it posts three or four cards weighted by my weekly focus. I tap one and say `go` in `#sk-worker`. The Worker builds for up to two hours, posts a summary with the test result and the cost, and waits. `approve N` pushes a private repo and moves the card to Built.

### The Curator pipeline, with real numbers

![Curator pipeline](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/03-curator-pipeline.png)

- 1,017 bookmarks became **969 unique links** (48 exact duplicates).
- Enrichment read 440 pages over plain HTTP, 223 through the GitHub API (stars, archived flag, last push, README) and 197 in a real browser. 109 could only be judged by their title: login walls and very long X threads.
- **Code rules** decide what is certain (dead, gone, archived, duplicate, stale): 48 links.
- **Gemma** judged the rest: 921 decisions, each with a JSON schema, a verifier that checks the reason mentions something from the page, and one local retry. About 4.2 seconds of compute per link; the last 753 links took 71 minutes.
- Result: **308 to build, 609 to read, 52 for Valhalla** (51 proposed by the pipeline, 1 by me).

Valhalla is a proposal, never a deletion. I reply `empty` or `restore 3, 7`, and the sloth writes a removal list. It never edits Chrome's bookmark file.

### What moves a card

![Card states](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/04-what-moves-a-card.png)

The Coordinator clustered the build pile into **58 cards**, each with a learning goal, a hypothesis, a done-means and kill criteria. Every arrow except the box timeout is one of my replies. A run that finishes waits in Building until I approve it, and a box that ends without meeting its done-means is Killed, with honest notes.

### Agents, skills and schedules

![Agents, skills and schedules](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/05-agents-skills-and-schedules.png)

Each agent is a Hermes profile with one job: its own model, skills, crons and channel. Deny rules block `sudo`, Docker and keychain commands, risky commands need my approval, and computer use is off. That's a command policy, not a sandbox: the agents still run as my user.

The Worker has **two providers**. By default it codes with **Gemma 4 26B A4B**, an open-weight model, through OpenRouter. When a card needs more, I say `go deep` and the same box runs on **Anthropic Claude Sonnet 5.5**. Every message about those runs says "(closed model)", and the cost is tracked either way.

### What gets stored

![What gets stored](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/06-what-gets-stored.png)

`links` is the hub. Triage keeps its history (1,098 rows for 969 links), so a page the browser reads later can change its verdict. `events` mirrors the `#sk-logs` channel, which is where every number in this post comes from.

### How each partner tool fits

![Partner tools](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/04-week3-slow-and-steady/docs/diagrams/png/07-partner-tools.png)

**Gemma**
- *What:* Gemma 4 12B (QAT, Apache 2.0) through Ollama on my M4 Max, plus Gemma 4 26B A4B through OpenRouter as the Worker's default coder.
- *Why:* the reading list is private and long. A local model can read all of it for the cost of electricity, and I can re-run it whenever the prompt improves.
- *How:* one Ollama alias with a 64k context, shared by every caller so the model never reloads. Ollama's JSON-schema mode keeps output valid, and since the model never sees the schema, the prompt spells out every field and allowed value. A verifier and a local retry catch the rest.

**Browserbase (Stagehand)**
- *What:* Stagehand's Python SDK drives a visible local Chrome. Browserbase's cloud isn't used.
- *Why:* 137 links were on hosts a plain HTTP fetch can't read, X above all. Without a browser, those links get judged by title only.
- *How:* `extract()` with a custom LLM callback pointed at the local Gemma, one browser session per batch, and a drain step after every timeout (see below). It read 197 pages, including 37 of 40 X posts in its last pass.

**Tiger Data**
- *What:* Postgres with TimescaleDB on Tiger Cloud's free tier: 9 tables.
- *Why:* three agents, crons and the GitHub sync all need one place that holds the truth. Plain SQL made every number in this post a query.
- *How:* an idempotent schema applied with `sloth apply-schema`, triage history kept as rows, and a partial unique index for "one main reading per day".

### What broke, and what I learned

- **Hermes refuses models under 64k context.** My first Discord message to the Coordinator failed because I had served Gemma at 32k to save memory.
- **A browser timeout is not a cancellation.** When Stagehand gave up on a long X thread after 45 seconds, Ollama kept working on it in its single slot, and every later request queued and timed out. Waiting for the abandoned request to drain fixed it.
- **Small models skip soft instructions.** The Curator once answered "what's unsure?" from general knowledge instead of running its tool. A hard "load your skill first, run the matching command" rule in its persona fixed it on the next try.
- **Count cached tokens once.** An early test run looked like $9.64. Hermes' input count already includes cached tokens; the real figure was about $1.02.
- **Park the agents you're done with.** One Hermes gateway serves every profile on the machine. Starting it brought my Week 2 WhatsApp agent back online for an hour; its allowlist kept it silent.
- **Crons don't have your keychain.** A morning job failed because the database password sat in the macOS keychain, which a locked session can't open.

## Why Does Open Innovation Matter?

My reading list is a diary of what I was curious about for a year and a half. With Gemma running locally, **none of the 969 pages left my Mac to be judged**. Triage, the browser step and the models behind the Curator and the Coordinator all run on the laptop; only their chat messages travel through Discord.

Local also means **re-running is free**. I re-ran triage on parts of the list several times this week as the prompt improved. With a hosted model each pass would be another bill; with Ollama it's electricity and a few minutes.

Open weights keep the Worker honest. Its default coder is Gemma 4 26B: hosted on OpenRouter and paid per run, but an open-weight model I could move home. When I choose `go deep`, I trade that for a stronger closed model, and the run says so.

The harness is open too. Hermes let me harden each profile and package all three agents as distributions, so the setup is `scripts/install.sh` on any other Hermes host instead of a page of instructions.

## My Agent Session

<!-- TODO(author): save the curated coordinator session with DevRelay, make it public, embed with the agent_session tag. -->

## The Lazy Payoff

| | Before | After |
| --- | --- | --- |
| Bookmarks waiting | 8,130 in Chrome, 1,017 of them in the Reading List | the Reading List fully triaged: 969 links, a reason each; 7,113 bookmarks still to go |
| Prototypes built from the list | 0 | 1 on open weights, approved and pushed (plus 1 labelled closed-model test) |
| From "what should I build?" to a tested repo | never happened | about 20 minutes: pick, `go`, a 4.9-minute build, `approve` |
| Cost of that build | n/a | $0.11 on Gemma 4 26B A4B (OpenRouter) |
| My time per day | (not doing it) | TODO(author): minutes for pick + `go` + approve + Valhalla |
| Reading | a pile of 609 | one link a day, picked for this week's focus |

The first open-weights build was the card I picked on Sunday evening, **Private Aztec Sandbox Smart Contract**. The Worker wrote a Noir counter contract with private state, two tests and a demo in 4.9 minutes. My first look said it failed: the runner checked `make test` without the Aztec toolchain on its PATH. With the same PATH the Worker had, both tests passed. They run in Aztec's test environment (TXE), not against a live Sandbox node, which is less than the Worker's own notes claimed. That gap is why the runner checks every build itself instead of trusting the agent's report.

## Future Work

My saved links don't only live in Chrome. The next sources are the bookmark piles on X and Facebook, flowing into the same `links` table (it already has a `source` column), so everything downstream stays the same.

- **X bookmarks.** The official route is the X API v2 bookmarks endpoint (`GET /2/users/:id/bookmarks`, OAuth 2.0 with the `bookmark.read` scope, the 800 most recent). The fallback needs nothing new: Stagehand already reads X posts, so it can scroll `x.com/i/bookmarks` in my own logged-in local Chrome and extract each post.
- **Facebook saved posts.** There is no API for saved items. One path is Facebook's own data export (Accounts Center → Download your information, JSON). The other is Stagehand on `facebook.com/saved` in the local browser.

Either way, the browser stays on my machine, the model stays local, and the agents don't change.

## Prize Categories

- **Gemma**: Gemma 4 12B runs all triage, card wording and daily-reading lines locally; Gemma 4 26B A4B is the Worker's default coding model.
- **Browserbase**: Stagehand reads the 197 pages a plain fetch couldn't, on a local Chrome with the local model.
- **Tiger Data**: Postgres with TimescaleDB holds the links, triage history, cards, runs, readings and the event timeline (9 tables).

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
