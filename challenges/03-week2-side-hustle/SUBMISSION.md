---
title: "RC Parts Finder: the parts desk for my RC club, in our WhatsApp group"
published: false
tags: devchallenge, hf26challenge, opensource, ai
---

<!-- DRAFT v1, 2026-10-18. Written from docs/CHALLENGE-MEMORY.md; every claim maps to an entry there. TODO markers are for the author. Not staged on DEV yet. -->

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## What I Built

I race 1/10 touring cars in Cuenca, Ecuador. Almost nothing we run is sold here, so parts come from the US, and every club member has a drawer of spares: a spur gear bought twice, the arms left over from a conversion. Meanwhile someone else in the club is asking the WhatsApp group for exactly that part, and the message scrolls away. When nobody has it, the member asks whoever brings parts in, and that person prices the import by hand.

RC Parts Finder is a bot that lives in the club's WhatsApp group and does both jobs.

- **Swap and sell inside the club, free.** "Tengo un spur 68T de TT-02 nuevo, $10" becomes a listing. "@bot busco un TAM54500" becomes a request. When a request meets a listing, the bot writes to both members in private.
- **Import quotes, paid.** When the club has nothing, the bot looks the part up at Michael's RC Hobbies and answers with the store price, the weight the store lists, our per-pound fee, and two totals: one if the member orders it and ships it to our forwarding address, one if we order it for them (+12%). The member answers "sí" and it goes into the next order batch. The maintainer (me) gets one summary per batch with links, quantities and what to charge whom.

![Workflow. P2P, free: members of two clubs in the same city post HAVE or NEED; the bot matches parts inside a club or across clubs, DMs both, they meet and swap, and a sold listing is closed. B2C, paid: no match leads to a quote computed in code ($16.30), the member says sí and sends a deposit receipt PDF, the maintainer confirms the transfer, the order batch goes to the store and the US forwarding address, and the part is imported to the club. Self-order branch: the member buys it and pays only the $1.74 fee.](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/03-week2-side-hustle/docs/workflow.png)

**Who pays:** the club member who wants a part brought in. The fee per pound and the 12% for placing the order are the side hustle; the free matching is what keeps the bot in the group. It is small and specific on purpose: one club, one store, one person running imports.

## Demo

<!-- TODO(author): embed the video. Suggested script, 2-3 min, all in the real test group:
1. Socio posts "tengo un spur 68T de TT-02, nuevo, $10" in the group (bot @mentioned) -> one-line confirmation.
2. Santiago posts "@bot busco un TAM54500" -> group one-liner; both phones show the private match message.
3. Santiago DMs "cuánto me sale traer un TAM54500?" -> the quote with both totals.
4. "sí" -> confirmation. 5. Maintainer's order summary arrives (hourly cron or run by hand).
Blur phone numbers. Show that no "running tool" messages appear. -->

{% embed TODO-video-url %}

<!-- TODO(author): 3 screenshots, numbers blurred: group match, quote in DM, order summary. -->

## Code

{% github santteegt/HacktoberFest2026 %}

The project is in [`challenges/03-week2-side-hustle`](https://github.com/santteegt/HacktoberFest2026/tree/main/challenges/03-week2-side-hustle). MIT licensed.

## How I Built It

Three pieces, and a strict line between what the model does and what code does.

![Architecture: club members, the club group and the maintainer on WhatsApp connect through an unofficial Baileys bridge to Hermes Agent (open source). Hermes uses Gemma 4 26B A4B (open weights, via OpenRouter) for language only and runs the rcparts CLI, which reads and writes Tiger Postgres and reads Michael's RC Hobbies store JSON. A cron job triggers the order batch.](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/03-week2-side-hustle/docs/architecture.png)

**The agent: Hermes Agent with Gemma 4.** [Hermes Agent](https://hermes-agent.nousresearch.com) is an open-source agent harness from Nous Research. It already has a WhatsApp gateway (a Baileys bridge that links a number like WhatsApp Web), skills, cron jobs and per-profile configuration. The bot is a Hermes **profile distribution**: a persona file, a config, two skills (`rc-listings` and `rc-quote`) and a manifest, so the whole agent installs on another Hermes machine with one script. The model is **Gemma 4 26B A4B**, an open-weight mixture-of-experts model with about 4B active parameters, served by OpenRouter. The bot has a dedicated prepaid SIM, answers in the group only when mentioned, and only allowlisted numbers can talk to it.

**The code: a small Python CLI, `rcparts`.** The skills tell the model to run `rcparts listing add --json '…'` or `rcparts quote --query TAM54500` and to send back the `reply` field as written. Every command prints one JSON object with `ok`, `reply` and `action` (the next step, which a mid-size model follows better than a paragraph in a skill). The CLI validates the listing, normalizes part numbers, saves it, finds matches, computes quotes from the store's own JSON, and sends the private messages with `hermes send`. The order batch is a Hermes cron job that runs a script with no model turn at all.

**The data: Postgres on Tiger Cloud.** Clubs, members, listings, matches, quotes and orders live in a Tiger Cloud service. Matching is an exact part-number match first, then Postgres full-text search with a `pg_trgm` similarity tiebreak, and a different brand or chassis on both sides vetoes a text match. The agent can also read the database through Tiger's MCP server for questions the CLI does not cover, with only the read-only `db_query` tool enabled.

What the model does: turn "tengo un spur 68T de TT-02 nuevo, lo doy en 10 dólares" into `{"kind":"HAVE","chassis":"TT-02","description":"spur 68T","condition":"new","price_usd":10}`, choose the skill, and relay the reply. What it never does: decide who is writing, compute a price, or message someone on its own.

Three things the real tests changed:

1. **The model invented phone numbers.** My first skill asked the model to pass the sender's phone. In the first real DM it searched the members table by WhatsApp display name for ten tool calls, then ran the command with `--phone 1234567890` and later `593000000000`, and told me I was not registered. Hermes already puts the sender of each turn in the environment of the shell it runs, so the CLI now reads it there and ignores any number the model passes. The skills don't mention phones anymore. That also means a member can't ask the bot to act as someone else.
2. **The model drifted from the JSON field names.** It wrote `type` instead of `kind`, `price` instead of `price_usd`, explicit nulls and a ```json fence. The values were right, so the validator accepts those variants in code instead of asking the member again.
3. **Members should only see answers.** Hermes shows tool progress in chats by default ("running rc-listings…"). In a club group that is noise, so the profile turns off tool progress, reasoning and interim messages for WhatsApp; the calls still go to the log.

The real quote for the part in the demo: TAM54500, TT-02 68T spur set, $13.00 at the store, 113 listed as its weight, 0.25 lb × $7.00/lb = $1.74 fee, $14.74 if the member orders it, $16.30 if we order it (+12%, $1.56). Those numbers come from the store JSON and `rcparts`; the model only passed them on.

## Why Does Open Innovation Matter?

**Because the business has to cost almost nothing to run.** The fee on a $13 part is a couple of dollars. Gemma 4 26B A4B costs $0.0675 per million input tokens on OpenRouter. A model call in this bot is about 20,000 tokens, most of it Hermes's own instructions and tool definitions, so a call is about a seventh of a cent and a full "add a listing" turn is well under one cent. A closed frontier model at many times that price would eat the margin of a club-sized business.

**Because I can leave.** The weights are open. OpenRouter also lists a free `:free` version of the same model; during the build its shared pool was rate-limited, so I pay for the regular one. If the price changes or the provider disappears, the same model family runs on Ollama on my own machine and the profile changes one block. I describe that swap; I have not tested it in this build.

**Because the agent itself is open.** Hermes gave me the WhatsApp bridge, skills, cron and a profile format I can version in git and install on my home server. When something went wrong I could read the session database and the exact tool calls the model made, which is how I found the invented phone numbers.

**Because the club's data stays with the club.** Listings live in a Postgres database I control. I also looked at self-hosted [Cognee](https://docs.cognee.ai/), an open-source memory layer, for remembering members' cars and habits. It can run on the same Postgres with open embeddings, but its extraction step makes several model calls per message and it was too much for this week, so it is the next step, not part of this build.

What is not open: WhatsApp itself, and the bridge is unofficial. A version for many clubs needs the official WhatsApp Business API.

## My Agent Session

<!-- TODO: curated DevRelay session (decision points + the phone-number failure), scrubbed of keys and phone numbers, made public. Optional. -->

## My First User

<!-- TODO(author): fill from what really happened; keep only what Socio agrees to share. Facts already logged:
- 2026-10-18, from their own phone, Socio asked the bot "Cuánto me cuesta traer un TAM54500?", got the quote ($16.30 if we order it) and answered "Si"; the quote was recorded as accepted in their name and went into the order batch.
Needed: would they pay $16.30 for it (or did they)? What did they say about it? What did they ask for next? A short quote with their permission.
Do NOT claim payment unless it happened. -->

## Prize Categories

**Best Use of Gemma.** Gemma 4 26B A4B is the only model in the project. It reads every message in the club group and in DMs, turns HAVE and NEED messages in Spanish or English into listing JSON, picks the skill and relays the replies.

**Best Use of Tiger Data.** The listings, matches, quotes and orders live in a Tiger Cloud Postgres service (Postgres 18, TimescaleDB 2.30). Matching uses Postgres full-text search plus `pg_trgm`, and the agent has Tiger's MCP server with the read-only `db_query` tool for questions the CLI does not cover; all writes go through the CLI. `pgvector` and `pg_textsearch` (BM25) are available on the same service and are the next step for matching Spanish against English.

## Limits

- The WhatsApp bridge is unofficial, and WhatsApp can restrict the bot's number.
- Inference is at OpenRouter, not local. The self-hosted path is described, not tested.
- The store does not say what unit its weight is in. 113 for the spur set is consistent with grams. <!-- TODO(author): weigh one part and update this line. -->
- One store. AMain Hobbies lists no weights and disallows search in robots.txt.
- No payments: quotes and orders are records, and I collect and place orders by hand.
- A turn takes 20 to 60 seconds, mostly model calls on a 20,000-token prompt.
- Matching is words, not meaning: pure Spanish against pure English will not match until embeddings are added.

<!-- Thanks for participating! -->

---

## Pre-submission checklist (not part of the post)
- [x] Started inside the challenge window (first commit 2026-10-18 00:20 UTC); later commits noted in README if any after the deadline
- [x] Tags `devchallenge` and `hf26challenge` present
- [ ] Public repo pushed with license; demo link or embed works
- [x] Open-source AI is at the core; "why open innovation matters" is explained
- [x] The post says who would pay for it and why
- [ ] "My First User" reports only what really happened, or the section is removed
- [x] Each prize category claimed has a concrete, meaningful use (Gemma, Tiger Data)
- [ ] No secrets or phone numbers in repo, screenshots or transcript
- [x] Credits for borrowed code/assets (README)
- [x] Written in English (prize eligibility)
- [ ] Posted with the default `ai_disclosure_level`
- [ ] Posted before the deadline (Oct 19 06:59 UTC = Oct 18 11:59 PM PDT = Oct 19 01:59 local)
