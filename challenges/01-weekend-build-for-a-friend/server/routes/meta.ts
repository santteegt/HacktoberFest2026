// GET /api/meta (T1): params, symptoms, levers, prechecks, kbStats (data read through server/engine/data.ts).
import { Hono } from "hono";
import { loadMeta } from "../vault/meta";

const r = new Hono();
r.get("/meta", (c) => c.json(loadMeta()));

export default r;
