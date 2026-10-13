# AGENTS.md: tiger_data

Instructions for any AI coding agent working in `global-hack-week/tiger_data/`. They add to [`../AGENTS.md`](../AGENTS.md) and the repo-level `AGENTS.md`.

## What this folder is

Hands-on Tiger / TimescaleDB tutorial: simulate IoT sensor metadata and time-series readings on the **`tigerdata-demo`** service, then run `time_bucket` analytics and hypertable metadata queries.

Human-facing walkthrough and the query report live in [`README.md`](README.md). Keep that file current when you re-run the tutorial.

## Target service

| Field | Value |
| --- | --- |
| Name | `tigerdata-demo` |
| Service ID | `lpjy0yvp2m` |
| Type | TimescaleDB |
| Region | `us-east-1` |
| Environment | `DEV` |

Confirm with Tiger MCP `service_list` / `service_get` before mutating another service. Never target a `PROD`-tagged service for this tutorial.

## Tiger MCP

Project MCP config: repo `.cursor/mcp.json` (server name `tiger`). Namespace in Cursor is typically `project-0-HacktoberFest2026-tiger`.

Useful tools:

- `service_list` / `service_get` — locate services
- `db_query` — run SQL (`query` or `file`); prefer `file` for scripts in this folder
- `db_schema` — inspect deployed schema
- `service_update_password` — rotate `tsdbadmin` password into keyring if SASL auth fails (`with_password: false` unless the user asks for the password)
- `search_docs` / `view_skill` — TimescaleDB docs and skills

Auth: `tiger auth login`. DB passwords stay in the OS keyring / pgpass — never commit them, never paste them into README or memory.

## Deploy workflow

Run against `lpjy0yvp2m` in this order:

1. `sql/sensors_table.sql`
2. `migration/sensors.sql`
3. `sql/sensordata_htable.sql`
4. `migration/sensordata.sql`

Example (MCP): `db_query` with `service_id: "lpjy0yvp2m"` and `file` set to the absolute path of each script.

Example (CLI):

```bash
tiger db query lpjy0yvp2m --file sql/sensors_table.sql
tiger db query lpjy0yvp2m --file migration/sensors.sql
tiger db query lpjy0yvp2m --file sql/sensordata_htable.sql
tiger db query lpjy0yvp2m --file migration/sensordata.sql
```

If tables already exist, either drop them (DEV only, after user yes) or skip DDL and only re-seed data intentionally.

## Verification queries

Sensors:

```sql
SELECT id, type, location FROM sensors ORDER BY id;
```

Dataset summary:

```sql
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT sensor_id) AS sensors,
  MIN(time) AS earliest,
  MAX(time) AS latest,
  ROUND(AVG(temperature)::numeric, 2) AS avg_temperature,
  ROUND(AVG(cpu)::numeric, 4) AS avg_cpu
FROM sensor_data;
```

Expect 4 sensors and about 1152–1160 rows for a full 24h × 5-minute × 4-sensor load.

## Tutorial queries

Average temperature and CPU by 30-minute windows:

```sql
SELECT
  time_bucket('30 minutes', time) AS period,
  ROUND(AVG(temperature)::numeric, 2) AS avg_temperature,
  ROUND(AVG(cpu)::numeric, 4) AS avg_cpu
FROM sensor_data
GROUP BY period
ORDER BY period;
```

Average and last temperature, average CPU by 30-minute windows:

```sql
SELECT
  time_bucket('30 minutes', time) AS period,
  ROUND(AVG(temperature)::numeric, 2) AS avg_temperature,
  ROUND(last(temperature, time)::numeric, 2) AS last_temperature,
  ROUND(AVG(cpu)::numeric, 4) AS avg_cpu
FROM sensor_data
GROUP BY period
ORDER BY period;
```

Metadata:

```sql
SELECT
  hypertable_schema,
  hypertable_name,
  num_dimensions,
  num_chunks,
  compression_enabled,
  tablespaces
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'sensor_data';

SELECT
  chunk_schema,
  chunk_name,
  range_start,
  range_end,
  is_compressed
FROM timescaledb_information.chunks
WHERE hypertable_name = 'sensor_data'
ORDER BY range_start;
```

## Charts (`viz/`)

After query results change, regenerate PNGs and keep README embeds in sync:

```bash
# from this folder
uv venv .venv          # once
uv pip install --python .venv/bin/python matplotlib
.venv/bin/python scripts/generate_charts.py
```

| File | Query |
| --- | --- |
| `viz/01-sensors.png` | Sensors verification |
| `viz/02-dataset-summary.png` | Simulated dataset summary (+ readings per sensor) |
| `viz/03-avg-temp-cpu-30m.png` | Avg temperature and CPU by 30m |
| `viz/04-avg-last-temp-cpu-30m.png` | Avg + last temperature, avg CPU by 30m |
| `viz/05-metadata.png` | Hypertable / chunk metadata |

Update `scripts/generate_charts.py` snapshot arrays when re-running SQL, then regenerate. Do not commit `.venv/`.

## After a successful run

1. Update [`README.md`](README.md) result tables if numbers changed (data is random).
2. Refresh `viz/*.png` and README image embeds if charts are stale.
3. Append an entry to [`docs/CHALLENGE-MEMORY.md`](docs/CHALLENGE-MEMORY.md) (decisions, failures, measurements). Never record secrets.
4. Do not publish a DEV post or claim Tiger credits unless the user explicitly asks.

## Rules

1. Read this file before changing SQL or re-deploying.
2. Prefer absolute paths when passing `file` to `db_query`.
3. Process aggregates in SQL; do not pull all raw rows into context.
4. `migration/sensors.sql` must insert four rows (ids 1–4) so `migration/sensordata.sql` FK inserts succeed.
5. Keep secrets out of git: no connection strings with passwords, no `.env` with live creds.
