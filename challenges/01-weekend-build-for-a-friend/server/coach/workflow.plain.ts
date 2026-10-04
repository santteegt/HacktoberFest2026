// Plain TypeScript CoachEngine fallback (T3; plan 2.5): same steps, TurnState persisted as JSON in
// a coach_runs table in var/pit.db. T0 stub.
import type { CoachEngine } from "./engine";

export function createPlainEngine(): CoachEngine {
  throw new Error("not implemented");
}
