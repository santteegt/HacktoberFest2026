# RC Pit Companion

An offline setup coach and setup vault for a 1/10 touring car (built around the Yokomo BD12), made for one friend who races it. Tell it how the car feels. It suggests **one** change at a time, says what to expect and how to check it, and lets you save the setups that worked together with the track conditions, so you can pull them up on race day.

**Challenge:** [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01) (DEV event 78) · **Window:** Oct 2, 2026 02:00 → Oct 5, 2026 06:59 UTC · **Tag:** `#hf26challenge`

## The friend

A club racer with a BD12 who goes to practice sessions and wants them to be worth the trip. In his words: "this app will be very useful for practice days so I can quickly store my settings and get feedback from what works, what might have affected my run."

What he asked for, and where it lives:

- Say what the car feels like, get a change to try next: **Coach** screen.
- Keep settings and the changes made during a practice day, with a better/same/worse outcome for each: **Setup** and **Session** screens.
- Find the setups that worked at a similar track when a championship race comes: **Race day** screen.
- Hands free at the pit table: push-to-talk in, spoken answer out. See the limits below before relying on it.

He would rather use it on his phone, but the phone test failed ([docs/PHONE-SPIKE.md](docs/PHONE-SPIKE.md)), so v1 is a laptop app. **No phone support is claimed.**

## How it works

The model is only allowed to do two language jobs. Everything else is plain code.

1. **Understand the symptom.** Gemma 4 maps what you said to one of 12 symptom ids (for example "pushes on turn-in" or "loose on power"), or to "not something my notes cover". Ollama's JSON-schema output keeps the answer to a valid id.
2. **Phrase the explanation.** After the advice is chosen, the model puts it into a short spoken-style paragraph.

In between, a hand-reviewed table (`data/levers.json`) decides what to change and by how much. The model never invents a number: values come from the table, a number guard checks the wording, and a template answer replaces the model's text if it strays. Only the 12 demo-path rows were reviewed by the author; the other 49 are shown with a "draft" badge in the app.

Every answer cites the offline notes it came from. Questions outside the notes get a refusal, not a guess.

## Architecture

![Architecture diagram: Chrome with the Preact screens, 3D explainers and voice talks over HTTP to a local Hono server; the server runs the six-step coach workflow (refuse, classify, pre-checks, pick lever, explain, pause) with Mastra and a plain-TypeScript fallback, calls Ollama on localhost for the two Gemma steps, and reads and writes files on disk (levers.json, the notes snapshot, the vault and the paused-turn store)](docs/architecture.png)

Source: [docs/architecture.svg](docs/architecture.svg). Only the two green boxes (classify and explain) call the model; everything else is plain code, and a chip tap skips the classify step.

## Run it

A step-by-step guide with fixes for common problems is in [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md). The short version:

You need **Node 22.13+** and [Ollama](https://ollama.com) (macOS 14+ on a Mac).

```bash
# 0. Get the code (the project is one folder of a larger repo)
git clone https://github.com/santteegt/HacktoberFest2026.git
cd HacktoberFest2026/challenges/01-weekend-build-for-a-friend

# 1. Get a model. E2B is the small one for older laptops; E4B is what the author develops with.
ollama pull gemma4:e2b-it-qat      # about 4.3 GB
# ollama pull gemma4:e4b-it-qat    # about 6.1 GB

# 2. Install and start
cp .env.example .env               # set OLLAMA_MODEL to the tag you pulled
npm ci                             # also builds the knowledge index
npm start                          # builds the UI and serves it from the local server
```

Open the address `npm start` prints (the server listens on `127.0.0.1:8787`). The first run walks through three steps: pick the car, start a practice session, and check that Ollama and the model are reachable.

Optional, to try it with example data before you have real sessions:

```bash
npm run seed:demo                  # clearly labelled DEMO tracks, runs and setups
```

Developing: `npm run dev`. Checks: `npm run typecheck`, `npm test`, `npm run kb:verify`, `npm run eval:symptoms`, `npm run eval:retrieval`.

`COACH_ENGINE=plain` runs the coach without Mastra, for comparison or if the workflow ever misbehaves.

## What is built on what

- **Model:** Gemma 4 (E2B / E4B, QAT builds), open weights, served by a local Ollama install. The browser never talks to Ollama; only the Node server does. No cloud call exists in `src` or `server`, and Mastra telemetry is switched off.
- **Agent framework:** [Mastra](https://mastra.ai) runs the coach as a workflow with two pause points (waiting for the driver's choice, then for the outcome), with a plain-TypeScript fallback behind the same interface.
- **Server:** Hono. **UI:** Preact, Vite, three.js for the explainer scenes. **Vault:** a single LibSQL file (`var/pit.db`). **Search over the notes:** MiniSearch (keyword, no embeddings).
- **Explainers:** ten three.js scenes and two SVG ones show what a change does to the car. They are schematic: directions come from the notes, some magnitudes are exaggerated for legibility, and the label says so. They are not to scale and show no measured values.

## Honest limits

- **Barely tested on the friend's laptop.** His machine is a 2019 Intel MacBook Pro (CPU-only inference). The only reading from it is one raw `ollama run --verbose` prompt: about 9.2 tokens/s generating and 38.7 tokens/s reading the prompt (model tag to be confirmed, presumed E2B). From that the author estimates a typed coach turn at roughly 25 s and a chip turn at roughly 15 s; the app itself has not been timed there (the demo video was recorded on that laptop, and the friend was very happy with it). All other timings come from the author's Apple M4 Max. E4B on that laptop is untested and would be slower.
- **Voice and offline were shown once, not tested broadly.** In the demo video, recorded on the friend's laptop, the author turns Wi-Fi off and voice input and output work. That is one recording; there is no test matrix. On-device speech recognition needs desktop Chrome (139 or newer) and a one-time download of the English speech pack, and in the author's embedded dev browser it reported "unavailable". Typing and the symptom chips work without it.
- **Offline use** is by design (everything is local) and a network audit of the author's machine saw only loopback traffic. Model download, `npm ci` and the speech pack need internet once.
- **Accuracy figures are small and ours.** The symptom set has 25 cases, 20 in the author's wording and 5 in the friend's own words. On the larger E4B model 24 of 25 are right; on E2B, which the friend's laptop runs, 21 of 25 alone and 23 of 25 with the off-topic gate (a hand-written word list, partly tuned on this set). A fresh set of 14 phrasings scored 13 of 14 on E4B. These are not general accuracy claims; details and caveats are in [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md).
- **The coach is advice from notes, not from the car.** It knows what the author's notes say about a BD12 and touring cars in general. Droop uses the generic gauge convention, not Yokomo's own BD12 procedure.
- **No installer.** The friend needs Node and Ollama.

## Prior work, credited

All code in this repository was written during the challenge window (`git log` starts on Oct 4, 2026). The touring-car **knowledge** it retrieves is not new: it is a frozen, hash-verified snapshot of the author's earlier notes (`kb/source/`, checked by `npm run kb:verify`), which were themselves distilled from third-party videos and manuals. Corrections and additions written in the window live separately in `kb/additions/`. See [kb/PROVENANCE.md](kb/PROVENANCE.md). The author's earlier 3D dynamics guide, its BD12 model and its setup-sheet app are **not** reused.

The agent-written parts of the code were produced with Claude Code (planner, builder and reviewer subagents). The working log of decisions, failures and measurements is [docs/CHALLENGE-MEMORY.md](docs/CHALLENGE-MEMORY.md), and the build plan is [docs/IMPLEMENTATION-PLAN.md](docs/IMPLEMENTATION-PLAN.md).

## Layout

```
server/         Hono server: routes, coach workflow (Mastra + plain), lever engine, vault, search, Ollama client
src/shared/     zod contracts used by both sides
src/ui/         Coach, Setup, Session, Race day, Settings screens
src/scene/      three.js and SVG explainers
src/voice/      push-to-talk and speech output
data/           params, symptoms, prechecks, levers (authored), eval sets and results
kb/             frozen snapshot, additions, manifest, provenance
scripts/        knowledge build and verify, evals, demo seed
tests/          engine, vault, analysis, UI logic, voice, search
src/spike/      the phone feasibility spike (kept for the record)
```

## Commits after the deadline

None so far. Any commit after Oct 5, 2026 06:59 UTC will be listed here.

## License

MIT, see [LICENSE](LICENSE).
