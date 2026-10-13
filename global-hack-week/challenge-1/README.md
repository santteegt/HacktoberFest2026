# Skyline Weather (challenge-1)

**Type:** challenge mini-app  
**Event:** [Global Hack Week: Hacktoberfest](https://events.mlh.io/events/14553-global-hack-week-hacktoberfest)  
**Dashboard:** <https://ghw.mlh.io/challenges>  
**Stack:** Vite + React + TypeScript PWA · [Open-Meteo](https://open-meteo.com/) (no API key)

A progressive web app that shows current conditions and a 5-day forecast for the user's position. If location access is denied or unavailable, a city search (Open-Meteo Geocoding API) takes over.

## Features

- Requests geolocation on open; falls back to city search
- Two summary cards: hero conditions + atmosphere details
- Interactive 5-day forecast with **Daily** / **Hourly** intervals
- Installable PWA; `npm run build` emits a static `dist/` artifact
- Offline-friendly caching for Open-Meteo responses via the service worker

## Quick start

```bash
cd global-hack-week/challenge-1
npm install
npm run dev
```

Open the printed local URL (usually `http://localhost:5173`). Allow location, or search for a city.

## Static artifact

```bash
npm run build
npm run preview   # serves ./dist
```

Or any static host / local server:

```bash
npx serve dist
# or: python3 -m http.server -d dist 8080
```

Deploy the contents of `dist/` to GitHub Pages, Netlify, Cloudflare Pages, S3, etc. No backend or secrets required for the free Open-Meteo non-commercial tier.

## Open-Meteo fields used

| Layer | Variables |
| --- | --- |
| Current | temperature, apparent temperature, humidity, weather code, cloud cover, pressure, wind speed/direction/gusts, precipitation, is_day |
| Hourly | temperature, apparent temperature, humidity, precip probability/amount, weather code, wind, cloud cover |
| Daily (5 days) | high/low (and feels-like), weather code, precip sum + max probability, wind max, UV index max, sunrise/sunset |
| Geocoding | city / admin1 / country → lat/lon |

Docs: <https://open-meteo.com/en/docs> · Geocoding: <https://open-meteo.com/en/docs/geocoding-api>

## Folder layout

```
challenge-1/
  AGENTS.md                 Agent-facing design decisions
  README.md                 This file
  LICENSE                   MIT
  docs/CHALLENGE-MEMORY.md  Running log
  public/                   Favicon + PWA icons
  src/
    api/                    Open-Meteo forecast + geocoding clients
    components/             Search, current cards, forecast viz
    hooks/                  Geolocation + weather fetch
    lib/                    WMO codes + formatting
```

## Notes for agents

Read [`AGENTS.md`](AGENTS.md) before changing architecture or API usage. Append to [`docs/CHALLENGE-MEMORY.md`](docs/CHALLENGE-MEMORY.md) when decisions or measurements land.
