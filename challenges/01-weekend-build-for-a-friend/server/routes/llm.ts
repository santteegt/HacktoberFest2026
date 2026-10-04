// LLM routes (T3): GET /api/llm/status, POST /api/llm/pull (SSE), POST /api/llm/warmup.
// Settings (ollamaUrl, model, numCtx) come from the vault settings table, falling back to env defaults.
import { Hono } from "hono";
import { streamSSE } from "hono/streaming";
import { apiError, parseBody } from "../http";
import { PullBody, type WarmupResponse } from "../../src/shared/api";
import type { PullEvent } from "../../src/shared/events";
import { ollamaFor, OllamaError } from "../llm/ollama";
import { getCoachDeps } from "../coach/steps";

const client = async () => ollamaFor(await getCoachDeps().settings());

const r = new Hono();

r.get("/llm/status", async (c) => c.json(await (await client()).status()));

r.post("/llm/pull", async (c) => {
  const b = await parseBody(c, PullBody);
  if (!b.ok) return b.res;
  const llm = await client();
  return streamSSE(c, async (stream) => {
    const ac = new AbortController();
    stream.onAbort(() => ac.abort()); // closing the tab stops the download
    const send = (e: PullEvent) => stream.writeSSE({ event: e.event, data: JSON.stringify(e.data) });
    try {
      for await (const p of llm.pull(b.data.model, ac.signal)) await send({ event: "progress", data: p });
      await send({ event: "done", data: { model: b.data.model } });
    } catch (e) {
      if (!ac.signal.aborted) await send({ event: "error", data: { message: (e as Error).message, stage: "pull" } });
    }
  });
});

r.post("/llm/warmup", async (c) => {
  try {
    const ms = await (await client()).warmup();
    return c.json<WarmupResponse>({ ms });
  } catch (e) {
    const unreachable = e instanceof OllamaError && e.unreachable;
    return apiError(c, unreachable ? 503 : 502, (e as Error).message, "warmup");
  }
});

export default r;
