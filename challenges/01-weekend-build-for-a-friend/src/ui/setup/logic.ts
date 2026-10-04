// Pure helpers for the Setup editor (T4b). No DOM or Preact imports so vitest can run them in node.
import type { ParamDef, ParamValue, SetupValues } from "../../shared/types";

/** Baseline rule (plan 4.1): the BD12 factory value when Yokomo gives one, else the generic value, else null. */
export function baselineOf(p: ParamDef): { value: ParamValue; generic: boolean } {
  if (p.bd12 !== null && p.bd12 !== undefined) return { value: p.bd12, generic: false };
  if (p.generic !== null && p.generic !== undefined) return { value: p.generic, generic: true };
  return { value: null, generic: false };
}

export function baselineValues(params: ParamDef[]): SetupValues {
  const out: SetupValues = {};
  for (const p of params) if (p.kind !== "computed") out[p.id] = baselineOf(p).value;
  return out;
}

/** Number of decimals in a step like 0.25 -> 2, used to avoid 1.4000000000000001. */
export function decimalsOf(step: number | undefined): number {
  if (!step) return 0;
  const s = String(step);
  const i = s.indexOf(".");
  return i < 0 ? 0 : s.length - i - 1;
}

export function roundTo(n: number, decimals: number): number {
  const f = 10 ** decimals;
  return Math.round(n * f) / f;
}

/**
 * Value after one stepper tap. A null value lands on the starting point (generic, else min, else 0) rather
 * than stepping from nowhere, so the first tap on an empty field just fills it in.
 */
export function stepValue(p: ParamDef, current: ParamValue, dir: 1 | -1): number {
  const step = p.step ?? 1;
  const dec = Math.max(decimalsOf(step), decimalsOf(typeof current === "number" ? current : undefined));
  if (typeof current !== "number") {
    const start = typeof p.generic === "number" ? p.generic : typeof p.min === "number" ? p.min : 0;
    return roundTo(start, dec);
  }
  return roundTo(current + dir * step, dec);
}

/** True when a numeric value sits outside the param's min..max. Out-of-range input is allowed, only flagged. */
export function isOutOfRange(p: ParamDef, v: ParamValue): boolean {
  if (typeof v !== "number") return false;
  if (typeof p.min === "number" && v < p.min) return true;
  if (typeof p.max === "number" && v > p.max) return true;
  return false;
}

/** The param's `range` note says the bounds are not sourced from the notes. */
export function rangeUnsourced(p: ParamDef): boolean {
  return /unsourced/i.test(p.range);
}

export function rangeText(p: ParamDef): string {
  if (typeof p.min === "number" && typeof p.max === "number") return `${p.min} to ${p.max}${p.unit ? " " + p.unit : ""}`;
  if (p.kind === "enum" && p.options) return p.options.join(" / ");
  return "";
}

/** Convention key (meta.conventions) that applies to a param, for the sign-convention line. */
export function conventionKey(id: string): string | null {
  if (/CamberLinkInnerShim/i.test(id)) return "camberLinkShim";
  if (/camber/i.test(id)) return "camber";
  if (id === "frontToeOutDeg") return "frontToe";
  if (id === "rearToeInDeg") return "rearToe";
  if (id === "casterDeg") return "caster";
  if (/^droop/i.test(id)) return "droop";
  if (/^rideHeight/i.test(id)) return "rideHeight";
  if (/ShockPos$/.test(id)) return "shockPos";
  return null;
}

// ---------- computed params (FDR) ----------

/** Tiny arithmetic evaluator (numbers, identifiers, + - * /, parentheses). Returns null if a value is missing. */
export function evalFormula(formula: string, values: SetupValues): number | null {
  const tokens = formula.match(/[A-Za-z_]\w*|\d+\.?\d*|\.\d+|[()+\-*/]/g);
  if (!tokens) return null;
  let pos = 0;
  let missing = false;
  const peek = () => tokens[pos];
  const next = () => tokens[pos++];
  function primary(): number {
    const t = next();
    if (t === undefined) {
      missing = true;
      return NaN;
    }
    if (t === "(") {
      const v = expr();
      if (next() !== ")") missing = true;
      return v;
    }
    if (t === "-") return -primary();
    if (/^[A-Za-z_]/.test(t)) {
      const v = values[t];
      if (typeof v !== "number") {
        missing = true;
        return NaN;
      }
      return v;
    }
    return Number(t);
  }
  function term(): number {
    let v = primary();
    while (peek() === "*" || peek() === "/") {
      const op = next();
      const r = primary();
      v = op === "*" ? v * r : v / r;
    }
    return v;
  }
  function expr(): number {
    let v = term();
    while (peek() === "+" || peek() === "-") {
      const op = next();
      const r = term();
      v = op === "+" ? v + r : v - r;
    }
    return v;
  }
  const out = expr();
  if (missing || pos !== tokens.length || !Number.isFinite(out)) return null;
  return out;
}

/** Final drive ratio from the param's own formula ("spurT / pinionT * 1.9"); null when spur or pinion is unset. */
export function computeFdr(params: ParamDef[], values: SetupValues): number | null {
  const fdr = params.find((p) => p.kind === "computed" && p.id === "fdr");
  const formula = fdr?.formula ?? "spurT / pinionT * 1.9";
  const v = evalFormula(formula, values);
  return v === null ? null : roundTo(v, 2);
}

// ---------- diffs ----------

export interface ParamChange {
  param: string;
  from: ParamValue;
  to: ParamValue;
}

export function sameValue(a: ParamValue | undefined, b: ParamValue | undefined): boolean {
  const x = a === undefined ? null : a;
  const y = b === undefined ? null : b;
  return x === y;
}

/** Params whose values differ between two setups (computed params are ignored). */
export function diffValues(a: SetupValues, b: SetupValues, params: ParamDef[]): ParamChange[] {
  const out: ParamChange[] = [];
  for (const p of params) {
    if (p.kind === "computed") continue;
    const from = a[p.id] ?? null;
    const to = b[p.id] ?? null;
    if (!sameValue(from, to)) out.push({ param: p.id, from, to });
  }
  return out;
}

/** Signed delta text: "+0.5", "-0.2"; "set" when going from empty; "" when not numeric. */
export function deltaText(from: ParamValue | undefined, to: ParamValue | undefined, dec = 2): string {
  if (typeof to !== "number") return "";
  if (typeof from !== "number") return "set";
  const d = roundTo(to - from, dec);
  if (d === 0) return "0";
  return (d > 0 ? "+" : "") + d;
}

/** Plain-language hint for a delta, using the sign conventions that are easy to misread. */
export function deltaMeaning(p: ParamDef, from: ParamValue | undefined, to: ParamValue | undefined): string {
  if (typeof from !== "number" || typeof to !== "number" || from === to) return "";
  const up = to > from;
  if (/^droop/.test(p.id)) return up ? "less droop" : "more droop";
  if (/camber/i.test(p.id) && !/Link/i.test(p.id)) return up ? "more negative camber" : "less negative camber";
  if (/ShockPos$/.test(p.id)) return up ? "more upright" : "more laid down";
  return "";
}

export function formatValue(v: ParamValue | undefined, unit?: string): string {
  if (v === null || v === undefined || v === "") return "not set";
  return unit && typeof v === "number" ? `${v} ${unit}` : String(v);
}

/** Parses a typed number ("1,5" and "1.5" both work). Returns null for empty, NaN for garbage. */
export function parseNumberInput(text: string): number | null {
  const t = text.trim().replace(",", ".");
  if (t === "") return null;
  if (!/^-?\d*\.?\d+$|^-?\d+\.$/.test(t)) return Number.NaN;
  return Number(t);
}
