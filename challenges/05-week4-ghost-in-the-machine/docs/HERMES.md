# Hermes: the `ghosts` profile and how to run the host

Written 2026-10-29 for Hermes Agent v0.22.5 on the author's Mac. Everything below is a command for **you** to run; the build lane installed nothing into `~/.hermes`, started no gateway, and parked no profile.

What the profile is: a Hermes profile distribution in [`hermes/`](../hermes) named `ghosts`. It has a persona (`SOUL.md`, the keeper of the altar), one skill (`ghost-stories`), two cron jobs that arrive paused (`ghost-of-the-day`, daily 09:00 local; `weekly-incident`, Mondays 10:00 local), the Ethereum History MCP server (`https://www.ethereumhistory.com/mcp`), and a model entry that points at Ollama (`ghosts-gemma4-12b`, open weights). The cron jobs are script-only (`no_agent`): no model turn of their own, they run `scripts/haunt.sh`, which runs `ghosts haunt` and posts one line built in code. In Discord the agent (Gemma on this Mac) only turns your message into a `haunt.sh` call and relays what it printed.

## State of this Mac when this was written (read-only checks, 2026-10-29)

- `hermes gateway list`: nothing is running, including the default profile (its `.env` has no bot token).
- `rc-parts` is already parked (`gateway.parked` exists).
- `sloth-curator` and `sloth-coordinator` each have an **active** cron job that is overdue since Oct 26 (`curator-daily`, `daily-pick`). The host runs the cron jobs of every unparked profile, so starting it before parking them would fire those jobs. Park first.
- `sloth-worker` has no cron job. `ghosts` is not installed yet. The Ollama alias `ghosts-gemma4-12b` does not exist yet.

## (a) Park the three sloth profiles (nothing is deleted)

```bash
hermes -p sloth-curator gateway stop
hermes -p sloth-coordinator gateway stop
hermes -p sloth-worker gateway stop
hermes gateway list          # all four old profiles should read parked or not running
ls ~/.hermes/profiles/*/gateway.parked    # rc-parts plus the three above
```

`stop` writes a `gateway.parked` marker in each profile. The host then skips that profile's adapters and its cron jobs, the marker survives host restarts, and sessions and memories stay. To bring one back later: `hermes -p sloth-curator gateway start`.

## (b) Install the `ghosts` profile

From this folder:

```bash
cd ~/GitRepositories/HacktoberFest2026/challenges/05-week4-ghost-in-the-machine
hermes/install.sh --dry-run --yes     # prints every step, changes nothing
hermes/install.sh --yes               # the real install
```

`install.sh` does five things: checks `hermes`, `uv`, `ollama`, `python3`; runs `uv sync`; creates the Ollama alias if missing (`ollama create ghosts-gemma4-12b` from a Modelfile with `FROM gemma4:12b-it-qat` and `PARAMETER num_ctx 65536`; Hermes refuses a model with under 64k context); runs `hermes profile install hermes --name ghosts --yes` (or `hermes profile update ghosts --yes` when it already exists); and fills three path placeholders (project folder, profile folder, and a PATH for cron made from the real directories of `uv`, `vercel`, `node`, `hermes`, `python3`, because cron scripts get a sanitized environment and nvm paths change). It never starts the gateway, parks anything, writes a token or resumes a cron job. Do not pass `--alias`: a shell wrapper called `ghosts` would sit next to the `ghosts` project CLI and confuse both.

After editing anything in `hermes/`, run `hermes/install.sh --yes` again: `profile update` replaces the distribution-owned files (the placeholders come back), the script fills them again, and your `config.yaml`, `.env`, memories and sessions are kept. To also take a changed `config.yaml` fragment: `hermes profile update ghosts --force-config --yes`, then `hermes/install.sh --yes` to refill.

Check it:

```bash
hermes profile info ghosts
hermes -p ghosts cron list            # two jobs, both [paused]
hermes -p ghosts config check
```

### The two models and the reload

The pipeline (`ghosts story`) calls `gemma4:12b-it-qat` at 8k context. Hermes talks to `ghosts-gemma4-12b`, the same weights at 64k context. To Ollama those are two different runners, so going from one to the other can unload and reload the model (seconds, not measured here). That is why the cron jobs are script-only and why the skill runs the pipeline as a subprocess in the terminal tool instead of through the agent's own model: a daily haunt never touches the 64k alias. Only a Discord conversation does.

## (c) Fill the profile `.env`

The profile's env file lives at `~/.hermes/profiles/ghosts/.env` and is never committed. The names (values are yours):

```bash
cp ~/.hermes/profiles/ghosts/.env.EXAMPLE ~/.hermes/profiles/ghosts/.env     # only if .env does not exist yet
$EDITOR ~/.hermes/profiles/ghosts/.env
```

| Name | What | Needed for |
| --- | --- | --- |
| `DISCORD_BOT_TOKEN` | this agent's own bot (a bot token shared with another profile parks the second adapter as a duplicate) | Discord conversation and the report posts |
| `DISCORD_ALLOWED_USERS` | your Discord user id; only you can talk to the bot | Discord |
| `DISCORD_ALLOWED_CHANNELS` | channel ids it listens in, comma-separated | Discord |
| `DISCORD_FREE_RESPONSE_CHANNELS` | channel ids where it answers without an @mention (usually the same) | Discord |
| `DISCORD_HOME_CHANNEL` | channel id where `haunt.sh` posts its report; use the channel you chat in | the report line |
| `VERCEL_TOKEN` | optional; empty means `deploy.sh` uses the Vercel CLI login of this macOS user | unattended deploys |

Everything is optional. Without the Discord names the profile runs cron-only: each haunt prints its one-line report into the cron output (`deliver: local`, `hermes -p ghosts cron list`) and the gallery at https://eth-ghosts.decentraminds.tech is the delivery. `haunt.sh` reads these names from the profile `.env` itself (it never prints a value), so the cron jobs need no `env_passthrough` and the agent's terminal does not get `VERCEL_TOKEN` in its environment. Creating the Discord bot and enabling its intents is in Hermes' own guide: `~/.hermes/hermes-agent/website/docs/user-guide/messaging/discord.md`.

Dry run of the script (prints the commands it would run, executes nothing, shows whether Discord and a Vercel token are seen):

```bash
~/.hermes/profiles/ghosts/scripts/haunt.sh --dry-run --source archive --seed daily --deploy
```

## (d) Start the host

One host gateway serves every unparked profile (`hermes -p ghosts gateway run` is refused by design). Start it from the default profile, after (a):

```bash
# in a spare terminal tab, foreground, easy to watch and stop with Ctrl-C:
hermes gateway run

# or as a macOS user service that survives closing the terminal:
hermes gateway install --start-now --no-start-on-login
hermes gateway status
hermes cron status          # scheduler alive? soonest run?
```

Stop it: `Ctrl-C` for the foreground run, `hermes gateway stop` for the service. Do not use `hermes -p ghosts chat -q` or similar before you want the host up: a CLI call on a profile can auto-start the multiplexed gateway (this brought an old profile online in Week 2).

## (e) Unpause the crons

```bash
hermes -p ghosts cron resume ghost-of-the-day      # daily 09:00 local
hermes -p ghosts cron resume weekly-incident       # Mondays 10:00 local (optional)
hermes -p ghosts cron list
hermes -p ghosts cron run ghost-of-the-day         # fire it on the next scheduler tick instead of waiting
```

Pause again with `hermes -p ghosts cron pause <name>`; `hermes pause` stops every scheduled fire on the host. A job that fails posts an error alert (non-zero exit) and the failure line is also posted to Discord by the script when Discord is configured.

## (f) Run one haunt by hand

Without Hermes in the loop (local page only, nothing is published):

```bash
~/.hermes/profiles/ghosts/scripts/haunt.sh --source archive --seed daily
~/.hermes/profiles/ghosts/scripts/haunt.sh --address 0x2af47a65da8cd66729b4209c22017d6a5c2d2400 --site bounties.network
~/.hermes/profiles/ghosts/scripts/haunt.sh --status        # last result, running?, last log lines
```

Add `--deploy` to publish to the gallery (`vercel deploy --prod` through `scripts/deploy.sh`). The script runs `uv run ghosts haunt ... --json`. While `ghosts haunt` is missing it falls back to `pick --dry-run`, `summon`, `wounds`, `classify`, `face` (a failure here never stops the chain), `story`, `render`, `gallery build` or `scripts/deploy.sh`. A second run while one is running exits with "already running". The log is `data/cache/hermes/haunt.log` (gitignored), the last report `data/cache/hermes/last-haunt.txt`.

Or the pipeline directly, from the project: `uv run ghosts haunt --source archive --seed daily [--deploy]`.

## (g) What to type in Discord

In the channel set in `DISCORD_ALLOWED_CHANNELS`, as the user in `DISCORD_ALLOWED_USERS`:

| Type | What happens |
| --- | --- |
| `tell a ghost story` / `haunt` / `today's ghost` | starts a haunt of the daily archive pick, no deploy; "started, result will be posted" |
| `haunt and publish` | same with `--deploy` (public gallery) |
| `random ghost`, `a 2016 ghost`, `bad ghost` / `incident` | random-block, year-limited, incident picks |
| `haunt 0x2af47a65da8cd66729b4209c22017d6a5c2d2400` (add `site bounties.network` for the dapp's website) | that contract |
| `status` | the last result and whether a haunt is running |
| `who is in the gallery` | the index: name, kind, age, address |
| `show the story of 0x...` / `is 0x... bad?` | title, tagline and first paragraphs / kind, reasons, and each wound as confirmed or suspected |

When the haunt ends, the script (not the model) posts one line: `Ghost of the day: <name> (<kind>, <era> era). "<title>" <tagline> <link>`, or `Haunt failed at step: <step>. ...`. After changing `SOUL.md` or the skill, send `/new` in the channel so the session picks them up.

## Honest lines

- **The deny rules are not a sandbox.** `approvals.deny` blocks matching command text (sudo, `launchctl`, `crontab`, `security`, `osascript`, `docker`, `rm -rf`, `git push`, `vercel`, `hermes gateway/profile/cron`, ...) before approvals are consulted, but it is a pattern list: it does not stop a different way of doing the same thing, a Python one-liner, or anything inside a script that is allowed to run. Approvals are `manual`; cron, single-query and unattended modes are `deny`.
- **The agent runs as your macOS user** with `terminal.backend: local`: it can read and write whatever you can, including the project, the Vercel CLI login, `~/.ssh`, the browser profile and the profile `.env` (Discord token, optional `VERCEL_TOKEN`). A Vercel token is account-scoped, not project-scoped. The only protection is that only you may talk to the bot, a small allowed toolset (browser, web, code execution, delegation and cron tools are disabled) and the policy above. Nothing from your wallet is on disk in this folder.
- **The Ethereum History MCP server is a third-party service.** Its replies are data for the agent; the skill tells it to quote them and never to use them in place of a haunt. The pipeline itself uses the REST API, not this MCP server.
- **Facts come from files, not from the model's memory.** A kind, a date, an address or a wound is read from `facts.json`, `verdict.json`, `wounds.json` or `story.json`; the verdict is "confirmed" only when `wounds.json` says so. A 12B model can still garble a relay, which is why the haunt report is built in code.
- The story text is written by Gemma on this Mac from code-verified facts; the data sources (Ethereum History, Blockscout, Sourcify, public RPC, Wayback) are online services.

## What was checked and what was not

Checked on 2026-10-29 (M4 Max, Hermes v0.22.5): `bash -n` on every script; `haunt.sh --dry-run` for archive, incident and address runs; argument validation; the whole script (fallback chain, `--json` path, Discord post call, failure report, lock, detach) against stub `uv` and `hermes` programs (`uv run pytest tests/test_e_hermes.py`, 23 tests, offline); the distribution installed with Hermes' own `install_distribution` into a scratch `HERMES_HOME` (jobs arrived paused, files copied, no secrets); the filled `config.yaml` loaded with Hermes' `load_config_readonly` and `validate_config_structure` (0 issues). `~/.hermes` was not touched.

Not checked: a real Discord conversation (no bot token yet); the Ethereum History MCP connection from Hermes; the skill triggering with Gemma 4 12B (the Week 1 and 3 lessons say to make skill-first a hard rule and list every phrase, both done, but only a live session shows it); `ghosts haunt` end to end through the script (Lane G's command was not wired when this was written, the `--json` handling follows its source); the Ollama alias creation and the model reload cost; a real `vercel deploy` from a cron script's sanitized environment; whether `hermes -p ghosts send --to discord` picks the profile's home channel (documented as home channel for a bare platform name, not run, it would post).
