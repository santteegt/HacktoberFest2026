// Server configuration: env + settings defaults. FROZEN (T0; only T7/T10 edit).
//
// IMPORTANT: import this module FIRST in server/index.ts (and in any script that touches Mastra).
// ES modules evaluate imports in order, so this body runs before any later import can load
// @mastra/core, which reads MASTRA_TELEMETRY_DISABLED at load time.
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { Settings } from "../src/shared/schemas";
import type { Settings as SettingsT } from "../src/shared/types";

/** Project root (the challenge folder), independent of the process cwd. */
export const ROOT = fileURLToPath(new URL("..", import.meta.url));

// 1. Load .env when present. process.loadEnvFile never overrides variables already set in the shell.
const envFile = join(ROOT, ".env");
if (existsSync(envFile)) process.loadEnvFile(envFile);

// 2. Mastra telemetry is on by default; force it off so nothing leaves the machine (offline/privacy claim).
process.env.MASTRA_TELEMETRY_DISABLED = "1";

const env = (name: string, ...fallbacks: string[]): string | undefined => {
  for (const key of [name, ...fallbacks]) {
    const v = process.env[key];
    if (v !== undefined && v !== "") return v;
  }
  return undefined;
};

const intEnv = (value: string | undefined, dflt: number): number => {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : dflt;
};

const pkg = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")) as { version: string };
const varDir = join(ROOT, "var");

export const config = {
  version: pkg.version,
  port: intEnv(env("PORT"), 8787),
  /** True when NODE_ENV=production; T1 also serves dist/ whenever dist/index.html exists. */
  isProd: process.env.NODE_ENV === "production",
  ollamaUrl: (env("OLLAMA_URL", "VITE_OLLAMA_URL") ?? "http://localhost:11434").replace(/\/+$/, ""),
  ollamaModel: env("OLLAMA_MODEL", "VITE_OLLAMA_MODEL") ?? "gemma4:e4b-it-qat",
  numCtx: intEnv(env("OLLAMA_NUM_CTX", "VITE_OLLAMA_NUM_CTX"), 4096),
  paths: {
    root: ROOT,
    data: join(ROOT, "data"),
    kbJson: join(ROOT, "data", "generated", "kb.json"),
    dist: join(ROOT, "dist"),
    var: varDir,
    backups: join(varDir, "backups"),
  },
  /** libsql URLs (absolute, so the server works from any cwd). */
  vaultDbUrl: env("PIT_DB_URL") ?? `file:${join(varDir, "pit.db")}`,
  mastraDbUrl: env("MASTRA_DB_URL") ?? `file:${join(varDir, "mastra.db")}`,
} as const;

/** Settings used when the settings table is empty; env decides the Ollama fields. */
export const defaultSettings: SettingsT = Settings.parse({
  ollamaUrl: config.ollamaUrl,
  model: config.ollamaModel,
  numCtx: config.numCtx,
});
