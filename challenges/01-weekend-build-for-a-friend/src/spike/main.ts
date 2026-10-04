// Throwaway feasibility spike: can Gemma 4 E2B run on this phone's browser, and how well?
// Measures only; the real app talks to the model through src/llm/provider.ts.
import { Engine, loadLiteRtLm } from "@litert-lm/core";
import "../style.css";

const MODEL_URL =
  "https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/resolve/main/gemma-4-E2B-it-web.litertlm";
const MODEL_BYTES = 2_008_432_640;
const CACHE_NAME = "spike-models";

const SYMPTOMS = [
  "entry-understeer",
  "mid-understeer",
  "exit-understeer",
  "entry-oversteer",
  "exit-oversteer",
  "traction-roll",
  "bumpy-track",
  "out-of-scope",
] as const;

const SYSTEM = `You classify what an RC touring car driver says about how the car feels.
Allowed symptom_id values: ${SYMPTOMS.join(", ")}.
Allowed phase values: entry, mid, exit, none.
Reply with ONE line of JSON only, no prose, no code fences:
{"symptom_id":"<id>","phase":"<phase>","confidence":<0..1>}
Use "out-of-scope" for anything not about on-road touring car handling.`;

const TESTS: Array<{ say: string; expect: (typeof SYMPTOMS)[number] }> = [
  { say: "The front washes out when I turn in to the hairpin", expect: "entry-understeer" },
  { say: "Car pushes wide in the middle of the long sweeper", expect: "mid-understeer" },
  { say: "It won't rotate and runs wide when I get on the throttle out of the corner", expect: "exit-understeer" },
  { say: "The rear steps out as soon as I brake and turn in", expect: "entry-oversteer" },
  { say: "Back end snaps loose when I punch the throttle exiting", expect: "exit-oversteer" },
  { say: "The car wants to roll over on the inside wheels in fast direction changes", expect: "traction-roll" },
  { say: "It skips and gets twitchy over the bumps on the straight", expect: "bumpy-track" },
  { say: "How do I tune my nitro engine needle?", expect: "out-of-scope" },
  { say: "What charge rate should I use for my LiPo pack?", expect: "out-of-scope" },
  { say: "The car feels nervous turning in and the rear is loose off the corner", expect: "entry-oversteer" },
];

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const logEl = $("log");
const bar = $<HTMLProgressElement>("bar");
const reportEl = $<HTMLTextAreaElement>("report");

const report: Record<string, unknown> = { startedAt: new Date().toISOString() };
let engine: Engine | undefined;

function log(msg: string) {
  const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logEl.textContent += line + "\n";
  logEl.scrollTop = logEl.scrollHeight;
  console.log(line);
}
function showReport() {
  reportEl.value = JSON.stringify(report, null, 2);
}
function median(xs: number[]) {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
}
async function step<T>(name: string, fn: () => Promise<T>) {
  log(`${name}: start`);
  const t0 = performance.now();
  try {
    const out = await fn();
    const ms = Math.round(performance.now() - t0);
    log(`${name}: ok (${ms} ms)`);
    report[name] = { ok: true, ms, ...(out as object) };
  } catch (e) {
    const err = e as Error;
    log(`${name}: FAILED ${err?.name}: ${err?.message}`);
    report[name] = { ok: false, error: `${err?.name}: ${err?.message}` };
  }
  showReport();
}

async function checkDevice() {
  const out: Record<string, unknown> = {
    userAgent: navigator.userAgent,
    isSecureContext: window.isSecureContext,
    onLine: navigator.onLine,
    deviceMemoryGB: (navigator as unknown as { deviceMemory?: number }).deviceMemory ?? null,
    cpuThreads: navigator.hardwareConcurrency,
    crossOriginIsolated: window.crossOriginIsolated,
  };
  const gpu = (navigator as unknown as { gpu?: GPU }).gpu;
  if (!gpu) {
    out.webgpu = "navigator.gpu missing";
  } else {
    const adapter = await gpu.requestAdapter({ powerPreference: "high-performance" });
    if (!adapter) out.webgpu = "no adapter";
    else {
      const info = (adapter as unknown as { info?: Record<string, string> }).info ?? {};
      out.webgpu = {
        vendor: info.vendor,
        architecture: info.architecture,
        description: info.description,
        shaderF16: adapter.features.has("shader-f16"),
        subgroups: adapter.features.has("subgroups"),
        maxBufferSizeMB: Math.round(adapter.limits.maxBufferSize / 1e6),
        maxStorageBufferBindingSizeMB: Math.round(adapter.limits.maxStorageBufferBindingSize / 1e6),
      };
    }
  }
  const est = await navigator.storage?.estimate?.();
  out.storage = est ? { quotaMB: Math.round((est.quota ?? 0) / 1e6), usageMB: Math.round((est.usage ?? 0) / 1e6) } : "n/a";
  out.persisted = (await navigator.storage?.persist?.()) ?? null;
  const SR = (window as unknown as { SpeechRecognition?: any; webkitSpeechRecognition?: any });
  const Rec = SR.SpeechRecognition ?? SR.webkitSpeechRecognition;
  const speech: Record<string, unknown> = { recognition: !!Rec };
  if (Rec) {
    speech.processLocallyProp = "processLocally" in Rec.prototype;
    try {
      speech.onDeviceAvailable = String(await Rec.available?.({ langs: ["en-US"], processLocally: true }));
    } catch (e) {
      speech.onDeviceAvailable = `error: ${(e as Error).message}`;
    }
  }
  speech.localVoices = (speechSynthesis?.getVoices?.() ?? []).filter((v) => v.localService).length;
  out.speech = speech;
  out.microphoneApi = !!navigator.mediaDevices?.getUserMedia;
  return out;
}

async function download() {
  const cache = await caches.open(CACHE_NAME);
  if (await cache.match(MODEL_URL)) return { alreadyCached: true };
  bar.hidden = false;
  const res = await fetch(MODEL_URL);
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
  const total = Number(res.headers.get("content-length")) || MODEL_BYTES;
  let loaded = 0;
  let lastLog = 0;
  const counted = res.body.pipeThrough(
    new TransformStream<Uint8Array, Uint8Array>({
      transform(chunk, ctl) {
        loaded += chunk.byteLength;
        bar.value = loaded / total;
        if (loaded - lastLog > 100e6) {
          lastLog = loaded;
          log(`downloaded ${Math.round(loaded / 1e6)} MB`);
        }
        ctl.enqueue(chunk);
      },
    }),
  );
  await cache.put(MODEL_URL, new Response(counted, { headers: { "content-length": String(total) } }));
  bar.hidden = true;
  return { bytes: loaded };
}

async function initRuntime() {
  await loadLiteRtLm(`${location.origin}/litert-wasm`);
  return { wasmPath: `${location.origin}/litert-wasm` };
}

async function createEngine() {
  const cache = await caches.open(CACHE_NAME);
  const hit = await cache.match(MODEL_URL);
  if (!hit?.body) throw new Error("model not in cache; run step 2");
  const onlineAtStart = navigator.onLine;
  engine = await Engine.create({ model: hit.body, mainExecutorSettings: { maxNumTokens: 2048 } });
  const mem = (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory;
  return { onlineAtStart, jsHeapMB: mem ? Math.round(mem.usedJSHeapSize / 1e6) : null };
}

async function runTests() {
  if (!engine) throw new Error("engine not created; run step 4");
  const results: unknown[] = [];
  const ttft: number[] = [];
  const rate: number[] = [];
  let valid = 0;
  let correct = 0;
  for (const [i, t] of TESTS.entries()) {
    const convo = await engine.createConversation({
      preface: { messages: [{ role: "system", content: SYSTEM }] },
      sessionConfig: { maxOutputTokens: 80 },
    });
    const t0 = performance.now();
    let first = 0;
    let chunks = 0;
    let text = "";
    for await (const chunk of convo.sendMessageStreaming(t.say)) {
      const parts = Array.isArray(chunk.content) ? chunk.content : chunk.content ? [chunk.content] : [];
      for (const item of parts) {
        const piece = typeof item === "string" ? item : item.type === "text" ? item.text : "";
        if (piece) {
          if (!first) first = performance.now() - t0;
          chunks += 1;
          text += piece;
        }
      }
    }
    const total = performance.now() - t0;
    (convo as unknown as { delete?: () => void }).delete?.();
    let parsed: { symptom_id?: string } | null = null;
    try {
      const m = text.match(/\{[\s\S]*\}/);
      parsed = m ? JSON.parse(m[0]) : null;
    } catch {
      parsed = null;
    }
    const isValid = !!parsed && SYMPTOMS.includes(parsed.symptom_id as (typeof SYMPTOMS)[number]);
    const isCorrect = isValid && parsed?.symptom_id === t.expect;
    if (isValid) valid += 1;
    if (isCorrect) correct += 1;
    ttft.push(first);
    if (chunks > 1) rate.push(chunks / ((total - first) / 1000));
    results.push({ i, say: t.say, expect: t.expect, got: parsed?.symptom_id ?? null, ok: isCorrect, ttftMs: Math.round(first), chunks, totalMs: Math.round(total), raw: text.slice(0, 160) });
    log(`test ${i + 1}/${TESTS.length}: ${parsed?.symptom_id ?? "INVALID"} (want ${t.expect}) ttft ${Math.round(first)} ms`);
    report.tests = { partial: results };
    showReport();
  }
  return {
    onLineDuringTests: navigator.onLine,
    jsonValidPct: Math.round((valid / TESTS.length) * 100),
    correctPct: Math.round((correct / TESTS.length) * 100),
    ttftMedianMs: Math.round(median(ttft) ?? 0),
    decodeChunksPerSecMedian: Math.round((median(rate) ?? 0) * 10) / 10,
    results,
  };
}

$("b1").addEventListener("click", () => step("device", checkDevice));
$("b2").addEventListener("click", () => step("download", download));
$("b3").addEventListener("click", () => step("runtime", initRuntime));
$("b4").addEventListener("click", () => step("engine", createEngine));
$("b5").addEventListener("click", () => step("tests", runTests));
$("b6").addEventListener("click", () => {
  showReport();
  reportEl.focus();
  reportEl.select();
});
addEventListener("error", (e) => log(`window error: ${e.message}`));
addEventListener("unhandledrejection", (e) => log(`unhandled: ${String((e as PromiseRejectionEvent).reason)}`));
log("ready");
