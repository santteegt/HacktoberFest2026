// GET /api/meta (T1): params, symptoms, levers, prechecks, kbStats (data read through server/engine/data.ts).
// T0 stub: 501 until T1 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.get("/meta", notImplemented("meta"));

export default r;
