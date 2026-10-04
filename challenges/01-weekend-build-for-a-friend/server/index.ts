// Server entry (T1). Opens and migrates the vault database, then serves /api plus dist/ (SPA fallback).
// `config` MUST stay the first import: it loads .env and disables Mastra telemetry before anything else loads.
import { config } from "./config";
import { serve } from "@hono/node-server";
import { closeDb, openDb } from "./db";
import { createApp } from "./vault/app";

await openDb(config.vaultDbUrl);
const app = createApp();

const server = serve({ fetch: app.fetch, port: config.port, hostname: "127.0.0.1" }, (info) => {
  console.log(`rc-pit-companion server ${config.version} on http://localhost:${info.port}`);
});

const shutdown = () => {
  server.close();
  closeDb();
  process.exit(0);
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
