# Screenshots

Taken on 2026-10-04 (UTC-5 evening) from a clean copy of the repository after `npm run seed:demo`, so the session, runs and saved setups are the labelled DEMO data, not real laps. Headless Chrome, 1280 px wide, with the model `gemma4:e4b-it-qat` served by Ollama on the author's Apple M4 Max (not the friend's laptop).

- `coach.png`: the friend's own sentence typed on the Coach screen. The suggestion comes from a lever row that is still a draft, and the card says so.
- `session.png`: the Session log with three DEMO runs and the change that went with each.
- `race-day.png`: saved setups ranked against today's conditions.
- `setup.png`: the Setup screen (values, ranges, and the car view per row).

## scenes/

Four of the twelve setting explainers, captured on 2026-10-05 from the scene's own test page (`src/scene/dev.html`, run with Vite from a clean copy of HEAD), 900 x 380 px, headless Chrome with software WebGL. It is the same scene component the Coach and Setup screens use. Each frame is the end of the one-step change animation: faint copy = before, blue = after. Every frame carries its own "Schematic, not to scale" and "exaggerated" labels.

- `camber-front.png`: front camber 1.5 to 1.0 deg negative, exaggerated x3.
- `toe-front.png`: front toe-out 1.0 to 1.5 deg, top view, exaggerated x4.
- `ride-height-rear.png`: rear ride height 5.0 to 5.8 mm, side view, exaggerated x4.
- `shock-angle-rear.png`: rear shock position 2 to 3 (inner hole = laid down, outer = upright), exaggerated x1.5.

## walkthrough/

Seven frames of one scripted pass through the app, captured on 2026-10-05 from a clean copy of HEAD (`b73888f` plus the off-topic gate) on a new, empty database, with the real model `gemma4:e2b-it-qat` (the model on the friend's laptop) served by Ollama on the author's Apple M4 Max. Headless Chrome driven over the DevTools protocol clicked the real buttons and typed into the real inputs; nothing in the images is edited. The track ("Club carpet") and the "Better" verdict are made up for the screenshots. Frame 7 was taken after `npm run seed:demo -- --yes` added the labelled DEMO setups, so Race day ranks the setup saved in frame 5 next to them.

1. `1-start-session.png`: the first-run session form.
2. `2-say-it.png`: a typed sentence classified as Loose on power, three quick checks, and a reviewed lever that asks for the current diff oil in Setup.
3. `3-tap-a-chip.png`: the "Push in" chip, Reduce caster 4 to 3 deg, the schematic 3D view, and the coach's wording.
4. `4-apply-and-rate.png`: after Apply, the Better / Same / Worse question.
5. `5-save-setup.png`: Better, then the setup saved with the session's conditions.
6. `6-session-log.png`: the change recorded in the session with its outcome.
7. `7-race-day.png`: saved setups ranked for today's conditions.
