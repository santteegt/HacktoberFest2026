// Race-day finder: similar conditions (T8; plan 4.6). Pure: the route does the vault reads.
import type { Grip, SavedSetup, Setup, SetupValues, SimilarHit, TrackConditions } from "../../src/shared/types";
import { diffSetups } from "./util";

const GRIP_ORD: Record<Grip, number> = { low: 0, medium: 1, high: 2 };
const LAYOUT_ORD = { tight: 0, medium: 1, fast: 2 } as const;
const DAY_MS = 86_400_000;

/** Plan 4.6 weights. A judgement call (unsourced), stated as such in the UI tooltip. */
export const SIMILARITY_WEIGHTS = {
  trackName: 3,
  surface: 3,
  grip: 2,
  bumpy: 1.5,
  trackTempC: 1.5,
  layout: 1,
  timeOfDay: 0.5,
  airTempC: 0.5,
  recency: 0.5,
} as const;

interface Part {
  w: number;
  s: number;
  reason?: string;
}

const stepWord = (n: number): string => (n === 1 ? "one step" : n === 2 ? "two steps" : `${n} steps`);
const round1 = (n: number): string => String(Math.round(n * 10) / 10);

function tempPart(label: string, w: number, today?: number, saved?: number): Part | null {
  if (today === undefined || saved === undefined) return null;
  const d = saved - today;
  const s = Math.max(0, 1 - Math.abs(d) / 15);
  const reason =
    Math.abs(d) < 2
      ? `${label} within ${round1(Math.max(1, Math.abs(d)))} C`
      : `${label} ${round1(Math.abs(d))} C ${d > 0 ? "warmer" : "cooler"} when saved`;
  return { w, s, reason };
}

/** Score one saved setup's conditions against today's (0-100) with the reasons behind it. */
export function scoreConditions(
  today: TrackConditions,
  saved: TrackConditions,
  savedAt: number,
  now: number,
): { score: number; reasons: string[]; surfaceMismatch: boolean } {
  const W = SIMILARITY_WEIGHTS;
  const sameTrack = today.trackName.trim().toLowerCase() === saved.trackName.trim().toLowerCase();
  const sameSurface = today.surface === saved.surface;
  const parts: Part[] = [];

  parts.push({ w: W.trackName, s: sameTrack ? 1 : 0, reason: sameTrack ? "same track" : `different track (${saved.trackName})` });
  parts.push({ w: W.surface, s: sameSurface ? 1 : 0, reason: sameSurface ? undefined : `different surface (${saved.surface}, not ${today.surface})` });

  const gd = GRIP_ORD[saved.grip] - GRIP_ORD[today.grip];
  parts.push({
    w: W.grip,
    s: 1 - Math.abs(gd) / 2,
    reason: gd === 0 ? "same grip" : `grip ${stepWord(Math.abs(gd))} ${gd < 0 ? "lower" : "higher"} when saved`,
  });

  parts.push({ w: W.bumpy, s: today.bumpy === saved.bumpy ? 1 : 0, reason: today.bumpy === saved.bumpy ? undefined : saved.bumpy ? "bumpier when saved" : "smoother when saved" });

  const tt = tempPart("track", W.trackTempC, today.trackTempC, saved.trackTempC);
  if (tt) parts.push(tt);

  if (today.layout && saved.layout) {
    const ld = Math.abs(LAYOUT_ORD[today.layout] - LAYOUT_ORD[saved.layout]);
    parts.push({ w: W.layout, s: 1 - ld / 2, reason: ld === 0 ? undefined : `layout ${saved.layout}, not ${today.layout}` });
  }

  if (today.timeOfDay && saved.timeOfDay) {
    const same = today.timeOfDay === saved.timeOfDay;
    parts.push({ w: W.timeOfDay, s: same ? 1 : 0.5, reason: same ? undefined : `${saved.timeOfDay} when saved` });
  }

  const at = tempPart("air", W.airTempC, today.airTempC, saved.airTempC);
  if (at) parts.push({ w: at.w, s: at.s }); // air temp feeds the score but stays out of the reasons

  const ageDays = Math.max(0, (now - savedAt) / DAY_MS);
  parts.push({ w: W.recency, s: Math.max(0, 1 - ageDays / 365) });

  const wSum = parts.reduce((a, p) => a + p.w, 0);
  const sSum = parts.reduce((a, p) => a + p.w * p.s, 0);
  return {
    score: Math.round((sSum / wSum) * 1000) / 10,
    reasons: parts.map((p) => p.reason).filter((r): r is string => Boolean(r)),
    surfaceMismatch: !sameSurface,
  };
}

/**
 * Rank saved setups by similarity to today's conditions. Same-surface hits come first (best score first),
 * then hits on another surface (also best first), so a surface mismatch can never outrank a match.
 * `diffVsCurrent` lists, per param, what changes going from the current setup to the saved one.
 */
export function similarSetups(
  today: TrackConditions,
  saved: SavedSetup[],
  current: SetupValues,
  setups: Map<string, Setup>,
  now: number = Date.now(),
): SimilarHit[] {
  const hits: SimilarHit[] = saved.map((s) => {
    const { score, reasons, surfaceMismatch } = scoreConditions(today, s.conditions, s.createdAt, now);
    const target = setups.get(s.setupId);
    return { saved: s, score, reasons, surfaceMismatch, diffVsCurrent: target ? diffSetups(current, target.values) : [] };
  });
  return hits.sort((a, b) => Number(a.surfaceMismatch) - Number(b.surfaceMismatch) || b.score - a.score || b.saved.createdAt - a.saved.createdAt);
}
