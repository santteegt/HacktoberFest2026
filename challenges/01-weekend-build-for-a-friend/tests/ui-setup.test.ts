// Pure-logic tests for the Setup editor and Session screen (T4b): lap-time parsing, FDR, range flags, diffs, stepping.
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { ParamsFile } from "../src/shared/schemas";
import { bestOf, nextTyreRuns, parseLapTimes, parseOneLap } from "../src/ui/session/logic";
import {
  baselineOf,
  baselineValues,
  computeFdr,
  deltaMeaning,
  deltaText,
  diffValues,
  isOutOfRange,
  parseNumberInput,
  rangeUnsourced,
  stepValue,
} from "../src/ui/setup/logic";

const file = ParamsFile.parse(JSON.parse(readFileSync(new URL("../data/params.bd12.json", import.meta.url), "utf8")));
const params = file.params;
const P = (id: string) => params.find((p) => p.id === id)!;

describe("lap time parsing", () => {
  it("parses pasted seconds separated by spaces and commas", () => {
    const r = parseLapTimes("14.9 15.1, 14.8");
    expect(r.laps).toEqual([14900, 15100, 14800]);
    expect(r.bad).toEqual([]);
  });
  it("handles newlines, semicolons and m:ss", () => {
    expect(parseLapTimes("14.9\n15.1;1:14.8").laps).toEqual([14900, 15100, 74800]);
  });
  it("reports tokens that are not lap times", () => {
    const r = parseLapTimes("14.9 abc 0 -3");
    expect(r.laps).toEqual([14900]);
    expect(r.bad).toEqual(["abc", "0", "-3"]);
  });
  it("rounds to whole milliseconds and finds the best lap", () => {
    expect(parseOneLap("14.8249")).toBe(14825);
    expect(bestOf([14900, 15100, 14800])).toBe(14800);
    expect(bestOf([])).toBeUndefined();
  });
  it("auto-increments the tyre counter from an unset or numeric value", () => {
    expect(nextTyreRuns(undefined)).toBe(1);
    expect(nextTyreRuns(null)).toBe(1);
    expect(nextTyreRuns(3)).toBe(4);
  });
});

describe("setup logic", () => {
  it("uses the BD12 value, else the generic value, as baseline", () => {
    expect(baselineOf(P("frontCamberDeg"))).toEqual({ value: 1.5, generic: false });
    expect(baselineOf(P("casterDeg"))).toEqual({ value: 4, generic: true });
    expect(baselineOf(P("frontSpringRate"))).toEqual({ value: null, generic: false });
  });
  it("computes FDR from spur / pinion x 1.9 and returns null while pinion is unset", () => {
    const base = baselineValues(params);
    expect(computeFdr(params, base)).toBeNull();
    expect(computeFdr(params, { ...base, spurT: 90, pinionT: 48 })).toBe(3.56);
  });
  it("flags out-of-range numbers but not in-range or non-numeric ones", () => {
    const fc = P("frontCamberDeg"); // 1.0 to 2.5
    expect(isOutOfRange(fc, 3)).toBe(true);
    expect(isOutOfRange(fc, 0.5)).toBe(true);
    expect(isOutOfRange(fc, 2.5)).toBe(false);
    expect(isOutOfRange(fc, null)).toBe(false);
    expect(rangeUnsourced(P("rearCamberDeg"))).toBe(true);
  });
  it("steps by the param's step without float noise, and fills a null on the first tap", () => {
    expect(stepValue(P("rideHeightFrontMm"), 5.0, 1)).toBe(5.2);
    expect(stepValue(P("rideHeightFrontMm"), 5.4, 1)).toBe(5.6);
    expect(stepValue(P("frontArbMm"), 1.3, -1)).toBe(1.2);
    expect(stepValue(P("casterDeg"), null, 1)).toBe(4); // generic
    expect(stepValue(P("frontSpringRate"), null, 1)).toBe(2); // min
  });
  it("lets stepping leave the range (flagged, not blocked)", () => {
    const v = stepValue(P("rearToeInDeg"), 3.5, 1);
    expect(v).toBe(4);
    expect(isOutOfRange(P("rearToeInDeg"), v)).toBe(true);
  });
  it("diffs two setups and ignores computed params", () => {
    const a = { ...baselineValues(params) };
    const b = { ...a, rearToeInDeg: 3.0, droopFrontGaugeMm: 5.4 };
    const d = diffValues(a, b, params);
    expect(d.map((x) => x.param).sort()).toEqual(["droopFrontGaugeMm", "rearToeInDeg"]);
  });
  it("shows signed deltas and the droop sign convention", () => {
    expect(deltaText(3.5, 3.0)).toBe("-0.5");
    expect(deltaText(5.6, 5.8)).toBe("+0.2");
    expect(deltaText(null, 3)).toBe("set");
    expect(deltaMeaning(P("droopFrontGaugeMm"), 5.6, 5.4)).toBe("more droop");
  });
  it("parses typed numbers", () => {
    expect(parseNumberInput("1,5")).toBe(1.5);
    expect(parseNumberInput("")).toBeNull();
    expect(Number.isNaN(parseNumberInput("abc"))).toBe(true);
  });
});
