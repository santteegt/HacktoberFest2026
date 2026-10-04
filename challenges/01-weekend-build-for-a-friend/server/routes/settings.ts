// GET/PUT /api/settings (T1). T0 stub: 501 until T1 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.get("/settings", notImplemented("settings"));
r.put("/settings", notImplemented("settings"));

export default r;
