// Ollama client on the native API (T3): /api/chat with `format` (JSON schema), options.num_ctx,
// temperature 0, think false, keep_alive "30m", NDJSON streaming, AbortSignal. Also /api/tags,
// /api/ps, /api/pull. The browser never talks to Ollama; only this server does.
//
// Why native and not the OpenAI-compatible endpoint: only /api/chat can set num_ctx per request and
// enforce a JSON schema via `format` (plan section 1).
import type { LlmStatus, PullProgress, Settings } from "../../src/shared/types";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface ChatOptions {
  messages: ChatMessage[];
  /** JSON schema for structured output (Ollama `format`). */
  format?: Record<string, unknown>;
  numCtx?: number;
  temperature?: number;
  /** Output cap (Ollama options.num_predict). */
  numPredict?: number;
  signal?: AbortSignal;
}

/** Ollama's own timing fields, converted from ns to ms (present on the final response). */
export interface OllamaTimings {
  totalMs?: number;
  loadMs?: number;
  promptEvalCount?: number;
  promptEvalMs?: number;
  evalCount?: number;
  evalMs?: number;
}

export interface ChatResult {
  text: string;
  /** Wall time of the call in ms. */
  ms: number;
  /** Time to first token in ms (streaming only). */
  ttftMs?: number;
  timings?: OllamaTimings;
}

/** Thrown for network failures and non-2xx answers; `unreachable` is true when nothing answered at all. */
export class OllamaError extends Error {
  constructor(
    message: string,
    readonly unreachable: boolean,
    readonly status?: number,
  ) {
    super(message);
    this.name = "OllamaError";
  }
}

export const KEEP_ALIVE = "30m";

interface RawChatChunk {
  message?: { content?: string };
  done?: boolean;
  error?: string;
  total_duration?: number;
  load_duration?: number;
  prompt_eval_count?: number;
  prompt_eval_duration?: number;
  eval_count?: number;
  eval_duration?: number;
}

const nsToMs = (ns?: number) => (typeof ns === "number" ? Math.round(ns / 1e6) : undefined);

function timingsOf(c: RawChatChunk): OllamaTimings {
  return {
    totalMs: nsToMs(c.total_duration),
    loadMs: nsToMs(c.load_duration),
    promptEvalCount: c.prompt_eval_count,
    promptEvalMs: nsToMs(c.prompt_eval_duration),
    evalCount: c.eval_count,
    evalMs: nsToMs(c.eval_duration),
  };
}

/** Splits a byte stream into parsed NDJSON objects (one JSON value per line). */
export async function* ndjson<T>(body: ReadableStream<Uint8Array>): AsyncGenerator<T> {
  const reader = body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl: number;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (line) yield JSON.parse(line) as T;
      }
    }
    buf += dec.decode();
    if (buf.trim()) yield JSON.parse(buf.trim()) as T;
  } finally {
    reader.releaseLock();
  }
}

export class OllamaClient {
  /** Wall time of the last successful chat call, for /api/llm/status. */
  lastLatencyMs?: number;

  constructor(
    readonly url: string,
    readonly model: string,
    readonly numCtx: number,
  ) {}

  private async post(path: string, body: unknown, signal?: AbortSignal): Promise<Response> {
    let res: Response;
    try {
      res = await fetch(`${this.url}${path}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
        signal,
      });
    } catch (e) {
      if (signal?.aborted) throw e;
      throw new OllamaError(`Ollama not reachable at ${this.url}: ${(e as Error).message}`, true);
    }
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      let msg = text;
      try {
        msg = (JSON.parse(text) as { error?: string }).error ?? text;
      } catch {
        /* plain text */
      }
      throw new OllamaError(`Ollama ${path} ${res.status}: ${msg}`, false, res.status);
    }
    return res;
  }

  private chatBody(o: ChatOptions, stream: boolean) {
    return {
      model: this.model,
      messages: o.messages,
      stream,
      think: false,
      keep_alive: KEEP_ALIVE,
      ...(o.format ? { format: o.format } : {}),
      options: {
        temperature: o.temperature ?? 0,
        num_ctx: o.numCtx ?? this.numCtx,
        ...(o.numPredict ? { num_predict: o.numPredict } : {}),
      },
    };
  }

  /** Non-streaming chat (used by the classifier with a JSON schema in `format`). */
  async chat(o: ChatOptions): Promise<ChatResult> {
    const t0 = performance.now();
    const res = await this.post("/api/chat", this.chatBody(o, false), o.signal);
    const j = (await res.json()) as RawChatChunk;
    if (j.error) throw new OllamaError(j.error, false);
    const ms = Math.round(performance.now() - t0);
    this.lastLatencyMs = ms;
    return { text: j.message?.content ?? "", ms, timings: timingsOf(j) };
  }

  /** Streams content tokens; the final ChatResult is the generator's return value. */
  async *chatStream(o: ChatOptions): AsyncGenerator<string, ChatResult> {
    const t0 = performance.now();
    const res = await this.post("/api/chat", this.chatBody(o, true), o.signal);
    if (!res.body) throw new OllamaError("Ollama returned no body", false);
    let text = "";
    let ttftMs: number | undefined;
    let timings: OllamaTimings | undefined;
    for await (const c of ndjson<RawChatChunk>(res.body)) {
      if (c.error) throw new OllamaError(c.error, false);
      const piece = c.message?.content ?? "";
      if (piece) {
        ttftMs ??= Math.round(performance.now() - t0);
        text += piece;
        yield piece;
      }
      if (c.done) timings = timingsOf(c);
    }
    const ms = Math.round(performance.now() - t0);
    this.lastLatencyMs = ms;
    return { text, ms, ttftMs, timings };
  }

  private async getJson<T>(path: string, timeoutMs: number): Promise<T> {
    let res: Response;
    try {
      res = await fetch(`${this.url}${path}`, { signal: AbortSignal.timeout(timeoutMs) });
    } catch (e) {
      throw new OllamaError(`Ollama not reachable at ${this.url}: ${(e as Error).message}`, true);
    }
    if (!res.ok) throw new OllamaError(`Ollama ${path} ${res.status}`, false, res.status);
    return (await res.json()) as T;
  }

  /** /api/tags (pulled) + /api/ps (loaded). Never throws: unreachable gives reachable=false. */
  async status(): Promise<LlmStatus> {
    const base: LlmStatus = {
      reachable: false,
      url: this.url,
      model: this.model,
      present: false,
      loaded: false,
      numCtx: this.numCtx,
      ...(this.lastLatencyMs !== undefined ? { lastLatencyMs: this.lastLatencyMs } : {}),
    };
    type Models = { models?: { name?: string; model?: string }[] };
    const has = (m: Models) => (m.models ?? []).some((x) => x.name === this.model || x.model === this.model);
    try {
      const tags = await this.getJson<Models>("/api/tags", 2000);
      base.reachable = true;
      base.present = has(tags);
      const ps = await this.getJson<Models>("/api/ps", 2000);
      base.loaded = has(ps);
    } catch {
      /* reachable stays as far as we got */
    }
    return base;
  }

  /** Streams /api/pull progress frames. The caller decides whether a pull is allowed. */
  async *pull(model: string, signal?: AbortSignal): AsyncGenerator<PullProgress> {
    const res = await this.post("/api/pull", { model, stream: true }, signal);
    if (!res.body) throw new OllamaError("Ollama returned no body", false);
    for await (const f of ndjson<{ status?: string; completed?: number; total?: number; error?: string }>(res.body)) {
      if (f.error) throw new OllamaError(f.error, false);
      yield {
        status: f.status ?? "",
        ...(typeof f.completed === "number" ? { completed: f.completed } : {}),
        ...(typeof f.total === "number" ? { total: f.total } : {}),
      };
    }
  }

  /** Loads the model with keep_alive (empty messages = load only) at our num_ctx; returns elapsed ms. */
  async warmup(): Promise<number> {
    const t0 = performance.now();
    const res = await this.post("/api/chat", {
      model: this.model,
      messages: [],
      keep_alive: KEEP_ALIVE,
      options: { num_ctx: this.numCtx },
    });
    await res.text();
    return Math.round(performance.now() - t0);
  }
}

// One client per (url, model, numCtx), so lastLatencyMs survives across requests.
let cached: OllamaClient | undefined;

export function ollamaFor(s: Pick<Settings, "ollamaUrl" | "model" | "numCtx">): OllamaClient {
  const url = s.ollamaUrl.replace(/\/+$/, "");
  if (!cached || cached.url !== url || cached.model !== s.model || cached.numCtx !== s.numCtx) {
    cached = new OllamaClient(url, s.model, s.numCtx);
  }
  return cached;
}
