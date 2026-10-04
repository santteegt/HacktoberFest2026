// Plain TypeScript CoachEngine fallback (T3; plan 2.5): same steps as the Mastra workflow, run in order,
// with the state persisted as JSON in the coach_runs table of var/pit.db (T1's migration creates it).
// Selected with COACH_ENGINE=plain, or automatically when the Mastra engine cannot be built.
import { randomUUID } from "node:crypto";
import type { CoachTurnInput, OutcomeResult, TurnState } from "../../src/shared/types";
import type { CoachEngine, DecideArgs, EmitFn, OutcomeArgs } from "./engine";
import {
  CoachError,
  CoachState,
  getCoachDeps,
  initialState,
  publicState,
  stepApply,
  stepClassify,
  stepExplain,
  stepLogOutcome,
  stepPickLever,
  stepPrecheck,
  type CoachDeps,
  type CoachStateT,
} from "./steps";
import { getDb } from "../db";

export interface RunStore {
  get(runId: string): Promise<CoachStateT | undefined>;
  put(st: CoachStateT): Promise<void>;
}

/** coach_runs table in the vault database. */
export const sqlRunStore: RunStore = {
  async get(runId) {
    const rs = await getDb().execute({ sql: "SELECT state FROM coach_runs WHERE id = ?", args: [runId] });
    const row = rs.rows[0];
    return row ? CoachState.parse(JSON.parse(String(row.state))) : undefined;
  },
  async put(st) {
    const now = Date.now();
    await getDb().execute({
      sql: `INSERT INTO coach_runs (id, state, created_at, updated_at) VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at`,
      args: [st.runId, JSON.stringify(st), now, now],
    });
  },
};

/** For tests and the self-test (lost on restart). */
export function memoryRunStore(): RunStore {
  const m = new Map<string, CoachStateT>();
  return { get: async (id) => m.get(id), put: async (st) => void m.set(st.runId, structuredClone(st)) };
}

export function createPlainEngine(opts: { deps?: () => CoachDeps; store?: RunStore } = {}): CoachEngine {
  const depsOf = opts.deps ?? getCoachDeps;
  const store = opts.store ?? sqlRunStore;
  const load = async (runId: string) => {
    const st = await store.get(runId);
    if (!st) throw new CoachError(404, `no coach run ${runId}`, "resume");
    return st;
  };
  return {
    kind: "plain",
    async start(input: CoachTurnInput, emit: EmitFn): Promise<TurnState> {
      const deps = depsOf();
      let st = initialState(randomUUID(), input);
      for (const step of [stepClassify, stepPrecheck, stepPickLever, stepExplain]) st = await step(st, emit, deps);
      await store.put(st);
      if (!st.halted && !st.refusal) await emit({ event: "suspended", data: { runId: st.runId, status: st.status } });
      return publicState(st);
    },
    async decide(runId: string, d: DecideArgs): Promise<TurnState> {
      const st = await stepApply(await load(runId), d, depsOf());
      await store.put(st);
      return publicState(st);
    },
    async outcome(runId: string, o: OutcomeArgs): Promise<OutcomeResult> {
      const st = await stepLogOutcome(await load(runId), o, depsOf());
      await store.put(st);
      return st.outcomeResult!;
    },
  };
}
