// Prompts and the classifier JSON schema (T3; Appendix B). T0 stub with the documented export names.
// Keep prompts tiny and stable (CPU-only latency budget); the model never produces numbers that reach the user.

/** System prompt for the symptom classifier (Appendix B.1). */
export const CLASSIFIER_SYSTEM = "";
/** System prompt for the explainer (Appendix B.2). */
export const EXPLAINER_SYSTEM = "";

/** JSON schema passed to Ollama `format`: { symptom_id, alt_id, phase, confidence }. */
export function classifierSchema(_symptomIds: string[]): Record<string, unknown> {
  throw new Error("not implemented");
}
