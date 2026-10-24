# Skunkworks Sloth: spec and milestones

Written 2026-10-24 05:30 UTC (Fri Oct 24, 00:30 local). Deadline Oct 26 06:59 UTC; publish target Sat Oct 25 22:00 local. About 49 hours remain, two of them nights. This spec is the build contract; [PLAN.md](PLAN.md) holds the clock and the kill rules; the memory file holds every measurement.

## One paragraph

A three-agent skunkworks that turns a hoarded reading list into prototypes. The **Curator** reads the Chrome "Reading List" folder in daily batches, enriches each link (with a real browser where a plain fetch fails), and uses a local Gemma 4 model to say which links are worth exploring and which go to **Valhalla** (the removal bucket). The **Coordinator** asks the author for a weekly focus, keeps the skunkworks board, and posts one daily pick. The **Worker** builds the picked prototype in a two-hour box with an open-weight model on OpenRouter, writes notes, and pushes the repo after an approval. Each agent lives in its own Discord channel on the author's existing server. Triage is local and private; the coding step is hosted open weights and the post says so with its cost.

## Scope for this week

- **Source:** only the Chrome bookmarks-bar folder **"Reading List"** (1,017 links on 2026-10-24: 427 saved in 2025, 590 in 2026; 32 subfolders such as AI agents, LLMs, Rust, Solidity, Decentralized AI, project ideas; github.com 251, x.com 134, facebook.com 9). Chrome's own reading-list root and the other 6,800 bookmarks are out of scope and said so.
- **Browser:** Stagehand on the author's local Chrome, Gemma through a custom LLM callback, for links where HTTP fetch returns no readable text (x.com posts, login walls, JS-only pages). Browserbase cloud is not used. If the local-model callback is unreliable, the fallback is a pinned hosted open-weight model for the browser step only, declared in the post. X-bookmarks extraction is a stretch goal after M1, only if the x.com enrichment works.
- **Agents:** three Hermes profiles (Curator, Coordinator, Worker), each attached to one Discord channel. If Hermes cannot route one profile per channel on one gateway, the fallback is one profile with three skills and a channel-based router (see M0).
- **Partners entered:** Gemma (triage, wording), Browserbase (Stagehand enrichment), Tiger Data (links, board, runs), Auth0 for AI Agents (one flow: CIBA approval before the Worker pushes a repo public, or Token Vault for the GitHub push), Entire if `entire enable` on the prototype repo takes under 30 minutes. Everything else is out.

## Agents

| Agent | Channel | Trigger | Model | Does | Never does |
| --- | --- | --- | --- | --- | --- |
| **Curator** | `#curator` | cron, daily batch of N links (N sized by M0 timing; 100-200 expected) and on demand `/curate` | Gemma 4 12B QAT via Ollama (E4B for page screenshots if needed) | collect → enrich → triage; posts a batch report: kept (with one-line idea), Valhalla (with reason), unsure (asks) | decide alone on "delete"; Valhalla is a bucket the author empties |
| **Coordinator** | `#coordinator` | weekly focus question (Sunday or on `/focus`), daily pick at a fixed hour, `/board` | Gemma 4 12B (wording) + code (selection) | maintains the board columns; asks "what are you in the mood for?" with 3-4 tappable options; moves cards | write code; pick without the author's tap (default pick only when the author has pre-approved "auto") |
| **Worker** | `#worker` | a card moved to Today | open-weight model on OpenRouter (id and cost logged per run) | creates the repo from the template, implements inside a 2 h box, runs tests, writes `NOTES.md`, asks for approval, pushes | push without approval; exceed the box (it stops and reports) |

Shared rules (from the playbook): models do language jobs; code holds the rules, the clock, the board state and identity (`HERMES_SESSION_USER_ID`); every model output has a JSON schema and a verifier; proactive messages are sent by scripts through the gateway's send command, not by a model turn.

## Discord layout

Server: the author's existing server. Channels: `#curator`, `#coordinator`, `#worker`, plus `#valhalla` (read-only log of removals) and `#skunkworks-log` (one line per state change, for the demo). Bot: one Discord application per profile if routing requires it, else one bot with `DISCORD_ALLOWED_CHANNELS` and `DISCORD_FREE_RESPONSE_CHANNELS` listing the three channels and `DISCORD_HOME_CHANNEL` per profile for cron output. Only the author's user id is allowed.

## Data

Postgres on Tiger Data (fallback: local SQLite with the same schema).

- `links` (id, url, canonical_url, title, folder_path, saved_at, source, status, final_url, content_kind, readable_chars, github_stars, github_last_commit, fetched_with: http | stagehand, fetched_at)
- `triage` (link_id, model, topic, vertical, kind, still_relevant bool, reason, buildable 0-3, one_line_idea, decided_by: code | model, tokens_in, tokens_out, ms, created_at) as a hypertable on `created_at`
- `cards` (id, title, vertical, learning_goal, hypothesis, box_minutes, link_ids[], kill_criteria, column: backlog | today | built | archived, created_at, moved_at)
- `runs` (card_id, model_id, started_at, ended_at, cost_usd, tokens, outcome: done | boxed_out | killed, repo_url, notes_path)
- `valhalla` (link_id, reason, decided_by, created_at)

The board is also written as markdown files in `board/<column>/<card-id>.md` so it is diffable and the second brain can link to it. The second brain is `brain/` (OKF-style plain markdown: one page per card built, one per vertical, an index) generated by a script, never hand-edited.

## Workflows

1. **Collect** (code): parse `~/Library/Application Support/Google/Chrome/Default/Bookmarks` → nodes under bookmark_bar → "Reading List"; canonicalize URL (strip tracking params, lowercase host); upsert into `links` with `folder_path` and `saved_at` (FILETIME → UTC).
2. **Enrich** (code first, browser second): HTTP GET with a 10 s timeout; readable text via a readability library; GitHub API for repos (stars, archived, pushed_at); if readable text < 200 chars or the host is in the browser list (x.com, facebook.com, medium members' posts), Stagehand on local Chrome `extract` {title, author, date, summary_text, outbound_links} with Gemma through the callback; record `fetched_with`.
3. **Triage** (code rules, then model): code decides Valhalla for dead links (4xx/5xx after one retry, parked domains), archived repos, repos with no push in 4 years, duplicates; the model gets the rest with one schema: `{topic, vertical, kind, still_relevant, reason, buildable, one_line_idea}`; verifier checks enum values and that `reason` mentions a fact from the input; one retry locally. Batch report to `#curator`: kept / Valhalla / unsure, with counts and the batch's wall time.
4. **Board** (Coordinator, code + wording): cluster kept links by vertical and topic; a card needs 2-5 links with `buildable >= 2`; the model writes `title`, `learning_goal`, `hypothesis`, the code sets `box_minutes` (120 default) and `kill_criteria`; cards go to `backlog`. Weekly focus: the author answers one question ("this week I care about: ...") which becomes a weight on verticals.
5. **Daily pick** (Coordinator): at the set hour, code scores backlog cards (focus weight, freshness of links, verticals not touched lately), the model words 3-4 options, the gateway shows them as buttons; the tap moves one card to `today` and pings `#worker`.
6. **Prototype box** (Worker): new repo from `templates/prototype/` (README stub, NOTES.md stub, tests folder, Makefile), the card as the task; the Worker implements, runs tests, stops at the box or at done-means; writes `NOTES.md` (built, learned, next, links used); posts a summary in `#worker` with the cost; asks for approval; on approval (Auth0 CIBA push if working, else a Discord button) pushes to GitHub and moves the card to `built`.
7. **Second brain**: a script renders `brain/` from `cards`, `runs` and `NOTES.md`; the Coordinator posts the new page link in `#skunkworks-log`.

## Milestones

Each milestone has a clock, an owner (Claude builds, the author tests and taps), and a done-means. A milestone that overruns its clock by 30 minutes triggers its fallback, not an extension.

### M0: Feasibility (Fri 09:00-11:30 local, parallel subagents)

- **M0.1 Discord + profiles:** three Hermes profiles with `DISCORD_*` config; the author's server with the five channels; test that a message in `#curator` reaches the Curator profile only. Fallback: one profile, three skills, router by channel id.
- **M0.2 Triage sample:** Gemma 4 12B QAT on 50 random Reading List links with the triage schema; measure links per minute and agreement with the author's labels on 20. Fallback: E4B if 12B is too slow for a 1,017-link run inside 2 hours.
- **M0.3 Stagehand + local model:** Stagehand (Python) on local Chrome with a Gemma callback, `extract` on 5 x.com links and 3 JS-only pages; count successes. Fallback: pinned hosted open-weight model for the browser step only.
- **M0.4 Worker model:** one toy card through two OpenRouter open-weight models in a Hermes profile with the shell and file tools restricted to a sandbox repo; record minutes and dollars; pick one.
- **M0.5 Tiger Data:** create the service, apply the schema, insert the collected links. Fallback: SQLite.
- **M0.6 Auth0 CIBA:** free tenant, Guardian push, one approval round-trip from a script, boxed to 60 minutes. Fallback: a Discord approval button; Auth0 dropped from the categories.
- Done-means: a table in the memory with each check's result, timing and chosen path.

### M1: Curator (Fri 11:30-16:00)

- Collector, enrich (HTTP + GitHub + Stagehand), triage, Valhalla, batch report in `#curator`, `/curate` on demand.
- Run the full 1,017 in batches; log total wall time, tokens, dead/stale/kept counts.
- Done-means: `#curator` shows at least two batch reports; `links` and `triage` are full; the author has emptied Valhalla once.

### M2: Coordinator (Fri 16:00-20:00)

- Card builder, board files, `/board`, weekly focus question (asked once today), daily pick with buttons.
- Done-means: a backlog of at least 10 cards; the author answered the focus question and tapped one pick; the card is in `today`.

### M3: Worker (Fri 20:00-Sat 12:00, includes the night)

- Prototype template, Worker profile and skill, box timer, `NOTES.md`, approval step, push, `built` move, brain page.
- Fri night: the toy run end to end. Sat morning: the first real prototype from the author's pick, reviewed over coffee.
- Done-means: one real prototype repo on GitHub with `NOTES.md`, a cost figure, and a brain page; the approval step shown in the log.

### M4: Freeze and package (Sat 12:00-16:00)

- Second prototype or fixes (12:00-14:00). Stretch, only if M0.3 was green: X-bookmarks extraction via Stagehand into the same pipeline.
- **Feature freeze 16:00.** Clean-clone test, `.env.example`, README, LICENSE, screenshots by script against labelled demo data, measurements consolidated in the memory.
- Done-means: a stranger can run collect → triage on their own Reading List from the README.

### M5: Story (Sat 16:00-22:00)

- Demo video: triage batch with Wi-Fi off, the Discord pick, the Worker run, the approval, the brain page. SUBMISSION.md from the memory's may-claim table; curated agent session; DEV draft staged (`published: false`), images on commit SHAs; read aloud once.
- 22:00: publish on the author's yes. Then the repo READMEs, STICKERS.md, the retrospective in `raw/`, `/okf-wiki`.

## Measurements (date, machine, model, method, or they do not count)

- Reading List: links, duplicates, dead, stale repos, Valhalla, kept; share decided by code vs model.
- Triage: links per minute, tokens in/out, wall time per batch and total, model tag, `num_ctx`; agreement with the author on 20-40 hand labels.
- Enrich: HTTP-only successes vs Stagehand successes vs failures; seconds per Stagehand extract.
- Worker: minutes from pick to running skeleton; OpenRouter model id; dollars per run; tests passing.
- Author time: minutes per day on picks, reports and Valhalla (stopwatch), against the "before" of zero links reviewed in years.

## Claims the post may make / must not make

- May: triage runs locally and offline on an M4 Max; the reading list never leaves the Mac; the Worker uses open weights (named) on a hosted provider at a stated cost; numbers above with method.
- Must not: that the Worker is local or free; that X or Facebook are supported unless the stretch shipped; that prototypes "graduated" unless they have README, demo and post; that Auth0 is used if the fallback button shipped.

## Repository layout (inside this challenge folder)

```
sloth/            Python package: collect, enrich, triage, board, brain, send
profiles/         Hermes profiles: curator/, coordinator/, worker/ (SOUL, skills, config)
templates/prototype/
board/            backlog/ today/ built/ archived/ (markdown cards)
brain/            generated second brain
scripts/          cron entry points, screenshots, clean-clone test
docs/             SPEC.md, PLAN.md, CHALLENGE-MEMORY.md
```
