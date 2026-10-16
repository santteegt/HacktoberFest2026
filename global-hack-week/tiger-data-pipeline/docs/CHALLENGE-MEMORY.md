# Challenge memory: Tiger Data pipeline (Twelve Data → Tiger Cloud → Grafana)

Running log of decisions and results for this GHW hands-on tutorial. **Append when it happens.** Never delete an entry; mark wrong ones `SUPERSEDED by <date>`. No secrets.

## Entry format

`- YYYY-MM-DD HH:MMZ [TAG] what happened or was learned. Evidence: <file, commit, command, link, or measurement context>.`

Tags: `DECISION` · `FINDING` · `MEASURE` · `FAILED` · `HONEST` · `PROCESS` · `QUOTE` · `PRIOR-WORK` · `PARTNER` · `TODO-REPORT`

## Claims the post may make / must not make

| May claim (with evidence) | Must NOT claim |
| --- | --- |
| Scaffolded Grafana via docker compose + uv Python project with Twelve Data / Postgres clients | Pipeline end-to-end ingest or live dashboards (not built yet) |
| Diagnosed why `crypto_ticks` stayed empty: batch gate + partial WS subscription | That the DB/driver path was broken (single-row insert succeeded) |
| Patched pipeline for smaller batches + Ctrl+C flush; smoke insert verified | Live multi-symbol free-tier reliability without watching subscribe-status |

## Log

- 2026-10-16 05:10Z [PROCESS] Scaffolded `global-hack-week/tiger-data-pipeline`: `docker-compose.yml` (image `grafana/grafana`, port 3000), `uv init` with Python 3.12, installed `twelvedata`, `websocket-client`, `psycopg2-binary`. Evidence: `pyproject.toml`, `uv.lock`, `docker-compose.yml`.
- 2026-10-16 05:10Z [DECISION] Self-host Grafana in Compose rather than Grafana Cloud so the tutorial stays local + Tiger Cloud only for the DB. Rejected bundling Postgres in Compose because the target store is Tiger Data Cloud.
- 2026-10-16 05:48Z [FINDING] `crypto_ticks` exists on Tiger Cloud but had 0 rows while the WS was running. DB connect + a one-row `execute_values` insert succeeded (`sslmode=require`). Root cause of "not ingesting": `MAX_BATCH_SIZE=100` with no flush of a partial batch on Ctrl+C, so nothing is written until 100 `price` events accumulate. Evidence: diagnostic script against service `lpjy0yvp2m` / table `crypto_ticks`; `pipeline/websocket.py` lines 16 and 55–59.
- 2026-10-16 05:48Z [FINDING] Twelve Data `subscribe-status` for `["BTC/USD", "ETH/USD", "MSFT", "AAPL"]` returned success only for `BTC/USD` and `AAPL`; `ETH/USD` and `MSFT` failed (likely free-tier concurrent symbol / credit limit). That slows batch fill to mostly BTC ticks. Evidence: same 25s diagnostic run (~20 price events, no insert yet).
- 2026-10-16 05:48Z [HONEST] Prior terminal run of `pipeline/websocket.py` was Ctrl+C'd with no "Current batch size" lines and no "Batch insert" — consistent with stopping before 100 events (and possibly before the first tick). Insert path itself is fine.
- 2026-10-16 05:50Z [DECISION] Patched `pipeline/websocket.py`: `MAX_BATCH_SIZE=10`, flush remaining batch on Ctrl+C, log `subscribe-status`, symbols limited to `BTC/USD`+`ETH/USD`, `sslmode=require`, timezone-aware timestamps, and `if __name__ == "__main__"` so import no longer starts the stream. Rejected keeping tutorial’s batch of 100 / four symbols while validating ingest. Evidence: file + smoke insert of 3 `SMOKE/TEST` rows then delete.
- 2026-10-16 05:53Z [FAILED] `uv run … python pipeline/websocket.py` crashed with `AttributeError: module 'websocket' has no attribute 'WebSocketApp'`. Cause: running that path puts `pipeline/` on `sys.path`, so twelvedata’s `import websocket` loaded our script instead of `websocket-client`. Evidence: terminal 2; `find_spec` pointed at `pipeline/websocket.py`.
- 2026-10-16 05:53Z [DECISION] Renamed `pipeline/websocket.py` → `pipeline/ingest.py` and `websocket_test.py` → `ws_smoke.py` so the local module name cannot shadow the package. Run with `uv run --env-file .env python pipeline/ingest.py`.
- 2026-10-16 06:12Z [FINDING] `one_day_candle` CAGG was empty while `crypto_ticks` had ~980 rows all on 2026-10-16. Policy `end_offset => INTERVAL '1 day'` (plus daily schedule) only materializes buckets in `[now-3d, now-1d)`, so today’s incomplete day never enters the matview until after that window. Evidence: tick min/max times; Tiger docs on refresh policies / end_offset.
