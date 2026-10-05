// Symptom classifier eval (T9; plan 8.1). Runs the real classifier path against Ollama, plus the
// keyword baseline on the same cases, and prints one JSON summary.
//
//   npm run eval:symptoms                       (model: OLLAMA_MODEL or gemma4:e4b-it-qat)
//   npm run eval:symptoms -- gemma4:e2b-it-qat  (model from the first CLI arg)
//   CPU_ONLY=1 npm run eval:symptoms            (num_gpu 0, 6 threads: a PROXY for an Intel Mac, not a measurement of one)
//   EVAL_OUT=path.json                          (also write the full per-case results to a file)
//   OLLAMA_URL, OLLAMA_NUM_CTX                  (defaults http://localhost:11434 and the server default 4096)
//
// Fidelity to the server: same system prompt, schema and knobs (imported from server/coach/prompts.ts),
// same body shape as OllamaClient.chatBody (think false, keep_alive, format, temperature 0, num_ctx,
// num_predict). Differences: streaming is on so the first content chunk can be timed (the server's
// classifier call is non-streaming, same compute), and CPU_ONLY adds num_gpu/num_thread.
// Ollama's `format` enforces the JSON schema, so every reply parses; what is measured is whether the
// chosen id is right and how fast. Gemma is judged on the model alone; the "pipeline" line applies the
// server's keyword refusal rules first, as server/coach/steps.ts does.
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { CLASSIFIER_OPTIONS, CLASSIFIER_SCHEMA, CLASSIFIER_SYSTEM } from "../server/coach/prompts";
import { keywordClassify, offTopic, refusalFor } from "../server/engine/keyword";
import { KEEP_ALIVE, ndjson } from "../server/llm/ollama";
import type { SymptomDef } from "../src/shared/types";

const OLLAMA = (process.env.OLLAMA_URL ?? "http://localhost:11434").replace(/\/+$/, "");
const MODEL = process.argv[2] ?? process.env.OLLAMA_MODEL ?? "gemma4:e4b-it-qat";
const NUM_CTX = Number(process.env.OLLAMA_NUM_CTX ?? 4096);
const CPU_ONLY = process.env.CPU_ONLY === "1";
const NUM_THREAD = 6;

const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));
interface Case {
  id: string;
  say: string;
  expect: string;
  style: "plain" | "colloquial";
  source: string;
  rewordSuggested?: boolean;
  friendWording?: boolean;
}
const { cases } = JSON.parse(readFileSync(here("../data/eval/symptom-utterances.json"), "utf8")) as { cases: Case[] };
const symptoms = JSON.parse(readFileSync(here("../data/symptoms.json"), "utf8")) as SymptomDef[];

const median = (xs: number[]) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m]! : (s[m - 1]! + s[m]!) / 2;
};
/** Nearest-rank percentile. */
const pct = (xs: number[], p: number) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.ceil((p / 100) * s.length) - 1)]!;
};
const r0 = (n: number | null) => (n === null ? null : Math.round(n));
const r1 = (n: number | null) => (n === null ? null : Math.round(n * 10) / 10);
const rate = (hit: number, n: number) => (n ? Math.round((hit / n) * 1000) / 10 : null);

interface Raw {
  message?: { content?: string };
  done?: boolean;
  error?: string;
  load_duration?: number;
  prompt_eval_count?: number;
  prompt_eval_duration?: number;
  eval_count?: number;
  eval_duration?: number;
}
interface Call {
  text: string;
  ttftMs: number;
  totalMs: number;
  prefillMs: number;
  promptTokens: number;
  evalTokens: number;
  tokPerSec: number;
}

async function classify(say: string): Promise<Call> {
  const body = {
    model: MODEL,
    stream: true,
    think: false,
    keep_alive: KEEP_ALIVE,
    format: CLASSIFIER_SCHEMA,
    messages: [
      { role: "system", content: CLASSIFIER_SYSTEM },
      { role: "user", content: say.trim().slice(0, CLASSIFIER_OPTIONS.maxUserChars) },
    ],
    options: {
      temperature: CLASSIFIER_OPTIONS.temperature,
      num_ctx: NUM_CTX,
      num_predict: CLASSIFIER_OPTIONS.numPredict,
      ...(CPU_ONLY ? { num_gpu: 0, num_thread: NUM_THREAD } : {}),
    },
  };
  const t0 = performance.now();
  const res = await fetch(`${OLLAMA}/api/chat`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!res.ok || !res.body) throw new Error(`Ollama HTTP ${res.status}: ${await res.text().catch(() => "")}`);
  let text = "";
  let ttftMs = NaN;
  let last: Raw = {};
  for await (const c of ndjson<Raw>(res.body)) {
    if (c.error) throw new Error(c.error);
    const piece = c.message?.content ?? "";
    if (piece) {
      if (Number.isNaN(ttftMs)) ttftMs = performance.now() - t0;
      text += piece;
    }
    if (c.done) last = c;
  }
  const totalMs = performance.now() - t0;
  const evalTokens = last.eval_count ?? 0;
  return {
    text,
    ttftMs: Number.isNaN(ttftMs) ? totalMs : ttftMs,
    totalMs,
    prefillMs: ((last.load_duration ?? 0) + (last.prompt_eval_duration ?? 0)) / 1e6,
    promptTokens: last.prompt_eval_count ?? 0,
    evalTokens,
    tokPerSec: last.eval_duration ? evalTokens / (last.eval_duration / 1e9) : 0,
  };
}

async function residency() {
  try {
    const j = (await (await fetch(`${OLLAMA}/api/ps`)).json()) as { models?: { name: string; size: number; size_vram: number; context_length?: number }[] };
    const m = (j.models ?? []).find((x) => x.name === MODEL);
    if (!m) return null;
    return { residentMB: Math.round(m.size / 1e6), vramMB: Math.round(m.size_vram / 1e6), gpuPct: Math.round((m.size_vram / m.size) * 100), contextLength: m.context_length ?? null };
  } catch {
    return null;
  }
}

async function ollamaVersion() {
  try {
    return ((await (await fetch(`${OLLAMA}/api/version`)).json()) as { version?: string }).version ?? null;
  } catch {
    return null;
  }
}

interface Row {
  id: string;
  say: string;
  expect: string;
  style: string;
  friendWording: boolean;
  got: string | null;
  alt: string | null;
  confidence: number | null;
  ok: boolean;
  top2: boolean;
  pipelineGot: string | null;
  pipelineOk: boolean;
  kw: string;
  kwOk: boolean;
  ttftMs: number;
  totalMs: number;
  prefillMs: number;
  promptTokens: number;
  evalTokens: number;
  tokPerSec: number;
}

/** Keyword baseline: the server's refusal rules, then keywordClassify; no match is reported as "no-match". */
function keywordBaseline(say: string): string {
  if (refusalFor(say) || offTopic(say)) return "out-of-scope";
  return keywordClassify(say, symptoms)?.symptomId ?? "no-match";
}

const stats = (rs: { ok: boolean }[]) => ({ n: rs.length, correct: rs.filter((r) => r.ok).length, pct: rate(rs.filter((r) => r.ok).length, rs.length) });

async function main() {
  const version = await ollamaVersion();
  if (!version) throw new Error(`Ollama is not reachable at ${OLLAMA}`);
  console.error(`model ${MODEL}  ollama ${version}  num_ctx ${NUM_CTX}  ${CPU_ONLY ? `CPU_ONLY (num_gpu 0, ${NUM_THREAD} threads)` : "default placement"}  ${cases.length} cases`);

  await classify("warm up: the front washes out into the corner"); // load the model so timings exclude cold start
  const rows: Row[] = [];
  for (const c of cases) {
    const r = await classify(c.say);
    let got: string | null = null;
    let alt: string | null = null;
    let confidence: number | null = null;
    try {
      const j = JSON.parse(r.text) as { symptom_id?: string; alt_id?: string; confidence?: number };
      got = j.symptom_id ?? null;
      alt = j.alt_id ?? null;
      confidence = typeof j.confidence === "number" ? j.confidence : null;
    } catch {
      /* counted as a miss, and reported under parseFailures */
    }
    const pipelineGot = refusalFor(c.say) || offTopic(c.say) ? "out-of-scope" : got;
    const kw = keywordBaseline(c.say);
    rows.push({
      id: c.id,
      say: c.say,
      expect: c.expect,
      style: c.style,
      friendWording: !!c.friendWording,
      got,
      alt,
      confidence,
      ok: got === c.expect,
      top2: got === c.expect || (alt !== null && alt !== "none" && alt === c.expect),
      pipelineGot,
      pipelineOk: pipelineGot === c.expect,
      kw,
      kwOk: kw === c.expect,
      ttftMs: r.ttftMs,
      totalMs: r.totalMs,
      prefillMs: r.prefillMs,
      promptTokens: r.promptTokens,
      evalTokens: r.evalTokens,
      tokPerSec: r.tokPerSec,
    });
    console.error(
      `${got === c.expect ? "ok  " : "MISS"} ${String(Math.round(r.ttftMs)).padStart(5)} ms ttft ${String(Math.round(r.totalMs)).padStart(5)} ms total  want ${c.expect.padEnd(21)} got ${String(got).padEnd(21)} kw ${kw}`,
    );
  }
  const resident = await residency();

  const oos = rows.filter((r) => r.expect === "out-of-scope");
  const colloquial = rows.filter((r) => r.style === "colloquial");
  const plain = rows.filter((r) => r.style === "plain");
  const friend = rows.filter((r) => r.friendWording);
  const inScope = rows.filter((r) => r.expect !== "out-of-scope");
  const timed = (f: (r: Row) => number) => rows.map(f);

  const summary = {
    date: new Date().toISOString(),
    model: MODEL,
    ollamaVersion: version,
    numCtx: NUM_CTX,
    cpuOnly: CPU_ONLY,
    numThread: CPU_ONLY ? NUM_THREAD : null,
    placement: resident,
    options: { temperature: CLASSIFIER_OPTIONS.temperature, numPredict: CLASSIFIER_OPTIONS.numPredict, think: false, format: "json schema (enforced)" },
    cases: rows.length,
    outOfScopeCases: oos.length,
    colloquialCases: colloquial.length,
    friendWordedCases: friend.length,
    parseFailures: rows.filter((r) => r.got === null).length,
    gemma: {
      overall: stats(rows),
      outOfScope: stats(oos),
      inScope: stats(inScope),
      colloquial: stats(colloquial),
      plain: stats(plain),
      friendWorded: friend.length ? stats(friend) : null,
      top2Pct: rate(rows.filter((r) => r.top2).length, rows.length),
      pipelineWithKeywordRefusals: stats(rows.map((r) => ({ ok: r.pipelineOk }))),
    },
    keywordBaseline: {
      overall: stats(rows.map((r) => ({ ok: r.kwOk }))),
      outOfScope: stats(oos.map((r) => ({ ok: r.kwOk }))),
      inScope: stats(inScope.map((r) => ({ ok: r.kwOk }))),
      colloquial: stats(colloquial.map((r) => ({ ok: r.kwOk }))),
      plain: stats(plain.map((r) => ({ ok: r.kwOk }))),
      noMatch: rows.filter((r) => r.kw === "no-match").length,
    },
    timingMs: {
      ttftWallMedian: r0(median(timed((r) => r.ttftMs))),
      ttftWallP90: r0(pct(timed((r) => r.ttftMs), 90)),
      totalWallMedian: r0(median(timed((r) => r.totalMs))),
      totalWallP90: r0(pct(timed((r) => r.totalMs), 90)),
      prefillOllamaMedian: r0(median(timed((r) => r.prefillMs))),
      prefillOllamaP90: r0(pct(timed((r) => r.prefillMs), 90)),
    },
    decodeTokensPerSecMedian: r1(median(timed((r) => r.tokPerSec))),
    promptTokensMedian: median(timed((r) => r.promptTokens)),
    outputTokensMedian: median(timed((r) => r.evalTokens)),
    misses: rows
      .filter((r) => !r.ok)
      .map((r) => ({ id: r.id, say: r.say, style: r.style, expect: r.expect, got: r.got, alt: r.alt, confidence: r.confidence, keyword: r.kw })),
    keywordMisses: rows.filter((r) => !r.kwOk).map((r) => ({ id: r.id, expect: r.expect, keyword: r.kw })),
    note: "Schema enforcement (Ollama `format`) guarantees valid JSON and valid ids; correctness is the chosen id. Single run per case at temperature 0. Dev-machine numbers, not the friend's laptop.",
  };
  console.log(JSON.stringify(summary, null, 2));
  if (process.env.EVAL_OUT) writeFileSync(process.env.EVAL_OUT, JSON.stringify({ summary, rows }, null, 2));
}

main().catch((e) => {
  console.error(`eval-symptoms failed: ${(e as Error).message}`);
  process.exit(1);
});
