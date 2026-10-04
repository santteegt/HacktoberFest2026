// Staged (uncommitted) setup edits (T4b). Module-level signals so staged values survive switching screens.
import { signal } from "@preact/signals";
import type { ParamValue, SetupValues } from "../../shared/types";
import { sameValue } from "./logic";

/** param id -> staged value (only entries that differ from the committed setup). */
export const staged = signal<Record<string, ParamValue>>({});
/** Snapshots of `staged` before each edit, for Undo. */
const history = signal<Record<string, ParamValue>[]>([]);
/** Session the staged edits belong to; edits are dropped when another session opens. */
let stagedFor: string | null = null;

export function bindStagedToSession(sessionId: string | null): void {
  if (stagedFor !== sessionId) {
    stagedFor = sessionId;
    staged.value = {};
    history.value = [];
  }
}

export function stagedCount(): number {
  return Object.keys(staged.value).length;
}

export function canUndo(): boolean {
  return history.value.length > 0;
}

/** Stages `value` for `param`; a value equal to the committed one removes the staged entry. */
export function stage(param: string, value: ParamValue, committed: SetupValues): void {
  const before = staged.value;
  const next = { ...before };
  if (sameValue(value, committed[param] ?? null)) delete next[param];
  else next[param] = value;
  if (sameValue(before[param], next[param]) && param in before === param in next) return;
  history.value = [...history.value, before];
  staged.value = next;
}

export function undoLast(): void {
  const h = history.value;
  if (!h.length) return;
  staged.value = h[h.length - 1];
  history.value = h.slice(0, -1);
}

export function discardAll(): void {
  if (!stagedCount()) return;
  history.value = [...history.value, staged.value];
  staged.value = {};
}

/** Clears staged edits after a successful commit. */
export function clearStaged(): void {
  staged.value = {};
  history.value = [];
}

/** Committed values with the staged edits laid over them. */
export function effectiveValues(committed: SetupValues, overlay: Record<string, ParamValue> = staged.value): SetupValues {
  return { ...committed, ...overlay };
}
