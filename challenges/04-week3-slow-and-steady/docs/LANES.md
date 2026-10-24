# Skunkworks Sloth: parallel execution (coordinator + 3 lanes)

Written 2026-10-24 16:40 UTC (**Sat Oct 24, 11:40 local**, UTC-5). Deadline Mon Oct 26 06:59 UTC = **Mon 01:59 local**; publish target **Sun Oct 25, 22:00 local**. About 38 hours remain, one night included. This file says who builds what, which files each lane owns, the contracts between lanes and the merge checkpoints. [SPEC.md](SPEC.md) stays the product contract; [PLAN.md](PLAN.md) the clock.

## Roles

| Role | Who | Owns | Never touches |
| --- | --- | --- | --- |
| **Coordinator** | this session | contracts (C0), `~/.hermes/` (all profiles, models, SOUL/skills install, the one gateway), `sloth/core/`, `sloth/cli/__init__.py`, `pyproject.toml` + `uv.lock`, `docs/` (SPEC, PLAN, LANES, CHALLENGE-MEMORY), merges, Discord channel test posts, the post | lane modules (asks the lane instead) |
| **Lane 1: Curator** | worker session 1 | collect, HTTP enrich, GitHub enrich, triage, Valhalla logic, Curator skill text | browser module, board, worker, `~/.hermes/` |
| **Lane 2: Board** | worker session 2 | cards, focus, scoring and daily pick, GitHub Project sync, brain renderer, Coordinator skill text | collect/enrich/triage, worker, `~/.hermes/` |
| **Lane 3: Builder** | worker session 3 | Stagehand browser extractor (M0.3), prototype template, Worker box runner, OpenRouter model choice (M0.4), approval button flow, Worker skill text | collect/triage, board, `~/.hermes/` |

Why this cut: each lane has one M0 risk of its own (L1 triage speed and quality, L2 the GitHub Project API, L3 Stagehand with a local model and the hosted coding model), no two lanes edit the same file, and every cross-lane dependency goes through a typed function or a database table defined in C0, with a fixture so nobody waits.

## Git and workspace rules

- Each lane runs in **its own git worktree on its own branch**: `lane/curator`, `lane/board`, `lane/builder`, cut from `main` after C0 is committed. Lanes commit often on their branch; they never push, never merge, never rebase `main`.
- The coordinator merges lane branches into `main` at each checkpoint (the author pre-authorizes checkpoint merges when the lanes start; otherwise the coordinator asks at each one). After a merge, lanes run `git merge main` into their branch to pick up the others' work.
- **Owned paths only.** A lane that needs a change outside its paths (a schema column, a new dependency, a CLI hook, a contract change) writes it as a request at the top of its lane log and keeps going on fixtures; the coordinator applies it on `main` and announces it.
- **Shared files are single-writer:** `pyproject.toml`/`uv.lock`, `sloth/core/*`, `sloth/cli/__init__.py`, `docs/CHALLENGE-MEMORY.md` are coordinator-only. Lanes record measurements, decisions and failures in their own log (`docs/lanes/<lane>.md`, same entry format as the memory: date, machine, model, method); the coordinator folds them into the memory at each checkpoint.
- **No Hermes gateway in lanes.** Only the coordinator starts the single multiplexed gateway. Lanes test their logic as plain Python and their skills with `hermes -p <profile> chat -q` against a scratch session, never by posting to Discord.
- **Secrets:** lanes read them at runtime through `sloth.core.secrets` (which loads the right profile `.env`); no lane copies a key into its worktree, a fixture, a log or a commit.
- **Private data:** the real Reading List stays out of git. Committed fixtures are synthetic; real samples go to `.sloth/` (gitignored).

## C0: contracts (coordinator, Sat 12:00-13:00, before any lane starts)

Committed to `main` so all three branches start from it:

1. **Package skeleton** (Python 3.14 via `uv`): `sloth/core/{config.py, db.py, secrets.py, models.py, notify.py, llm.py}`, `sloth/cli/__init__.py` (Typer app that imports `sloth.cli.curator`, `sloth.cli.board`, `sloth.cli.builder` if present), empty lane packages `sloth/curator/`, `sloth/board/`, `sloth/builder/`, `tests/` with one smoke test per lane.
2. **Dependencies pre-added:** `psycopg[binary]`, `httpx`, `trafilatura`, `pydantic`, `typer`, `rich`, `ollama`, `openai` (OpenRouter client), `stagehand` (Python SDK, v4), `pytest`. Anything else is a request.
3. **Schema** `sloth/core/schema.sql` (the tables in SPEC "Data", plus `enrichment` split out of `links`), applied to the `skunkworks-sloth` Tiger service; `sloth/core/db.py` gives `connect()` and `apply_schema()`. SQLite fallback uses the same DDL subset.
4. **Shared types** `sloth/core/models.py` (pydantic): `Link`, `Enrichment`, `BrowserExtract`, `Triage`, `Card`, `PickOption`, `Run`, with enums for `vertical`, `kind`, `column`, `fetched_with`, `run outcome`.
5. **Config** `sloth/core/config.py` reads `.sloth/config.toml` (gitignored; `config.example.toml` committed): bookmarks path and folder name, Tiger service id, Discord channel ids for `curator`, `valhalla`, `coordinator`, `worker`, `log`, the Ollama model tag and `num_ctx`, the OpenRouter model id (set by L3 after M0.4), the box minutes, the GitHub Project number.
6. **Notify** `sloth.core.notify.post(channel, text, *, as_profile)` wraps `hermes -p <profile> send --to discord:<id>`; `notify.log(event)` posts one line to `#sk-logs`. Coordinator verifies it posts as the right bot (closes the open M0.1 question).
7. **LLM helper** `sloth.core.llm.local_json(prompt, schema, *, model=None)` calls Ollama's native `/api/chat` with a JSON-schema `format`, one alias and one `num_ctx` for everybody (playbook: avoids model reloads).
8. **Fixtures** (synthetic, committed): `tests/fixtures/links.json` (40 links covering github, x.com, medium, dead, duplicate), `tests/fixtures/triage.json` (30 triage rows across 6 verticals), `tests/fixtures/card.json` (one buildable card).
9. **Hermes profiles** (coordinator, outside git): Curator and Coordinator models → Gemma 4 through Ollama; Worker model left unset until M0.4; each profile's `terminal.cwd` pointing at the merged `main` checkout (lanes never rely on the gateway).
10. **Lane logs** `docs/lanes/curator.md`, `board.md`, `builder.md` with the lane's checklist below.

## Contracts between lanes

| Producer → consumer | Contract | Fixture until real |
| --- | --- | --- |
| L1 → L2 | rows in `links`, `enrichment`, `triage` (schema in C0); `sloth curate` exits 0 and prints a batch summary | `tests/fixtures/triage.json` loaded by `sloth board seed-fixtures` |
| L3 → L1 | `sloth.builder.browser.extract(url: str, *, timeout_s: int = 45) -> BrowserExtract \| None` (None = could not read) | L1 uses a stub returning None until L3 lands it |
| L2 → L3 | a card row with `column='today'`; `sloth work <card_id>` is the entry point L3 implements | `tests/fixtures/card.json` |
| L3 → L2 | `runs` row written on start (`building`) and end (`built`/`killed`, cost, model, repo); L2's GitHub sync reads it | L2 writes a fake run row in its own tests |
| all → coordinator | `sloth.core.notify.post/log` for every Discord message; no lane talks to Discord directly | prints to stdout when `SLOTH_DRY_RUN=1` (default in lanes) |

CLI ownership: L1 `sloth curate [--batch N] [--source reading-list]`, `sloth valhalla {show,restore,empty}`; L2 `sloth board {build,sync,init,seed-fixtures}`, `sloth focus`, `sloth pick {options,choose}`, `sloth brain`; L3 `sloth work <card_id>`, `sloth approve <run_id>`, `sloth browser test <url>`.

## Lane checklists (done-means per checkpoint)

### Lane 1: Curator (`sloth/curator/`, `sloth/cli/curator.py`, `profiles/curator/`, `tests/curator/`, `docs/lanes/curator.md`)

- **By CP1:** collector over the real Bookmarks file → `links` (1,017 expected), canonical URL dedupe, `saved_at` from FILETIME; HTTP enrich with trafilatura and GitHub API (stars, archived, pushed_at; unauthenticated rate limit respected or `gh api` via the keyring); **M0.2** triage on 50 real links with Gemma 4 12B: links/min, tokens, wall time, agreement with the author's labels on 20 (author labels them in a 10-minute file the lane prepares). Decide 12B vs E4B.
- **By CP2:** code rules for Valhalla (dead, archived, stale > 4 years, duplicate) and model triage with verifier and one retry; `sloth curate --batch 200` end to end on real data; batch summary text for `#sk-curator` and the Valhalla list text for `#sk-valhalla`; Curator skill text (how to answer `restore 3, 7` / `empty`, calls the CLI).
- **By CP3:** full Reading List triaged (in batches, overnight if needed); measurements logged.

### Lane 2: Board (`sloth/board/`, `sloth/cli/board.py`, `profiles/coordinator/`, `board/`, `brain/`, `tests/board/`, `docs/lanes/board.md`)

- **By CP1:** card builder on fixtures (cluster by vertical/topic, 2-5 links with buildable >= 2, model writes title/goal/hypothesis via `core.llm`, code sets box and kill criteria); markdown board files; **GitHub Project** `sloth board init` (project, fields, ids file) and idempotent `sloth board sync` with batched GraphQL and the README status block, against fixtures. Boxed to 45 minutes for the Project part; fallback is markdown only.
- **By CP2:** cards from real triage rows; focus question and scoring; `sloth pick options` (3-4 options, model wording only) and `sloth pick choose`; Coordinator skill text (weekly focus, daily pick with buttons through Hermes `clarify`); brain renderer from cards + runs + NOTES.md.
- **By CP3:** board synced after every move, including the Worker's run rows.

### Lane 3: Builder (`sloth/builder/`, `sloth/cli/builder.py`, `profiles/worker/`, `templates/prototype/`, `tests/builder/`, `docs/lanes/builder.md`)

- **By CP1:** **M0.3** Stagehand (Python, v4) on local Chrome with a Gemma callback: `extract` on 5 x.com links and 3 JS-only pages from the real list; success count and seconds each; decide local callback vs hosted open-weight fallback vs drop (kill rule in PLAN). **M0.4** one fixture card through two OpenRouter open-weight models inside the `sloth-worker` profile (tools restricted, cwd `~/GitRepositories/skunkworks-prototypes`): minutes, dollars, tests passing; pick one and write its id to the lane log.
- **By CP2:** `browser.extract()` landed for L1; prototype template; `sloth work <card_id>`: new repo dir from the template, Hermes Worker run with the card as the task, 2-hour box timer, `NOTES.md`, `runs` row, summary text with cost; approval flow (`sloth approve` + Discord button wording) and `gh repo create --private` + push on approval; toy card run end to end.
- **By CP3:** first real prototype from the author's pick, reviewed; visibility flip to public only after the author's tap.

## Checkpoints (coordinator merges, integrates, folds lane logs into the memory)

| When (local) | Checkpoint | Coordinator does |
| --- | --- | --- |
| Sat 13:00 | **Lanes start** | C0 on `main`; three sessions started from it |
| Sat 16:00 | **CP1** | merge all three; review M0 results; take fallbacks per the kill rules; re-plan if a lane is red |
| Sat 20:00 | **CP2** | merge; integration run on real data: `curate` → `board build/sync` → author focus + pick in Discord → `work` on the toy card; start the gateway with all three profiles |
| overnight | | L1 batches finish the list; nothing else runs unattended |
| Sun 09:00 | author picks the day's card in `#sk-coordinator` | |
| Sun 12:00 | **CP3** | first real prototype built and approved; merge; measurements into the memory |
| Sun 12:00-15:00 | runner-ups, in order, only if CP3 is green | Gmail via Auth0 Token Vault (90 min, one lane), Project status read-back, X bookmarks via Stagehand, second prototype |
| Sun 15:00 | **Freeze** | lanes stop and hand over; clean-clone test, README, screenshots, demo |
| Sun 15:00-21:00 | story | coordinator writes SUBMISSION.md from the memory; one lane may help with screenshots and README run-steps |
| Sun 22:00 | publish on the author's yes | |

## What each worker session gets as its brief

Its lane section above, the C0 contracts table, the git and workspace rules, the CLI it owns, its checkpoint times, the paths it may write, and the instruction to stop and write a request in its lane log rather than edit a file it does not own. It reports at each checkpoint with: done items, measurements (with method), failures, requests.
