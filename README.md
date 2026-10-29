# Hacktoberfest 2026

Monorepo for my Hacktoberfest 2026 challenge entries and the knowledge base behind them.

Hacktoberfest 2026 is run by [MLH](https://mlh.io) and [DEV](https://dev.to), presented by DigitalOcean. The theme is **"AI belongs to everyone"**: build with open-weight models and open-source AI. **Pull requests no longer count.** Rewards come from virtual stickers (see [STICKERS.md](STICKERS.md)), and the DEV Challenges carry cash prizes.

## Challenges

Each challenge lives in its own folder under [`challenges/`](challenges/README.md). I'm starting with the weekend challenge and adding the others as they open.

| # | Challenge | Window (UTC) | Status |
| --- | --- | --- | --- |
| 01 | [Weekend: Build for a Friend](challenges/01-weekend-build-for-a-friend): RC Pit Companion | Oct 2 02:00 → Oct 5 06:59 | ✅ [Published](https://dev.to/santteegt/a-setup-coach-for-my-friends-rc-car-that-stays-on-his-laptop-4ahn) |
| 02 | [Week 1: Touch Grass](challenges/02-week1-touch-grass): Idea Leash | Oct 5 18:00 → Oct 12 06:59 | ✅ [Published](https://dev.to/santteegt/idea-leash-an-open-source-walk-buddy-with-a-local-model-for-a-brain-499n) 2026-10-11 23:30 local |
| 03 | [Week 2: Side Hustle](challenges/03-week2-side-hustle): PartsPaddock | Oct 12 19:00 → Oct 19 06:59 | ✅ [Published](https://dev.to/santteegt/partspaddock-a-whatsapp-parts-desk-agent-for-rc-clubs-p2p-b2c-market-connecting-hobbyists-14oa) 2026-10-18 23:21 local |
| 04 | [Week 3: Slow and Steady](challenges/04-week3-slow-and-steady): Skunkworks Sloth | Oct 19 19:00 → Oct 26 06:59 | ✅ [Published](https://dev.to/santteegt/skunkworks-sloth-a-set-of-agents-automating-my-bookmarks-review-keeping-me-focused-and-growing-my-1168) by 2026-10-25 23:32 local |
| 05 | [Week 4: Ghost in the Machine](challenges/05-week4-ghost-in-the-machine): _project not chosen yet_ | Oct 26 19:00 → Nov 1 06:59 | 🟡 Scaffolded, brainstorm pending |
| – | [Global Hack Week: Hacktoberfest](global-hack-week) (MLH, not a DEV Challenge) | Oct 9 → Oct 15 | 🟡 In progress |

Dates come from live data and have shifted before. Check `challenges/README.md` for the source and discrepancies.

## Global Hack Week: Hacktoberfest

The challenges and hands-on sessions that are exclusive to MLH's Global Hack Week: Hacktoberfest (Oct 9 → Oct 15) live in [`global-hack-week/`](global-hack-week/AGENTS.md), one folder each. They earn GHW points toward stickers (see [STICKERS.md](STICKERS.md)), and none of them are DEV Challenge entries.

## Repo layout

```
AGENTS.md                  Instructions for any AI agent (CLAUDE.md is a symlink)
STICKERS.md                Sticker tracker toward the 3 / 10 / 15 milestones
challenges/                One folder per DEV challenge (+ _template/)
global-hack-week/          GHW: Hacktoberfest challenges and hands-on sessions, one folder each
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
