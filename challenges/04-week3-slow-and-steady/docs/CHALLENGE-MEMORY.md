# Challenge memory: Hacktoberfest Open-Source AI Challenge: Week 3 (Slow and Steady)

Running log of everything that should survive into the final report and the DEV post. **Append when it happens, not at the end.** Never delete an entry; if it turns out wrong, add a new entry that marks it `SUPERSEDED by <date>` and says why. Required by the root `AGENTS.md`.

## Entry format

`- YYYY-MM-DD HH:MMZ [TAG] what happened or was learned. Evidence: <file, commit, command, link, or measurement context>.`

Tags: `DECISION` (a choice and why, including options rejected) · `FINDING` (something learned that wasn't obvious) · `MEASURE` (a number, with date, device, model, method) · `FAILED` (something tried that didn't work, and why) · `HONEST` (a limit or caveat the post must state) · `PROCESS` (how the work was done: tools, agents, time) · `QUOTE` (the friend's words, with permission) · `PRIOR-WORK` (anything not created in the window) · `PARTNER` (what a partner tech really did or didn't do) · `TODO-REPORT` (must appear in the report).

Rules: measurements need date, device or machine, model and method, or they don't go in. Backfilled entries say `(backfilled)`. No secrets, no private data.

## Post material by template heading (keep current)

| Heading | Entries to draw on |
| --- | --- |
| What I Built | |
| How I Built It | |
| Why Does Open Innovation Matter? | |
| My Agent Session | |
| The Lazy Payoff | |
| Prize Categories | |

## Claims the post may make / must not make

| May claim (with evidence) | Must NOT claim |
| --- | --- |
| | |

## Log

- 2026-10-19 20:45Z [PROCESS] Folder scaffolded from `_template/` after the window opened (19:00Z), with `AGENTS.md`, rules snapshot, official Week 3 template and MIT `LICENSE`. No project code yet. Evidence: `get_challenge_details` id 81 and the challenge page, fetched 2026-10-19 20:42Z.
- 2026-10-19 20:45Z [FINDING] Deadline mismatch: DEV API `ends_at` is Oct 25 06:59Z (Sat Oct 24, 11:59 PM PDT); `full_details`, the page and the contest rules say Oct 25, 11:59 PM PDT (Oct 26 06:59Z). Plan to publish by the earlier time. Evidence: CHALLENGE.md header. (Plan part SUPERSEDED by 2026-10-19, see the DECISION entry below.)
- 2026-10-19 20:45Z [FINDING] Template changed from Week 2: "My First User" is replaced by an optional "The Lazy Payoff" section (time or effort saved, used this week). Three new partner categories: Auth0 for AI Agents, Browserbase, Ultramarine (Paper Instruments); 20 categories, $2,850 over 21 winners. Evidence: challenge page, 2026-10-19.
- 2026-10-19 20:45Z [TODO-REPORT] Measure the lazy payoff (before/after time or effort, with date, machine, model, method) so the post has a backed number.
- 2026-10-19 21:05Z [DECISION] Deadline follows the challenge page: Oct 26 06:59Z (Sun Oct 25, 11:59 PM PDT), not the DEV API `ends_at` (Oct 25 06:59Z). Author's call; rejected the safer earlier target. Evidence: challenge page and contest rules, fetched 2026-10-19.
- 2026-10-20 03:30Z [PARTNER] Checked the three new Week 3 partners (hub page, vendor docs, web). **Auth0 for AI Agents** (`$100`): sign users in, Token Vault for third-party tokens (Google, GitHub, Slack, Microsoft, Box), CIBA async approval of risky actions, FGA for RAG; free plan 25k MAU with 2 Token Vault connected apps; SDKs for LangChain, LlamaIndex, Vercel AI SDK, Genkit, Cloudflare. Nothing in it is open-source AI; it would be a wrapper around the open core. **Browserbase** (`$100`): Stagehand v4 (MIT, TS + Python) drives a real browser; works with a local Chrome and no Browserbase key, but then needs a pinned model with its own provider key or a custom LLM callback; Ollama is only reachable through the callback (older docs) or Vercel AI SDK (TS only) and the docs warn small local models give inconsistent structured output. Model Gateway (auto model pick) needs Browserbase-hosted browsers. **Ultramarine 1 Flash** (`$100`, Paper Instruments, released 2026-10-14): post-trained from GLM-5.3 Flash for knowledge work (memos, decks, spreadsheets, document reasoning), OpenAI/Anthropic-compatible API at api.paperinstruments.com, $0.15/M in, $0.03/M cached, $0.50/M out (reasoning billed as output, effort low/high/max, default max, 32k output ceiling incl. reasoning), no vision training, $5 credit at hacktoberfest.com/my/promos; **weights "coming soon", not published as of 2026-10-15**, so it is a hosted closed API this week; category text requires stating the run cost. Evidence: dev.to/challenges/hf26, docs.stagehand.dev/configuration/models and /v4/first-steps/quickstart, docs.paperinstruments.com/docs/ultramarine, aicoder.com and wavect.io launch coverage, auth0.com/docs/get-started/auth0-for-ai-agents.md.
- 2026-10-20 03:30Z [HONEST] Ultramarine must not be called open-weight or local in the post unless its weights are on Hugging Face by publish time (re-check before publishing). If used, it is a paid hosted model sitting beside the open core, and the post must state the measured dollar cost of the run.
- 2026-10-20 03:30Z [FINDING] No sponsor Agent Skills are published for the Week 3 MLH event (`list_event_agent_skills` returned an empty list), so partner integrations go by the vendor docs above.
