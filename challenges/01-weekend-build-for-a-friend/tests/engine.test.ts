import { describe, expect, it } from "vitest";
import { loadLevers, loadParams, loadPrechecks, loadSymptoms } from "../server/engine/data";
import { keywordClassify, refusalFor } from "../server/engine/keyword";
import { NO_LEVER_REASON, selectLevers, type SelectLeversArgs } from "../server/engine/levers";
import { getChunk, search } from "../server/kb/search";
import type { Change, LeverRow, ParamDef, SetupValues } from "../src/shared/types";

const params = loadParams().params;
const levers = loadLevers();
const symptoms = loadSymptoms();

/** A stock BD12: the factory value where Yokomo gives one, otherwise null (unknown). */
const stock: SetupValues = Object.fromEntries(params.map((p) => [p.id, p.bd12 ?? null]));

const base = (over: Partial<SelectLeversArgs>): SelectLeversArgs => ({
  symptomId: "exit-oversteer",
  phase: "exit",
  grip: "medium",
  setup: stock,
  params,
  levers,
  history: [],
  reviewedOnly: false,
  ...over,
});

const change = (over: Partial<Change>): Change => ({
  id: "c1",
  sessionId: "s1",
  beforeSetupId: "a",
  afterSetupId: "b",
  param: "rearShockPos",
  from: 2,
  to: 3,
  source: "coach",
  createdAt: 1,
  ...over,
});

const row = (over: Partial<LeverRow>): LeverRow => ({
  id: "t-row",
  symptomId: "test",
  phases: ["none"],
  kind: "numeric",
  action: "a",
  effect: "e",
  tradeOff: "t",
  verify: "v",
  citations: [],
  priority: 1,
  basis: "stated",
  status: "reviewed",
  ...over,
});

describe("domain data", () => {
  it("loads and validates the four files with the expected counts", () => {
    expect(params).toHaveLength(37);
    expect(symptoms).toHaveLength(12);
    expect(loadPrechecks()).toHaveLength(14);
    expect(levers).toHaveLength(61);
    expect(levers.filter((l) => l.status === "reviewed")).toHaveLength(12);
  });
});

describe("selectLevers", () => {
  it("skips xo-rear-toe-in-more as at-limit on a stock BD12 (3.5 deg is the top of the range)", () => {
    const s = selectLevers(base({}));
    expect(s.skipped).toContainEqual({ leverId: "xo-rear-toe-in-more", reason: "at-limit" });
    expect(s.primary?.lever.id).not.toBe("xo-rear-toe-in-more");
    // medium grip: the low-grip diff row is a grip mismatch, so the shocks row is primary and needs a value
    expect(s.primary?.lever.id).toBe("xo-rear-shocks-up");
    expect(s.primary?.needsCurrentValue).toBe(true);
  });

  it("gives xo-rear-shocks-up its numbers once the current value is known, with a scene binding", () => {
    const s = selectLevers(base({ setup: { ...stock, rearShockPos: 2 } }));
    expect(s.primary?.lever.id).toBe("xo-rear-shocks-up");
    expect(s.primary).toMatchObject({ from: 2, to: 3, needsCurrentValue: false, atLimit: false });
    expect(s.primary?.scene).toEqual({ explainer: "shockAngle", param: "rearShockPos", from: 2, to: 3 });
  });

  it("clamps at the minimum instead of overshooting", () => {
    // eu-caster-down: casterDeg, decrease, step 1, min 2
    const s = selectLevers(base({ symptomId: "entry-understeer", phase: "entry", setup: { ...stock, casterDeg: 2.5 } }));
    expect(s.primary?.lever.id).toBe("eu-caster-down");
    expect(s.primary).toMatchObject({ from: 2.5, to: 2, atLimit: false });
    // and at the minimum there is nothing left to do
    const s2 = selectLevers(base({ symptomId: "entry-understeer", phase: "entry", setup: { ...stock, casterDeg: 2 } }));
    expect(s2.skipped).toContainEqual({ leverId: "eu-caster-down", reason: "at-limit" });
    expect(s2.primary?.lever.id).not.toBe("eu-caster-down");
  });

  it("does not move a value that is outside the bounds against the lever's direction", () => {
    const s = selectLevers(base({ symptomId: "entry-understeer", phase: "entry", setup: { ...stock, casterDeg: 1 } }));
    expect(s.skipped).toContainEqual({ leverId: "eu-caster-down", reason: "at-limit" });
  });

  it("returns needsCurrentValue with null from/to when the setup has no value", () => {
    const s = selectLevers(base({ symptomId: "entry-understeer", phase: "entry" }));
    expect(s.primary?.lever.id).toBe("eu-caster-down");
    expect(s.primary).toMatchObject({ from: null, to: null, needsCurrentValue: true, atLimit: false });
    expect(s.primary?.scene).toBeUndefined();
  });

  it("skips a lever whose (param, direction) was tried with outcome worse, and same", () => {
    const setup = { ...stock, rearShockPos: 2 };
    const worse = selectLevers(base({ setup, history: [change({ outcome: "worse" })] }));
    expect(worse.skipped).toContainEqual({ leverId: "xo-rear-shocks-up", reason: "tried-worse" });
    expect(worse.primary?.lever.id).not.toBe("xo-rear-shocks-up");
    const same = selectLevers(base({ setup, history: [change({ outcome: "same" })] }));
    expect(same.skipped).toContainEqual({ leverId: "xo-rear-shocks-up", reason: "tried-same" });
    // a better outcome, the opposite direction, or an old change (outside the last 3) does not skip it
    const better = selectLevers(base({ setup, history: [change({ outcome: "better" })] }));
    expect(better.primary?.lever.id).toBe("xo-rear-shocks-up");
    const opposite = selectLevers(base({ setup, history: [change({ outcome: "worse", from: 3, to: 2 })] }));
    expect(opposite.primary?.lever.id).toBe("xo-rear-shocks-up");
    const old = [
      change({ id: "old", outcome: "worse" }),
      change({ id: "n1", param: "x", from: 1, to: 2, outcome: "better" }),
      change({ id: "n2", param: "x", from: 2, to: 3, outcome: "better" }),
      change({ id: "n3", param: "x", from: 3, to: 4, outcome: "better" }),
    ];
    expect(selectLevers(base({ setup, history: old })).primary?.lever.id).toBe("xo-rear-shocks-up");
  });

  it("steps enum params to the neighbouring option and stops at the end", () => {
    const hex = params.find((p) => p.id === "rearHexMm") as ParamDef;
    expect(hex.kind).toBe("enum");
    const lowGrip = { grip: "low" as const, reviewedOnly: false };
    // xo-rear-track-narrower: rearHexMm, decrease, step 1 (ignored for enums)
    const only = levers.filter((l) => l.id === "xo-rear-track-narrower");
    const s = selectLevers(base({ ...lowGrip, levers: only, setup: { ...stock, rearHexMm: 4.5 } }));
    expect(s.primary).toMatchObject({ from: 4.5, to: 4.3 });
    const s2 = selectLevers(base({ ...lowGrip, levers: only, setup: { ...stock, rearHexMm: 4 } }));
    expect(s2.skipped).toContainEqual({ leverId: "xo-rear-track-narrower", reason: "at-limit" });
    // a value between options moves to the next option in the direction
    const up = selectLevers({
      ...base({}),
      symptomId: "test",
      phase: "none",
      levers: [row({ param: "rearHexMm", direction: "increase" })],
      setup: { rearHexMm: 4.3 },
    });
    expect(up.primary).toMatchObject({ from: 4.3, to: 4.5 });
  });

  it("hides draft rows when reviewedOnly is on", () => {
    const s = selectLevers(base({ reviewedOnly: true, grip: "low" }));
    const shown = [s.primary, ...s.alternatives].filter(Boolean).map((x) => x!.lever);
    expect(shown.length).toBeGreaterThan(0);
    expect(shown.every((l) => l.status === "reviewed")).toBe(true);
    const drafts = levers.filter((l) => l.symptomId === "exit-oversteer" && l.status === "draft");
    for (const d of drafts) expect(s.skipped).toContainEqual({ leverId: d.id, reason: "draft-hidden" });
  });

  it("prefers the reviewed diff-oil row for low-grip exit oversteer on a stock BD12", () => {
    const s = selectLevers(base({ grip: "low" }));
    expect(s.skipped).toContainEqual({ leverId: "xo-rear-toe-in-more", reason: "at-limit" });
    expect(s.primary?.lever.id).toBe("xo-rear-diff-softer");
    expect(s.primary?.needsCurrentValue).toBe(true);
    expect(s.alternatives[0]?.lever.id).toBe("xo-rear-shocks-up");
    expect(s.alternatives).toHaveLength(2);
  });

  it("returns primary plus at most two alternatives in priority order", () => {
    const s = selectLevers(base({ setup: { ...stock, rearShockPos: 2 } }));
    const ids = [s.primary, ...s.alternatives].map((x) => x!.lever.priority);
    expect(ids).toEqual([...ids].sort((a, b) => a - b));
    expect(s.alternatives.length).toBeLessThanOrEqual(2);
  });

  it("explains itself when nothing is left", () => {
    const s = selectLevers(base({ symptomId: "no-such-symptom" }));
    expect(s.primary).toBeNull();
    expect(s.noLeverReason).toBe(NO_LEVER_REASON);
  });

  it("passes qualitative rows through without clamping or history", () => {
    const s = selectLevers(base({ symptomId: "low-grip", phase: "none", grip: "low" }));
    const q = [s.primary, ...s.alternatives].find((x) => x?.lever.kind === "qualitative");
    expect(q).toMatchObject({ from: null, to: null, atLimit: false, needsCurrentValue: false });
  });
});

describe("refusalFor", () => {
  it("refuses tyre compound / shore / insert questions with the gap citation", () => {
    for (const q of ["what shore tyres", "Which foam insert is best?", "what compound should I run"]) {
      const r = refusalFor(q);
      expect(r?.reason, q).toBe("tyre-compound-gap");
      expect(r?.citations).toEqual(["touring-car-traction-and-tire-management#a-real-gap-not-an-extraction-failure"]);
      expect(getChunk(r!.citations[0]!)).toBeDefined();
    }
  });

  it("refuses ESC/motor, nitro, LiPo and other car types", () => {
    expect(refusalFor("what boost should I set on my ESC")?.reason).toBe("electronics");
    expect(refusalFor("How do I tune my nitro engine needle?")?.reason).toBe("other-car-type");
    expect(refusalFor("What charge rate should I use for my LiPo pack?")?.reason).toBe("electronics");
    expect(refusalFor("setting up my buggy for the dirt track")?.reason).toBe("other-car-type");
    expect(refusalFor("it's an off-road crawler")?.reason).toBe("other-car-type");
  });

  it("lets ordinary driving talk through", () => {
    for (const q of [
      "the rear steps out when I get on the power",
      "my motor gets hot after a few minutes",
      "it skips over the bumps and the car drifts wide",
      "the tyres are glued but I have no grip",
    ]) {
      expect(refusalFor(q), q).toBeNull();
    }
  });
});

describe("keywordClassify", () => {
  it("matches synonyms and falls back to token overlap", () => {
    expect(keywordClassify("it's loose on power coming out of the hairpin", symptoms)).toMatchObject({
      symptomId: "exit-oversteer",
      phase: "exit",
      source: "keyword",
    });
    expect(keywordClassify("the car pushes on turn-in", symptoms)?.symptomId).toBe("entry-understeer");
    expect(keywordClassify("my motor gets hot and it fades late", symptoms)?.symptomId).toBe("fade-late-run");
    expect(keywordClassify("front washes out", symptoms)?.symptomId).toBe("entry-understeer");
  });

  it("returns null for talk it cannot place", () => {
    expect(keywordClassify("", symptoms)).toBeNull();
    expect(keywordClassify("what a lovely day at the track", symptoms)).toBeNull();
  });
});

describe("kb search", () => {
  it("returns 3 chunks for droop, and chunks resolve by id", () => {
    const hits = search("droop", 3);
    expect(hits).toHaveLength(3);
    expect(getChunk(hits[0]!.id)).toEqual(hits[0]);
    expect(search("", 3)).toEqual([]);
  });
});
