// Builds the Hono app: /api routes, error mapping, and static serving of dist/ with SPA fallback (T1).
// Kept out of server/index.ts so tests can call createApp().request(...) without starting a listener.
import { existsSync, statSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { extname, join, resolve, sep } from "node:path";
import { Hono } from "hono";
import { HTTPException } from "hono/http-exception";
import { config } from "../config";
import { apiError } from "../http";
import { createApi } from "../routes/index";
import { VaultError } from "./errors";

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webmanifest": "application/manifest+json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".wasm": "application/wasm",
  ".txt": "text/plain; charset=utf-8",
  ".map": "application/json",
};

export function createApp(distDir: string = config.paths.dist): Hono {
  const app = new Hono();

  app.onError((err, c) => {
    if (err instanceof VaultError) return apiError(c, err.status, err.message, err.stage);
    if (err instanceof HTTPException) return apiError(c, err.status, err.message, "http");
    console.error(err);
    return apiError(c, 500, err instanceof Error ? err.message : "internal error", "server");
  });

  app.route("/api", createApi());

  // Static dist/ with SPA fallback. Checked per request, so a build made while the server runs is picked up.
  app.get("*", async (c) => {
    const index = join(distDir, "index.html");
    if (!existsSync(index)) return apiError(c, 404, "UI not built: run `npm run build` or use `npm run dev`", "static");
    const root = resolve(distDir);
    let rel: string;
    try {
      rel = decodeURIComponent(new URL(c.req.url).pathname);
    } catch {
      return apiError(c, 400, "bad path", "static");
    }
    const file = resolve(root, "." + rel);
    const inside = file === root || file.startsWith(root + sep);
    if (inside && existsSync(file) && statSync(file).isFile()) {
      const hashed = rel.startsWith("/assets/");
      return new Response(new Uint8Array(await readFile(file)), {
        headers: {
          "content-type": MIME[extname(file).toLowerCase()] ?? "application/octet-stream",
          "cache-control": hashed ? "public, max-age=31536000, immutable" : "no-cache",
        },
      });
    }
    // Missing asset (has an extension): a real 404. Anything else is a client-side route: index.html.
    if (extname(rel) !== "") return apiError(c, 404, "not found", "static");
    return new Response(new Uint8Array(await readFile(index)), {
      headers: { "content-type": MIME[".html"]!, "cache-control": "no-cache" },
    });
  });

  return app;
}
