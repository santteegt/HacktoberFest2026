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

Dates are in UTC. **Source: DEV Events API (`get_challenges`) and `hacktoberfest-api.mlh.com/api/schedule`, fetched 2026-10-04.**

| # | Folder | Challenge | DEV ID | Tag | Window | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | [`01-weekend-build-for-a-friend`](01-weekend-build-for-a-friend) | Hacktoberfest Weekend Challenge: Build for a Friend (project: **RC Pit Companion**) | 78 | `#hf26challenge` | Oct 2 02:00 → Oct 5 06:59 | 🟡 In progress |
| 02 | _not created yet_ | Open-Source AI Challenge: Week 1 | 79 | `#hf26challenge` (confirm) | Oct 5 → Oct 12 | 🔵 Details drop at launch |
| 03 | _not created yet_ | Open-Source AI Challenge: Week 2 | 80 | confirm | Oct 12 → Oct 19 | 🔵 |
| 04 | _not created yet_ | Open-Source AI Challenge: Week 3 | 81 | confirm | Oct 19 → Oct 26 | 🔵 |
| 05 | _not created yet_ | Open-Source AI Challenge: Week 4 | 82 | confirm | Oct 26 → Nov 1 | 🔵 |
| – | _no code expected_ | Global Hack Week: Hacktoberfest | n/a (MLH event) | n/a | Oct 9 → Oct 15 | 🔵 |

Challenge pages: `https://dev.to/challenges/<slug>` (slugs: `hacktoberfest-weekend-2026-10-01`, `hacktoberfest-week{1..4}-2026-10-{05,12,19,26}`).

### Known data discrepancies (re-check before relying on them)

- **Week 1 start:** the schedule feed and DevRelay KB say Oct 5 **07:00**; the DEV Events API says Oct 5 **16:00**. The Week 4 end differs too (DEV API: Oct 31 06:59; schedule feed: Nov 1 06:59). Treat the challenge page as authoritative once the details drop.
- **Weekend deadline in local time:** Oct 5 06:59 UTC is Sun Oct 4 11:59 PM PDT.
- **Weeks 1–4 share one prompt** ("build something with open-source AI at its core"), with a new theme revealed each Monday. Details are empty until launch.
- **One submission per person per challenge**, and each challenge needs a **new** project started in its window.

## When a new challenge opens

1. `get_challenges` → find the ID; `get_challenge_details` → read `full_details`.
2. Create the folder with the `hf26-challenge` skill (or copy `_template/`), save the rules into `CHALLENGE.md`.
3. Add a row above, and add a `topic` or `idea` source to `knowledge-base/hacktoberfest-2026/raw/` if the theme taught anything reusable.
