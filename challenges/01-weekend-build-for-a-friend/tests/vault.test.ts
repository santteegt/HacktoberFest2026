// Vault tests (T1): in-memory libsql, a tiny params fixture, repo functions and the HTTP routes.
import { mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterAll, beforeEach, describe, expect, it } from "vitest";
import { config } from "../server/config";
import { closeDb, getDb, openDb } from "../server/db";
import { setParamsOverride } from "../server/vault/meta";
import * as repo from "../server/vault/repo";
import { createApp } from "../server/vault/app";
import type { ParamsFile, TrackConditions } from "../src/shared/types";

const FIXTURE: ParamsFile = {
  car: "yokomo-bd12",
  status: "test",
  baselineRule: "bd12 then generic",
  conventions: {},
  params: [
    { id: "frontCamberDeg", label: "Front camber", group: "alignment", unit: "deg", kind: "number", bd12: 1.5, generic: 2, src: [], range: "x" },
    { id: "casterDeg", label: "Caster", group: "alignment", unit: "deg", kind: "number", bd12: null, generic: 4, src: [], range: "x" },
    { id: "rearToeInDeg", label: "Rear toe-in", group: "alignment", unit: "deg", kind: "number", bd12: 3.5, generic: 3, src: [], range: "x" },
    { id: "frontSpringRate", label: "Front spring", group: "damping", unit: "", kind: "text", bd12: null, generic: null, src: [], range: "x" },
    { id: "fdr", label: "FDR", group: "drivetrain", unit: "", kind: "computed", formula: "a/b", bd12: null, generic: null, src: [], range: "x" },
  ],
};

const COND: TrackConditions = { trackName: "Club track", surface: "asphalt", grip: "medium", bumpy: false, trackTempC: 24 };
const backupDir = mkdtempSync(join(tmpdir(), "pit-backups-"));
const origBackups = config.paths.backups;
(config.paths as { backups: string }).backups = backupDir;

beforeEach(async () => {
  await openDb(":memory:");
  setParamsOverride(FIXTURE);
});
afterAll(() => {
  closeDb();
  setParamsOverride(null);
  (config.paths as { backups: string }).backups = origBackups;
  rmSync(backupDir, { recursive: true, force: true });
});

const newSession = () => repo.createSession({ date: "2026-10-04", car: "yokomo-bd12", conditions: COND });

describe("sessions and baseline", () => {
  it("creates a baseline setup: BD12 value first, then generic, null when neither; computed params are skipped", async () => {
    const s = await newSession();
    const b = await repo.getSessionBundle(s.id);
    expect(b.setups).toHaveLength(1);
    expect(b.session.currentSetupId).toBe(b.setups[0]!.id);
    expect(b.setups[0]!.values).toEqual({
      frontCamberDeg: 1.5, // bd12
      casterDeg: 4, // bd12 null -> generic
      rearToeInDeg: 3.5,
      frontSpringRate: null, // neither
    });
    expect(b.setups[0]!.parentId).toBeUndefined();
  });

  it("generic car prefers generic values", async () => {
    const s = await repo.createSession({ date: "2026-10-04", car: "generic", conditions: COND });
    const b = await repo.getSessionBundle(s.id);
    expect(b.setups[0]!.values.frontCamberDeg).toBe(2);
    expect(b.setups[0]!.values.rearToeInDeg).toBe(3);
  });

  it("lists newest first, patches conditions and notes, 404s on unknown ids", async () => {
    const a = await newSession();
    const b = await newSession();
    expect((await repo.listSessions()).map((s) => s.id)).toEqual([b.id, a.id]);
    const p = await repo.patchSession(a.id, { conditions: { ...COND, grip: "high" }, notes: "dusty" });
    expect(p.conditions.grip).toBe("high");
    expect(p.notes).toBe("dusty");
    expect((await repo.getSessionBundle(a.id)).session.notes).toBe("dusty");
    await expect(repo.getSessionBundle("nope")).rejects.toMatchObject({ status: 404 });
  });
});

describe("applySetupChanges (copy-on-write)", () => {
  it("writes one Change per changed param and a new setup row; the old row is untouched", async () => {
    const s = await newSession();
    const before = (await repo.getSessionBundle(s.id)).setups[0]!;
    const r = await repo.applySetupChanges(
      s.id,
      { rearToeInDeg: 3, casterDeg: 5, frontCamberDeg: 1.5 /* unchanged: ignored */ },
      { source: "coach", leverId: "xo-1", symptomId: "exit-oversteer", coachRunId: "cr1" },
    );
    expect(r.changes).toHaveLength(2);
    expect(r.setup.parentId).toBe(before.id);
    expect(r.setup.values).toMatchObject({ rearToeInDeg: 3, casterDeg: 5, frontCamberDeg: 1.5 });
    const toe = r.changes.find((c) => c.param === "rearToeInDeg")!;
    expect(toe).toMatchObject({ from: 3.5, to: 3, beforeSetupId: before.id, afterSetupId: r.setup.id, source: "coach", leverId: "xo-1", symptomId: "exit-oversteer", coachRunId: "cr1" });

    const b = await repo.getSessionBundle(s.id);
    expect(b.session.currentSetupId).toBe(r.setup.id);
    expect(b.changes).toHaveLength(2);
    expect(b.setups).toHaveLength(2);
    expect(b.setups.find((x) => x.id === before.id)!.values.rearToeInDeg).toBe(3.5);
  });

  it("is a no-op when nothing changes, and rejects unknown params", async () => {
    const s = await newSession();
    const r = await repo.applySetupChanges(s.id, { frontCamberDeg: 1.5 }, { source: "manual" });
    expect(r.changes).toEqual([]);
    expect((await repo.getSessionBundle(s.id)).setups).toHaveLength(1);
    await expect(repo.applySetupChanges(s.id, { bogus: 1 }, { source: "manual" })).rejects.toMatchObject({ status: 400 });
  });

  it("can set a text param from null and chain changes", async () => {
    const s = await newSession();
    await repo.applySetupChanges(s.id, { frontSpringRate: "soft" }, { source: "manual" });
    const r = await repo.applySetupChanges(s.id, { frontSpringRate: "medium" }, { source: "manual" });
    expect(r.changes[0]).toMatchObject({ from: "soft", to: "medium" });
    expect((await repo.getSessionBundle(s.id)).changes).toHaveLength(2);
  });
});

describe("runs and outcomes", () => {
  it("stores lap times as ms, numbers runs, binds to the current setup and defaults best lap", async () => {
    const s = await newSession();
    const r1 = await repo.addRun(s.id, { lapTimesMs: [14900, 15100, 14800], rating: 4, feel: ["exit-oversteer"], notes: "ok" });
    expect(r1).toMatchObject({ seq: 1, lapTimesMs: [14900, 15100, 14800], bestLapMs: 14800, rating: 4, feel: ["exit-oversteer"] });
    const { setup } = await repo.applySetupChanges(s.id, { rearToeInDeg: 3 }, { source: "manual" });
    const r2 = await repo.addRun(s.id, { feel: [] });
    expect(r2.seq).toBe(2);
    expect(r2.setupId).toBe(setup.id);
    expect(r2.setupId).not.toBe(r1.setupId);
    expect(r2.lapTimesMs).toBeUndefined();
    const b = await repo.getSessionBundle(s.id);
    expect(b.runs.map((r) => r.seq)).toEqual([1, 2]);
    expect(b.runs[0]!.lapTimesMs).toEqual([14900, 15100, 14800]);
    await expect(repo.addRun(s.id, { lapTimesMs: [-1], feel: [] })).rejects.toMatchObject({ status: 400 });
  });

  it("records change outcomes", async () => {
    const s = await newSession();
    const { changes } = await repo.applySetupChanges(s.id, { casterDeg: 5 }, { source: "manual" });
    const run = await repo.addRun(s.id, { feel: [] });
    const c = await repo.setChangeOutcome(changes[0]!.id, "worse", run.id);
    expect(c).toMatchObject({ outcome: "worse", outcomeRunId: run.id });
    expect((await repo.getSessionBundle(s.id)).changes[0]!.outcome).toBe("worse");
    await expect(repo.setChangeOutcome("nope", "better")).rejects.toMatchObject({ status: 404 });
  });
});

describe("saved setups", () => {
  it("saves, lists and deletes", async () => {
    const s = await newSession();
    const saved = await repo.saveSetup({ label: "Club good", setupId: s.currentSetupId, conditions: COND, sessionId: s.id, verdict: "great" });
    expect(saved.id).toBeTruthy();
    expect(await repo.listSaved()).toHaveLength(1);
    await expect(repo.saveSetup({ label: "x", setupId: "missing", conditions: COND })).rejects.toMatchObject({ status: 404 });
    await repo.deleteSaved(saved.id);
    expect(await repo.listSaved()).toEqual([]);
    await expect(repo.deleteSaved(saved.id)).rejects.toMatchObject({ status: 404 });
  });
});

describe("settings", () => {
  it("returns defaults, merges patches, validates", async () => {
    const d = await repo.getSettings();
    expect(d).toMatchObject({ numCtx: 4096, llmPhrasing: true, voiceIn: "off", tempUnit: "C" });
    const s = await repo.putSettings({ reviewedOnly: true, voiceName: "Samantha" });
    expect(s).toMatchObject({ reviewedOnly: true, voiceName: "Samantha", model: d.model });
    expect((await repo.getSettings()).reviewedOnly).toBe(true);
  });
});

describe("export, import, reset", () => {
  async function seed() {
    const s = await newSession();
    await repo.applySetupChanges(s.id, { rearToeInDeg: 3, casterDeg: 5 }, { source: "manual" });
    await repo.addRun(s.id, { lapTimesMs: [15000, 15100], feel: [] });
    await repo.saveSetup({ label: "A", setupId: s.currentSetupId, conditions: COND });
    await repo.putSettings({ tempUnit: "F" });
    return s;
  }

  it("round-trips counts and content, writing a backup first", async () => {
    await seed();
    const dump = await repo.exportAll();
    expect(dump.tables).toMatchObject({});
    const counts = { settings: 1, setups: 2, sessions: 1, runs: 1, changes: 2, savedSetups: 1 };
    expect(Object.fromEntries(Object.entries(dump.tables).map(([k, v]) => [k, v.length]))).toEqual(counts);

    await openDb(":memory:"); // a different, empty vault
    const before = readdirSync(backupDir).length;
    const res = await repo.importAll(dump);
    expect(res).toEqual({ ok: true, counts });
    expect(readdirSync(backupDir).length).toBe(before + 1);

    const again = await repo.exportAll();
    expect({ ...again, exportedAt: 0 }).toEqual({ ...dump, exportedAt: 0 });
    expect((await repo.getSettings()).tempUnit).toBe("F");
  });

  it("import replaces existing data and rejects a wrong schemaVersion", async () => {
    await seed();
    const dump = await repo.exportAll();
    await newSession(); // extra data that import must drop
    await repo.importAll(dump);
    expect(await repo.listSessions()).toHaveLength(1);
    await expect(repo.importAll({ ...dump, schemaVersion: 99 })).rejects.toMatchObject({ status: 400 });
    expect(await repo.listSessions()).toHaveLength(1);
  });

  it("the backup file holds the vault as it was before the import", async () => {
    await seed();
    const dump = await repo.exportAll();
    await repo.importAll(dump);
    const files = readdirSync(backupDir).filter((f) => f.endsWith("before-import.json")).sort();
    const last = JSON.parse(readFileSync(join(backupDir, files[files.length - 1]!), "utf8"));
    expect(last.tables.sessions).toHaveLength(1);
  });

  it("reset empties the vault but keeps settings", async () => {
    await seed();
    await repo.resetAll();
    const d = await repo.exportAll();
    expect(d.tables.sessions).toEqual([]);
    expect(d.tables.setups).toEqual([]);
    expect(d.tables.changes).toEqual([]);
    expect((await repo.getSettings()).tempUnit).toBe("F");
    expect((await getDb().execute("SELECT COUNT(*) AS n FROM coach_runs")).rows[0]!.n).toBe(0);
  });
});

describe("HTTP routes", () => {
  const app = createApp(join(tmpdir(), "no-such-dist-dir"));
  const call = (method: string, path: string, body?: unknown) =>
    app.request(path, { method, headers: { "content-type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });

  it("session, setup, run, bundle, outcome, saved, settings, export/import/reset", async () => {
    const sres = await call("POST", "/api/sessions", { date: "2026-10-04", car: "yokomo-bd12", conditions: COND });
    expect(sres.status).toBe(200);
    const session = await sres.json();
    expect(session.currentSetupId).toBeTruthy();

    const setup = await (await call("POST", `/api/sessions/${session.id}/setup`, { values: { casterDeg: 5, rearToeInDeg: 3 }, source: "manual" })).json();
    expect(setup.changes).toHaveLength(2);

    const run = await (await call("POST", `/api/sessions/${session.id}/runs`, { feel: ["traction-roll"], lapTimesMs: [14900, 15100], rating: 3 })).json();
    expect(run).toMatchObject({ seq: 1, setupId: setup.setup.id, bestLapMs: 14900 });

    const ch = await (await call("PATCH", `/api/changes/${setup.changes[0].id}`, { outcome: "better", outcomeRunId: run.id })).json();
    expect(ch.outcome).toBe("better");

    const bundle = await (await call("GET", `/api/sessions/${session.id}`)).json();
    expect(bundle.runs).toHaveLength(1);
    expect(bundle.changes).toHaveLength(2);
    expect(bundle.setups).toHaveLength(2);

    const saved = await (await call("POST", "/api/saved", { label: "Good", setupId: setup.setup.id, conditions: COND })).json();
    expect((await (await call("GET", "/api/saved")).json())).toHaveLength(1);
    expect((await (await call("DELETE", `/api/saved/${saved.id}`)).json())).toEqual({ ok: true });

    const st = await (await call("PUT", "/api/settings", { llmPhrasing: false })).json();
    expect(st.llmPhrasing).toBe(false);
    expect((await (await call("GET", "/api/settings")).json()).llmPhrasing).toBe(false);

    const dump = await (await call("GET", "/api/export")).json();
    expect(dump.tables.sessions).toHaveLength(1);
    const imp = await (await call("POST", "/api/import", dump)).json();
    expect(imp.ok).toBe(true);
    expect(imp.counts.changes).toBe(2);

    expect((await call("POST", "/api/reset", {})).status).toBe(400);
    expect((await call("POST", "/api/reset", { confirm: "reset" })).status).toBe(400);
    expect((await (await call("POST", "/api/reset", { confirm: "RESET" })).json())).toEqual({ ok: true });
    expect(await (await call("GET", "/api/sessions")).json()).toEqual([]);
  });

  it("returns { error, stage } for bad input, unknown ids and unknown endpoints", async () => {
    let r = await call("POST", "/api/sessions", { date: "x" });
    expect(r.status).toBe(400);
    expect(await r.json()).toMatchObject({ stage: "validate", error: expect.any(String) });
    r = await call("GET", "/api/sessions/does-not-exist");
    expect(r.status).toBe(404);
    expect(await r.json()).toMatchObject({ stage: "vault" });
    r = await call("POST", "/api/sessions/does-not-exist/runs", { feel: [] });
    expect(r.status).toBe(404);
    r = await call("GET", "/api/nope");
    expect(r.status).toBe(404);
    expect(await r.json()).toMatchObject({ error: expect.any(String) });
    expect((await call("GET", "/api/health")).status).toBe(200);
  });

  it("serves /api/meta from the real data files", async () => {
    setParamsOverride(null);
    const m = await (await call("GET", "/api/meta")).json();
    expect(m.params.length).toBeGreaterThan(10);
    expect(m.symptoms.length).toBeGreaterThan(5);
    expect(m.levers.length).toBeGreaterThan(5);
    expect(Array.isArray(m.prechecks)).toBe(true);
    expect(m.kbStats.chunks).toBeGreaterThan(0);
  });
});

describe("static serving", () => {
  it("serves files and falls back to index.html for client routes, never for /api or missing assets", async () => {
    const dist = mkdtempSync(join(tmpdir(), "pit-dist-"));
    const { writeFileSync, mkdirSync } = await import("node:fs");
    writeFileSync(join(dist, "index.html"), "<html>spa</html>");
    mkdirSync(join(dist, "assets"));
    writeFileSync(join(dist, "assets", "a.js"), "console.log(1)");
    const app = createApp(dist);
    expect(await (await app.request("/")).text()).toContain("spa");
    expect(await (await app.request("/session/abc")).text()).toContain("spa");
    const js = await app.request("/assets/a.js");
    expect(js.headers.get("content-type")).toContain("javascript");
    expect((await app.request("/assets/missing.js")).status).toBe(404);
    expect(await (await app.request("/..%2f..%2fetc%2fpasswd")).text()).toContain("spa"); // traversal never leaves dist
    expect((await app.request("/api/nope")).headers.get("content-type")).toContain("json");
    rmSync(dist, { recursive: true, force: true });
  });
});
