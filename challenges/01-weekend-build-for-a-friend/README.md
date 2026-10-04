# RC Pit Companion

An offline, voice-first setup coach and setup vault for the 1/10 touring car (built around the Yokomo BD12). Tell it how the car feels; it suggests **one** change at a time, shows the effect on a 3D car, and lets you save the setups that worked together with the track conditions, so you can pull them up on race day.

Built for a friend, for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01) (`#hf26challenge`). **Status: scaffold. Nothing below "Planned" works yet.**

## The friend

A club racer with a Yokomo BD12 who goes to practice sessions and wants them to be worth the trip:

- say what the car feels like and get a setup change to try next;
- keep the best setups with their track conditions (surface, grip, bumps, temperature);
- find the setups that worked at a similar track when a championship race comes around;
- use it at the pit table. He prefers his phone, but the phone test failed (see below), so v1 runs on his consumer laptop, which can run a small Gemma model (E2B/E4B).

## Planned

- **Coach:** push-to-talk voice in, spoken answer out. A fixed symptom list and a hand-reviewed table of adjustments (`data/`) decide the advice; the model only maps speech to a symptom and phrases the explanation. Every answer cites the offline notes it came from, and out-of-scope questions get a refusal.
- **Setup vault:** sessions, change log with better/same/worse outcomes, saved setups searchable by track conditions. Stored on the device (IndexedDB), no account.
- **3D view:** a small parametric car that animates the change (camber, toe, ride height, shock angle).
- **Open AI core:** Gemma 4 (E2B/E4B) served by a local Ollama install on the laptop, behind one interface (`src/llm/provider.ts`).

## Decision: laptop-first (phone spike failed)

The friend would rather use it on his phone, so on 2026-10-04 we tested Gemma 4 E2B on-device in a phone browser. Download worked; creating the engine and running prompts lagged too much to be usable. Details and method: [docs/PHONE-SPIKE.md](docs/PHONE-SPIKE.md). v1 targets the consumer laptop he also owns (Gemma E2B/E4B). No phone support is claimed.

**Runtime: Ollama (decided 2026-10-04).** Gemma 4 E4B (E2B for weaker laptops) is served by a local Ollama install, so nothing leaves the machine and the app needs no multi-gigabyte browser cache. Still open: the agent framework (Mastra or plain code), the local store for the field knowledge and the setup vault, and how voice input works offline (on-device speech recognition is documented for desktop Chrome only, so it will be verified on the target laptop before any offline-voice claim).

## Prior work, credited

All code in this repository was started during the challenge window (see `git log`). The setup **knowledge** it retrieves comes from the author's earlier touring-car notes, will be imported as a frozen, credited snapshot; see [kb/PROVENANCE.md](kb/PROVENANCE.md). The author's earlier 3D dynamics guide, its BD12 model and its setup-sheet app are **not** reused.

## Run

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + production build
```

## Layout

```
src/agent  src/llm  src/voice  src/kb  src/scene  src/state  src/ui   typed stubs, no logic yet
data/                symptoms.json, levers.json (authored, reviewed)
kb/                  PROVENANCE.md, later the frozen notes snapshot
public/icons/        PWA icons
scripts/             copy-wasm.mjs (phone spike); build-kb.ts (planned)
```

## License

MIT, see [LICENSE](LICENSE).
