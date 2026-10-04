// Mounts every route module under /api. FROZEN (T0; only T7/T10 edit).
// Each module is a Hono sub-app that declares its own full paths relative to /api
// (e.g. vault.ts declares "/sessions"), so owners never need to edit this file.
import { Hono } from "hono";
import { config } from "../config";
import { apiError } from "../http";
import type { HealthResponse } from "../../src/shared/api";
import vault from "./vault";
import meta from "./meta";
import settings from "./settings";
import kb from "./kb";
import coach from "./coach";
import llm from "./llm";
import analysis from "./analysis";
import speak from "./speak";

export function createApi(): Hono {
  const api = new Hono();
  api.get("/health", (c) => c.json<HealthResponse>({ ok: true, version: config.version }));
  for (const mod of [meta, settings, vault, kb, coach, llm, analysis, speak]) api.route("/", mod);
  // Last: unknown /api paths get the contract error shape (a sub-app notFound() is ignored once mounted).
  api.all("*", (c) => apiError(c, 404, "no such endpoint", "route"));
  return api;
}
