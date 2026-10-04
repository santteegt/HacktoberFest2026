// Typed fetch + SSE client for the /api contract in src/shared/api.ts (T4a).
//
// EXPORTED NAMES (stable: other agents code against these; add, do not rename):
//   Low level   request(key, body?, opts?)      one JSON endpoint, typed by the Endpoints table
//               ApiRequestError                  thrown on 4xx/5xx/network failure ({ status, stage })
//               isMock()                         true with ?mock=1 or VITE_MOCK_API=1 (canned in-memory data)
//   Meta        getHealth, getMeta
//   Settings    getSettings, putSettings(patch)
//   Sessions    createSession(body), listSessions(), getSession(id), patchSession(id, body)
//               applySetup(sessionId, body)      copy-on-write, one Change per changed param
//               addRun(sessionId, body)
//   Changes     patchChange(id, { outcome, outcomeRunId? })
//   Saved       listSaved(), saveSetup(body), deleteSaved(id)
//   Data        exportAll(), importAll(dump), resetAll()      (resetAll sends { confirm: "RESET" })
//   KB          kbSearch(q, limit = 3), kbChunk(id)           (no model call)
//   Coach       coachTurn(input, signal?)   async generator of CoachEvent (SSE over fetch)
//               coachDecide(runId, body), coachOutcome(runId, body)
//   LLM         getLlmStatus(), pullModel(model, signal?) async generator of PullEvent (SSE),
//               warmupLlm()
//   Analysis    getSimilar(sessionId), getCompare(runA, runB), getHistory()
//   Speech      speak(text, voice?)
//   SSE         parseSse(response, signal?)  generic `event:`/`data:` parser (used by both generators)
//
// POST SSE endpoints need fetch + a ReadableStream parser: EventSource cannot POST.
import type { EndpointKey, Endpoints } from "../shared/api";
import { isCoachEventName, PULL_EVENTS, type CoachEvent, type PullEvent } from "../shared/events";
import type { CoachTurnInput } from "../shared/types";

export interface RequestOptions {
  /** Values substituted into ":id"-style path segments. */
  params?: Record<string, string>;
  query?: Record<string, string | number | undefined>;
  signal?: AbortSignal;
}

/** Mock mode: `?mock=1` in the page URL or VITE_MOCK_API=1 at build/dev time. */
const MOCK: boolean = (() => {
  try {
    if (import.meta.env?.VITE_MOCK_API === "1") return true;
    return typeof location !== "undefined" && new URLSearchParams(location.search).get("mock") === "1";
  } catch {
    return false;
  }
})();

export const isMock = (): boolean => MOCK;

export class ApiRequestError extends Error {
  readonly status: number;
  readonly stage?: string;
  constructor(message: string, status = 0, stage?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.stage = stage;
  }
}

const mockModule = () => import("./mock");

function buildUrl(path: string, opts?: RequestOptions): string {
  let p = path;
  for (const [k, v] of Object.entries(opts?.params ?? {})) p = p.replace(`:${k}`, encodeURIComponent(v));
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(opts?.query ?? {})) if (v !== undefined && v !== "") qs.set(k, String(v));
  const s = qs.toString();
  return s ? `${p}?${s}` : p;
}

async function toError(res: Response): Promise<ApiRequestError> {
  let message = `${res.status} ${res.statusText}`.trim();
  let stage: string | undefined;
  try {
    const j = (await res.json()) as { error?: string; stage?: string };
    if (j?.error) message = j.error;
    stage = j?.stage;
  } catch {
    /* body was not JSON */
  }
  return new ApiRequestError(message, res.status, stage);
}

/** Calls one JSON endpoint; rejects with ApiRequestError carrying the server's `{ error, stage }` on 4xx/5xx. */
export async function request<K extends EndpointKey>(
  key: K,
  body?: Endpoints[K]["body"],
  opts?: RequestOptions,
): Promise<Endpoints[K]["res"]> {
  if (MOCK) return (await mockModule()).mockRequest(key, body, opts);
  const space = key.indexOf(" ");
  const method = key.slice(0, space);
  const path = key.slice(space + 1);
  const init: RequestInit = { method, signal: opts?.signal, headers: { accept: "application/json" } };
  if (body !== undefined && method !== "GET") {
    init.body = JSON.stringify(body);
    (init.headers as Record<string, string>)["content-type"] = "application/json";
  }
  let res: Response;
  try {
    res = await fetch(buildUrl(path, opts), init);
  } catch (e) {
    if ((e as Error)?.name === "AbortError") throw e;
    throw new ApiRequestError("Cannot reach the pit server. Is `npm run dev` running?", 0);
  }
  if (!res.ok) throw await toError(res);
  return (await res.json()) as Endpoints[K]["res"];
}

// ---------- SSE ----------

export interface SseFrame {
  event: string;
  data: unknown;
}

/** Parses a standard SSE response body (`event:` + `data:` lines, blank-line separated) into frames. */
export async function* parseSse(res: Response, signal?: AbortSignal): AsyncGenerator<SseFrame> {
  if (!res.body) throw new ApiRequestError("The server sent no stream.", res.status);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  const onAbort = () => void reader.cancel().catch(() => {});
  signal?.addEventListener("abort", onAbort);
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      let i: number;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const raw = buf.slice(0, i);
        buf = buf.slice(i + 2);
        const frame = parseFrame(raw);
        if (frame) yield frame;
      }
    }
    buf += decoder.decode().replace(/\r\n/g, "\n");
    if (buf.trim()) {
      const frame = parseFrame(buf);
      if (frame) yield frame;
    }
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
  } finally {
    signal?.removeEventListener("abort", onAbort);
    reader.releaseLock?.();
  }
}

function parseFrame(raw: string): SseFrame | null {
  let event = "message";
  const data: string[] = [];
  for (const line of raw.split("\n")) {
    if (!line || line.startsWith(":")) continue; // comment / keep-alive
    const c = line.indexOf(":");
    const field = c < 0 ? line : line.slice(0, c);
    const value = c < 0 ? "" : line.slice(c + 1).replace(/^ /, "");
    if (field === "event") event = value;
    else if (field === "data") data.push(value);
  }
  if (!data.length) return null;
  const text = data.join("\n");
  try {
    return { event, data: JSON.parse(text) };
  } catch {
    return { event, data: text };
  }
}

async function postSse(path: string, body: unknown, signal?: AbortSignal): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "POST",
      signal,
      headers: { "content-type": "application/json", accept: "text/event-stream" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    if ((e as Error)?.name === "AbortError") throw e;
    throw new ApiRequestError("Cannot reach the pit server. Is `npm run dev` running?", 0);
  }
  if (!res.ok) throw await toError(res);
  return res;
}

/** POST /api/coach/turn: yields events in the order documented in src/shared/events.ts. Abort the signal to cancel. */
export async function* coachTurn(input: CoachTurnInput, signal?: AbortSignal): AsyncGenerator<CoachEvent> {
  if (MOCK) {
    yield* (await mockModule()).mockCoachTurn(input, signal);
    return;
  }
  const res = await postSse("/api/coach/turn", input, signal);
  for await (const f of parseSse(res, signal)) {
    if (isCoachEventName(f.event)) yield { event: f.event, data: f.data } as CoachEvent;
  }
}

/** POST /api/llm/pull: yields progress frames, then done or error. */
export async function* pullModel(model: string, signal?: AbortSignal): AsyncGenerator<PullEvent> {
  if (MOCK) {
    yield* (await mockModule()).mockPull(model, signal);
    return;
  }
  const res = await postSse("/api/llm/pull", { model }, signal);
  for await (const f of parseSse(res, signal)) {
    if ((PULL_EVENTS as readonly string[]).includes(f.event)) yield { event: f.event, data: f.data } as PullEvent;
  }
}

// ---------- named wrappers (one per endpoint in plan 2.4) ----------

type Body<K extends EndpointKey> = Endpoints[K]["body"];

export const getHealth = () => request("GET /api/health");
export const getMeta = () => request("GET /api/meta");

export const getSettings = () => request("GET /api/settings");
export const putSettings = (patch: Body<"PUT /api/settings">) => request("PUT /api/settings", patch);

export const createSession = (body: Body<"POST /api/sessions">) => request("POST /api/sessions", body);
export const listSessions = () => request("GET /api/sessions");
export const getSession = (id: string) => request("GET /api/sessions/:id", undefined, { params: { id } });
export const patchSession = (id: string, body: Body<"PATCH /api/sessions/:id">) =>
  request("PATCH /api/sessions/:id", body, { params: { id } });
export const applySetup = (sessionId: string, body: Body<"POST /api/sessions/:id/setup">) =>
  request("POST /api/sessions/:id/setup", body, { params: { id: sessionId } });
export const getSetup = (id: string) => request("GET /api/setups/:id", undefined, { params: { id } });
export const addRun = (sessionId: string, body: Body<"POST /api/sessions/:id/runs">) =>
  request("POST /api/sessions/:id/runs", body, { params: { id: sessionId } });

export const patchChange = (id: string, body: Body<"PATCH /api/changes/:id">) =>
  request("PATCH /api/changes/:id", body, { params: { id } });

export const listSaved = () => request("GET /api/saved");
export const saveSetup = (body: Body<"POST /api/saved">) => request("POST /api/saved", body);
export const deleteSaved = (id: string) => request("DELETE /api/saved/:id", undefined, { params: { id } });

export const exportAll = () => request("GET /api/export");
export const importAll = (dump: Body<"POST /api/import">) => request("POST /api/import", dump);
export const resetAll = () => request("POST /api/reset", { confirm: "RESET" });

export const kbSearch = (q: string, limit = 3, signal?: AbortSignal) =>
  request("GET /api/kb/search", undefined, { query: { q, limit }, signal });
export const kbChunk = (id: string) => request("GET /api/kb/chunk/:id", undefined, { params: { id } });

export const coachDecide = (runId: string, body: Body<"POST /api/coach/:runId/decide">) =>
  request("POST /api/coach/:runId/decide", body, { params: { runId } });
export const coachOutcome = (runId: string, body: Body<"POST /api/coach/:runId/outcome">) =>
  request("POST /api/coach/:runId/outcome", body, { params: { runId } });

export const getLlmStatus = (signal?: AbortSignal) => request("GET /api/llm/status", undefined, { signal });
export const warmupLlm = () => request("POST /api/llm/warmup");

export const getSimilar = (sessionId: string) =>
  request("GET /api/analysis/similar", undefined, { query: { sessionId } });
export const getCompare = (runA: string, runB: string) =>
  request("GET /api/analysis/compare", undefined, { query: { runA, runB } });
export const getHistory = () => request("GET /api/analysis/history");

export const speak = (text: string, voice?: string) => request("POST /api/speak", { text, voice });
