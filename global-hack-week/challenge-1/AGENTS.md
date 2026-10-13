# AGENTS.md: challenge-1 (Skyline Weather)

Instructions for any AI coding agent working in `global-hack-week/challenge-1/`. They add to [`../AGENTS.md`](../AGENTS.md) and the repo-level `AGENTS.md`.

## What this folder is

GHW mini-app: a **static Progressive Web App** for local weather and a 5-day forecast.

- **Product name in UI:** Skyline
- **Folder slug:** `challenge-1` (keep the folder name; rename only if the user asks)
- **Not a DEV Challenge.** Do not scaffold under `challenges/` or publish a DEV post unless the user explicitly asks.

## Product requirements (source of truth)

1. On open, request location services.
2. If location is denied/unavailable, show a city search bar and still load weather.
3. UX: weather-like UI with **two cards** summarizing current conditions, plus an **interactive 5-day forecast** that toggles **hourly / daily**.
4. Weather data: **Open-Meteo** free tier (no API key for non-commercial use).
5. Ship as a **static artifact** (`dist/` from Vite).

## Design decisions

| Decision | Choice | Why / rejected |
| --- | --- | --- |
| Framework | Vite + React + TypeScript | Fast static build, typed API mapping, easy PWA plugin. Rejected Next.js (needs adapter / not pure static by default) and plain HTML (harder interactive forecast). |
| PWA | `vite-plugin-pwa` + Workbox | Manifest + service worker from the same build; `NetworkFirst` for Open-Meteo. |
| Weather API | Open-Meteo Forecast + Geocoding | Free, CORS-friendly, no key, current + hourly + daily in one call. Rejected OpenWeatherMap (key + free-tier limits). |
| Forecast length | `forecast_days=5` | Matches the product brief. |
| Location fallback | Geolocation first → city search always available | Search is elevated when geo fails; users with geo can still search and return via “Use my location”. |
| Visual system | Deep coastal sky palette, Newsreader + Figtree | Weather atmosphere without purple-gradient / cream-serif AI defaults. Cards used only for current summary + forecast panel (interaction containers). |

## Open-Meteo mapping (keep in sync with UI)

Prefer rich-but-useful fields; avoid dumping every model variable into the UI.

**Current card (hero):** `temperature_2m`, `apparent_temperature`, `weather_code`, `is_day`, `time`

**Atmosphere card:** `relative_humidity_2m`, `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, `precipitation`, `cloud_cover`, `pressure_msl`

**Hourly viz:** temperature series + precip probability; detail panel uses humidity, precip amount, wind, cloud cover, weather code

**Daily viz:** `temperature_2m_max/min`, weather code, precip sum + max probability; detail adds feels-like range, wind max, `uv_index_max`, sunrise/sunset

**Timezone:** `timezone=auto` so labels match the place, not the browser alone.

WMO codes → labels/icons live in `src/lib/weatherCodes.ts`.

## Commands

```bash
npm install
npm run dev       # local SPA
npm run build     # static dist/
npm run preview   # smoke-test dist/
npm run lint
```

## Verification checklist

- [ ] `npm run build` succeeds and produces `dist/index.html` + SW assets
- [ ] With location allowed: current cards + forecast render for coordinates
- [ ] With location blocked: city search finds a place and weather loads
- [ ] Daily ↔ Hourly toggle updates the chart and detail panel
- [ ] No secrets in repo (Open-Meteo needs none for this app)

## Rules

1. Read this file before changing stack, API params, or PWA caching.
2. Keep `docs/CHALLENGE-MEMORY.md` append-only for decisions, failures, and measurements.
3. Do not commit `.env` with secrets; none are required today. If a future change needs keys, add `.env.example` only.
4. Do not submit to MLH / claim offers / publish DEV posts without an explicit yes in the current session.
5. Prefer absolute paths when running scripts from the monorepo root.
