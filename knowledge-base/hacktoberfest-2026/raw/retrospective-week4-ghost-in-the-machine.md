# Retrospective: Week 4 "Ghost in the Machine" (Eth Ghosts)

Written 2026-10-30 about 00:30 local (05:30 UTC, UTC-5), right after staging. Source of truth for the details is the project's running log, `challenges/05-week4-ghost-in-the-machine/docs/CHALLENGE-MEMORY.md`, with the lane logs in `docs/lanes/`. The post is **staged as a draft on DEV (article 4944855), not published**. Publish target is Sat Oct 31 22:00 local; the page deadline is Sun Nov 1 01:59 local (Nov 1 06:59 UTC). The agent session (1294) is public and `main` is pushed. The outcome is not known.

## What was built

Eth Ghosts ("Ghosts in the Decentralized World Computer"): an altar of old Ethereum contracts that still sit on chain after their dapps died. A Python pipeline (`ghosts haunt`) picks a contract, gathers its facts, finds its wounds, decides what kind of ghost it is, and has a local model tell its story as a comic page. The storyteller is Doña Gwei, a catrina-style elder, chosen by the author from six names.

The chain in code: pick, summon, wounds, classify, face, story, render, og, gallery, deploy. Three pickers feed it: the Ethereum History archive (documented 2015-2017 contracts, daily seed), DeFiHackLabs incidents, and random blocks from dRPC. Facts come from five keyless, cached sources: Ethereum History, Sourcify, Blockscout, a public RPC and Wayback CDX. Wounds come in three tiers: Slither 0.11.6 on verified source (solc 0.4 and later), a catalog of 10 cited incidents from 2016-2020, and regex on older source, labelled "suspected". Code decides the kind: banished, bad, alive, lingering, friendly. Medium findings are scars, not a death sentence.

Gemma 4 12B QAT through Ollama, thinking off, writes every story at runtime on the author's M4 Max. A lexical verifier checks that every year, date, number, ETH amount, multi-word name, identifier and quote exists in the facts; a failing sentence gets one repair call, then is dropped. Bad ghosts get a buster chapter and a fix from 14 hand-written recipes: Gemma picks names, code checks them, and solc 0.8.38 compiles the result. The comic template was designed once with Claude Code (closed) at build time; no model touches it at render time.

The pages land in a static gallery on Vercel at eth-ghosts.decentraminds.tech, a .tech domain claimed through Hacktoberfest. A Hermes Agent profile, `ghosts`, runs the haunts on two crons (ghost of the day, weekly incident), reads the Ethereum History MCP server, and posts a report line to Discord. Its deny rules are a command policy, not a sandbox.

Altar at writing time: 26 ghosts, 8 friendly, 5 lingering, 13 bad; 4 never called, 8 scarred, 10 with a historian's story. Categories entered: Gemma and .tech Domain. Tiger Data was not built; ElevenLabs was deferred.

Not open: Vercel (hosting), Discord (report line), and Claude Code for the template. The data sources are online services, so the project is not offline; only the model and the data on disk are local.

## Timeline (author's local time, UTC-5)

Times come from the memory log. Its stamps were written by the coordinator and drift from git's clock on Oct 29 (the first commit is stamped 15:30 in the log, 13:52 in git), so read them as approximate. Commit times below are git's.

- Oct 26, 14:00: window opened.
- Oct 26, 17:40: folder scaffolded. The DEV API and the page disagreed on the deadline by a day, again.
- Oct 26, 18:10: brainstorm from the wiki first, then DEV. Three ideas, a recommendation ("the contract still answers"), and a kill rule for Tue 09:00. Feasibility checked with curl the same night.
- Oct 28, 23:00: the author chose idea 1, about 75 h before the page deadline, with his own nuances: friendly vs bad ghosts, a buster story with a fix in Solidity 0.8.38, a comic template, a Hermes agent on open weights.
- Oct 28, 23:40: deadline fixed to the page's; freeze set for Sat 15:00, publish Sat 22:00. Scope widened to 2015-2023 with two new pickers.
- Oct 29, 00:00-00:40: .tech category confirmed; StandardBounties picked as the first ghost and found still in use, which created the "lingering" kind; M0 (sources, cache, `summon`) done.
- Oct 29, 01:15: orchestration decided. Five lanes launched at once: A verdicts, B stories, C1 template, C2 gallery, D pickers.
- Oct 29, 01:40: empty gallery live on the .tech domain.
- Oct 29, 03:35: CP1. All commands wired; 4 real ghosts live.
- Oct 29, 04:20-05:40: Lane E built the Hermes profile; Lane G built `ghosts haunt` and a batch of 21 ghosts.
- Oct 29, 08:05: CP2. 25 ghosts live; claims table filled.
- Oct 29, 08:40-09:15: README (Lane H) and the post draft (Lane I).
- Oct 29, 11:30: author asked for the Hermes profile now, plus gallery feedback round 1 (Lane C3).
- Oct 29, 12:45-13:20: host started; first live haunt through the profile script in 28 s; the Discord report failed on a 403, then posted once the author fixed the bot's channel access.
- Oct 29, 13:52: first commit (git), local only.
- Oct 29, 14:50: link-preview cards on every page.
- Oct 29, 16:35-18:30: feedback rounds 2-4: shared header and audio (Lane J), Doña Gwei, favicon and pagination (Lane K), first-visit welcome (Lane L). Committed 17:55 and 17:58 (git).
- Oct 29, 22:10-23:30: post reviewed against the claims table; "Why open" rewritten on the author's brief; architecture diagram (Lane M), a screenshot (Lane N), session curated (Lane O).
- Oct 29, 23:42-23:50: post and assets committed; session 1294 submitted; DEV draft 4944855 staged.
- Oct 30, 00:05-00:25: title changed on DEV; `main` pushed; images repinned; session made public.

## Week 3 lessons, applied

- **Choose the idea within a day.** Partly. The brainstorm came 4 h after the window opened, with a recommendation and a kill rule. The decision still waited two days, until Oct 28 23:00. That left about 75 h to the deadline, against about 50 h in Week 3.
- **Claims table in the first hour.** Partly. HONEST entries went in with the pick (online sources, closed template, deny rules not a sandbox). The table itself was filled at CP2, about 9 h into the build. It then did its job: StandardBounties is never called hacked, the verifier is never called proof, and the "Hermes has not run live" row was superseded by a dated entry instead of quietly dropped.
- **Freeze with margin.** Yes. The freeze was set for Sat 15:00. The draft was staged about 40 h before that freeze and about 50 h before the deadline.
- **Measured demo before the freeze.** Yes. The first live haunt (28 s, the 26th ghost, deployed and reported to Discord) ran on Oct 29.
- Also carried over: Hermes alias at 64k context, skill-first rule in SOUL.md, old profiles parked before starting the host, images pinned to a commit.

## What worked

- **Coordinator plus worker lanes, by complexity.** One session wrote the lane contracts (`docs/LANES.md`: owned paths, schemas, the taxonomy) and never coded; sixteen worker lanes built (A-E, G-O, with C split in three; there was no lane F). Opus took design and correctness (verdicts, stories, template, README, post, diagram); Sonnet took plumbing (gallery, pickers, Hermes profile, haunt, favicon, screenshots, session curation). Timed first deliveries ran from 35 s (N) to 56 min (G); together about 3.5 h of agent time, follow-ups not timed.
- **The model does language, code does facts.** Gemma never decides a date, a kind, a vulnerability or a line of fixed code. On the final runs the verifier checked 540 sentences on 18 ghosts: 536 grounded, 4 repaired, 0 dropped. Its first real catch was "eleven other scars" on a contract that has one.
- **Fixes as recipes, not generation.** Gemma only picks names from the old source; code renames a hand-written recipe, checks role, arity and job, verifies the cure pattern and compiles with 0.8.38. Where no recipe fits (the hacked protocols' design flaws), the buster says so and `fix` is null.
- **Thinking off.** One schema-constrained sentence took 20.1 s with thinking on (about 1,000 thinking tokens). With `think:false` a whole story ran 14-41 s.
- **Checkpoints and early deploys.** The gallery was public from the first night, so every round was checked on the live site.
- **The author's feedback rounds.** Four rounds turned a working gallery into a place: papel picado, story of the day, a flying ghost, audio, Doña Gwei, preview cards. The first-visit welcome ("Hunt the ghost" on the index, "Light the candle" on ghost pages) turns the browser autoplay rule into part of the story: the first click lights the page and starts the music.
- **Keyless sources.** None of the six sources asked for a key or an account. Ethereum History's MCP server worked as a side door for the agent.

## What went wrong or cost time

- **Two days to decide.** The idea sat from Oct 26 to Oct 28; the kill rule's Tuesday deadline passed without a switch or a choice.
- **A deploy before review.** The coordinator ran `render-all` and deployed while Lane G was still writing; the live gallery jumped from 4 to 18 ghosts, two of them facts-only pages. Rule since: no render or deploy while a lane writes under `data/ghosts`.
- **Blockscout's zero.** Its transaction counter returns 0 for contracts it never counted, and `tx_count` counted only calls, so 9 of 25 ghosts read as never called and stories said "last call on the day it was born". The verifier passed it because the number was in the facts. Checking zeros against the transaction list found real calls in 6 of the 9.
- **Medium findings as fatal.** The first rule made StandardBounties "bad" with no documented exploit. Medium became scars.
- **Incident picks.** All came out bad even when heavily used, the contract held was often a token or helper, and the buster still claimed 0.8.38 "seals" the wound. Fixed with honest busters and "its part in the incident" wording.
- **Lexical only.** Gemma's remaining errors are semantic: an invented ownership-transfer feature for KotE, "for" vs "by" on who deployed the throne. The verifier cannot see them.
- **Small API traps.** Slither refused Sourcify's standard JSON until run from the sources folder. Wayback reduced a tweet URL to all of x.com. Ethereum History's per-contract URL is singular (`/contract/`); the plural 404s. Vercel rejects header sources with alternation groups. A first Vercel deploy stopped at upload.
- **Hermes edges.** `gateway stop` refused to park a profile with no host running; the marker file was written by hand. The bot connected but its first report got Discord 403 "Missing Access" until the author fixed channel permissions.
- **The live altar runs ahead of the repo.** Haunts deploy but never commit, so each cron run adds a ghost the repository does not have. Kept manual on purpose.
- **DEV staging.** The gateway answered "DEV is unavailable" on writes that had succeeded, twice. DEV caches each image at first save, and the first save came before the push, so some images stayed broken although the URLs returned 200. Repinning to a new commit fixed it. The draft title was 130 characters; DEV caps at 128.
- **Clock drift in the log.** Week 3's "use `date -u`" was not kept; Oct 29 stamps drift from git's clock. Two lane logs also called UTC times "local".
- **Headless only.** The welcome, audio, pagination and gallery were checked in headless Chromium, not Safari, Firefox, a real phone or a screen reader. The Discord chat path (Gemma choosing the skill) and the MCP call from inside Hermes are still untested.

## Numbers

- Altar: 26 ghosts born 2015-2023; 8 friendly, 5 lingering, 13 bad; 4 never called, 8 scarred, 10 with a historian. CryptoPunks, MoonCatRescue and Etheria classified alive and skipped.
- Verifier: final runs 540 sentences on 18 ghosts, 536 grounded, 4 repaired, 0 dropped; first batch of 21 ghosts 599 sentences, 10 repaired, 1 dropped.
- Story speed (M4 Max, gemma4:12b-it-qat, think off): 14.1-40.5 s per ghost on the re-told first four; a full haunt 20-80 s in the batch; the first live haunt 28 s end to end.
- Slither: 2.6 s on StandardBounties. Fix recipes: 14, all compiled with solc 0.8.38.
- DeFiHackLabs: 143 verified mainnet victims for 2021-2023; about 63% of entries dropped as non-mainnet.
- Random picker on dRPC: 1 to 17 blocks per draw for 2018-2023; 2016 and 2017 needed 886 and 181 blocks.
- Pages: about 40-90 KB each, self-contained; 26 preview cards in 2.9 s.
- Audio: ambient track 5.66 MB to 1.70 MB after re-encoding.
- Tests: 260 offline, green at staging.
- Post: about 3,250 words, nine images, title 74 characters.
- Session: 3,748 transcript records curated to 50 messages and 350 tool calls.

## Playbook additions

1. Hold the idea decision to the kill rule's date; a recommendation with a deadline still needs a decision on that deadline.
2. Write the claims table with the pick, even if half its rows say "pending", and supersede rows with dated entries.
3. Never render or deploy while a lane writes to the shared data folder; deploy only at checkpoints.
4. Treat a zero from an indexer's counter as unknown and check it against the raw list.
5. Let the model pick names and words; let code assemble anything that must compile or be true.
6. Turn browser autoplay limits into a first-click moment instead of a muted site.
7. Push before the first DEV save, because DEV caches images at that save; if not, repin to a new commit.
8. On the DevRelay gateway, read back after any "DEV is unavailable" before retrying a write.
9. Stamp every log entry with `date -u`, workers included, and say UTC.
10. Test the agent's chat path, not only its scripts, before calling the agent live.
