# Retrospective: Weekend Challenge "Build for a Friend" (RC Pit Companion)

Written 2026-10-05, right after publishing. Source of truth for the details is the project's running log, `challenges/01-weekend-build-for-a-friend/docs/CHALLENGE-MEMORY.md`. Outcome is not known yet: winners are announced the week of Oct 5.

## What was built

RC Pit Companion: an offline-by-design setup coach and setup vault for one friend's 1/10 touring car (Yokomo BD12). The friend speaks or taps how the car feels, a hand-reviewed lever table picks one change, Gemma 4 (via Ollama) understands the sentence and phrases the answer, and a local vault stores setups with track conditions so he can find them on race day. Post: https://dev.to/santteegt/a-setup-coach-for-my-friends-rc-car-that-stays-on-his-laptop-4ahn · Code: https://github.com/santteegt/HacktoberFest2026 (folder `challenges/01-weekend-build-for-a-friend`).

Partner categories entered: Gemma (real use: both language steps) and Mastra (real use: the coach workflow with two suspend points). Everything else was skipped on purpose (see the partner catalog).

## Timeline (author's local time, UTC-5)

- Oct 4, 00:47 to about 11:40: repo, knowledge base and skills set up; partner triage by a research subagent; two idea deep dives.
- Oct 4, 14:34 to 15:35: idea chosen (RC Pit Companion), scaffold committed (first commit 14:37), phone spike run and failed, switch to laptop + Ollama, frozen notes snapshot imported (15:34).
- Oct 4, about 16:00 to 18:30: implementation plan written, 12 lever rows reviewed by the author, build done by subagents in parallel (T0 to T12), clean-clone test passed about 18:30.
- Oct 4, 21:00 to Oct 5, 00:30: README, post draft, the friend's own sentences, first speed reading from his laptop, bugs found on his laptop, screenshots, architecture diagram, demo video, agent session, publish at 00:26 on Oct 5 (about 1.5 h before the 01:59 deadline).

## What worked

- **One real person, one real quote.** The friend's words ("quickly store my settings and get feedback from what works, what might have affected my run") put the vault on equal footing with the coach, which a generic "RC coach" would not have.
- **The model never invents numbers.** Two small language jobs (classify, phrase); everything else is a reviewed table, clamps and plain code, with a number guard and template fallback. It made the safety story simple and the accuracy claims checkable.
- **A frozen, credited knowledge snapshot** (sha256 manifest, `npm run kb:verify`) kept "new work only" honest while still using the author's earlier notes.
- **A running challenge memory with a may-claim / must-not-claim table.** The post was written from it; it stopped several overclaims (phone support, offline voice, partner use).
- **Subagents with file ownership and orchestrator-only commits.** Opus for hard parts (plan, workflow, explainers, integration), Sonnet for plumbing. Parallel work did not collide because each task card named the files it owned, its own port and its own database.
- **A fresh-clone test** found that the documented install did not work (the generated knowledge index was not in the repo). Fixed before anyone else hit it.
- **Scripted screenshots** (headless Chrome driven over the DevTools protocol, real buttons, real model) gave an honest image walkthrough in minutes, instead of hand-captured and hand-edited images.
- **Honest limits in the post** (numbers with machine, model and method; an estimate called an estimate) read better than a polished claim and cost nothing.

## What went wrong, and what it cost

- **Phone spike failed.** Gemma 4 E2B in a phone browser (LiteRT-LM, WebGPU) downloaded but lagged too much. Cost: about 1 h, and the phone preference of the friend was dropped. The runtime also fetched its WASM from jsDelivr by default, which would have broken any offline claim; self-hosting was needed.
- **Every accuracy test ran on the wrong model.** All evals used E4B (author's Mac); the friend's laptop runs E2B. On E2B the classifier fell back to the first symptom on anything it could not place, so the coach answered "reduce caster" to "hello". Found only when the author used the app on the friend's laptop, about 2 h before the deadline. Fix: a deterministic off-topic gate in front of the model (E2B 21/25 alone, 23/25 with it; the gate's word list is partly tuned on the test). **Lesson: run the eval on the smallest model the friend will actually run, on day one, before building anything on top of it.**
- **Dead-end first run.** Voice input defaulted to off with no pointer to Settings. Found on the friend's laptop. Fix: default on-device, and an actionable message.
- **Speed.** The only reading from his 2019 Intel MacBook Pro (CPU-only): about 9.2 tokens/s writing and 38.7 tokens/s reading a prompt on E2B. That makes a typed turn about 25 s and a chip turn about 15 s (estimates, the app itself was never timed there). A setting turns the model's wording off. Prompt length, not caching, sets latency: Ollama did not reuse a shared prefix when the user text differed.
- **Clock errors.** Several agent-written timestamps and time-left figures were wrong (a UTC reading used as local time). **Lesson: always read `date` and state local time; never reuse an earlier clock reading.**
- **A guide nobody could find.** The getting-started page existed but was not linked from the README or the post until the author asked. **Lesson: when something is made for users, link it from the places users start, at the time it is made.**
- **Tooling friction on DEV.** `update_article` on a 16 KB body failed on the first try several times ("outcome unknown"); the write had not landed, so the fix was to check with `get_my_articles` and retry once. A raw session upload showed 0 parsed messages; submitting a curated, normalised `curated_data` payload of about 30 KB worked on the third attempt.
- **Small process slips.** A `git add -A` swept an unrelated, user-installed skill folder into a README commit; the agent hit its session limit twice mid-build.

## Numbers worth remembering

| Item | Value | Where / caveat |
| --- | --- | --- |
| Symptom eval, E4B | 24/25 | 25 cases, 20 in the author's wording, 5 in the friend's; M4 Max |
| Symptom eval, E2B | 21/25 alone, 23/25 with the gate | same set; the gate is partly tuned on it |
| Friend's 5 sentences | E2B 5/5, E4B 4/5 | one miss was an ambiguous label |
| Fresh phrasings (written before running) | 13/14 on E4B | orchestrator-written |
| Notes retrieval (MiniSearch, 113 chunks) | 9/10 held-out | n=10, same agent that built the fixes |
| Classifier prompt | 389 to 252 tokens, accuracy unchanged on the 25 cases | below 252 it lost cases |
| Lever table | 61 rows, 12 reviewed by the author | the app shows a draft badge on the rest |
| Friend's laptop speed, E2B | 9.2 tok/s decode, 38.7 tok/s prefill | one `ollama run --verbose` prompt |
| Clean-clone install | `npm ci` 3 s | Node 24.13.0 |
| Tests | 94 | engine, vault, analysis, UI logic, voice, search |

## Playbook for the next challenges

1. **Day one:** get the friend's (or user's) exact hardware and run the smallest candidate model on it with the real prompt. Decide the model from that, not from the dev machine.
2. **Eval on the target model**, including off-topic and gibberish inputs; add a deterministic gate for refusals instead of trusting a small model to refuse.
3. **Keep the model's job tiny** and put numbers, rules and safety in plain code; it is what makes small local models usable on CPU.
4. **Write the challenge memory from the first hour**, with a may-claim table, and write the post from it.
5. **Freeze features at T minus 3 hours.** Use the last stretch for the clean-clone test, the demo recording, screenshots, the post and the agent session; the post is judged most heavily.
6. **Record the demo on the real target device**, with the network visibly off if that is the claim.
7. **Stage the DEV post early** (`published: false`), then iterate; check for leftover TODO comments before publishing; link every helper doc from the README and the post.
8. **Capture screenshots by script** against a clean database and say they are demo data.
9. **Curate the agent session** (prompts and final replies, scrubbed) rather than uploading a raw 19 MB transcript; keep it short enough to inline.
10. **Pick partner categories only where the code really uses them**, and say which parts are not open.

## Open items after publishing

- Outcome unknown; friend was very happy but has not yet used it at a real practice session.
- 49 of 61 lever rows are still drafts; the E2B in-scope accuracy is lower than E4B's and unchanged.
- The app's own speed on the friend's laptop (chip turn, typed turn, phrasing off) is still unmeasured.
- The caster explainer is too small at its default framing and the roll-centre diagram's caption overlaps its own text on the scene test page.
- This retrospective and the partner catalog live in the knowledge base, outside the project folder, so they do not count as project commits.
