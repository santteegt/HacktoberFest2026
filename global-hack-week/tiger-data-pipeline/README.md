# Tiger Data pipeline: Twelve Data → Tiger Cloud → Grafana

**Type:** hands-on session / tutorial  
**Stack:** Tiger Data Cloud (TimescaleDB) · self-hosted Grafana · Python 3 · Twelve Data API  
**Started:** 2026-10-16

Ingest market time-series from Twelve Data into Tiger Cloud, then visualize it in a local Grafana instance.

## Prerequisites

- Docker / Docker Compose
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- A Tiger Cloud service and a [Twelve Data](https://twelvedata.com/) API key

## Quick start

### 1. Grafana (Docker Compose)

```bash
cd global-hack-week/tiger-data-pipeline
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000) — default login `admin` / `admin` (change on first login).

Stop with `docker compose down`. Data persists in the `grafana-data` volume.

### 2. Python project (uv)

Already initialized. Recreate the venv and install deps:

```bash
uv sync
```

Activate (optional; `uv run` works without it):

```bash
source .venv/bin/activate
```

Dependencies: `twelvedata`, `websocket-client`, `psycopg2-binary`.

### 3. Secrets

```bash
cp .env.example .env
# fill TWELVEDATA_API_KEY and DATABASE_URL
```

Never commit `.env`.

## Folder layout

```
tiger-data-pipeline/
  docker-compose.yml    Grafana (grafana/grafana)
  pyproject.toml        uv project + deps
  uv.lock
  main.py               placeholder entrypoint
  pipeline/ingest.py    Twelve Data → Tiger Cloud streamer
  pipeline/ws_smoke.py  websocket-only smoke (no DB)
  .env.example
  docs/
    CHALLENGE-MEMORY.md
```

Stream ticks:

```bash
uv run --env-file .env python pipeline/ingest.py
```

Do not name a local module `websocket.py` — it shadows the `websocket-client` package when you run a script from `pipeline/`.

## Next steps

- Add a Grafana PostgreSQL/Timescale datasource pointing at Tiger Cloud
- Dashboard panels on `crypto_ticks`
