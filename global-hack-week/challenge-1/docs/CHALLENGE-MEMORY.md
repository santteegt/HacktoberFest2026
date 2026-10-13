# Challenge memory: Skyline Weather (GHW challenge-1)

Running log of decisions and verification for this GHW mini-app. **Append when it happens.** Never delete an entry; mark wrong ones `SUPERSEDED by <date>`. No secrets.

## Entry format

`- YYYY-MM-DD HH:MMZ [TAG] what happened. Evidence: <file, command, link>.`

Tags: `DECISION` · `FINDING` · `MEASURE` · `FAILED` · `HONEST` · `PROCESS` · `PRIOR-WORK` · `TODO-REPORT`

## Claims the post / README may make / must not make

| May claim (with evidence) | Must NOT claim |
| --- | --- |
| Static Vite PWA using Open-Meteo without an API key | That MLH awarded points until confirmed on the dashboard |
| Geolocation with city-search fallback | Commercial Open-Meteo SLA / paid tier usage |
| 5-day daily + 48h hourly interactive forecast | Accuracy guarantees vs a national weather service |

## Log

- 2026-10-13 22:45Z [DECISION] Scaffold `global-hack-week/challenge-1` as Vite + React + TypeScript + `vite-plugin-pwa` so the deliverable is a static `dist/` artifact. Rejected Next.js (not pure-static by default) and OpenWeatherMap (API key). Evidence: `AGENTS.md`, `package.json`.
- 2026-10-13 22:45Z [DECISION] Open-Meteo fields: current (temp, feels-like, humidity, WMO code, clouds, pressure, wind+gusts, precip, is_day); hourly (temp, feels-like, humidity, precip prob/amount, code, wind, clouds); daily 5d (high/low, feels, code, precip sum/prob, wind max, UV max, sunrise/sunset); geocoding for city fallback. Evidence: `src/api/openMeteo.ts`, Open-Meteo docs.
- 2026-10-13 22:45Z [PROCESS] Product UI named Skyline; folder kept as `challenge-1` per user request. Evidence: `README.md`, `index.html` title.
- 2026-10-13 22:58Z [MEASURE] `npm run build` produces static `dist/` including `index.html`, `manifest.webmanifest`, `sw.js`, `workbox-*.js` (vite-plugin-pwa generateSW, 8 precache entries / ~248 KiB). Machine: local darwin; method: production Vite build. Evidence: build log 2026-10-13.
- 2026-10-13 22:58Z [MEASURE] Open-Meteo forecast for Berlin returned current temp + daily series; geocoding `Berlin` → id 2950159. Full app parameter set for NYC returned 5 daily days. Evidence: curl / node fetch against api.open-meteo.com and geocoding-api.open-meteo.com.
- 2026-10-13 22:58Z [FINDING] `vite-plugin-pwa` v2 `generateSW` can hang under the Cursor sandbox; build completes (including `sw.js`) with full permissions. Evidence: sandbox vs `required_permissions: all` rebuild comparison.
- 2026-10-13 22:58Z [HONEST] Browser geolocation UX was not interactively clicked in this session; city-search and coordinate forecast paths were verified via API. Location permission flow is implemented in `useGeolocation`.
- 2026-10-14 00:05Z [DECISION] Hourly forecast: drop `1fr` column sizing (it prevented overflow scroll), use fixed 68px columns in a horizontal scroller, show the full remaining 5-day hourly series with day labels, and overlay an SVG temperature polyline through each interval. Evidence: user feedback; `ForecastViz.tsx`, `App.css`.
- 2026-10-14 00:10Z [FINDING] Hourly scroll still failed because the scroller grew with its content (`min-width: auto` on CSS grid items). Fix: `min-width: 0` / `max-width: 100%` on `.shell` and `.forecast`, plus drag-to-scroll. Temperature “zigzag” came from line points on column edges (`i/(n-1)`) instead of centers, plus sharp polylines — switched to center x and Catmull-Rom smoothing. Evidence: user feedback follow-up.
- 2026-10-14 00:15Z [PROCESS] Scrubbed Cursor transcript (session `5c05989d-30b1-4a81-8667-ca6d76fc79cc`) and submitted to DEV as unpublished agent session “Skyline Weather PWA — GHW challenge-1 (Open-Meteo)” (`skyline-weather-pwa-ghw-challenge-1-open-meteo-3k1fdx`, 10 messages). Evidence: https://dev.to/agent_sessions/skyline-weather-pwa-ghw-challenge-1-open-meteo-3k1fdx
