// Typed fetch + SSE client for the /api contract in src/shared/api.ts (T4a). T0 stub.
// POST SSE endpoints (coach turn, llm pull) need fetch + a ReadableStream parser: EventSource cannot POST.
import type { EndpointKey, Endpoints } from "../shared/api";
import type { CoachEvent, PullEvent } from "../shared/events";
import type { CoachTurnInput } from "../shared/types";

export interface RequestOptions {
  /** Values substituted into ":id"-style path segments. */
  params?: Record<string, string>;
  query?: Record<string, string | number | undefined>;
  signal?: AbortSignal;
}

/** Calls one JSON endpoint; rejects with the server's `{ error, stage }` on 4xx/5xx. */
export async function request<K extends EndpointKey>(
  _key: K,
  _body?: Endpoints[K]["body"],
  _opts?: RequestOptions,
): Promise<Endpoints[K]["res"]> {
  throw new Error("not implemented");
}

/** POST /api/coach/turn: yields events in the order documented in src/shared/events.ts. */
export async function* coachTurn(_input: CoachTurnInput, _signal?: AbortSignal): AsyncGenerator<CoachEvent> {
  throw new Error("not implemented");
}

/** POST /api/llm/pull: yields progress frames, then done or error. */
export async function* pullModel(_model: string, _signal?: AbortSignal): AsyncGenerator<PullEvent> {
  throw new Error("not implemented");
}
