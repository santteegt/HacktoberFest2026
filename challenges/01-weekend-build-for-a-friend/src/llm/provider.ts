// One interface so the model runtime can be swapped without touching the app.
// v1 backend: Ollama on the laptop (decided 2026-10-04 after the phone spike, see
// docs/PHONE-SPIKE.md). The in-browser LiteRT-LM path was only used for that spike.

export type LlmBackend = "ollama";

export interface LlmStatus {
  backend: LlmBackend;
  ready: boolean;
  modelId?: string;
  detail?: string; // e.g. download progress, or why it is unavailable
}

export interface JsonRequest {
  system: string;
  user: string;
  /** JSON Schema; Ollama enforces it via `format`, other backends validate after the fact. */
  schema: object;
  temperature?: number;
}

export interface LlmProvider {
  readonly backend: LlmBackend;
  status(): Promise<LlmStatus>;
  /** Make sure the model is available locally (pull it if missing); resolves when it can run with the network off. */
  prepare(onProgress?: (fraction: number) => void): Promise<void>;
  generateJson<T>(req: JsonRequest): Promise<T>;
  generateText(req: Omit<JsonRequest, "schema">): AsyncIterable<string>;
}
