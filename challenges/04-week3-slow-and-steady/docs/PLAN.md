# Skunkworks Sloth: the clock

Revised 2026-10-24 05:30 UTC (Fri Oct 24, 00:30 local, UTC-5) after the author's feedback. Deadline **Oct 26 06:59 UTC** (Sun Oct 26 01:59 local). **About 49 hours remain**, two of them nights. Publish target **Sat Oct 25, 22:00 local**. The build contract is [SPEC.md](SPEC.md); this file is the schedule and the kill rules.

Working budget: Fri Oct 24 about 10 h, Sat Oct 25 about 12 h. The post, README, demo and agent session get Saturday 16:00-22:00.

## Schedule (local time)

| When | Milestone | Done-means |
| --- | --- | --- |
| Fri 09:00-11:30 | **M0 Feasibility** (five checks in parallel) | results table in the memory; every fallback decided |
| Fri 11:30-16:00 | **M1 Curator** | full Reading List collected, enriched, triaged; two batch reports in `#curator`; Valhalla emptied once |
| Fri 16:00-20:00 | **M2 Coordinator** | 10+ cards, also on the GitHub Project board; focus answered; one pick tapped into `today` |
| Fri 20:00-Sat 12:00 | **M3 Worker** | toy run Fri night; one real prototype on GitHub by Sat noon with notes, cost, brain page |
| Sat 12:00-16:00 | **M4 Freeze and package** | second prototype or fixes; **freeze 16:00**; clean-clone test, README, screenshots, measurements |
| Sat 16:00-22:00 | **M5 Story** | demo video, SUBMISSION.md, agent session, DEV draft staged; publish at 22:00 on the author's yes |
| Sun 00:00-01:59 | margin | last edits on DEV only |

## Kill rules

- A milestone 30 minutes over its clock takes its fallback (listed in SPEC.md), not an extension.
- M0.1: profile-per-channel routing not working by 10:30 → one profile, three skills, channel router.
- M0.2: full triage projected over 2 hours → E4B, or 12B on the 2026 links (590) and a sample of 2025.
- M0.3: fewer than 3 of 5 x.com extracts succeed with the local callback → hosted open-weight model for the browser step only; fewer than 3 with that too → drop Stagehand and the Browserbase category, enrich with HTTP only.
- Auth0/Gmail: not in the MVP (author, 2026-10-24). Runner-up only after M3 ships a real prototype; 90-minute box; if not working, it stays out of the post.
- M2: GitHub Project init + sync not working within its 45-minute box → board markdown files only, Project dropped from the demo.
- M3: no real prototype by Sat 12:00 → the post shows the toy run and says the factory ran once.
- M4: anything not green at 16:00 is cut from the demo and listed as a follow-up in the README.

## Measurements to log as they happen

See SPEC.md "Measurements". Every number goes into `docs/CHALLENGE-MEMORY.md` with date, machine, model and method the moment it exists, not at the end.
