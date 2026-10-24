# Skunkworks Sloth: the clock

Revised 2026-10-24 16:40 UTC (**Sat Oct 24, 11:40 local**, UTC-5) for parallel execution. Earlier versions of this file labelled Oct 24 as Friday and Oct 25 as Saturday; that was wrong (Oct 24, 2026 is a Saturday). The hour arithmetic was right; the day names are fixed here.

Deadline **Mon Oct 26 06:59 UTC** (Mon 01:59 local). **About 38 hours remain**, one night included. Publish target **Sun Oct 25, 22:00 local**. Product contract: [SPEC.md](SPEC.md). Who builds what in parallel: [LANES.md](LANES.md).

## Schedule (local time)

| When | Who | Milestone | Done-means |
| --- | --- | --- | --- |
| Sat 12:00-13:00 | coordinator | **C0 contracts** | skeleton, deps, schema on Tiger, shared types, config, notify, LLM helper, fixtures, profile models switched, lane logs; committed to `main` |
| Sat 13:00-16:00 | 3 lanes | **M0 inside each lane** (L1: triage sample; L2: GitHub Project; L3: Stagehand + OpenRouter model) and first modules on fixtures | **CP1 16:00**: results in lane logs, merged, fallbacks decided |
| Sat 16:00-20:00 | 3 lanes | **M1 Curator / M2 Board / M3a Builder** on real data | **CP2 20:00**: merged; integration run curate → board → Discord pick → toy `work` run; gateway up |
| Sat night | L1 | finish triage batches | full Reading List in `triage` |
| Sun 09:00-12:00 | author + L3 | **M3b** first real prototype from the author's pick | **CP3 12:00**: real prototype built, approved, synced, brain page |
| Sun 12:00-15:00 | lanes | runner-ups only if CP3 is green (Gmail via Auth0, Project read-back, X bookmarks, second prototype) | each inside its box or dropped |
| Sun 15:00 | all | **Freeze** | lanes stop; clean-clone test, README, screenshots |
| Sun 15:00-21:00 | coordinator (+1 lane for screenshots/README) | **M5 story** | demo video, SUBMISSION.md from the memory, agent session, DEV draft staged |
| Sun 22:00 | author | publish on the author's yes | then repo READMEs, STICKERS.md, retrospective, `/okf-wiki` |
| Mon 00:00-01:59 | | margin | last edits on DEV only |

## Kill rules

- A lane 30 minutes past a checkpoint on an item takes that item's fallback; it does not extend.
- L1 / M0.2: full triage projected over 2 hours → E4B, or 12B on the 2026 links (590) and a sample of 2025.
- L3 / M0.3: fewer than 3 of 5 x.com extracts with the local callback → hosted open-weight model for the browser step only; fewer than 3 with that too → drop Stagehand and the Browserbase category, HTTP-only enrich.
- L2 / GitHub Project: init + sync not working within its 45-minute box → markdown board only, Project dropped from the demo.
- Coordinator / M0.1: `hermes -p <profile> send` posting as the wrong bot → `notify` calls the Discord REST API with each profile's token directly.
- L3 / M3b: no real prototype by Sun 12:00 → the post shows the toy run and says the factory ran once; runner-ups are cancelled.
- Auth0/Gmail: runner-up only after CP3; 90-minute box; otherwise out of the post.
- Freeze: anything not green at Sun 15:00 is cut from the demo and listed as a follow-up in the README.

## Measurements to log as they happen

See SPEC.md "Measurements". Lanes write them in `docs/lanes/<lane>.md` with date, machine, model and method; the coordinator folds them into `docs/CHALLENGE-MEMORY.md` at each checkpoint.
