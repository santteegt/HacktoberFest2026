// Coach steps shared by the Mastra and plain engines (T3). T0 stub with the planned signatures.
import type {
  Classification,
  CoachTurnInput,
  LeverSuggestion,
  PrecheckDef,
  Refusal,
  Suggestion,
  TurnState,
} from "../../src/shared/types";
import type { EmitFn } from "./engine";

/** Chip passthrough, else keyword refusal check, else LLM (keyword fallback when Ollama is down). */
export async function classify(
  _input: CoachTurnInput,
  _emit: EmitFn,
): Promise<{ classification?: Classification; refusal?: Refusal }> {
  throw new Error("not implemented");
}

export function precheck(_symptomId: string): PrecheckDef[] {
  throw new Error("not implemented");
}

export async function pickLever(_state: TurnState, _emit: EmitFn): Promise<Suggestion> {
  throw new Error("not implemented");
}

/** LLM phrasing (streamed as `token` events), number guard, template fallback. */
export async function explain(
  _s: LeverSuggestion,
  _emit: EmitFn,
): Promise<{ text: string; source: "llm" | "template"; ms?: number }> {
  throw new Error("not implemented");
}

/** True when every number in `text` appears in the card (from, to, action, effect, verify). */
export function numberGuard(_text: string, _s: LeverSuggestion): boolean {
  throw new Error("not implemented");
}

/** "{action}: {from} to {to} {unit}. {effect} Trade-off: {tradeOff} Check: {verify}" */
export function templateExplanation(_s: LeverSuggestion): string {
  throw new Error("not implemented");
}
