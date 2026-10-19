# PartsPaddock

![PartsPaddock logo: a chat bubble with a friendly bot above a touring car whose wheels are orange gears, next to the name PartsPaddock and the tagline "the parts desk of your RC club"](docs/logo/logo-lockup.png)

> A WhatsApp agent for an RC car club. Members tell it what parts they have in the drawer and what they need; it connects the two sides inside the club, and when nobody has the part it quotes the import from a US hobby shop and batches the accepted quotes into one order for the person who runs the imports.

**Challenge:** [Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12) (DEV event 80) · **Window:** Oct 12 19:00 → Oct 19 06:59 UTC · **Tags:** `#devchallenge` `#hf26challenge`

## The problem and who pays

In our club, most of us run chassis that are not sold locally, so parts come from the US. Everyone ends up with spares in a drawer (a spur gear bought twice, the arms from a kit you converted) while someone else in the club is asking the group chat for exactly that part. The message scrolls away in minutes. When nobody has it, you ask the one person in the club who brings parts in, and they price it by hand: store price, weight, shipping per pound, a fee for placing the order.

PartsPaddock sits in the club's WhatsApp group and does both jobs:

- **Swap and sell inside the club (free).** "Tengo un spur 68T de TT-02 nuevo, $10" becomes a listing. "Busco un TAM54500" becomes a request. When the two meet, the agent writes to both members in private.
- **Import quotes (paid).** When the club has nothing, the agent looks the part up at [Michael's RC Hobbies](https://www.michaelsrchobbies.com/), reads the store's price, stock and listed weight, and answers with two totals: what it costs if the member orders it and ships it to the forwarding address, and what it costs if we order it for them. If we order it, the member sends a deposit receipt (PDF) that the maintainer checks by hand; if they order it themselves, they send the store's tracking number. Only then does it go into the order batch, and the maintainer gets one summary per batch with links, quantities and what to charge whom.

![Workflow. P2P, free: members of two clubs in the same city post HAVE or NEED; the bot matches parts inside a club or across clubs, DMs both, they meet and swap, and a sold listing is closed. B2C, paid: no match leads to a quote computed in code ($16.30), the member says sí and sends a deposit receipt PDF, the maintainer confirms the transfer, the order batch goes to the store and the US forwarding address, and the part is imported to the club. Self-order branch: the member buys it and pays only the $1.74 fee.](docs/workflow.png)

Source: [docs/workflow.svg](docs/workflow.svg).

The import service is the side hustle: a per-pound fee on everything that ships through the forwarding address, plus 12% on orders we place. The matching is free, and it is the reason members keep the bot in the group.

## How it works

![Architecture: club members, the club group and the maintainer on WhatsApp connect through an unofficial Baileys bridge to Hermes Agent (open source). Hermes uses Gemma 4 26B A4B (open weights, via OpenRouter) for language only and runs the rcparts CLI, which reads and writes Tiger Postgres and reads Michael's RC Hobbies store JSON. A cron job triggers the order batch.](docs/architecture.png)

Source: [docs/architecture.svg](docs/architecture.svg). In text form:

```
club WhatsApp group / DMs ──(Baileys bridge)──> Hermes Agent gateway ──> profile "rc-parts"
                                                   │  SOUL.md + 2 skills (rc-listings, rc-quote)
                                                   │  model turns: Gemma 4 26B A4B (open weights) via OpenRouter
                                                   ▼
                                     rcparts CLI (Python) ── Tiger Cloud Postgres (listings, matches, quotes, orders)
                                                   │      └─ Michael's RC Hobbies store JSON (price, stock, weight)
                                                   └─ hermes send ──> private messages to matched members / maintainer
Hermes cron (no model turn) ──> rcparts orders daily --send ──> order summary to the maintainer
```

The model does language only: it turns a member's message into a small JSON listing, picks the skill, and relays the reply. Everything a member has to be able to trust is code:

- **Who is writing** comes from the WhatsApp session (Hermes sets it for each turn), never from the model. In testing, the model invented phone numbers when it was asked to pass one, so the code ignores any number the model gives.
- **Validation and matching:** part numbers are normalized (`tam 54500` → `TAM54500`, `TT-02` → `TT02`), an exact part number matches first, then Postgres full-text search (with a `pg_trgm` similarity tiebreak where the extension is installed, as it is on Tiger), and a different brand or chassis on both sides vetoes a text match.
- **Every number in a quote** (price, weight, fee, totals) is computed by `rcparts` from the store's own JSON and sent as written. The model is told to send `reply` verbatim.
- **Private messages** to matched members and the order summary go out through `hermes send`, from code.

Members only see final answers: tool progress, reasoning and interim notices are turned off for WhatsApp in the profile.

### Data model

![Data model: seven tables. clubs have members; listings (HAVE or NEED, with a full-text search column) belong to a club and a member; matches link a NEED and a HAVE; quotes belong to a member and optionally a listing and an order; deposits belong to a quote; orders group quotes per store. Quote status goes quoted, awaiting_deposit, deposit_submitted, paid, ordered when we order it, or quoted, awaiting_tracking, in_transit, ordered for a self-order.](docs/db-schema.png)

Source: [docs/db-schema.svg](docs/db-schema.svg); the tables are defined in [sql/schema.sql](sql/schema.sql).

## Why open matters here

- **The economics.** A listing turn costs well under one cent with Gemma 4 26B A4B on OpenRouter ($0.0675 per million input tokens, about 20k tokens per model call, most of it Hermes's own instructions). A club bot that answers dozens of messages a day has to cost close to nothing, or the fee on a $13 part does not cover it.
- **No lock-in.** The weights are open. If OpenRouter's price changes or the free pool stays saturated (it was rate-limited during the build), the same model family runs on Ollama on the maintainer's own machine; the profile only changes its `model` block. That swap is described, not tested this week.
- **The harness is open too.** Hermes Agent gives the WhatsApp bridge, skills, cron and per-profile config. The whole agent is a profile distribution in [`agent/`](agent) that installs with one command on another Hermes instance (the plan is the maintainer's home server).
- **The members' data stays with the club.** Listings live in a Postgres database the maintainer controls. An open-source alternative for the memory layer, self-hosted [Cognee](https://docs.cognee.ai/) on the same Postgres with open embeddings, was evaluated and is in the backlog.

## Demo

<!-- TODO: video link (YouTube) and 3 screenshots with phone numbers blurred: group match, quote in DM, maintainer's order summary. -->

## Run it

You need [uv](https://docs.astral.sh/uv/), Python 3.12+, a Postgres database (Tiger Cloud's free service works), an [OpenRouter](https://openrouter.ai) key, [Hermes Agent](https://hermes-agent.nousresearch.com) 0.22+, and a spare phone number for the bot's WhatsApp.

```bash
cd challenges/03-week2-side-hustle
cp .env.example .env              # fill in OPENROUTER_API_KEY, DATABASE_URL (or TIGER_DATA_DB_URL), fees, phones
uv sync
uv run pytest -q                  # offline tests (DB and live-store tests skip without credentials)
uv run rcparts db check           # server version and available extensions
uv run rcparts db init
uv run rcparts club add --name "My RC Club" --country EC --city "My City"
uv run rcparts member add --club 1 --phone 5939XXXXXXXX --name Ana --rc-class "1/10 touring"

scripts/setup-profile.sh --env-file .env   # installs the Hermes profile "rc-parts" from agent/ + skills/
hermes -p rc-parts whatsapp                # scan the QR code with the bot's phone (Linked devices)
scripts/gateway-restart.sh                 # one host gateway serves every Hermes profile
scripts/install-cron.sh                    # order batch on ORDER_BATCH_SCHEDULE (daily 18:00 by default)
```

Then add the bot's number to the club group, @mention it once, read the group id (`…@g.us`) from the gateway log, put it in `WHATSAPP_GROUP_ALLOWED_USERS` and run `scripts/setup-profile.sh --env-file .env` again. Details: [agent/README.md](agent/README.md).

The CLI is usable on its own, which is also how the maintainer works with it:

```bash
uv run rcparts quote --phone 5939XXXXXXXX --query TAM54500
uv run rcparts search --club 1 --text "spur TT-02" --kind HAVE
uv run rcparts orders daily --dry-run
```

## Stack

- **Model:** Gemma 4 26B A4B instruct (open weights, Google), served by OpenRouter (`google/gemma-4-26b-a4b-it`). The `:free` id exists but its shared pool was rate-limited during the build.
- **Agent harness:** Hermes Agent 0.22.2 (Nous Research): WhatsApp gateway (Baileys bridge), skills, cron, profile distribution.
- **Code:** Python 3.14, `psycopg`, `httpx`; 39 offline tests.
- **Database:** Postgres 18 on Tiger Cloud (TimescaleDB service) with `pg_trgm`; the agent can read it through Tiger MCP (`db_query` only); all writes go through `rcparts`.
- **Store:** Michael's RC Hobbies' public storefront JSON (`?format=json`), respecting its 2-second crawl delay.
- **Prize categories:** Gemma, Tiger Data.

## Honest limits

- **Unofficial WhatsApp client.** The Baileys bridge links the bot's number like WhatsApp Web; WhatsApp can restrict such numbers. A real deployment for many clubs needs the official WhatsApp Business Cloud API, which only works with groups the business creates and needs business verification.
- **Model not local.** Inference runs at OpenRouter, not on the maintainer's machine. The self-host path (Ollama) is described, not tested in this build.
- **Weight unit.** The store's JSON does not say its weight unit. 113 for the TT-02 spur set is consistent with grams; quotes say "weight as listed by the store" until it is checked against a part on a scale.
- **One store.** AMain Hobbies was dropped: its product pages list no weight and its robots.txt disallows search.
- **No payments.** Quotes and orders are records; the maintainer collects and places orders by hand.
- **One club.** The schema has `club_id`, but onboarding several clubs, roles and per-club fees are backlog.
- **Matching is text, not meaning.** "front lower arms" matched "brazos delanteros inferiores (front lower arm set)" because the member wrote the English too; pure Spanish against pure English would not match without embeddings.
- **Latency.** A turn takes 20 to 60 seconds, mostly model calls on a 20k-token prompt.

## Credits

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research) for the harness and WhatsApp bridge; [Baileys](https://github.com/WhiskeySockets/Baileys) under it.
- [Gemma](https://ai.google.dev/gemma) (Google DeepMind), served by [OpenRouter](https://openrouter.ai).
- [Tiger Data](https://www.tigerdata.com/) for the Postgres service, CLI and MCP server.
- Product data from [Michael's RC Hobbies](https://www.michaelsrchobbies.com/)' public storefront. Not affiliated.
- Built with Claude Code as the coding agent; decisions, measurements and failures are logged in [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md), the plan in [docs/SPEC.md](docs/SPEC.md).

All code in this folder was written inside the challenge window (first commit 2026-10-18 00:20 UTC). Nothing was reused from the author's earlier challenge projects.

## License

MIT, see [LICENSE](LICENSE).
