# Retrospective: Week 2 "Side Hustle" (PartsPaddock)

Written 2026-10-18 (local time, UTC-5), right after publishing. Source of truth for the details is the project's running log, `challenges/03-week2-side-hustle/docs/CHALLENGE-MEMORY.md`. Outcome is not known yet: winners are announced the week of Oct 19.

## What was built

PartsPaddock: a WhatsApp agent for RC car clubs. Members tell it what parts they have in the drawer (HAVE) and what they need (NEED) in the club group or by DM. It matches them inside a club and across clubs in the same city and introduces both members by DM (free, P2P). When no club has the part, it quotes an import from a US hobby shop (store price + weight × per-pound fee, +12% if "we order it"); "we order it" needs a deposit receipt PDF that the maintainer confirms by hand, a self-order needs the store's tracking number, and confirmed items go into an order batch sent to the maintainer (paid, B2C: the maintainer's side hustle).

Stack: Hermes Agent 0.22.2 (open source) as the harness, with its Baileys WhatsApp bridge on a spare prepaid SIM, a profile distribution (`SOUL.md`, `config.yaml`, two skills `rc-listings` and `rc-quote`, a manifest) and a cron job; Gemma 4 26B A4B (open weights) through OpenRouter; a Python CLI `rcparts` that does identity, validation, matching, quote math, deposits, tracking and notifications; Postgres 18 on Tiger Cloud (with `pg_trgm`, `unaccent`, read-only Tiger MCP for the agent); Michael's RC Hobbies storefront JSON. Not open: WhatsApp and the unofficial bridge, OpenRouter as the host, the store.

Post: https://dev.to/santteegt/partspaddock-a-whatsapp-parts-desk-agent-for-rc-clubs-p2p-b2c-market-connecting-hobbyists-14oa (published 2026-10-18 23:21 local, 2026-10-19 04:21 UTC, about 2 h 38 min before the deadline). Demo video: https://youtu.be/q_8uofEnFSc. Partner categories entered: Gemma (the only model) and Tiger Data (the database, full-text matching, read-only MCP). Everything else skipped on purpose.

## Timeline (author's local time, UTC-5)

- Oct 12, afternoon: folder scaffolded after the challenge opened; never committed for five days.
- Oct 17, 18:30: brainstorming started with about 31 h left. Three Opus subagents checked feasibility in parallel (hobby-shop scrapability, WhatsApp bot options, agent-commerce protocols). Idea chosen: RC parts finder; the agent-to-agent marketplace was rejected (fails "small, specific, who pays"; multi-week).
- Oct 17, 19:20: scaffold and spec committed (first commit inside the window). Hermes installed natively. Partners chosen (Gemma, Tiger Data); Cognee evaluated and kept as backlog.
- Oct 17 night: profile, skills and the `rcparts` CLI (built by a subagent against a fixed CLI contract); full CLI cycle on Tiger; WhatsApp paired; first real DM delivered.
- Oct 18, 00:00 to 01:00: first real WhatsApp rounds; the model invented phone numbers; sender identity moved to code; quiet display mode.
- Oct 18, morning: diagrams, demo seed and reset, cross-club matching, close-by-DM, deposit receipts (two parallel subagents); history rewritten to remove real phone numbers before the first push; self-order tracking numbers; rename to PartsPaddock and the logo.
- Oct 18, 17:00 to 18:00: live test by the author found four gaps (English vs Spanish matching, quotes staying in the group, no "my orders", literal store search); fixed by a subagent in about 18 min with 112 tests.
- Oct 18, 22:40 to 23:21: demo video, final draft, audit, humanizer pass, staged on DEV, first push, images fixed, author's edits synced, published.

## What worked

- **Identity in code, not in the prompt.** The model cannot see phone numbers and invented them when asked. Hermes puts the sender of each turn in the shell environment (`HERMES_SESSION_USER_ID`), so the CLI reads it there and ignores any `--phone` the model passes. That also blocks a member from acting as someone else and makes "only the maintainer confirms payments" a real control.
- **One JSON contract for every command (`ok`, `reply`, `action`).** The model relays `reply` verbatim and follows `action`. Every number a member sees (price, weight, fee, totals) is computed by code from the store's JSON. Validator tolerance in code (field-name drift, nulls, code fences) beat re-prompting.
- **Human verification where documents vary.** Bank receipts differ across institutions, so the PDF goes to the maintainer and only a confirmation from the maintainer's number marks a quote paid. The first real deposit round trip (test PDF, confirmation) worked on the first try.
- **Feasibility subagents before choosing.** Three parallel Opus checks in the first hour settled the store (one shop with weight in its JSON; the other had no weight and disallowed search), WhatsApp (Hermes's Baileys bridge; the official Cloud API needs days of verification) and payments (x402 is the only self-serve testnet; out of scope).
- **Parallel subagents with file ownership.** Code and diagrams were built at the same time without conflicts because each agent owned its files and nothing was committed until review.
- **Profile distribution.** The agent is a folder (`agent/` + `skills/`) installed with one script; reinstalling after every skill change was trivial.
- **The memory file and its may/must-not-claim table** kept the post honest: no local-inference claim, no payment claim (the receipt was a test PDF), the weight unit stated as unverified, seeded demo data labelled.

## What went wrong or cost time

- **Starting late.** Five days passed between scaffolding and brainstorming, so the whole build fit in about 28 hours with little sleep.
- **Free model pool saturated.** `google/gemma-4-26b-a4b-it:free` was rate-limited upstream; the paid id of the same weights answered at once ($0.0675 / $0.225 per 1M tokens, about $0.0014 per 20k-token call).
- **Hermes keeps a session's creation-time prompt.** Skill and SOUL fixes did not reach open chats until `/new`; one test failed only because of that.
- **Gateway restarts.** Closing a terminal tab killed the gateway and left its bridge on the port; a quick restart after a clean stop fails about half the time because the old bridge holds the session for a few seconds. `scripts/gateway-restart.sh` (stop, wait, start, retry) fixed it. One host gateway serves every profile in Hermes 0.22.
- **Search gaps found only in live use.** The 'simple' full-text config has no stemming or translation: plurals missed, and English "rear lower arm" missed Spanish "brazo inferior trasero". A 42-concept bilingual glossary with per-concept overlap, accent folding, plural folding and position vetoes (front/rear, left/right, upper/lower) fixed it; a later finding was that a match must share an actual part concept, not only modifiers.
- **Store search is literal and order-sensitive.** "kit Xray XB2D 2026" found nothing while "Xray XB2D 2026" found the kit; up to four rewritten queries fixed it.
- **Real phone numbers in local commits.** Tests written with the real numbers had to be scrubbed from 18 unpushed commits with `git filter-branch` before the first push; a backup branch kept the old history until it was deleted and pruned.
- **DEV image cache.** DEV's image proxy fetched two `raw.githubusercontent.com/.../main/...` URLs before the first push and kept the 404. Pointing the images at a commit SHA gave DEV new URLs to fetch.
- **Pushing late.** The repo was first pushed after the draft was staged, so the post's images and GitHub card were broken during review.

## Numbers

- Build: first commit 2026-10-18 00:20 UTC; published 04:21 UTC the next day.
- Tests: 112 passed against Tiger at the end (108 offline).
- Per model call about 20.5k prompt tokens, mostly Hermes's own instructions; a listing turn well under one cent.
- Turn latency on WhatsApp: about 20 s for a quote, about 66 s for a four-call group listing turn.
- Live quote from the store: about 2.7 s (2 s crawl delay); 3.7 s when the second query variant is needed.
- Demo seed: 20 real Xray parts (10 X4, 10 X1), 2 clubs, 2 real members, 8 HAVE and 2 NEED; reset and seed in 18 s.

## Playbook additions

1. Brainstorm the day the challenge opens; a late start removes the margin for real-user testing.
2. Run feasibility checks as parallel subagents in the first hour, before choosing the idea.
3. Never let the model pass identity; take it from the platform session in code.
4. Test bilingual input and plurals early when users write in more than one language; word-based search will miss both.
5. Use test placeholders for phone numbers from the first test file; scrubbing history later is slow and risky.
6. Push the repo before staging the post, and point post images at a commit SHA when an image was ever fetched while missing.
7. After any skill or SOUL change in Hermes, start a new session in each chat (`/new`) before testing.
8. Keep a restart script for long-running gateways; never kill them by closing a terminal.
