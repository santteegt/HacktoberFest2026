# Skunkworks Sloth: plan for the time left

Written 2026-10-24 05:00 UTC (Fri Oct 23, 23:59 local, UTC-5). Deadline **Oct 26 06:59 UTC** (Sun Oct 26 01:59 local). **50 hours remain**, two of them nights. Publish target: **Sat Oct 25, 22:00 local** (03:00 UTC Sun), which leaves the playbook's margin for last edits on DEV.

Working budget: Fri Oct 24 (about 10 h), Sat Oct 25 (about 12 h). Everything below fits in those 22 hours or it is cut. The post, README, demo and agent session get the last 6 hours of Saturday.

## What ships (MVP)

1. **Collect:** Chrome `Bookmarks` JSON (both profiles) → Postgres on Tiger Data (links, folders, `saved_at` hypertable), deduped by canonical URL. Gmail newsletter links only if the Auth0 Token Vault read works in under an hour; otherwise skipped and said so.
2. **Enrich:** HTTP status, final URL, title, readable text for a sample; GitHub API stars and last commit for github.com links (1,122 of them, no model). No Stagehand in the MVP.
3. **Triage (local Gemma 4 through Ollama):** one JSON schema per link: topic, vertical, kind, still_relevant + reason, buildable 0-3, one_line_idea. Dead links and stale repos decided in code; the model judges the rest. Run over all 7,845; measure wall time, tokens and agreement with the author's own labels on 40 links.
4. **Board:** clusters per vertical as markdown cards (learning goal, prototype idea, 2 h box, links, kill criteria) in `board/`; columns Inbox → Triaged → Backlog → Today → Built → Archived.
5. **Daily pick:** Hermes profile on Telegram (Discord is a config switch): "what are you in the mood for?" with 3-4 options drawn by code; the model writes only the wording.
6. **Prototype box:** Hermes profile with a coding skill, open-weight model on OpenRouter (model id and cost recorded per run), fresh repo from a template, 2 h box, `NOTES.md` at the end. At least **one real prototype** finished by Saturday noon, a second if time allows.
7. **Second brain + publish:** card + notes → an OKF-style wiki page (plain markdown); repo pushed to GitHub; CIBA push approval through Auth0 before the push goes public, if the Auth0 flow is working by Saturday morning; otherwise a Telegram confirm button and Auth0 is dropped from the categories.

## Partner categories to enter

- **Gemma** (core, certain) · **Tiger Data** (certain, known from Week 2) · **Auth0 for AI Agents** (one flow only: CIBA approval before publishing, or Token Vault for Gmail; whichever works first) · **Entire** only if `entire enable` on the prototype repo costs under 30 minutes.
- **Cut from this week:** Browserbase (X and Facebook extraction become a documented follow-up; the Chrome pile alone makes the story true), DigitalOcean, Temporal, SerpApi, Sentry, Ultramarine, Backboard, Render/.tech.

## Schedule

**Fri Oct 24 (local)**

- 09:00-11:00 Feasibility, in parallel: (a) Chrome JSON → Postgres with dedupe; (b) Gemma 12B triage schema on 200 random links, timing and a 40-link agreement check; (c) one card through two OpenRouter open-weight models via Hermes, cost per run; (d) Auth0 tenant + CIBA push on the free plan, time-boxed to 60 min.
- 11:00-13:00 Collect + enrich over the full pile; GitHub API pass.
- 14:00-17:00 Full triage run (background), board generator, first cards.
- 17:00-19:00 Hermes Telegram profile: daily pick flow; first pick by the author.
- 19:00-21:00 Prototype box end to end on a toy card; template repo; `NOTES.md`.
- Log every measurement in `docs/CHALLENGE-MEMORY.md` as it happens.

**Sat Oct 25 (local)**

- 09:00-12:00 First real prototype from the author's pick (the agent builds, the author reviews); wiki page; GitHub push with the approval step.
- 12:00-14:00 Second prototype or fixes; Gmail collector if Auth0 Token Vault is already working; Entire if trivial.
- 14:00-16:00 **Feature freeze at 16:00.** Clean-clone test, `.env.example`, README, LICENSE check, screenshots by script, measurements consolidated.
- 16:00-19:00 Demo video (triage stage with Wi-Fi off, then the Telegram pick, then the prototype run), SUBMISSION.md from the memory file's may-claim table, agent session curated and scrubbed.
- 19:00-21:00 Stage the DEV draft (`published: false`), fix images (commit SHA URLs), read the post aloud once.
- 22:00 Publish on the author's yes. Then update the repo READMEs, STICKERS.md, retrospective in `raw/`, `/okf-wiki`.

**Sun Oct 26, 00:00-01:59 local:** margin only; no new features.

## Kill rules

- Any feasibility check that is not green by Fri 11:00 is replaced by its fallback (Telegram confirm instead of CIBA, SQLite instead of Tiger if the connection fights back, one model instead of a comparison).
- If the full triage of 7,845 links is slower than 2 hours on the M4 Max, triage the 2025-2026 pile (2,296) fully and sample the rest; say so.
- If no real prototype exists by Sat 12:00, the post shows the toy prototype and says the factory ran once.

## Measurements to capture (date, machine, model, method)

- Bookmarks collected, deduped, dead, stale, kept.
- Triage: links per minute, tokens, wall time, model tag, `num_ctx`; agreement on 40 hand-labelled links.
- Prototype: minutes from pick to running skeleton; OpenRouter model id and dollars per run.
- Human time: minutes the author spent answering picks and skimming the board this week.
