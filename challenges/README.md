# Challenges

One folder per challenge, numbered in order of opening: `NN-<slug>/`. Each folder is a self-contained project plus its submission material.

## Folder contract

| File | Purpose |
| --- | --- |
| `README.md` | Project README (also what judges see in the repo): what, who for, why open matters, setup, demo link, license, credits |
| `CHALLENGE.md` | Snapshot of the challenge rules from `get_challenge_details` → `full_details`, with the fetch date |
| `docs/CHALLENGE-MEMORY.md` | Running log of decisions, findings, measurements, failures and honest limits; feeds the final report. Mandatory, append as things happen |
| `SUBMISSION.md` | Draft of the DEV post following the challenge's submission template, plus a pre-submission checklist |
| everything else | Source code, `LICENSE`, `.env.example` |

Start from [`_template/`](_template) or the `hf26-challenge` skill.

## Index

Dates are in UTC. **Source: DEV Events API (`get_challenges`) and `hacktoberfest-api.mlh.com/api/schedule`, fetched 2026-10-04; Week 2 row re-fetched 2026-10-12; Week 3 row re-fetched 2026-10-19; Week 4 row re-fetched 2026-10-26.**

| # | Folder | Challenge | DEV ID | Tag | Window | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | [`01-weekend-build-for-a-friend`](01-weekend-build-for-a-friend) | Hacktoberfest Weekend Challenge: Build for a Friend (project: **RC Pit Companion**) | 78 | `#hf26challenge` | Oct 2 02:00 → Oct 5 06:59 | ✅ [Published](https://dev.to/santteegt/a-setup-coach-for-my-friends-rc-car-that-stays-on-his-laptop-4ahn) |
| 02 | [`02-week1-touch-grass`](02-week1-touch-grass) | Open-Source AI Challenge: Week 1, Touch Grass (project: **Idea Leash**) | 79 | `#hf26challenge` | Oct 5 18:00 → Oct 12 06:59 | ✅ [Published](https://dev.to/santteegt/idea-leash-an-open-source-walk-buddy-with-a-local-model-for-a-brain-499n) 2026-10-11 23:30 local |
| 03 | [`03-week2-side-hustle`](03-week2-side-hustle) | Open-Source AI Challenge: Week 2, Side Hustle (project: **PartsPaddock**) | 80 | `#hf26challenge` | Oct 12 19:00 → Oct 19 06:59 | ✅ [Published](https://dev.to/santteegt/partspaddock-a-whatsapp-parts-desk-agent-for-rc-clubs-p2p-b2c-market-connecting-hobbyists-14oa) 2026-10-18 23:21 local |
| 04 | [`04-week3-slow-and-steady`](04-week3-slow-and-steady) | Open-Source AI Challenge: Week 3, Slow and Steady (project: **Skunkworks Sloth**) | 81 | `#hf26challenge` | Oct 19 19:00 → Oct 26 06:59 (page; API says Oct 25 06:59) | ✅ [Published](https://dev.to/santteegt/skunkworks-sloth-a-set-of-agents-automating-my-bookmarks-review-keeping-me-focused-and-growing-my-1168) by 2026-10-25 23:32 local |
| 05 | [`05-week4-ghost-in-the-machine`](05-week4-ghost-in-the-machine) | Open-Source AI Challenge: Week 4, Ghost in the Machine (project: _not chosen yet_) | 82 | `#hf26challenge` | Oct 26 19:00 → Nov 1 06:59 (page; API says Oct 31 06:59) | 🟡 Scaffolded, brainstorm pending |
| – | _no code expected_ | Global Hack Week: Hacktoberfest | n/a (MLH event) | n/a | Oct 9 → Oct 15 | 🔵 |

Challenge pages: `https://dev.to/challenges/<slug>` (slugs: `hacktoberfest-weekend-2026-10-01`, `hacktoberfest-week{1..4}-2026-10-{05,12,19,26}`).

### Known data discrepancies (re-check before relying on them)

- **Week 1 start:** the schedule feed and DevRelay KB say Oct 5 **07:00**; the DEV Events API says Oct 5 **16:00**. The Week 4 end differs too (DEV API: Oct 31 06:59; schedule feed and page: Nov 1 06:59); see the Week 4 note below.
- **Week 4 end:** same pattern as Week 3. The DEV Events API says Oct 31 **06:59** UTC (Fri Oct 30, 11:59 PM PDT); `full_details`, the page and the contest rules say Oct 31, 11:59 PM PDT (Nov 1 06:59 UTC). Following the challenge page (author's call, confirmed 2026-10-29: deadline Nov 1 06:59 UTC, publish target Oct 31 22:00 local).
- **Week 3 end:** the DEV Events API says Oct 25 **06:59** UTC (Sat Oct 24, 11:59 PM PDT); `full_details`, the page and the contest rules say Oct 25, 11:59 PM PDT (Oct 26 06:59 UTC). Following the challenge page (author's call, 2026-10-19).
- **Weekend deadline in local time:** Oct 5 06:59 UTC is Sun Oct 4 11:59 PM PDT.
- **Weeks 1–4 share one prompt** ("build something with open-source AI at its core"), with a new theme revealed each Monday. Details are empty until launch.
- **One submission per person per challenge**, and each challenge needs a **new** project started in its window.

## When a new challenge opens

1. `get_challenges` → find the ID; `get_challenge_details` → read `full_details`.
2. Create the folder with the `hf26-challenge` skill (or copy `_template/`), save the rules into `CHALLENGE.md`.
3. Add a row above, and add a `topic` or `idea` source to `knowledge-base/hacktoberfest-2026/raw/` if the theme taught anything reusable.
