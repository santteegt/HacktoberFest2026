# AGENTS.md

Instructions for any AI coding agent working in this repository (Claude Code, Codex, Gemini CLI, Cursor, etc.). `CLAUDE.md` is a symlink to this file.

## What this repo is

A monorepo for the **Hacktoberfest 2026** challenges, which are run by MLH and DEV, presented by DigitalOcean. Theme: *"AI belongs to everyone"*, which means building with open-weight models and open-source AI. Each challenge gets its own folder under `challenges/`, and a shared knowledge base in `knowledge-base/hacktoberfest-2026/` keeps ideas, tools, and frameworks between challenges.

> Hacktoberfest 2026 **does not count pull requests**. Rewards come from virtual stickers (events, livestreams, DEV Challenges, Global Hack Week, tools, surveys). Do not apply 2014–2025 PR-based rules. See `STICKERS.md`.

## Layout

```
.agents/skills/            Canonical agent skills (harness-neutral). Edit here only.
.claude/skills             Symlink to ../.agents/skills (for Claude Code)
challenges/                One folder per challenge; see challenges/README.md
  _template/               Copy this to start a new challenge folder
  NN-<slug>/               AGENTS.md (challenge brief + instructions), README.md, CHALLENGE.md,
                           SUBMISSION.md, docs/CHALLENGE-MEMORY.md (keep it current) + the project code.
                           Read its AGENTS.md before working there.
knowledge-base/hacktoberfest-2026/   OKF wiki (raw/ sources, wiki/ pages)
STICKERS.md                Sticker tracker toward the 3 / 10 / 15 milestones
```

## Rules for agents

0. **Working inside a challenge folder?** Read that folder's `AGENTS.md` first; it holds the theme, partner list, and submission steps and overrides this file for that challenge.

1. **Verify live data before stating it.** Challenge prompts, dates, prizes, and rubrics change. Use the DevRelay MCP tools `get_challenges` / `get_challenge_details` (read `full_details`) and the `devrelay-knowledge` skill (`get_knowledge_document`, topic `hacktoberfest`). Never quote a date from memory. Today's date comes from the environment, not from this file.
2. **One challenge = one folder = one project.** Keep code, README, license, and submission draft together under `challenges/NN-<slug>/`. Do not share code between challenge folders by import; copy or extract to a new folder under `challenges/` if you must.
3. **New work only.** DEV rules require each entry to be started inside the challenge window. Never reuse a prior project's commits as a submission. Note any post-deadline commits in that project's README.
4. **Publishing is the user's call.** Stage DEV posts with `create_article` and `published: false`. Publish only after an explicit yes in the current session. Leave `ai_disclosure_level` at the DevRelay default (`some_ai`).
5. **Claims and credits.** Offers and promo codes (`devrelay-offers`) consume inventory, so ask before claiming. Sponsor skills (`devrelay-sponsor-skills`) return an install command, so ask before installing.
6. **Secrets.** Never commit keys or tokens. Use `.env` (ignored) and commit `.env.example`. Check agent-session transcripts for secrets before publishing them.
7. **Licensing.** Give every project an OSS license (MIT unless stated otherwise). The prompt asks for open-source AI at the core.
8. **Keep the challenge memory (mandatory).** Every challenge folder has `docs/CHALLENGE-MEMORY.md`, the running log that feeds the final report and DEV post. **Append an entry the moment something relevant happens, not at the end**: a decision and why (including options rejected), a non-obvious finding, a measurement, something that failed, an honest limit, a process lesson, a partner's real behavior, a friend quote, or any prior work used. Never delete or rewrite entries; mark a wrong one `SUPERSEDED by <date>` and add the correction. Measurements need date, machine, model and method, or they don't go in. Never record secrets or private data. Before writing the report or post, read the whole file and honor its "may claim / must NOT claim" table. Details and entry format: [`challenges/_template/docs/CHALLENGE-MEMORY.md`](challenges/_template/docs/CHALLENGE-MEMORY.md). If a session ends or context gets compacted, the memory file is the source of truth for what was decided.

## Knowledge base (OKF wiki)

`knowledge-base/hacktoberfest-2026/` follows the Open Knowledge Format via the **`okf-wiki` skill** (`.agents/skills/okf-wiki`). Do not hand-edit `wiki/index.md`, `wiki/log.md`, or `wiki/.hashes.json`. To add context (an idea, a tool evaluation, a framework comparison, a post-mortem), save it as markdown in `knowledge-base/hacktoberfest-2026/raw/` and run `/okf-wiki`. See that folder's `AGENTS.md`.

Before brainstorming or choosing tools for a challenge, **read `wiki/index.md` first**, then the relevant pages. Do this before searching the web.

## Skills in `.agents/skills`

| Skill | Use |
| --- | --- |
| `hf26-challenge` | Scaffold, audit, and submit a challenge folder (project-specific) |
| `okf-wiki` | Ingest and lint the knowledge base |
| `devrelay-challenges` | Live DEV Challenges and their `full_details` |
| `devrelay-knowledge` | Static program guides (Hacktoberfest, GHW, DEV rules) |
| `devrelay-sponsor-skills` | Sponsor SDK skills for prize categories |
| `devrelay-offers` | Sponsor credits and promo codes for MLH events |
| `devrelay-publishing` | Draft and stage DEV posts |
| `devrelay-sessions` | Save and embed agent session transcripts |
| `devrelay-community-wisdom` | Community patterns from dev.to |
| `devrelay-navigator` | Route to the right DevRelay MCP tool |
| `devrelay-mlh-submissions` | MLH project submission (Hack Day / MLH events) |

The `devrelay-*` skills need the `devrelay-gateway` MCP server (`curl -fsSL https://devrelay.com/install.sh | sh`, then `devrelay login`). Installing and logging in is itself a sticker.

## Adding or changing skills

Put them in `.agents/skills/<name>/SKILL.md` and nowhere else. Harness-specific folders (`.claude/`, etc.) should only symlink back. If a new harness needs its own path, add a symlink and list it here.
