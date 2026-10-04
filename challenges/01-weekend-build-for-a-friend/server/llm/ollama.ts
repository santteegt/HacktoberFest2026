// Ollama client on the native API (T3): /api/chat with `format` (JSON schema), options.num_ctx,
// temperature 0, think false, keep_alive "30m", NDJSON streaming, AbortSignal. Also /api/tags,
// /api/ps, /api/pull. The browser never talks to Ollama; only this server does. T0 stub.
import type { LlmStatus, PullProgress } from "../../src/shared/types";

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
  signal?: AbortSignal;
}

export interface ChatResult {
  text: string;
  /** Wall time of the call in ms. */
  ms: number;
  /** Time to first token in ms (streaming only). */
  ttftMs?: number;
}

export class OllamaClient {
  constructor(
    readonly url: string,
    readonly model: string,
    readonly numCtx: number,
  ) {}

  async chat(_opts: ChatOptions): Promise<ChatResult> {
    throw new Error("not implemented");
  }

  /** Streams content tokens; the final ChatResult is the generator's return value. */
  async *chatStream(_opts: ChatOptions): AsyncGenerator<string, ChatResult> {
    throw new Error("not implemented");
  }

  async status(): Promise<LlmStatus> {
    throw new Error("not implemented");
  }

  async *pull(_model: string, _signal?: AbortSignal): AsyncGenerator<PullProgress> {
    throw new Error("not implemented");
  }

  /** Loads the model with keep_alive; returns elapsed ms. */
  async warmup(): Promise<number> {
    throw new Error("not implemented");
  }
}
