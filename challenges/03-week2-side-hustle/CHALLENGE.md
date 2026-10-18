# Hacktoberfest Open-Source AI Challenge: Week 2 (Side Hustle): rules snapshot

- **DEV event ID:** 80 · **Page:** https://dev.to/challenges/hacktoberfest-week2-2026-10-12
- **Fetched:** 2026-10-12 (21:07 UTC) via `get_challenge_details` / `get_challenges` (`full_details`); submission template and partner category blurbs fetched from the challenge page the same day. Re-fetch before submitting.
- **Window (UTC):** Oct 12, 2026 19:00 (DEV Events API) → **Oct 19, 2026 06:59** (= Sun Oct 18, 11:59 PM PDT; Oct 19 1:59 AM at UTC-5, the author's local time)
- **Required tag:** `#hf26challenge` (the official template's front matter also adds `devchallenge`)
- **Winners:** announced the week of Oct 19
- **Discrepancies to watch:** `full_details` calls Week 2 "the second of five" challenges while the page says "Challenge 3 of 5" (the page is right; the weekend was the first). `full_details` lists ElevenLabs among the partners giving credits; the page lists Tinker, Render, Backboard and a free .tech domain, and points to `hacktoberfest.com/my/promos`. The start time was not in earlier snapshots (the registry only had "Oct 12"). The challenge page wins.

## Prompt and theme

**Theme: Side Hustle.** Build something with open-weight models or open-source AI that **someone would actually pay for**.

"Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or all three. The open pieces must be what makes the project work.

Think small, specific and useful: a real problem for a real person (a freelancer, a small business owner, a niche hobby community, a friend who keeps complaining about the same tedious task).

Example ideas from the prompt: a local invoice and receipt sorter for freelancers, so client data never leaves the laptop; a listing writer for Etsy or eBay sellers that turns product photos into a description; a menu translator for a local restaurant that handles its specific dishes better than a generic tool.

The post must say why open innovation matters for what was built: does running your own model keep costs low enough that the business works, keep customers' data private, allow fine-tuning for a niche a general API handles poorly, or avoid lock-in to someone else's pricing? Say where the open approach beat a closed one.

**Bonus points** for landing a first user: get it in front of someone, let them use it, and report how it went. Did they pay? Would they? What did they ask for next?

## Judging criteria

1. **Writing Quality** (weighted most heavily): is the post clear and engaging; does it explain what was built, who it's for, and why open innovation matters?
2. **Relevance to the Prompt and Theme:** is open-source AI or an open-weight model at the core; is it something someone would actually pay for?
3. **Creativity:** an original idea or a fresh take on a familiar problem.
4. **Technical Execution:** does it work, and is it well built?
5. **Use of Partner Technology** (optional): if entering a partner category, is that technology used in a meaningful way?

Saving the agent session with DevRelay and embedding or linking it in the post is optional but helps judges.

## Prizes and prize categories

$2,550 across 18 winners.

- Overall winner (1): $250 + DEV++ membership + exclusive DEV badge
- Featured category winners (6): $200 + badge each
- Partner category winners (11): $100 + badge each
- All valid submissions: completion badge on the DEV profile

One project can enter every category it genuinely uses; each participant can win once per challenge. Credits and promo codes are claimed at hacktoberfest.com/my/promos. Ask the user before claiming.

What each category asks for (from the challenge page, 2026-10-12):

| Category | Tier | What the page asks for |
| --- | --- | --- |
| Render | Featured $200 | Render as the project's AI runtime, host for an agent's front end, or to run Hermes or OpenClaw |
| TabPFN | Featured $200 | Forecast, predict, classify or spot anomalies from historical data like a CSV. TabPFN-3.5 recommended (key at platform.priorlabs.ai, free non-commercial license). Favors TabPFN inside a wider prediction agent, with or without the MCP server |
| Tinker | Featured $200 | Fine-tune a model for a specific task and show a clear improvement in performance, latency or cost over a baseline |
| Arduino | Featured $200 | Build with an Arduino UNO Q: run a model on the board, a physical agent that senses and acts, or optimize a model with Qualcomm AI Hub |
| DigitalOcean | Featured $200 | Host the app or agent, run an open-weight model on a GPU Droplet (1-Click Models), or build an agent on the Gradient AI Platform |
| Gemma | Featured $200 | Use Gemma in the project: run it locally, fine-tune it, or serve it through Google Cloud or another provider |
| Backboard | Partner $100 | Build with R-CLI, compare open-weight models through one Backboard API key, or give an assistant memory and RAG |
| ElevenLabs | Partner $100 | Give an open-source agent a voice, transcribe audio for a local model, or narrate the demo |
| Entire | Partner $100 | Share the agent sessions behind the project in the write-up, or search past agent work to explain why code exists |
| GitHub Copilot | Partner $100 | Build with Copilot's coding agent, CLI or app, automate with GitHub Actions, or review PRs with Copilot |
| Mastra | Partner $100 | Orchestrate an agent over open models, add memory and tools to a chat agent, or build a workflow |
| MongoDB Atlas | Partner $100 | Atlas as the data layer: Vector Search, long-term agent memory, or the app database |
| Sentry Agent Tracing | Partner $100 | Show the agent's setup, performance (latency, tokens, cost), findings and debugging, with traces or screenshots in the write-up |
| SerpApi | Partner $100 | Live web search for an agent, RAG grounded in fresh results, or news tracking |
| Temporal | Partner $100 | Wrap the agent in a Temporal workflow so it survives failures, retries tool calls and resumes |
| Tiger Data | Partner $100 | pgvector embeddings, hybrid keyword and vector search, or database management through Tiger MCP |
| **.tech Domain** (new this week) | Partner $100 | Put the project live on a .tech domain claimed through Hacktoberfest and link it in the write-up. Free first year, then renews at $29.99 a year |

## Required elements (license, demo, diagrams, IDs, credentials)

- New project built during the window; PRs to existing projects and old projects don't count. One entry per person.
- Post on DEV using the template below, with the tags `devchallenge` and `hf26challenge`.
- The post says what was built **and who would pay for it**, shows a demo, and explains why open innovation matters.
- Demo: deployed link or video. Code: public repo.
- Optional "My First User" section; this is where the bonus points are.
- Teams: one member publishes and lists teammates' DEV usernames in the body.
- Non-English entries aren't prize-eligible. Entrants must be 18+.
- No login-credentials requirement stated; if the demo needs a login, supply test credentials anyway.

## Official submission template (fetched from the challenge page)

```
---
title: 
published: 
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## What I Built
<!-- What does it do, and who would pay for it?  What problem does it solve for them? -->

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

## My First User
<!-- Optional, but this is where bonus points live.  Did someone use it?  Who were they, what did they say, and did they pay?  If not, remove this section. -->

## Prize Categories
<!-- Which partner categories are you entering?  List every one that applies, or remove this section. -->

<!-- Team Submissions: Please pick one member to publish the submission and credit teammates by listing their DEV usernames directly in the body of the post. -->

<!-- Thanks for participating! -->
```

## Verbatim `full_details`

The Hacktoberfest Open-Source AI Challenge: Week 2 runs October 12 to October 18. Build something with open-weight models or open-source AI that someone would actually pay for. $2,550 in prizes across 18 winners.

This year's Hacktoberfest is all about building brand-new projects with open-source AI and open-weight models. Week 2 is the second of five Hacktoberfest DEV Challenges. See all five challenges and every partner category on the HF26 DEV Challenge Hub: https://dev.to/challenges/hf26

This Week's Theme: Side Hustle

Build something with open-weight models or open-source AI that someone would actually pay for.

That can mean running an open-weight model, building on an open-source agent harness or framework, running inference locally, or all three. Whatever you pick, the open pieces should be what makes your project work.

Think small, specific, and useful. The best builds here solve a real problem for a real person, whether that's a freelancer, a small business owner, a niche hobby community, or your friend who keeps complaining about the same tedious task. A few ideas to get you going:

    An invoice and receipt sorter for freelancers that runs locally, so client data never leaves their laptop
    A listing writer for Etsy or eBay sellers that turns a few product photos into a polished description
    A menu translator for a local restaurant that handles their specific dishes better than a generic tool

In your post, tell us why open innovation matters for what you built. Does running your own model keep costs low enough that the business actually works? Keep your customers' data private? Let you fine-tune for a niche that a general-purpose API handles poorly? Avoid getting locked into someone else's pricing?

Bonus points if you land your first user. Get it in front of someone, let them use it, and tell us how it went. Did they pay? Would they? What did they ask for next?

Prize Categories

Alongside the overall winner, there are 17 prize categories for projects that use a specific partner's technology. You don't need to use any of these to win the overall prize.

Featured categories: Best Use of Render, Best Use of TabPFN, Best Use of Tinker, Best Use of Arduino, Best Use of DigitalOcean, Best Use of Gemma

Partner categories: Best Use of Backboard, Best Use of ElevenLabs, Best Use of Entire, Best Use of GitHub Copilot, Best Use of Mastra, Best Use of MongoDB Atlas, Best Use of Sentry Agent Tracing, Best Use of SerpApi, Best Use of Temporal, Best Use of Tiger Data, Best Use of a .tech Domain

One project can enter every category it genuinely uses, but each participant can only win once per challenge. Several partners are giving participants free credits and promo codes, including Tinker, Render, Backboard, and ElevenLabs. Claim yours at hacktoberfest.com/my.

Judging Criteria

    Writing Quality (weighted most heavily): Is the post clear and engaging? Does it explain what you built, who it's for, and why open innovation matters?
    Relevance to the Prompt and Theme: Is open-source AI or open-weight models at the core of the project? Is it something someone would actually pay for?
    Creativity: Is it an original idea, or a fresh take on a familiar problem?
    Technical Execution: Does it work, and is it well built?
    Use of Partner Technology (optional): If entering a partner category, does the project use that technology in a meaningful way?

Saving your agent session with DevRelay and embedding it in your post is optional, but it helps the judges understand your process.

Prizes 🏆

    Overall winner (1): $250 USD, a DEV++ membership, and an exclusive DEV badge
    Featured category winners (6): $200 USD and an exclusive DEV badge each
    Partner category winners (11): $100 USD and an exclusive DEV badge each

All participants with a valid submission will receive a completion badge on their DEV profile.

How To Participate

Publish a post on DEV using the Side Hustle submission template and be sure to include the required challenge tag: #hf26challenge. Tell us what you built and who would pay for it, show us a demo, and explain why open innovation matters for what you built.

Important Dates

    October 12: Hacktoberfest Open-Source AI Challenge: Week 2 begins!
    October 18: Submissions due at 11:59 PM PDT
    Week of October 19: Winners announced
