import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";
import basicSsl from "@vitejs/plugin-basic-ssl";

// HTTPS=1 serves a self-signed cert so a phone on the LAN gets a secure context
// (WebGPU, microphone and service workers all require one). Used by `npm run spike`.
const https = process.env.HTTPS === "1";

// Model weights are NOT precached by the service worker: they are fetched once into
// Cache Storage / OPFS by src/llm so the app shell stays small and updates stay fast.
export default defineConfig({
  server: { host: https ? true : undefined },
  plugins: [
    ...(https ? [basicSsl()] : []),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/icon.svg"],
      manifest: {
        name: "RC Pit Companion",
        short_name: "Pit Companion",
        description: "Offline, voice-first setup coach and setup vault for 1/10 touring car.",
        theme_color: "#0f1419",
        background_color: "#0f1419",
        display: "standalone",
        orientation: "portrait",
        start_url: "/",
        icons: [
          { src: "icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: { globPatterns: ["**/*.{js,css,html,svg,png,json}"], globIgnores: ["litert-wasm/**"] },
    }),
  ],
});
