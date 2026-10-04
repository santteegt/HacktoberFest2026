// Mastra "coach-turn" workflow engine (T3; plan 2.5).
// classify -> precheck -> pick-lever -> explain -> await-decision [suspend] -> apply
//          -> await-outcome [suspend] -> log-outcome
// One state schema (CoachState) is every step's input and output; steps no-op once the turn has stopped
// (refusal, error, nothing to suggest). Snapshots live in a LibSQL file (MASTRA_DB_URL), so a run can be
// resumed by another process after a server restart: createRun({ runId }) then resume({ step, resumeData }).
//
// SSE events: steps look up the live `emit` for their runId in an in-process registry. Only the first
// segment (start -> first suspend) emits; resumes return JSON. This avoids depending on Mastra's stream
// event shapes (plan 2.5 fallback rule).
//
// Do not import @mastra/core before server/config.ts has run (it disables telemetry): this module loads
// Mastra lazily with dynamic import(), and config is the first import of server/index.ts.
import { randomUUID } from "node:crypto";
import { z } from "zod";
import { config } from "../config";
import { DecideBody, OutcomeBody } from "../../src/shared/api";
import type { CoachTurnInput, OutcomeResult, TurnState } from "../../src/shared/types";
import type { CoachEngine, DecideArgs, EmitFn, OutcomeArgs } from "./engine";
import {
  assertAwaitingOutcome,
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
  targetOf,
  type CoachDeps,
  type CoachStateT,
} from "./steps";

export const WORKFLOW_ID = "coach-turn";

/** Workflow-internal state: CoachState plus the resume payload carried from a suspend step to the next step. */
const WfState = CoachState.extend({
  pendingDecision: DecideBody.optional(),
  pendingOutcome: OutcomeBody.optional(),
});
type WfStateT = z.infer<typeof WfState>;

const emitters = new Map<string, EmitFn>();
const noEmit: EmitFn = async () => {};
const emitFor = (runId: string): EmitFn => emitters.get(runId) ?? noEmit;

type Wf = { createRun(o: { runId: string }): Promise<any>; getWorkflowRunById(id: string): Promise<any> };

async function buildWorkflow(depsOf: () => CoachDeps, dbUrl: string): Promise<{ wf: Wf }> {
  const { createWorkflow, createStep } = await import("@mastra/core/workflows");
  const { Mastra } = await import("@mastra/core/mastra");
  const { LibSQLStore } = await import("@mastra/libsql");

  const s = (id: string, run: (st: WfStateT) => Promise<WfStateT>) =>
    createStep({ id, inputSchema: WfState, outputSchema: WfState, execute: async ({ inputData }) => run(inputData) });

  const classify = s("classify", (st) => stepClassify(st, emitFor(st.runId), depsOf()) as Promise<WfStateT>);
  const precheck = s("precheck", (st) => stepPrecheck(st, emitFor(st.runId), depsOf()) as Promise<WfStateT>);
  const pickLever = s("pick-lever", (st) => stepPickLever(st, emitFor(st.runId), depsOf()) as Promise<WfStateT>);
  const explain = s("explain", (st) => stepExplain(st, emitFor(st.runId), depsOf()) as Promise<WfStateT>);

  const awaitDecision = createStep({
    id: "await-decision",
    inputSchema: WfState,
    outputSchema: WfState,
    suspendSchema: WfState,
    resumeSchema: DecideBody,
    execute: async ({ inputData, resumeData, suspend }) => {
      if (inputData.status !== "awaiting-decision") return inputData; // stopped earlier: nothing to decide
      if (!resumeData) return (await suspend(inputData)) as unknown as WfStateT;
      return { ...inputData, pendingDecision: resumeData };
    },
  });
  const apply = s("apply", async (st) => {
    if (!st.pendingDecision || st.status !== "awaiting-decision") return st;
    const { pendingDecision, ...rest } = st;
    return (await stepApply(rest, pendingDecision, depsOf())) as WfStateT;
  });
  const awaitOutcome = createStep({
    id: "await-outcome",
    inputSchema: WfState,
    outputSchema: WfState,
    suspendSchema: WfState,
    resumeSchema: OutcomeBody,
    execute: async ({ inputData, resumeData, suspend }) => {
      if (inputData.status !== "awaiting-outcome") return inputData;
      if (!resumeData) return (await suspend(inputData)) as unknown as WfStateT;
      return { ...inputData, pendingOutcome: resumeData };
    },
  });
  const logOutcome = s("log-outcome", async (st) => {
    if (!st.pendingOutcome || st.status !== "awaiting-outcome") return st;
    const { pendingOutcome, ...rest } = st;
    return (await stepLogOutcome(rest, pendingOutcome, depsOf())) as WfStateT;
  });

  const workflow = createWorkflow({ id: WORKFLOW_ID, inputSchema: WfState, outputSchema: WfState })
    .then(classify)
    .then(precheck)
    .then(pickLever)
    .then(explain)
    .then(awaitDecision)
    .then(apply)
    .then(awaitOutcome)
    .then(logOutcome)
    .commit();

  const storage = new LibSQLStore({ id: "mastra-storage", url: dbUrl });
  const mastra = new Mastra({ workflows: { coachTurn: workflow }, storage });
  // Wrapped on purpose: a Workflow has .then() (step chaining), so returning it bare from an async
  // function makes `await` treat it as a thenable that never settles (found in the spike).
  return { wf: mastra.getWorkflow("coachTurn") as unknown as Wf };
}

type RunResult = { status: string; result?: unknown; error?: unknown; steps?: Record<string, { status?: string; suspendPayload?: unknown }> };

function stateFromResult(r: RunResult, runId: string, stage: string): CoachStateT {
  if (r.status === "success" && r.result) return CoachState.parse(r.result);
  if (r.status === "suspended") {
    const suspended = Object.values(r.steps ?? {}).find((x) => x?.status === "suspended");
    if (suspended?.suspendPayload) return CoachState.parse(suspended.suspendPayload);
  }
  const err = r.error as { message?: string } | string | undefined;
  const msg = typeof err === "string" ? err : err?.message ?? `workflow ${r.status}`;
  // A CoachError thrown inside a step comes back serialized; keep its message.
  throw new CoachError(500, `run ${runId}: ${msg}`, stage);
}

export function createMastraEngine(opts: { deps?: () => CoachDeps; dbUrl?: string } = {}): CoachEngine {
  const depsOf = opts.deps ?? getCoachDeps;
  let built: Promise<{ wf: Wf }> | undefined;
  // Never return the bare Workflow from an async function (thenable trap, see buildWorkflow): callers destructure.
  const wfP = () => (built ??= buildWorkflow(depsOf, opts.dbUrl ?? config.mastraDbUrl));

  /** Current state of a run, read from the persisted snapshot (works after a restart). */
  async function readState(runId: string): Promise<CoachStateT> {
    const { wf } = await wfP();
    const r = await wf.getWorkflowRunById(runId);
    if (!r) throw new CoachError(404, `no coach run ${runId}`, "resume");
    return stateFromResult(r as RunResult, runId, "resume");
  }

  return {
    kind: "mastra",

    async start(input: CoachTurnInput, emit: EmitFn): Promise<TurnState> {
      const { wf } = await wfP();
      const runId = randomUUID();
      emitters.set(runId, emit);
      try {
        const run = await wf.createRun({ runId });
        const r = (await run.start({ inputData: initialState(runId, input) })) as RunResult;
        const st = stateFromResult(r, runId, "start");
        if (!st.halted && !st.refusal) await emit({ event: "suspended", data: { runId, status: st.status } });
        return publicState(st);
      } finally {
        emitters.delete(runId);
      }
    },

    async decide(runId: string, d: DecideArgs): Promise<TurnState> {
      const st = await readState(runId);
      targetOf(st, d); // validate before resuming, so a bad request never fails the persisted run
      const run = await (await wfP()).wf.createRun({ runId });
      const r = (await run.resume({ step: "await-decision", resumeData: d })) as RunResult;
      return publicState(stateFromResult(r, runId, "apply"));
    },

    async outcome(runId: string, o: OutcomeArgs): Promise<OutcomeResult> {
      const st = await readState(runId);
      assertAwaitingOutcome(st);
      const run = await (await wfP()).wf.createRun({ runId });
      const r = (await run.resume({ step: "await-outcome", resumeData: o })) as RunResult;
      const done = stateFromResult(r, runId, "outcome");
      if (!done.outcomeResult) throw new CoachError(500, `run ${runId} finished without an outcome result`, "outcome");
      return done.outcomeResult;
    },
  };
}
