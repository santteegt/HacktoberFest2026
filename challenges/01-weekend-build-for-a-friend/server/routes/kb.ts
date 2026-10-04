// KB routes (T2): GET /api/kb/search?q=&limit=3, GET /api/kb/chunk/:id. T0 stub: 501 until T2 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.get("/kb/search", notImplemented("kb"));
r.get("/kb/chunk/:id", notImplemented("kb"));

export default r;
