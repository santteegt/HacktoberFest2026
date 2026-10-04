// Small pure helpers shared by the analysis modules (T8).
import type { ParamValue, SetupValues } from "../../src/shared/types";

export type Direction = "increase" | "decrease" | "changed";

export interface ParamDiffRow {
  param: string;
  from: ParamValue;
  to: ParamValue;
  direction: Direction;
}

/** Direction of a value change; non-numeric values (enums, text) are just "changed". */
export function directionOf(from: ParamValue, to: ParamValue): Direction {
  if (typeof from === "number" && typeof to === "number") return to > from ? "increase" : "decrease";
  return "changed";
}

const same = (a: ParamValue | undefined, b: ParamValue | undefined): boolean => (a ?? null) === (b ?? null);

/** Params whose value differs between two setups (from -> to). Stable order: keys of `from`, then new keys of `to`. */
export function diffSetups(from: SetupValues, to: SetupValues): ParamDiffRow[] {
  const keys = [...Object.keys(from)];
  for (const k of Object.keys(to)) if (!keys.includes(k)) keys.push(k);
  const out: ParamDiffRow[] = [];
  for (const k of keys) {
    const a = from[k] ?? null;
    const b = to[k] ?? null;
    if (same(a, b)) continue;
    out.push({ param: k, from: a, to: b, direction: directionOf(a, b) });
  }
  return out;
}

/** Format a value for text: numbers trimmed of float noise, null as "unset". */
export function fmt(v: ParamValue | undefined): string {
  if (v === null || v === undefined) return "unset";
  if (typeof v === "number") return String(Math.round(v * 1000) / 1000);
  return v;
}
