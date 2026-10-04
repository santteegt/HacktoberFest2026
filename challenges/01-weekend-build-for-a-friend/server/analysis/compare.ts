// "What might have affected my run" (T8; plan 4.7). Pure: the route loads the bundles.
// Honest-statistics rules (docs/CHALLENGE-MEMORY.md): never say "caused", never name a winner when the
// gap is inside the noise floor, state the floor, and flag laps-within-a-run dependence.
import type { LeverRow, ParamDef, RunBundle, RunComparison, TrackConditions } from "../../src/shared/types";
import { diffSetups, fmt } from "./util";

export const CITE = {
  mde: "minimum-detectable-lap-time-difference#definition",
  dependence: "minimum-detectable-lap-time-difference#laps-within-a-single-run-are",
  noWinner: "minimum-detectable-lap-time-difference#any-setup-comparison-tool-should-report-an",
  paired: "minimum-detectable-lap-time-difference#a-paired-back-to-back-testing-design-same",
  gripEvolves: "vehicle-dynamics-fundamentals#track-grip-changes-across-a-race-day",
  tyreDiameter: "touring-car-traction-and-tire-management#tyre-diameter-is-a-geometry-input-not-just-a-wea",
} as const;

/** Extra field on top of the provisional `RunComparison` (change request: add to the zod schema). */
export type RunComparisonOut = RunComparison & { confoundCitations?: string[] };

const TYRE_RUNS_PARAM = "tyreRunsOnSet";
const TEMP_DELTA_C = 5;
const TYRE_RUNS_DELTA = 3;
const MIN_LAPS = 3;

export function mean(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

/** Sample standard deviation (n - 1). */
export function sd(xs: number[]): number {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((a, x) => a + (x - m) ** 2, 0) / (xs.length - 1));
}

/** Pooled SD of two samples (weights by n - 1). */
export function pooledSd(a: number[], b: number[]): number {
  const dof = a.length + b.length - 2;
  if (dof <= 0) return 0;
  return Math.sqrt(((a.length - 1) * sd(a) ** 2 + (b.length - 1) * sd(b) ** 2) / dof);
}

/** Smallest reliably-detectable lap-time difference: delta ~ 2.8 * sigma * sqrt(2 / n). Seconds in, seconds out. */
export function noiseFloor(sigma: number, n: number): number {
  return 2.8 * sigma * Math.sqrt(2 / n);
}

const s2 = (x: number): string => x.toFixed(2);

function lapStatsFor(a: number[] | undefined, b: number[] | undefined): RunComparison["lapStats"] {
  const la = a ?? [];
  const lb = b ?? [];
  if (la.length < MIN_LAPS || lb.length < MIN_LAPS) {
    return {
      status: "insufficient-data",
      n: Math.min(la.length, lb.length),
      text: `Not enough timed laps to compare: each run needs ${MIN_LAPS} or more (run A has ${la.length}, run B has ${lb.length}). No lap-time statistics shown.`,
      citations: [CITE.mde],
    };
  }
  const secA = la.map((ms) => ms / 1000);
  const secB = lb.map((ms) => ms / 1000);
  const meanA = mean(secA);
  const meanB = mean(secB);
  const sigma = pooledSd(secA, secB);
  const n = Math.min(secA.length, secB.length);
  const delta = noiseFloor(sigma, n);
  const diffS = meanB - meanA;
  const base = { meanA, meanB, sigma, n, delta, diffS };
  if (Math.abs(diffS) < delta) {
    return {
      status: "within-noise",
      ...base,
      text: `No clear difference: the gap (${s2(Math.abs(diffS))} s) is smaller than the noise floor (about ${s2(delta)} s). Mean lap was ${s2(meanA)} s in run A and ${s2(meanB)} s in run B. Treat the runs as equal until a paired, back-to-back test says otherwise.`,
      citations: [CITE.mde, CITE.noWinner, CITE.dependence],
    };
  }
  const word = diffS < 0 ? "faster" : "slower";
  return {
    status: "above-noise",
    ...base,
    text: `Run B was ${s2(Math.abs(diffS))} s ${word} on average, above the noise floor (about ${s2(delta)} s), but laps within a run are not independent, so treat it as a hint, not proof.`,
    citations: [CITE.mde, CITE.dependence],
  };
}

/** The best lever rows for a (param, direction): reviewed before draft, then by priority. */
function leverRowsFor(levers: LeverRow[], param: string, direction: string): LeverRow[] {
  return levers
    .filter((l) => l.param === param && l.direction === direction)
    .sort((x, y) => Number(y.status === "reviewed") - Number(x.status === "reviewed") || x.priority - y.priority)
    .slice(0, 2);
}

function conditionsOf(b: RunBundle): TrackConditions {
  return { ...b.session.conditions, ...(b.run.conditions ?? {}) } as TrackConditions;
}

function isLater(a: RunBundle, b: RunBundle): "A" | "B" | null {
  if (a.session.id !== b.session.id) return null;
  if (a.run.seq === b.run.seq) return null;
  return b.run.seq > a.run.seq ? "B" : "A";
}

export function compareRuns(a: RunBundle, b: RunBundle, ctx: { params: ParamDef[]; levers: LeverRow[] }): RunComparisonOut {
  const label = (id: string) => ctx.params.find((p) => p.id === id)?.label ?? id;
  const unit = (id: string) => ctx.params.find((p) => p.id === id)?.unit ?? "";

  // 1. Setup differences (A -> B).
  const setupDiffs: RunComparison["setupDiffs"] = diffSetups(a.setup.values, b.setup.values).map((d) => {
    const rows = d.direction === "changed" ? [] : leverRowsFor(ctx.levers, d.param, d.direction);
    const u = unit(d.param);
    const change = `${label(d.param)} ${fmt(d.from)} to ${fmt(d.to)}${u ? ` ${u}` : ""}`;
    if (rows.length === 0) return { ...d, citations: [] };
    const effect = rows
      .map((r, i) => `${i === 0 ? "" : "Also: "}${r.effect}${r.status === "draft" ? " (draft note, not yet reviewed)" : ""}`)
      .join(" ");
    return {
      ...d,
      leverId: rows[0]!.id,
      effect: `${change}: notes say ${effect.charAt(0).toLowerCase()}${effect.slice(1)}`,
      citations: [...new Set(rows.flatMap((r) => r.citations))],
    };
  });

  // 2. Condition differences.
  const ca = conditionsOf(a);
  const cb = conditionsOf(b);
  const conditionDiffs: RunComparison["conditionDiffs"] = [];
  let conditionThings = 0; // things the driver or the day changed; the "later run" note is informational only
  const note = (text: string, citations: string[] = [], counts = true) => {
    conditionDiffs.push({ text, citations });
    if (counts) conditionThings += 1;
  };

  if (ca.trackName.trim().toLowerCase() !== cb.trackName.trim().toLowerCase()) note(`Different track: ${ca.trackName} versus ${cb.trackName}.`);
  if (ca.surface !== cb.surface) note(`Surface changed from ${ca.surface} to ${cb.surface}.`, [CITE.gripEvolves]);
  if (ca.grip !== cb.grip) note(`Track grip was rated ${ca.grip} for run A and ${cb.grip} for run B.`, [CITE.gripEvolves]);
  if (ca.trackTempC !== undefined && cb.trackTempC !== undefined && Math.abs(cb.trackTempC - ca.trackTempC) >= TEMP_DELTA_C) {
    const d = cb.trackTempC - ca.trackTempC;
    note(`Track temperature was ${Math.abs(Math.round(d * 10) / 10)} C ${d > 0 ? "warmer" : "cooler"} for run B (${ca.trackTempC} C to ${cb.trackTempC} C).`, [CITE.gripEvolves]);
  }
  if (ca.timeOfDay && cb.timeOfDay && ca.timeOfDay !== cb.timeOfDay) note(`Time of day changed from ${ca.timeOfDay} to ${cb.timeOfDay}.`, [CITE.gripEvolves]);
  const ta = a.setup.values[TYRE_RUNS_PARAM];
  const tb = b.setup.values[TYRE_RUNS_PARAM];
  let tyreFlagged = false;
  if (typeof ta === "number" && typeof tb === "number" && Math.abs(tb - ta) >= TYRE_RUNS_DELTA) {
    tyreFlagged = true;
    note(`The tyre set has ${Math.abs(tb - ta)} ${tb > ta ? "more" : "fewer"} runs on it in run B (${ta} to ${tb}); wear changes tyre diameter, which shifts ride height and droop.`, [CITE.tyreDiameter]);
  }
  const later = isLater(a, b);
  if (later) {
    note(`Run ${later} came later in the same session (run ${a.run.seq} versus run ${b.run.seq}); grip usually climbs through a session, so a later run can be faster for reasons unrelated to the setup.`, [CITE.gripEvolves], false);
  }

  // 3. Lap-time statistics.
  const lapStats = lapStatsFor(a.run.lapTimesMs, b.run.lapTimesMs);

  // 4. Confounding: more than one thing changed (setup params plus real condition changes).
  const setupThings = setupDiffs.filter((d) => !(tyreFlagged && d.param === TYRE_RUNS_PARAM)).length;
  const things = setupThings + conditionThings;
  const confounded = things > 1;

  return {
    runA: a.run.id,
    runB: b.run.id,
    setupDiffs,
    conditionDiffs,
    lapStats,
    confounded,
    ...(confounded
      ? {
          confoundText: `${things} things changed at once (${setupThings} setup, ${conditionThings} conditions); the notes recommend one change at a time, back to back, so any difference cannot be pinned on one of them.`,
          confoundCitations: [CITE.paired],
        }
      : {}),
  };
}
