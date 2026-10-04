// Coach self-test with injected fakes (T3): no Ollama, no vault, no Mastra storage needed.
//   npx tsx server/coach/selftest.ts
// Checks: chip turns make zero model calls; the number guard rejects an invented number and the template
// is used; keyword refusal ends the turn after `classified`; an unreachable model falls back to keywords;
// the plain engine runs start -> decide -> outcome(worse) with offer-revert and a next suggestion.
import "../config";
import assert from "node:assert/strict";
import type { CoachEvent } from "../../src/shared/events";
import type { Change, LeverRow, OutcomeResult, Settings } from "../../src/shared/types";
import { defaultSettings } from "../config";
import { loadLevers, loadParams, loadPrechecks, loadSymptoms } from "../engine/data";
import { keywordClassify, refusalFor } from "../engine/keyword";
import { selectLevers } from "../engine/levers";
import { OllamaError, type OllamaClient } from "../llm/ollama";
import { numberGuard, templateExplanation, type CoachDeps } from "./steps";
import { createPlainEngine, memoryRunStore } from "./workflow.plain";

function fakeLlm(opts: { classify?: string; explain?: string; down?: boolean }) {
  const calls = { chat: 0, stream: 0 };
  const llm = {
    async chat() {
      calls.chat++;
      if (opts.down) throw new OllamaError("Ollama not reachable (fake)", true);
      return { text: opts.classify ?? "{}", ms: 1 };
    },
    async *chatStream() {
      calls.stream++;
      if (opts.down) throw new OllamaError("Ollama not reachable (fake)", true);
      for (const w of (opts.explain ?? "").split(/(?<= )/)) yield w;
      return { text: opts.explain ?? "", ms: 1 };
    },
  } as unknown as OllamaClient;
  return { llm, calls };
}

function fakeDeps(llm: OllamaClient | null, settings: Partial<Settings> = {}) {
  const changes: Change[] = [];
  let setup: Record<string, number | string | null> = { rearToeInDeg: 3.5, rearShockPos: 1, rearArbMm: 1.2, droopFrontGaugeMm: 5.6 };
  let n = 0;
  const deps: CoachDeps = {
    settings: async () => ({ ...defaultSettings, ...settings }),
    llm: () => llm,
    symptoms: loadSymptoms,
    prechecks: loadPrechecks,
    levers: loadLevers,
    params: () => loadParams().params,
    getChunk: () => undefined,
    keywordClassify,
    refusalFor,
    selectLevers,
    sessionContext: async () => ({ grip: "medium", setup, history: changes }),
    async applySetupChanges(sessionId, values, meta) {
      const out: Change[] = Object.entries(values).map(([param, to]) => ({
        id: `ch${++n}`, sessionId, beforeSetupId: `s${n}`, afterSetupId: `s${n + 1}`, param, from: setup[param] ?? null, to,
        source: meta.source, leverId: meta.leverId, symptomId: meta.symptomId, coachRunId: meta.coachRunId, createdAt: n,
      }));
      setup = { ...setup, ...values };
      changes.push(...out);
      return { setup: { id: `s${n + 1}`, values: setup, createdAt: n }, changes: out };
    },
    async setChangeOutcome(id, outcome) {
      const c = changes.find((x) => x.id === id)!;
      c.outcome = outcome;
      return c;
    },
  };
  return { deps, changes };
}

const collect = () => {
  const events: CoachEvent[] = [];
  return { events, emit: async (e: CoachEvent) => void events.push(e), names: () => events.filter((e) => e.event !== "token").map((e) => e.event).join(",") };
};

const results: string[] = [];
const ok = (name: string) => results.push(`ok   ${name}`);

// 1. chip: zero model calls for classify
{
  const f = fakeLlm({ explain: "Stand the rear shocks up one position for more exit traction. Check it over 3-5 laps." });
  const { deps } = fakeDeps(f.llm);
  const eng = createPlainEngine({ deps: () => deps, store: memoryRunStore() });
  const c = collect();
  const st = await eng.start({ sessionId: "s", symptomId: "exit-oversteer" }, c.emit);
  assert.equal(f.calls.chat, 0, "chip must not call classify");
  assert.equal(st.classification?.source, "chip");
  assert.equal(c.names(), "classified,precheck,suggestion,explained,suspended");
  ok(`chip turn: classify calls=${f.calls.chat}, explain calls=${f.calls.stream}, events=${c.names()}`);

  // 5. plain engine apply -> outcome worse
  const d = await eng.decide(st.runId, { decision: "apply" });
  assert.equal(d.status, "awaiting-outcome");
  const o: OutcomeResult = await eng.outcome(st.runId, { outcome: "worse" });
  assert.equal(o.prompt, "offer-revert");
  assert.deepEqual(o.revert, { param: "rearShockPos", to: 1 });
  assert.ok(o.next?.primary && o.next.skipped.some((k) => k.leverId === "xo-rear-shocks-up" && k.reason === "tried-worse"));
  ok(`plain engine: apply -> worse gives ${o.prompt} ${JSON.stringify(o.revert)}, next=${o.next!.primary!.lever.id}`);
}

// 2. number guard rejects an invented number -> template
{
  const f = fakeLlm({ explain: "Stand the rear shocks up to hole 4 and run 12 laps." });
  const { deps } = fakeDeps(f.llm);
  const c = collect();
  const st = await createPlainEngine({ deps: () => deps, store: memoryRunStore() }).start({ sessionId: "s", symptomId: "exit-oversteer" }, c.emit);
  assert.equal(st.explanation?.source, "template");
  ok(`number guard: invented "4"/"12" rejected -> template: ${JSON.stringify(st.explanation?.text.slice(0, 70))}...`);
  const lever = loadLevers().find((l) => l.id === "xo-rear-shocks-up") as LeverRow;
  const s = { lever, from: 1, to: 2, atLimit: false, needsCurrentValue: false };
  assert.ok(numberGuard("Go from 1 to 2, then three to five laps.", s));
  assert.ok(!numberGuard("Go to 7.", s));
  assert.ok(templateExplanation(s).startsWith("Stand the rear shocks up one position: 1 to 2 pos."));
  ok("number guard unit cases");
}

// 3. keyword refusal before any model call
{
  const f = fakeLlm({});
  const { deps } = fakeDeps(f.llm);
  const c = collect();
  const st = await createPlainEngine({ deps: () => deps, store: memoryRunStore() }).start({ sessionId: "s", utterance: "what shore hardness tyres" }, c.emit);
  assert.equal(f.calls.chat, 0);
  assert.equal(st.refusal?.reason, "tyre-compound-gap");
  assert.equal(c.names(), "classified,refusal");
  ok(`refusal: events=${c.names()}, citations=${JSON.stringify(st.refusal?.citations)}`);
}

// 4. model unreachable: keyword classification + template explanation; no match -> clear error event
{
  const f = fakeLlm({ down: true });
  const { deps } = fakeDeps(f.llm);
  const eng = createPlainEngine({ deps: () => deps, store: memoryRunStore() });
  const c = collect();
  const st = await eng.start({ sessionId: "s", utterance: "loose on power out of every corner" }, c.emit);
  assert.equal(st.classification?.source, "keyword");
  assert.equal(st.explanation?.source, "template");
  ok(`unreachable: ${st.classification?.symptomId} via keyword, explanation=${st.explanation?.source}, events=${c.names()}`);
  const c2 = collect();
  await eng.start({ sessionId: "s", utterance: "hmm not sure" }, c2.emit);
  assert.equal(c2.names(), "error");
  ok(`unreachable + no keyword: events=${c2.names()} ${JSON.stringify((c2.events[0]!.data as { message: string }).message)}`);
}

console.log(results.join("\n"));
console.log(`${results.length} checks passed`);
