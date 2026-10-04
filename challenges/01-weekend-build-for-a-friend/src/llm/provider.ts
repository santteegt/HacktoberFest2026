// One interface, several backends. The app never imports a runtime directly.
//  - "litert-web": Gemma 4 E2B/E4B on-device via WebGPU (phone or laptop browser)
//  - "ollama":     Gemma 4 on a laptop running Ollama (localhost, or LAN if HTTPS allows)

export type LlmBackend = "litert-web" | "ollama";

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
  /** Download and cache weights once; resolves when the model can run with the network off. */
  prepare(onProgress?: (fraction: number) => void): Promise<void>;
  generateJson<T>(req: JsonRequest): Promise<T>;
  generateText(req: Omit<JsonRequest, "schema">): AsyncIterable<string>;
}
