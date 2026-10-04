// Baseline: can the local model map a driver's words to a fixed symptom id?
// Usage: node scripts/eval-symptoms.mjs [model]   (default from VITE_OLLAMA_MODEL or gemma4:e4b-it-qat)
// Uses Ollama's JSON-schema `format`, so output shape is enforced; we measure correctness and speed.
import { readFileSync } from "node:fs";

const OLLAMA = process.env.VITE_OLLAMA_URL ?? "http://localhost:11434";
const MODEL = process.argv[2] ?? process.env.VITE_OLLAMA_MODEL ?? "gemma4:e4b-it-qat";
const NUM_CTX = Number(process.env.OLLAMA_NUM_CTX ?? 4096);
const CPU_ONLY = process.env.CPU_ONLY === "1"; // proxy for machines without a usable GPU (not a real measurement of them)
const { symptoms, cases } = JSON.parse(readFileSync("data/eval/symptom-utterances.json", "utf8"));

const system = `You classify what an RC touring car driver says about how the car feels.
Allowed symptom_id values: ${symptoms.join(", ")}.
Allowed phase values: entry, mid, exit, none.
Use "out-of-scope" for anything not about on-road touring car handling.`;
const schema = {
  type: "object",
  properties: {
    symptom_id: { type: "string", enum: symptoms },
    phase: { type: "string", enum: ["entry", "mid", "exit", "none"] },
    confidence: { type: "number" },
  },
  required: ["symptom_id", "phase", "confidence"],
};
const median = (xs) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)];

async function chat(say) {
  const res = await fetch(`${OLLAMA}/api/chat`, {
    method: "POST",
    body: JSON.stringify({
      model: MODEL, stream: false, format: schema, think: false,
      options: { temperature: 0, num_ctx: NUM_CTX, ...(CPU_ONLY ? { num_gpu: 0, num_thread: 6 } : {}) },
      messages: [{ role: "system", content: system }, { role: "user", content: say }],
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

await chat("warm up"); // load the model so timings exclude cold start
const rows = [];
for (const c of cases) {
  const r = await chat(c.say);
  let got = null;
  try { got = JSON.parse(r.message.content).symptom_id; } catch {}
  const ttftMs = (r.load_duration + r.prompt_eval_duration) / 1e6;
  const tps = r.eval_count / (r.eval_duration / 1e9);
  rows.push({ say: c.say, expect: c.expect, got, ok: got === c.expect, ttftMs: Math.round(ttftMs), tokens: r.eval_count, tokensPerSec: Math.round(tps * 10) / 10 });
  console.log(`${got === c.expect ? "ok  " : "MISS"} ${String(Math.round(ttftMs)).padStart(5)} ms  want ${c.expect.padEnd(17)} got ${got}`);
}
const correct = rows.filter((r) => r.ok).length;
console.log(JSON.stringify({
  model: MODEL, numCtx: NUM_CTX, cpuOnly: CPU_ONLY, date: new Date().toISOString(), cases: rows.length,
  correctPct: Math.round((correct / rows.length) * 100),
  ttftMedianMs: median(rows.map((r) => r.ttftMs)),
  tokensPerSecMedian: median(rows.map((r) => r.tokensPerSec)),
}, null, 2));
