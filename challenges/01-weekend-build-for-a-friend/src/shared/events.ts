// SSE event names and payloads (plan section 2.4). FROZEN: only T0, T7 and T10 edit this file.
//
// POST /api/coach/turn streams, in this fixed order:
//   classified, then either refusal (and the stream ends) or
//   precheck, suggestion, token*, explained, suspended.
// `error` may arrive at any point and ends the stream.
// The UI renders the suggestion card as soon as `suggestion` arrives; `token`s only fill the "coach says" line.
//
// Wire format (standard SSE, as written by hono/streaming streamSSE):
//   event: <name>\n data: <JSON payload>\n\n
import type {
  Classification,
  PrecheckDef,
  PullProgress,
  Refusal,
  Suggestion,
  Explanation,
  TurnStatus,
} from "./types";

export const COACH_EVENTS = [
  "classified",
  "refusal",
  "precheck",
  "suggestion",
  "token",
  "explained",
  "suspended",
  "error",
] as const;

export type CoachEventName = (typeof COACH_EVENTS)[number];

export interface CoachEventMap {
  classified: Classification;
  refusal: Refusal;
  precheck: PrecheckDef[];
  suggestion: Suggestion;
  token: { text: string };
  explained: Explanation;
  suspended: { runId: string; status: TurnStatus };
  error: { message: string; stage?: string };
}

/** Discriminated union used by the server's `emit` callback and the UI's SSE parser. */
export type CoachEvent = { [K in CoachEventName]: { event: K; data: CoachEventMap[K] } }[CoachEventName];

// POST /api/llm/pull streams `progress` frames (Ollama /api/pull lines), then `done` or `error`.
export const PULL_EVENTS = ["progress", "done", "error"] as const;
export type PullEventName = (typeof PULL_EVENTS)[number];
export interface PullEventMap {
  progress: PullProgress;
  done: { model: string };
  error: { message: string; stage?: string };
}
export type PullEvent = { [K in PullEventName]: { event: K; data: PullEventMap[K] } }[PullEventName];

export const isCoachEventName = (s: string): s is CoachEventName =>
  (COACH_EVENTS as readonly string[]).includes(s);
