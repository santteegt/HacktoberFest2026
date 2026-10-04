// Domain data access for the vault and /api/meta (T1). Reads through server/engine/data.ts (T2).
// The only test seam is setParamsOverride(), so vault tests do not depend on the real parameter table.
import { readFileSync, statSync } from "node:fs";
import { loadLevers, loadParams, loadPrechecks, loadSymptoms } from "../engine/data";
import { config } from "../config";
import type { MetaResponse } from "../../src/shared/api";
import type { CarId, KbStats, ParamDef, ParamsFile, ParamValue, SetupValues } from "../../src/shared/types";

let paramsOverride: ParamsFile | null = null;

/** Tests only: replace the parameter table (null restores the real file). */
export function setParamsOverride(p: ParamsFile | null): void {
  paramsOverride = p;
}

export function getParamsFile(): ParamsFile {
  return paramsOverride ?? loadParams();
}

/**
 * Baseline value of one param (plan 4.1 baseline rule): the BD12 value where Yokomo gives one, else the
 * generic (Xray-derived) value, else null. A "generic" car profile prefers the generic value.
 */
export function baselineValue(p: ParamDef, car: CarId): ParamValue {
  const first = car === "generic" ? p.generic : p.bd12;
  const second = car === "generic" ? p.bd12 : p.generic;
  return first ?? second ?? null;
}

/** Baseline setup values for a car. Computed params (e.g. FDR) are derived in the UI and are not stored. */
export function baselineSetup(params: ParamDef[], car: CarId): SetupValues {
  const out: SetupValues = {};
  for (const p of params) {
    if (p.kind === "computed") continue;
    out[p.id] = baselineValue(p, car);
  }
  return out;
}

let kbCache: { mtimeMs: number; stats: KbStats } | null = null;

/** pages / chunks / contentHash of data/generated/kb.json (cached by mtime). */
export function kbStats(): KbStats {
  try {
    const st = statSync(config.paths.kbJson);
    if (kbCache && kbCache.mtimeMs === st.mtimeMs) return kbCache.stats;
    const kb = JSON.parse(readFileSync(config.paths.kbJson, "utf8")) as {
      contentHash?: string;
      pages?: unknown[];
      chunks?: unknown[];
    };
    const stats: KbStats = {
      pages: kb.pages?.length ?? 0,
      chunks: kb.chunks?.length ?? 0,
      contentHash: kb.contentHash ?? "",
    };
    kbCache = { mtimeMs: st.mtimeMs, stats };
    return stats;
  } catch {
    return { pages: 0, chunks: 0, contentHash: "" };
  }
}

export function loadMeta(): MetaResponse {
  const pf = getParamsFile();
  return {
    car: pf.car,
    baselineRule: pf.baselineRule,
    conventions: pf.conventions,
    params: pf.params,
    symptoms: loadSymptoms(),
    levers: loadLevers(),
    prechecks: loadPrechecks(),
    kbStats: kbStats(),
  };
}
