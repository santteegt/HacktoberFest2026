/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import basicSsl from "@vitejs/plugin-basic-ssl";

// HTTPS=1 serves a self-signed cert so a phone on the LAN gets a secure context.
// Only used by `npm run spike` (the phone-spike record in spike.html / src/spike/).
const https = process.env.HTTPS === "1";

// The app is a local Node server (server/, port 8787) plus this Preact UI.
// In dev, Vite proxies /api to the server (127.0.0.1: the server binds IPv4 loopback only); in production the server serves dist/.
// No service worker: on a localhost app it only adds stale-cache bugs.
const apiPort = Number(process.env.PORT ?? 8787);

export default defineConfig({
  plugins: [...(https ? [basicSsl()] : []), preact()],
  server: {
    host: https ? true : undefined,
    port: Number(process.env.UI_PORT ?? 5173), // parallel agents set UI_PORT/PORT to avoid clashes
    strictPort: true,
    proxy: {
      "/api": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: false },
    },
  },
  test: {
    include: ["tests/**/*.test.ts"],
    environment: "node",
  },
});
