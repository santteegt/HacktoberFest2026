# AGENTS.md: tiger-data-pipeline

Instructions for agents working in `global-hack-week/tiger-data-pipeline/`. They add to [`../AGENTS.md`](../AGENTS.md) and the repo-level `AGENTS.md`.

## What this folder is

Hands-on tutorial: stream or poll market data from the **Twelve Data API** into **Tiger Data Cloud** (TimescaleDB), then visualize it in **self-hosted Grafana** (`docker compose`, image `grafana/grafana`).

## Stack

| Piece | Choice |
| --- | --- |
| Database | Tiger Cloud (not Compose Postgres) |
| Viz | Local Grafana via `docker-compose.yml` |
| Language | Python 3.12+ managed with `uv` |
| Market data | `twelvedata` + `websocket-client` |
| DB driver | `psycopg2-binary` |

## Local commands

```bash
docker compose up -d          # Grafana → http://localhost:3000
uv sync                       # restore .venv from uv.lock
uv run python main.py         # entrypoint (grows with the tutorial)
```

## Secrets

Use `.env` from `.env.example`. Never commit API keys or Tiger connection strings with passwords. Prefer Tiger MCP / OS keyring for DB passwords when querying services.

## After each meaningful step

Append to [`docs/CHALLENGE-MEMORY.md`](docs/CHALLENGE-MEMORY.md). Update [`README.md`](README.md) when run instructions change.

## Rules

1. Read this file before adding pipeline code or changing Compose.
2. Do not put a Postgres container in Compose unless the user asks — the store is Tiger Cloud.
3. Ask before claiming Tiger / MLH promo codes or installing sponsor skills.
