// Server entry (T1). Opens and migrates the vault database, then serves /api plus dist/ (SPA fallback).
// `config` MUST stay the first import: it loads .env and disables Mastra telemetry before anything else loads.
import { config } from "./config";
import { existsSync } from "node:fs";
import { serve } from "@hono/node-server";
import { closeDb, openDb } from "./db";
import { createApp } from "./vault/app";
import { kbStats } from "./kb/search";

// The knowledge index is a generated file (gitignored). Check it before anything else so a fresh clone
// gets one clear line instead of a stack trace in the middle of a coach turn (T10).
if (!existsSync(config.paths.kbJson)) {
  console.error(
    "rc-pit-companion: the knowledge index data/generated/kb.json is missing.\n" +
      "  Run `npm run kb:build` (npm install and npm start also build it), then start the server again.",
  );
  process.exit(1);
}
try {
  const kb = kbStats();
  console.log(`knowledge index: ${kb.pages} pages, ${kb.chunks} chunks`);
} catch (e) {
  console.error(
    `rc-pit-companion: data/generated/kb.json could not be loaded (${(e as Error).message.split("\n")[0]}).\n` +
      "  Run `npm run kb:build` to rebuild it, then start the server again.",
  );
  process.exit(1);
}

await openDb(config.vaultDbUrl);
const app = createApp();
console.log(`coach engine: ${process.env.COACH_ENGINE === "plain" ? "plain (COACH_ENGINE=plain)" : "mastra"}`);

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
