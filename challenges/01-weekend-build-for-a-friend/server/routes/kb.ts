// KB routes (T2): GET /api/kb/search?q=&limit=3, GET /api/kb/chunk/:id.
import { Hono } from "hono";
import { apiError } from "../http";
import { getChunk, search } from "../kb/search";

const r = new Hono();

r.get("/kb/search", (c) => {
  const q = (c.req.query("q") ?? "").trim();
  if (!q) return apiError(c, 400, "q is required", "kb");
  const n = Number.parseInt(c.req.query("limit") ?? "3", 10);
  const limit = Number.isFinite(n) ? Math.min(10, Math.max(1, n)) : 3;
  return c.json(search(q, limit));
});

r.get("/kb/chunk/:id", (c) => {
  const chunk = getChunk(c.req.param("id"));
  return chunk ? c.json(chunk) : apiError(c, 404, "no such chunk", "kb");
});

export default r;
