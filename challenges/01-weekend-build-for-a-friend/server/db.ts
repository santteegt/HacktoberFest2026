// libsql client + migrations for var/pit.db (T1; plan 4.5). T0 stub.
// Tables: settings, setups, sessions, runs, changes, saved_setups, coach_runs (plain fallback only).
import type { Client } from "@libsql/client";

/** Open (and migrate) a database; also becomes the singleton returned by getDb(). Tests pass ":memory:". */
export async function openDb(_url?: string): Promise<Client> {
  throw new Error("not implemented");
}

/** The database opened by openDb(); throws if none is open. */
export function getDb(): Client {
  throw new Error("not implemented");
}

export async function migrate(_db: Client): Promise<void> {
  throw new Error("not implemented");
}
