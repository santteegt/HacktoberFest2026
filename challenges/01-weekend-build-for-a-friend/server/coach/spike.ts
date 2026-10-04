// Mastra spike (T3, plan 2.5 / card T3): proves suspend -> process restart -> resume -> suspend -> restart -> resume
// against a LibSQL snapshot file. Each phase runs in a SEPARATE process:
//   npx tsx server/coach/spike.ts start            -> prints runId, ends suspended at "await-decision"
//   npx tsx server/coach/spike.ts decide <runId>   -> resumes, ends suspended at "await-outcome"
//   npx tsx server/coach/spike.ts outcome <runId>  -> resumes, ends "success"
// or `npx tsx server/coach/spike.ts all` to run the three phases as child processes.
// Uses MASTRA_DB_URL (default var/mastra.db via server/config.ts).
import { config } from "../config"; // FIRST: disables Mastra telemetry before @mastra/core loads
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { z } from "zod";

const State = z.object({
  runId: z.string(),
  log: z.array(z.string()),
  decision: z.string().optional(),
  outcome: z.string().optional(),
  pid: z.array(z.number()),
});
type StateT = z.infer<typeof State>;

async function build() {
  const { createWorkflow, createStep } = await import("@mastra/core/workflows");
  const { Mastra } = await import("@mastra/core/mastra");
  const { LibSQLStore } = await import("@mastra/libsql");

  const prep = createStep({
    id: "prep",
    inputSchema: State,
    outputSchema: State,
    execute: async ({ inputData }) => ({ ...inputData, log: [...inputData.log, "prep"], pid: [...inputData.pid, process.pid] }),
  });
  const awaitDecision = createStep({
    id: "await-decision",
    inputSchema: State,
    outputSchema: State,
    resumeSchema: z.object({ decision: z.string() }),
    execute: async ({ inputData, resumeData, suspend }) => {
      if (!resumeData) return (await suspend({})) as unknown as StateT;
      return { ...inputData, decision: resumeData.decision, log: [...inputData.log, "decided"], pid: [...inputData.pid, process.pid] };
    },
  });
  const awaitOutcome = createStep({
    id: "await-outcome",
    inputSchema: State,
    outputSchema: State,
    resumeSchema: z.object({ outcome: z.string() }),
    execute: async ({ inputData, resumeData, suspend }) => {
      if (!resumeData) return (await suspend({})) as unknown as StateT;
      return { ...inputData, outcome: resumeData.outcome, log: [...inputData.log, "outcome"], pid: [...inputData.pid, process.pid] };
    },
  });
  const wf = createWorkflow({ id: "coach-turn-spike", inputSchema: State, outputSchema: State })
    .then(prep)
    .then(awaitDecision)
    .then(awaitOutcome)
    .commit();
  const storage = new LibSQLStore({ id: "mastra-storage", url: config.mastraDbUrl });
  const mastra = new Mastra({ workflows: { spike: wf }, storage });
  // Wrapped: a Workflow has .then() (step chaining), so returning it from an async fn makes await hang.
  return { wf: mastra.getWorkflow("spike") };
}

function summarize(phase: string, r: { status: string; [k: string]: unknown }) {
  const out: Record<string, unknown> = { phase, pid: process.pid, status: r.status };
  if (r.status === "suspended") out.suspended = r.suspended;
  if (r.status === "success") out.result = r.result;
  if (r.status === "failed") out.error = String((r as { error?: unknown }).error);
  console.log(JSON.stringify(out));
}

async function main() {
  const [mode, runIdArg] = process.argv.slice(2);
  if (mode === "all") {
    const self = fileURLToPath(import.meta.url);
    const run = (args: string[]) => {
      const p = spawnSync("npx", ["tsx", self, ...args], { encoding: "utf8", env: process.env });
      process.stdout.write(p.stdout);
      if (p.status !== 0) process.stderr.write(p.stderr);
      return p.stdout;
    };
    const first = run(["start"]);
    const runId = /"runId":"([^"]+)"/.exec(first)?.[1];
    if (!runId) throw new Error("no runId from start");
    run(["decide", runId]);
    run(["outcome", runId]);
    return;
  }
  const { wf } = await build();
  const t0 = performance.now();
  if (mode === "start") {
    const runId = `spike-${Date.now()}`;
    const run = await wf.createRun({ runId });
    const r = await run.start({ inputData: { runId, log: [], pid: [] } });
    console.log(JSON.stringify({ runId }));
    summarize("start", r as never);
  } else if (mode === "decide" && runIdArg) {
    const run = await wf.createRun({ runId: runIdArg });
    const r = await run.resume({ step: "await-decision", resumeData: { decision: "apply" } });
    summarize("decide", r as never);
  } else if (mode === "outcome" && runIdArg) {
    const run = await wf.createRun({ runId: runIdArg });
    const r = await run.resume({ step: "await-outcome", resumeData: { outcome: "worse" } });
    summarize("outcome", r as never);
  } else {
    console.error("usage: spike.ts start | decide <runId> | outcome <runId> | all");
    process.exit(2);
  }
  console.log(JSON.stringify({ ms: Math.round(performance.now() - t0) }));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
