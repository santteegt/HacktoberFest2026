// Deterministic lever engine (T2; plan 4.3). Pure function: no I/O, no model, no randomness.
import type {
  Change,
  Grip,
  LeverRow,
  LeverSuggestion,
  ParamDef,
  ParamValue,
  Phase,
  SceneBinding,
  SetupValues,
  SkipReason,
  Suggestion,
} from "../../src/shared/types";

export interface SelectLeversArgs {
  symptomId: string;
  phase: Phase;
  grip: Grip;
  setup: SetupValues;
  params: ParamDef[];
  levers: LeverRow[];
  /** Changes in this session, newest last. */
  history: Change[];
  reviewedOnly: boolean;
}

export const NO_LEVER_REASON =
  "Every option in my notes for this is at its limit or already tried. Re-check the basics, or log what you changed by hand.";

/** How many of the most recent changes are checked for a `worse` or `same` outcome. */
const HISTORY_WINDOW = 3;

/** Round to the precision of the step so 0.1 + 0.2 never shows as 0.30000000000000004. */
function tidy(n: number, step: number): number {
  const decimals = Math.min(6, (String(step).split(".")[1] ?? "").length);
  return Number(n.toFixed(decimals));
}

function directionOf(c: Change): "increase" | "decrease" | null {
  if (typeof c.from !== "number" || typeof c.to !== "number" || c.from === c.to) return null;
  return c.to > c.from ? "increase" : "decrease";
}

/** Combined bounds: the narrower of the lever row's and the parameter's min/max. */
function boundsOf(row: LeverRow, param: ParamDef | undefined): { lo: number; hi: number } {
  return {
    lo: Math.max(row.min ?? -Infinity, param?.min ?? -Infinity),
    hi: Math.min(row.max ?? Infinity, param?.max ?? Infinity),
  };
}

/** Next value for a numeric row. Returns `current` itself when there is no room to move. */
function stepNumber(current: number, row: LeverRow, param: ParamDef | undefined): number {
  const dir = row.direction === "decrease" ? -1 : 1;
  const step = row.step ?? param?.step ?? 1;
  const { lo, hi } = boundsOf(row, param);
  let to = tidy(Math.min(hi, Math.max(lo, current + dir * step)), step);
  // A value already outside the bounds must never be "moved" against the requested direction.
  if ((dir < 0 && to > current) || (dir > 0 && to < current)) to = current;
  return to;
}

/** Next option for an enum param, in the lever's direction; `current` when none is left. */
function stepEnum(current: number, row: LeverRow, param: ParamDef): number {
  const lo = row.min ?? -Infinity;
  const hi = row.max ?? Infinity;
  const options = [...(param.options ?? [])].filter((o) => o >= lo && o <= hi).sort((a, b) => a - b);
  const next =
    row.direction === "decrease"
      ? [...options].reverse().find((o) => o < current)
      : options.find((o) => o > current);
  return next ?? current;
}

function sceneFor(param: ParamDef | undefined, from: ParamValue, to: ParamValue): SceneBinding | undefined {
  if (!param?.explainer || typeof from !== "number" || typeof to !== "number") return undefined;
  return { explainer: param.explainer, param: param.id, from, to };
}

export function selectLevers(args: SelectLeversArgs): Suggestion {
  const { symptomId, phase, grip, setup, params, levers, history, reviewedOnly } = args;
  const paramById = new Map(params.map((p) => [p.id, p]));
  const skipped: Suggestion["skipped"] = [];
  const skip = (leverId: string, reason: SkipReason) => skipped.push({ leverId, reason });

  // (param, direction) pairs tried in the last few changes that did not help.
  const failed = new Map<string, "tried-worse" | "tried-same">();
  for (const c of history.slice(-HISTORY_WINDOW)) {
    const dir = directionOf(c);
    if (!dir || (c.outcome !== "worse" && c.outcome !== "same")) continue;
    const key = `${c.param}|${dir}`;
    // `worse` is the stronger signal, so it wins when both appear.
    if (failed.get(key) !== "tried-worse") failed.set(key, c.outcome === "worse" ? "tried-worse" : "tried-same");
  }

  const candidates: LeverSuggestion[] = [];
  const rows = levers
    .map((row, i) => ({ row, i }))
    .filter(({ row }) => row.symptomId === symptomId)
    .filter(({ row }) => phase === "none" || row.phases.includes(phase) || row.phases.includes("none"))
    .sort((a, b) => a.row.priority - b.row.priority || a.i - b.i);

  for (const { row } of rows) {
    // 1. grip and review filters
    if (row.grip && !row.grip.includes(grip)) {
      skip(row.id, "grip-mismatch");
      continue;
    }
    if (reviewedOnly && row.status !== "reviewed") {
      skip(row.id, "draft-hidden");
      continue;
    }

    let from: ParamValue = null;
    let to: ParamValue = null;
    let needsCurrentValue = false;
    let currentOutOfRange = false;

    if (row.kind === "numeric" && row.param) {
      const param = paramById.get(row.param);
      const current = setup[row.param];
      const { lo, hi } = boundsOf(row, param);
      if (current === undefined || current === null || typeof current !== "number") {
        // 2. no current value: the card says "one step <direction>" and asks for it
        needsCurrentValue = true;
      } else if (param?.kind !== "enum" && (current < lo || current > hi)) {
        // 2b. (T10) the current value is outside the range in the notes (often a typing slip such as
        // 50,500,000 cSt): never clamp it into a big jump; ask the driver to check it in Setup.
        from = current;
        needsCurrentValue = true;
        currentOutOfRange = true;
      } else {
        from = current;
        to = param?.kind === "enum" ? stepEnum(current, row, param) : stepNumber(current, row, param);
        if (to === current) {
          skip(row.id, "at-limit");
          continue;
        }
      }
      // 3. history
      const dir = row.direction;
      const why = dir ? failed.get(`${row.param}|${dir}`) : undefined;
      if (why) {
        skip(row.id, why);
        continue;
      }
      candidates.push({
        lever: row,
        from,
        to,
        atLimit: false,
        needsCurrentValue,
        ...(currentOutOfRange ? { currentOutOfRange: true } : {}),
        scene: sceneFor(param, from, to),
      });
    } else {
      // qualitative row: nothing to clamp, nothing to remember
      candidates.push({ lever: row, from: null, to: null, atLimit: false, needsCurrentValue: false });
    }
  }

  // 4. rows are already priority-sorted: primary plus two alternatives
  const [primary = null, ...rest] = candidates;
  const out: Suggestion = { primary, alternatives: rest.slice(0, 2), skipped };
  if (!primary) out.noLeverReason = NO_LEVER_REASON; // 5.
  return out;
}
