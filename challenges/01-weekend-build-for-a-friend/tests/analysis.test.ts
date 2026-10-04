import { describe, expect, it } from "vitest";
import { compareRuns, noiseFloor, pooledSd } from "../server/analysis/compare";
import { paramHistory } from "../server/analysis/history";
import { similarSetups } from "../server/analysis/similar";
import { loadLevers, loadParams } from "../server/engine/data";
import { getChunk } from "../server/kb/search";
import type { Change, Run, SavedSetup, Session, Setup, TrackConditions } from "../src/shared/types";

const ctx = { params: loadParams().params, levers: loadLevers() };
const NOW = Date.UTC(2026, 9, 4);

const today: TrackConditions = { trackName: "Club Track", surface: "asphalt", grip: "medium", bumpy: false, trackTempC: 25, layout: "medium", timeOfDay: "morning" };
const setup = (id: string, values: Setup["values"]): Setup => ({ id, values, createdAt: 1 });
const saved = (id: string, setupId: string, conditions: Partial<TrackConditions>, createdAt = NOW): SavedSetup => ({
  id,
  label: id,
  setupId,
  conditions: { ...today, ...conditions },
  createdAt,
});

describe("similarSetups", () => {
  const setups = new Map([
    ["su-a", setup("su-a", { rearArbMm: 1.2, casterDeg: 8 })],
    ["su-b", setup("su-b", { rearArbMm: 1.1, casterDeg: 8 })],
    ["su-c", setup("su-c", { rearArbMm: 1.2, casterDeg: 8 })],
  ]);
  const current = { rearArbMm: 1.2, casterDeg: 6 };

  it("ranks the same track and surface above a different track", () => {
    const hits = similarSetups(today, [saved("other", "su-b", { trackName: "Elsewhere" }), saved("same", "su-a", {})], current, setups, NOW);
    expect(hits.map((h) => h.saved.id)).toEqual(["same", "other"]);
    expect(hits[0]!.score).toBeGreaterThan(hits[1]!.score);
    expect(hits[0]!.reasons).toContain("same track");
    expect(hits[0]!.reasons).toContain("same grip");
  });

  it("groups a different surface separately even when everything else matches", () => {
    const hits = similarSetups(today, [saved("carpet", "su-c", { surface: "carpet" }), saved("other", "su-b", { trackName: "Elsewhere", grip: "low" })], current, setups, NOW);
    expect(hits[0]!.saved.id).toBe("other");
    expect(hits[1]!.saved.id).toBe("carpet");
    expect(hits[1]!.surfaceMismatch).toBe(true);
    expect(hits[0]!.surfaceMismatch).toBe(false);
    expect(hits[1]!.score).toBeGreaterThan(hits[0]!.score); // closer on paper, still grouped last
  });

  it("scores 100 for identical conditions saved now and explains deviations", () => {
    const [exact] = similarSetups(today, [saved("x", "su-a", {})], current, setups, NOW);
    expect(exact!.score).toBe(100);
    const [warm] = similarSetups(today, [saved("w", "su-a", { trackTempC: 29, grip: "low" })], current, setups, NOW);
    expect(warm!.reasons).toContain("track 4 C warmer when saved");
    expect(warm!.reasons).toContain("grip one step lower when saved");
  });

  it("lists the params that differ from the current setup with direction", () => {
    const [h] = similarSetups(today, [saved("x", "su-b", {})], current, setups, NOW);
    expect(h!.diffVsCurrent).toEqual([
      { param: "rearArbMm", from: 1.2, to: 1.1, direction: "decrease" },
      { param: "casterDeg", from: 6, to: 8, direction: "increase" },
    ]);
  });

  it("decays the recency weight with age", () => {
    const [fresh] = similarSetups(today, [saved("f", "su-a", {}, NOW)], current, setups, NOW);
    const [old] = similarSetups(today, [saved("o", "su-a", {}, NOW - 365 * 86_400_000)], current, setups, NOW);
    expect(fresh!.score).toBeGreaterThan(old!.score);
  });
});

const session: Session = { id: "s1", date: "2026-10-04", car: "yokomo-bd12", conditions: today, currentSetupId: "su1", createdAt: 1 };
const run = (id: string, seq: number, lapsS: number[] | undefined, over: Partial<Run> = {}): Run => ({
  id,
  sessionId: "s1",
  seq,
  setupId: "su1",
  lapTimesMs: lapsS?.map((s) => Math.round(s * 1000)),
  feel: [],
  createdAt: seq,
  ...over,
});
const bundle = (r: Run, values: Setup["values"], sess: Session = session) => ({ run: r, setup: setup(r.setupId, values), session: sess });

/** Laps with a known mean and a (sample) SD of exactly `sd`: alternating mean +/- d. */
const laps = (mean: number, n: number, d: number): number[] => Array.from({ length: n }, (_, i) => mean + (i % 2 === 0 ? d : -d));

describe("noise floor", () => {
  it("is about 0.19 s for sigma 0.15 s and n 10 (the notes' worked example)", () => {
    expect(noiseFloor(0.15, 10)).toBeCloseTo(0.1878, 3);
    expect(noiseFloor(0.15, 10).toFixed(2)).toBe("0.19");
  });
  it("pools the SD weighting by degrees of freedom", () => {
    expect(pooledSd([1, 3], [5, 5])).toBeCloseTo(Math.sqrt((2 + 0) / 2), 6);
  });
});

describe("compareRuns lap statistics", () => {
  const values = { rearArbMm: 1.2 };

  it("returns within-noise for a 0.11 s gap under the floor, with no winner", () => {
    // sigma ~0.15 (alternating +/-0.1 with n 10 gives sample SD 0.105; use +/-0.15 -> SD ~0.158).
    const a = laps(20.0, 10, 0.15);
    const b = laps(20.11, 10, 0.15);
    const cmp = compareRuns(bundle(run("a", 1, a), values), bundle(run("b", 2, b), values), ctx);
    expect(cmp.lapStats.status).toBe("within-noise");
    expect(cmp.lapStats.delta!).toBeGreaterThan(0.11);
    expect(cmp.lapStats.diffS!).toBeCloseTo(0.11, 2);
    expect(cmp.lapStats.text).toContain("No clear difference");
    expect(cmp.lapStats.text).toContain("noise floor");
    expect(cmp.lapStats.text).not.toMatch(/faster|slower|caused/i);
  });

  it("returns above-noise with the not-independent caveat and never says caused", () => {
    const cmp = compareRuns(bundle(run("a", 1, laps(20.0, 10, 0.05)), values), bundle(run("b", 2, laps(19.6, 10, 0.05)), values), ctx);
    expect(cmp.lapStats.status).toBe("above-noise");
    expect(cmp.lapStats.diffS!).toBeLessThan(0);
    expect(cmp.lapStats.text).toContain("Run B was 0.40 s faster");
    expect(cmp.lapStats.text).toContain("not independent");
    expect(cmp.lapStats.text).not.toMatch(/caused/i);
  });

  it("returns insufficient-data with fewer than 3 laps in either run", () => {
    const cmp = compareRuns(bundle(run("a", 1, [20, 20.1]), values), bundle(run("b", 2, laps(20, 10, 0.1)), values), ctx);
    expect(cmp.lapStats.status).toBe("insufficient-data");
    expect(cmp.lapStats.delta).toBeUndefined();
    expect(compareRuns(bundle(run("a", 1, undefined), values), bundle(run("b", 2, undefined), values), ctx).lapStats.status).toBe("insufficient-data");
  });
});

describe("compareRuns setup and condition differences", () => {
  it("sets confounded when two params changed", () => {
    const cmp = compareRuns(bundle(run("a", 1, []), { rearArbMm: 1.2, casterDeg: 6 }), bundle(run("b", 2, []), { rearArbMm: 1.1, casterDeg: 8 }), ctx);
    expect(cmp.setupDiffs).toHaveLength(2);
    expect(cmp.confounded).toBe(true);
    expect(cmp.confoundText).toContain("2 things changed at once");
    expect(cmp.confoundText).toContain("one change at a time");
  });

  it("does not flag a single param change between consecutive runs of one session", () => {
    const cmp = compareRuns(bundle(run("a", 1, []), { rearArbMm: 1.2 }), bundle(run("b", 2, []), { rearArbMm: 1.1 }), ctx);
    expect(cmp.confounded).toBe(false);
    expect(cmp.conditionDiffs.some((d) => d.text.includes("came later in the same session"))).toBe(true);
    expect(cmp.conditionDiffs.find((d) => d.text.includes("later"))!.citations).toContain("vehicle-dynamics-fundamentals#track-grip-changes-across-a-race-day");
  });

  it("includes the lever row's effect and citations for a changed (param, direction)", () => {
    const cmp = compareRuns(bundle(run("a", 1, []), { rearArbMm: 1.2 }), bundle(run("b", 2, []), { rearArbMm: 1.1 }), ctx);
    const d = cmp.setupDiffs[0]!;
    expect(d.direction).toBe("decrease");
    expect(d.leverId).toBe("xo-rear-arb-thinner");
    expect(d.effect).toContain("notes say more on-power rear traction");
    expect(d.effect).toContain("draft note");
    const row = ctx.levers.find((l) => l.id === "xo-rear-arb-thinner")!;
    expect(row.citations.length).toBeGreaterThan(0);
    for (const c of row.citations) expect(d.citations).toContain(c);
    for (const c of d.citations) expect(getChunk(c), c).toBeDefined();
  });

  it("gives no effect text when no lever row exists for the direction", () => {
    const cmp = compareRuns(bundle(run("a", 1, []), { spurT: 80 }), bundle(run("b", 2, []), { spurT: 84 }), ctx);
    expect(cmp.setupDiffs[0]!.effect).toBeUndefined();
    expect(cmp.setupDiffs[0]!.citations).toEqual([]);
  });

  it("notes track temperature 5 C or more, grip change and 3+ tyre runs, and counts them as things changed", () => {
    const s2: Session = { ...session, id: "s2", conditions: { ...today, trackTempC: 31, grip: "high" } };
    const rb = run("b", 1, [], { sessionId: "s2" });
    const cmp = compareRuns(bundle(run("a", 1, []), { rearArbMm: 1.2, tyreRunsOnSet: 1 }), bundle(rb, { rearArbMm: 1.2, tyreRunsOnSet: 4 }, s2), ctx);
    const texts = cmp.conditionDiffs.map((d) => d.text).join(" | ");
    expect(texts).toContain("6 C warmer");
    expect(texts).toContain("grip was rated medium for run A and high for run B");
    expect(texts).toContain("3 more runs");
    expect(cmp.conditionDiffs.find((d) => d.text.includes("tyre set"))!.citations).toContain("touring-car-traction-and-tire-management#tyre-diameter-is-a-geometry-input-not-just-a-wea");
    expect(cmp.confounded).toBe(true);
    expect(cmp.confoundText).toContain("3 things changed at once"); // temp, grip, tyre runs; tyreRunsOnSet not double counted
  });

  it("treats the tyre-run counter as a condition only: no setup diff, not confounded by itself (T7)", () => {
    // The session log writes tyreRunsOnSet to a new setup row before each run; one real change plus one more run.
    const cmp = compareRuns(
      bundle(run("a", 1, []), { rearArbMm: 1.2, tyreRunsOnSet: 1 }),
      bundle(run("b", 2, []), { rearArbMm: 1.1, tyreRunsOnSet: 2 }),
      ctx,
    );
    expect(cmp.setupDiffs.map((d) => d.param)).toEqual(["rearArbMm"]);
    expect(cmp.conditionDiffs.some((d) => d.text.includes("tyre set"))).toBe(false); // under 3 runs: no note
    expect(cmp.confounded).toBe(false);
  });

  it("ignores a temperature gap under 5 C", () => {
    const s2: Session = { ...session, id: "s2", conditions: { ...today, trackTempC: 28 } };
    const cmp = compareRuns(bundle(run("a", 1, []), { rearArbMm: 1.2 }), bundle(run("b", 1, [], { sessionId: "s2" }), { rearArbMm: 1.2 }, s2), ctx);
    expect(cmp.conditionDiffs).toEqual([]);
    expect(cmp.confounded).toBe(false);
  });
});

describe("paramHistory", () => {
  const ch = (id: string, param: string, from: number, to: number, outcome?: Change["outcome"], source: Change["source"] = "coach"): Change => ({
    id,
    sessionId: "s1",
    beforeSetupId: "a",
    afterSetupId: "b",
    param,
    from,
    to,
    source,
    outcome,
    createdAt: 1,
  });

  it("counts better/same/worse per (param, direction) across sessions", () => {
    const rows = paramHistory([
      ch("1", "rearArbMm", 1.2, 1.1, "better"),
      ch("2", "rearArbMm", 1.1, 1.0, "better"),
      ch("3", "rearArbMm", 1.2, 1.1, "worse"),
      ch("4", "rearArbMm", 1.0, 1.1, "same"),
      ch("5", "casterDeg", 6, 8),
      ch("6", "rearArbMm", 1.1, 1.2, undefined, "revert"),
      ch("7", "tyreRunsOnSet", 1, 2, undefined, "manual"), // T7: tyre counter is not a try
    ]);
    expect(rows.some((r) => r.param === "tyreRunsOnSet")).toBe(false);
    const dec = rows.find((r) => r.param === "rearArbMm" && r.direction === "decrease")!;
    expect(dec).toMatchObject({ tries: 3, better: 2, same: 0, worse: 1 });
    const inc = rows.find((r) => r.param === "rearArbMm" && r.direction === "increase")!;
    expect(inc).toMatchObject({ tries: 1, better: 0, same: 1, worse: 0 }); // revert not counted
    const caster = rows.find((r) => r.param === "casterDeg")!;
    expect(caster).toMatchObject({ tries: 1, better: 0, same: 0, worse: 0 }); // no outcome tap yet
    expect(rows[0]).toBe(dec); // most tries first
    expect(rows.every((r) => r.label === "your feel, not lap-time proof")).toBe(true);
  });
});
