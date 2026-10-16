# AGENTS.md: Global Hack Week: Hacktoberfest

Instructions for work inside `global-hack-week/`. They add to the repo-level `../AGENTS.md`, which still applies. `CLAUDE.md` here is a symlink to this file.

This folder holds the **challenges and hands-on sessions that belong only to Global Hack Week (GHW): Hacktoberfest**. It is not a DEV Challenge, so nothing here goes under `../challenges/` and nothing needs a DEV post.

## What GHW: Hacktoberfest is

- **Organizer:** MLH. Free, online, week-long, open to all levels. It counts toward Hacktoberfest 2026 stickers (see [`../STICKERS.md`](../STICKERS.md), section "Global Hack Week: Hacktoberfest").
- **Window:** Fri Oct 9 → Thu Oct 15, 2026 (event times are America/New_York). Opening ceremony Oct 9 10:00 ET, "Today in Global Hack Week" Days 2 to 6 on Oct 10 to 14 at 12:00 ET, closing ceremony Oct 15 12:00 ET.
- **Event:** <https://events.mlh.io/events/14553-global-hack-week-hacktoberfest> (MLH slug `global-hack-week-open-source-90`). Verified with `search_mlh_events` and `get_events` on 2026-10-10.
- **Points:** challenges earn experience points, and each live-session check-in earns one point (per the opening-ceremony description). Sticker thresholds are 15, 30 and 75 points, plus the registration challenges and a livestream check-in. MLH does not publish per-challenge point values.
- **Mechanics:** daily Twitch workshops (`https://www.twitch.tv/mlh`), Discord mini-events (`https://discord.mlh.io`), and a challenge dashboard. Some challenges are completed live on the stream.

Background and general rules: `get_knowledge_document` topic `global-hack-week` (static guide, last verified 2026-09-30).

## Layout

One folder per challenge or per hands-on session, flat, named by slug. Each folder is self-contained.

```
global-hack-week/
  AGENTS.md                    This file (CLAUDE.md is a symlink)
  <slug>/                      One challenge or one hands-on session
    README.md                  What it is, type (challenge | session), source link, how to run, result
    docs/CHALLENGE-MEMORY.md   Running log, same format as ../challenges/_template/docs/
    ...                        Code, assets, LICENSE, .env.example
```

Rules for a folder:

1. **Name it by slug**, such as `workshop-gemma-gradient`. Put the type (challenge or session) in its `README.md`, not in the folder name.
2. **Record the source in the README**: challenge title and dashboard link, or the session title, date and time (ET), speaker or partner, and the recording link once it exists.
3. **Hands-on sessions** are follow-along builds from a workshop. Keep the code the session produced, note what you changed, and credit the presenter and partner.
4. **No sharing code by import** between folders. Copy it. Same rule as `../challenges/`.
5. **Licensing and secrets** follow the root rules: MIT unless stated otherwise, never commit keys, commit `.env.example`.
6. **Keep `docs/CHALLENGE-MEMORY.md` current** the moment something relevant happens (decisions, measurements, failures, honest limits, points earned and how). Append only. Never record secrets.

## Index

| Folder | Type | Source | Status |
| --- | --- | --- | --- |
| [`tiger_data`](tiger_data/) | session | Tiger / TimescaleDB IoT sensor simulation tutorial on `tigerdata-demo` | Deployed 2026-10-13; see folder README |
| [`tiger-data-pipeline`](tiger-data-pipeline/) | session | Twelve Data → Tiger Cloud → self-hosted Grafana pipeline (Python + uv) | Scaffolded 2026-10-16 (Compose + uv deps) |
| [`challenge-1`](challenge-1/) | challenge | Local weather + 5-day forecast PWA (Open-Meteo); GHW dashboard <https://ghw.mlh.io/challenges> | Scaffolded + working static PWA 2026-10-13 |
| [`challenge-2`](challenge-2/) | challenge | 1/10 FWD touring-car body-shell sprites from `BASE_PROMPT.md` + CA45 schematics; multi-model entries | Three agent entries + comparison README 2026-10-14 |

Add a row when you create a folder.

## Rules for agents

1. **Verify live data before stating it.** The challenge list, point values and schedule change. Use the challenge dashboard at <https://ghw.mlh.io/challenges> (it redirects to the current event's page on mlh.com), <https://ghw.mlh.com/schedule>, and `get_events` / `search_mlh_events`. The schedule page can lag, so cross-check on `events.mlh.com`. Never quote a point value or challenge from memory.
2. **Check-ins and codes.** Daily sessions use `code_required` self check-in. Never guess or invent a venue code, and ask the user before checking in with `check_in_to_mlh_event`.
3. **Claims and installs.** Sponsor credits (`list_event_offers`, `claim_promo_code`) and sponsor skills (`list_event_agent_skills`) need a yes from the user first.
4. **Submitting is the user's call.** If a challenge asks for a project submission, use `devrelay-mlh-submissions`, stage it, and submit only after an explicit yes in the current session. Do not publish DEV posts about GHW work without the same yes.
5. **Keep the tracker honest.** Tick boxes in `../STICKERS.md` from the Hacktoberfest dashboard (<https://hacktoberfest.com/my/>), not from memory of what you completed.
6. **Distinguish from the DEV Challenges.** The Hacktoberfest Open-Source AI Challenge weeks (DEV events 79 to 82) are separate and live in `../challenges/`. A GHW project may not be reused as a DEV Challenge entry unless it was started inside that challenge's window.
