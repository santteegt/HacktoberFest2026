// Coach routes (T3): POST /api/coach/turn (SSE, see src/shared/events.ts), decide, outcome.
// T0 stub: 501 until T3 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.post("/coach/turn", notImplemented("coach"));
r.post("/coach/:runId/decide", notImplemented("coach"));
r.post("/coach/:runId/outcome", notImplemented("coach"));

export default r;
