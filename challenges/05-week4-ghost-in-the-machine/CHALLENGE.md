# Hacktoberfest Open-Source AI Challenge: Week 4 (Ghost in the Machine): rules snapshot

- **DEV event ID:** 82 · **Page:** https://dev.to/challenges/hacktoberfest-week4-2026-10-26
- **Fetched:** 2026-10-26 (22:40 UTC) via `get_challenge_details` (`full_details`); submission template, partner category blurbs and contest-rules line fetched from the challenge page the same day. Re-fetch before submitting.
- **Window (UTC):** Oct 26, 2026 19:00 (DEV Events API) → **Nov 1, 2026 06:59** (= Sat Oct 31, 11:59 PM PDT; Nov 1 1:59 AM at UTC-5, the author's local time), per the challenge page and contest rules
- **Required tags:** `#hf26challenge` and `devchallenge` (both in the official template's front matter)
- **Winners:** announced the week of Nov 2
- **Deadline discrepancy (same pattern as Week 3):** the DEV Events API `ends_at` is **Oct 31 06:59 UTC** (= Fri Oct 30, 11:59 PM PDT). `full_details`, the challenge page and the contest rules ("Contest entry period ends October 31, 2026 at 11:59 PM PDT") all say **Oct 31, 11:59 PM PDT** (= **Nov 1 06:59 UTC**). **We follow the challenge page**: the author confirmed Nov 1 06:59 UTC (Sun Nov 1 01:59 local) as the deadline on 2026-10-29, consistent with the Week 3 decision. Publish target Sat Oct 31 22:00 local.
- **Other notes:** the page calls this "Challenge 5 of 5", the final one of the series. Same 20 partner categories as Week 3 (nothing marked new). Entrants must be 18+ (contest rules). Winners may be asked for an affidavit of eligibility and tax information within 7 business days.

## Prompt and theme

**Theme: Ghost in the Machine.** Build something **spooky**, or something that **honors the past in the spirit of Día de los Muertos**, with open-weight models or open-source AI. Halloween is Oct 31 and Día de los Muertos is Nov 1-2: "a stretch of the calendar when the line between past and present feels a little thinner." Things that go bump in the night, ofrendas with marigolds and candlelight, or the memories and stories we carry with us all qualify. The theme is intentionally broad.

"Open-source AI" means an open-weight model, an open-source agent harness or framework, local inference, or all three. The open pieces must be what makes the project work.

Example ideas from the prompt:
- A haunted terminal that "possesses" your shell and whispers eerie commentary on the commands you run
- A digital ofrenda builder that helps you write a remembrance for a loved one and gather their favorite foods, songs and stories
- An offline séance chatbot that channels the spirit of a long-dead programming language
- A local oral history tool that records and transcribes family stories so they're never lost
- A ghost story generator that weaves your smart home's sensor logs into a creepy tale of what happened while you were asleep
- A project that brings an abandoned open-source tool or a forgotten corner of internet history back to life

The post must say why open innovation matters for what was built: does running your own model mean it works with the lights (and the internet) off? Keep family photos and stories private and on your own machine? Make sure it isn't locked inside a service that might disappear someday? Say where the open approach beat a closed one.

**Bonus (template section "The Spirit of It"):** show the moment it landed. Did it give someone chills, bring back a memory, or keep a story alive? Remove the section if there is no such moment.

## Judging criteria

| Criterion | Note |
| --- | --- |
| Writing Quality | **Weighted most heavily** ("This is DEV, so your write-up matters most") |
| Relevance to the Prompt and Theme | Open-source AI at the core; spooky or honoring the past |
| Creativity | |
| Technical Execution | |
| Use of Partner Technology | Optional, for prize category entries |

Saving the agent session with DevRelay and embedding it is optional but "helps the judges understand your process."

## Prizes and prize categories

$2,850 across 21 winners. Overall winner (1): $250 + DEV++ membership + exclusive badge. Featured category winners (6): $200 + badge. Partner category winners (14): $100 + badge. Every valid submission gets a completion badge. One project can enter every category it genuinely uses, but can win only once per challenge. You don't need any partner tech to win overall.

**Featured ($200 each)**

| Category | What it asks for (from the challenge page) |
| --- | --- |
| Render | Render as the project's AI runtime, to host an agent's front end, or to run Hermes or OpenClaw |
| TabPFN | Prior Labs' tabular foundation model to forecast, predict, classify or spot anomalies from historical data like a CSV. TabPFN-3.5 strongly recommended (open-weight, free after signing the non-commercial license at platform.priorlabs.ai, runs locally; the API adds Thinking Mode). Favors TabPFN inside a wider prediction agent, with or without the MCP server |
| Tinker | Fine-tune a model for a specific task with Thinking Machines' Tinker and show a clear improvement in performance, latency or cost over a baseline |
| Arduino | Build with an Arduino UNO Q: run a model on the board, build a physical agent that senses and acts, or optimize a model for it with Qualcomm AI Hub. Open to anyone with an UNO Q |
| DigitalOcean | Build or deploy on DigitalOcean: host the app or agent, run an open-weight model on a GPU Droplet (1-Click Models), or build an agent on the Gradient AI Platform |
| Gemma | Use Gemma, Google's open-weight model: run it locally, fine-tune it, or serve it through Google Cloud or another provider |

**Partner ($100 each)**

| Category | What it asks for |
| --- | --- |
| Auth0 for AI Agents | Sign users in to an agent, call tools on a user's behalf with Token Vault, ask a person to approve a risky action before the agent takes it, or limit what a RAG pipeline can retrieve with fine-grained authorization |
| Backboard | Build with R-CLI (Backboard's open-source terminal coding agent), compare open-weight models through a single Backboard API key, or give an open-source project's assistant memory and RAG |
| Browserbase | Give the agent a real browser with Stagehand's SDK: drive a live site end to end, pull the context an open-weight model reasons over, or turn a one-off run into a repeatable workflow |
| ElevenLabs | Give an open-source agent a voice, transcribe audio for a local model, or generate narration for the demo |
| Entire | Share the agent sessions behind the project in the write-up, or search past agent work to explain why code exists |
| GitHub Copilot | Copilot's coding agent, the Copilot CLI or the new Copilot app; GitHub Actions automation; or Copilot PR review |
| Mastra | Orchestrate an agent over open models, add memory and tools to a chat agent, or build a workflow that triages GitHub issues |
| MongoDB Atlas | Atlas as the data layer: Vector Search for retrieval, long-term memory for an agent, or the database behind an app built on an open-weight model |
| Sentry Agent Tracing | Show the agent's work: setup, performance (latency, tokens, cost), findings and debugging, with traces or screenshots in the write-up |
| SerpApi | Live web search for an agent, RAG grounded in fresh results, or news tracking for an open-source project |
| Temporal | Make the agent durable: wrap it in a Temporal workflow so it survives failures, retries flaky tool calls and picks up where it left off |
| Tiger Data | Store embeddings with pgvector, run hybrid keyword and vector search for an agent, or let an agent manage a database through Tiger MCP |
| Ultramarine (Paper Instruments) | Put Ultramarine to work on something real: research, analysis, drafting, or an agent that reasons over a pile of documents. Call it with the OpenAI or Anthropic SDKs and **say what the run actually cost**. $5 free credit at hacktoberfest.com/my/promos |
| .tech Domain | Put the project live on a .tech domain claimed through Hacktoberfest and link it in the write-up (free first year, renews at $29.99/year) |

Partner credits and promo codes (Tinker, Render, Backboard, a free .tech domain, Ultramarine $5): https://hacktoberfest.com/my/promos. **Ask the user before claiming any.** Category hub: https://dev.to/challenges/hf26. Partner docs are linked from the challenge page.

## Required elements (license, demo, diagrams, IDs, credentials)

- New project built during the window; PRs to existing projects and old projects don't count. One entry per person; up to one submission per challenge.
- Post on DEV using the template below, with the tags `devchallenge` and `hf26challenge` (the template adds them).
- The post says what was built **and how the theme was interpreted** (what inspired it), shows a demo, and explains why open innovation matters.
- Demo: deployed link or video. Code: public repo (embeddable).
- **If the app requires logging in, provide testing credentials and/or testing instructions for judges** (stated explicitly this week).
- Optional "My Agent Session" (DevRelay `agent_session` embed or link) and "The Spirit of It" sections; remove "The Spirit of It" if there is no moment to show.
- Teams: one member publishes and lists teammates' DEV usernames in the body.
- Any non-generic, non-trivial use of prior work, including open-source code, must be credited; plagiarism disqualifies.
- Non-English entries get the completion badge but aren't prize-eligible. Entrants must be 18+.

## Official submission template (fetched from the challenge page, 2026-10-26)

```markdown
---
title: 
published: 
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)*

## What I Built
<!-- What does it do, and how did you interpret the theme? What inspired it? -->

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

## The Spirit of It
<!-- Optional, but this is where you can make your post stand out.  Did it give someone chills, bring back a memory, or keep a story alive?  Show us the moment it landed.  If not, remove this section. -->

## Prize Categories
<!-- Which partner categories are you entering?  List every one that applies, or remove this section. -->

<!-- Team Submissions: Please pick one member to publish the submission and credit teammates by listing their DEV usernames directly in the body of the post. -->

<!-- Thanks for participating! -->
```

## Verbatim `full_details`

The Hacktoberfest Open-Source AI Challenge: Week 4 runs October 26 to October 31. Build something spooky, or something that honors the past in the spirit of Día de los Muertos, with open-weight models or open-source AI. $2,850 in prizes across 21 winners.

This is the final challenge of our Hacktoberfest series. This year's Hacktoberfest is all about building brand-new projects with open-source AI and open-weight models, and the theme is intentionally broad, so interpret it however you'd like!

Our Theme: Ghost in the Machine

Build something spooky, or something that honors the past in the spirit of Día de los Muertos, with open-weight models or open-source AI.

This week brings us Halloween on October 31 and Día de los Muertos on November 1 and 2, a stretch of the calendar when the line between past and present feels a little thinner. Whether that brings to mind things that go bump in the night, ofrendas glowing with marigolds and candlelight, or the memories and stories we carry with us, we want to see what it inspires you to build.

That can mean running an open-weight model, building on an open-source agent harness or framework, running inference locally, or all three. Whatever you pick, the open pieces should be what makes your project work.

A few ideas to get you going:

    A haunted terminal that "possesses" your shell and whispers back eerie commentary on the commands you run
    A digital ofrenda builder that helps you write a remembrance for a loved one and gather their favorite foods, songs, and stories
    An offline séance chatbot that channels the spirit of a long-dead programming language
    A local oral history tool that records and transcribes family stories so they're never lost
    A ghost story generator that weaves your smart home's sensor logs into a creepy tale of what happened while you were asleep
    A project that brings an abandoned open-source tool or a forgotten corner of internet history back to life

In your post, tell us why open innovation matters for what you built. Does running your own model mean your project works with the lights (and the internet) off? Keep your family's photos and stories private and on your own machine? Make sure what you build isn't locked inside a service that might disappear someday? Tell us where your open-based approach worked better than a closed one.

Prize Categories

Alongside our overall winner, we have 20 prize categories for projects that use a specific partner's technology. You don't need to use any of these to win the overall prize. Full descriptions are on the HF26 DEV Challenge Hub (https://dev.to/challenges/hf26).

Featured categories: Best Use of Render, Best Use of TabPFN, Best Use of Tinker, Best Use of Arduino, Best Use of DigitalOcean, Best Use of Gemma

Partner categories: Best Use of Auth0 for AI Agents, Best Use of Backboard, Best Use of Browserbase, Best Use of ElevenLabs, Best Use of Entire, Best Use of GitHub Copilot, Best Use of Mastra, Best Use of MongoDB Atlas, Best Use of Sentry Agent Tracing, Best Use of SerpApi, Best Use of Temporal, Best Use of Tiger Data, Best Use of Ultramarine (Paper Instruments), Best Use of a .tech Domain

One project can enter every category it genuinely uses, but you can only win once per challenge. Several partners are giving participants free credits and promo codes at hacktoberfest.com/my.

Judging Criteria

This is DEV, so your write-up matters most. Submissions will be evaluated for:

    Writing Quality (weighted most heavily)
    Relevance to the Prompt and Theme
    Creativity
    Technical Execution
    Use of Partner Technology (optional, for prize category entries)

Show your work: saving your agent session with DevRelay and embedding it in your post is optional, but it helps the judges understand your process.

Prizes 🏆

Overall winner (1) will receive:

    $250 USD cash prize
    DEV++ Membership
    Exclusive DEV Badge

Featured category winners (6) will each receive:

    $200 USD cash prize
    Exclusive DEV Badge

Partner category winners (14) will each receive:

    $100 USD cash prize
    Exclusive DEV Badge

All participants with a valid submission will receive a completion badge on their DEV profile.

How To Participate

Publish a post on DEV using the submission template on the challenge page and be sure to include the required challenge tag: #hf26challenge. Tell us what you built and how you interpreted the theme, show us a demo, and explain why open innovation matters for what you built.

If your app requires logging in, please provide testing credentials in your submission and/or instructions on how to best test your application for judges.

Important Dates

    October 26: Hacktoberfest Open-Source AI Challenge: Week 4 begins!
    October 31: Submissions due at 11:59 PM PDT
    Week of November 2: Winners Announced
