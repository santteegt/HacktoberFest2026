# Retrospective: Week 3 "Slow and Steady" (Skunkworks Sloth)

Written 2026-10-25 23:35 local (2026-10-26 04:35 UTC, UTC-5), right after publishing. Source of truth for the details is the project's running log, `challenges/04-week3-slow-and-steady/docs/CHALLENGE-MEMORY.md`. Outcome is not known yet: winners are announced the week of Oct 26.

## What was built

Skunkworks Sloth: three Hermes agents on the author's Discord server work through the Chrome "Reading List" folder (1,017 links saved in 2025-2026 "to learn by building", none built). The **Curator** collects, enriches and triages the links with local Gemma into build / read / Valhalla (a removal list the author confirms; nothing is deleted from Chrome). The **Coordinator** asks for a weekly focus, keeps a skunkworks board of cards (mirrored one-way to a private GitHub Project), posts a daily pick and a daily reading link, and renders the second brain as an Obsidian graph. The **Worker** builds the picked card in a two-hour box, writes notes, and pushes a private repo only after `approve`.

Stack: Hermes Agent 0.22.5 (open source) with one multiplexed gateway, three profiles, one Discord bot each, script-only crons; Gemma 4 12B QAT on Ollama (alias `sloth-gemma4-12b`, 64k context) for triage, card wording and reading lines; `embeddinggemma:300m` for the brain taxonomy; Stagehand v4 (Browserbase's MIT SDK) on a local headful Chrome with the local model through a custom LLM callback; Postgres with TimescaleDB on Tiger Cloud (9 tables); a Python CLI `sloth` (uv, typer, pydantic, psycopg). Worker providers: open weights `google/gemma-4-26b-a4b-it` on OpenRouter by default, Anthropic Claude Sonnet 5.5 for `go deep` (closed, labelled and costed), and an allowlisted `go with <model>` picker. The agents ship as Hermes profile distributions with install and export scripts. Not open: Discord, OpenRouter as the host, Anthropic, GitHub, Tiger Cloud.

Post: https://dev.to/santteegt/skunkworks-sloth-a-set-of-agents-automating-my-bookmarks-review-keeping-me-focused-and-growing-my-1168 (published by 2026-10-25 23:32 local, 2026-10-26 04:32 UTC, about 2 h 27 min before the deadline). Ten annotated screenshots instead of a demo video; seven diagrams; agent session embedded. Partner categories entered: Gemma, Browserbase, Tiger Data. Auth0 (Gmail source) was planned and moved to runner-up; it never ran.

## Timeline (author's local time, UTC-5)

- Oct 19, 15:46: folder scaffolded inside the window. The page and the DEV API disagreed on the deadline by a day; the author followed the page (Oct 26 06:59 UTC).
- Oct 19-20: the three new partners (Auth0, Browserbase, Ultramarine) researched and ingested; seven seed ideas written.
- Oct 20, 21:30: the author proposed Skunkworks Sloth; bookmarks counted (7,845 then).
- Oct 24, 00:00: project chosen with about 50 h left; 00:30 scope cut to the Reading List, Stagehand back in, three profiles, Discord over Telegram; 01:10 GitHub Project mirror added.
- Oct 24, 11:00-11:40: profiles created, Tiger service created, Hermes updated to 0.22.5, deny-rule hardening on every profile, Auth0 moved to runner-up, plan rewritten for one coordinator and three parallel lanes (Curator, Board, Builder) in their own worktrees.
- Oct 24, 11:41: C0 contracts on `main` (schema, shared types, config, notify, LLM helper, fixtures). 12:35 CP1 merged early, no conflicts.
- Oct 24, 13:08: found the auto-started gateway had served the Week 2 WhatsApp bot for an hour; parked it.
- Oct 24, 13:51: first Discord turn failed on Hermes' 64k context minimum; 15:13 first good turn (focus set).
- Oct 24, 15:29: first Worker run on Sonnet (test mode); cost double count found and fixed.
- Oct 24, 15:51 to 17:36: whole Reading List triaged; browser pass fixed; Curator CP3 merged; Curator reports posted to Discord.
- Oct 24, 23:31 to Oct 25 00:25: Curator skill skip found and fixed; daily reading channel and job shipped; blueprint diagrams drawn.
- Oct 25, daytime: no logged build work. Two morning crons failed on the keychain.
- Oct 25, 18:24: the 15:00 freeze had passed with no measured run and no post; about 7.5 h left.
- Oct 25, 18:25-19:30: cron secret fix, profile distributions, two Worker providers, measured open-weights run (18:58, 4.9 min, $0.11), verification fix, approval 19:14, model picker, Obsidian-graph brain. Post draft v2 written alongside.
- Oct 25, 23:10-23:32: author's screenshots and edits, secret scan, first push, images pinned to a commit, DEV draft, agent session saved, published.

## What worked

- **One coordinator, three lanes with owned paths.** A one-hour contracts step (schema, shared types, fixtures) let three sessions build in parallel without waiting on each other; single-writer rules for `~/.hermes`, `sloth/core/` and the memory meant every merge was conflict-free. Each lane carried one risky M0 check.
- **Code decides, the model judges the rest.** Code rules settled 48 of 51 pipeline Valhalla proposals (dead links, redirects to home pages, archived repos, duplicates); Gemma judged the remainder. Capping articles and threads at "buildable 1" in code fixed Gemma's habit of rating landing pages as buildable.
- **Local triage at a usable speed.** About 4.2 s of model compute per link on the M4 Max; the full list ran overnight in 200-link batches.
- **Stagehand with a local model works if you drain the slot.** 197 browser-only pages read with local Gemma; pass 5 read 68 of 73 at a median 17.3 s once each timeout waited for the abandoned Ollama request to finish.
- **Script-only crons and `hermes send`.** Posting reports, picks and the log channel through scripts (no model turn) is fast, cheap and predictable; per-profile `send` posts as that profile's bot.
- **Open-weights Worker was cheap and quick.** The measured run built and tested a Noir contract in 4.9 min for $0.11; pick to approved private repo took about 20 min.
- **Profile distributions.** Shipping the agents as Hermes distributions with an install script (tested on a scratch `HERMES_HOME`) and an export script that refuses secrets made "install on another host" and "migrate" real instructions.
- **The memory file and its claims table** kept the post honest: TXE not Sandbox, triage local but the system not offline, agents not sandboxed, Sonnet runs labelled closed.

## What went wrong or cost time

- **Late start, again.** The idea was proposed on Oct 20 but chosen on Oct 24 with about 50 h left, and Sunday daytime had no build work, so the measured run, the post and the polish all landed in the last 7.5 hours. The 15:00 freeze was missed.
- **Context below Hermes' minimum.** C0 set the Ollama alias to 32k to save memory; Hermes 0.22.5 refuses models under 64k. Week 1 had used 65,536 for this reason, but the playbook did not say why.
- **Browser timeouts cascaded through Ollama's single slot.** Stagehand's client timeout left the request running, so every later call queued and timed out; it looked like an Ollama wedge.
- **The small model skipped its skill** and answered "what's unsure?" from general knowledge. A hard "load the skill first, run the command" rule in SOUL.md plus a skill description listing every request fixed it (same lesson as Week 1).
- **Cost double count.** The runner added cache reads to an input total that already included them ($9.64 instead of $1.02). Checked against Hermes' source and its own cost estimate, fixed with a test.
- **A multiplexed gateway woke an old bot.** A lane's `hermes chat` auto-started the gateway, which brought the Week 2 WhatsApp profile online for an hour. Nothing was sent; the profile is now parked.
- **Keychain in crons.** `tiger db uri --with-password` cannot read a locked keychain from a cron run; two Sunday crons failed. The DB URL now sits in the owner-only profile `.env` files.
- **Post-run verification without the login PATH.** The runner's `make test` could not find the Aztec toolchain and marked a passing run "killed". It now uses the PATH a login shell gives, and `sloth work --verify` re-checks a run.
- **Model overstated its own result.** The Worker's notes said "deployed in Sandbox"; the tests ran in Aztec's test environment (TXE). The post says TXE.
- **Raw image 404 after the first push.** Same fix as Week 2: pin image URLs to a commit SHA.
- **Day names wrong in the plan.** Oct 24 was labelled Friday; the hour math was right. Agent-estimated memory timestamps had to be corrected; from then on every entry used `date -u`.

## Numbers

- Bookmarks: 8,130 in the Chrome profile; Reading List 1,017 (12.5%), 969 unique.
- Enrich: 440 HTTP, 223 GitHub API, 197 browser, 109 title-only.
- Triage: 308 build, 609 read, 52 Valhalla (51 proposed by the pipeline, 1 by the author); 95% of decisions by the model. Agreement with the author 16/20 on three buckets, measured on the 20 links the prompt was tuned on.
- Triage speed: about 4.2 s compute per link at 32k and 64k; 753 links in 71 min wall with about 7.5% queueing.
- Board: 58 cards (6 per vertical cap), GitHub Project re-sync 1 call in 2.8 s.
- Worker, open weights (run 2): 4.9 min of a 120-min box, $0.1113, 3.22M input tokens (2.78M cache reads), 8,436 output; about 20 min pick to approved repo.
- Worker, Sonnet 5.5 test (run 1): 10 min, $1.0214; 97.5% of 4.31M input tokens were cache reads.
- Discord latency on the local 12B: Curator 14 s to 103 s; a Coordinator turn about 7 min while triage shared the Ollama slot.
- Second brain: 125 notes, 465 wikilinks, 0 dangling; 917 links placed in 49 subtopics by `embeddinggemma:300m` with per-vertical centring.
- Code: 145 commits in the challenge folder; 79 tests passed, 11 skipped.
- Author time per day (author's estimate): 30-120 min, including reading and code review.

## Playbook additions

1. Choose the idea within a day of the challenge opening; a proposal that waits four days for a decision costs the margin.
2. For parallel agent sessions, spend the first hour on contracts (schema, types, fixtures) and give each lane owned paths and one risky check; keep one writer for shared config.
3. Set any local model used by Hermes to at least 64k context, and keep one alias shared by every caller.
4. When a browser agent calls a single-slot local model, wait for an abandoned request to drain after each timeout.
5. Write a hard skill-first rule into each small-model agent's SOUL, and list every request phrase in the skill description.
6. Park every old Hermes profile at the end of a challenge; any CLI call can start a gateway that serves them all.
7. Crons must not depend on the macOS keychain; put what they need in owner-only files.
8. Verify agent work in the same environment the agent used (login-shell PATH), and treat the model's own success report as unverified.
9. Check cost math against the harness's own estimate before quoting a number.
10. Run the measured demo before the freeze, not after it.
