// Loads and validates the domain data files with the shared zod schemas (T2).
// data/params.bd12.json, data/symptoms.json, data/levers.json, data/prechecks.json. T0 stub.
import type { ParamsFile, LeverRow, PrecheckDef, SymptomDef } from "../../src/shared/types";

export function loadParams(): ParamsFile {
  throw new Error("not implemented");
}
export function loadSymptoms(): SymptomDef[] {
  throw new Error("not implemented");
}
export function loadLevers(): LeverRow[] {
  throw new Error("not implemented");
}
export function loadPrechecks(): PrecheckDef[] {
  throw new Error("not implemented");
}
