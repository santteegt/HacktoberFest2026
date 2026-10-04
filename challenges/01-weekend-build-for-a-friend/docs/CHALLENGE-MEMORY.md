# Challenge memory: Hacktoberfest Weekend Challenge: Build for a Friend (RC Pit Companion)

Running log of everything that should survive into the final report and the DEV post. **Append when it happens, not at the end.** Never delete an entry; if it turns out wrong, add a new entry that marks it `SUPERSEDED by <date>` and says why. Required by the root `AGENTS.md`.

## Entry format

`- YYYY-MM-DD HH:MMZ [TAG] what happened or was learned. Evidence: <file, commit, command, link, or measurement context>.`

Tags: `DECISION` (a choice and why, including options rejected) · `FINDING` (something learned that wasn't obvious) · `MEASURE` (a number, with date, device, model, method) · `FAILED` (something tried that didn't work, and why) · `HONEST` (a limit or caveat the post must state) · `PROCESS` (how the work was done: tools, agents, time) · `QUOTE` (the friend's words, with permission) · `PRIOR-WORK` (anything not created in the window) · `PARTNER` (what a partner tech really did or didn't do) · `TODO-REPORT` (must appear in the report).

Rules: measurements need date, device or machine, model and method, or they don't go in. Backfilled entries say `(backfilled)`. No secrets, no private data.

## Post material by template heading (keep current)

| Heading | Entries to draw on |
| --- | --- |
| What I Built | friend persona, idea choice, scope (1/10 touring car, BD12), setup vault |
| How I Built It | Ollama + Gemma 4 E4B QAT, frozen KB snapshot + chunk build, symptom-to-lever table (reviewed), Mastra (if used), voice, 3D view |
| Why Does Open Innovation Matter? | offline at the track, no per-question cost, inspectable and correctable knowledge, swappable model; plus where closed/hosted partners did not fit |
| My Agent Session | DEV session 504 (private until made public): repo setup, research, phone spike |
| Prize Categories | Gemma (via Ollama), Mastra (only if it truly runs the workflow); Entire dropped (workload); everything else deliberately skipped, with reasons |

## Claims the post may make / must not make

| May claim (with evidence) | Must NOT claim |
| --- | --- |
| Code written in the challenge window (see `git log`) | That the app has "no pre-existing work": the touring-car knowledge comes from a pre-window notebook and wiki |
| The coach never invents numbers: values come from a hand-reviewed lever table (once built and reviewed) | Phone support, or that Gemma runs on a phone: the phone spike failed |
| Knowledge snapshot is frozen and hash-verified (`npm run kb:verify`) | Offline voice, until verified on the target laptop |
| Phone spike method and outcome as recorded in `docs/PHONE-SPIKE.md` | Any partner technology the code does not actually use |
| | Any number that is not in a MEASURE entry |

## Log


### Decisions

- 2026-10-04 (backfilled) [DECISION] Built the RC Pit Companion instead of the Community Skunkworks agent. Why: the friend and the pit-table moment are concrete, the demo (voice, 3D car, airplane mode) is vivid, and the story is personal. Runner-up had the stronger privacy argument and lower technical risk but a vaguer "friend" and a board-UI demo on synthetic data. Evidence: research notes in the local, gitignored `ideas/` folder.
- 2026-10-04 (backfilled) [DECISION] Friend persona: races a 1/10 touring car (Yokomo BD12), wants practice sessions to be worth it: say how the car feels, get setup recommendations, store the best setups with track conditions to retrieve them at championship races. Prefers his phone; also owns a consumer laptop that can run Gemma E2B/E4B.
- 2026-10-04 (backfilled) [DECISION] No fine-tuning of Gemma for this challenge. Why: ~10k words of facts teach style not reliable facts; tuned weights cannot cite or be corrected by editing a file; the design needs cited, reviewed advice; MLX has gemma4 model files but LoRA training on E4B and serving the adapter in Ollama were unverified; estimated 3-5 h with real failure risk. Revisit only if symptom-classification accuracy lands below ~85% (then prefer few-shot first).
- 2026-10-04 20:05Z (backfilled) [DECISION] Laptop-only for v1 after the phone spike failed; runtime = Ollama (Gemma 4 E4B QAT, E2B QAT as fallback for weaker machines). Evidence: `docs/PHONE-SPIKE.md`, commit c4bd117.
- 2026-10-04 20:30Z (backfilled) [DECISION] Knowledge: import the author's existing touring-car wiki (11 pages) as a frozen, credited snapshot in its own commit; NotebookLM extraction only as extras after the core loop works, stored in `kb/additions/`. Do not label the notebook "no pre-existing work": it is pre-window source material; the extraction/structuring done in the window is new. Evidence: `kb/PROVENANCE.md`, commit c0c2d08.
- 2026-10-04 20:30Z (backfilled) [DECISION] KB format: OKF markdown for source and additions; runtime chunks compiled by `npm run kb:build` (106 chunks from the snapshot); keyword search (BM25-style) for v1, no embeddings unless a ~20-question top-3 hit-rate check falls below ~85%. Mastra + one local SQLite (LibSQL) file proposed as orchestration and store; **not yet confirmed or built**.
- 2026-10-04 (backfilled) [DECISION] Partner scope: enter only categories the code really uses (Gemma via Ollama; Mastra if it runs the workflow; Entire if used). Skipped Tiger Data, MongoDB Atlas, Backboard, Sentry, ElevenLabs, Render, Temporal, TabPFN, Tinker, DigitalOcean, Arduino because they need cloud/Docker, break the offline story, or have no data/hardware here.

- 2026-10-04 21:15Z [DECISION] (PROPOSED by the planner subagent in `docs/IMPLEMENTATION-PLAN.md`; the author has not approved it yet) Architecture: local Node (Hono) server + Preact UI on localhost; Mastra 1.74 runs only the coach workflow (two suspend points, LibSQL snapshots) with a 45-minute timebox and a plain-TypeScript fallback behind the same `CoachEngine` interface; LLM calls go to Ollama's native `/api/chat` (`format`, `num_ctx` 4096) and skip Mastra's model layer and Agent/Memory; vault in `var/pit.db` via `@libsql/client`; MiniSearch for retrieval; three.js explainers with an SVG fallback. Rejected by the planner: Mastra model router / OpenAI-compatible endpoint (cannot set `num_ctx`), Preact 11 (released 2026-09-30, too new), a PWA service worker on localhost. This supersedes the earlier "static PWA" assumption. Evidence: `docs/IMPLEMENTATION-PLAN.md` sections 1-3.

- 2026-10-04 21:30Z [DECISION] Entire is dropped as a partner category (author: too much workload). The build session is shared through DevRelay's agent-session tool when writing the submission. Planned categories are now Gemma (via Ollama) and, only if the coach workflow really ships on it, Mastra. Evidence: `docs/IMPLEMENTATION-PLAN.md` section 1.
- 2026-10-04 21:30Z [DECISION] Droop: keep the generic droop gauge method (front 5.6 / rear 4.6, tagged "generic") instead of Yokomo's own upward-extension method for the BD12. Consequence to state honestly: droop values in the app are the generic gauge convention, not Yokomo's BD12 procedure. Evidence: plan Appendix A.5.
- 2026-10-04 21:30Z [DECISION] Rear diff oil / exit traction: the snapshot contradicts itself (see the FINDING of 21:15Z). The author is deciding which reading to use as a lever; no row exists until then.

### Findings

- 2026-10-04 (backfilled) [FINDING] The LiteRT-LM web package defaults to loading its WASM runtime from jsDelivr, which silently breaks any "works offline" claim. Fixed by self-hosting the files (`npm run setup:wasm`); verified no CDN request in the network log. Evidence: spike page, `scripts/copy-wasm.mjs`.
- 2026-10-04 (backfilled) [FINDING] Phone test needs HTTPS (WebGPU, microphone and service workers need a secure context): served from the laptop with a self-signed cert on the LAN. Plain `http://` to an HTTPS-only dev server looks exactly like "page not reachable".
- 2026-10-04 (backfilled) [FINDING] Most $100 partner categories are closed or hosted services (ElevenLabs, Backboard, SerpApi, MongoDB Atlas, Sentry); the openly licensed ones are Gemma (Apache-2.0), Mastra core (Apache-2.0), Entire CLI (MIT), Temporal server (MIT), Tiger Data's database extensions. The post should say where a closed partner was used as an add-on or not used at all.
- 2026-10-04 (backfilled) [FINDING] Mastra is a Node framework, so using it turns the product from a static PWA into Ollama + a local Node process + a browser UI on localhost. Mastra telemetry is on by default: set `MASTRA_TELEMETRY_DISABLED=1` for any offline/privacy claim.
- 2026-10-04 (backfilled) [FINDING] The knowledge base is tiny (11 pages, 106 chunks, ~7,500 words), so this is not a vector-database problem; retrieval by id from the lever table covers the common path.
- 2026-10-04 (backfilled) [FINDING] The knowledge notes record their own gap: tyre shore hardness and foam inserts appear nowhere in the 50-source notebook, so the coach must refuse that topic instead of guessing.

- 2026-10-04 20:50Z [FINDING] Friend's laptop: MacBook Pro 2019, 9th-gen Intel Core i7 (6-core, 2.6 GHz), 16 GB DDR4-2666. No Apple Silicon: per Ollama's macOS docs, Intel Macs run CPU-only and need macOS 14 (Sonoma) or newer. His macOS version and GPU are not yet known. Evidence: author message; https://docs.ollama.com/macos.
- 2026-10-04 20:50Z [DECISION] Design for a CPU-only laptop: Gemma 4 E2B QAT (4.3 GB) is the likely model for him (E4B QAT stays the dev default); set `num_ctx` to 4096; tiny, stable prompts; stream output; use the model only for speech-to-symptom and for phrasing, with everything else plain code. The final model choice must come from a measurement on his machine, not from this Mac.

- 2026-10-04 21:00Z [FINDING] Correction/addition from the author: the friend's MacBook Pro also has an AMD Radeon Pro 5300M (4 GB GDDR6) next to the Intel UHD Graphics 630. That points to the 16-inch 2019 model (my inference, not confirmed), which should be able to run macOS 14 or newer (also unconfirmed). Ollama's macOS docs only promise CPU inference on Intel Macs, so plan as CPU-only; any AMD GPU offload would be an unverified bonus, and 4 GB of VRAM could not hold E4B anyway. Evidence: author message; https://docs.ollama.com/macos.
- 2026-10-04 21:00Z [DECISION] Benchmarking on the friend's laptop (E2B vs E4B speed via `ollama run --verbose`) is deferred: he is unreachable right now. Until then, build to the CPU-only latency budget in the challenge `AGENTS.md`. Keep the TODO-REPORT measurement entries open.
- 2026-10-04 21:15Z [FINDING] Planner-reported, not independently verified: Ollama's gemma4 tags list text and image input only (no audio) for E2B/E4B, so speech-to-text cannot come from Gemma via Ollama (I did see "Text, Image input" on the tags page earlier). MDN compat data (per the planner) lists `SpeechRecognition.processLocally`, `available()` and `install()` as Chrome desktop 139+ only (no Safari, no Chrome Android); `phrases` biasing is Chrome 142+. Evidence: https://ollama.com/library/gemma4/tags; mdn/browser-compat-data `api/SpeechRecognition.json`.
- 2026-10-04 21:15Z [FINDING] The snapshot conflicts with itself on rear diff oil for exit traction (drivetrain page: thicker oil gives forward traction and exit stability; traction page: softer oil, down to ~3,000 cSt, for rear traction on low grip), so no lever row exists for it until the author decides. On a stock BD12 the "more rear toe-in" lever is already at the top of the snapshot's range (3.5 deg), which makes a good demo line: the app explains why it skipped the obvious change. Evidence: `docs/IMPLEMENTATION-PLAN.md` Appendix A.5.
- 2026-10-04 21:15Z [PROCESS] Draft lever table from the planner: 60 rows (51 numeric, 9 qualitative), 37 parameters, 14 pre-checks, 12 symptoms; every citation resolves against the 106 chunk ids (58 distinct chunks cited); all rows `status: draft` until the author reviews them. 5 rows rest on an inverse or an inference (flagged in `basis`). Planner run: ~22.5 min, ~282k tokens. Evidence: Appendix A.
- 2026-10-04 21:45Z [FINDING] Rear diff oil, three statements from the pre-window notes, not two: (1) snapshot drivetrain page: thinner oil frees the rear for turn-in and agility but "can go loose on low grip"; thicker locks the rear under power for forward traction and exit stability, with understeer risk if too stiff; (2) snapshot traction page (ToniSport "More Rear Traction" material): softer rear diff oil, down to ~3,000 cSt on low-grip asphalt, is a rear-traction lever; (3) the author's un-shipped raw notes from the BD-series/"Gear Diff Talk" material: thinner oil lets the wheels differentiate more freely (more mid-corner steering and side bite, prevents rear sliding on loose or dusty low-grip surfaces), thicker oil sends more torque straight to the wheels (stronger exit acceleration, calmer on high grip, no added lateral bite). The real clash is on low grip: (1) calls thinner risky, (2) and (3) recommend it. Not settled by the sources; the author is deciding, ideally after asking the notebook directly. Evidence: `kb/source/touring-car-drivetrain-tuning.md`, `kb/source/touring-car-traction-and-tire-management.md`; raw note not shipped.

### Failed / did not work

- 2026-10-04 20:05Z (backfilled) [FAILED] Gemma 4 E2B in the phone browser: the 2 GB model downloaded, but engine creation and prompts lagged too much to use. No numbers were captured, so none may be claimed. TODO: record phone model, OS and browser before stating them. Evidence: `docs/PHONE-SPIKE.md`.

### Measurements

- (SUPERSEDED in part by the 2026-10-04 20:39Z entries below, which cover the dev machine only; the friend's target laptop is still TODO) [TODO-REPORT] Baseline on the laptop: Gemma 4 E4B QAT via Ollama on the 10-utterance symptom set: JSON-valid %, correct %, time to first token, tokens/s, peak memory. Record machine, model tag, Ollama version, date.
- (none yet) [TODO-REPORT] Top-3 retrieval hit rate of keyword search on ~20 follow-up questions.
- (none yet) [TODO-REPORT] Offline run (Wi-Fi off) of the full loop on the target laptop, and the voice-input outcome on that laptop.

- 2026-10-04 20:39Z [MEASURE] Symptom classification baseline, `npm run eval:symptoms`: Gemma 4 E4B QAT (`gemma4:e4b-it-qat`, 6.1 GB on disk) via Ollama 0.35.1 on an Apple M4 Max, 64 GB, 100% GPU, temperature 0, Ollama JSON-schema output (`format`), model warmed up first. 10 utterances: 10/10 correct (100%), median time to first token 138 ms (load + prompt processing; first call 379 ms), median decode 85.8 tokens/s, 3.7 GB resident per `ollama ps` with a 131072-token context. Evidence: `data/eval/symptom-utterances.json`, `scripts/eval-symptoms.mjs`.
- 2026-10-04 20:39Z [HONEST] Limits of that baseline, state them with the number: only 10 cases, written by us in plain wording (not the friend's real phrasing); one MacBook-class high-end machine (M4 Max, 64 GB), far faster than a consumer laptop; the schema-enforced output means "valid JSON" is guaranteed by Ollama, not earned by the model. Do not present 100% as general accuracy. TODO: expand to ~20 cases with colloquial phrasing ("tail happy", "pushes", "loose") and 5+ out-of-scope, then rerun on the friend's laptop.

- 2026-10-04 20:48Z [MEASURE] CPU-only PROXY, not the friend's machine: Gemma 4 E4B QAT via Ollama 0.35.1 on an Apple M4 Max with the GPU disabled (`num_gpu 0`, 6 threads), temperature 0, default 131072 context: short prompt (16 tokens) prefill 169 tokens/s, decode 62.9 tokens/s; longer prompt (929 tokens) prefill 199 tokens/s, decode 57.1 tokens/s; 6.9 GB in memory (`ollama ps`, 100% CPU). Script: /tmp-style one-off (not in repo); reproduce with `CPU_ONLY=1 npm run eval:symptoms`.
- 2026-10-04 20:48Z [HONEST] That proxy flatters the friend's machine: an M4 Max CPU has far more memory bandwidth and faster cores than a 2019 i7-9750H-class chip with dual-channel DDR4-2666. My estimate (unmeasured, from hardware ratios) is several times slower: decode on the order of 5-15 tokens/s and prompt processing 20-50 tokens/s for E4B, better for E2B. Do not quote any speed for his laptop until measured on it.

- 2026-10-04 20:52Z [MEASURE] CPU-only PROXY (not the friend's machine): `CPU_ONLY=1 npm run eval:symptoms`, Gemma 4 E4B QAT, Ollama 0.35.1, Apple M4 Max with GPU disabled (6 threads), `num_ctx` 4096, temperature 0, schema-enforced JSON: 10/10 correct, median time to first token 642 ms, median decode 56.9 tokens/s. Same caveats as the other baseline (10 plain-wording cases; schema guarantees the JSON shape).

### Honest limits to state in the post

- 2026-10-04 (backfilled) [HONEST] Phone is not supported in v1; the phone spike failed.
- 2026-10-04 (backfilled) [HONEST] Touring-car knowledge comes from the author's pre-window notes (credited), itself distilled from third-party videos and manuals; the app's code, lever table, retrieval, workflow, voice, UI and vault are new in the window. The earlier 3D guide app, BD12 model and setup-sheet app are not reused.
- 2026-10-04 (backfilled) [HONEST] In the desktop baseline of the spike harness (embedded Chromium 152, Apple Silicon) on-device speech recognition reported "unavailable"; offline voice must be verified on the friend's laptop before it is claimed.

### Process

- 2026-10-04 (backfilled) [PROCESS] Work done with Claude Code: repo and knowledge-base setup, three Opus subagent research passes (partner triage ~6 min / ~113k tokens; two idea deep dives ~6.5 and ~9.7 min / ~120k and ~179k tokens), a phone spike, a frozen snapshot import. Agent session saved privately to DEV as session 504; make it public from DEV before embedding it.
- 2026-10-04 (backfilled) [PROCESS] Process lesson: a small-model summary of the challenge page listed a wrong featured category (Qualcomm); the launch post and the API agreed with each other. Verify summaries against the primary source before building on them.
- 2026-10-04 (backfilled) [PROCESS] DEV agent-session upload: the raw route stores a `.jsonl` via a presigned S3 URL, but the signed headers are not documented. It worked with `Content-Type: application/x-jsonlines` and `x-amz-acl: private` after a header sweep. The API then reported 0 parsed messages for the raw upload. Possible feedback for DevRelay.
- 2026-10-04 (backfilled) [PROCESS] Exporting a Claude Code session: the continuation file replays earlier history, so merging files duplicates turns; scrub paths, email, signed URLs and own scrubbing commands before upload.

- 2026-10-04 20:57Z [PROCESS] Implementation planning delegated to an Opus subagent (planner) that reads the memory, snapshot pages and code state and writes `docs/IMPLEMENTATION-PLAN.md` (stack, API contracts, domain data, UI, visual explainers, task cards with file ownership and recommended model per task, UTC timeline with MVP/cut lines, draft lever rows for the author's review). Execution then goes to subagents (Sonnet for well-specified plumbing/UI, Opus for the visual explainers, workflow/prompt design and integration). The planner was told not to open the author's earlier 3D guide or setup-sheet app (originality rule).

### Partners

- 2026-10-04 (backfilled) [PARTNER] (SUPERSEDED by 2026-10-04 21:30Z: Entire dropped) Gemma (via Ollama), Mastra and Entire are the only categories planned. Nothing is claimed until the code uses them. Update this section when each is actually integrated or dropped.

### Friend quotes

- 2026-10-04 20:50Z [QUOTE] Friend (a 1/10 touring-car racer, BD12 owner), relayed by the author: "this app will be very useful for practice days so I can quickly store my settings and get feedback from what works, what might have affected my run". TODO: confirm he agrees to be quoted in the public post (and whether to name him). Implication: the setup vault and "what affected my run" feedback are as central as the symptom coach; storing settings must be quick (voice or minimal taps).
- (SUPERSEDED in part by the 20:50Z quote above; permission to quote still TODO) [TODO-REPORT] Get the friend's own words (what he needs before a practice session, what he said after trying it) and permission to quote.

### Open questions

- Friend's macOS version and GPU (laptop is a 2019 MBP, i7, 16 GB)? Must be macOS 14+ for Ollama. Measure E2B vs E4B on it before choosing.
- Is the voice path acceptable on his laptop (Chrome on-device speech or a local Whisper)?
- Which promo codes, if any, are worth claiming (current plan: none).
