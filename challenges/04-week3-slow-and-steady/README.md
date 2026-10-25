# Skunkworks Sloth

> Three agents turn a hoarded Chrome Reading List into prototypes. You answer one question a day.

**Challenge:** [Hacktoberfest Open-Source AI Challenge: Week 3, Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19) (DEV event 81) · **Window:** Oct 19 19:00 → Oct 26 06:59 UTC · **Tags:** `#hf26challenge` `#devchallenge`

I saved 1,017 links in a Chrome bookmarks folder called "Reading List" in 2025 and 2026, all of them "to learn by building". I built none of them. Skunkworks Sloth reads the folder, decides with a local model what is worth building, worth reading, or dead, keeps a board of small project cards, and asks me once a day which card I'm in the mood for. A coding agent then builds that card in a two-hour box, writes down what it learned, and pushes the repo only after I approve.

## How it works

Three [Hermes Agent](https://github.com/NousResearch/hermes-agent) profiles live on my Discord server, one bot each. Code holds the rules, the clock, the board state and every write. The models only do language jobs: classify a link, word a card, write the prototype.

```
Chrome "Reading List" ──► Curator ──► Postgres (links, triage) ──► Coordinator ──► card in Today
  (Bookmarks file)          │  local Gemma 4 12B + Stagehand          │  local Gemma 4 12B       │
                            ▼                                         ▼                          ▼
              #sk-curator  #sk-valhalla  #sk-daily-reading     #sk-coordinator              Worker (#sk-worker)
                                                               GitHub Project board         2-hour box, open weights
                                                                                            NOTES.md → brain/ → approve → GitHub
                                       every state change ──► #sk-logs
```

| Agent | Channel(s) | What it does | What it never does |
| --- | --- | --- | --- |
| **Curator** | `#sk-curator`, `#sk-valhalla`, `#sk-daily-reading` | Collects the folder (canonical-URL dedupe), enriches each link (HTTP + readability, GitHub API, Stagehand on a local Chrome for pages a plain fetch can't read), triages with Gemma 4 into **build / read / Valhalla**, posts a batch report. Sends dead, archived, stale and duplicate links to **Valhalla**, a removal bucket I empty with `empty` or `restore 3, 7`. Posts one link a day from the reading bucket. | Delete anything. Valhalla is a proposal; I remove the links from Chrome myself. |
| **Coordinator** | `#sk-coordinator` | Clusters build-worthy links into cards (2-5 links each, title, learning goal, hypothesis and done-means worded by Gemma; box and kill criteria set by code). Asks a weekly focus question, scores the backlog, and offers 3-4 options with buttons each day. My tap moves one card to **Today**. | Pick without my tap. |
| **Worker** | `#sk-worker` | On `go`, `sloth work` creates a repo from [`templates/prototype/`](templates/prototype/) and runs the Worker profile on the card under a hard two-hour timer. Code runs `make test` itself after the box, completes `NOTES.md` (built, learned, next, links used), records cost and model, and posts a summary. `approve <run_id>` pushes a **private** repo; `publish <run_id>` makes it public. | Push before an approval, or run past the box. |

- **`#sk-logs`**: one line per state change, posted by script as the agent that made it (`[curator] batch …`, `[worker] card k05d2 run 1 done …`). It's the timeline of the week and the source of the numbers below.
- **GitHub Project board**: a one-way mirror of the cards (Backlog → Today → Building → Built / Killed), with cost, model and repo fields and a README status block, so progress shows up in a browser or the GitHub app. Postgres stays the source of truth; edits in the GitHub UI are overwritten on the next sync.
- **Second brain**: [`brain/`](brain/) is plain markdown generated from cards, runs and each prototype's `NOTES.md` (a page per built card, per vertical, and an index). `board/` holds the cards as markdown files. Both are generated, never hand-edited, and gitignored because they carry titles and URLs from my private list.

## Why open matters here

The split is honest, so here it is:

- **Local and private.** Triage, the browser step and the Coordinator run on **Gemma 4 12B** (`gemma4:12b-it-qat`, Apache 2.0) through **Ollama** on my M4 Max. The reading list never leaves the Mac; 95% of the triage decisions were made by the local model and the rest by code rules. It works offline, and running it again costs nothing.
- **The browser step is local too.** [Stagehand](https://github.com/browserbase/stagehand) (MIT) drives a local Chrome, and Gemma reads the page through Stagehand's bring-your-own-LLM callback. Browserbase's cloud is not used.
- **Hosted, paid, open weights.** The Worker writes code with **`google/gemma-4-26b-a4b-it`** on **OpenRouter**. The weights are open, but the inference is hosted and costs money per run. Each run's model id and cost are recorded.
- **Closed test runs, labelled.** While wiring Discord, some Worker runs used **Anthropic Claude Sonnet 5.5** (closed) to test the plumbing. They are recorded as `anthropic/claude-sonnet-5-5`, every message about them says "(closed model, test run)", and none of them backs a number in the lazy payoff below.

Because every model sits behind one alias or one config key (`llm.ollama_model`, `llm.worker_provider` / `llm.worker_model`), any piece can be swapped for another open model without touching the code.

## The lazy payoff

Measured on 2026-10-24 on an M4 Max with `sloth-gemma4-12b` (method and raw numbers in [`docs/CHALLENGE-MEMORY.md`](docs/CHALLENGE-MEMORY.md) and the lane logs in [`docs/lanes/`](docs/lanes/)):

| What | Number |
| --- | --- |
| Bookmarks in the folder | **1,017** (427 saved in 2025, 590 in 2026) |
| Unique after canonical-URL dedupe | **969** (48 exact duplicates) |
| Triage result | **308 to build · 609 to read · 52 Valhalla** |
| Triage compute per link | **≈ 4.2 s** (local Gemma 4 12B) |
| Wall time for the last 753 links | **71 min**, in four background batches |
| Cards on the board | 58, mirrored to the GitHub Project |
| My minutes per day (picks, reports, Valhalla) | TODO(CP3): stopwatch figure |
| First measured Worker run (open weights) | TODO(CP3): card, minutes, dollars, tests |

Before: zero of 1,017 links reviewed, zero built. After: every link has a decision and a one-line reason, the dead ones are queued for one-word removal, and the daily pick offers 3-4 cards to tap.

## Run it

Tested on **macOS on Apple Silicon** (M4 Max), Python 3.13 with [uv](https://docs.astral.sh/uv/), Ollama 0.40, Hermes Agent 0.22.5, Chrome. Other platforms are untested.

1. **Install and configure**
   ```bash
   uv sync
   mkdir -p .sloth && cp config.example.toml .sloth/config.toml
   ```
   Edit `.sloth/config.toml`: the Bookmarks path and folder name, the Tiger service id (or set `SLOTH_DATABASE_URL` for any Postgres), the Discord channel ids, the Ollama alias, and the OpenRouter model id. The file holds no secrets.

2. **Local model.** Create the Ollama alias every component shares (one alias and one context size, so Ollama never reloads the model):
   ```bash
   ollama pull gemma4:12b-it-qat
   printf 'FROM gemma4:12b-it-qat\nPARAMETER num_ctx 65536\n' > Modelfile.sloth
   ollama create sloth-gemma4-12b -f Modelfile.sloth
   ```

3. **Agents and bots.** Create three Hermes profiles, `sloth-curator`, `sloth-coordinator` and `sloth-worker`, each with its own Discord bot. Install the skills from [`profiles/`](profiles/) (each folder's README says where they go). Keys live only in each profile's `.env` and are read at runtime, never copied: `DISCORD_BOT_TOKEN` in all three, `OPENROUTER_API_KEY` in `sloth-worker` (and `ANTHROPIC_API_KEY` only if you run closed test runs). Curator and Coordinator use the Ollama alias; the Worker uses OpenRouter with the browser and computer-use toolsets disabled and manual approvals. Set `SLOTH_DRY_RUN=0` in the profiles that should post; anywhere else, every Discord line prints to stdout instead.

4. **Check and create the tables**
   ```bash
   uv run sloth doctor
   uv run sloth apply-schema
   ```

5. **Use it**
   ```bash
   uv run sloth curate --batch 200        # collect, enrich, triage; report to #sk-curator, Valhalla to #sk-valhalla
   uv run sloth valhalla show             # then reply `restore 3 7` or `empty` in #sk-valhalla
   uv run sloth board build               # cluster build-worthy links into cards
   uv run sloth board init                # once: create the GitHub Project and its fields
   uv run sloth board sync                # mirror the cards (also runs after every move)
   uv run sloth focus                     # the weekly focus question
   uv run sloth pick options              # the daily options; `sloth pick choose <card>` moves one to Today
   uv run sloth work <card_id>            # the two-hour box (or say `go` in #sk-worker)
   uv run sloth approve <run_id>          # push a private repo; add --public to publish it
   uv run sloth brain                     # regenerate the markdown second brain
   ```

6. **Crons.** `scripts/curate-daily.sh` runs as a Hermes cron (`0 7 * * *`, script only): it collects new Reading List links and triages them only when there are any. The Coordinator's crons are the daily pick (09:00), the weekly focus (Sunday 18:00) and a 30-minute `sloth board sync` safety net; see [`profiles/coordinator/README.md`](profiles/coordinator/README.md).

Tests: `uv run pytest` (database tests run only against a scratch schema; see the test files).

## Stack

| Piece | Role | License / openness |
| --- | --- | --- |
| Gemma 4 12B (`gemma4:12b-it-qat`) | triage, card wording, browser extraction, the Curator and Coordinator agents | open weights, Apache 2.0, runs locally |
| Gemma 4 26B A4B (`google/gemma-4-26b-a4b-it`) | the Worker's coding model | open weights, **hosted** on OpenRouter (paid) |
| [Ollama](https://github.com/ollama/ollama) | local inference | MIT |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | the three agents, Discord gateway, crons | MIT |
| [Stagehand](https://github.com/browserbase/stagehand) (Browserbase, Python v4) | reads JS-only pages and x.com posts in a local Chrome | MIT; no Browserbase cloud |
| Postgres on Tiger Data | links, triage, cards, runs, Valhalla, events | Postgres is open source; Tiger Cloud is a hosted service |
| trafilatura, httpx, psycopg, pydantic, Typer | enrichment and plumbing | open source |
| GitHub Projects | the board UI | GitHub service, not open source |

**Not open:** Discord (where the agents talk to me), OpenRouter (the Worker's inference host), Tiger Cloud (Postgres hosting), GitHub (repos and the Project board), and the Anthropic Sonnet 5.5 test runs. Only card titles and bodies go to GitHub; the reading list itself stays local.

## Limits

- **Headful Chrome.** x.com answers headless Chrome with a 403, so the browser step opens a visible, separate Chrome window. I don't disguise the browser. Posts are read logged out, so login-walled content isn't reachable.
- **One Ollama slot.** Triage, the browser step and the Discord agents share one local model. While a batch runs, an agent turn takes minutes, not seconds.
- **24 long x.com threads stay title-only.** They don't fit the browser step's time budget.
- **Triage agreement is optimistic.** It was measured on 20 links that I labelled and that the prompt was then tuned on. Agreement on keep was 20/20 and on build/read/Valhalla 16/20; there was no held-out set.
- **Not a sandbox.** The Worker runs as my macOS user, with shell deny rules and manual approvals. That is a command policy, not OS isolation.
- **Prototypes are small.** A card is done when its done-means passes and `make test` passes, not when someone has reviewed the product.

## Credits and license

Built during the challenge window (from Oct 24, 2026) by Santiago Gonzalez ([@santteegt](https://github.com/santteegt)) with AI coding agents, in a coordinator-plus-three-lanes setup described in [`docs/LANES.md`](docs/LANES.md). It reuses no code from this repo's earlier challenge folders. Thanks to the Gemma, Ollama, Hermes Agent and Stagehand teams for the open pieces it stands on.

MIT, see [LICENSE](LICENSE). Any commits made after the deadline (Oct 26, 2026 06:59 UTC) will be listed here.
