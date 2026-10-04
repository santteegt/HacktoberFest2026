---
name: hf26-challenge
description: Scaffold, audit, and prepare the DEV submission for a Hacktoberfest 2026 challenge folder in this monorepo. Use when the user wants to start a new challenge (Weekend, Week 1-4), asks "what's open now", wants to check a project against a challenge's rules before submitting, or wants a submission draft. Specific to this repo's challenges/ layout.
---

# hf26-challenge

Project-specific workflow for `challenges/NN-<slug>/`. Read `AGENTS.md` first for the rules; this file is the procedure.

## 1. Start a challenge

1. **Find it live.** Call `get_challenges` (devrelay-gateway). Classify by `starts_at` / `ends_at` against today's date (Active / Upcoming / Past). Never start a past challenge. Report days remaining and the deadline in UTC and PDT.
2. **Read the rules.** Call `get_challenge_details` with the ID and read `full_details` fully. If `full_details` is empty, the prompt hasn't dropped; say so and wait, don't guess. Hacktoberfest weeks reveal their theme at launch.
3. **Scaffold.** Pick the next number `NN` (see `challenges/README.md`) and a short slug. Copy `challenges/_template/` to `challenges/NN-<slug>/`.
4. **Create the challenge memory.** `docs/CHALLENGE-MEMORY.md` comes from the template; fill the title and post-material table. From now on append to it as things happen (root `AGENTS.md` rule 8).
5. **Fill `CHALLENGE.md`** with the rules snapshot (fetch date, window in UTC, tag, prompt, theme, judging criteria, prizes, prize categories, requirements) plus the verbatim `full_details`.
6. **Register it.** Add or update the row in `challenges/README.md` and the root `README.md` table. Tick nothing in `STICKERS.md` until the user confirms the submission is live.
7. **Brainstorm from the wiki first.** Read `knowledge-base/hacktoberfest-2026/wiki/index.md` and the pages on tools, ideas, and frameworks, then propose 2-3 ideas with a recommendation. Don't search the web for what the wiki already covers.
8. **Prize categories.** For each category the user wants, load `devrelay-sponsor-skills` (ask before installing anything) and check `hacktoberfest.com/my` for credits (ask before claiming).

## 2. Audit before submitting

Check the project folder against `CHALLENGE.md`, and report pass/fail per item:

- Started in the window: `git log` first-commit date is inside it; later commits are noted in the README.
- Open-source AI is the core, and the README/post says why open matters.
- Public repo, `LICENSE` present (MIT unless told otherwise), `.env.example` present, no secrets (`git grep -nEi 'api[_-]?key|secret|token'` on tracked files).
- Demo works (live link or embed); test credentials supplied if login is needed.
- Each claimed prize category has a concrete, meaningful use.
- README has setup steps, credits for borrowed work, and teammates' DEV handles.

## 3. Draft the submission

0. Read all of `docs/CHALLENGE-MEMORY.md` first. Use its entries for the post, restrict claims to its "may claim" table, include every `HONEST` item, and resolve every `TODO-REPORT` entry or say it was not done.

1. Use the challenge's submission template (from `full_details` or the announcement post) to fill `SUBMISSION.md`. Include the required tag. Writing quality is often weighted most, so write plainly and concretely; run the `humanizer` skill if available.
2. For the optional agent session: use `devrelay-sessions`; scrub keys and sensitive data first and remember uploads are unlisted until made public.
3. Stage with `create_article` (`published: false`, `ai_disclosure_level` left at default). Give the user the draft link and the checklist from `SUBMISSION.md`.
4. **Publish only after an explicit yes** in the current session. After the user confirms it is live, update `challenges/README.md`, `STICKERS.md`, and add a retrospective source to the knowledge base `raw/` folder (what worked, tools, gotchas) and run `okf-wiki`.

## Gotchas

- Hacktoberfest 2026 does not count PRs. Don't suggest PR-based plans.
- One submission per person per challenge; the weekly rounds share a prompt but each needs a fresh project.
- Dates differ across sources (DEV API vs schedule feed). The challenge page wins; flag any mismatch to the user.
- Non-English entries aren't prize-eligible.
