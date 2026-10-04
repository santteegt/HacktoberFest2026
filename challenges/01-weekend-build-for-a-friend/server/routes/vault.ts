// Vault routes (T1): sessions, setups (copy-on-write), runs, changes, saved setups, export/import, reset.
// Repo functions throw VaultError (mapped to `{ error, stage }` by server/vault/app.ts); bodies are zod-validated.
import { Hono } from "hono";
import { parseBody } from "../http";
import {
  AddRunBody,
  ApplySetupBody,
  CreateSessionBody,
  ImportBody,
  PatchChangeBody,
  PatchSessionBody,
  ResetBody,
  SaveSetupBody,
} from "../../src/shared/api";
import type { OkResponse } from "../../src/shared/api";
import * as repo from "../vault/repo";

const r = new Hono();

r.post("/sessions", async (c) => {
  const b = await parseBody(c, CreateSessionBody);
  if (!b.ok) return b.res;
  return c.json(await repo.createSession(b.data));
});
r.get("/sessions", async (c) => c.json(await repo.listSessions()));
r.get("/sessions/:id", async (c) => c.json(await repo.getSessionBundle(c.req.param("id"))));
r.patch("/sessions/:id", async (c) => {
  const b = await parseBody(c, PatchSessionBody);
  if (!b.ok) return b.res;
  return c.json(await repo.patchSession(c.req.param("id"), b.data));
});
r.post("/sessions/:id/setup", async (c) => {
  const b = await parseBody(c, ApplySetupBody);
  if (!b.ok) return b.res;
  const { values, ...meta } = b.data;
  return c.json(await repo.applySetupChanges(c.req.param("id"), values, meta));
});
r.get("/setups/:id", async (c) => c.json(await repo.getSetup(c.req.param("id"))));
r.post("/sessions/:id/runs", async (c) => {
  // The path id is the session; an old client's body `sessionId` is stripped by the schema and ignored.
  const b = await parseBody(c, AddRunBody);
  if (!b.ok) return b.res;
  return c.json(await repo.addRun(c.req.param("id"), b.data));
});
r.patch("/changes/:id", async (c) => {
  const b = await parseBody(c, PatchChangeBody);
  if (!b.ok) return b.res;
  return c.json(await repo.setChangeOutcome(c.req.param("id"), b.data.outcome, b.data.outcomeRunId));
});
r.get("/saved", async (c) => c.json(await repo.listSaved()));
r.post("/saved", async (c) => {
  const b = await parseBody(c, SaveSetupBody);
  if (!b.ok) return b.res;
  return c.json(await repo.saveSetup(b.data));
});
r.delete("/saved/:id", async (c) => {
  await repo.deleteSaved(c.req.param("id"));
  return c.json<OkResponse>({ ok: true });
});
r.get("/export", async (c) => c.json(await repo.exportAll()));
r.post("/import", async (c) => {
  const b = await parseBody(c, ImportBody);
  if (!b.ok) return b.res;
  return c.json(await repo.importAll(b.data));
});
r.post("/reset", async (c) => {
  const b = await parseBody(c, ResetBody);
  if (!b.ok) return b.res;
  await repo.resetAll();
  return c.json<OkResponse>({ ok: true });
});

export default r;
