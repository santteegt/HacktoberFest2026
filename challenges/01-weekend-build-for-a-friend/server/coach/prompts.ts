// Prompts and the classifier JSON schema (T3; Appendix B, copied verbatim).
// The system prompts are byte-stable on every call so Ollama can reuse the cached prefix; the variable
// part goes last in the user message and stays short. The model never produces numbers that reach the
// user: the explainer output passes the number guard in steps.ts or is replaced by the template.

/** System prompt for the symptom classifier (Appendix B.1). */
export const CLASSIFIER_SYSTEM = `You sort what an RC touring car driver says about how the car feels into ONE symptom id.
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
"what lipo charger should I buy" -> out-of-scope`;

/** System prompt for the explainer (Appendix B.2). */
export const EXPLAINER_SYSTEM = `You are a calm pit-side setup coach for a 1/10 touring car.
Rewrite CARD as 2 or 3 short spoken sentences to the driver ("you").
Use only facts from CARD and NOTES. Never add a number that is not in CARD.
Say the change, what it should do, the trade-off, then how to check it.
No lists, no markdown, no sources, no greetings.`;

/** The 12 symptom ids in the order of CLASSIFIER_SYSTEM (and data/symptoms.json). */
export const SYMPTOM_IDS = [
  "entry-understeer",
  "mid-understeer",
  "exit-understeer",
  "entry-oversteer",
  "exit-oversteer",
  "traction-roll",
  "bumpy-track",
  "nervous-twitchy",
  "low-grip",
  "fade-late-run",
  "left-right-difference",
  "out-of-scope",
] as const;

/** JSON schema passed to Ollama `format`: { symptom_id, alt_id, phase, confidence }. */
export function classifierSchema(symptomIds: readonly string[] = SYMPTOM_IDS): Record<string, unknown> {
  return {
    type: "object",
    properties: {
      symptom_id: { type: "string", enum: [...symptomIds] },
      alt_id: { type: "string", enum: ["none", ...symptomIds] },
      phase: { type: "string", enum: ["entry", "mid", "exit", "none"] },
      confidence: { type: "number" },
    },
    required: ["symptom_id", "alt_id", "phase", "confidence"],
  };
}

/** Built once so the `format` payload is identical on every call. */
export const CLASSIFIER_SCHEMA = classifierSchema();

/** Classifier request knobs (Appendix B.1). */
// numPredict: plan B.1 says 48, but on 2026-10-04 Ollama emitted pretty-printed JSON that used exactly 48 tokens
// (eval_count 48), one token from truncation; 64 leaves headroom. Output still stops at the closing brace.
export const CLASSIFIER_OPTIONS = { temperature: 0, numPredict: 64, maxUserChars: 300 } as const;
/** Explainer request knobs (Appendix B.2). */
export const EXPLAINER_OPTIONS = { temperature: 0.2, numPredict: 110, notesChunks: 2, notesWords: 60 } as const;

export interface ExplainerCard {
  symptom: string;
  action: string;
  from: number | string | null;
  to: number | string | null;
  unit: string;
  effect: string;
  tradeOff: string;
  verify: string;
  skipped?: string;
}

/** First `n` words of a chunk text (NOTES are capped at 60 words each). */
export const firstWords = (text: string, n: number) => text.split(/\s+/).filter(Boolean).slice(0, n).join(" ");

/** User message for the explainer: `CARD: {json}` then `NOTES:` with at most two numbered chunks. */
export function explainerUser(card: ExplainerCard, notes: string[]): string {
  const lines = [`CARD: ${JSON.stringify(card)}`, "NOTES:"];
  notes.slice(0, EXPLAINER_OPTIONS.notesChunks).forEach((n, i) => lines.push(`${i + 1}. ${firstWords(n, EXPLAINER_OPTIONS.notesWords)}`));
  return lines.join("\n");
}
