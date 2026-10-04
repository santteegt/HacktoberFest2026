// The process-wide CoachEngine. Mastra by default (the T3 spike passed); COACH_ENGINE=plain forces the
// plain fallback. If the Mastra engine fails on its first use, the server logs it and switches to plain,
// so a coach turn still works (the Mastra claim then does not hold for that run: `kind` says which ran).
import type { CoachEngine } from "./engine";
import { createMastraEngine } from "./workflow.mastra";
import { createPlainEngine } from "./workflow.plain";

let engine: CoachEngine | undefined;

export function getCoachEngine(): CoachEngine {
  if (engine) return engine;
  if (process.env.COACH_ENGINE === "plain") return (engine = createPlainEngine());
  const mastra = createMastraEngine();
  const plain = createPlainEngine();
  let fellBack = false;
  const guard =
    <A extends unknown[], R>(f: (...a: A) => Promise<R>, g: (...a: A) => Promise<R>) =>
    async (...a: A): Promise<R> => {
      if (fellBack) return g(...a);
      try {
        return await f(...a);
      } catch (e) {
        // Only an engine that cannot even load Mastra falls back; request errors (CoachError) pass through.
        if ((e as Error).name === "CoachError" || !/Cannot find (module|package)|ERR_MODULE_NOT_FOUND/.test(String(e))) throw e;
        console.error(`[coach] Mastra engine unavailable, falling back to plain: ${(e as Error).message}`);
        fellBack = true;
        return g(...a);
      }
    };
  engine = {
    get kind() {
      return fellBack ? "plain" : "mastra";
    },
    start: guard(mastra.start, plain.start),
    decide: guard(mastra.decide, plain.decide),
    outcome: guard(mastra.outcome, plain.outcome),
  } as CoachEngine;
  return engine;
}

/** Tests: replace the engine. */
export function setCoachEngine(e: CoachEngine | undefined): void {
  engine = e;
}
