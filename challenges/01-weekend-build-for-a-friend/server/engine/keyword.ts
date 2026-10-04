// Keyword classifier (fallback and eval baseline) and canned refusals (T2; plan 4.3). T0 stub.
import type { Classification, Refusal, SymptomDef } from "../../src/shared/types";

/** Synonym substring + token overlap; null below the threshold. */
export function keywordClassify(_utterance: string, _symptoms: SymptomDef[]): Classification | null {
  throw new Error("not implemented");
}

/** Keyword refusals: tyre compound gap, ESC/motor, nitro, LiPo, off-road/other car types. */
export function refusalFor(_utterance: string): Refusal | null {
  throw new Error("not implemented");
}
