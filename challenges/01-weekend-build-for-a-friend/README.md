# RC Pit Companion

An offline, voice-first setup coach and setup vault for the 1/10 touring car (built around the Yokomo BD12). Tell it how the car feels; it suggests **one** change at a time, shows the effect on a 3D car, and lets you save the setups that worked together with the track conditions, so you can pull them up on race day.

Built for a friend, for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01) (`#hf26challenge`). **Status: scaffold. Nothing below "Planned" works yet.**

## The friend

A club racer with a Yokomo BD12 who goes to practice sessions and wants them to be worth the trip:

- say what the car feels like and get a setup change to try next;
- keep the best setups with their track conditions (surface, grip, bumps, temperature);
- find the setups that worked at a similar track when a championship race comes around;
- do it on his **phone** at the pit table; he also has a consumer laptop that can run a small Gemma model (E2B/E4B).

## Planned

- **Coach:** push-to-talk voice in, spoken answer out. A fixed symptom list and a hand-reviewed table of adjustments (`data/`) decide the advice; the model only maps speech to a symptom and phrases the explanation. Every answer cites the offline notes it came from, and out-of-scope questions get a refusal.
- **Setup vault:** sessions, change log with better/same/worse outcomes, saved setups searchable by track conditions. Stored on the device (IndexedDB), no account.
- **3D view:** a small parametric car that animates the change (camber, toe, ride height, shock angle).
- **Open AI core:** Gemma 4 (E2B/E4B) running on-device in the browser, with an Ollama backend on a laptop as the fallback, behind one interface (`src/llm/provider.ts`).

## Open decision: where the model runs for a phone-first user

To settle in the first hours, with measurements, before building on it:

| Option | Question to answer |
| --- | --- |
| Model in the phone browser (WebGPU) | Does Gemma 4 E2B load and run acceptably on his phone, and stay cached offline? |
| Model on the laptop, phone as the screen | Mic and service workers need a secure context, and an HTTPS page generally can't call a plain-HTTP LAN server. Can this be made to work with a hotspot, without fiddly setup? |
| Laptop-only | Always works, but contradicts the phone-first need. |

Speech is the second constraint: on-device recognition is documented for desktop Chrome only, so phone voice offline probably needs a local Whisper model. The README will state exactly what was tested on which device.

## Prior work, credited

All code in this repository was started during the challenge window (see `git log`). The setup **knowledge** it retrieves comes from the author's earlier touring-car notes and will be imported as a frozen, credited snapshot; see [kb/PROVENANCE.md](kb/PROVENANCE.md). The author's earlier 3D dynamics guide, its BD12 model and its setup-sheet app are **not** reused.

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
scripts/             build-kb.ts (planned)
```

## License

MIT, see [LICENSE](LICENSE).
