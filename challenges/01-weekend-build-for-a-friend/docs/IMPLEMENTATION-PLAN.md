# RC Pit Companion: implementation plan

**Written:** 2026-10-04 21:15Z by the planner subagent (read-only research; no code, installs or commits).
**Deadline:** 2026-10-05 06:59Z. **Time left when computed (`date -u` at 20:57Z): 10 h 02 min.**
**Budget:** about 5 h 10 min of build (22:05Z to 03:15Z), 30 min rehearsal, a protected 2 h 30 min writing block (03:45Z to 06:15Z), 45 min publish buffer.
**Project folder (`$P`):** `challenges/01-weekend-build-for-a-friend/`. All paths below are relative to `$P` unless they start with `/`.

Binding inputs, in priority order: `docs/CHALLENGE-MEMORY.md` (its "may claim / must NOT claim" table), `$P/AGENTS.md`, root `AGENTS.md`, then this plan. If this plan conflicts with the memory file, the memory file wins and the conflict gets logged.

## 0. Rules every task agent must follow

1. Read this whole section, your task card (section 7) and the contracts (section 2). Do not open the author's earlier OpenGrid project folder (outside this repo): its 3D guide, BD12 model and setup-sheet app must not be reused.
2. Never edit `kb/source/`. Run `npm run kb:verify` before you report done.
3. Touch only the files your card owns. If you need a change in a file you do not own, describe it in your report; do not make it.
4. Do not run `npm install` (T0 installs everything once). Do not commit (the orchestrator commits each task's paths after its acceptance checks pass). Do not publish, claim codes, or pull models.
5. Do not edit `docs/CHALLENGE-MEMORY.md` yourself (parallel edits collide). End your report with a block `MEMORY ENTRIES:` holding entries in the file's format (`- YYYY-MM-DD HH:MMZ [TAG] ... Evidence: ...`); the orchestrator appends them. Measurements need date, machine, model and method.
6. The model never produces numbers that reach the user. Values come from `data/levers.json` and `data/params.bd12.json`.
7. Mark anything you could not verify as unverified in your report.

## 1. Headline decisions

| Topic | Choice | Why | Time cost | Fallback (trigger) |
| --- | --- | --- | --- | --- |
| Shape | Local Node server (Hono) + Preact UI in Chrome on `localhost`; Ollama on the same laptop | One process owns Ollama, the vault file and `say`; browser never talks to Ollama, so no CORS or `OLLAMA_ORIGINS` setup | baseline | none needed |
| Orchestration | **Mastra workflow** `coach-turn` (`@mastra/core` 1.74.0) with two suspend points (await decision, await outcome), snapshots in a LibSQL file | The coach loop is a real multi-step, human-in-the-loop flow: suggest, go run laps, come back with better/same/worse. Mastra's suspend/resume with persisted snapshots is that exact shape; zod step schemas double as contracts | +45 min timebox inside T3 | Plain TypeScript engine behind the same `CoachEngine` interface (no start, suspend, resume, resume against `var/mastra.db` by T3 start + 45 min). Then drop the Mastra category and log it |
| Model calls | Our own `OllamaClient` on Ollama's native `/api/chat` with `format` (JSON schema), `options.num_ctx: 4096`, `temperature: 0`, `think: false`, `keep_alive: "30m"`, streaming | Ollama's OpenAI-compatible endpoint cannot set `num_ctx` (docs say to bake it into a Modelfile) and documents only JSON mode, so Mastra's model router / Agent would lose both the context cap and schema enforcement | none | n/a |
| Mastra Agent / Memory | **Not used** | The vault is the memory; Gemma tool calling is not needed; avoids AI SDK provider wiring | saves ~1 h | n/a |
| Model | `gemma4:e4b-it-qat` (6.1 GB) on the dev M4 Max; `gemma4:e2b-it-qat` (4.3 GB) default for the friend's Intel MacBook (CPU-only per Ollama docs) | E2B is the smaller QAT build; his speed is unmeasured | none | Text-only path with chips + keyword matcher if Ollama is missing or too slow |
| UI | Preact 10.29.8 + `@preact/signals` 2.11.3 + `@preact/preset-vite` 2.10.6, hand-written CSS, hash router | Agents write JSX fluently; 4 KB runtime; no router or CSS framework to learn. Preact 11.0.0 shipped 2026-09-30, too new to bet on | +10 min setup | Vanilla TS (if the preset fails with Vite 8: use Vite's `oxc.jsx` settings with `importSource: "preact"` instead, unverified) |
| Vault store | One SQLite file `var/pit.db` through `@libsql/client` 0.18.0 (prebuilt `@libsql/darwin-x64` exists) | Mastra needs LibSQL anyway; copy-on-write setup rows make diffs trivial; JSON export/import for backup and moving data to his laptop | 20 min | JSON files under `var/` if the native binary fails on his Mac |
| KB search | MiniSearch 7.2.0 over `data/generated/kb.json` (106 chunks), in the server | Pure JS, BM25-style ranking, no native code; the corpus is tiny | 20 min | Plain substring scoring |
| Speech in | Web Speech API in Chrome 139+ with `processLocally = true` after `SpeechRecognition.available()` / `install()`; `phrases` biasing on Chrome 142+ | Only path that can be on-device in a browser without new downloads we host; MDN compat: Chrome desktop 139+, not Safari | 60 min (T6) | Typing + symptom chips always work. Opt-in, clearly labelled "Chrome online recognition (audio goes to Google)", off by default. Whisper via transformers.js only post-deadline |
| Speech out | Browser `speechSynthesis` restricted to `localService` voices; fallback `POST /api/speak` running macOS `say` | Both are local and free; browser voice streams per sentence and needs no process handling | 30 min | Text only |
| Visuals | three.js 0.186.1, new procedural schematic car, 5 essential explainers; SVG for 2D geometry (roll centre, weight transfer) | Shows each change on the car; render-on-demand keeps an integrated GPU idle | 2 h timebox (T5) | SVG side/front/top diagrams with the same API (fewer than 2 three.js views working at T5 + 75 min) |
| Validation, tests | zod 4.6.5 (shared schemas), vitest 5.0.3 for engine and vault only | zod is already Mastra's peer; tests where bugs would cost demo time | in tasks | n/a |
| Runner | `tsx` 4.23.15 for the server, `concurrently` 10.0.5 for dev | Boring, works on Node 24 | 5 min | `node --watch` with type stripping |
| Partner categories | Gemma (via Ollama) yes; Mastra only if T3 ships it; **Entire dropped (author decision 2026-10-04: workload)** | Memory rule: no claim the code does not earn | none | Drop Mastra too if T3 falls back to plain TypeScript |

**Decisions the author had to make before T0 (all made 2026-10-04: architecture and Mastra timebox approved; 12 demo-path lever rows reviewed and approved; both A.5 questions resolved; Entire dropped; pending work committed):**
1. Approve the Mastra timebox and fallback.
2. Review the lever rows on the demo path in Appendix A (`exit-oversteer`, `entry-understeer`, `traction-roll`, `bumpy-track`) and flip their `status` to `"reviewed"`; the rest during wave 1. Resolve the two open data questions in A.5.
3. Accept that his laptop needs Node 22.13+ and Ollama (macOS 14+) installed; there is no installer in v1.
4. ~~Run `entire enable`~~ **DECIDED 2026-10-04: Entire is dropped.** The build session is shared through DevRelay's agent-session tool when writing the submission.
5. Commit the current working-tree changes (memory file, eval script, AGENTS edits) so task commits start clean.

## 2. Architecture and contracts

```
 Chrome (localhost:5173 in dev, localhost:8787 in prod)
 +-----------------------------------------------------------------------+
 | Preact UI: Coach | Setup | Session | Race day | Settings               |
 |  voice/  Web Speech in (processLocally)   speechSynthesis out (local)  |
 |  scene/  three.js explainers (render on demand), SVG 2D diagrams       |
 |  api/    typed fetch + SSE client                                      |
 +-------------------------------|---------------------------------------+
                                 | HTTP JSON + SSE  (/api/*)
 +-------------------------------v---------------------------------------+
 | Node 24 server (Hono on @hono/node-server, port 8787)                  |
 |  routes/coach  -> CoachEngine: Mastra workflow "coach-turn"            |
 |                   classify -> precheck -> pickLever -> explain         |
 |                   -> [suspend: decision] -> apply                      |
 |                   -> [suspend: outcome] -> logOutcome/next             |
 |  routes/vault  -> vault repo (@libsql/client, var/pit.db)              |
 |  routes/analysis -> similar setups, run comparison (pure functions)    |
 |  routes/kb     -> MiniSearch over data/generated/kb.json               |
 |  routes/meta   -> params, symptoms, levers, prechecks (data/*.json)    |
 |  routes/llm    -> status, pull (SSE), warmup                           |
 |  routes/speak  -> macOS `say` (fallback TTS)                           |
 |  static        -> dist/ (prod)                                         |
 +-------------------------------|---------------------------------------+
                                 | native /api/chat, /api/tags, /api/ps, /api/pull
 +-------------------------------v---------------------------------------+
 | Ollama localhost:11434   gemma4:e2b-it-qat | gemma4:e4b-it-qat         |
 +-----------------------------------------------------------------------+
 Files: var/pit.db (vault), var/mastra.db (workflow snapshots), var/backups/
```

The model is called only twice per coach turn: classify (skipped when the driver taps a chip) and explain (skippable in Settings). Everything else is plain code.

### 2.1 Folder layout after T0

```
server/index.ts            boot, config, static, mount routes        (T1)
server/config.ts           env + settings defaults                    (T0, frozen)
server/db.ts               libsql client + migrations                 (T1)
server/routes/index.ts     mounts every route module                  (T0, frozen)
server/routes/{vault,meta,settings}.ts                                (T1)
server/routes/{kb}.ts      server/kb/search.ts                        (T2)
server/engine/{levers,keyword,data}.ts                                (T2)
server/llm/ollama.ts                                                  (T3)
server/coach/{prompts,steps,workflow.mastra,workflow.plain,engine}.ts (T3)
server/routes/{coach,llm}.ts                                          (T3)
server/analysis/{similar,compare,history}.ts  server/routes/analysis.ts (T8)
server/routes/speak.ts                                                (T6)
src/shared/{schemas,types,api,events}.ts   contracts                  (T0, frozen)
src/api/client.ts                                                     (T4a)
src/main.tsx  src/ui/app/**  src/ui/coach/**  src/ui/store.ts  src/style.css  index.html (T4a; store.ts created by T0)
src/ui/setup/**  src/ui/session/**                                    (T4b)
src/ui/race/**  src/ui/settings/**                                    (T4c)
src/scene/**                                                          (T5)
src/voice/**                                                          (T6)
data/params.bd12.json data/symptoms.json data/levers.json data/prechecks.json (T2)
data/eval/**  scripts/eval-*.ts  scripts/eval-retrieval.ts             (T9)
scripts/seed-demo.ts                                                  (T10)
tests/engine.test.ts (T2)  tests/vault.test.ts (T1)  tests/analysis.test.ts (T8)
```

"Frozen" means only T0 and the integration tasks (T7, T10) edit it. A task that needs a new contract field writes the request into its report; T7 applies it.

### 2.2 Shared types (`src/shared/schemas.ts`, zod as the single source; `types.ts` re-exports `z.infer` types)

```ts
type Grip = "low" | "medium" | "high";
type Phase = "entry" | "mid" | "exit" | "none";
type Outcome = "better" | "same" | "worse";
type ParamValue = number | string | null;
type SetupValues = Record<string, ParamValue>;          // keys = ParamDef.id

interface ParamDef { id: string; label: string; group: "alignment"|"chassis"|"steering"|"damping"|"drivetrain"|"aero"|"tyres";
  unit: string; kind: "number"|"enum"|"text"|"computed"; min?: number; max?: number; step?: number;
  options?: number[]; formula?: string; bd12: ParamValue; generic: ParamValue; src: string[]; range: string; explainer?: ExplainerId }
interface SymptomDef { id: string; label: string; phase: Phase; precheckOnly?: boolean; prechecks: string[]; synonyms: string[] }
interface PrecheckDef { id: string; label: string; detail: string; citations: string[] }
interface LeverRow { id: string; symptomId: string; phases: Phase[]; grip?: Grip[]; kind: "numeric"|"qualitative";
  param?: string; direction?: "increase"|"decrease"; step?: number; min?: number; max?: number; unit?: string;
  action: string; effect: string; tradeOff: string; verify: string; followUp?: string; citations: string[];
  priority: number; basis: "stated"|"inverse"|"inferred"; notes?: string; status: "draft"|"reviewed" }

interface TrackConditions { trackName: string; surface: "asphalt"|"carpet"|"concrete"|"other"; grip: Grip; bumpy: boolean;
  layout?: "tight"|"medium"|"fast"; airTempC?: number; trackTempC?: number; timeOfDay?: "morning"|"midday"|"evening"; dusty?: boolean; notes?: string }

interface Setup { id: string; values: SetupValues; parentId?: string; createdAt: number }
interface Session { id: string; date: string; car: "yokomo-bd12"|"generic"; conditions: TrackConditions; currentSetupId: string; notes?: string; createdAt: number }
interface Run { id: string; sessionId: string; seq: number; setupId: string; conditions?: Partial<TrackConditions>;
  lapTimesMs?: number[]; bestLapMs?: number; rating?: 1|2|3|4|5; feel: string[]; /* symptom ids */ notes?: string; createdAt: number }
interface Change { id: string; sessionId: string; beforeSetupId: string; afterSetupId: string; param: string; from: ParamValue; to: ParamValue;
  leverId?: string; symptomId?: string; source: "coach"|"manual"|"revert"; coachRunId?: string; outcome?: Outcome; outcomeRunId?: string; createdAt: number }
interface SavedSetup { id: string; label: string; setupId: string; conditions: TrackConditions; sessionId?: string; runId?: string;
  eventName?: string; verdict?: string; createdAt: number }

interface Classification { symptomId: string; altId: string | "none"; phase: Phase; confidence: number; source: "llm"|"chip"|"keyword"; ms?: number }
type ExplainerId = "camber"|"toe"|"caster"|"rideHeight"|"droop"|"shockAngle"|"arb"|"ackermann"|"bumpSteer"|"rollCentre"|"weight"|"body";
interface SceneBinding { explainer: ExplainerId; param: string; from: number; to: number }
interface LeverSuggestion { lever: LeverRow; from: ParamValue; to: ParamValue; atLimit: boolean; needsCurrentValue: boolean; scene?: SceneBinding }
interface Suggestion { primary: LeverSuggestion | null; alternatives: LeverSuggestion[]; skipped: { leverId: string; reason: "at-limit"|"tried-worse"|"tried-same"|"grip-mismatch"|"draft-hidden" }[]; noLeverReason?: string }
interface Refusal { reason: "out-of-scope"|"tyre-compound-gap"|"electronics"|"other-car-type"; message: string; citations: string[] }
interface CoachTurnInput { sessionId: string; utterance?: string; symptomId?: string; phase?: Phase }   // one of utterance | symptomId
interface TurnState { runId: string; input: CoachTurnInput; classification?: Classification; refusal?: Refusal;
  prechecks: PrecheckDef[]; suggestion?: Suggestion; explanation?: { text: string; source: "llm"|"template"; ms?: number };
  decision?: "apply"|"skip"|"alternative"; appliedChangeId?: string; outcome?: Outcome; status: "awaiting-decision"|"awaiting-outcome"|"done" }
interface OutcomeResult { change: Change; prompt: "save-setup"|"next-lever"|"offer-revert"; revert?: { param: string; to: ParamValue }; next?: Suggestion }
```

### 2.3 Engine interfaces (TypeScript, in `src/shared/api.ts` or server-only as noted)

```ts
// server/coach/engine.ts (T0 stub; T3 implements twice: Mastra and plain)
interface CoachEngine {
  start(input: CoachTurnInput, emit: (e: CoachEvent) => Promise<void>): Promise<TurnState>;          // runs until the first suspend
  decide(runId: string, d: { decision: "apply"|"skip"|"alternative"; alternativeIndex?: number }): Promise<TurnState>;
  outcome(runId: string, o: { outcome: Outcome; runRef?: string }): Promise<OutcomeResult>;
}
// server/engine/levers.ts (T2)
selectLevers(args: { symptomId: string; phase: Phase; grip: Grip; setup: SetupValues; params: ParamDef[]; levers: LeverRow[];
  history: Change[]; reviewedOnly: boolean }): Suggestion
keywordClassify(utterance: string, symptoms: SymptomDef[]): Classification | null
refusalFor(utterance: string): Refusal | null           // keyword refusals (tyre compound gap, ESC/motor, nitro, LiPo, off-road)
// server/kb/search.ts (T2)
search(q: string, limit?: number): KbChunk[];  getChunk(id: string): KbChunk | undefined
// server/analysis (T8)
similarSetups(today: TrackConditions, saved: SavedSetup[], current: SetupValues, setups: Map<string, Setup>): SimilarHit[]
compareRuns(a: RunBundle, b: RunBundle, ctx: { params: ParamDef[]; levers: LeverRow[] }): RunComparison
paramHistory(changes: Change[]): { param: string; direction: string; tries: number; better: number; same: number; worse: number }[]
```

### 2.4 HTTP API (all JSON unless marked SSE; errors are `{ error: string, stage?: string }` with 4xx/5xx)

| Method, path | Body / query | Returns | Owner |
| --- | --- | --- | --- |
| GET `/api/health` | | `{ ok, version }` | T0 |
| GET `/api/meta` | | `{ params, symptoms, levers, prechecks, kbStats }` | T1 (reads T2's data via `server/engine/data.ts`) |
| GET/PUT `/api/settings` | `Settings` | `Settings` | T1 |
| POST `/api/sessions` | `{ date, car, conditions }` | `Session` (creates the baseline setup row) | T1 |
| GET `/api/sessions`, `/api/sessions/:id` | | `Session[]`, `{ session, runs, changes, setups }` | T1 |
| PATCH `/api/sessions/:id` | `{ conditions?, notes? }` | `Session` | T1 |
| POST `/api/sessions/:id/setup` | `{ values: Partial<SetupValues>, source: "manual"|"coach"|"revert", leverId?, symptomId?, coachRunId? }` | `{ setup, changes: Change[] }` (copy-on-write; one Change per changed param) | T1 |
| POST `/api/sessions/:id/runs` | `Omit<Run,"id"|"seq"|"createdAt"|"setupId">` | `Run` (setupId = session.currentSetupId) | T1 |
| PATCH `/api/changes/:id` | `{ outcome, outcomeRunId? }` | `Change` | T1 |
| GET/POST `/api/saved` , DELETE `/api/saved/:id` | `SavedSetup` minus id | `SavedSetup[]` / `SavedSetup` | T1 |
| GET `/api/export` ; POST `/api/import` | ; `{ schemaVersion, tables }` | full dump ; `{ ok, counts }` (writes `var/backups/<ts>.json` first) | T1 |
| POST `/api/reset` | `{ confirm: "RESET" }` | `{ ok }` | T1 |
| GET `/api/kb/search?q=&limit=3` ; GET `/api/kb/chunk/:id` | | `KbChunk[]` ; `KbChunk` | T2 |
| POST `/api/coach/turn` **SSE** | `CoachTurnInput` | events below; ends after `suspended` or `refusal` | T3 |
| POST `/api/coach/:runId/decide` | `{ decision, alternativeIndex? }` | `TurnState` | T3 |
| POST `/api/coach/:runId/outcome` | `{ outcome, runRef? }` | `OutcomeResult` | T3 |
| GET `/api/llm/status` | | `{ reachable, url, model, present, loaded, numCtx, lastLatencyMs? }` | T3 |
| POST `/api/llm/pull` **SSE** | `{ model }` | `{ status, completed?, total? }` frames from Ollama `/api/pull` | T3 |
| POST `/api/llm/warmup` | | `{ ms }` | T3 |
| GET `/api/analysis/similar?sessionId=` | | `SimilarHit[]` | T8 |
| GET `/api/analysis/compare?runA=&runB=` | | `RunComparison` | T8 |
| GET `/api/analysis/history` | | `paramHistory` rows | T8 |
| POST `/api/speak` | `{ text, voice? }` | `{ ok }` (spawns `say`, kills any previous) | T6 |

**SSE event names (`src/shared/events.ts`):** `classified` (Classification), `refusal` (Refusal), `precheck` (PrecheckDef[]), `suggestion` (Suggestion), `token` ({ text }), `explained` ({ text, source, ms }), `suspended` ({ runId, status }), `error` ({ message, stage }). Order is fixed: classified, then refusal (and stop) or precheck, suggestion, token*, explained, suspended. The UI renders the suggestion card as soon as `suggestion` arrives; tokens only fill the "coach says" line.

**Settings shape:** `{ ollamaUrl, model, numCtx: 4096, llmPhrasing: boolean, reviewedOnly: boolean, voiceIn: "local"|"cloud-optin"|"off", voiceOut: "browser"|"say"|"off", voiceName?, tempUnit: "C"|"F", car: "yokomo-bd12"|"generic" }`, stored in a `settings` table.

### 2.5 Mastra workflow design (T3)

- One state schema `TurnState` for every step's input and output, so `.then()` chaining never fights schema merging. Steps no-op when `refusal` is set. No `.branch()` needed.
- Steps: `classify` (chip passthrough, else keyword refusal check, else LLM; emits `classified`), `precheck`, `pickLever` (calls `selectLevers`; emits `suggestion`), `explain` (LLM stream through `writer.write({ type: "token", ... })`, number guard, template fallback; emits `explained`), `awaitDecision` (`suspend()`; `resumeSchema { decision, alternativeIndex? }`), `apply` (vault write through the same repo functions T1 exposes), `awaitOutcome` (`suspend()`; `resumeSchema { outcome, runRef? }`), `logOutcome` (PATCH change; compute `OutcomeResult`).
- Storage: `new LibSQLStore({ id: "mastra-storage", url: "file:./var/mastra.db" })`. Resume after a server restart with `workflow.createRun({ runId })` then `resume({ step, resumeData })`.
- Set `MASTRA_TELEMETRY_DISABLED=1` in `server/config.ts` before importing Mastra; do not add `@mastra/observability` or the `mastra` CLI. Verify no outbound traffic in the airplane-mode run (T10).
- If forwarding `writer` events through `run.stream()` costs more than 20 min, stop streaming tokens: `explain` returns the full text in state, and the route emits one `explained` event. The card still appears first, so the UX cost is small.
- Plain fallback `workflow.plain.ts`: same steps as functions, `TurnState` persisted as JSON in a `coach_runs` table in `var/pit.db`.

## 3. Stack (versions checked with `npm view` on 2026-10-04 ~21:00Z)

| Package | Version | Role | Note |
| --- | --- | --- | --- |
| `@mastra/core` | 1.74.0 | workflow engine | peer `zod ^3.25 || ^4`; Node >= 22.13; bundles AI SDK provider specs v5-v7 (unused here) |
| `@mastra/libsql` | 1.25.0 | workflow snapshot storage | peer `@mastra/core >=1.68` |
| `@libsql/client` | 0.18.0 | vault DB | native `libsql` 0.5.29 has a `darwin-x64` build |
| `hono` / `@hono/node-server` | 4.13.13 / 2.1.3 | HTTP + SSE (`hono/streaming` `streamSSE`) | Mastra already depends on hono ^4.13 |
| `zod` | 4.6.5 | schemas | |
| `minisearch` | 7.2.0 | KB search | |
| `preact` | 10.29.8 (pin, not 11.0.0) | UI | |
| `@preact/signals` | 2.11.3 | state | peer `preact >=10.25` |
| `@preact/preset-vite` (dev) | 2.10.6 | JSX + HMR | peer allows Vite 8; pulls `@babel/core` |
| `three` / `@types/three` | 0.186.1 / 0.186.0 | explainers | |
| `tsx` | 4.23.15 | server runtime (dependency, used by `npm start`) | |
| `concurrently` (dev) | 10.0.5 | `npm run dev` | |
| `vitest` (dev) | 5.0.3 | tests | peer Vite 6-8 |
| existing | `typescript` 7.0.2, `vite` 8.3.2, `@types/node` 26 | | TS 7 is the native compiler; T0 must confirm `jsxImportSource` works |
| not added | `ai`, `ollama-ai-provider-v2` 4.0.1, `@mastra/memory`, `mastra` CLI, `better-sqlite3`, `ollama` npm | | fetch is enough for Ollama |
| stretch only | `@huggingface/transformers` 4.3.0 | Whisper fallback | post-deadline |

Local tooling seen on the dev Mac: Node v24.13.0, npm 11.6.2, Ollama 0.35.1 with `gemma4:e4b-it-qat` pulled, `/usr/bin/say` present, `entire` not installed.

T0 also: removes `VitePWA` from `vite.config.ts` and `registerSW` from the entry (a service worker on a localhost app adds stale-cache bugs and no value; packages stay installed so `spike.html` still builds), adds a Vite proxy `/api -> http://localhost:8787`, adds `var/` to `.gitignore`, renames env keys to `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX`, `PORT`, `MASTRA_TELEMETRY_DISABLED=1` in `.env.example` (server falls back to the old `VITE_*` names), and adds scripts:

```
"dev": "concurrently -k -n server,ui \"tsx watch server/index.ts\" \"vite\"",
"start": "vite build && tsx server/index.ts",
"test": "vitest run --passWithNoTests", "typecheck": "tsc --noEmit",
"eval:symptoms": "tsx scripts/eval-symptoms.ts", "eval:retrieval": "tsx scripts/eval-retrieval.ts",
"seed:demo": "tsx scripts/seed-demo.ts"
```

`tsconfig.json`: add `"jsx": "react-jsx", "jsxImportSource": "preact"`, include `server`, `scripts`, `tests`. Server loads `.env` with `process.loadEnvFile()` when the file exists.

## 4. Domain data design

### 4.1 Setup parameters

37 parameters in 7 groups (full JSON in Appendix A.1). Baseline rule, from `yokomo-bd12#factory-baseline-alignment`: use the BD12 factory value where Yokomo gives one, else the generic (Xray-derived) value, shown with a "generic" tag. BD12 factory values in the snapshot: front camber 1.5 deg negative, rear camber 2.5 deg negative, rear toe-in 3.5 deg, front toe-out 1.0 deg, ride height 5.0 mm, droop set as 1.5-2.0 mm upward extension at 5.0 mm ride height, 90T spur, 4-hole pistons, 5 front shock positions.

Sign conventions shown next to each field (and used by the explainers): camber stored as degrees negative; front toe is toe-out (front toe-in is never used); rear toe is toe-in; droop is the gauge reading where a **lower number means more droop**; shock position index 1 = most laid down.

Honest gaps the editor must show (a small "range: unsourced" hint): no BD12 values for caster, droop gauge, ARB, springs, oil, diff, Ackermann, bump steer; most step sizes and outer bounds; the rear shock position count.

### 4.2 Symptoms

12 ids (Appendix A.2): `entry-understeer`, `mid-understeer`, `exit-understeer`, `entry-oversteer`, `exit-oversteer`, `traction-roll`, `bumpy-track`, `nervous-twitchy`, `low-grip`, `fade-late-run`, `left-right-difference` (pre-check only: it never suggests a setup change, it walks the tweak, weight and steering checks), and `out-of-scope`. The first seven keep the ids already used by `data/eval/symptom-utterances.json`. Each has driver synonyms used by the keyword matcher (fallback and eval baseline) and as chip tooltips.

### 4.3 Lever engine (T2)

`selectLevers` in order:
1. Rows where `symptomId` matches and `phases` includes the phase (or `none`), and `grip` is absent or includes today's grip. If `reviewedOnly`, drop `draft` rows (recorded in `skipped`).
2. For numeric rows: `current = setup[param]`. If null: `needsCurrentValue = true`, `to = null` (card says "one step <direction>; enter your current value in Setup for the exact number"). Else `to = clamp(current +/- step, max(row.min, param.min), min(row.max, param.max))`; enum params move to the next option. If `to === current`: `atLimit`, skip with reason `at-limit`.
3. Skip levers whose `(param, direction)` was applied in this session with outcome `worse` or `same` in the last 3 changes.
4. Sort by `priority`; primary = first, alternatives = next two. Attach `scene` when the param has an explainer and both values are numbers.
5. No row left: `noLeverReason` ("Every option in my notes for this is at its limit or already tried. Re-check the basics, or log what you changed by hand.").

Worked example on a stock BD12, exit-oversteer: `xo-rear-toe-in-more` is skipped as at-limit (3.5 deg is already the top of the snapshot range); `xo-rear-shocks-up` needs a current value; once entered, it becomes the primary. This is a good demo line: the app explains why it did not pick the obvious change.

**Number guard (T3):** collect every number in the LLM explanation; each must appear in the card (`from`, `to`, the action text, effect, verify). Otherwise discard the LLM text and use the template `"{action}: {from} to {to} {unit}. {effect} Trade-off: {tradeOff} Check: {verify}"`.

**Refusals:** classifier `out-of-scope`, or keyword hits before the LLM: tyre compound / shore / insert / foam gives the gap message citing `touring-car-traction-and-tire-management#a-real-gap-not-an-extraction-failure`; ESC / timing / boost / motor; nitro / engine / glow; LiPo / charge; buggy / off-road / crawler / drift. Messages are canned strings in `server/engine/keyword.ts`.

### 4.4 Pre-check gate

14 checks (Appendix A.3), drawn from the re-check cadence and the five common setup errors. Each symptom lists up to four. The UI shows them as big toggles above the card: "OK" or "Found a problem". A problem ends the turn with "Fix that first, then run again" and a session note. The gate never blocks: "Already checked" skips it.

### 4.5 Vault

Tables in `var/pit.db`: `settings(key, value)`, `setups(id, values, parent_id, created_at)`, `sessions`, `runs`, `changes`, `saved_setups`, `coach_runs` (plain fallback only). JSON columns for `values`, `conditions`, `lap_times_ms`, `feel`. Setups are copy-on-write: every change creates a new row, so a run points at the exact setup it used and any two runs diff by comparing two rows.

Quick entry (his words: "quickly store my settings"):
- **Start session:** track name (autocomplete from past sessions), surface, grip, bumpy, layout, track temp; all chips except name and temperature. One screen, about 5 taps.
- **Log run:** rating 1-5 (big buttons), feel chips (symptoms), optional best lap, optional pasted lap times (any whitespace/comma-separated seconds), tyre runs counter auto-incremented, note. The setup is implicit: the session's current setup.
- **Change a setting:** stepper buttons in the Setup screen; each tap stages a change; "Commit changes" writes one setup row and one Change per param (source `manual`).
- **Save setup:** from Session or Setup: label + conditions copied from the session + optional verdict.

### 4.6 Race-day finder: similar conditions

```
similarity(today, saved) = sum(w_i * s_i) / sum(w_i)  over fields present in both
  trackName   w=3    s = 1 if same (case-insensitive) else 0
  surface     w=3    s = 1 if same else 0          (mismatch also sets surfaceMismatch=true and groups the hit under "other surface")
  grip        w=2    s = 1 - |ord(a)-ord(b)| / 2   (low=0, medium=1, high=2)
  bumpy       w=1.5  s = 1 if same else 0
  trackTempC  w=1.5  s = max(0, 1 - |a-b| / 15)
  layout      w=1    s = 1 - |ord(a)-ord(b)| / 2
  timeOfDay   w=0.5  s = 1 if same else 0.5
  airTempC    w=0.5  s = max(0, 1 - |a-b| / 15)
  recency     w=0.5  s = max(0, 1 - ageDays / 365)
```

Weights are a judgement call (unsourced), stated as such in the UI tooltip. Each hit returns `score` (0-100), `reasons` ("same track", "track 4 C warmer", "grip one step lower"), and `diffVsCurrent` (params that differ from today's setup, with direction). Surface separation is grounded in the snapshot's note that BD12 driver sheets split by surface (`yokomo-bd12#real-driver-setup-sheets-exist-for-this-exact-ch`). The card has "Load this setup", which stages the diff in the Setup screen (one commit = changes with source `manual`).

### 4.7 "What might have affected my run"

`compareRuns(A, B)` (default: the selected run versus the previous run in the same session; the user can pick any run or a saved setup):
1. **Setup differences:** every param that differs, with direction and, when a lever row exists for that `(param, direction)`, its `effect` and citations ("rear bar 1.2 to 1.1: notes say more on-power rear traction").
2. **Condition differences:** track temperature change of 5 C or more; grip or surface change; time of day; a later run in the same session (grip usually climbs through the day: `vehicle-dynamics-fundamentals#track-grip-changes-across-a-race-day`); tyre runs on the set up by 3 or more (worn tyres lower ride height and add droop: `touring-car-traction-and-tire-management#tyre-diameter-is-a-geometry-input-not-just-a-wea`).
3. **Lap times, honest statistics** (only when both runs have 3 or more lap times): means, pooled SD `sigma`, `n = min(nA, nB)`, noise floor `delta = 2.8 * sigma * sqrt(2 / n)` from `minimum-detectable-lap-time-difference#definition`. If `|meanB - meanA| < delta`: "No clear difference: the gap is smaller than the noise floor (about delta s)". Otherwise: "Run B was X s faster, above the noise floor, but laps within a run are not independent, so treat it as a hint" (`...#laps-within-a-single-run-are`). Never "caused", never a winner when the interval spans zero (`...#any-setup-comparison-tool-should-report-an`).
4. **Confounding flag:** if more than one setup param changed, or conditions changed too: "N things changed at once; the notes recommend one change at a time, back to back" (`...#a-paired-back-to-back-testing-design-same`).
5. **What has worked (history):** for each `(param, direction)` across all sessions: tries and better/same/worse counts from the driver's own outcome taps, labelled "your feel, not lap-time proof".

The text is built from templates. An LLM summary of these facts is a stretch item and must pass the number guard.

## 5. UI plan

Target: a laptop on a pit table, 1280x800 or larger (works down to 1024 wide). Dark, high-contrast theme: background `#0b0f14`, panels `#151c24`, text `#f2f5f8`, accent `#7fb2ff`, warn `#ffbf3c`, ok `#4fd18b`, danger `#ff6b6b`. Base font 18 px, numbers in `font-variant-numeric: tabular-nums`. Every button at least 48 px tall with 12 px gaps; primary actions 64 px. No hover-only controls. Keyboard: Space = push-to-talk while held (when focus is not in an input), Enter submits text. Mobile is out of scope.

### 5.1 Main layout and Coach screen

```
+------------------------------------------------------------------------------------------+
| RC PIT COMPANION   Session: Club track | asphalt | medium grip | 24 C    [Gemma E2B: ready] [offline] |
+---------+--------------------------------------------------------------------------------+
| COACH   |  [  HOLD TO TALK (Space)  ]   [ type how the car feels ...................  ] [Go] |
| SETUP   |  Quick: [Push in] [Push mid] [Push on power] [Loose in] [Loose on power]          |
| SESSION |         [Traction roll] [Bumpy] [Twitchy] [No grip] [Fades late] [Left vs right]  |
| RACE DAY|-----------------------------------------------------------------------------------|
| SETTINGS|  Heard: "the rear lets go when I squeeze the trigger"                               |
|         |  -> Loose on power (exit oversteer)  conf 0.86   [Not it? Push on power | other]   |
|         |  First check:  [OK] Belts quiet   [OK] Tyres glued   [ ? ] Cross-tweak  [Checked] |
|         |  +-------------------------------------------+  +------------------------------+ |
|         |  | TRY ONE CHANGE                             |  |  3D: rear shock angle        | |
|         |  | Stand the rear shocks up one position      |  |  ghost = now, solid = after  | |
|         |  |   2  ->  3                                 |  |  [Front] [Side] [Top] [Iso]  | |
|         |  | More corner-exit rear traction.            |  |  angle exaggerated x2        | |
|         |  | Trade-off: less progressive.               |  +------------------------------+ |
|         |  | Check: 3-5 laps, judge power-on exits.     |                                   |
|         |  | Notes: [suspension: shock angle] [traction: rear grip]                       |
|         |  | Not picked: rear toe-in is already 3.5, the top of the range in my notes.    |
|         |  | [ APPLY ]   [ ANOTHER OPTION ]   [ SKIP ]          draft row (not reviewed)  |
|         |  +-------------------------------------------+                                   |
|         |  Coach: "Move the rear shocks one hole more upright..."   (streams; spoken)      |
|         |  After your run:   [ BETTER ]   [ SAME ]   [ WORSE ]                              |
|         |  Ask the notes: [ why does droop matter? ......... ] -> 3 cited chunks            |
+---------+-----------------------------------------------------------------------------------+
```

States: idle (chips visible, last turn summary); listening (button pulses, interim transcript); thinking (step list with live timers: "Understanding... 4.2 s", then "Picking a change" instant, then "Phrasing" with streaming text; a Cancel button aborts the fetch); refusal (grey card with the reason and, for tyre compounds, the gap citation); no lever (explains why and links to Setup); model unavailable (banner: "Coach phrasing is off: Ollama not reachable. Chips and typed keywords still work." with a Settings link). Citation chips open a side drawer with the chunk text, page title and "from the author's pre-window notes" label.

### 5.2 Setup editor

```
+--------------------------------------------------------------------------------------+
| SETUP  (BD12)        [Show: all | changed only]     Staged: 2 changes [Commit] [Undo] |
+--------------------------------------------------------------------------------------+
| ALIGNMENT                       baseline        current                    |
|  Front camber (deg neg)          1.5            [ - ]  1.5  [ + ]                     |
|  Rear toe-in (deg)               3.5            [ - ]  3.0  [ + ]   -0.5  (changed)   |
|  Caster (deg)                    4  generic     [ - ]  4    [ + ]                     |
| CHASSIS                                                                               |
|  Droop front (gauge; lower = more)  5.6 generic [ - ]  5.4  [ + ]   -0.2 (more droop) |
| DAMPING ...   DRIVETRAIN: Spur 90  Pinion [ 48 ]  FDR 3.56 (computed)                  |
|  [ ? ] per row opens: description, sign convention, range source, explainer view      |
+--------------------------------------------------------------------------------------+
| [ Save as setup... ]   [ Compare with a saved setup v ]                               |
+--------------------------------------------------------------------------------------+
```

Diff highlighting: changed rows get an accent left border and a signed delta badge; staged-but-uncommitted values are amber. Out-of-range input is allowed but flagged ("outside the range in my notes"). Clicking a row with an explainer opens it in a right-side panel.

### 5.3 Session (practice log) and run comparison

```
+--------------------------------------------------------------------------------+
| SESSION  Club track, 2026-10-04   [Edit conditions]   [ + LOG RUN ]  [ New session ] |
| Run 3  rating 4  best 14.82  feel: loose on power   setup: rear bar 1.1 (changed) |
| Run 2  rating 3  best 14.95  feel: loose on power                                 |
| Run 1  rating 3  best 15.01  feel: -                                              |
| Changes: 19:40 rear bar 1.2 -> 1.1 (coach)  outcome: better                       |
| [ What affected run 3? ]                                                          |
+--------------------------------------------------------------------------------+
| WHAT AFFECTED RUN 3 vs RUN 2                                                    |
| Setup: rear anti-roll bar 1.2 -> 1.1  (notes: more on-power rear traction) [cite]|
| Conditions: track 3 C warmer; one run later in the session (grip usually rises)  |
| Lap times: 0.11 s faster on average; noise floor ~0.19 s -> no clear difference  |
|  [ ? how is this computed ]   One change at a time keeps this readable.          |
+--------------------------------------------------------------------------------+
```

### 5.4 Race day

Top: "Today's conditions" chips (prefilled from the open session). Below: ranked saved setups (score bar, reasons as chips, "N params differ from now", [Load], [Compare]); a second group "Other surface". Right column: "What has worked for you" history table. Empty state: "No saved setups yet. Save one from a practice session that went well."

### 5.5 Settings

| Section | Controls |
| --- | --- |
| Model | Ollama URL (default `http://localhost:11434`); model dropdown from `/api/tags` plus free text; status line (reachable / model present / loaded, from `/api/ps`); [Pull model] with a progress bar (SSE); [Warm up]; last latency; "Coach phrasing (LLM explanations)" on/off; num_ctx shown read-only (4096) under "Advanced" |
| Advice | "Use reviewed lever rows only" toggle; count of reviewed vs draft rows |
| Voice | Input: Chrome on-device / Chrome online (opt-in, labelled "audio goes to Google") / off, with the live `available()` result and [Install speech pack]; Output: browser local voice (dropdown of `localService` voices) / macOS `say` / off; [Test] buttons |
| Car and units | Car profile BD12 / generic; temperature C/F |
| Data | [Export JSON] (download), [Import JSON] (shows counts, writes a backup first), [Reset] (type RESET) |
| About | Provenance summary with a link to `kb/PROVENANCE.md`, version, an offline checklist (Ollama model present, speech pack installed, local voice selected) |

**First run:** a 3-step overlay: (1) car profile (BD12 default); (2) start a session (track name + chips); (3) model check (status, pull hint `ollama pull gemma4:e2b-it-qat`, or "skip, use chips only").

**Slow-model states:** show the step list with live elapsed timers; stream tokens; never block the card on the explanation; show "First answer after start can take longer while the model loads" when `loaded` is false; send `/api/llm/warmup` when the app opens and after a model change.

## 6. Visual explainers

**Car model (new, procedural, about 300 lines):** chassis plate (box), top deck (thin box), four wheel assemblies (cylinder tyre + rim disc) on uprights, lower arms and camber links as thin cylinders between hardpoints, shock towers, shocks as two coaxial cylinders between a tower hole and an arm point, an anti-roll bar (thin tube with two arms), a translucent wireframe body outline with a lip. Proportions from the snapshot: wheelbase about 261 mm, width about 192 mm over the tyres, shocks 14-17 mm ahead of the front axle and 14-19 mm behind the rear axle (`yokomo-bd12#specification-gaps-partly-filled-from-yokomo-s-o`, `...#component-layout-from-the-setup-sheet-top-view`). It is labelled "schematic, not to scale" and is not derived from any earlier model.

**Scene API (`src/scene/types.ts`, replacing the current stub):**

```ts
interface CarScene {
  mount(el: HTMLElement): void;
  setPose(pose: Partial<ScenePose>): void;                       // immediate
  showChange(b: SceneBinding, opts?: { exaggerate?: number; ms?: number }): void; // ghost at `from`, solid lerps to `to`, highlights the part
  setView(v: "front" | "side" | "top" | "iso" | "auto"): void;   // auto = the explainer's default view
  highlight(part: PartId | null): void;
  dispose(): void;
}
interface ScenePose { frontCamberDeg; rearCamberDeg; frontToeOutDeg; rearToeInDeg; casterDeg; rideHeightFrontMm; rideHeightRearMm;
  droopFrontGaugeMm; droopRearGaugeMm; frontShockPos; rearShockPos; frontArbMm; rearArbMm; steerDeg; compressionMm; liftChassis: boolean }
```

`SceneBinding` comes only from the server's `LeverSuggestion.scene` or the Setup editor's own values; the LLM never emits scene values.

| Explainer | View | What moves | Default exaggeration | Ship |
| --- | --- | --- | --- | --- |
| camber | front | wheels tilt, top in for negative | x3 | **MVP** |
| toe | top | wheels yaw; front toe-out, rear toe-in | x4 | **MVP** |
| caster | side | kingpin axis tilts back; contact patch marker behind the pivot | x2 | **MVP** |
| rideHeight + droop | side | chassis height; "lift" toggle lets wheels hang to show droop (gauge label: lower = more travel) | x4 (mm) | **MVP** |
| shockAngle | front/rear | shock top moves between tower holes 1..5 (inner = laid down, outer = upright) | x1.5 | **MVP** |
| arb | iso | bar thickness and twist under roll | x3 | stretch |
| ackermann | top, SVG | inner wheel steers more than outer at lock; shims move toward parallel | x2 | stretch |
| bumpSteer | front | compress suspension; toe-in appears with more shim | x5 | stretch |
| rollCentre | front, SVG | lines from arm and camber link to the instant centre; RC height mark | x1 | stretch |
| weight | top, SVG | front/rear %, arrow for transfer under braking (`dW = m*a*h/L`) | n/a | stretch |
| body | side | shell slides forward/back | x2 | stretch |

**Interaction:** sliders bound to the selected param (Setup panel) or a before/after toggle (Coach card); ghost copy at 35% opacity for "before"; the changed part in the accent colour; 600 ms ease; camera presets as big buttons; a permanent label "angles exaggerated xN for visibility"; OrbitControls limited (no pan, clamp zoom).

**Accuracy rules:** directions and sign conventions only from the snapshot pages cited in Appendix A.1; never show a magnitude without the exaggeration label; no tyre, motor or body brand detail.

**Performance (Intel UHD 630 / Radeon 5300M):** one `WebGLRenderer`, `antialias: true`, `setPixelRatio(Math.min(devicePixelRatio, 1.5))`, render on demand (only during tweens or orbit drags), under 5k triangles, `MeshLambertMaterial` + one directional + one ambient light, no shadows or post-processing, stop the loop on `visibilitychange`, dispose geometries on unmount. Target under 16 ms per frame during tweens (measure with the browser performance panel on the dev Mac; his laptop unmeasured).

**Overrun rule:** T5 is timeboxed to 2 h. At T5 start + 75 min, if fewer than 2 three.js explainers work, switch the remaining MVP views to SVG (`src/scene/svg/*`) behind the same `CarScene` API.

## 7. Task cards

Model guide: **Sonnet 5.5** for well-specified plumbing, CRUD and UI; **Opus 5.5** for contracts, the coach workflow and prompts, three.js, and integration. Parallel tasks share one working tree with disjoint paths; the orchestrator runs each card's acceptance commands and commits only that card's paths with a conventional message (`feat(server): ...`, `feat(ui): ...`, `chore: ...`), after `npm run kb:verify` and `npm run typecheck`.

### Dependency graph

```
                 T0 contracts + scaffold (Opus)
   +-----------+-----------+-----------+-----------+-----------+
   T1 server   T2 data +   T3 coach    T4a shell + T4b setup + T5 explainers
   + vault     engine + kb workflow    coach UI    session UI  (Opus, 2 h box)
   (Sonnet)    (Sonnet)    (Opus)      (Sonnet)    (Sonnet)
   |           |  \          |           |           |           |
   |           |   T8 analysis (Sonnet, after T2)    |           |
   +-----------+----+--------+-----------+-----------+           |
                    T7 walking skeleton integration (Opus) <------+ (binding only)
                    |
     +--------------+--------------+-------------+
     T4c race day + settings UI   T6 voice      T9 eval + measurements
     (Sonnet)                     (Sonnet)      (Sonnet)
     +--------------+--------------+-------------+
                    T10 final integration, airplane run, seed, freeze (Opus)
```

### T0 Contracts and scaffold (Opus, 30 min, serial, starts 22:05Z)
- **Goal:** everything other tasks need to work in parallel without touching shared files.
- **Owns:** `package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `.gitignore`, `.env.example`, `index.html` (initial), `src/main.tsx` (initial; delete `src/main.ts`), `src/shared/**`, `src/ui/store.ts`, `server/config.ts`, `server/routes/index.ts`, `server/coach/engine.ts` (interface), and **stub files** for every module in 2.1 exporting the documented signatures (throw `new Error("not implemented")` or return 501), plus one empty component per screen (`src/ui/setup/SetupScreen.tsx`, `src/ui/session/SessionScreen.tsx`, `src/ui/race/RaceScreen.tsx`, `src/ui/settings/SettingsScreen.tsx`, `src/ui/coach/CoachScreen.tsx`).
- **Do:** install the packages in section 3 in one `npm install`; apply the config edits in section 3; write the zod schemas and types of 2.2 and the SSE event names; `src/ui/store.ts` with signals `meta`, `settings`, `session`, `currentSetup`, `llmStatus`, `route`; `server/index.ts` minimal (T1 takes it over) serving `/api/health`.
- **Acceptance:** `npm run typecheck` passes; `npm run dev` then `curl -s localhost:5173/api/health` returns `{"ok":true,...}` through the proxy; `npm test` exits 0 (no tests yet is fine with `--passWithNoTests`); `npm run kb:verify` ok; `npm run kb:build` still 106 chunks.
- **Risk:** TS 7 / preset-vite JSX config. Fallback in section 1.

### T1 Server core and vault (Sonnet, 75 min, parallel)
- **Goal:** all vault, settings, meta, export/import routes on a migrated `var/pit.db`.
- **Owns:** `server/index.ts`, `server/db.ts`, `server/vault/**`, `server/routes/{vault,meta,settings}.ts`, `tests/vault.test.ts`.
- **Inputs:** 2.2 types, 2.4 table, 4.5 vault design. Read data files through `server/engine/data.ts` (T2) once it exists; until then import the JSON directly behind a small loader in `server/vault/meta.ts`.
- **Interfaces:** export repo functions `createSession`, `getSessionBundle`, `applySetupChanges(sessionId, values, meta) -> { setup, changes }`, `addRun`, `setChangeOutcome`, `listSaved`, `saveSetup`, `exportAll`, `importAll`, `getSettings`, `putSettings` (T3's `apply` step calls `applySetupChanges`). Serve `dist/` with SPA fallback when `NODE_ENV=production` or `dist/index.html` exists and the request is not `/api/*`.
- **Acceptance:** `npm test -- tests/vault.test.ts` passes (uses `:memory:`: session create gives a baseline setup with BD12-then-generic values; `applySetupChanges` writes one Change per changed param and a new setup row; export then import round-trips counts); `curl` POST session, POST setup change, POST run, GET bundle all return valid shapes.
- **Risk:** low. libsql native binary on Intel Mac is unverified (fallback: JSON files).

### T2 Domain data, lever engine, KB search (Sonnet, 60 min, parallel)
- **Goal:** the reviewed tables as files, the deterministic engine, keyword classifier/refusals, search.
- **Owns:** `data/params.bd12.json`, `data/symptoms.json`, `data/levers.json`, `data/prechecks.json`, `server/engine/**`, `server/kb/**`, `server/routes/kb.ts`, `scripts/build-kb.mjs`, `tests/engine.test.ts`.
- **Do:** copy Appendix A blocks into the data files exactly, keeping `status` values as the author set them. Extend `build-kb.mjs` to also fail when a lever `param` or a precheck id is unknown, or a precheck/param citation does not resolve. Implement 4.3 (`selectLevers`, clamp, enum stepping, history skip), `keywordClassify` (synonym substring + token overlap; returns null below a threshold), `refusalFor`, MiniSearch index over `text` + `lead` + `pageTitle` with prefix and fuzzy 0.2.
- **Acceptance:** `npm run kb:build` passes with 0 unknown citations; `npm test -- tests/engine.test.ts` covers: BD12 exit-oversteer skips `xo-rear-toe-in-more` as at-limit; clamp at min; null current gives `needsCurrentValue`; `worse` history skips a lever; enum hex stepping; `reviewedOnly` hides drafts; refusal for "what shore tyres". `curl 'localhost:8787/api/kb/search?q=droop'` returns 3 chunks.
- **Risk:** lever review not done yet: ship with `draft` status; the flag handles it.

### T3 Coach workflow, Ollama client, prompts (Opus, 90 min, parallel; Mastra timebox 45 min)
- **Goal:** `CoachEngine` implemented with Mastra (fallback plain), SSE route, LLM status/pull/warmup.
- **Owns:** `server/llm/**`, `server/coach/**` (except the interface file), `server/routes/{coach,llm}.ts`.
- **Inputs:** 2.3-2.5, Appendix B prompts, T2's `selectLevers`/`refusalFor`/`keywordClassify` (stub-call them until T2 lands), T1's `applySetupChanges`/`setChangeOutcome`.
- **Do:** first 45 min: a script `server/coach/spike.ts` that starts the workflow, suspends, restarts the process, resumes twice against `var/mastra.db`. Pass: continue with Mastra. Fail: implement `workflow.plain.ts`, report FAILED + DECISION memory entries. Then the Ollama client (native `/api/chat`, stream parse of NDJSON, `format`, `num_ctx`, `keep_alive`, `AbortSignal`), the number guard, template fallback, the classifier (schema `{symptom_id enum, alt_id enum+none, phase enum, confidence number}`), timing fields (`ms`) on events.
- **Acceptance:** `curl -N -X POST localhost:8787/api/coach/turn -d '{"sessionId":"<id>","utterance":"back end snaps loose when I punch it out of the hairpin"}' -H 'content-type: application/json'` prints `classified` (exit-oversteer), `precheck`, `suggestion`, `token`s, `explained`, `suspended`; then `decide` apply writes a Change; `outcome` worse returns `offer-revert` and a `next` suggestion; killing and restarting the server between `decide` and `outcome` still works (Mastra path); `{"symptomId":"traction-roll"}` makes no classify LLM call; "what shore hardness tyres" returns `refusal` with the gap citation; with Ollama stopped, the route still returns keyword classification or a clear `error` event and template explanations.
- **Risk:** Mastra API details (stream event shapes). Mitigations in 2.5.

### T4a App shell, coach panel, API client (Sonnet, 90 min, parallel)
- **Owns:** `src/main.tsx`, `index.html`, `src/style.css` (theme tokens, base components: Button, Chip, Card, Banner, Drawer in `src/ui/app/`), `src/ui/app/**`, `src/ui/coach/**`, `src/api/client.ts`.
- **Do:** layout of 5.1, hash router, top status bar (polls `/api/llm/status` every 15 s, `navigator.onLine`), first-run overlay, coach flow over SSE (`fetch` + `ReadableStream` parser, since `EventSource` cannot POST), citation drawer, outcome buttons, "Ask the notes" box (kb search results as cards). Use the voice and scene modules only through their `types.ts` interfaces with a no-op fallback until T6/T5 land.
- **Acceptance:** with the server running: tap "Loose on power" shows a card in under 1 s on the dev Mac; typed utterance streams tokens; APPLY then WORSE shows the revert offer; all buttons at least 48 px (check in devtools); no console errors.

### T4b Setup editor and session log (Sonnet, 90 min, parallel)
- **Owns:** `src/ui/setup/**`, `src/ui/session/**`.
- **Do:** 5.2 and 5.3 (without the comparison panel content, which renders `RunComparison` from T8 when available), start-session form, log-run form, save-setup dialog, staged changes with commit/undo, computed FDR, range hints, explainer panel slot (calls `CarScene` via `src/scene` exports).
- **Acceptance:** create session, change two params, commit: two Change rows appear in the session view; log a run with pasted lap times "14.9 15.1, 14.8": stored as `[14900, 15100, 14800]`; out-of-range value flagged.

### T5 Visual explainers (Opus, 2 h timebox, parallel)
- **Owns:** `src/scene/**`.
- **Do:** section 6: procedural car, the 5 MVP explainers, `showChange` with ghost and highlight, camera presets, exaggeration label, render on demand, dispose. Export `createCarScene(): CarScene` and `explainerFor(param): ExplainerId | null`. A dev page is allowed at `src/scene/dev.html` (not linked from the app).
- **Acceptance:** in the dev page, each MVP explainer animates from `from` to `to` with the label visible; switching views works; after 30 s idle the render loop is stopped (log count of frames); no WebGL warnings; T4a's coach card shows the scene for `xo-rear-shocks-up`.
- **Risk:** overrun; rule in section 6.

### T7 Walking skeleton integration (Opus, 30 min, serial, ~00:20Z)
- **Goal:** the MVP-1 loop works end to end in the browser. May edit any file; applies contract change requests from task reports.
- **Acceptance (MVP-1):** fresh `var/`: first-run overlay, start session; type "rear steps out on power" (or tap the chip); classified exit-oversteer; pre-check toggles; one cited change card; APPLY updates Setup and logs a Change; log a run; WORSE offers revert; revert applies; all visible in Session. `npm test`, `npm run typecheck`, `npm run kb:verify` pass.

### T8 Analysis: similar conditions, run comparison, history (Sonnet, 45 min, parallel after T2)
- **Owns:** `server/analysis/**`, `server/routes/analysis.ts`, `tests/analysis.test.ts`.
- **Do:** 4.6 and 4.7 exactly; return types `SimilarHit`, `RunComparison` added to `src/shared` by request (or defined locally and re-exported; T7 moves them).
- **Acceptance:** tests: the same track and surface ranks above a different track; surface mismatch is grouped; MDE with sigma 0.15, n 10 gives 0.19 s (rounded); a 0.11 s gap with that floor returns "within-noise"; fewer than 3 laps returns "insufficient-data"; two changed params set `confounded`.

### T4c Race day, comparison panel, settings (Sonnet, 75 min, wave 2)
- **Owns:** `src/ui/race/**`, `src/ui/settings/**`, plus `src/ui/session/ComparePanel.tsx` (handed over from T4b by name).
- **Do:** 5.4, 5.5, comparison rendering of 5.3, export download / import upload, pull progress bar.
- **Acceptance:** two saved setups at different tracks rank correctly for today's conditions; Load stages the diff in Setup; export then reset then import restores counts; pull shows progress (test with a small model or a mocked SSE).

### T6 Voice in and out (Sonnet, 60 min, wave 2)
- **Owns:** `src/voice/**`, `server/routes/speak.ts`.
- **Do:** `SpeechInput` with `processLocally = true`, `available({ langs: ["en-US"], processLocally: true })`, `install(...)`, interim results, `phrases` biasing when present (droop, Ackermann, caster, camber, toe, bump steer, anti-roll bar, understeer, oversteer, traction roll); cloud mode only when the setting says so; `SpeechOutput` with local voices only and sentence-by-sentence speaking of the streamed text; `say` fallback route (spawn with args array, never a shell string; kill the previous process on new text or cancel). Exact `available()`/`install()`/`phrases` call signatures: check MDN and Chrome's current docs before coding (marked unverified here).
- **Acceptance:** on the dev Mac in Chrome (version noted): report what `available()` returns; with Wi-Fi off, record whether on-device recognition works (this is a MEASURE/HONEST entry either way); speech output works with Wi-Fi off using a voice where `localService === true`; Space push-to-talk works; disabling voice leaves the text path untouched.

### T9 Eval and measurements (Sonnet, 60 min, wave 2)
- **Owns:** `data/eval/**`, `scripts/eval-symptoms.ts` (replaces the `.mjs`, which T9 deletes; imports the classifier prompt and schema from `server/coach/prompts.ts`), `scripts/eval-retrieval.ts`. T0 creates both `.ts` files and `scripts/seed-demo.ts` as stubs so the npm scripts resolve.
- **Do:** section 8. Run on the dev Mac (GPU, and `CPU_ONLY=1` proxy). Report numbers as MEMORY ENTRIES with full context.
- **Acceptance:** both scripts print a JSON summary; symptom eval has 25 cases (6 out-of-scope); retrieval eval has 20 questions; the keyword baseline is reported next to Gemma.

### T10 Final integration, seed, airplane run, freeze (Opus, 55 min, serial, 02:20Z)
- **Owns:** anything; `scripts/seed-demo.ts`.
- **Do:** fix integration bugs; seed a clearly labelled demo session (`trackName: "DEMO track"`, notes "demo data"); run the demo checklist (section 8.3) including Wi-Fi off; Safari smoke test; record measurements; `npm run build` and `npm start` on the dev Mac; update nothing in README (writing phase owns it).
- **Acceptance:** demo checklist all green or each failure logged as HONEST; code freeze tag commit `chore: code freeze for submission`.

### Timeline (UTC)

| Time | Work | Gate |
| --- | --- | --- |
| 21:45-22:05 | Author: decisions in section 1, demo-path lever review, commit pending changes, (Entire dropped by the author) | |
| 22:05-22:35 | T0 | typecheck + proxy health |
| 22:35-00:20 | Wave 1 parallel: T1, T2 (then T8 at ~23:35), T3, T4a, T4b, T5. Author reviews remaining lever rows by 23:15 | T2 data in by 23:35 |
| 00:20-00:50 | T7 walking skeleton (author eats while agents of wave 2 are briefed) | **MVP-1 line 00:50**: the loop in T7 acceptance |
| 00:50-02:20 | Wave 2 parallel: T4c, T6, T9, T5 finishes/binds, T3 polish (number guard, timings) | **MVP-2 line 02:20**: + race-day finder, run comparison, 4-5 explainers, voice out, eval numbers |
| 02:45 | **Cut line:** no new features after this | |
| 02:20-03:15 | T10 | **Code freeze 03:15** |
| 03:15-03:45 | Author: rehearse demo twice, screenshots | |
| 03:45-04:30 | Record demo video (airplane mode on camera) | protected |
| 04:30-05:00 | README (run steps, prior-work credit, honest limits, post-deadline commit note) | protected |
| 05:00-05:50 | DEV post draft from the memory file; humanizer pass | protected |
| 05:50-06:05 | DevRelay session export, scrub, upload (private), get embed | protected |
| 06:05-06:15 | `hf26-challenge` audit; `create_article` with `published: false`; give the author the draft link | protected |
| 06:15-06:40 | Author reads; publishes only on his explicit yes | |
| 06:40-06:59 | Buffer | deadline |

**If MVP-1 is not reached by 01:15:** cut in this order until it is: (1) "Ask the notes" LLM summary; (2) stretch explainers; (3) Whisper (already post-deadline); (4) `say` fallback; (5) remaining three.js views to SVG; (6) Mastra to plain TS; (7) voice input (keep typing and chips); (8) run comparison reduced to the setup and condition diff (no lap statistics); (9) race-day finder reduced to a sorted list by track name and surface. Never cut: the lever table with citations, the vault quick entry, the honest-statistics wording, or the writing block.

## 8. Quality and verification

### 8.1 Eval plan (T9)

**Symptom set:** keep the 10 existing cases and add 15 (25 total, 6 out-of-scope). Drafts below; the author should reword at least five in the friend's own way of speaking before the run, so the eval is not written to fit the prompt.

| say | expect |
| --- | --- |
| it's pushing like a shopping cart going into the hairpin | entry-understeer |
| tail happy on the brakes into turn one | entry-oversteer |
| the back end lets go the moment I squeeze the trigger | exit-oversteer |
| the thing tipped over twice in the fast left-hander | traction-roll |
| super darty down the straight, I can't keep it in a line | nervous-twitchy |
| feels like driving on ice everywhere this morning | low-grip |
| great for the first couple of minutes then it goes off and gets lazy | fade-late-run |
| it turns way better to the left than to the right | left-right-difference |
| it hops and bounces through the bumpy chicane | bumpy-track |
| plows wide through the long sweeper and never comes back to the apex | mid-understeer |
| when I get back on the gas it just goes straight on | exit-understeer |
| what shore hardness tyres should I buy for this track? | out-of-scope |
| how do I set the timing on my ESC? | out-of-scope |
| best brushless motor for 13.5 stock? | out-of-scope |
| my buggy lands badly off the double, what shocks? | out-of-scope |

Report: correct %, out-of-scope correct %, median and p90 time to first token and total ms, decode tokens/s, for (a) `gemma4:e4b-it-qat` on M4 Max GPU, (b) same with `CPU_ONLY=1`, (c) `gemma4:e2b-it-qat` CPU-only proxy if the author pulls it (ask first; 4.3 GB), (d) the keyword baseline. State that schema enforcement guarantees valid JSON.

**Retrieval check (`eval-retrieval.ts`):** 20 questions, hit = any expected id in MiniSearch top 3. Pass threshold 85% (memory decision); below it, add synonyms to the index (`kb` field boosts) before considering embeddings.

| question | accept any of |
| --- | --- |
| what does droop do | `touring-car-setup-procedure#droop-baselines`, `vehicle-dynamics-fundamentals#droop` |
| why reset droop after changing ride height | `touring-car-setup-procedure#the-load-bearing-dependency` |
| bd12 factory camber and toe | `yokomo-bd12#factory-baseline-alignment` |
| how much ackermann shim | `touring-car-steering-geometry#ackermann-effect` |
| what is bump steer | `touring-car-steering-geometry#bump-steer` |
| caster for tight hairpins | `touring-car-steering-geometry#caster` |
| thicker rear anti roll bar effect | `touring-car-suspension-tuning#anti-roll-bars-arb` |
| what is the roll centre | `touring-car-suspension-tuning#roll-center` |
| shock oil cst range | `touring-car-suspension-tuning#shock-oil-viscosity` |
| laying shocks down | `touring-car-suspension-tuning#shock-mounting-angle` |
| stop traction rolling | `touring-car-traction-and-tire-management#traction-rolling` |
| more rear grip on exit | `touring-car-traction-and-tire-management#increasing-rear-specific-traction` |
| how often rotate tyres | `touring-car-traction-and-tire-management#rotation-cadence-is-per-pack-not-per-session`, `...#tire-rotation-and-cycling` |
| front rear weight balance target | `touring-car-weight-balance#front-rear-target` |
| belt tension steps | `touring-car-drivetrain-tuning#belt-tension` |
| final drive ratio formula | `touring-car-drivetrain-tuning#gearing` |
| brake epa percent | `touring-car-radio-and-servo-setup#brake-epa-is-the-other-mechanically-consequentia`, `touring-car-setup-procedure#other-race-day-critical-checks` |
| body shell forward or back | `touring-car-aerodynamics#fore-aft-body-position` |
| front lip clearance on asphalt | `touring-car-aerodynamics#front-lip-clearance` |
| how many laps to tell a setup is faster | `minimum-detectable-lap-time-difference#definition`, `...#with-a-typical-lap-time-standard-deviation` |

**Unit tests (only these):** `tests/engine.test.ts` (T2), `tests/vault.test.ts` (T1), `tests/analysis.test.ts` (T8). No UI tests.

### 8.2 What to measure for the post (append as MEASURE entries with date, machine, model, method)

1. Symptom eval results per configuration above, plus the keyword baseline.
2. Coach turn latency on the dev Mac: chip tap to card (ms), typed utterance to card, utterance to first explanation token, to full explanation; on GPU and CPU-only proxy; `ollama ps` resident memory with `num_ctx` 4096.
3. Retrieval top-3 hit rate.
4. Lever table stats: rows, reviewed, draft, `inverse`/`inferred` rows, flagged gaps, distinct chunks cited (current draft: 60 rows, 58 distinct chunks cited across levers, prechecks and params).
5. Airplane-mode run outcome on the dev Mac (what worked: model, vault, explainers, speech out, speech in).
6. If the friend becomes reachable: the same eval and latency on his laptop with E2B, his macOS and Chrome versions, and his words after trying it (quote only with permission).

### 8.3 Demo-day checklist (T10, repeated by the author before recording)

- [ ] `npm run kb:verify`, `npm run typecheck`, `npm test` green; `npm start` serves the built app on 8787.
- [ ] Model warmed (`/api/llm/warmup`), `ollama ps` shows it loaded with context 4096.
- [ ] **Wi-Fi off:** chip path, typed path with Gemma, citations drawer, apply, log run, outcome, revert, race-day finder, run comparison, explainer animation, speech out. Note any outbound request (Chrome devtools Network tab; optionally `lsof -i -P | grep -E 'node|ollama'`).
- [ ] Voice in: record the `available()` result with Wi-Fi off; if not on-device, the demo uses typing and chips and says so.
- [ ] Out-of-scope refusal ("what shore tyres") shows the gap citation.
- [ ] Stock BD12 exit-oversteer shows "rear toe already at 3.5" skip line.
- [ ] Safari: app loads, text path works, voice input reported unsupported (expected).
- [ ] Demo data visibly labelled "DEMO".

### 8.4 Commit strategy

Small commits per task by the orchestrator, conventional messages, each commit only the task's owned paths (`git add <paths>`), never `git add -A`. `npm run kb:verify` before every commit. Commits after 06:59Z go in a README section "Commits after the deadline". The memory file is committed by the orchestrator with each batch of appended entries (`docs: update challenge memory`).

## 9. Entire, DevRelay and what the post needs

| When | Item | Who |
| --- | --- | --- |
| ~~21:45-22:05~~ | ~~Install the Entire CLI and `entire enable`~~ **Dropped by the author (workload), 2026-10-04.** | n/a |
| ~~any time~~ | ~~Entire checkpoints~~ dropped | n/a |
| 05:50-06:05 | DevRelay session export (`devrelay-sessions`): curate the build session, scrub paths, email, signed URLs; upload private; author makes it public on DEV before embedding | orchestrator + author |
| 06:05-06:15 | `create_article` with `published: false`, default `ai_disclosure_level`; return the draft link | orchestrator |

**Assets the build must produce for the post:** screenshots of the coach card with citation chips and the skip line; setup editor with diff badges; race-day finder; run comparison saying "no clear difference" with the noise floor; an explainer before/after ghost; settings model status. One GIF or short clip: speak or type, card appears, wheels/shocks move, APPLY, outcome. The architecture diagram from section 2. Measurements from 8.2. The lever-table review story (rows reviewed, gaps refused).

## 10. Risks

| # | Risk | Trigger | Mitigation / fallback |
| --- | --- | --- | --- |
| 1 | Mastra friction (stream events, resume semantics, API churn in a 1.74 release) | T3 spike not passing at +45 min | Plain `CoachEngine`; drop the Mastra category; log FAILED + DECISION |
| 2 | Gemma too slow on his CPU-only i7 (unmeasured; planner estimate in the memory file: E4B decode 5-15 tok/s) | Classify over ~10 s in the CPU proxy, or his numbers when measured | Chips skip the classifier; card before explanation; "Coach phrasing" off; E2B; `num_ctx` 4096; stable prompt prefix for KV reuse; warm-up; `keep_alive` 30 m |
| 3 | On-device speech recognition unavailable (Intel Mac Chrome language pack support unverified; embedded Chromium already said "unavailable") | `available()` not `available`/`downloadable` with `processLocally` | Typing and chips; opt-in cloud mode labelled; no offline-voice claim; Whisper post-deadline |
| 4 | three.js overrun | Fewer than 2 explainers working at T5 + 75 min | SVG views behind the same API; ship 3 views minimum |
| 5 | Lever table review bottleneck (60 rows) | Demo-path rows not reviewed by 22:05, rest not by 23:15 | Demo path first; `status` badge and `reviewedOnly` setting; the post states how many rows were reviewed |
| 6 | His laptop not ready (no Ollama, macOS < 14, no Node 22.13+), and he is unreachable | No contact before 03:15 | Degraded mode (vault + lever table + keyword) works without Ollama; README install steps; post says handover is pending and no claims about his machine |
| 7 | Parallel-agent collisions or contract drift | `npm run typecheck` fails after a task, or a task edits a file it does not own | T0 contracts and stubs, ownership table, single install, orchestrator-only commits, T7 applies contract changes |
| 8 | Time overrun eats the writing block (Writing Quality is weighted most) | MVP-1 missed at 01:15, or code not frozen by 03:15 | Cut order in section 7; the writing block starts at 03:45 regardless |

Also watched: Safari differences (target Chrome; Safari text path only); misclassification (alt-id chips under confidence 0.6, eval); model number invention (number guard plus template); Mastra telemetry (env var set; verify in the airplane run).

## Appendix A: DRAFT-FOR-REVIEW data (traceable to snapshot chunk ids)

All citations below were checked against the 113 chunk ids in `data/generated/kb.json` (106 from the snapshot + 7 from `kb/additions`) (built by `scripts/build-kb.mjs`; slug rule: page file name + `#` + the bold lead of the Key Points bullet, lower-cased, non-alphanumerics to `-`, cut to 48 characters). Result: 0 unknown citations, 61 lever rows (52 numeric, 9 qualitative), 37 parameters, 14 pre-checks, 12 symptoms, 58 distinct chunks cited. Every row starts as `"status": "draft"`; the author flips rows to `"reviewed"`. T2 copies each block verbatim into the named file.

### A.1 BD12 parameter schema -> `data/params.bd12.json`

```json
{
  "car": "yokomo-bd12",
  "status": "DRAFT-FOR-REVIEW",
  "baselineRule": "Use the bd12 value when present; otherwise the generic (Xray-derived) value, shown with a 'generic' tag. Source: yokomo-bd12#factory-baseline-alignment.",
  "conventions": {
    "camber": "Stored as degrees of NEGATIVE camber (1.5 = 1.5 deg negative; top of the tyre leans in).",
    "frontToe": "Front toe-OUT per side in degrees; front toe-in is never used (min 0).",
    "rearToe": "Rear toe-IN in degrees.",
    "caster": "Positive caster in degrees: steering axis tilted back, pivot ahead of the contact patch.",
    "droop": "Droop GAUGE reading in mm: a LOWER number means MORE droop (more travel).",
    "rideHeight": "mm, measured behind the front arm / in front of the rear arm, never at the chassis ends.",
    "shockPos": "Index: 1 = most laid down (inner hole) ... max = most upright (outer hole).",
    "camberLinkShim": "Shim under the INNER camber-link ball stud: more shim = flatter link = lower roll centre, less camber gain."
  },
  "params": [
    {"id": "frontCamberDeg", "label": "Front camber", "group": "alignment", "unit": "deg neg", "kind": "number", "min": 1.0, "max": 2.5, "step": 0.5, "bd12": 1.5, "generic": 2.0, "src": ["yokomo-bd12#factory-baseline-alignment", "touring-car-setup-procedure#camber-and-toe-baselines", "touring-car-traction-and-tire-management#traction-rolling"], "range": "partial: 1.0 from traction-rolling; max 2.5 UNSOURCED", "explainer": "camber"},
    {"id": "rearCamberDeg", "label": "Rear camber", "group": "alignment", "unit": "deg neg", "kind": "number", "min": 1.5, "max": 3.0, "step": 0.5, "bd12": 2.5, "generic": 2.0, "src": ["yokomo-bd12#factory-baseline-alignment", "touring-car-setup-procedure#camber-and-toe-baselines"], "range": "UNSOURCED", "explainer": "camber"},
    {"id": "frontToeOutDeg", "label": "Front toe-out (per side)", "group": "alignment", "unit": "deg", "kind": "number", "min": 0, "max": 1.5, "step": 0.5, "bd12": 1.0, "generic": 1.0, "src": ["yokomo-bd12#factory-baseline-alignment", "touring-car-setup-procedure#camber-and-toe-baselines", "touring-car-traction-and-tire-management#traction-rolling"], "range": "snapshot (toe-in never used; ~1.5 for traction rolling)", "explainer": "toe"},
    {"id": "rearToeInDeg", "label": "Rear toe-in", "group": "alignment", "unit": "deg", "kind": "number", "min": 2.0, "max": 3.5, "step": 0.5, "bd12": 3.5, "generic": 2.5, "src": ["yokomo-bd12#factory-baseline-alignment", "touring-car-setup-procedure#camber-and-toe-baselines", "touring-car-traction-and-tire-management#increasing-rear-specific-traction"], "range": "snapshot (2.0 high grip ... 3.5 low grip)", "explainer": "toe"},
    {"id": "casterDeg", "label": "Caster", "group": "alignment", "unit": "deg", "kind": "number", "min": 2, "max": 6, "step": 1, "bd12": null, "generic": 4, "src": ["touring-car-steering-geometry#caster"], "range": "snapshot (2 ... 5-6)", "explainer": "caster"},
    {"id": "rideHeightFrontMm", "label": "Ride height front", "group": "chassis", "unit": "mm", "kind": "number", "min": 5.0, "max": 5.8, "step": 0.2, "bd12": 5.0, "generic": 5.0, "src": ["yokomo-bd12#factory-baseline-alignment", "touring-car-setup-procedure#ride-height-baseline"], "range": "snapshot (5.0 smooth ... 5.8 bumpy)", "explainer": "rideHeight"},
    {"id": "rideHeightRearMm", "label": "Ride height rear", "group": "chassis", "unit": "mm", "kind": "number", "min": 5.0, "max": 5.8, "step": 0.2, "bd12": 5.0, "generic": 5.2, "src": ["yokomo-bd12#factory-baseline-alignment", "touring-car-setup-procedure#ride-height-baseline"], "range": "snapshot; rear usually 0.2 above front (rake)", "explainer": "rideHeight"},
    {"id": "droopFrontGaugeMm", "label": "Droop front (gauge; lower = more droop)", "group": "chassis", "unit": "mm", "kind": "number", "min": 4.8, "max": 6.4, "step": 0.2, "bd12": null, "generic": 5.6, "src": ["touring-car-setup-procedure#droop-baselines", "yokomo-bd12#factory-baseline-alignment"], "range": "UNSOURCED (only baseline known); BD12 specifies droop differently: 1.5-2.0 mm upward extension when lifted at 5.0 mm ride height", "explainer": "droop"},
    {"id": "droopRearGaugeMm", "label": "Droop rear (gauge; lower = more droop)", "group": "chassis", "unit": "mm", "kind": "number", "min": 3.8, "max": 5.4, "step": 0.2, "bd12": null, "generic": 4.6, "src": ["touring-car-setup-procedure#droop-baselines"], "range": "UNSOURCED (only baseline known)", "explainer": "droop"},
    {"id": "weightFrontPct", "label": "Front weight", "group": "chassis", "unit": "%", "kind": "number", "min": 48, "max": 52, "step": 1, "bd12": null, "generic": 50, "src": ["touring-car-weight-balance#front-rear-target"], "range": "snapshot (48/52 ... 52/48)", "explainer": "weight"},
    {"id": "weightLeftPct", "label": "Left weight", "group": "chassis", "unit": "%", "kind": "number", "min": 48, "max": 52, "step": 1, "bd12": null, "generic": 50, "src": ["touring-car-weight-balance#left-right-target", "touring-car-weight-balance#on-the-owner-s-bd12-the-layout-starts-asymmetric"], "range": "target 50, 49-51 acceptable; outer bounds UNSOURCED"},
    {"id": "ackermannShimMm", "label": "Ackermann shim (rack)", "group": "steering", "unit": "mm", "kind": "number", "min": 0, "max": 1.0, "step": 0.5, "bd12": null, "generic": 0.5, "src": ["touring-car-steering-geometry#ackermann-effect"], "range": "snapshot (0 ... ~1.0 ceiling; baseline 0-0.5)", "explainer": "ackermann"},
    {"id": "bumpSteerShimMm", "label": "Bump-steer shim (outer block)", "group": "steering", "unit": "mm", "kind": "number", "min": 0, "max": 2.0, "step": 0.5, "bd12": null, "generic": 1.0, "src": ["touring-car-steering-geometry#bump-steer"], "range": "snapshot (asphalt 1.0-2.0, carpet 0-1.0)", "explainer": "bumpSteer"},
    {"id": "steeringExpoPct", "label": "Steering expo", "group": "steering", "unit": "%", "kind": "number", "min": -20, "max": 0, "step": 5, "bd12": null, "generic": -5, "src": ["touring-car-radio-and-servo-setup#steering-expo"], "range": "snapshot (wheel -5 to -10, stick -10 to -20)"},
    {"id": "frontArbMm", "label": "Front anti-roll bar", "group": "damping", "unit": "mm", "kind": "number", "min": 1.0, "max": 1.6, "step": 0.1, "bd12": null, "generic": 1.3, "src": ["touring-car-suspension-tuning#anti-roll-bars-arb"], "range": "UNSOURCED (baseline ~1.3 only)", "explainer": "arb"},
    {"id": "rearArbMm", "label": "Rear anti-roll bar", "group": "damping", "unit": "mm", "kind": "number", "min": 1.0, "max": 1.6, "step": 0.1, "bd12": null, "generic": 1.2, "src": ["touring-car-suspension-tuning#anti-roll-bars-arb"], "range": "UNSOURCED (baseline ~1.2 only)", "explainer": "arb"},
    {"id": "frontSpringRate", "label": "Front spring rate (one brand's scale)", "group": "damping", "unit": "rate", "kind": "number", "min": 2.0, "max": 3.2, "step": 0.1, "bd12": null, "generic": null, "src": ["touring-car-suspension-tuning#springs"], "range": "snapshot spans 2.0-2.3 (BD11 rear) to 3.0-3.2 (hard); step UNSOURCED"},
    {"id": "rearSpringRate", "label": "Rear spring rate (one brand's scale)", "group": "damping", "unit": "rate", "kind": "number", "min": 2.0, "max": 3.2, "step": 0.1, "bd12": null, "generic": null, "src": ["touring-car-suspension-tuning#springs", "yokomo-bd12#the-bd11-predecessor"], "range": "as front"},
    {"id": "frontOilCst", "label": "Front shock oil", "group": "damping", "unit": "cSt", "kind": "number", "min": 300, "max": 600, "step": 50, "bd12": null, "generic": null, "src": ["touring-car-suspension-tuning#shock-oil-viscosity"], "range": "snapshot (300-600, usually 400-500); step UNSOURCED"},
    {"id": "rearOilCst", "label": "Rear shock oil", "group": "damping", "unit": "cSt", "kind": "number", "min": 300, "max": 600, "step": 50, "bd12": null, "generic": null, "src": ["touring-car-suspension-tuning#shock-oil-viscosity"], "range": "as front"},
    {"id": "frontShockPos", "label": "Front shock top hole (1 laid down ... 5 upright)", "group": "damping", "unit": "hole", "kind": "number", "min": 1, "max": 5, "step": 1, "bd12": null, "generic": null, "src": ["yokomo-bd12#design-changes-versus-the-bd11", "touring-car-suspension-tuning#shock-mounting-angle"], "range": "BD12 has 5 front mounting steps (snapshot); which index is the kit default is UNSOURCED", "explainer": "shockAngle"},
    {"id": "rearShockPos", "label": "Rear shock position (1 laid down ... 3 upright)", "group": "damping", "unit": "pos", "kind": "number", "min": 1, "max": 3, "step": 1, "bd12": null, "generic": null, "src": ["yokomo-bd12#design-changes-versus-the-bd11", "touring-car-suspension-tuning#shock-mounting-angle"], "range": "UNSOURCED: BD12 rear angle is set with spacers; 3 positions is a modelling choice", "explainer": "shockAngle"},
    {"id": "frontShockTopSpacerMm", "label": "Front shock top spacer", "group": "damping", "unit": "mm", "kind": "number", "min": 2, "max": 6, "step": 1, "bd12": null, "generic": 4.0, "src": ["touring-car-suspension-tuning#shock-shimming"], "range": "UNSOURCED (baseline 4.0 only)"},
    {"id": "frontCamberLinkInnerShimMm", "label": "Front camber-link inner shim", "group": "damping", "unit": "mm", "kind": "number", "min": 0, "max": 3.0, "step": 0.5, "bd12": null, "generic": null, "src": ["touring-car-suspension-tuning#camber-link-length-and-ball-stud-height-are-the-", "touring-car-suspension-tuning#roll-center"], "range": "UNSOURCED", "explainer": "rollCentre"},
    {"id": "rearCamberLinkInnerShimMm", "label": "Rear camber-link inner shim", "group": "damping", "unit": "mm", "kind": "number", "min": 0, "max": 3.0, "step": 0.5, "bd12": null, "generic": null, "src": ["touring-car-suspension-tuning#camber-link-length-and-ball-stud-height-are-the-", "touring-car-suspension-tuning#roll-center"], "range": "UNSOURCED", "explainer": "rollCentre"},
    {"id": "rearDiffOilCst", "label": "Rear gear-diff oil", "group": "drivetrain", "unit": "cSt", "kind": "number", "min": 3000, "max": 10000, "step": 1000, "bd12": null, "generic": null, "src": ["touring-car-drivetrain-tuning#differentials"], "range": "snapshot (3,000-10,000); step UNSOURCED; 3,000 is a spec-class baseline, not Modified"},
    {"id": "spurT", "label": "Spur", "group": "drivetrain", "unit": "T", "kind": "number", "min": 60, "max": 120, "step": 1, "bd12": 90, "generic": null, "src": ["yokomo-bd12#design-changes-versus-the-bd11"], "range": "UNSOURCED bounds"},
    {"id": "pinionT", "label": "Pinion", "group": "drivetrain", "unit": "T", "kind": "number", "min": 15, "max": 60, "step": 1, "bd12": null, "generic": null, "src": ["touring-car-drivetrain-tuning#gearing"], "range": "UNSOURCED bounds"},
    {"id": "fdr", "label": "Final drive ratio (computed)", "group": "drivetrain", "unit": "", "kind": "computed", "formula": "spurT / pinionT * 1.9", "src": ["touring-car-drivetrain-tuning#gearing"], "range": "IGR 1.9 = 38T diff gear / 20T pulley from BD-series build notes; confirm for BD12 with the manual"},
    {"id": "beltFrontSteps", "label": "Front belt (steps tighter than centre)", "group": "drivetrain", "unit": "steps", "kind": "number", "min": 0, "max": 5, "step": 1, "bd12": null, "generic": 3, "src": ["touring-car-drivetrain-tuning#belt-tension"], "range": "UNSOURCED bounds"},
    {"id": "beltRearSteps", "label": "Rear belt (steps tighter than centre)", "group": "drivetrain", "unit": "steps", "kind": "number", "min": 0, "max": 5, "step": 1, "bd12": null, "generic": 2, "src": ["touring-car-drivetrain-tuning#belt-tension"], "range": "UNSOURCED bounds; rear must not be tighter than front"},
    {"id": "bodyForwardMm", "label": "Body shell forward offset", "group": "aero", "unit": "mm", "kind": "number", "min": 0, "max": 6, "step": 2, "bd12": null, "generic": 0, "src": ["touring-car-aerodynamics#fore-aft-body-position"], "range": "snapshot cites forward 2.0-6.0 mm; 0 reference UNSOURCED", "explainer": "body"},
    {"id": "frontLipClearanceMm", "label": "Front lip clearance", "group": "aero", "unit": "mm", "kind": "number", "min": 6, "max": 10, "step": 0.5, "bd12": null, "generic": 7.5, "src": ["touring-car-aerodynamics#front-lip-clearance", "touring-car-setup-procedure#front-body-clearance-and-up-stops"], "range": "snapshot (7-8 asphalt; 6 with stoppers; 9-10 CRC carpet only)"},
    {"id": "frontHexMm", "label": "Front wheel hex", "group": "aero", "unit": "mm", "kind": "enum", "options": [4.0, 4.3, 4.5, 5.0], "bd12": null, "generic": null, "src": ["touring-car-aerodynamics#wheelbase-and-track-width-sit-alongside-these-as", "yokomo-bd12#the-setup-sheet-pdf-s-field-structure-has-been-f"], "range": "options from snapshot"},
    {"id": "rearHexMm", "label": "Rear wheel hex", "group": "aero", "unit": "mm", "kind": "enum", "options": [4.0, 4.3, 4.5, 5.0], "bd12": null, "generic": null, "src": ["touring-car-aerodynamics#wheelbase-and-track-width-sit-alongside-these-as", "yokomo-bd12#the-setup-sheet-pdf-s-field-structure-has-been-f"], "range": "options from snapshot"},
    {"id": "tyreSet", "label": "Tyre set label", "group": "tyres", "unit": "", "kind": "text", "bd12": null, "generic": null, "src": [], "range": "free text; no compound advice (snapshot gap)"},
    {"id": "tyreRunsOnSet", "label": "Runs on this tyre set", "group": "tyres", "unit": "runs", "kind": "number", "min": 0, "max": 40, "step": 1, "bd12": null, "generic": 0, "src": ["touring-car-traction-and-tire-management#tyre-diameter-is-a-geometry-input-not-just-a-wea"], "range": "counter"}
  ]
}
```

### A.2 Symptoms -> `data/symptoms.json`

```json
[
  {"id": "entry-understeer", "label": "Pushes on turn-in", "phase": "entry", "prechecks": ["pc-body-stoppers", "pc-free-steering", "pc-droop-after-rh"], "synonyms": ["pushes on turn-in", "won't turn in", "front washes out", "lazy turn-in", "no front bite", "plows on entry"]},
  {"id": "mid-understeer", "label": "Pushes mid-corner", "phase": "mid", "prechecks": ["pc-body-stoppers", "pc-arb-free", "pc-free-steering"], "synonyms": ["pushes mid-corner", "runs wide in the sweeper", "won't hold a line", "understeers in the middle"]},
  {"id": "exit-understeer", "label": "Pushes on power", "phase": "exit", "prechecks": ["pc-arb-free", "pc-tyre-glue"], "synonyms": ["pushes on power", "runs wide on exit", "won't turn on throttle", "goes straight on the gas"]},
  {"id": "entry-oversteer", "label": "Loose on entry", "phase": "entry", "prechecks": ["pc-cross-tweak", "pc-droop-after-rh", "pc-tyre-glue"], "synonyms": ["rear steps out on the brakes", "loose on entry", "tail happy into the corner", "spins on turn-in", "rear comes around when I brake"]},
  {"id": "exit-oversteer", "label": "Loose on power", "phase": "exit", "prechecks": ["pc-belt-noise", "pc-tyre-glue", "pc-cross-tweak"], "synonyms": ["loose on power", "snaps on throttle", "no rear grip out of corners", "fishtails accelerating", "rear steps out on exit"]},
  {"id": "traction-roll", "label": "Traction rolls / digs in", "phase": "mid", "prechecks": ["pc-cross-tweak", "pc-arb-free"], "synonyms": ["traction rolls", "tips over", "flips in fast corners", "digs in", "lifts the inside wheels", "grip rolls"]},
  {"id": "bumpy-track", "label": "Unsettled over bumps", "phase": "none", "prechecks": ["pc-belt-noise", "pc-droop-after-rh"], "synonyms": ["bounces over bumps", "skips on the bumps", "unsettled on the bumpy section", "hops"]},
  {"id": "nervous-twitchy", "label": "Nervous / darty", "phase": "none", "prechecks": ["pc-free-steering", "pc-cross-tweak"], "synonyms": ["twitchy", "darty", "nervous", "edgy", "hard to keep straight", "too sensitive"]},
  {"id": "low-grip", "label": "No grip anywhere", "phase": "none", "prechecks": ["pc-track-state", "pc-battery-holder", "pc-tyre-glue"], "synonyms": ["no grip anywhere", "sliding everywhere", "dusty track", "feels like ice", "slippery all over"]},
  {"id": "fade-late-run", "label": "Fades late in the run", "phase": "none", "prechecks": ["pc-drivetrain-free", "pc-tyre-rotation"], "synonyms": ["fades at the end of the run", "loses grip after a few minutes", "slower at the end", "motor gets hot", "steering goes soft late"]},
  {"id": "left-right-difference", "label": "Different left vs right", "phase": "none", "precheckOnly": true, "prechecks": ["pc-cross-tweak", "pc-lr-balance", "pc-steering-equal", "pc-tyre-rotation"], "synonyms": ["turns better left than right", "pulls to one side", "different each direction", "one side grips more"]},
  {"id": "out-of-scope", "label": "Not something my notes cover", "phase": "none", "prechecks": [], "synonyms": []}
]
```

### A.3 Pre-checks -> `data/prechecks.json`

```json
[
  {"id": "pc-cross-tweak", "label": "Cross-tweak", "detail": "Lift from the centre holes: all four tyres should leave the board together. Needing more than 1.0 mm preload difference means a real fault, not a tweak.", "citations": ["touring-car-setup-procedure#cross-tweak-diagnostic-limit", "touring-car-setup-procedure#pre-race-pit-sequence"]},
  {"id": "pc-ride-height-unworn", "label": "Ride height measured right", "detail": "Measure behind the front arm and in front of the rear arm, never at the worn chassis ends.", "citations": ["touring-car-setup-procedure#ride-height-baseline", "touring-car-setup-procedure#other-race-day-critical-checks"]},
  {"id": "pc-belt-noise", "label": "Belts quiet, rear not tighter", "detail": "No clack or skip under hard throttle or braking; the rear belt must not be tighter than the front (rear overdrive makes it loose on power).", "citations": ["touring-car-drivetrain-tuning#belt-tension", "touring-car-drivetrain-tuning#belt-failure-signature"]},
  {"id": "pc-tyre-glue", "label": "Tyres glued", "detail": "Check the beads; re-glue every 3-4 runs.", "citations": ["touring-car-traction-and-tire-management#tire-preparation"]},
  {"id": "pc-free-steering", "label": "Steering free at full lock", "detail": "At full lock the linkage moves by hand and the servo does not buzz (EPA not binding).", "citations": ["touring-car-setup-procedure#five-common-setup-errors-named-against-the-xray-", "touring-car-radio-and-servo-setup#steering-epa"]},
  {"id": "pc-battery-holder", "label": "Battery holder not over-tight", "detail": "The pack should float slightly; a clamped pack locks out chassis flex.", "citations": ["touring-car-setup-procedure#five-common-setup-errors-named-against-the-xray-", "touring-car-suspension-tuning#chassis-flex"]},
  {"id": "pc-arb-free", "label": "Anti-roll bars free", "detail": "Bars sit flat and move freely with slight play; over-tight collars bind them.", "citations": ["touring-car-suspension-tuning#anti-roll-bars-arb", "yokomo-bd12#assembly-maintenance-notes-from-the-designer"]},
  {"id": "pc-body-stoppers", "label": "Body lip and stoppers", "detail": "Front lip 7-8 mm on asphalt; stoppers touch only at the end of travel, not holding the body up.", "citations": ["touring-car-aerodynamics#front-lip-clearance", "touring-car-aerodynamics#the-named-failure-mode"]},
  {"id": "pc-drivetrain-free", "label": "Drivetrain spins free", "detail": "With the pinion out of mesh the drivetrain spins freely; spur mesh has a little backlash.", "citations": ["touring-car-drivetrain-tuning#pre-run-mechanical-checks"]},
  {"id": "pc-tyre-rotation", "label": "Tyres rotated", "detail": "Swap left/right after every pack so wear stays even.", "citations": ["touring-car-traction-and-tire-management#rotation-cadence-is-per-pack-not-per-session"]},
  {"id": "pc-lr-balance", "label": "Left/right weight", "detail": "Aim for 50/50; 51/49 is acceptable. On the BD12 the electronics sit left and the battery right.", "citations": ["touring-car-weight-balance#left-right-target", "touring-car-weight-balance#on-the-owner-s-bd12-the-layout-starts-asymmetric"]},
  {"id": "pc-steering-equal", "label": "Steering equal both ways", "detail": "Turnbuckles equal length; the physical throw matches left and right (EPA numbers may differ).", "citations": ["touring-car-radio-and-servo-setup#the-90-degree-horn-rule", "touring-car-radio-and-servo-setup#steering-epa"]},
  {"id": "pc-droop-after-rh", "label": "Droop re-set after ride height", "detail": "Ride height (and tyre wear) changes droop; re-set the downstops after any ride-height change.", "citations": ["touring-car-setup-procedure#the-load-bearing-dependency", "touring-car-traction-and-tire-management#tyre-diameter-is-a-geometry-input-not-just-a-wea"]},
  {"id": "pc-track-state", "label": "Track state", "detail": "Cold, dusty morning track? Grip usually climbs through the day; compare runs with that in mind.", "citations": ["touring-car-traction-and-tire-management#what-kills-traction", "vehicle-dynamics-fundamentals#track-grip-changes-across-a-race-day"]}
]
```

### A.4 Lever rows -> `data/levers.json`

Fields: `phases` (where the symptom shows), optional `grip` filter, `kind` numeric or qualitative, `param`/`direction`/`step`/`min`/`max`/`unit` for numeric rows, `effect`, `tradeOff`, `verify`, `citations`, `priority` (1 = try first), `basis` (stated, inverse of a stated direction, or inferred), `notes`, `status`.

```json
[
  {"id": "eu-caster-down", "symptomId": "entry-understeer", "phases": ["entry"], "kind": "numeric", "param": "casterDeg", "direction": "decrease", "step": 1, "min": 2, "max": 6, "unit": "deg", "action": "Reduce caster", "effect": "Sharper off-power turn-in bite; useful for tight hairpins.", "tradeOff": "More twitchy on the straight and more on-power push at exit.", "verify": "3-5 laps; judge turn-in on the same two corners.", "citations": ["touring-car-steering-geometry#caster"], "priority": 1, "basis": "stated", "status": "reviewed"},
  {"id": "eu-rear-droop-more", "symptomId": "entry-understeer", "phases": ["entry", "mid"], "kind": "numeric", "param": "droopRearGaugeMm", "direction": "decrease", "step": 0.2, "min": 3.8, "max": 5.4, "unit": "mm", "action": "More rear droop (lower rear gauge reading)", "effect": "The chassis pitches forward under braking: more entry and mid-corner steering.", "tradeOff": "The rear gets looser on entry.", "verify": "3-5 laps; judge turn-in and mid-corner on the same corners.", "citations": ["touring-car-setup-procedure#droop-baselines", "vehicle-dynamics-fundamentals#droop"], "priority": 2, "basis": "stated", "notes": "step 0.2 UNSOURCED", "status": "reviewed"},
  {"id": "eu-front-arb-thicker", "symptomId": "entry-understeer", "phases": ["entry"], "kind": "numeric", "param": "frontArbMm", "direction": "increase", "step": 0.1, "min": 1.0, "max": 1.6, "unit": "mm", "action": "Thicker front anti-roll bar", "effect": "Sharper turn-in and high-speed steering.", "tradeOff": "Adds edginess.", "verify": "3-5 laps; judge turn-in and fast direction changes.", "citations": ["touring-car-suspension-tuning#anti-roll-bars-arb"], "priority": 3, "basis": "stated", "notes": "step 0.1 UNSOURCED (bar sizes are discrete)", "status": "reviewed"},
  {"id": "eu-body-forward", "symptomId": "entry-understeer", "phases": ["entry"], "kind": "numeric", "param": "bodyForwardMm", "direction": "increase", "step": 2, "min": 0, "max": 6, "unit": "mm", "action": "Move the body shell forward", "effect": "More front downforce: sharper turn-in and steering response.", "tradeOff": "Less rear stability in fast sweepers.", "verify": "3-5 laps; judge turn-in, and watch the fast sweeper for a looser rear.", "citations": ["touring-car-aerodynamics#fore-aft-body-position", "touring-car-setup-procedure#grip-levers-outside-the-fixed-sequence"], "priority": 4, "basis": "stated", "status": "draft"},
  {"id": "eu-weight-rearward", "symptomId": "entry-understeer", "phases": ["entry"], "grip": ["low", "medium"], "kind": "numeric", "param": "weightFrontPct", "direction": "decrease", "step": 1, "min": 48, "max": 52, "unit": "%", "action": "Shift weight about 1% rearward", "effect": "More weight pitches forward under braking: sharper off-power turn-in and apex rotation.", "tradeOff": "48/52 is aggressive and hard to drive over a full run.", "verify": "Re-weigh race-ready, then 3-5 laps judging turn-in.", "citations": ["touring-car-weight-balance#front-rear-target", "touring-car-weight-balance#why-it-matters"], "priority": 5, "basis": "stated", "status": "draft"},
  {"id": "eu-ackermann-less", "symptomId": "entry-understeer", "phases": ["entry"], "grip": ["low", "medium"], "kind": "numeric", "param": "ackermannShimMm", "direction": "increase", "step": 0.5, "min": 0, "max": 1.0, "unit": "mm", "action": "Add Ackermann shim at the rack (less Ackermann)", "effect": "Front wheels closer to parallel: sharper turn-in.", "tradeOff": "Twitchier, and more traction-rolling risk on high grip.", "verify": "3-5 laps; judge turn-in at the tightest corner.", "citations": ["touring-car-steering-geometry#ackermann-effect"], "priority": 6, "basis": "stated", "status": "draft"},
  {"id": "mu-front-shocks-down", "symptomId": "mid-understeer", "phases": ["mid"], "kind": "numeric", "param": "frontShockPos", "direction": "decrease", "step": 1, "min": 1, "max": 5, "unit": "hole", "action": "Lay the front shocks down one hole", "effect": "Softer initial stroke and more mid-corner side-bite.", "tradeOff": "Slower initial response.", "verify": "3-5 laps; judge the line through the same sweeper.", "citations": ["touring-car-suspension-tuning#shock-mounting-angle", "touring-car-setup-procedure#grip-levers-outside-the-fixed-sequence"], "priority": 1, "basis": "inferred", "notes": "Snapshot gives the effect of laying shocks down without naming the axle; applying it at the FRONT for front side-bite is our inference. Author confirm.", "status": "draft"},
  {"id": "mu-front-springs-softer", "symptomId": "mid-understeer", "phases": ["mid"], "kind": "numeric", "param": "frontSpringRate", "direction": "decrease", "step": 0.1, "min": 2.0, "max": 3.2, "unit": "rate", "action": "One step softer front springs", "effect": "More roll and side-bite in sweepers.", "tradeOff": "Less initial bite.", "verify": "3-5 laps; judge the sweeper.", "citations": ["touring-car-suspension-tuning#springs", "vehicle-dynamics-fundamentals#springs-set-how-much-weight-transfer-happens-dam"], "priority": 2, "basis": "stated", "notes": "front-specific application inferred; step UNSOURCED", "status": "draft"},
  {"id": "mu-shorter-camber-link", "symptomId": "mid-understeer", "phases": ["mid"], "kind": "qualitative", "action": "Shorter front upper camber link", "effect": "More camber gain keeps the contact patch flatter in roll: more lateral side bite.", "tradeOff": "Edgier than a longer link.", "verify": "3-5 laps; judge the sweeper.", "citations": ["touring-car-suspension-tuning#camber-link-length-and-ball-stud-height-are-the-", "touring-car-traction-and-tire-management#increasing-overall-traction"], "priority": 3, "basis": "stated", "status": "draft"},
  {"id": "mu-bump-steer-more", "symptomId": "mid-understeer", "phases": ["mid"], "grip": ["low", "medium"], "kind": "numeric", "param": "bumpSteerShimMm", "direction": "increase", "step": 0.5, "min": 0, "max": 2.0, "unit": "mm", "action": "Add bump-steer shim at the outer steering block", "effect": "More toe-in under compression: more mid-corner-to-exit steering.", "tradeOff": "More aggressive, nervous front end.", "verify": "3-5 laps; judge mid-corner to exit.", "citations": ["touring-car-steering-geometry#bump-steer"], "priority": 4, "basis": "stated", "status": "draft"},
  {"id": "xu-caster-up", "symptomId": "exit-understeer", "phases": ["exit"], "kind": "numeric", "param": "casterDeg", "direction": "increase", "step": 1, "min": 2, "max": 6, "unit": "deg", "action": "Add caster", "effect": "More on-power mid-corner and exit steering, and better straight-line stability.", "tradeOff": "Less sharp off-power entry.", "verify": "3-5 laps; judge power-on exit from the same slow corners.", "citations": ["touring-car-steering-geometry#caster"], "priority": 1, "basis": "stated", "status": "draft"},
  {"id": "xu-bump-steer-more", "symptomId": "exit-understeer", "phases": ["exit"], "grip": ["low", "medium"], "kind": "numeric", "param": "bumpSteerShimMm", "direction": "increase", "step": 0.5, "min": 0, "max": 2.0, "unit": "mm", "action": "Add bump-steer shim at the outer steering block", "effect": "More toe-in under compression: more mid-corner-to-exit steering.", "tradeOff": "More aggressive, nervous front end.", "verify": "3-5 laps; judge power-on exit.", "citations": ["touring-car-steering-geometry#bump-steer"], "priority": 2, "basis": "stated", "status": "draft"},
  {"id": "xu-wing-forward", "symptomId": "exit-understeer", "phases": ["exit"], "kind": "qualitative", "action": "Move the wing forward, or run it lower and flatter", "effect": "Less rear downforce, more corner-exit steering.", "tradeOff": "Less high-speed rear traction.", "verify": "3-5 laps; judge exits and the fastest corner.", "citations": ["touring-car-aerodynamics#wing-angle-and-position"], "priority": 3, "basis": "stated", "status": "draft"},
  {"id": "xu-diff-thinner", "symptomId": "exit-understeer", "phases": ["exit"], "grip": ["medium", "high"], "kind": "numeric", "param": "rearDiffOilCst", "direction": "decrease", "step": 1000, "min": 3000, "max": 10000, "unit": "cSt", "action": "Thinner rear diff oil", "effect": "Frees the rear axle, removing the push a too-stiff diff causes.", "tradeOff": "Can get loose, especially on low grip.", "verify": "3-5 laps; judge power-on exit.", "citations": ["touring-car-drivetrain-tuning#differentials"], "priority": 4, "basis": "inverse", "notes": "Snapshot: thicker oil risks understeer if too stiff; thinner frees the rear. Step UNSOURCED. See CONFLICT note on diff oil.", "status": "draft"},
  {"id": "eo-rear-droop-less", "symptomId": "entry-oversteer", "phases": ["entry"], "kind": "numeric", "param": "droopRearGaugeMm", "direction": "increase", "step": 0.2, "min": 3.8, "max": 5.4, "unit": "mm", "action": "Less rear droop (higher rear gauge reading)", "effect": "Less forward pitch under braking: a calmer rear on entry.", "tradeOff": "Less entry steering.", "verify": "3-5 laps; judge braking into the same two corners.", "citations": ["touring-car-setup-procedure#droop-baselines"], "priority": 1, "basis": "inverse", "notes": "Inverse of 'more rear droop = looser rear on entry'. Step UNSOURCED.", "status": "draft"},
  {"id": "eo-rear-arb-thicker", "symptomId": "entry-oversteer", "phases": ["entry"], "kind": "numeric", "param": "rearArbMm", "direction": "increase", "step": 0.1, "min": 1.0, "max": 1.6, "unit": "mm", "action": "Thicker rear anti-roll bar", "effect": "Less off-power rotation.", "tradeOff": "Less on-power rear traction.", "verify": "3-5 laps; judge entry, then check exits did not get loose.", "citations": ["touring-car-suspension-tuning#anti-roll-bars-arb"], "priority": 2, "basis": "stated", "status": "draft"},
  {"id": "eo-caster-up", "symptomId": "entry-oversteer", "phases": ["entry"], "kind": "numeric", "param": "casterDeg", "direction": "increase", "step": 1, "min": 2, "max": 6, "unit": "deg", "action": "Add caster", "effect": "Smoother entry and better stability.", "tradeOff": "Less sharp off-power entry.", "verify": "3-5 laps; judge entry.", "citations": ["touring-car-steering-geometry#caster"], "priority": 3, "basis": "stated", "status": "draft"},
  {"id": "eo-weight-forward", "symptomId": "entry-oversteer", "phases": ["entry"], "kind": "numeric", "param": "weightFrontPct", "direction": "increase", "step": 1, "min": 48, "max": 52, "unit": "%", "action": "Shift weight about 1% forward", "effect": "Less forward pitch under braking: calmer corner entry.", "tradeOff": "Less apex rotation.", "verify": "Re-weigh race-ready, then 3-5 laps judging entry.", "citations": ["touring-car-weight-balance#why-it-matters", "touring-car-weight-balance#front-rear-target"], "priority": 4, "basis": "stated", "status": "draft"},
  {"id": "eo-body-back", "symptomId": "entry-oversteer", "phases": ["entry"], "kind": "numeric", "param": "bodyForwardMm", "direction": "decrease", "step": 2, "min": 0, "max": 6, "unit": "mm", "action": "Move the body shell back", "effect": "More rear downforce and stability.", "tradeOff": "Less front downforce and turn-in.", "verify": "3-5 laps; judge entry and the fastest corner.", "citations": ["touring-car-aerodynamics#fore-aft-body-position", "touring-car-setup-procedure#grip-levers-outside-the-fixed-sequence"], "priority": 5, "basis": "stated", "status": "draft"},
  {"id": "xo-rear-toe-in-more", "symptomId": "exit-oversteer", "phases": ["exit"], "kind": "numeric", "param": "rearToeInDeg", "direction": "increase", "step": 0.5, "min": 2.0, "max": 3.5, "unit": "deg", "action": "More rear toe-in", "effect": "More rear traction on power.", "tradeOff": "Toe trades corner-entry response against straight-line stability.", "verify": "3-5 laps; judge power-on exit from the same slow corners.", "citations": ["touring-car-traction-and-tire-management#increasing-rear-specific-traction", "touring-car-setup-procedure#camber-and-toe-baselines", "vehicle-dynamics-fundamentals#camber-caster-and-toe-are-compromises-not-settin"], "priority": 1, "basis": "stated", "notes": "BD12 factory 3.5 is already the top of the snapshot range, so the engine skips this on a stock BD12 and says why.", "status": "reviewed"},
  {"id": "xo-rear-diff-softer", "symptomId": "exit-oversteer", "phases": ["exit"], "grip": ["low"], "kind": "numeric", "param": "rearDiffOilCst", "direction": "decrease", "step": 1000, "min": 3000, "max": 10000, "unit": "cSt", "action": "Softer rear diff oil (toward 3,000-4,000 cSt)", "effect": "Lets the rear wheels turn independently: more side grip, and you can get on the power earlier without the rear sliding on a low-grip or dusty track.", "tradeOff": "The notes warn thinner oil can feel looser into the corner; very thin oil can feel edgy at the apex on high grip (lower confidence, from the notebook's own summary).", "verify": "3-5 laps; judge power-on exits on the same corners, then check turn-in did not get looser.", "followUp": "Check rear toe-in first: the episodes pair thinner oil with 3.0-3.5 deg rear toe-in.", "citations": ["rear-diff-oil-and-low-grip-exit-traction#loose-on-power-on-low-grip-go-softer-on-the-rear", "rear-diff-oil-and-low-grip-exit-traction#pair-thinner-oil-with-enough-rear-toe-in", "touring-car-drivetrain-tuning#differentials", "touring-car-traction-and-tire-management#increasing-rear-specific-traction"], "priority": 2, "basis": "stated", "notes": "Needs the diff opened and rebuilt, so it is not a quick pit-table change. Source: ToniSport 'Gear Diff Talk' and 'More Overall Traction' via the author's NotebookLM notebook (kb/additions). Author decision 2026-10-04: use as a low-grip lever (option B).", "status": "reviewed"},
  {"id": "xo-rear-shocks-up", "symptomId": "exit-oversteer", "phases": ["exit"], "kind": "numeric", "param": "rearShockPos", "direction": "increase", "step": 1, "min": 1, "max": 3, "unit": "pos", "action": "Stand the rear shocks up one position", "effect": "Stiffer initial stroke and faster weight transfer: more corner-exit rear traction.", "tradeOff": "Less progressive; more roll stiffness.", "verify": "3-5 laps; judge power-on exit.", "citations": ["touring-car-suspension-tuning#shock-mounting-angle", "touring-car-traction-and-tire-management#increasing-rear-specific-traction"], "priority": 3, "basis": "stated", "status": "reviewed"},
  {"id": "xo-rear-arb-thinner", "symptomId": "exit-oversteer", "phases": ["exit"], "kind": "numeric", "param": "rearArbMm", "direction": "decrease", "step": 0.1, "min": 1.0, "max": 1.6, "unit": "mm", "action": "Thinner rear anti-roll bar", "effect": "More on-power rear traction.", "tradeOff": "More off-power rotation.", "verify": "3-5 laps; judge exits, then check entry did not get loose.", "citations": ["touring-car-suspension-tuning#anti-roll-bars-arb", "touring-car-traction-and-tire-management#increasing-rear-specific-traction"], "priority": 4, "basis": "stated", "status": "draft"},
  {"id": "xo-front-droop-more", "symptomId": "exit-oversteer", "phases": ["exit"], "kind": "numeric", "param": "droopFrontGaugeMm", "direction": "decrease", "step": 0.2, "min": 4.8, "max": 6.4, "unit": "mm", "action": "More front droop (lower front gauge reading)", "effect": "The nose lifts on power and load shifts rearward: more exit traction.", "tradeOff": "Less turn-in sharpness.", "verify": "3-5 laps; judge exits and turn-in.", "citations": ["touring-car-setup-procedure#droop-baselines", "touring-car-traction-and-tire-management#increasing-rear-specific-traction"], "priority": 5, "basis": "stated", "notes": "step UNSOURCED", "status": "draft"},
  {"id": "xo-weight-rearward", "symptomId": "exit-oversteer", "phases": ["exit"], "kind": "numeric", "param": "weightFrontPct", "direction": "decrease", "step": 1, "min": 48, "max": 52, "unit": "%", "action": "Shift weight about 1% rearward", "effect": "More rear traction.", "tradeOff": "48/52 is aggressive and hard to drive over a full run.", "verify": "Re-weigh race-ready, then 3-5 laps judging exits.", "citations": ["touring-car-traction-and-tire-management#increasing-rear-specific-traction", "touring-car-weight-balance#front-rear-target"], "priority": 6, "basis": "stated", "status": "draft"},
  {"id": "xo-rear-track-narrower", "symptomId": "exit-oversteer", "phases": ["exit"], "grip": ["low"], "kind": "numeric", "param": "rearHexMm", "direction": "decrease", "step": 1, "unit": "mm", "action": "Narrower rear track (thinner rear hexes, 4.3 or 4.5 mm)", "effect": "More rear traction and side bite on low grip.", "tradeOff": "A wider rear gives less roll and more corner speed on high grip.", "verify": "3-5 laps; judge exits.", "citations": ["touring-car-aerodynamics#wheelbase-and-track-width-sit-alongside-these-as", "touring-car-setup-procedure#grip-levers-outside-the-fixed-sequence"], "priority": 7, "basis": "stated", "notes": "enum param: step 1 = next option down", "status": "draft"},
  {"id": "xo-body-back", "symptomId": "exit-oversteer", "phases": ["exit"], "kind": "numeric", "param": "bodyForwardMm", "direction": "decrease", "step": 2, "min": 0, "max": 6, "unit": "mm", "action": "Move the body shell back", "effect": "More rear downforce and stability.", "tradeOff": "Less turn-in.", "verify": "3-5 laps; judge exits and the fastest corner.", "citations": ["touring-car-traction-and-tire-management#increasing-rear-specific-traction", "touring-car-aerodynamics#fore-aft-body-position"], "priority": 8, "basis": "stated", "status": "draft"},
  {"id": "tr-front-camber-less", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "frontCamberDeg", "direction": "decrease", "step": 0.5, "min": 1.0, "max": 2.5, "unit": "deg neg", "action": "Less front negative camber (toward 1.0 deg)", "effect": "The outer front tyre loses flat contact deep in fast corners, so it slides instead of digging in.", "tradeOff": "Less front grip.", "verify": "3-5 laps; watch the fastest corner for lifting or tripping.", "citations": ["touring-car-traction-and-tire-management#traction-rolling"], "priority": 1, "basis": "stated", "status": "reviewed"},
  {"id": "tr-front-toe-out-more", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "frontToeOutDeg", "direction": "increase", "step": 0.5, "min": 0, "max": 1.5, "unit": "deg", "action": "More front toe-out (toward 1.5 deg per side)", "effect": "Reduces traction-rolling tendency.", "tradeOff": "Not stated in the notes.", "verify": "3-5 laps; watch the fastest corner.", "citations": ["touring-car-traction-and-tire-management#traction-rolling"], "priority": 2, "basis": "stated", "status": "reviewed"},
  {"id": "tr-weight-forward", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "weightFrontPct", "direction": "increase", "step": 1, "min": 48, "max": 52, "unit": "%", "action": "Shift weight forward (toward 51/49)", "effect": "Calmer turn-in and less traction rolling on high grip.", "tradeOff": "Less apex rotation.", "verify": "Re-weigh race-ready, then 3-5 laps.", "citations": ["touring-car-traction-and-tire-management#traction-rolling", "touring-car-weight-balance#front-rear-target"], "priority": 3, "basis": "stated", "status": "reviewed"},
  {"id": "tr-front-shocks-down", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "frontShockPos", "direction": "decrease", "step": 1, "min": 1, "max": 5, "unit": "hole", "action": "Lay the front shocks down one hole", "effect": "Softer initial stroke; lower traction-rolling risk.", "tradeOff": "Slower initial response.", "verify": "3-5 laps; watch the fastest corner.", "citations": ["touring-car-traction-and-tire-management#traction-rolling", "touring-car-suspension-tuning#shock-mounting-angle"], "priority": 4, "basis": "stated", "notes": "Snapshot says 'shocks laid down' without an axle; front first is our choice.", "status": "draft"},
  {"id": "tr-front-droop-less", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "droopFrontGaugeMm", "direction": "increase", "step": 0.2, "min": 4.8, "max": 6.4, "unit": "mm", "action": "Less front droop (higher front gauge reading)", "effect": "Restricts chassis pitch and roll.", "tradeOff": "Less weight transfer, less rear traction on exit.", "verify": "3-5 laps; watch the fastest corner.", "citations": ["touring-car-traction-and-tire-management#traction-rolling", "touring-car-setup-procedure#droop-baselines"], "priority": 5, "basis": "stated", "status": "draft"},
  {"id": "tr-rear-droop-less", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "droopRearGaugeMm", "direction": "increase", "step": 0.2, "min": 3.8, "max": 5.4, "unit": "mm", "action": "Less rear droop (higher rear gauge reading)", "effect": "Restricts chassis pitch and roll.", "tradeOff": "Less entry steering.", "verify": "3-5 laps; watch the fastest corner.", "citations": ["touring-car-traction-and-tire-management#traction-rolling", "touring-car-setup-procedure#droop-baselines"], "priority": 6, "basis": "stated", "status": "draft"},
  {"id": "tr-roll-centre-lower", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "frontCamberLinkInnerShimMm", "direction": "increase", "step": 0.5, "min": 0, "max": 3.0, "unit": "mm", "action": "Lower the front roll centre (add shim under the inner camber-link ball stud)", "effect": "Smoother roll; traction builds later; less traction-rolling risk on high grip.", "tradeOff": "Softer turn-in.", "verify": "3-5 laps; watch the fastest corner and turn-in.", "citations": ["touring-car-suspension-tuning#roll-center", "touring-car-suspension-tuning#camber-link-length-and-ball-stud-height-are-the-", "touring-car-traction-and-tire-management#traction-rolling"], "priority": 7, "basis": "stated", "status": "draft"},
  {"id": "tr-ackermann-shim-less", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "ackermannShimMm", "direction": "decrease", "step": 0.5, "min": 0, "max": 1.0, "unit": "mm", "action": "Remove Ackermann shim", "effect": "Smoother, more forgiving turn-in; less traction rolling.", "tradeOff": "Less sharp turn-in.", "verify": "3-5 laps.", "citations": ["touring-car-traction-and-tire-management#traction-rolling", "touring-car-steering-geometry#ackermann-effect", "touring-car-steering-geometry#these-three-interact-with-each-other-and-with-we"], "priority": 8, "basis": "stated", "status": "draft"},
  {"id": "tr-bump-steer-less", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "bumpSteerShimMm", "direction": "decrease", "step": 0.5, "min": 0, "max": 2.0, "unit": "mm", "action": "Remove bump-steer shim", "effect": "Flatter toe under compression; less traction rolling.", "tradeOff": "Less mid-corner-to-exit steering.", "verify": "3-5 laps.", "citations": ["touring-car-traction-and-tire-management#traction-rolling", "touring-car-steering-geometry#bump-steer"], "priority": 9, "basis": "stated", "status": "draft"},
  {"id": "tr-springs-softer", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "numeric", "param": "frontSpringRate", "direction": "decrease", "step": 0.1, "min": 2.0, "max": 3.2, "unit": "rate", "action": "One step softer springs", "effect": "Listed as a traction-rolling countermeasure.", "tradeOff": "More roll.", "verify": "3-5 laps.", "citations": ["touring-car-traction-and-tire-management#traction-rolling"], "priority": 10, "basis": "stated", "notes": "axle not specified; front chosen", "status": "draft"},
  {"id": "tr-ca-sidewall", "symptomId": "traction-roll", "phases": ["mid", "none"], "grip": ["high"], "kind": "qualitative", "action": "Thin CA glue on the front tyres' outer sidewall", "effect": "The outer edge stops digging in.", "tradeOff": "Not stated in the notes.", "verify": "3-5 laps; watch the fastest corner.", "citations": ["touring-car-traction-and-tire-management#traction-rolling"], "priority": 11, "basis": "stated", "status": "draft"},
  {"id": "bt-ride-height-front-up", "symptomId": "bumpy-track", "phases": ["none"], "kind": "numeric", "param": "rideHeightFrontMm", "direction": "increase", "step": 0.2, "min": 5.0, "max": 5.8, "unit": "mm", "action": "Raise front ride height one step (bumpy asphalt runs 5.4-5.8 mm)", "effect": "More clearance over bumps.", "tradeOff": "Higher centre of gravity; droop changes with ride height.", "followUp": "Re-set the droop screws afterwards.", "verify": "3-5 laps through the bumpy section.", "citations": ["touring-car-setup-procedure#ride-height-baseline", "touring-car-setup-procedure#the-load-bearing-dependency"], "priority": 1, "basis": "stated", "status": "reviewed"},
  {"id": "bt-ride-height-rear-up", "symptomId": "bumpy-track", "phases": ["none"], "kind": "numeric", "param": "rideHeightRearMm", "direction": "increase", "step": 0.2, "min": 5.0, "max": 5.8, "unit": "mm", "action": "Raise rear ride height one step (keep the rear about 0.2 mm above the front)", "effect": "More clearance over bumps.", "tradeOff": "Higher centre of gravity; droop changes with ride height.", "followUp": "Re-set the droop screws afterwards.", "verify": "3-5 laps through the bumpy section.", "citations": ["touring-car-setup-procedure#ride-height-baseline", "touring-car-setup-procedure#the-load-bearing-dependency"], "priority": 2, "basis": "stated", "status": "reviewed"},
  {"id": "bt-caster-up", "symptomId": "bumpy-track", "phases": ["none"], "kind": "numeric", "param": "casterDeg", "direction": "increase", "step": 1, "min": 2, "max": 6, "unit": "deg", "action": "Add caster", "effect": "Better bump absorption on outdoor asphalt and more straight-line stability.", "tradeOff": "Less sharp off-power entry.", "verify": "3-5 laps through the bumpy section.", "citations": ["touring-car-steering-geometry#caster"], "priority": 3, "basis": "stated", "status": "reviewed"},
  {"id": "bt-springs-softer", "symptomId": "bumpy-track", "phases": ["none"], "kind": "numeric", "param": "frontSpringRate", "direction": "decrease", "step": 0.1, "min": 2.0, "max": 3.2, "unit": "rate", "action": "One step softer springs", "effect": "Hard springs bounce on bumps; softer ones settle.", "tradeOff": "Less initial bite.", "verify": "3-5 laps through the bumpy section.", "citations": ["touring-car-suspension-tuning#springs"], "priority": 4, "basis": "inverse", "status": "draft"},
  {"id": "bt-belts-tighter", "symptomId": "bumpy-track", "phases": ["none"], "kind": "qualitative", "action": "Belts one step tighter, front and rear", "effect": "Stops belts skipping on bumpy asphalt.", "tradeOff": "More drivetrain friction.", "verify": "Listen for clack or skip on the next run.", "citations": ["touring-car-drivetrain-tuning#belt-tension", "touring-car-drivetrain-tuning#belt-failure-signature"], "priority": 5, "basis": "stated", "status": "draft"},
  {"id": "nt-front-arb-thinner", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "numeric", "param": "frontArbMm", "direction": "decrease", "step": 0.1, "min": 1.0, "max": 1.6, "unit": "mm", "action": "Thinner front anti-roll bar", "effect": "Takes edginess out of the front.", "tradeOff": "Less sharp turn-in and high-speed steering.", "verify": "3-5 laps; judge the straight and fast direction changes.", "citations": ["touring-car-suspension-tuning#anti-roll-bars-arb"], "priority": 1, "basis": "inverse", "status": "draft"},
  {"id": "nt-caster-up", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "numeric", "param": "casterDeg", "direction": "increase", "step": 1, "min": 2, "max": 6, "unit": "deg", "action": "Add caster", "effect": "Better straight-line stability, smoother entry.", "tradeOff": "Less sharp off-power entry.", "verify": "3-5 laps; judge the straight.", "citations": ["touring-car-steering-geometry#caster"], "priority": 2, "basis": "stated", "status": "draft"},
  {"id": "nt-ackermann-more", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "numeric", "param": "ackermannShimMm", "direction": "decrease", "step": 0.5, "min": 0, "max": 1.0, "unit": "mm", "action": "Remove Ackermann shim (more Ackermann)", "effect": "Smoother, more forgiving turn-in.", "tradeOff": "Less sharp turn-in.", "verify": "3-5 laps; judge turn-in.", "citations": ["touring-car-steering-geometry#ackermann-effect"], "priority": 3, "basis": "stated", "status": "draft"},
  {"id": "nt-bump-steer-less", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "numeric", "param": "bumpSteerShimMm", "direction": "decrease", "step": 0.5, "min": 0, "max": 2.0, "unit": "mm", "action": "Remove bump-steer shim", "effect": "Flatter toe under compression: smoother turn-in.", "tradeOff": "Less mid-corner-to-exit steering.", "verify": "3-5 laps.", "citations": ["touring-car-steering-geometry#bump-steer"], "priority": 4, "basis": "stated", "status": "draft"},
  {"id": "nt-front-track-wider", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "numeric", "param": "frontHexMm", "direction": "increase", "step": 1, "unit": "mm", "action": "Wider front track (thicker front hexes, 4.5 or 5.0 mm)", "effect": "Calms a darty front end.", "tradeOff": "Not stated in the notes.", "verify": "3-5 laps; judge the straight.", "citations": ["touring-car-aerodynamics#wheelbase-and-track-width-sit-alongside-these-as"], "priority": 5, "basis": "stated", "notes": "enum param: step 1 = next option up", "status": "draft"},
  {"id": "nt-expo-more", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "numeric", "param": "steeringExpoPct", "direction": "decrease", "step": 5, "min": -20, "max": 0, "unit": "%", "action": "More negative steering expo (wheel radio -5 to -10%)", "effect": "Less sensitive around neutral; smoother initial steering.", "tradeOff": "Slower initial response.", "verify": "3-5 laps; judge the straight.", "citations": ["touring-car-radio-and-servo-setup#steering-expo"], "priority": 6, "basis": "stated", "status": "draft"},
  {"id": "nt-shock-spacer-more", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "numeric", "param": "frontShockTopSpacerMm", "direction": "increase", "step": 1, "min": 2, "max": 6, "unit": "mm", "action": "Add spacer under the front shock top ball stud", "effect": "Softer damping feel and freer rotation: takes edginess out of a nose-heavy car.", "tradeOff": "Not stated in the notes.", "verify": "3-5 laps.", "citations": ["touring-car-suspension-tuning#shock-shimming"], "priority": 7, "basis": "stated", "notes": "step UNSOURCED", "status": "draft"},
  {"id": "nt-longer-camber-link", "symptomId": "nervous-twitchy", "phases": ["none"], "kind": "qualitative", "action": "Longer front upper camber link", "effect": "Smoother, more progressive, less edgy feel.", "tradeOff": "Less side bite.", "verify": "3-5 laps.", "citations": ["touring-car-suspension-tuning#camber-link-length-and-ball-stud-height-are-the-"], "priority": 8, "basis": "stated", "status": "draft"},
  {"id": "lg-chassis-flex", "symptomId": "low-grip", "phases": ["none"], "grip": ["low"], "kind": "qualitative", "action": "Add chassis flex: remove inner top-deck screws (or the front motor-mount screws)", "effect": "More mechanical grip on loose or dusty asphalt.", "tradeOff": "Less responsive if grip comes up.", "verify": "3-5 laps.", "citations": ["touring-car-suspension-tuning#chassis-flex", "touring-car-traction-and-tire-management#increasing-overall-traction"], "priority": 1, "basis": "stated", "status": "draft"},
  {"id": "lg-roll-centre-higher", "symptomId": "low-grip", "phases": ["none"], "grip": ["low"], "kind": "numeric", "param": "frontCamberLinkInnerShimMm", "direction": "decrease", "step": 0.5, "min": 0, "max": 3.0, "unit": "mm", "action": "Raise the front roll centre (remove shim under the inner camber-link ball stud)", "effect": "Immediate initial bite and less roll.", "tradeOff": "More traction-rolling risk as grip comes up.", "verify": "3-5 laps.", "citations": ["touring-car-suspension-tuning#roll-center", "touring-car-suspension-tuning#camber-link-length-and-ball-stud-height-are-the-", "touring-car-traction-and-tire-management#increasing-overall-traction"], "priority": 2, "basis": "stated", "status": "draft"},
  {"id": "lg-rear-toe-in-more", "symptomId": "low-grip", "phases": ["none"], "grip": ["low"], "kind": "numeric", "param": "rearToeInDeg", "direction": "increase", "step": 0.5, "min": 2.0, "max": 3.5, "unit": "deg", "action": "Rear toe-in toward the low-grip value (3.0-3.5 deg)", "effect": "More rear grip on low-grip asphalt.", "tradeOff": "Toe trades corner-entry response against straight-line stability.", "verify": "3-5 laps.", "citations": ["touring-car-setup-procedure#camber-and-toe-baselines", "touring-car-traction-and-tire-management#increasing-rear-specific-traction"], "priority": 3, "basis": "stated", "status": "draft"},
  {"id": "lg-springs-harder", "symptomId": "low-grip", "phases": ["none"], "grip": ["low"], "kind": "numeric", "param": "frontSpringRate", "direction": "increase", "step": 0.1, "min": 2.0, "max": 3.2, "unit": "rate", "action": "One step harder springs (pair with thinner oil)", "effect": "Sharper initial bite on low-grip or dusty surfaces.", "tradeOff": "Bounces on bumps.", "verify": "3-5 laps.", "citations": ["touring-car-suspension-tuning#springs", "touring-car-suspension-tuning#shock-oil-viscosity"], "priority": 4, "basis": "stated", "status": "draft"},
  {"id": "lg-oil-thinner", "symptomId": "low-grip", "phases": ["none"], "grip": ["low"], "kind": "numeric", "param": "frontOilCst", "direction": "decrease", "step": 50, "min": 300, "max": 600, "unit": "cSt", "action": "Thinner shock oil", "effect": "Faster roll and initial side-bite.", "tradeOff": "A less calm car.", "verify": "3-5 laps.", "citations": ["touring-car-suspension-tuning#shock-oil-viscosity", "touring-car-traction-and-tire-management#increasing-overall-traction"], "priority": 5, "basis": "stated", "notes": "step UNSOURCED", "status": "draft"},
  {"id": "lg-bump-steer-more", "symptomId": "low-grip", "phases": ["none"], "grip": ["low"], "kind": "numeric", "param": "bumpSteerShimMm", "direction": "increase", "step": 0.5, "min": 0, "max": 2.0, "unit": "mm", "action": "More bump-steer shim", "effect": "Helps generate front grip on lower-traction asphalt.", "tradeOff": "More nervous front end.", "verify": "3-5 laps.", "citations": ["touring-car-steering-geometry#bump-steer"], "priority": 6, "basis": "stated", "status": "draft"},
  {"id": "lg-additive-soak", "symptomId": "low-grip", "phases": ["none"], "grip": ["low"], "kind": "qualitative", "action": "Longer additive soak (about 20 min, with warmers)", "effect": "More tyre grip on low-grip asphalt.", "tradeOff": "Too much grip later in the day can cause traction rolling.", "verify": "Next run on the same tyres.", "citations": ["touring-car-traction-and-tire-management#tire-preparation"], "priority": 7, "basis": "stated", "status": "draft"},
  {"id": "fl-tyre-heat", "symptomId": "fade-late-run", "phases": ["none"], "kind": "qualitative", "action": "Check for tyre overheating: softer springs reduce it on hot tracks; don't run overheated tyres back-to-back", "effect": "Grip stays more consistent to the end of the run.", "tradeOff": "Softer springs mean less initial bite.", "verify": "Compare the last minute of the next run with the first.", "citations": ["touring-car-suspension-tuning#springs", "touring-car-traction-and-tire-management#tire-rotation-and-cycling"], "priority": 1, "basis": "stated", "status": "draft"},
  {"id": "fl-pinion-down", "symptomId": "fade-late-run", "phases": ["none"], "kind": "numeric", "param": "pinionT", "direction": "decrease", "step": 1, "min": 15, "max": 60, "unit": "T", "action": "If the motor runs hot: drop the pinion one tooth", "effect": "Lower motor temperature and sharper exit acceleration.", "tradeOff": "Less top speed.", "verify": "Check motor temperature after the next run.", "citations": ["touring-car-drivetrain-tuning#overheating-remedy-order", "touring-car-drivetrain-tuning#gearing"], "priority": 2, "basis": "stated", "status": "draft"},
  {"id": "fl-servo-bec", "symptomId": "fade-late-run", "phases": ["none"], "kind": "qualitative", "action": "If steering fades late: run the servo on a 6.0 V BEC", "effect": "Consistent, fade-free steering from start to finish.", "tradeOff": "Less peak servo speed than 7.4 V.", "verify": "Judge steering in the last minute of the next run.", "citations": ["touring-car-radio-and-servo-setup#servo-choice-and-bec-voltage"], "priority": 3, "basis": "stated", "status": "draft"}
]
```

### A.5 Review notes: gaps, conflicts, inferences (author decides)

**Open questions to resolve before T2 copies the data:**
1. **Rear diff oil direction for exit traction: RESOLVED 2026-10-04 (author, option B).** The snapshot contradicted itself on low grip. The author asked the NotebookLM notebook directly; the ToniSport episodes ('Gear Diff Talk', 'More Overall Traction') recommend softer rear diff oil, with 3.0-3.5 deg rear toe-in, when the car is loose or sliding on the throttle out of corners on low grip. One low-grip row (`xo-rear-diff-softer`, priority 2) was added, citing the new `kb/additions/rear-diff-oil-and-low-grip-exit-traction.md`. No thicker-oil or high-grip row: no episode quote supports one.
2. **Droop on the BD12.** Yokomo specifies droop as 1.5-2.0 mm of upward extension when lifted at 5.0 mm ride height; the droop levers use the generic gauge reading (front 5.6 / rear 4.6). **DECIDED 2026-10-04 by the author: keep the generic gauge method with a "generic" tag; no `bd12DroopExtensionMm` field.**

**Rows built on an inverse or inference (flagged in `basis`):** `eo-rear-droop-less`, `xu-diff-thinner`, `bt-springs-softer`, `nt-front-arb-thinner` (inverse of a stated direction); `mu-front-shocks-down` (axle inferred). Rows whose axle is our choice because the snapshot names none: `mu-front-springs-softer`, `tr-front-shocks-down`, `tr-springs-softer` (noted in `notes`).

**Gaps (the app must not invent these):** no rear-camber lever in the snapshot; no BD12 values for caster, droop gauge, anti-roll bars, springs, shock oil, shock positions, diff oil, Ackermann or bump steer; most step sizes and outer bounds are unsourced (marked in `range`/`notes`); tyre compounds, shore hardness and inserts are a recorded gap (refuse); ESC and motor pages were deliberately left out of the snapshot (refuse ESC/motor setup questions; the qualitative "throttle profile" mention stays out of the lever table); wing position and diff height stay qualitative or out; Active Rear Suspension toe gain is not used (unknown whether his BD12 runs ARS).

**Review checklist per row (about 20-30 s each):** direction matches the cited chunk; the trade-off is in the chunk or marked "Not stated in the notes"; step and bounds plausible for his car; the action is something he can do at the pit table; then set `"status": "reviewed"`.

## Appendix B: prompts for a CPU-only machine

Design rules: the system prompt is byte-identical on every call (Ollama can reuse the cached prefix; unverified how much this saves on his machine); the variable part goes last and stays short; `temperature: 0`, `think: false`, `num_ctx: 4096`, `keep_alive: "30m"`; output length capped with `num_predict`. Token counts below are characters / 4, a rough estimate (the Gemma tokenizer may differ by about 20%), and exclude the JSON schema passed in `format` (whether Ollama also inserts the schema into the prompt text is unverified).

### B.1 Symptom classifier (`server/coach/prompts.ts` export `CLASSIFIER_SYSTEM`)

Request: `POST /api/chat` with `stream: false`, `format: CLASSIFIER_SCHEMA`, `options: { temperature: 0, num_ctx: 4096, num_predict: 48 }`, messages `[system, user = the driver's words, trimmed to 300 characters]`.

```text
You sort what an RC touring car driver says about how the car feels into ONE symptom id.
Reply with JSON only.
Symptom ids:
entry-understeer: front will not turn in, pushes or washes out as the car enters a corner
mid-understeer: pushes or runs wide in the middle of the corner
exit-understeer: runs wide or goes straight when back on the throttle
entry-oversteer: rear slides or steps out on braking or turn-in
exit-oversteer: rear loose, snaps or spins on throttle out of corners
traction-roll: car tips, digs in, lifts inside wheels or rolls over in corners
bumpy-track: bounces, hops, skips or gets unsettled over bumps
nervous-twitchy: darty, twitchy, edgy, hard to keep straight
low-grip: slides everywhere, no grip front or rear, dusty or cold track
fade-late-run: good early in the run, then grip, speed or steering fades
left-right-difference: turns better one way than the other, pulls to one side
out-of-scope: anything else (engines, nitro, batteries, charging, ESC, motors, tyre compounds, other car types, not about RC handling)
Rules: pick the closest id. If a second id also fits, put it in alt_id, else "none". phase: entry, mid, exit or none. confidence: 0 to 1.
Examples:
"front washes out into the hairpin" -> entry-understeer
"tail steps out when I hit the gas" -> exit-oversteer
"what lipo charger should I buy" -> out-of-scope
```

Schema:

```json
{"type":"object","properties":{
  "symptom_id":{"type":"string","enum":["entry-understeer","mid-understeer","exit-understeer","entry-oversteer","exit-oversteer","traction-roll","bumpy-track","nervous-twitchy","low-grip","fade-late-run","left-right-difference","out-of-scope"]},
  "alt_id":{"type":"string","enum":["none","entry-understeer","mid-understeer","exit-understeer","entry-oversteer","exit-oversteer","traction-roll","bumpy-track","nervous-twitchy","low-grip","fade-late-run","left-right-difference","out-of-scope"]},
  "phase":{"type":"string","enum":["entry","mid","exit","none"]},
  "confidence":{"type":"number"}},
 "required":["symptom_id","alt_id","phase","confidence"]}
```

Estimate: system about 340 tokens (cached after the first call), user 10-40 tokens, output about 25-35 tokens. Post-processing in code: if `confidence < 0.6` or `alt_id != "none"`, the UI shows "Did you mean" chips for both ids. The model's confidence is self-reported and uncalibrated; it is used only to decide whether to ask.

### B.2 Explainer (`EXPLAINER_SYSTEM`)

Request: `POST /api/chat` with `stream: true`, no `format`, `options: { temperature: 0.2, num_ctx: 4096, num_predict: 110 }`.

```text
You are a calm pit-side setup coach for a 1/10 touring car.
Rewrite CARD as 2 or 3 short spoken sentences to the driver ("you").
Use only facts from CARD and NOTES. Never add a number that is not in CARD.
Say the change, what it should do, the trade-off, then how to check it.
No lists, no markdown, no sources, no greetings.
```

User message template (example filled for `xo-rear-arb-thinner` on a BD12 with generic bar baseline):

```text
CARD: {"symptom":"Loose on power","action":"Thinner rear anti-roll bar","from":1.2,"to":1.1,"unit":"mm","effect":"More on-power rear traction.","tradeOff":"More off-power rotation.","verify":"3-5 laps; judge exits, then check entry did not get loose.","skipped":"Rear toe-in is already 3.5 deg, the top of the range in the notes."}
NOTES:
1. <text of citations[0], first 60 words>
2. <text of citations[1], first 60 words>
```

Estimate: system about 80 tokens, user about 190-250 tokens, output 60-100 tokens. NOTES carry at most two chunks, each cut to 60 words. After generation, the number guard (section 4.3) checks the text; on failure the template is used and the event says `source: "template"`.

### B.3 Ask the notes (stretch, only if time remains)

Search returns 3 chunks; the UI shows them as cards without any model call. Optional summary prompt: same rules as B.2 ("Answer in 2 sentences using only NOTES; if NOTES do not answer, say you don't have that in your notes"), `num_predict: 90`, NOTES = top 2 chunks at 60 words each, plus the number guard against the chunk texts.

### B.4 Latency budget (planning figures, not measurements)

| Step | Tokens in / out | Dev M4 Max GPU (measured classify) | His i7 CPU-only (unmeasured) |
| --- | --- | --- | --- |
| Classify | ~370 / ~30 | median TTFT 138 ms, 85.8 tok/s decode (memory, 10 cases, E4B) | unknown; the memory file's hardware-ratio estimate for E4B is 5-15 tok/s decode, 20-50 tok/s prefill, better for E2B. Chip taps skip this step |
| Pick lever | none | under 10 ms (plain code) | same |
| Explain | ~300 / ~90 | not measured yet (T9) | unknown; the card is already on screen while this streams |

## Sources

- Ollama: https://docs.ollama.com/macos (macOS 14+, Intel CPU only) · https://docs.ollama.com/api/openai-compatibility (no `num_ctx` via the OpenAI API; Modelfile workaround) · https://docs.ollama.com/capabilities/structured-outputs · https://ollama.com/library/gemma4/tags (`gemma4:e2b-it-qat` 4.3 GB, `gemma4:e4b-it-qat` 6.1 GB, text and image input; no audio listed)
- Mastra (via Context7 `/mastra-ai/mastra`, docs sources under `docs/src/content/en/`): workflows overview, human-in-the-loop (`suspend`, `resumeSchema`), snapshots (`LibSQLStore`, `createRun({ runId })`, `resume`), streaming (`writer.write`), models (custom OpenAI-compatible endpoints) · https://mastra.ai/docs
- Web Speech: https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition/processLocally · MDN browser-compat-data `api/SpeechRecognition.json` (processLocally, `available()`, `install()`: Chrome 139; `phrases`: Chrome 142; Safari: no) · `api/SpeechSynthesisVoice.json` (`localService`)
- Entire: https://docs.entire.io/platforms/cli (`entire enable --yes --agent claude-code`)
- npm registry (`npm view`, 2026-10-04): versions and peer dependencies in section 3
- Local: `docs/CHALLENGE-MEMORY.md`, `AGENTS.md`, `README.md`, `docs/PHONE-SPIKE.md`, `CHALLENGE.md`, `PARTNER-REPORT.md`, `ideas/02-rc-pit-companion.md`, `ideas/FINAL-REPORT.md`, `kb/PROVENANCE.md`, all 11 pages in `kb/source/`, `data/generated/kb.json` (106 chunk ids, read, not rebuilt)

**Unverified in this plan:** Mastra stream event shapes for custom `writer` events; Chrome on-device speech on an Intel Mac; exact `available()`/`install()`/`phrases` signatures; `@preact/preset-vite` with Vite 8 + TS 7 in practice; libsql native binary on his machine; his macOS, Chrome and Node versions; any speed on his laptop; whether Ollama adds the schema to the prompt text (affects token estimates slightly); Entire behaviour in a monorepo subfolder.
