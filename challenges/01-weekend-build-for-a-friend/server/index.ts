// Server entry. T0 minimal version; T1 owns it from here (static dist/ with SPA fallback, db init).
// `config` MUST stay the first import: it loads .env and disables Mastra telemetry before anything else loads.
import { config } from "./config";
import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { createApi } from "./routes/index";

const app = new Hono();
app.route("/api", createApi());

serve({ fetch: app.fetch, port: config.port, hostname: "127.0.0.1" }, (info) => {
  console.log(`rc-pit-companion server ${config.version} on http://localhost:${info.port}`);
});
