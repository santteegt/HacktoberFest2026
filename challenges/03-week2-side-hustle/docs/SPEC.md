# PartsPaddock: project spec

**Challenge:** Hacktoberfest Open-Source AI Challenge: Week 2, Side Hustle (DEV event 80) · **Deadline:** 2026-10-19 06:59 UTC (Sun Oct 18, 11:59 PM PDT; Mon Oct 19 1:59 AM at UTC-5). Written 2026-10-18 00:50 UTC with about 30 h left. Decisions and their reasons are in [CHALLENGE-MEMORY.md](CHALLENGE-MEMORY.md); this file is the plan.

## 1. The problem and who pays

RC club members buy chassis kits and spare parts from the US, and most of them end up with parts in a drawer that someone else in the club is looking for. Today the search is "does anyone have a 68T spur for a TT-02?" in the club's WhatsApp group, scrolled past in minutes. When nobody has it, the member either waits for the next trip or asks the one person in the club who runs group imports, who then prices it by hand (store price, weight, import fee).

**The product:** an agent that lives in the club's WhatsApp group. Members tell it what they **have** and what they **need**; it keeps the club's stock and wish list, connects the two sides, and, when the club has nothing, quotes an import from a whitelisted US hobby shop and batches the day's accepted quotes into one order.

**Who pays:** the member who accepts an import quote pays the import service (a weight-based fee plus an optional 12% processing fee when the maintainer places the order). The club-to-club matching is free; it is the reason members keep the bot in the group. The maintainer (the author) runs the import service, which is the side hustle.

## 2. Scope

### In scope for the submission (ordered; each stage leaves a working product)

| Stage | What exists at the end | Est. | Done when |
| --- | --- | --- | --- |
| **S0 Scaffold and spec** | Folder, rules snapshot, this spec, first commit | 0.5 h | Committed inside the window |
| **S1 Agent up** | Hermes profile `rc-parts` in `agent/` (SOUL, `config.yaml`, `distribution.yaml`, `.env.example`), OpenRouter provider with Gemma 4 26B A4B, WhatsApp bridge paired on the spare SIM, one test club group allowlisted by JID, `WHATSAPP_REQUIRE_MENTION=true`, DM allowlist for the two members and the maintainer | 2 h | The bot answers "@bot hello" in the group and a DM from a member |
| **S2 Listings** | Skill `rc-listings`: HAVE / NEED messages → JSON listing validated by code, saved to Postgres; a confirmation reply that echoes the parsed fields; one clarifying question when a required field is missing | 2.5 h | 10 scripted messages (English and Spanish, with part numbers and without) parse to valid rows; bad ones get a question, never a silent guess |
| **S3 Matching** | Matcher in code: exact part number, then hybrid keyword search (Tiger `pg_textsearch` BM25 over normalized brand + chassis + description); on a match, DM both members an intro with the listing details | 2 h | A NEED posted after a HAVE (and the reverse) produces two DMs within one turn |
| **S4 Import quote** | Skill `rc-quote`: no match → Michael's RC Hobbies search and product JSON (`?format=json`, 2 s crawl delay) → price, stock, weight → quote computed in code from `.env` parameters (`FEE_PER_KG`, `PROCESSING_PCT`, `US_ADDRESS`) → "reply YES to add to today's order" | 2 h | A quote for a known part shows the store price, the weight as the store lists it, the fee and the total; YES stores an accepted quote |
| **S5 Daily batch** | Hermes cron (profile-level) groups accepted quotes by store and DMs the maintainer a summary with links and totals | 1 h | A manual cron run sends the summary with two accepted quotes |
| **S6 Ship** | Demo video in the real test group (2 members), README, `.env.example`, audit, DEV draft staged, first-user section with what the members did and said | 4–5 h | Post staged before Sunday 18:00 local; published by the author with margin |

Freeze features at **Sun Oct 18, 20:00 local (01:00 UTC)**. After that only fixes, demo, README and post.

### Prize categories entered

- **Gemma** (featured): the only model in the project, `google/gemma-4-26b-a4b-it:free` through OpenRouter; the same family runs on Ollama for self-hosting.
- **Tiger Data** (partner): the listings database on Tiger Cloud; hybrid keyword search for matching; Tiger MCP in the profile so the agent can answer ad-hoc stock questions. Model gets read-only tools; writes are code.
- **ElevenLabs** (partner, decide at S4): voice notes in the group transcribed by Scribe through a Hermes `command` STT provider. Default is Hermes's local faster-whisper; switch only if Spanish transcripts are poor and time allows.

### Out of scope this week (backlog, say so in the post)

Multi-tenancy beyond a `club_id` column · user-level memory beyond a `members` row (self-hosted Cognee evaluated 2026-10-18: workable later as `cognee-mcp` on the same Tiger pgvector, 4-8 h and too many free-tier LLM calls for this window; it is the project's named open-source alternative to Tiger for memory and search, with open embeddings via fastembed or Ollama, or OpenAI embeddings on the author's credits) · AMain Hobbies (no weight, search disallowed by robots) · order placement, payment and tracking-number intake · x402 or any settlement · hosting on Render or DigitalOcean (the maintainer deploys the profile to a home Hermes instance after the challenge) · Temporal for the quote workflow · the official WhatsApp Cloud API.

## 3. Architecture

```
club WhatsApp group  ──(Baileys bridge)──>  Hermes gateway, profile rc-parts
   @bot HAVE / NEED / quote / YES               │
   voice notes (STT provider)                   ├─ SOUL.md: persona, rules, next-step hints
                                                ├─ skill rc-listings: parse → validate → insert
                                                ├─ skill rc-quote: store JSON → quote (code)
                                                ├─ cron daily-order: batch → DM maintainer
                                                └─ mcp_servers.tiger (read-only tools)
                        model turns ──> OpenRouter: google/gemma-4-26b-a4b-it:free
                        SQL ────────> Tiger Cloud (TimescaleDB + pg_textsearch, pgvector available)
                        quotes ─────> michaelsrchobbies.com/…?format=json
```

**Model jobs (language only):** map a member's message to a JSON listing or a quote request; phrase replies and clarifying questions. **Code jobs:** validation, normalization, matching, prices, fees, totals, the daily batch, every message that must be true.

## 4. Data model (Postgres on Tiger)

- `clubs(id, name, country, city, whatsapp_group_jid)`
- `members(id, club_id, phone, display_name, rc_class, brands text[], created_at)`
- `listings(id, club_id, member_id, kind HAVE|NEED, brand, chassis, part_number, description, condition, price_usd, qty, status open|matched|closed, created_at, search tsvector/BM25 index)`
- `matches(id, need_id, have_id, notified_at)`
- `quotes(id, listing_id, store, store_url, store_price_usd, weight_g, fee_usd, processing_usd, total_usd, status quoted|accepted|ordered, created_at)`
- `orders(id, store, date, quote_ids int[], summary_sent_at)`

## 5. Risks and hedges

| Risk | Hedge |
| --- | --- |
| WhatsApp number restricted | Spare SIM only; members message the bot first; Telegram gateway as a 15 min fallback; record the demo early |
| OpenRouter free tier rate-limited | Same model id without `:free` on paid credits, by config; log cost in the memory |
| Mid-size model skips instructions (Week 1) | Next step inside tool replies; validator on every parse; critical messages from code |
| Tiger connection fails during the demo | SQLite fallback behind the same repository module is **not** planned; instead keep the Tiger password saved in the CLI keyring and test the connection first thing on demo day |
| Michael's weight unit | Confirm against one part the author owns before the demo; show "weight as listed by the store" |
| Time | Each stage ships a working product; S5 and ElevenLabs are the first cuts |

## 6. Honesty rules for the post

May claim only what the memory's "may claim" table has evidence for. Must say: unofficial WhatsApp client; model served by OpenRouter, not local; which stages were cut; what the two members actually did and said (with permission) and whether anyone paid.
