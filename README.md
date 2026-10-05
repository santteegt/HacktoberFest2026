# Hacktoberfest 2026

Monorepo for my Hacktoberfest 2026 challenge entries and the knowledge base behind them.

Hacktoberfest 2026 is run by [MLH](https://mlh.io) and [DEV](https://dev.to), presented by DigitalOcean. The theme is **"AI belongs to everyone"**: build with open-weight models and open-source AI. **Pull requests no longer count.** Rewards come from virtual stickers (see [STICKERS.md](STICKERS.md)), and the DEV Challenges carry cash prizes.

## Challenges

Each challenge lives in its own folder under [`challenges/`](challenges/README.md). I'm starting with the weekend challenge and adding the others as they open.

| # | Challenge | Window (UTC) | Status |
| --- | --- | --- | --- |
| 01 | [Weekend: Build for a Friend](challenges/01-weekend-build-for-a-friend): RC Pit Companion | Oct 2 02:00 → Oct 5 06:59 | ✅ [Published](https://dev.to/santteegt/a-setup-coach-for-my-friends-rc-car-that-stays-on-his-laptop-4ahn) |
| 02 | Week 1: Open-Source AI | Oct 5 → Oct 12 | 🔵 Opens Oct 5 |
| 03 | Week 2: Open-Source AI | Oct 12 → Oct 19 | 🔵 Upcoming |
| 04 | Week 3: Open-Source AI | Oct 19 → Oct 26 | 🔵 Upcoming |
| 05 | Week 4: Open-Source AI | Oct 26 → Nov 1 | 🔵 Upcoming |
| – | Global Hack Week: Hacktoberfest | Oct 9 → Oct 15 | 🔵 Upcoming |

Dates come from live data and have shifted before. Check `challenges/README.md` for the source and discrepancies.

## Repo layout

```
AGENTS.md                  Instructions for any AI agent (CLAUDE.md is a symlink)
STICKERS.md                Sticker tracker toward the 3 / 10 / 15 milestones
challenges/                One folder per challenge (+ _template/)
knowledge-base/hacktoberfest-2026/
                           OKF wiki: raw/ sources → wiki/ pages (ideas, tools, frameworks)
.agents/skills/            Agent skills, shared across harnesses
.claude/skills             Symlink to .agents/skills for Claude Code
```

## Working with agents

The repo is harness-neutral. Skills and agent config live in `.agents/`, and `AGENTS.md` is the entry point. Claude Code gets the same content through the `CLAUDE.md` and `.claude/skills` symlinks. The agent skills need the DevRelay MCP gateway:

```bash
curl -fsSL https://devrelay.com/install.sh | sh
devrelay login
```

Start a new challenge folder with the `hf26-challenge` skill, or copy `challenges/_template` by hand. Add notes to the knowledge base by dropping markdown into `knowledge-base/hacktoberfest-2026/raw/` and running `/okf-wiki`.

## Key links

- Hacktoberfest: <https://hacktoberfest.com> · dashboard <https://hacktoberfest.com/my/>
- DEV Challenges: <https://dev.to/challenges>
- Global Hack Week: <https://ghw.mlh.com/events/open-source>
- Schedule feed: <https://hacktoberfest-api.mlh.com/api/schedule>
