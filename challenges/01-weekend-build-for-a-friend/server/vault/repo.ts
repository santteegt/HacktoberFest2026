// Vault repository (T1; plan 4.5). T3's `apply` step calls applySetupChanges and its `logOutcome` step calls
// setChangeOutcome. Functions use getDb() from server/db.ts. Every write goes through one serial queue, and
// multi-row writes use a single libsql batch (atomic; also keeps ":memory:" databases intact).
import { randomUUID } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { InStatement, Row } from "@libsql/client";
import { config, defaultSettings } from "../config";
import { getDb } from "../db";
import { Settings as SettingsSchema, SettingsPatch as SettingsPatchSchema, SCHEMA_VERSION } from "../../src/shared/schemas";
import type {
  AddRunBody,
  ApplySetupResponse,
  CreateSessionBody,
  ImportResponse,
  PatchSessionBody,
  SaveSetupBody,
  SessionBundle,
} from "../../src/shared/api";
import type {
  Change,
  ChangeSource,
  ExportDump,
  Outcome,
  ParamValue,
  Run,
  SavedSetup,
  Session,
  Setup,
  SetupValues,
  Settings,
  SettingsPatch,
  TrackConditions,
} from "../../src/shared/types";
import { VaultError } from "./errors";
import { baselineSetup, getParamsFile } from "./meta";

// ---------- helpers ----------

let queue: Promise<unknown> = Promise.resolve();
/** Run writes one at a time (read-modify-write functions must not interleave). Never nest calls. */
function serial<T>(fn: () => Promise<T>): Promise<T> {
  const p = queue.then(() => fn());
  queue = p.catch(() => undefined);
  return p;
}

const newId = (): string => randomUUID();
const json = (v: unknown): string => JSON.stringify(v);
const parse = <T>(s: unknown): T => JSON.parse(String(s)) as T;
/** SQL NULL becomes undefined so rows satisfy the zod contract (optional fields reject null). */
const opt = <T>(v: unknown): T | undefined => (v === null || v === undefined ? undefined : (v as T));
const optJson = <T>(v: unknown): T | undefined => (v === null || v === undefined ? undefined : parse<T>(v));

function clean<T extends object>(o: T): T {
  for (const k of Object.keys(o) as (keyof T)[]) if (o[k] === undefined) delete o[k];
  return o;
}

const rowSetup = (r: Row): Setup =>
  clean({
    id: String(r.id),
    values: parse<SetupValues>(r.values),
    parentId: opt<string>(r.parent_id),
    createdAt: Number(r.created_at),
  });

const rowSession = (r: Row): Session =>
  clean({
    id: String(r.id),
    date: String(r.date),
    car: String(r.car) as Session["car"],
    conditions: parse<TrackConditions>(r.conditions),
    currentSetupId: String(r.current_setup_id),
    notes: opt<string>(r.notes),
    createdAt: Number(r.created_at),
  });

const rowRun = (r: Row): Run =>
  clean({
    id: String(r.id),
    sessionId: String(r.session_id),
    seq: Number(r.seq),
    setupId: String(r.setup_id),
    conditions: optJson<Run["conditions"]>(r.conditions),
    lapTimesMs: optJson<number[]>(r.lap_times_ms),
    bestLapMs: opt<number>(r.best_lap_ms) === undefined ? undefined : Number(r.best_lap_ms),
    rating: opt<Run["rating"]>(r.rating === null ? null : Number(r.rating)),
    feel: parse<string[]>(r.feel),
    notes: opt<string>(r.notes),
    createdAt: Number(r.created_at),
  });

const rowChange = (r: Row): Change =>
  clean({
    id: String(r.id),
    sessionId: String(r.session_id),
    beforeSetupId: String(r.before_setup_id),
    afterSetupId: String(r.after_setup_id),
    param: String(r.param),
    from: parse<ParamValue>(r.from_value),
    to: parse<ParamValue>(r.to_value),
    leverId: opt<string>(r.lever_id),
    symptomId: opt<string>(r.symptom_id),
    source: String(r.source) as ChangeSource,
    coachRunId: opt<string>(r.coach_run_id),
    outcome: opt<Outcome>(r.outcome),
    outcomeRunId: opt<string>(r.outcome_run_id),
    createdAt: Number(r.created_at),
  });

const rowSaved = (r: Row): SavedSetup =>
  clean({
    id: String(r.id),
    label: String(r.label),
    setupId: String(r.setup_id),
    conditions: parse<TrackConditions>(r.conditions),
    sessionId: opt<string>(r.session_id),
    runId: opt<string>(r.run_id),
    eventName: opt<string>(r.event_name),
    verdict: opt<string>(r.verdict),
    createdAt: Number(r.created_at),
  });

// Insert statements shared by the normal write paths and by import.
const insSetup = (s: Setup): InStatement => ({
  sql: `INSERT INTO setups (id, "values", parent_id, created_at) VALUES (?, ?, ?, ?)`,
  args: [s.id, json(s.values), s.parentId ?? null, s.createdAt],
});
const insSession = (s: Session): InStatement => ({
  sql: `INSERT INTO sessions (id, date, car, conditions, current_setup_id, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)`,
  args: [s.id, s.date, s.car, json(s.conditions), s.currentSetupId, s.notes ?? null, s.createdAt],
});
const insRun = (r: Run): InStatement => ({
  sql: `INSERT INTO runs (id, session_id, seq, setup_id, conditions, lap_times_ms, best_lap_ms, rating, feel, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  args: [
    r.id,
    r.sessionId,
    r.seq,
    r.setupId,
    r.conditions ? json(r.conditions) : null,
    r.lapTimesMs ? json(r.lapTimesMs) : null,
    r.bestLapMs ?? null,
    r.rating ?? null,
    json(r.feel),
    r.notes ?? null,
    r.createdAt,
  ],
});
const insChange = (c: Change): InStatement => ({
  sql: `INSERT INTO changes (id, session_id, before_setup_id, after_setup_id, param, from_value, to_value, lever_id, symptom_id,
                             source, coach_run_id, outcome, outcome_run_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  args: [
    c.id,
    c.sessionId,
    c.beforeSetupId,
    c.afterSetupId,
    c.param,
    json(c.from),
    json(c.to),
    c.leverId ?? null,
    c.symptomId ?? null,
    c.source,
    c.coachRunId ?? null,
    c.outcome ?? null,
    c.outcomeRunId ?? null,
    c.createdAt,
  ],
});
const insSaved = (s: SavedSetup): InStatement => ({
  sql: `INSERT INTO saved_setups (id, label, setup_id, conditions, session_id, run_id, event_name, verdict, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  args: [s.id, s.label, s.setupId, json(s.conditions), s.sessionId ?? null, s.runId ?? null, s.eventName ?? null, s.verdict ?? null, s.createdAt],
});
const insSetting = (key: string, value: unknown): InStatement => ({
  sql: `INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value`,
  args: [key, json(value)],
});

async function loadSession(id: string): Promise<Session> {
  const rs = await getDb().execute({ sql: "SELECT * FROM sessions WHERE id = ?", args: [id] });
  const row = rs.rows[0];
  if (!row) throw new VaultError(404, `session ${id} not found`, "vault");
  return rowSession(row);
}

async function loadSetup(id: string): Promise<Setup> {
  const rs = await getDb().execute({ sql: `SELECT * FROM setups WHERE id = ?`, args: [id] });
  const row = rs.rows[0];
  if (!row) throw new VaultError(404, `setup ${id} not found`, "vault");
  return rowSetup(row);
}

/** GET /api/setups/:id (T7): one setup row by id; 404 VaultError when missing. */
export function getSetup(id: string): Promise<Setup> {
  return loadSetup(id);
}

// ---------- sessions ----------

/** Creates the session and its baseline setup row (BD12 value, else generic; plan 4.1) in one batch. */
export function createSession(body: CreateSessionBody): Promise<Session> {
  return serial(async () => {
    const now = Date.now();
    const setup: Setup = { id: newId(), values: baselineSetup(getParamsFile().params, body.car), createdAt: now };
    const session: Session = clean({
      id: newId(),
      date: body.date,
      car: body.car,
      conditions: body.conditions,
      currentSetupId: setup.id,
      notes: body.notes,
      createdAt: now,
    });
    await getDb().batch([insSetup(setup), insSession(session)], "write");
    return session;
  });
}

export async function listSessions(): Promise<Session[]> {
  const rs = await getDb().execute("SELECT * FROM sessions ORDER BY created_at DESC, rowid DESC");
  return rs.rows.map(rowSession);
}

export async function getSessionBundle(sessionId: string): Promise<SessionBundle> {
  const session = await loadSession(sessionId);
  const db = getDb();
  const runs = (
    await db.execute({ sql: "SELECT * FROM runs WHERE session_id = ? ORDER BY seq", args: [sessionId] })
  ).rows.map(rowRun);
  const changes = (
    await db.execute({ sql: "SELECT * FROM changes WHERE session_id = ? ORDER BY created_at, rowid", args: [sessionId] })
  ).rows.map(rowChange);
  const ids = new Set<string>([session.currentSetupId]);
  for (const r of runs) ids.add(r.setupId);
  for (const c of changes) {
    ids.add(c.beforeSetupId);
    ids.add(c.afterSetupId);
  }
  const list = [...ids];
  const setups: Setup[] = [];
  if (list.length > 0) {
    const rs = await db.execute({
      sql: `SELECT * FROM setups WHERE id IN (${list.map(() => "?").join(",")}) ORDER BY created_at, rowid`,
      args: list,
    });
    setups.push(...rs.rows.map(rowSetup));
  }
  return { session, runs, changes, setups };
}

export function patchSession(sessionId: string, body: PatchSessionBody): Promise<Session> {
  return serial(async () => {
    const s = await loadSession(sessionId);
    const next: Session = clean({
      ...s,
      conditions: body.conditions ?? s.conditions,
      notes: body.notes ?? s.notes,
    });
    await getDb().execute({
      sql: "UPDATE sessions SET conditions = ?, notes = ? WHERE id = ?",
      args: [json(next.conditions), next.notes ?? null, sessionId],
    });
    return next;
  });
}

// ---------- setups and changes ----------

/**
 * Copy-on-write: one new setup row and one Change per changed param. Values equal to the current ones are
 * ignored; when nothing changes, no row is written and the current setup is returned with no changes.
 * Unknown param ids are rejected (400) so a typo cannot silently create a phantom parameter.
 */
export function applySetupChanges(
  sessionId: string,
  values: Record<string, ParamValue>,
  meta: { source: ChangeSource; leverId?: string; symptomId?: string; coachRunId?: string },
): Promise<ApplySetupResponse> {
  return serial(async () => {
    const session = await loadSession(sessionId);
    const current = await loadSetup(session.currentSetupId);
    const known = new Set(getParamsFile().params.map((p) => p.id));
    const unknown = Object.keys(values).filter((k) => !known.has(k));
    if (unknown.length > 0) throw new VaultError(400, `unknown param(s): ${unknown.join(", ")}`, "validate");

    const diffs = Object.entries(values).filter(([k, v]) => (current.values[k] ?? null) !== v);
    if (diffs.length === 0) return { setup: current, changes: [] };

    const now = Date.now();
    const setup: Setup = {
      id: newId(),
      values: { ...current.values, ...Object.fromEntries(diffs) },
      parentId: current.id,
      createdAt: now,
    };
    const changes: Change[] = diffs.map(([param, to]) =>
      clean<Change>({
        id: newId(),
        sessionId,
        beforeSetupId: current.id,
        afterSetupId: setup.id,
        param,
        from: current.values[param] ?? null,
        to,
        leverId: meta.leverId,
        symptomId: meta.symptomId,
        source: meta.source,
        coachRunId: meta.coachRunId,
        createdAt: now,
      }),
    );
    await getDb().batch(
      [insSetup(setup), ...changes.map(insChange), { sql: "UPDATE sessions SET current_setup_id = ? WHERE id = ?", args: [setup.id, sessionId] }],
      "write",
    );
    return { setup, changes };
  });
}

export function setChangeOutcome(changeId: string, outcome: Outcome, outcomeRunId?: string): Promise<Change> {
  return serial(async () => {
    const db = getDb();
    const rs = await db.execute({
      sql: "UPDATE changes SET outcome = ?, outcome_run_id = ? WHERE id = ?",
      args: [outcome, outcomeRunId ?? null, changeId],
    });
    if (rs.rowsAffected === 0) throw new VaultError(404, `change ${changeId} not found`, "vault");
    const row = (await db.execute({ sql: "SELECT * FROM changes WHERE id = ?", args: [changeId] })).rows[0]!;
    return rowChange(row);
  });
}

// ---------- runs ----------

/** setupId = the session's current setup; seq = next number in the session; bestLapMs defaults to the fastest lap. */
export function addRun(sessionId: string, body: AddRunBody): Promise<Run> {
  return serial(async () => {
    const session = await loadSession(sessionId);
    const laps = body.lapTimesMs;
    if (laps && laps.some((t) => !Number.isFinite(t) || t <= 0)) {
      throw new VaultError(400, "lapTimesMs must be positive numbers (milliseconds)", "validate");
    }
    const best = body.bestLapMs ?? (laps && laps.length > 0 ? Math.min(...laps) : undefined);
    const rs = await getDb().execute({ sql: "SELECT COALESCE(MAX(seq), 0) AS m FROM runs WHERE session_id = ?", args: [sessionId] });
    const run: Run = clean<Run>({
      id: newId(),
      sessionId,
      seq: Number(rs.rows[0]!.m) + 1,
      setupId: session.currentSetupId,
      conditions: body.conditions,
      lapTimesMs: laps,
      bestLapMs: best,
      rating: body.rating,
      feel: body.feel,
      notes: body.notes,
      createdAt: Date.now(),
    });
    await getDb().execute(insRun(run));
    return run;
  });
}

// ---------- saved setups ----------

export async function listSaved(): Promise<SavedSetup[]> {
  const rs = await getDb().execute("SELECT * FROM saved_setups ORDER BY created_at DESC, rowid DESC");
  return rs.rows.map(rowSaved);
}

export function saveSetup(body: SaveSetupBody): Promise<SavedSetup> {
  return serial(async () => {
    await loadSetup(body.setupId); // 404 when the setup does not exist
    const saved: SavedSetup = clean<SavedSetup>({ ...body, id: newId(), createdAt: Date.now() });
    await getDb().execute(insSaved(saved));
    return saved;
  });
}

export function deleteSaved(id: string): Promise<void> {
  return serial(async () => {
    const rs = await getDb().execute({ sql: "DELETE FROM saved_setups WHERE id = ?", args: [id] });
    if (rs.rowsAffected === 0) throw new VaultError(404, `saved setup ${id} not found`, "vault");
  });
}

// ---------- export / import / reset ----------

export async function exportAll(): Promise<ExportDump> {
  const db = getDb();
  const all = async (sql: string) => (await db.execute(sql)).rows;
  const settings = (await all("SELECT key, value FROM settings ORDER BY key")).map((r) => ({
    key: String(r.key),
    value: parse<unknown>(r.value),
  }));
  return {
    schemaVersion: SCHEMA_VERSION,
    exportedAt: Date.now(),
    tables: {
      settings,
      setups: (await all("SELECT * FROM setups ORDER BY created_at, rowid")).map(rowSetup),
      sessions: (await all("SELECT * FROM sessions ORDER BY created_at, rowid")).map(rowSession),
      runs: (await all("SELECT * FROM runs ORDER BY session_id, seq")).map(rowRun),
      changes: (await all("SELECT * FROM changes ORDER BY created_at, rowid")).map(rowChange),
      savedSetups: (await all("SELECT * FROM saved_setups ORDER BY created_at, rowid")).map(rowSaved),
    },
  };
}

/** Write the current vault to <dir>/<UTC timestamp>-<label>.json; returns the file path. */
async function writeBackup(label: string, dir: string): Promise<string> {
  mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const file = join(dir, `${stamp}-${label}.json`);
  writeFileSync(file, JSON.stringify(await exportAll(), null, 2));
  return file;
}

const counts = (d: ExportDump): ImportResponse["counts"] => ({
  settings: d.tables.settings.length,
  setups: d.tables.setups.length,
  sessions: d.tables.sessions.length,
  runs: d.tables.runs.length,
  changes: d.tables.changes.length,
  savedSetups: d.tables.savedSetups.length,
});

/** Replaces the whole vault with the dump. Writes a backup of the current vault first (default var/backups/). */
export function importAll(dump: ExportDump, opts: { backupDir?: string } = {}): Promise<ImportResponse> {
  return serial(async () => {
    if (dump.schemaVersion !== SCHEMA_VERSION) {
      throw new VaultError(400, `unsupported schemaVersion ${dump.schemaVersion} (expected ${SCHEMA_VERSION})`, "import");
    }
    // Validate settings before touching anything.
    const settingRows: [string, unknown][] = [];
    for (const { key, value } of dump.tables.settings) {
      const r = SettingsPatchSchema.safeParse({ [key]: value });
      if (!r.success) throw new VaultError(400, `invalid setting "${key}": ${r.error.message}`, "import");
      if (key in r.data) settingRows.push([key, (r.data as Record<string, unknown>)[key]]);
    }
    await writeBackup("before-import", opts.backupDir ?? config.paths.backups);
    const t = dump.tables;
    await getDb().batch(
      [
        ...["settings", "setups", "sessions", "runs", "changes", "saved_setups"].map((n) => `DELETE FROM ${n}`),
        ...settingRows.map(([k, v]) => insSetting(k, v)),
        ...t.setups.map(insSetup),
        ...t.sessions.map(insSession),
        ...t.runs.map(insRun),
        ...t.changes.map(insChange),
        ...t.savedSetups.map(insSaved),
      ],
      "write",
    );
    return { ok: true, counts: counts(dump) };
  });
}

/**
 * Deletes all vault data (setups, sessions, runs, changes, saved setups, coach_runs). Settings are kept: they are
 * configuration, not driver data. Writes a backup first. The route enforces the RESET confirmation.
 */
export function resetAll(opts: { backupDir?: string } = {}): Promise<void> {
  return serial(async () => {
    await writeBackup("before-reset", opts.backupDir ?? config.paths.backups);
    await getDb().batch(["setups", "sessions", "runs", "changes", "saved_setups", "coach_runs"].map((n) => `DELETE FROM ${n}`), "write");
  });
}

// ---------- settings ----------

export async function getSettings(): Promise<Settings> {
  const rs = await getDb().execute("SELECT key, value FROM settings");
  const stored: Record<string, unknown> = {};
  for (const r of rs.rows) stored[String(r.key)] = parse<unknown>(r.value);
  const merged = SettingsSchema.safeParse({ ...defaultSettings, ...stored });
  // A corrupt stored value must not take the app down: fall back to the defaults.
  return merged.success ? merged.data : defaultSettings;
}

export function putSettings(patch: SettingsPatch): Promise<Settings> {
  return serial(async () => {
    const entries = Object.entries(patch).filter(([, v]) => v !== undefined);
    if (entries.length > 0) {
      await getDb().batch(entries.map(([k, v]) => insSetting(k, v)), "write");
    }
    return getSettings();
  });
}
