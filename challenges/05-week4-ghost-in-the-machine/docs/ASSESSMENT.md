# A ghosts in the decentralized world computer: feasibility assessment

Written 2026-10-29 04:00Z (Wed Oct 28, 23:00 local). Safe deadline Oct 31 06:59Z (Fri Oct 30, 01:59 local) is **51 hours away**; the page deadline (Nov 1 06:59Z, Sun 01:59 local) is 75 hours away. Everything below was checked live tonight unless marked "not checked".

## 1. Are the Ethereum History tools enough?

**Short answer: they cover discovery and the contract's birth and body, not its death, its wounds, or its face.** They are the right spine for picking and describing ghosts; four other free, keyless sources fill the gaps.

| Need | Ethereum History (API, MCP, skills) | Gap filler (checked) |
| --- | --- | --- |
| Find old contracts, by era, type, time range, text | **Yes.** REST `GET /api/agent/contracts` with `era_id`, `from_timestamp`/`to_timestamp`, `q`, `featured`; MCP `browse_contracts` (era enum frontier → spurious-dragon, type enum token/multisig/crowdsale/exchange/wallet/registry…), `search_contracts`, `get_contract_of_the_day` (deterministic daily rotation over **4,127 documented contracts**; 1,368,496 total in the archive, all 2015-2017) | None needed. Note: the apex host returns a 307 to `www.`; call `https://www.ethereumhistory.com` directly, 20 req/min anonymous, 120 with a free historian key |
| Birth: deployer, tx, block, timestamp, era | **Yes**, in `GET /api/agent/contracts/{address}` | |
| Body: runtime bytecode, decompiled code, ABI, heuristics (`contract_type`, `is_proxy`, `has_selfdestruct`, `is_erc20_like`) | **Yes** | Verified source for 2017+ contracts: **Sourcify v2** (BAT 0.4.10: full match, 1 source; Rubixi 0.2.1: match; TheDAO: absent, but EH documents it). Etherscan free key as a second fallback |
| The documented story (what it was, why it mattered, links, predecessor/successor) | **Yes for the 4,127 documented ones** (`short_description`, `description`, `historical_significance`, `links`), written by historians; frontier era is 148/200 documented in the first page, later eras 2-22/200 | For undocumented ones the ghost only has its code; pick documented ones for the demo |
| **Death: last state transition, activity by year, balance now** | **No.** Only some documented contracts carry a `metadata.tx_counts_by_year_external_to_v1` entry | **Blockscout v2, keyless**: `/api/v2/addresses/{a}` (balance, verified, creation tx), `/addresses/{a}/transactions?filter=to` (newest first → last tx date and method; KotE: 2016-02-19 `sweepCommission`), `/addresses/{a}/counters` (21 txs). Public RPC `eth_getCode` tells banished (selfdestructed) from lingering |
| **Vulnerabilities** | **No** (the archive is "factual, non-opinionated"); `has_selfdestruct` is the only hint, and prose descriptions sometimes name a bug (KotE: "gas-stipend bug") | **Slither 0.11.6** via `uv tool run`, with `solc-select` (0.4.10 installed in seconds; BAT analyzed in 2.6 s, 45 findings). **Limit: Slither needs solc ≥ 0.4**, so frontier and homestead contracts (solc 0.1-0.3, like Rubixi 0.2.1) need a second tier: a curated incident catalog plus regex gates plus a Gemma reading, labelled "suspected" |
| Modern fix | n/a | `solc-select` offers **0.8.38** (the release the author linked), so every "ghost buster" snippet can be compile-checked before it is shown |
| **Screenshot of the dapp** | **No** | **Wayback CDX** lists captures (kingoftheether.com from 2016-02-11); archive.org has no screenshot API, so the tool renders `web.archive.org/web/<ts>/<url>` itself with headless Chromium (Playwright; a cached Chromium exists on this Mac but no matching Python package, so `playwright install chromium` is a one-time 2-minute step; **not yet proven end to end**) |
| Agent use at runtime | **MCP server is streamable HTTP** at `https://www.ethereumhistory.com/mcp` (initialize and `tools/list` answered; 5 tools). **Hermes v0.22.5 accepts `mcp_servers.<name>.url`** in `config.yaml`, so the Hermes ghost can call it natively | Our own CLI exposed as a Hermes skill does the heavy pipeline; MCP is for the agent's free questions and the daily pick |
| The skills repo | `eth-historian` (write stories into the archive; needs an invite-only historian account), `eth-researcher` (find undocumented contracts, verify facts via Etherscan), `eth-cracker` (reproduce bytecode). **Not needed for our features**, but `eth-researcher`'s fact-check list (deployer, era, source leads) is the model for our "facts first, story second" step, and the repo is the citation for the MCP and API shapes | Install only if the Hermes agent should also *contribute* stories back to the archive (a nice closing paragraph, not an MVP item) |

## 2. Feature by feature

| Feature | Feasible in 51 h? | How | Theme fit |
| --- | --- | --- | --- |
| **F1. Find ghosts and tell the story from inception to the day it passed away** | **Yes, core.** | `ghosts summon <address>`: EH facts + Sourcify source + Blockscout last tx, counts and balance + Wayback first/last capture → `facts.json` (every number from code). Gemma 4 12B writes the life story in chapters (birth, life, silence) **only from facts.json**, with a code check that every date, number and name in the story exists in the facts (Week 1-3 verifier pattern; the same rule Wayback Séance used, which judges will have seen). "Passed away" = date of the last successful external transaction | Strong: honoring the past, and the "ghost in the machine" is literal: code with nobody behind it, still answering |
| **F2. Friendly ghost = simply stopped being used** | **Yes, trivial.** | Code decides: last tx older than 2 years, code still present, no confirmed vulnerability → `friendly`. Still active → `not yet a ghost` (skipped by the daily pick). `eth_getCode` empty → `banished` (selfdestructed; gravestone only) | Friendly-ghost tone: Día de los Muertos remembrance |
| **F3. Bad ghost = had a vulnerability; scary story + code snippet** | **Yes, two tiers, partly.** | Tier A (solc ≥ 0.4, verified on Sourcify): Slither, keep only a shortlist of detectors (`reentrancy-eth`, `suicidal`, `arbitrary-send-eth`, `controlled-delegatecall`, `uninitialized-state/storage`, `unchecked-transfer`, `locked-ether`, `weak-prng`, `tx-origin`) → `confirmed` with the exact source lines from Slither's mapping. Tier B (frontier/homestead, solc < 0.4): a hand-written incident catalog (TheDAO reentrancy, KotE gas stipend, Rubixi constructor rename, GovernMental, Parity wallet `initWallet`/delegatecall, EtherPot, …) with SWC ids and line hints, plus regex gates (`call.value`, unchecked `send(`, `suicide`, `tx.origin`, constructor name ≠ contract name) → `suspected`, and the post says so. Gemma writes the scary story from the finding; the snippet is cut by code, never by the model | Strong: the spooky half of the brief |
| **F4. Ghost buster story + fix snippet in Solidity 0.8.38** | **Yes, with a gate.** | Per detector, a fix recipe (checks-effects-interactions and a reentrancy lock; `constructor` keyword; built-in overflow checks; `require` over `throw`; `call` with checked return; `selfdestruct` deprecated since 0.8.18 and neutered by EIP-6780 on Cancun). Gemma adapts the recipe to the contract's names; **solc 0.8.38 compiles the snippet before it is shown**; if it fails twice, the recipe's generic version is shown and labelled | Fun, and it is where the "why open" of Solidity itself (open compiler, open history) lands |
| **F5. Comic-like animated UI template made by a Claude agent; Hermes (open weights) picks a contract on a schedule, generates the story, renders an artifact** | **Yes, if the template is modest.** | Claude Code builds `template/` once: static HTML + CSS animations (panel layout, a storyteller and a flying-ghost sprite as inline SVG, a summary card: name, era, born, last seen, balance, kind of ghost, verdict). The CLI fills it from `story.json` → `gallery/<address>.html`. Hermes profile `ghosts`: `mcp_servers.ethereum_history.url` for free questions and the daily pick (`get_contract_of_the_day` or `browse_contracts` at random), one skill with one command (`ghosts haunt --random`) that runs the whole pipeline, a cron that runs it daily and drops the file (and posts the path or link to Discord **only if the author restarts the gateway**; the Week 3 memory says restart only on the author's word) | Direct hit on the brief ("open-source agent harness", "running inference locally"). **Honest line for the post:** the template was designed with a closed model at build time; every story at runtime is Gemma 4 12B on the Mac |
| **F6. Wayback screenshot of the dapp** | **Likely, 1-2 h, not yet proven.** | CDX → pick first 200-status capture and the last before death → Playwright headless Chromium renders the archived page with the Wayback toolbar hidden → PNG into the comic's "in life" panel. Only for contracts with a known site (EH `links`, or the author's own list) | Nice: the ghost's "face" |

**What has to be cut to fit 51 hours:** no interactive séance (eth_call question answering) from the Week 4 brainstorm, no author-bookmark scan; the ghosts come from the archive's documented set plus a short hand-picked list of famous ones. Gallery target: **8 ghosts** (4 friendly, 4 bad with busters), one rendered by the Hermes cron on camera.

## 3. Partner tools around the idea

| Partner | Use here | Verdict |
| --- | --- | --- |
| **Gemma** (featured) | Gemma 4 12B QAT on Ollama writes every story, scary tale, buster tale and fix adaptation; `embeddinggemma:300m` for "ghosts like this one" | **In, core** |
| **Tiger Data** | Postgres: ghosts, facts, stories, Slither findings, embeddings (pgvector) and the per-year activity series (a hypertable) behind the life chart; hybrid search "which ghosts had reentrancy" | **In** if it costs under 1.5 h (Week 2-3 code patterns, rewritten) |
| **.tech domain / Render** | Publish the gallery (static) at a .tech name; Render static site for free | **In if the author wants it; ask before claiming the domain** (free first year, renews at $29.99) |
| **ElevenLabs** | The storyteller reads the comic aloud (opt-in button, closed and online; say so) and narrates the demo video | **Optional**, 30-45 min, last |
| **Browserbase (Stagehand)** | Stagehand `extract` of the dapp's tagline from the archived page with local Gemma | **Out**: plain Playwright does the screenshot; claiming the category for that would not be meaningful |
| **Sentry Agent Tracing** | Trace the Hermes runs (latency, tokens) | Out (no time; Hermes has no first-hand tracing path in the wiki) |
| **Entire** | Share agent sessions behind the build | Out unless trivial at the end |
| **TabPFN** | Predict "will it die within a year" from early activity | Out (good follow-up) |
| Temporal, Auth0, SerpApi, MongoDB, Mastra, Copilot, Ultramarine, Arduino, DigitalOcean, Tinker, Backboard | No real use | Out |

Credits at hacktoberfest.com/my/promos: ask before claiming anything.

## 4. Clock (local time, UTC-5)

| When | Milestone |
| --- | --- |
| Wed 23:00 → Thu 01:00 | M0: repo skeleton, `facts` layer (EH, Sourcify, Blockscout, RPC, CDX) with caching, 3 ghosts summoned |
| Thu 09:00 → 13:00 | M1: classification, Slither tier and catalog tier, story generation with the fact verifier |
| Thu 13:00 → 17:00 | M2: comic template, renderer, gallery of 8; Wayback screenshots |
| Thu 17:00 → 21:00 | M3: Hermes profile (MCP, skill, cron), Tiger Data store, one on-camera daily run |
| **Thu 23:00** | **Feature freeze**; screenshots, README, post draft, agent session |
| Fri 00:30 → 01:30 | Publish (safe deadline 01:59). The page deadline (Sun 01:59) is margin for post edits only |

Kill rules: if the fact verifier rejects more than half of Gemma's sentences by Thu 13:00, drop chapters to one paragraph per ghost. If Hermes cannot drive the pipeline by Thu 21:00, the cron runs the CLI directly (`--no-agent`) and the post says the agent only picks and posts.

## 5. Questions for the author

1. Restart the Hermes gateway for Discord delivery, or run the ghost agent on the CLI and cron only?
2. Claim a .tech domain for the gallery (ask before claiming), or keep it on GitHub Pages?
3. ElevenLabs narration as a stretch, yes or no?
4. Any contracts you want on the altar (ones your 2017 self touched), given privately and never committed?

## 6. Feedback round 1 (2026-10-29 04:40Z, Wed Oct 28 23:40 local)

### 6.1 Deadline: verified, Sun Nov 1, 01:59 local

The page and contest rules say "October 31 at 11:59 PM PDT". US daylight time ends Nov 1 at 02:00 local Pacific, so Oct 31 is still PDT (UTC-7): **Oct 31 23:59 PDT = Nov 1 06:59 UTC = Sun Nov 1 01:59 at UTC-5** (computed with `zoneinfo`, America/Los_Angeles → America/Guayaquil). The author's reading is right, and it matches the Week 3 decision to follow the page. The DEV Events API `ends_at` is a day earlier (Oct 31 06:59 UTC, Sat 01:59 local). Risk, stated once: Week 3 was published after the API time and before the page time; whether DEV counted it is unknown until winners are announced (week of Oct 26). **Clock reset below to the page deadline, 75 hours from this note.**

### 6.2 Hermes: park the old agents, run only the new profile

Yes, without deleting anything. Hermes v0.22.5 docs (`multi-profile-gateways.md`, "Stopping one profile without stopping the host"): `hermes -p <profile> gateway stop` writes a `gateway.parked` marker in the profile home; the host then skips that profile's adapters **and its cron jobs**; the marker survives host restarts; `gateway start` on the profile removes it. State on this Mac tonight: the host gateway is **not running**; `rc-parts` is already parked; `sloth-curator`, `sloth-coordinator`, `sloth-worker` are not parked (they went offline when the host stopped on Oct 26). The default profile's `.env` holds no bot token (only terminal and browser settings), so starting the host from the default profile brings **no** old bot online. Plan, on the author's word: park the three sloth profiles (three commands), install the new `ghosts` profile, then `hermes gateway run` (or `install` + `start`). The ghosts profile needs its own Discord bot token if Discord delivery is wanted; otherwise it runs cron-only and the gallery is the delivery.

### 6.3 Gallery as a static web app on Vercel at eth-ghosts.decentraminds.tech

Feasible and cheap. Verified: Vercel CLI 62.2.0 is installed and logged in as the author; `decentraminds.tech` is in the author's Vercel account (registrar "Third Party", nameservers `ns1/ns2.vercel-dns.com`), so a subdomain is one project-domain assignment and Vercel DNS writes the record itself; no registrar login needed. Design:

- `web/` in this folder: a framework-free static site. `web/ghosts/<address>/index.html` (the comic artifact), `web/ghosts/index.json` (the index the home page reads: address, name, era, kind, born, last seen, cover image), `web/index.html` (the gallery with filters: friendly, bad, era), `web/assets/` (template CSS, sprites, screenshots). A tiny build script regenerates `index.json` from the ghost folders.
- Deploy on every new story: the cron's last step runs `vercel deploy --prod --yes` from `web/` (token in the profile `.env`; project linked once with `vercel link`), so a new ghost is live in about a minute. Git is not in the loop at runtime, which keeps commits meaningful; the generated ghosts are also committed at checkpoints so the repo holds the gallery.
- Monorepo: the Vercel project's root directory is `challenges/05-week4-ghost-in-the-machine/web` with framework "Other" and no build command (or the build script).
- Partner note: the ".tech Domain" category asks for a domain **claimed through Hacktoberfest**. If `decentraminds.tech` was claimed through Hacktoberfest (this year or an earlier one), the author can enter it; if not, the site still goes there and the category is skipped. Vercel is not a partner; Render would have been. The author's call stands.

### 6.4 ElevenLabs

Deferred to after V1 of the prototype, as a storyteller voice. Not in the plan before the freeze.

### 6.5 Why 2015-2017, and how to reach 2015-2023

Only because the Ethereum History archive stops at Spurious Dragon (early 2017): its eras are frontier, homestead, dao-fork, tangerine-whistle, spurious-dragon, and its 1.37 M contracts and 4,127 historian stories are all from that window. Everything else in the pipeline (Blockscout for death and balance, Sourcify for source, Slither for wounds, Wayback for the face, Gemma for the story) works for any year. Expanding to 2023 means adding two pickers:

| Picker | Years | Source (checked) | Gives |
| --- | --- | --- | --- |
| **Archive** | 2015-2017 | Ethereum History API and MCP | Random or daily documented contract with a historian's story |
| **Incidents** | 2017-2020 curated, 2021-2023 machine-readable | **DeFiHackLabs** (`past/2021/README.md` 65 incidents, `past/2022` 192, `past/2023` 436; each entry has date, name, vulnerability class, loss, a PoC `.sol` under `src/test/<year-month>/` that names the victim addresses, and a write-up link); 2017-2020 from a short hand-written catalog (Parity multisig, Fomo3D, Bancor, dForce, Harvest…) | **Bad ghosts** with a known cause, so the scary story and the fix have a real reference, not only Slither's opinion |
| **Random block** | 2018-2023 | A public RPC that still serves old blocks: **dRPC** (`eth.drpc.org`) answered `eth_getBlockByNumber` for block 7,000,000 with full transactions; **publicnode has pruned history before block 15,500,000** (error 4444), llamarpc, cloudflare and ankr refused. Contract creations are rare: 1 in 6 sampled blocks tonight (a 2022 token, verified on Blockscout); so sample 60-100 blocks per draw, keep verified and named ones | **Friendly ghosts** nobody chose: forgotten tokens and one-off contracts, which is on theme |

Era labels become hard-fork ages for every year (Frontier, Homestead, Byzantium, Constantinople, Istanbul, Berlin, London, the Merge, Shanghai), decided from the block number in code. Cost: about 3 hours more than the 2015-2017 plan (DeFiHackLabs parser with address extraction from the PoC, block sampler, hard-fork table). Honest line: for 2018-2023 there is no historian prose, so the life story leans on code facts, the source's comments and the archived website; the post says which ghosts had a historian and which did not.

### 6.6 Clock, reset to the page deadline (local time, UTC-5)

| When | Milestone |
| --- | --- |
| Wed 23:40 → Thu 01:30 | M0: repo skeleton, facts layer (EH, Sourcify, Blockscout, dRPC, CDX) with caching, 3 archive ghosts summoned |
| Thu 09:00 → 14:00 | M1: classification, Slither tier, incident catalog, story generation with the fact verifier, fix snippets compiled with 0.8.38 |
| Thu 14:00 → 20:00 | M2: comic template (Claude Code), renderer, `web/` gallery, first Vercel deploy at eth-ghosts.decentraminds.tech |
| Fri 09:00 → 14:00 | M3: DeFiHackLabs and random-block pickers, hard-fork ages, Wayback screenshots |
| Fri 14:00 → 20:00 | M4: Hermes `ghosts` profile (MCP server, skill, cron → render → deploy), old profiles parked, one on-camera daily run; Tiger Data store if under 1.5 h |
| Sat 09:00 → 15:00 | M5: 10+ ghosts across 2015-2023, screenshots, README, agent session, post draft staged |
| **Sat 15:00** | **Feature freeze** (Week 3 missed its freeze; this one is the rule) |
| Sat 22:00 | Publish target; hard deadline Sun 01:59 |

Kill rules unchanged (section 4), plus: if the random-block picker yields fewer than 3 verified ghosts in 10 minutes of sampling by Fri 12:00, the 2018-2023 friendly ghosts come from a hand-picked list and the post says so.
