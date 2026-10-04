// Seeds clearly labelled DEMO data into the vault so the race-day finder, run comparison and
// "what affected my run" have something to show on a fresh install (T10).
//
//   npm run seed:demo                                   # seeds var/pit.db (the default vault)
//   PIT_DB_URL=file:/abs/path/demo.db npm run seed:demo  # seeds another database
//   npm run seed:demo -- --yes                          # needed when the database already has real sessions
//
// What it writes (every label says DEMO; none of it is the friend's data):
//   - session "DEMO track" (asphalt, low grip), notes "demo data, not real laps":
//       a manual change entering the current values, run 1, a coach change (rear shocks up, outcome
//       "same"), run 2, a coach change (softer rear diff oil, outcome "better"), run 3, a manual change
//       (front toe-out, outcome "worse") and its revert.
//       Run 1 vs run 2 is within the lap-time noise; run 2 vs run 3 is above it.
//   - session "DEMO Indoor Hall" (carpet) with two manual changes.
//   - 3 saved setups: two asphalt tracks (DEMO track, DEMO Lakeside) and one carpet (DEMO Indoor Hall).
//
// Idempotent: it first deletes the previous demo rows only (sessions whose track name starts with "DEMO"
// AND whose notes say "demo data", their runs, changes and setup rows, and saved setups whose label starts
// with "DEMO"). Nothing else is touched. Writes go through the vault repo functions (no HTTP), so the
// server does not need to run; stop it first if it uses the same database file.
import { config } from "../server/config";
import { closeDb, getDb, openDb } from "../server/db";
import * as repo from "../server/vault/repo";
import type { TrackConditions } from "../src/shared/types";

const DEMO_NOTE = "demo data, not real laps";

/** Fixed lap-to-lap scatter in seconds (sums to 0, sd about 0.14 s), so the verdicts are reproducible. */
const SCATTER = [0.12, -0.18, 0.05, 0.2, -0.1, -0.05, 0.16, -0.2, 0.02, -0.02];
const laps = (meanS: number) => SCATTER.map((d) => Math.round((meanS + d) * 1000));

async function removePreviousDemo(): Promise<{ sessions: number; saved: number; setups: number }> {
  const db = getDb();
  const sessions = (
    await db.execute(
      "SELECT id, current_setup_id FROM sessions WHERE json_extract(conditions, '$.trackName') LIKE 'DEMO%' AND notes LIKE '%demo data%'",
    )
  ).rows.map((r) => ({ id: String(r.id), setup: String(r.current_setup_id) }));
  const saved = (await db.execute("SELECT id, setup_id FROM saved_setups WHERE label LIKE 'DEMO%'")).rows.map((r) => ({
    id: String(r.id),
    setup: String(r.setup_id),
  }));

  // Setup rows reachable from the demo rows.
  const setupIds = new Set<string>([...sessions.map((s) => s.setup), ...saved.map((s) => s.setup)]);
  for (const s of sessions) {
    const b = await repo.getSessionBundle(s.id);
    for (const x of b.setups) setupIds.add(x.id);
  }
  // Keep any setup row that non-demo data still points at.
  const demoSessionIds = sessions.map((s) => s.id);
  const demoSavedIds = saved.map((s) => s.id);
  const notIn = (col: string, ids: string[]) => (ids.length ? `${col} NOT IN (${ids.map(() => "?").join(",")})` : "1=1");
  const used = new Set<string>();
  const q = async (sql: string, args: string[]) => {
    for (const r of (await db.execute({ sql, args })).rows) for (const v of Object.values(r)) if (v) used.add(String(v));
  };
  await q(`SELECT current_setup_id FROM sessions WHERE ${notIn("id", demoSessionIds)}`, demoSessionIds);
  await q(`SELECT setup_id FROM runs WHERE ${notIn("session_id", demoSessionIds)}`, demoSessionIds);
  await q(`SELECT before_setup_id, after_setup_id FROM changes WHERE ${notIn("session_id", demoSessionIds)}`, demoSessionIds);
  await q(`SELECT setup_id FROM saved_setups WHERE ${notIn("id", demoSavedIds)}`, demoSavedIds);
  const dropSetups = [...setupIds].filter((id) => !used.has(id));

  const stmts: { sql: string; args: string[] }[] = [];
  for (const id of demoSessionIds) {
    stmts.push({ sql: "DELETE FROM runs WHERE session_id = ?", args: [id] });
    stmts.push({ sql: "DELETE FROM changes WHERE session_id = ?", args: [id] });
    stmts.push({ sql: "DELETE FROM sessions WHERE id = ?", args: [id] });
  }
  for (const id of demoSavedIds) stmts.push({ sql: "DELETE FROM saved_setups WHERE id = ?", args: [id] });
  for (const id of dropSetups) stmts.push({ sql: "DELETE FROM setups WHERE id = ?", args: [id] });
  if (stmts.length) await db.batch(stmts, "write");
  return { sessions: demoSessionIds.length, saved: demoSavedIds.length, setups: dropSetups.length };
}

async function main() {
  await openDb(config.vaultDbUrl);
  console.log(`seed-demo: database ${config.vaultDbUrl}`);
  // "What has worked for you" (race day) pools the outcomes of every session, so demo outcomes would mix
  // with real ones. Ask for an explicit --yes before seeding a vault that already holds real sessions.
  const real = Number(
    (
      await getDb().execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE NOT (json_extract(conditions, '$.trackName') LIKE 'DEMO%' AND notes LIKE '%demo data%')",
      )
    ).rows[0]!.n,
  );
  if (real > 0 && !process.argv.includes("--yes")) {
    console.error(
      `seed-demo: this database already has ${real} real session(s). Demo outcomes would show up in race day's\n` +
        '  "What has worked for you" next to yours. Use a separate database (PIT_DB_URL=file:/abs/path/demo.db),\n' +
        "  or run `npm run seed:demo -- --yes` to add the demo rows anyway (real rows are never changed).",
    );
    closeDb();
    process.exit(2);
  }
  const removed = await removePreviousDemo();
  if (removed.sessions || removed.saved)
    console.log(`  removed previous demo rows: ${removed.sessions} sessions, ${removed.saved} saved setups, ${removed.setups} setup rows`);

  // ---- session 1: DEMO track (asphalt, low grip) ----
  const track: TrackConditions = {
    trackName: "DEMO track",
    surface: "asphalt",
    grip: "low",
    bumpy: false,
    layout: "medium",
    airTempC: 21,
    trackTempC: 26,
    timeOfDay: "midday",
    dusty: true,
    notes: "DEMO conditions",
  };
  const s1 = await repo.createSession({ date: "2026-10-04", car: "yokomo-bd12", conditions: track, notes: DEMO_NOTE });
  const out: string[] = [];
  out.push(`session "DEMO track" ${s1.id}`);

  // The stock BD12 sheet has no value for these two, so the driver "enters" them first.
  const entered = await repo.applySetupChanges(s1.id, { rearShockPos: 2, rearDiffOilCst: 5000 }, { source: "manual" });
  out.push("  manual: rearShockPos - -> 2, rearDiffOilCst - -> 5000 (entering current values)");

  const r1 = await repo.addRun(s1.id, {
    lapTimesMs: laps(15.4),
    rating: 2,
    feel: ["exit-oversteer"],
    notes: "DEMO run 1: demo data, not real laps. Loose on power out of the hairpin.",
  });
  out.push(`  run 1: 10 laps, mean 15.40 s (${r1.id})`);

  const a = await repo.applySetupChanges(s1.id, { rearShockPos: 3 }, {
    source: "coach",
    leverId: "xo-rear-shocks-up",
    symptomId: "exit-oversteer",
  });
  const r2 = await repo.addRun(s1.id, {
    lapTimesMs: laps(15.36),
    rating: 3,
    feel: ["exit-oversteer"],
    notes: "DEMO run 2: demo data, not real laps. About the same.",
  });
  await repo.setChangeOutcome(a.changes[0]!.id, "same", r2.id);
  out.push("  coach: rearShockPos 2 -> 3 (xo-rear-shocks-up), outcome same");
  out.push(`  run 2: 10 laps, mean 15.36 s, within the noise of run 1 (${r2.id})`);

  const b = await repo.applySetupChanges(s1.id, { rearDiffOilCst: 4000 }, {
    source: "coach",
    leverId: "xo-rear-diff-softer",
    symptomId: "exit-oversteer",
  });
  const r3 = await repo.addRun(s1.id, {
    lapTimesMs: laps(14.9),
    rating: 4,
    feel: [],
    notes: "DEMO run 3: demo data, not real laps. Rear stays planted on exit.",
  });
  await repo.setChangeOutcome(b.changes[0]!.id, "better", r3.id);
  const bestSetupId = b.setup.id;
  out.push("  coach: rearDiffOilCst 5000 -> 4000 (xo-rear-diff-softer), outcome better");
  out.push(`  run 3: 10 laps, mean 14.90 s, above the noise vs run 2 (${r3.id})`);

  const c = await repo.applySetupChanges(s1.id, { frontToeOutDeg: 1.5 }, { source: "manual" });
  await repo.setChangeOutcome(c.changes[0]!.id, "worse");
  const rv = await repo.applySetupChanges(s1.id, { frontToeOutDeg: 1 }, { source: "revert" });
  out.push("  manual: frontToeOutDeg 1 -> 1.5, outcome worse; reverted to 1");

  // ---- session 2: DEMO Indoor Hall (carpet) ----
  const hall: TrackConditions = {
    trackName: "DEMO Indoor Hall",
    surface: "carpet",
    grip: "high",
    bumpy: false,
    layout: "tight",
    airTempC: 19,
    trackTempC: 19,
    timeOfDay: "evening",
    notes: "DEMO conditions",
  };
  const s2 = await repo.createSession({ date: "2026-09-27", car: "yokomo-bd12", conditions: hall, notes: DEMO_NOTE });
  const h = await repo.applySetupChanges(s2.id, { frontCamberDeg: 2, rideHeightFrontMm: 5.4, rearShockPos: 2 }, { source: "manual" });
  out.push(`session "DEMO Indoor Hall" ${s2.id}`);
  out.push("  manual: frontCamberDeg 1.5 -> 2, rideHeightFrontMm 5 -> 5.4, rearShockPos - -> 2");

  // ---- saved setups: two asphalt tracks, one carpet ----
  const saved = [
    await repo.saveSetup({
      label: "DEMO: DEMO track, low grip (best run 3)",
      setupId: bestSetupId,
      conditions: track,
      sessionId: s1.id,
      runId: r3.id,
      eventName: "DEMO practice day",
      verdict: "DEMO data, not a real result",
    }),
    await repo.saveSetup({
      label: "DEMO: Lakeside, high grip asphalt",
      setupId: r1.setupId,
      conditions: {
        trackName: "DEMO Lakeside",
        surface: "asphalt",
        grip: "high",
        bumpy: true,
        layout: "fast",
        airTempC: 28,
        trackTempC: 38,
        timeOfDay: "midday",
        notes: "DEMO conditions",
      },
      eventName: "DEMO club round",
      verdict: "DEMO data, not a real result",
    }),
    await repo.saveSetup({
      label: "DEMO: Indoor Hall carpet",
      setupId: h.setup.id,
      conditions: hall,
      sessionId: s2.id,
      eventName: "DEMO winter series",
      verdict: "DEMO data, not a real result",
    }),
  ];
  for (const s of saved) out.push(`saved setup "${s.label}" (${s.conditions.surface}) ${s.id}`);

  // A fresh browser opens the newest session, so demo sessions are dated before any real session
  // (and DEMO track after DEMO Indoor Hall). With no real sessions, DEMO track is the one that opens.
  const db = getDb();
  const oldest = (
    await db.execute({ sql: "SELECT MIN(created_at) AS m FROM sessions WHERE id NOT IN (?, ?)", args: [s1.id, s2.id] })
  ).rows[0]?.m;
  // The session starts 9 x 12 minutes before `top` and its 8 timeline events follow, so nothing is in the future.
  const top = (oldest === null || oldest === undefined ? Date.now() : Number(oldest) - 60_000) - 9 * 12 * 60_000;
  await db.batch(
    [
      { sql: "UPDATE sessions SET created_at = ? WHERE id = ?", args: [top, s1.id] },
      { sql: "UPDATE sessions SET created_at = ? WHERE id = ?", args: [top - 7 * 86_400_000, s2.id] },
    ],
    "write",
  );
  // Everything above was written within a second; space the events out (12 minutes apart) so the
  // session log lists them in the order they happened.
  const timeline: [table: "changes" | "runs", ids: string[]][] = [
    ["changes", entered.changes.map((x) => x.id)],
    ["runs", [r1.id]],
    ["changes", a.changes.map((x) => x.id)],
    ["runs", [r2.id]],
    ["changes", b.changes.map((x) => x.id)],
    ["runs", [r3.id]],
    ["changes", c.changes.map((x) => x.id)],
    ["changes", rv.changes.map((x) => x.id)],
  ];
  await db.batch(
    timeline.flatMap(([table, ids], i) =>
      ids.map((id) => ({ sql: `UPDATE ${table} SET created_at = ? WHERE id = ?`, args: [top + (i + 1) * 12 * 60_000, id] })),
    ),
    "write",
  );
  await db.batch(
    h.changes.map((x) => ({ sql: "UPDATE changes SET created_at = ? WHERE id = ?", args: [top - 7 * 86_400_000 + 10 * 60_000, x.id] })),
    "write",
  );
  if (oldest !== null && oldest !== undefined) out.push("demo sessions dated before your real sessions, so the app still opens yours first");

  console.log(out.join("\n"));
  console.log("seed-demo: done. Every row above is labelled DEMO; re-run to replace them.");
  closeDb();
}

main().catch((e) => {
  console.error(`seed-demo failed: ${(e as Error).message}`);
  process.exit(1);
});
