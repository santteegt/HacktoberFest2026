// libsql client + migrations for the vault database var/pit.db (T1; plan 4.5).
// Tables: settings, setups, sessions, runs, changes, saved_setups, coach_runs (plain fallback only).
// JSON columns (values, conditions, lap_times_ms, feel, from/to) are stored as TEXT.
// No foreign keys are declared: import replaces whole tables and must not depend on insert order.
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { createClient, type Client } from "@libsql/client";
import { config } from "./config";

let current: Client | null = null;

/** Ordered migrations; PRAGMA user_version records how many have been applied. Append only. */
const MIGRATIONS: string[][] = [
  [
    `CREATE TABLE settings (
       key   TEXT PRIMARY KEY,
       value TEXT NOT NULL
     )`,
    `CREATE TABLE setups (
       id         TEXT PRIMARY KEY,
       "values"   TEXT NOT NULL,
       parent_id  TEXT,
       created_at INTEGER NOT NULL
     )`,
    `CREATE TABLE sessions (
       id               TEXT PRIMARY KEY,
       date             TEXT NOT NULL,
       car              TEXT NOT NULL,
       conditions       TEXT NOT NULL,
       current_setup_id TEXT NOT NULL,
       notes            TEXT,
       created_at       INTEGER NOT NULL
     )`,
    `CREATE TABLE runs (
       id           TEXT PRIMARY KEY,
       session_id   TEXT NOT NULL,
       seq          INTEGER NOT NULL,
       setup_id     TEXT NOT NULL,
       conditions   TEXT,
       lap_times_ms TEXT,
       best_lap_ms  REAL,
       rating       INTEGER,
       feel         TEXT NOT NULL,
       notes        TEXT,
       created_at   INTEGER NOT NULL
     )`,
    `CREATE INDEX runs_session ON runs (session_id, seq)`,
    `CREATE TABLE changes (
       id              TEXT PRIMARY KEY,
       session_id      TEXT NOT NULL,
       before_setup_id TEXT NOT NULL,
       after_setup_id  TEXT NOT NULL,
       param           TEXT NOT NULL,
       from_value      TEXT NOT NULL,
       to_value        TEXT NOT NULL,
       lever_id        TEXT,
       symptom_id      TEXT,
       source          TEXT NOT NULL,
       coach_run_id    TEXT,
       outcome         TEXT,
       outcome_run_id  TEXT,
       created_at      INTEGER NOT NULL
     )`,
    `CREATE INDEX changes_session ON changes (session_id, created_at)`,
    `CREATE TABLE saved_setups (
       id         TEXT PRIMARY KEY,
       label      TEXT NOT NULL,
       setup_id   TEXT NOT NULL,
       conditions TEXT NOT NULL,
       session_id TEXT,
       run_id     TEXT,
       event_name TEXT,
       verdict    TEXT,
       created_at INTEGER NOT NULL
     )`,
    `CREATE TABLE coach_runs (
       id         TEXT PRIMARY KEY,
       state      TEXT NOT NULL,
       created_at INTEGER NOT NULL,
       updated_at INTEGER NOT NULL
     )`,
  ],
];

/** Path part of a `file:` libsql URL, or null for :memory: and remote URLs. */
function filePathOf(url: string): string | null {
  if (!url.startsWith("file:")) return null;
  let p = url.slice("file:".length);
  if (p.startsWith("//")) p = p.slice(2); // file:///abs -> /abs
  const q = p.indexOf("?");
  if (q >= 0) p = p.slice(0, q);
  return p === "" || p === ":memory:" ? null : p;
}

/** Open (and migrate) a database; also becomes the singleton returned by getDb(). Tests pass ":memory:". */
export async function openDb(url: string = config.vaultDbUrl): Promise<Client> {
  if (current) {
    current.close();
    current = null;
  }
  const file = filePathOf(url);
  if (file) mkdirSync(dirname(file), { recursive: true });
  const db = createClient({ url });
  if (file) {
    try {
      await db.execute("PRAGMA journal_mode = WAL");
    } catch {
      // WAL is an optimisation only.
    }
  }
  await migrate(db);
  current = db;
  return db;
}

/** The database opened by openDb(); throws if none is open. */
export function getDb(): Client {
  if (!current) throw new Error("database not open: call openDb() first");
  return current;
}

/** Close the singleton (tests, shutdown). */
export function closeDb(): void {
  current?.close();
  current = null;
}

export async function migrate(db: Client): Promise<void> {
  const rs = await db.execute("PRAGMA user_version");
  const version = Number(rs.rows[0]?.[0] ?? 0);
  for (let i = version; i < MIGRATIONS.length; i++) {
    // One batch per migration is atomic (BEGIN ... COMMIT on one connection, so :memory: keeps its data).
    await db.batch([...MIGRATIONS[i]!, `PRAGMA user_version = ${i + 1}`], "write");
  }
}
