# A ghosts in the decentralized world computer

> Old Ethereum contracts whose dapps are gone but whose code still answers, each told as a short comic by an open-weight model running on my Mac, from facts that code checked first.

**Gallery:** https://eth-ghosts.decentraminds.tech · **Post:** staged as a draft on DEV (article 4944855) on 2026-10-30, to be published before the deadline; the draft text is [SUBMISSION.md](SUBMISSION.md)

**Challenge:** [Hacktoberfest Open-Source AI Challenge: Week 4, Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26) (DEV event 82) · **Window:** Oct 26 19:00 → Nov 1 06:59 UTC · **Tags:** `#hf26challenge` `#devchallenge`

A contract on Ethereum cannot leave. The team moves on, the website goes dark, the Discord empties, and the code stays at its address, still answering anyone who calls it. Some of them are still being called in 2026 by people who never got the memo. That is my reading of "ghost in the machine", and of Día de los Muertos: remember what was built and by whom, before it fell silent.

## What it does

For one contract address, the `ghosts` CLI:

1. **Gathers the facts with code.** [Ethereum History](https://www.ethereumhistory.com) gives the birth (deployer, block, time), the decompiled code and, for documented contracts, a historian's story. [Sourcify](https://sourcify.dev) gives verified source. [Blockscout](https://eth.blockscout.com) gives the calls, the last successful call, the balance and the activity of the last 12 months. A public JSON-RPC node says whether the code is still on chain. The [Internet Archive](https://web.archive.org)'s Wayback CDX lists captures of the dapp's website. Everything lands in `data/ghosts/<address>/facts.json`. The age is the hard fork of the birth block (Frontier, Homestead, Byzantium, ...).
2. **Finds its wounds.** For verified source compiled with solc ≥ 0.4, [Slither](https://github.com/crytic/slither) runs on it, with the right compiler installed on demand by solc-select. A hand-written catalog of 10 incidents from 2016-2020, each with its references, confirms known hacks (TheDAO, Rubixi, King of the Ether Throne, ...). Older source gets regex checks (`call.value`, unchecked `send`, a misnamed constructor, ...), and those findings are labelled **suspected**, never confirmed.
3. **Decides what kind of ghost it is, in code:**
   - **banished**: the code is gone (self-destructed). Only a gravestone.
   - **bad**: a cataloged incident, or a High-impact Slither finding with at least Medium confidence. This wins over everything but banished. Medium findings are **scars**: they are counted and mentioned, but they do not make a ghost bad.
   - **alive**: 100 or more successful calls in the last 12 months, or at least 5 % of its lifetime calls. Not a ghost yet, so the pickers skip it.
   - **lingering**: some calls in the last 12 months, below that bar, while the dapp is gone. The platform died; people still knock.
   - **friendly**: no successful call for 2 years or more, and no fatal wound. A contract nobody ever called is friendly too, unless it is bad.
4. **Tells its story.** Gemma 4 12B (`gemma4:12b-it-qat`, open weights, Apache 2.0) runs locally through [Ollama](https://ollama.com), with thinking off. It writes one chapter per call, seeing only that chapter's facts: birth, life and silence (or "the knocking" for lingering ghosts), and for bad ghosts a first-person haunting and a ghost-buster chapter. A **lexical verifier** then checks every sentence: each year, date, number, ETH amount, multi-word name, identifier and quote must exist in the facts, verdict or wounds. A sentence that fails gets one rewrite; if the rewrite fails too, it is dropped and shown struck through on the page.
5. **Shows a fix, when one exists.** There are 14 hand-written fix recipes (checks-effects-interactions with a lock, checked `call`, the `constructor` keyword, ...). The model only picks which names in the old contract match the recipe's names; code applies the renames, checks that the cure is still there, and solc 0.8.38 must compile it before it is shown. When no recipe fits (most hacked DeFi protocols: oracle, governance or logic flaws), the buster says no compiler upgrade fixes this, gives general advice, and shows no code.
6. **Renders a page** from a comic template: a calavera storyteller named Doña Gwei with a candle, a sheet ghost whose face follows its kind (a happy contract block flies in the early chapters, so you see when it turned), the ofrenda card with the facts, the guilty code with real line numbers, the fix with its compile result, a timeline, the verifier tally, and Wayback screenshots of the dapp when a site is known. Pages are self-contained HTML (no CDN), about 48-61 KB each.
7. **Adds it to the gallery**, a framework-free static site in `web/` with filters by kind and age, deployed to Vercel.

**Three pickers** find ghosts when you don't give an address: the Ethereum History archive (documented contracts from 2015-2017, with a `daily` seed), [DeFiHackLabs](https://github.com/SunWeb3Sec/DeFiHackLabs) incidents from 2021-2023 (mainnet only, victim verified on Blockscout), and random blocks from 2016-2023 through the keyless dRPC node (the first verified, named contract created in a sampled block).

**A Hermes profile** (`hermes/`) packages it as an agent: the [Hermes Agent](https://github.com/NousResearch/hermes-agent) profile `ghosts` talks to Gemma through Ollama, connects to the Ethereum History MCP server, has one skill (`ghost-stories`), and ships two script-only cron jobs, installed paused: `ghost-of-the-day` (daily 09:00) and `weekly-incident` (Mondays 10:00). On my Mac it runs live since 2026-10-29: the Hermes host is a launchd user service with the `ghosts` Discord bot connected, both crons are active, and the old profiles are parked. Its first haunt (`haunt.sh --source archive --seed daily --deploy`) picked a 2016 forwarding wallet nobody ever called, "The Silent Small Half" (`0xc820366606e803339730ad88465998f470116adf`), deployed it as the 26th ghost and the featured story, and posted its report line to the Discord home channel. The report line is built by code, not by the model. Discord is optional; without it the gallery is the delivery. Setup and its honest limits: [docs/HERMES.md](docs/HERMES.md).

## Why open matters here

- **The storyteller is a file on my disk.** Gemma 4 12B runs in Ollama on my M4 Max. No API key, no per-story bill, no service that can retire the model under me. Any other Ollama model is one environment variable away (`GHOSTS_MODEL`).
- **The checks are plain code you can read.** The kind of ghost, the wounds, the verifier and the compile gate are Python, Slither and solc, not a model's opinion. A small local model is good enough because it never decides a fact; it only words facts that code already holds.
- **The subjects are open and permanent.** Contract code and its history sit on a public chain; the source is verified in public registries; the archive's stories are public. A ghost can be re-told by anyone, any time.
- **Nothing needs a key.** Every source answers anonymously. Keys only raise rate limits.

The honest counterweight:

- **It is not offline.** Ethereum History, Blockscout, Sourcify, the public RPC nodes and the Internet Archive are online services. The model and the data on disk are local; the pipeline is not. Answers are cached under `data/cache/`.
- **The comic template was designed with a closed model** (Claude Code) at build time. Every story on the altar is written at runtime by Gemma.
- **The verifier is lexical.** It proves that the dates, numbers and names came from the facts, not that each sentence is true. Gemma's remaining mistakes are semantic (more in Limits).

## Numbers

All from [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md) and the lane logs in [docs/lanes/](docs/lanes/), measured 2026-10-29 on an Apple M4 Max 64 GB with `gemma4:12b-it-qat`, `think: false`, `num_ctx` 8192.

| What | Number | Method |
| --- | --- | --- |
| Ghosts on the altar | **26**, born 2015-2023 | count of `data/ghosts/*/verdict.json` and the live gallery index |
| Kinds, first 25 | **13 bad, 7 friendly, 5 lingering**; 3 never called, 8 with scars, 9 with a historian's story; the 26th is friendly and never called | `verdict.json` kind, scars and labels |
| Verifier, final stories | 540 sentences on 18 re-told ghosts: **536 grounded, 4 repaired, 0 dropped** | `story.json` verifier fields; the 4 repairs were verifier mistakes, since fixed |
| Verifier, first batch | 599 sentences on 21 ghosts: 10 repaired, **1 dropped**, a real invention: "eleven other scars" on a contract with one | `story.json` from that batch run |
| One whole haunt | 20-80 s per ghost; the story step 10-42 s | `haunt.json` step timings, first batch |
| First live haunt through Hermes | **28 s** end to end, pick to deploy ("The Silent Small Half", friendly) | the profile script's `last-haunt.txt` and the live index |
| Slither | 2.6 s for StandardBounties (solc 0.4.18) | `ghosts wounds`, Slither 0.11.6 |
| Incident pool | 10 cited catalog incidents (2016-2020); 143 verified mainnet victims from DeFiHackLabs (2021-2023) | `ghosts/catalog/incidents.json`; `ghosts incidents fetch` |
| Random picker | a verified, named contract within 1-17 blocks for 2018-2023; 2016-2017 needed 181-886 blocks | `ghosts pick --source random --year N`, one try per year on dRPC |
| Fix recipes | 14, all compile with solc 0.8.38 | `solc --bin` per recipe (offline test) |

CryptoPunks, MoonCatRescue and Etheria came out **alive** (still in real use) and were skipped.

## Run it

Tested on macOS on Apple Silicon (M4 Max) with Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/). Other platforms are untested.

1. **Install.**
   ```bash
   uv sync
   uv run playwright install chromium        # only needed for `ghosts face` (Wayback screenshots)
   uv tool run --from solc-select solc-select install 0.8.38   # the compile gate for fixes
   ```
   Slither and solc-select run through `uv tool run`, so there is nothing else to install; the old compiler a contract needs (0.4.x, ...) is installed on demand the first time Slither meets it.

2. **Local model.**
   ```bash
   ollama pull gemma4:12b-it-qat
   ```

3. **Optional settings.** `cp .env.example .env` and fill what you want. Nothing loads `.env` by itself; export it in your shell with `set -a; source .env; set +a`. Every key is optional.

4. **Haunt a ghost.**
   ```bash
   uv run ghosts haunt 0x2af47a65da8cd66729b4209c22017d6a5c2d2400 --site bounties.network --site gitcoin.co
   uv run ghosts haunt --source archive --seed daily     # today's pick from the archive
   uv run ghosts haunt --source incident --year 2022     # a hacked protocol
   uv run ghosts haunt --source random --year 2019       # a contract nobody chose
   ```
   `haunt` runs pick → summon → wounds → classify → face → story → render → gallery build, writes `haunt.json`, and skips steps whose output exists (`--force` redoes them). `--deploy` also publishes. The page lands in `web/ghosts/<address>/index.html`; open it in a browser.

5. **One step at a time**, if you want to look inside:
   ```bash
   uv run ghosts pick --source archive --year 2016 --dry-run
   uv run ghosts summon <address> --site <host>
   uv run ghosts wounds <address>
   uv run ghosts classify <address>
   uv run ghosts face <address>
   uv run ghosts story <address>
   uv run ghosts render <address>             # or: ghosts render-all
   uv run ghosts incidents fetch              # DeFiHackLabs 2021-2023 into data/incidents/
   uv run ghosts gallery build                # web/ghosts/index.json and web/sitemap.txt
   ```

6. **Publish the gallery.** `scripts/deploy.sh` rebuilds the index and runs `vercel deploy --prod` from `web/`. It uses your Vercel CLI login, or `VERCEL_TOKEN` when set. Link your own project first (`cd web && vercel link`).

7. **Tests.** `uv run pytest`. They are offline: fixtures, a fake model, a stubbed Ollama.

8. **The agent.** `hermes/install.sh --dry-run --yes`, then follow [docs/HERMES.md](docs/HERMES.md) to install the `ghosts` profile, fill its own `.env` (Discord names live in `hermes/.env.example`) and resume the crons. It never starts the gateway or resumes a cron for you. The bot needs View Channels and Send Messages in the home channel, or the report post fails with Discord 403 "Missing Access".

No login is needed to see the demo: the gallery is public.

## How it was built

One coordinator session (Claude Code) wrote the lane contracts in [docs/LANES.md](docs/LANES.md) (owned paths, file schemas, the taxonomy) and handed the work to worker lanes: A-G for the pipeline, C1-C3 for the template and gallery, H for this README, I for the post, J-L for the author's gallery feedback rounds (shared header and audio, favicon and pagination, the first-visit welcome), M-O for the post's diagram, screenshot and agent session; Opus for the design and correctness lanes and Sonnet for the plumbing. Each lane logged its measurements and failures in [docs/lanes/](docs/lanes/). The retrospective is in the knowledge base: [retrospective-week4-ghost-in-the-machine.md](../../knowledge-base/hacktoberfest-2026/raw/retrospective-week4-ghost-in-the-machine.md). Feasibility checks and decisions are in [docs/ASSESSMENT.md](docs/ASSESSMENT.md) and the running log in [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md).

## Limits

- **Lexical, not semantic.** The verifier passes a sentence whose tokens all exist in the facts even when the relation is wrong. Seen in real output: an ownership-transfer feature invented for King of the Ether Throne, "for" instead of "by" on who deployed it, a balance tied to a theft it had nothing to do with. A number is matched against every fact, not the one the sentence means. Single capitalized words and one-digit numbers are not checked.
- **Suspected is not confirmed.** Regex findings on pre-0.4 source never make a ghost bad. TheDAO's source comes from the archive's `source.eh.sol`, not a bytecode-matched verification.
- **Scars are not hacks.** StandardBounties has 5 Medium Slither findings, none fatal, and no documented exploit. It is lingering: people still call it in 2026.
- **Incident ghosts are often a part, not the whole.** The DeFiHackLabs victim address is a hint after filtering well-known addresses; we may hold a token, a proxy or a router. The page tells the story of the contract we hold and says its part in the incident. All 7 incident ghosts have design-flaw wounds with no recipe, so their buster shows no code, and the advice is hand-written per kind of flaw, not taken from each post-mortem.
- **A compiler version fixes little by itself.** Only 4 recipes are enforced by the compiler (constructor names, overflow, uninitialized storage, shadowing). "Compiled" means solc 0.8.38 built it, not that it is audited. A fix is a minimal pattern, not a patched copy of the old contract.
- **Thin stories for strangers.** Ghosts born after 2018 have no historian prose, and random picks have no known website, so they have no screenshots and no proof that a dapp died; their ghostliness is silence alone.
- **Pickers.** The archive's `daily` seed mimics the MCP server's "contract of the day" but is not the same rotation. The incident chain filter trusts the network named in each PoC. About 63 % of DeFiHackLabs entries are on other chains and are dropped.
- **Counting calls.** Blockscout's counter answers 0 for contracts it never counted, so a zero is checked against the transaction list. "Never called" counts direct transactions only; a contract called only by other contracts would look never called.
- **Snapshots.** Balances and counts are read at summon time, not live.
- **Wayback.** archive.org has no screenshot API; we render the archived page with Playwright. Some captures render partly (missing CDN assets).
- **The agent.** The delivery path ran live once on 2026-10-29: host service, the profile's `haunt.sh`, `ghosts haunt --deploy`, the gallery, the Discord report. Still untested: a Discord conversation with the agent (Gemma choosing the `ghost-stories` skill) and the Ethereum History MCP call from inside Hermes. A bot invited without access to the home channel connects fine but its report post fails with Discord 403 "Missing Access" (code 50001); give it View Channels and Send Messages there. Its deny rules are a command policy, not a sandbox; the agent runs as my macOS user.

## Credits

- [Ethereum History](https://www.ethereumhistory.com) by cartoonitunes: the archive of 2015-2017 contracts, its historians' stories, its REST API, MCP server and skills. The pipeline stands on it.
- [Blockscout](https://eth.blockscout.com) and [Sourcify](https://sourcify.dev): keyless chain data and verified source.
- The [Internet Archive](https://web.archive.org): the Wayback Machine keeps the dapps' faces.
- [DeFiHackLabs](https://github.com/SunWeb3Sec/DeFiHackLabs) by SunWeb3Sec: the incident records and PoCs behind the 2021-2023 bad ghosts.
- [Slither](https://github.com/crytic/slither) and [solc-select](https://github.com/crytic/solc-select) by Trail of Bits; the Solidity compiler.
- [Ollama](https://ollama.com), and [Gemma](https://ai.google.dev/gemma) by Google (Apache 2.0).
- [Playwright](https://playwright.dev) for the screenshots; [Vercel](https://vercel.com) hosts the gallery; [Hermes Agent](https://github.com/NousResearch/hermes-agent) runs the agent profile.
- The comic template was designed with Claude Code (closed model), once, at build time.

## Post-deadline commits

None yet. Any commit after Nov 1 06:59 UTC will be listed here.

## License

MIT, see [LICENSE](LICENSE).
