// LLM routes (T3): GET /api/llm/status, POST /api/llm/pull (SSE), POST /api/llm/warmup.
// T0 stub: 501 until T3 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.get("/llm/status", notImplemented("llm"));
r.post("/llm/pull", notImplemented("llm"));
r.post("/llm/warmup", notImplemented("llm"));

export default r;
