// CoachEngine interface (plan 2.3). FROZEN (T0; only T7/T10 edit).
// T3 implements it twice: workflow.mastra.ts (Mastra "coach-turn" workflow with two suspend points)
// and workflow.plain.ts (plain TypeScript fallback). Routes depend only on this interface.
import type { CoachEvent } from "../../src/shared/events";
import type { CoachTurnInput, Decision, Outcome, OutcomeResult, TurnState } from "../../src/shared/types";

export type { CoachEvent };

/** Sends one SSE event to the client (classified, refusal, precheck, suggestion, token, explained, suspended, error). */
export type EmitFn = (e: CoachEvent) => Promise<void>;

export interface DecideArgs {
  decision: Decision;
  /** Index into `suggestion.alternatives` when decision is "alternative". */
  alternativeIndex?: number;
}

export interface OutcomeArgs {
  outcome: Outcome;
  /** Run id the outcome was judged on, when the driver logged one. */
  runRef?: string;
}

export interface CoachEngine {
  /** "mastra" or "plain": reported in logs and the post, so the Mastra claim stays honest. */
  readonly kind: "mastra" | "plain";
  /** Runs classify -> precheck -> pickLever -> explain and stops at the first suspend (awaiting-decision) or a refusal. */
  start(input: CoachTurnInput, emit: EmitFn): Promise<TurnState>;
  /** Resumes the decision suspend point; "apply" writes the change through the vault repo. */
  decide(runId: string, d: DecideArgs): Promise<TurnState>;
  /** Resumes the outcome suspend point; logs the outcome on the Change and computes the next prompt. */
  outcome(runId: string, o: OutcomeArgs): Promise<OutcomeResult>;
}
