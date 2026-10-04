// Pure helpers for the Race day screen (T4c). No DOM or Preact imports.
import type { ParamDef, ParamDiff, ParamHistoryRow, SimilarHit } from "../../shared/types";

/** Tyre wear is a condition, not a setup change (the server leaves it out of run comparison too). */
export const TYRE_RUNS_PARAM = "tyreRunsOnSet";

/** Always shown with history rows: they are the driver's own outcome taps. */
export const HISTORY_LABEL = "your feel, not lap-time proof";

/** The weights behind the score (plan 4.6). Stated as a judgement call: they are not from any source. */
export const WEIGHTS_TEXT =
  "The score is a weighted match on the fields both setups have: track name 3, surface 3, grip 2, bumpy 1.5, track temperature 1.5, layout 1, time of day 0.5, air temperature 0.5, how recently it was saved 0.5. " +
  "These weights are a judgement call. They are not from any source in the notes, so treat the ranking as a sorted shortlist, not a measurement.";

/** Params that Load would stage: drops the tyre-run counter and computed values (those follow from other fields). */
export function loadableDiff(diff: ParamDiff[], params: ParamDef[]): ParamDiff[] {
  const computed = new Set(params.filter((p) => p.kind === "computed").map((p) => p.id));
  return diff.filter((d) => d.param !== TYRE_RUNS_PARAM && !computed.has(d.param));
}

/** Same-surface hits first (ranked by the server), then the "other surface" group. */
export function splitHits(hits: SimilarHit[]): { same: SimilarHit[]; other: SimilarHit[] } {
  return { same: hits.filter((h) => !h.surfaceMismatch), other: hits.filter((h) => h.surfaceMismatch) };
}

export function directionWord(direction: string): string {
  if (direction === "increase") return "raised";
  if (direction === "decrease") return "lowered";
  return "changed";
}

/** "3 tries: 2 better, 1 same, 0 worse (tapped 3 of 3)" */
export function historySummary(r: ParamHistoryRow): string {
  const tapped = r.better + r.same + r.worse;
  const base = `${r.better} better, ${r.same} same, ${r.worse} worse`;
  return tapped < r.tries ? `${base} (${tapped} of ${r.tries} rated)` : base;
}

export function tryWord(n: number): string {
  return n === 1 ? "1 try" : `${n} tries`;
}

export function paramCountText(n: number): string {
  if (n === 0) return "Same settings as now";
  return n === 1 ? "1 param differs from now" : `${n} params differ from now`;
}
