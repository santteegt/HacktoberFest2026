Decision flow (deterministic state machine; the LLM only does steps 2 and 5):

1. Context: car, grip, surface, current setup.
2. Symptom: LLM maps the driver's words to `{symptomId, phase, confidence}` from the fixed list.
3. Pre-check gate: basic car checks before any setup change.
4. Lever: filter `data/levers.json` by symptom, phase and grip; clamp to min/max.
5. Explain: 2-3 sentences built only from the lever row and its cited chunks.
6. Verify: how to confirm over the next few laps.
7. Log the outcome (better / same / worse); revert or continue.
