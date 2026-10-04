// Coach routes (T3): POST /api/coach/turn (SSE, see src/shared/events.ts), decide, outcome.
// Event order on /coach/turn: classified, then refusal (end) or precheck, suggestion, token*, explained,
// suspended. `error` may arrive at any point and ends the stream.
import { Hono, type Context } from "hono";
import { streamSSE } from "hono/streaming";
import { apiError, parseBody } from "../http";
import { DecideBody, OutcomeBody } from "../../src/shared/api";
import { CoachTurnInput } from "../../src/shared/schemas";
import type { CoachEvent } from "../../src/shared/events";
import { getCoachEngine } from "../coach/instance";
import { CoachError } from "../coach/steps";
import { VaultError } from "../vault/errors";

function fail(c: Context, e: unknown, stage: string) {
  if (e instanceof CoachError) return apiError(c, e.status, e.message, e.stage);
  if (e instanceof VaultError) return apiError(c, e.status, e.message, e.stage);
  console.error(`[coach] ${stage} failed:`, e);
  return apiError(c, 500, (e as Error).message ?? String(e), stage);
}

const r = new Hono();

r.post("/coach/turn", async (c) => {
  const b = await parseBody(c, CoachTurnInput);
  if (!b.ok) return b.res;
  const engine = getCoachEngine();
  return streamSSE(c, async (stream) => {
    let closed = false;
    stream.onAbort(() => {
      closed = true;
    });
    const emit = async (e: CoachEvent) => {
      if (closed) return; // client went away: keep the run going (it is persisted), stop writing
      await stream.writeSSE({ event: e.event, data: JSON.stringify(e.data) });
    };
    try {
      const t0 = Date.now();
      await engine.start(b.data, emit);
      // One line per turn so the log shows which engine really ran (Mastra claim; T10).
      console.log(`[coach] turn finished on the ${engine.kind} engine in ${Date.now() - t0} ms`);
    } catch (e) {
      const stage = e instanceof CoachError ? e.stage : e instanceof VaultError ? e.stage : "coach";
      console.error(`[coach] turn failed (${engine.kind}):`, e);
      await emit({ event: "error", data: { message: (e as Error).message ?? String(e), stage } });
    }
  });
});

r.post("/coach/:runId/decide", async (c) => {
  const b = await parseBody(c, DecideBody);
  if (!b.ok) return b.res;
  try {
    return c.json(await getCoachEngine().decide(c.req.param("runId"), b.data));
  } catch (e) {
    return fail(c, e, "decide");
  }
});

r.post("/coach/:runId/outcome", async (c) => {
  const b = await parseBody(c, OutcomeBody);
  if (!b.ok) return b.res;
  try {
    return c.json(await getCoachEngine().outcome(c.req.param("runId"), b.data));
  } catch (e) {
    return fail(c, e, "outcome");
  }
});

export default r;
