// What has worked: outcome counts per (param, direction) across sessions (T8; plan 4.7 item 5).
import type { Change, ParamHistoryRow } from "../../src/shared/types";
import { directionOf } from "./util";

/** Shown next to every history row: these are the driver's own taps, not measurements. */
export const HISTORY_LABEL = "your feel, not lap-time proof";

export type ParamHistoryRowOut = ParamHistoryRow & { label: string };

/**
 * One row per (param, direction). `tries` counts the driver's changes (reverts excluded, they undo a try rather
 * than make one); better/same/worse count only changes that got an outcome tap, so they can sum to less than `tries`.
 * Sorted by tries, then param.
 */
export function paramHistory(changes: Change[]): ParamHistoryRowOut[] {
  const rows = new Map<string, ParamHistoryRowOut>();
  for (const c of changes) {
    if (c.source === "revert") continue;
    const direction = directionOf(c.from, c.to);
    const key = `${c.param}|${direction}`;
    let row = rows.get(key);
    if (!row) {
      row = { param: c.param, direction, tries: 0, better: 0, same: 0, worse: 0, label: HISTORY_LABEL };
      rows.set(key, row);
    }
    row.tries += 1;
    if (c.outcome) row[c.outcome] += 1;
  }
  return [...rows.values()].sort((a, b) => b.tries - a.tries || a.param.localeCompare(b.param) || a.direction.localeCompare(b.direction));
}
