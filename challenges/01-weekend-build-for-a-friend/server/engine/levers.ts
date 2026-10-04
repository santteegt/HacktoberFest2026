// Deterministic lever engine (T2; plan 4.3). T0 stub with the documented signature.
import type { Change, Grip, LeverRow, ParamDef, Phase, SetupValues, Suggestion } from "../../src/shared/types";

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

export function selectLevers(_args: SelectLeversArgs): Suggestion {
  throw new Error("not implemented");
}
