# Hacktoberfest Open-Source AI Challenge: Week 3 (Slow and Steady): rules snapshot

- **DEV event ID:** 81 · **Page:** https://dev.to/challenges/hacktoberfest-week3-2026-10-19
- **Fetched:** 2026-10-19 (20:42 UTC) via `get_challenge_details` (`full_details`); submission template and partner category blurbs fetched from the challenge page the same day. Re-fetch before submitting.
- **Window (UTC):** Oct 19, 2026 19:00 (DEV Events API) → **Oct 26, 2026 06:59** (= Sun Oct 25, 11:59 PM PDT; Oct 26 1:59 AM at UTC-5, the author's local time), per the challenge page
- **Required tags:** `#hf26challenge` and `devchallenge` (both in the official template's front matter)
- **Winners:** announced the week of Oct 26
- **Deadline discrepancy:** the DEV Events API `ends_at` is **Oct 25 06:59 UTC** (= Sat Oct 24, 11:59 PM PDT). `full_details`, the challenge page and the contest rules all say submissions are due **Oct 25, 11:59 PM PDT** (= **Oct 26 06:59 UTC**; Oct 26 1:59 AM at UTC-5, the author's local time). **We follow the challenge page** (author's decision, 2026-10-19).
- **Other notes:** the page calls this "Challenge 4 of 5". It now lists **20** partner categories (Week 2 had 17): **Auth0 for AI Agents**, **Browserbase** and **Ultramarine (Paper Instruments)** are new this week.

## Prompt and theme

**Theme: Slow and Steady.** Build something with open-weight models or open-source AI that **rewards laziness**. October 20 is International Sloth Day: "build something that does the work so you don't have to." It can help someone relax, automate a task they dread, or just make life a little easier.

"Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or all three. The open pieces must be what makes the project work.

Example ideas from the prompt: a local agent that reads group chats overnight and hands you a two-line morning summary; a wind-down companion that makes a calming bedtime story or ambient soundscape, fully offline; a fridge photo to grocery list tool; a file and inbox tidier that sorts, renames and archives clutter.

The post must say why open innovation matters for what was built: does running your own model mean the automation works offline, keeps personal messages and files on your own machine, or can be set up once and never paid for again? Say where the open approach beat a closed one.

**Bonus:** show the lazy payoff. How much time or effort does the project actually save? Did you (or someone else) use it this week? The template has an optional "The Lazy Payoff" section for this.

## Judging criteria

| Criterion | Note |
| --- | --- |
| Writing Quality | **Weighted most heavily** |
| Relevance to the Prompt and Theme | Open-source AI at the core; rewards laziness |
| Creativity | |
| Technical Execution | |
| Use of Partner Technology | Optional |

## Prizes and prize categories

$2,850 across 21 winners. Overall winner (1): $250 + DEV++ membership + exclusive badge. Featured category winners (6): $200 + badge. Partner category winners (14): $100 + badge. Every valid submission gets a completion badge. One project can enter every category it genuinely uses, but can win only once per challenge. You don't need any partner tech to win overall.

**Featured ($200 each)**

| Category | What it asks for (from the challenge page) |
| --- | --- |
| Render | Render as the AI runtime, to host an agent's front end, or to run Hermes or OpenClaw |
| TabPFN | Prior Labs' tabular foundation model to forecast, predict, classify or spot anomalies from historical data. TabPFN-3.5 recommended (open-weight, free after signing the non-commercial license at platform.priorlabs.ai, runs locally). Favors TabPFN inside a wider prediction agent |
| Tinker | Fine-tune a model for a specific task with Thinking Machines' Tinker and show a clear improvement in performance, latency or cost over a baseline |
| Arduino | Build with an Arduino UNO Q: run a model on the board, build a physical agent, or optimize a model with Qualcomm AI Hub |
| DigitalOcean | Build or deploy on DigitalOcean: host the app or agent, run an open-weight model on a GPU Droplet (1-Click Models), or build on the Gradient AI Platform |
| Gemma | Use Gemma: run it locally, fine-tune it, or serve it through Google Cloud or another provider |

**Partner ($100 each)**

| Category | What it asks for |
| --- | --- |
| Auth0 for AI Agents (new) | Sign users in to an agent, call tools on a user's behalf with Token Vault, ask a person to approve a risky action, or limit RAG retrieval with fine-grained authorization |
| Backboard | R-CLI (open-source terminal coding agent), compare open-weight models through one Backboard key, or give an OSS project's assistant memory and RAG |
| Browserbase (new) | Give the agent a real browser with Stagehand: drive a live site, pull context for an open-weight model, or make a one-off run a repeatable workflow |
| ElevenLabs | Give an open-source agent a voice, transcribe audio for a local model, or narrate the demo |
| Entire | Share the agent sessions behind the project, or search past agent work to explain why code exists |
| GitHub Copilot | Copilot coding agent, CLI or app, GitHub Actions automation, or Copilot PR review |
| Mastra | Orchestrate an agent over open models, add memory and tools to a chat agent, or triage GitHub issues |
| MongoDB Atlas | Atlas as the data layer: Vector Search, agent long-term memory, or the database behind the app |
| Sentry Agent Tracing | Show the agent's setup, performance (latency, tokens, cost), findings and debugging, with traces or screenshots in the write-up |
| SerpApi | Live web search for an agent, RAG grounded in fresh results, or news tracking |
| Temporal | Wrap the agent in a Temporal workflow so it survives failures, retries flaky tool calls and resumes |
| Tiger Data | pgvector embeddings, hybrid keyword + vector search, or let an agent manage a database through Tiger MCP |
| Ultramarine (Paper Instruments) (new) | Put Ultramarine to work on research, analysis, drafting or document reasoning via the OpenAI or Anthropic SDKs, and **say what the run cost**. $5 free credit at hacktoberfest.com/my/promos |
| .tech Domain | Put the project live on a .tech domain claimed through Hacktoberfest and link it in the post (free first year, renews at $29.99) |

Partner credits and promo codes (Tinker, Render, Backboard, a free .tech domain, Ultramarine $5): https://hacktoberfest.com/my/promos. **Ask the user before claiming any.** Category hub: https://dev.to/challenges/hf26

## Required elements (license, demo, diagrams, IDs, credentials)

- New project built during the window; PRs to existing projects and old projects don't count. One entry per person.
- Post on DEV using the template below, with the tags `devchallenge` and `hf26challenge`.
- The post says what was built **and what effort it saves**, shows a demo, and explains why open innovation matters.
- Demo: deployed link or video. Code: public repo (embeddable).
- Optional "My Agent Session" (DevRelay `agent_session` embed or link) and "The Lazy Payoff" sections; remove "The Lazy Payoff" if nobody used it this week.
- Teams: one member publishes and lists teammates' DEV usernames in the body.
- Non-English entries aren't prize-eligible. Entrants must be 18+.
- No login-credentials requirement stated; if the demo needs a login, supply test credentials anyway.

## Official submission template (fetched from the challenge page)

```markdown
---
title: 
published: 
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built
<!-- What does it do, and what effort does it save? Who gets to be a little lazier because of it? -->

## Demo
<!-- Share a deployed link or a video demo. -->

## Code
<!-- Show us the code!  You can embed a GitHub repo directly into your post. -->

## How I Built It
<!-- Which open-source AI did you use (open-weight models, agent harnesses, frameworks, local inference), and how is your project built around it? -->

## Why Does Open Innovation Matter?
<!-- Why does open innovation matter for what you built?  What did it make possible that a closed API wouldn't? -->

## My Agent Session
<!-- Optional, but judges love it.  Save your session with DevRelay and embed it with the agent_session tag (see the challenge page), or link to it. -->

## The Lazy Payoff
<!-- Optional, but this is where you can make your post stand out.  How much time or effort does it actually save?  Did you (or someone else) use it this week?  If not, remove this section. -->

## Prize Categories
<!-- Which partner categories are you entering?  List every one that applies, or remove this section. -->

<!-- Team Submissions: Please pick one member to publish the submission and credit teammates by listing their DEV usernames directly in the body of the post. -->

<!-- Thanks for participating! -->
```

## Verbatim `full_details`

The Hacktoberfest Open-Source AI Challenge: Week 3 runs October 19 to October 25. In honor of International Sloth Day, build something with open-source AI that rewards laziness: a tool for relaxation, an automation for a task you dread, or anything that makes life easier. $2,850 in prizes across 21 winners.

New to Hacktoberfest this year? Instead of pull requests, you build a brand-new project with open-source AI at its core and write about it on DEV. Every challenge is a fresh start, so it's never too late to join.

This week's theme: Slow and Steady

Build something with open-weight models or open-source AI that rewards laziness.

October 20 is International Sloth Day, and sloths have it figured out. They move at their own pace, conserve their energy, and let the world come to them. This week, channel your inner sloth and build something that does the work so you don't have to.

That can mean running an open-weight model, building on an open-source agent harness or framework, running inference locally, or all three. Whatever you pick, the open pieces should be what makes your project work.

A few ideas to get you going:

    A local agent that reads your group chats overnight and hands you a two-line summary in the morning
    A wind-down companion that generates a calming bedtime story or ambient soundscape, running entirely offline
    A fridge photo to grocery list tool, so you never have to stand there with the door open again
    A file and inbox tidier that quietly sorts, renames, and archives the clutter you keep putting off

In your post, tell us why open innovation matters for what you built. Bonus points for showing the lazy payoff: how much time or effort does your project actually save?

Prize Categories

Alongside our overall winner, there are 20 prize categories for projects that use a specific partner's technology. You don't need to use any of these to win the overall prize.

Featured categories ($200 each): Best Use of Render, Best Use of TabPFN, Best Use of Tinker, Best Use of Arduino, Best Use of DigitalOcean, Best Use of Gemma

Partner categories ($100 each): Best Use of Auth0 for AI Agents, Best Use of Backboard, Best Use of Browserbase, Best Use of ElevenLabs, Best Use of Entire, Best Use of GitHub Copilot, Best Use of Mastra, Best Use of MongoDB Atlas, Best Use of Sentry Agent Tracing, Best Use of SerpApi, Best Use of Temporal, Best Use of Tiger Data, Best Use of Ultramarine (Paper Instruments), Best Use of a .tech Domain

One project can enter every category it genuinely uses, but you can only win once per challenge. Full descriptions are on the HF26 DEV Challenge Hub: https://dev.to/challenges/hf26

Judging Criteria

    Writing Quality (weighted most heavily)
    Relevance to the Prompt and Theme
    Creativity
    Technical Execution
    Use of Partner Technology (optional)

Prizes 🏆

Overall winner (1) will receive:

    $250 USD
    DEV++ Membership
    Exclusive DEV Badge

Featured category winners (6) will each receive:

    $200 USD
    Exclusive DEV Badge

Partner category winners (14) will each receive:

    $100 USD
    Exclusive DEV Badge

All participants with a valid submission will receive a completion badge on their DEV profile.

How To Participate

Publish a post on DEV using the submission template on the challenge page and be sure to include the required challenge tag: #hf26challenge. Tell us what you built and what effort it saves, show us a demo, and explain why open innovation matters for what you built. You may submit one entry per challenge, and each submission must be a new project built during the challenge window.

Important Dates

    October 19: Hacktoberfest Open-Source AI Challenge: Week 3 begins!
    October 20: International Sloth Day 🦥
    October 25: Submissions due at 11:59 PM PDT
    Week of October 26: Winners Announced
