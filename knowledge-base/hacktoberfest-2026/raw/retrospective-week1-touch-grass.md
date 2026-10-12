# Retrospective: Week 1 "Touch Grass" (Idea Leash)

Written 2026-10-11 (local time, UTC-5), right after publishing. Source of truth for the details is the project's running log, `challenges/02-week1-touch-grass/docs/CHALLENGE-MEMORY.md`. Outcome is not known yet: winners are announced the week of Oct 12.

## What was built

Idea Leash: an open-source walk buddy for one person who walks a dog in the morning and does a fast evening walk with a podcast. The author sends a podcast link to a Telegram bot, the Mac transcribes it and writes verified notes into an OKF markdown wiki plus a five-question quiz, a phone web app records the walk (GPS, voice ideas, offline queue), and after the walk the Mac sends a summary and the quiz is taken in Telegram with buttons. Sixteen badges, streaks and distances are plain code. A "Leash agent" (a Hermes profile in a Lume macOS VM) is the ambient front door in Telegram.

Open pieces, all on one M4 Max Mac: Gemma 4 12B QAT through Ollama, Hermes Agent v0.21.6, whisper.cpp (large-v3-turbo), graphify with faster-whisper, Piper, Lume, a standard-library Python tool server and a one-file phone app. Not open: Telegram, Tailscale, SerpApi, the podcast host, macOS in the VM.

Post: https://dev.to/santteegt/idea-leash-an-open-source-walk-buddy-with-a-local-model-for-a-brain-499n (published 2026-10-11 23:30 local, about 2.5 h before the deadline). Demo video: https://youtu.be/ikb7P_XMQAw. Partner categories entered: Gemma (real use: notes, quiz, grading wording, chat) and SerpApi (real use: voice-requested web search, capped at 8 a day). Everything else skipped on purpose.

## Timeline (author's local time, UTC-5)

- Oct 5, evening: folder scaffolded from the template (04:37 UTC on Oct 6), live challenge details read, wiki read before brainstorming.
- Oct 6 to 8: five brainstorm rounds with subagents; idea chosen (Idea Leash v2); open stack tested on the target Mac; `podcast-quiz` skill built with four eval iterations (27/27 checks with the verifier, 20/27 for a plain prompt).
- Oct 8 to 9: ingest pipeline, tool server, Hermes profile in a Lume VM, Telegram gateway; four real test walks with a throwaway page found that a hidden web page gets no GPS; first real walk with the app (35 min, no gaps); first full Telegram quiz (5 of 6).
- Oct 10: offline dog walk uploaded after reconnecting; voice-requested search; podcast walk and quiz; the 12B told the author a wrong answer was right, so the Mac now sends grades and "podcast ready" itself; launchd services.
- Oct 11: vault promoted from the test vault to the real one; one real walk interruption handled; agent session saved to DEV (session 786) and made public; post drafts v1 to v8 with an Opus reviewer, an Opus editor and the humanizer pass; diagram redone twice; demo video recorded by the author; published 23:30.

## What worked

- **A hard rule for the model: language jobs only.** Distances, scores, badges, streaks, scheduling and every message that has to be true are code. After the 12B praised a wrong answer, moving grades and "ready" messages to the Mac removed the failure instead of prompting around it.
- **Verifier plus repair loop beat prose instructions.** The quiz skill's checking script (quote must exist in the transcript, spoken length, answer-length bias) did more than the SKILL.md text. Free local calls made up to three regenerations per quiz affordable.
- **Putting the instruction in the tool's reply.** The 12B ignored a paragraph in a skill and asked in plain text; an `action` field in the `leashctl next` reply made it call the buttons tool.
- **Real walks, early.** The GPS finding (no fixes while a page is hidden, one-time location permission lost when backgrounded) came from four short real walks and would not have appeared in any desktop test. It reshaped the app (screen stays on behind a black cover).
- **launchd services and a trust-SSH-not-`lume ls` check** made the stack survive sleep, wake and crashes without babysitting.
- **The challenge memory and its may-claim / must-not-claim table.** It stopped overclaims (fully open stack, phone offline AI, an open versus closed comparison that was never run) and let the post be written quickly from dated facts.
- **Reviewer subagents, checked.** An Opus reviewer and editor improved the post's structure and found stale text; their overstatements (Piper described as used in the quiz, "whole loop works", "tested only with a fake Telegram") were caught by checking each claim against the log.
- **Publishing with a margin.** Feature freeze about three hours before the deadline and publishing 2.5 h early left room for the final edits the author wanted.

## What went wrong, and what it cost

- **Secrets did not reach the shell tool.** The agent's token was missing for two tests until `terminal.env_passthrough` and the skill's `required_environment_variables` were set.
- **The model replayed an old error from its chat history** and answered "token missing" after it was fixed. Fix: persona rule "old errors do not count" and a fresh session.
- **Voice notes failed ("STT unavailable")** because faster-whisper was not in the VM; solved by a command speech provider that calls whisper.cpp on the Mac.
- **Host sleep killed the tunnel and the gateway.** Fixed with launchd agents; `lume ls` reported a running VM as stopped, so the start script trusts SSH.
- **An unshuffled, unverified quiz was served** (every correct answer in position A). Now code always shuffles, labels a quiz `ok`, `partial` or `failed`, and never serves a failed one.
- **Two model names and two context sizes made Ollama reload the model at every hand-off.** One alias and one context size fixed it (found through Ollama's loaded-model endpoint).
- **A search query started with "the web about..."** and returned films. Leading filler is now stripped, verified with one real search.
- **Test notes polluted the real vault.** Fixed by promoting only ten real notes to the new vault with a script.
- **DEV cached the old diagram.** Replacing the PNG at the same URL did not change the post; changing the URL (commit-pinned) did. When DEV publishes it re-hosts images anyway.
- **Editing the draft on DEV and locally at once.** Every update through the API replaces the whole body, so each update started with a fetch of the live draft to avoid overwriting the author's edits.
- **A long post.** The final body was about 2,600 words with tables. The author cut the test-sessions table, the OKF subsection and the "what the tests changed" list in the final pass; the argument was clearer shorter.
- **Things never done:** no closed-API comparison, no fine-tuning, no scheduled nudges (the "ambient" agent speaks when something happened, not on a timer), no cold-open offline test, no second phone, screenshots rendered at phone width in a desktop browser rather than captured on the phone.

## Numbers worth remembering

| Item | Value | Where / caveat |
| --- | --- | --- |
| 30.7 and 56.7 minute episodes to notes and quiz | 477 s and 1,090 s | about a third of the episode length, M4 Max, two episodes |
| Quiz skill checks | 27/27 with verifier, 20/27 plain prompt | three transcripts, local 12B, one run per cell |
| Chat requests to the local model, first day | 183, all local | Ollama log, tests included |
| 15 second voice clip, whisper.cpp | 0.95 s | one measurement on the Mac |
| First real walk with the app | 2,116 of 2,117 s tracked, 3.15 km | median accuracy 6.9 m, Redmi Note 11, Chrome 154 |
| Hidden page GPS | zero fixes in about 6 minutes | screen off or another app in front |
| Offline dog walk | uploaded about 30 s after reconnecting | one walk, three voice notes |
| Services crash test | back within about 25 s | killed the server and tunnel by hand |
| Battery, screen on behind the cover | 0.1 to 0.17 % per minute | three walks, 1 % resolution |
| Agent turn latency | most 0.7 to 7 s, three outliers of 1 to 2.5 min | unexplained |
| Totals after four app walks | 7.66 km, 112 min, nine voice ideas, 7 of 16 badges | one person, one phone |

## Playbook for the next challenges

1. **Test on the real device and a real outing on day one**, and expect the platform to surprise you (hidden web pages get no GPS).
2. **Keep the model's job to language**; make anything the user must be able to trust (grades, readiness, distances) a code path that does not pass through the model.
3. **Put the next-step instruction in the tool's reply**, not in a paragraph the small model may skip.
4. **Write the verifier first** for anything the model generates, and log how many tries it needed.
5. **Keep the memory file and the claims table from hour one**; write the post from it, and check every reviewer-agent edit against it.
6. **Fetch before you overwrite** when the author edits a draft in the DEV editor, and change the image URL when replacing an image DEV already shows.
7. **Freeze features about three hours early and publish with a margin**; the last hours go to the demo, the diagram and a final read.
