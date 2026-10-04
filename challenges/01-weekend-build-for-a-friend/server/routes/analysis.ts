// Analysis routes (T8): similar setups, run comparison, param history. All read-only.
// The analysis functions are pure; this module reads the vault once per request (exportAll) and hands them plain objects.
import { Hono } from "hono";
import { apiError } from "../http";
import { compareRuns } from "../analysis/compare";
import { paramHistory } from "../analysis/history";
import { similarSetups } from "../analysis/similar";
import { loadLevers, loadParams } from "../engine/data";
import { exportAll } from "../vault/repo";
import type { RunBundle, Setup } from "../../src/shared/types";

const r = new Hono();

r.get("/analysis/similar", async (c) => {
  const sessionId = c.req.query("sessionId");
  if (!sessionId) return apiError(c, 400, "sessionId is required", "analysis");
  const { tables } = await exportAll();
  const session = tables.sessions.find((s) => s.id === sessionId);
  if (!session) return apiError(c, 404, "no such session", "analysis");
  const setups = new Map<string, Setup>(tables.setups.map((s) => [s.id, s]));
  const current = setups.get(session.currentSetupId)?.values ?? {};
  return c.json(similarSetups(session.conditions, tables.savedSetups, current, setups));
});

r.get("/analysis/compare", async (c) => {
  const runA = c.req.query("runA");
  const runB = c.req.query("runB");
  if (!runA || !runB) return apiError(c, 400, "runA and runB are required", "analysis");
  const { tables } = await exportAll();
  const setups = new Map<string, Setup>(tables.setups.map((s) => [s.id, s]));
  const bundle = (id: string): RunBundle | string => {
    const run = tables.runs.find((x) => x.id === id);
    if (!run) return `no such run: ${id}`;
    const session = tables.sessions.find((s) => s.id === run.sessionId);
    const setup = setups.get(run.setupId);
    if (!session || !setup) return `run ${id} is missing its session or setup`;
    return { run, setup, session };
  };
  const a = bundle(runA);
  const b = bundle(runB);
  if (typeof a === "string") return apiError(c, 404, a, "analysis");
  if (typeof b === "string") return apiError(c, 404, b, "analysis");
  return c.json(compareRuns(a, b, { params: loadParams().params, levers: loadLevers() }));
});

r.get("/analysis/history", async (c) => {
  const { tables } = await exportAll();
  return c.json(paramHistory(tables.changes));
});

export default r;
