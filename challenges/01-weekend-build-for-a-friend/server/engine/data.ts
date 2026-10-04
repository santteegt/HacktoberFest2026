// Loads and validates the domain data files with the shared zod schemas (T2).
// data/params.bd12.json, data/symptoms.json, data/levers.json, data/prechecks.json.
// Each file is read and validated once, then cached for the life of the process.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import * as S from "../../src/shared/schemas";
import type { ParamsFile, LeverRow, PrecheckDef, SymptomDef } from "../../src/shared/types";

const dataPath = (name: string) => fileURLToPath(new URL(`../../data/${name}`, import.meta.url));

function load<T extends z.ZodType>(name: string, schema: T): z.infer<T> {
  const raw = JSON.parse(readFileSync(dataPath(name), "utf8")) as unknown;
  const r = schema.safeParse(raw);
  if (!r.success) throw new Error(`data/${name} failed validation: ${r.error.message}`);
  return r.data;
}

function once<T>(fn: () => T): () => T {
  let cache: { v: T } | undefined;
  return () => (cache ??= { v: fn() }).v;
}

export const loadParams = once((): ParamsFile => load("params.bd12.json", S.ParamsFile));
export const loadSymptoms = once((): SymptomDef[] => load("symptoms.json", z.array(S.SymptomDef)));
export const loadLevers = once((): LeverRow[] => load("levers.json", z.array(S.LeverRow)));
export const loadPrechecks = once((): PrecheckDef[] => load("prechecks.json", z.array(S.PrecheckDef)));
