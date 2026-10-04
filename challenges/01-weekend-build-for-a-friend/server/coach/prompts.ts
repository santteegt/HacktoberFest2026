// Prompts and the classifier JSON schema (T3, from plan Appendix B; the classifier prompt was shortened in T11).
// The system prompts are kept identical on every call and the variable part goes last and short. Do NOT expect
// Ollama to reuse a cached prefix: measured on gemma4 (T11), it only reuses a fully identical prompt, so prompt
// LENGTH is what sets classify latency. Any edit to the classifier prompt must re-run `npm run eval:symptoms`
// with and without CPU_ONLY=1 (25/25 at 252 tokens is the floor found; shorter variants lost cases).
// The model never produces numbers that reach the user: the explainer output passes the number guard in
// steps.ts or is replaced by the template.

/**
 * System prompt for the symptom classifier. Slimmed by T11 (2026-10-04) from the 389-token Appendix B.1 prompt
 * (examples dropped, definitions shortened): 252 prompt tokens per call, still 25/25 on the eval on both the GPU and
 * the CPU_ONLY proxy. Time to first token tracks prompt tokens (Ollama does not reuse a shared prefix when the user
 * text differs, measured), so do not grow this casually; re-run `npm run eval:symptoms` (and CPU_ONLY=1) after any edit.
 * The schema's `enum`s are grammar only: the model never sees them (a prompt with the definitions only in schema
 * descriptions scored 3/25), so every id and its meaning must stay in this text.
 */
export const CLASSIFIER_SYSTEM = `Pick ONE id for an RC touring car driver's handling complaint. JSON only.
entry-understeer: front won't turn in, pushes on entry
mid-understeer: pushes wide mid-corner
exit-understeer: wide or straight on throttle exit
entry-oversteer: rear steps out braking or turn-in
exit-oversteer: rear snaps loose on throttle exit
traction-roll: tips over, digs in, lifts inside wheels
bumpy-track: bounces, hops, skips, unsettled over bumps
nervous-twitchy: darty, edgy, hard to keep straight
low-grip: slides everywhere, ice, dusty or cold
fade-late-run: good early, then fades
left-right-difference: better one way, pulls to a side
out-of-scope: not RC handling (engines, batteries, ESC, motors, tyres, other cars)
alt_id: runner-up id or "none". phase: entry, mid, exit or none. confidence: 0 to 1.`;

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
