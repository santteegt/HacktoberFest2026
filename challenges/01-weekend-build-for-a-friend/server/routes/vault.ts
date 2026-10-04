// Vault routes (T1): sessions, setups (copy-on-write), runs, changes, saved setups, export/import, reset.
// T0 stub: every endpoint answers 501 until T1 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.post("/sessions", notImplemented("vault"));
r.get("/sessions", notImplemented("vault"));
r.get("/sessions/:id", notImplemented("vault"));
r.patch("/sessions/:id", notImplemented("vault"));
r.post("/sessions/:id/setup", notImplemented("vault"));
r.post("/sessions/:id/runs", notImplemented("vault"));
r.patch("/changes/:id", notImplemented("vault"));
r.get("/saved", notImplemented("vault"));
r.post("/saved", notImplemented("vault"));
r.delete("/saved/:id", notImplemented("vault"));
r.get("/export", notImplemented("vault"));
r.post("/import", notImplemented("vault"));
r.post("/reset", notImplemented("vault"));

export default r;
