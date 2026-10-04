// MOCK API (T4a). Canned in-memory data behind the same typed client, enabled with `?mock=1` or VITE_MOCK_API=1.
// Purpose: test the UI before the real backend works, and a stand-alone demo fallback.
//   ?mock=1            demo session "Demo track (mock)" with two runs and one saved setup
//   ?mock=1&fresh=1    no sessions (shows the first-run overlay)
// Reads the real data files (levers, symptoms, params, prechecks, kb) so labels and citations are genuine,
// but the lever selection here is a small stand-in for the server engine, not the engine itself.
// Nothing here talks to a network or to a model; "explained" text is template text streamed word by word.
import type { Endpoints, MetaResponse, SessionBundle } from "../shared/api";
import type { CoachEvent, PullEvent } from "../shared/events";
import type {
  Change,
  CoachTurnInput,
  KbChunk,
  LeverRow,
  LeverSuggestion,
  OutcomeResult,
  ParamDef,
  ParamValue,
  PrecheckDef,
  Run,
  SavedSetup,
  Session,
  Setup,
  Settings,
  SetupValues,
  Suggestion,
  SymptomDef,
  TurnState,
} from "../shared/types";
import type { RequestOptions } from "./client";
import kbJson from "../../data/generated/kb.json";
import leversJson from "../../data/levers.json";
import paramsJson from "../../data/params.bd12.json";
import prechecksJson from "../../data/prechecks.json";
import symptomsJson from "../../data/symptoms.json";

const levers = leversJson as unknown as LeverRow[];
const symptoms = symptomsJson as unknown as SymptomDef[];
const prechecks = prechecksJson as unknown as PrecheckDef[];
const paramsFile = paramsJson as unknown as {
  car: "yokomo-bd12" | "generic";
  baselineRule: string;
  conventions: Record<string, string>;
  params: ParamDef[];
};
const kb = kbJson as unknown as { contentHash: string; pages: unknown[]; chunks: KbChunk[] };
const paramById = new Map(paramsFile.params.map((p) => [p.id, p]));

// ---------- helpers ----------

let counter = 0;
const nid = (p: string) => `mock-${p}-${++counter}`;
const now = () => Date.now();
const round = (n: number) => Math.round(n * 100) / 100;
const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v)) as T;

class MockError extends Error {
  status: number;
  constructor(message: string, status = 400) {
    super(message);
    this.status = status;
  }
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(new DOMException("Aborted", "AbortError"));
    const t = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(t);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

// ---------- state ----------

const settings: Settings = {
  ollamaUrl: "http://localhost:11434",
  model: "gemma4:e2b-it-qat",
  numCtx: 4096,
  llmPhrasing: true,
  reviewedOnly: false,
  voiceIn: "off",
  voiceOut: "browser",
  tempUnit: "C",
  car: "yokomo-bd12",
};

const setups = new Map<string, Setup>();
const sessions = new Map<string, Session>();
const runs: Run[] = [];
const changes: Change[] = [];
const saved: SavedSetup[] = [];
const turns = new Map<string, { state: TurnState; symptomId: string; phase: TurnState["input"]["phase"] }>();

function baseline(car: Session["car"]): SetupValues {
  const v: SetupValues = {};
  for (const p of paramsFile.params) {
    if (p.kind === "computed") continue;
    const first = car === "generic" ? p.generic : p.bd12;
    const second = car === "generic" ? p.bd12 : p.generic;
    v[p.id] = first ?? second ?? null;
  }
  return v;
}

function makeSession(body: Pick<Session, "date" | "car" | "conditions" | "notes">, extra?: SetupValues): Session {
  const setup: Setup = { id: nid("setup"), values: { ...baseline(body.car), ...extra }, createdAt: now() };
  setups.set(setup.id, setup);
  const s: Session = { id: nid("session"), ...body, currentSetupId: setup.id, createdAt: now() };
  sessions.set(s.id, s);
  return s;
}

function seedDemo(): void {
  const s = makeSession(
    {
      date: new Date().toISOString().slice(0, 10),
      car: "yokomo-bd12",
      conditions: {
        trackName: "Demo track (mock)",
        surface: "asphalt",
        grip: "medium",
        bumpy: false,
        layout: "medium",
        trackTempC: 24,
        timeOfDay: "midday",
      },
      notes: "Mock data. Rear shock position preset to 2 so the demo path has a number.",
    },
    { rearShockPos: 2, frontShockPos: 2 },
  );
  runs.push(
    {
      id: nid("run"),
      sessionId: s.id,
      seq: 1,
      setupId: s.currentSetupId,
      lapTimesMs: [15100, 15010, 15050],
      bestLapMs: 15010,
      rating: 3,
      feel: [],
      createdAt: now() - 3_600_000,
    },
    {
      id: nid("run"),
      sessionId: s.id,
      seq: 2,
      setupId: s.currentSetupId,
      lapTimesMs: [15020, 14950, 14990],
      bestLapMs: 14950,
      rating: 3,
      feel: ["exit-oversteer"],
      createdAt: now() - 1_800_000,
    },
  );
  saved.push({
    id: nid("saved"),
    label: "Demo track, midday (mock)",
    setupId: s.currentSetupId,
    conditions: s.conditions,
    sessionId: s.id,
    verdict: "Mock saved setup",
    createdAt: now() - 86_400_000,
  });
}

function resetState(withDemo: boolean): void {
  setups.clear();
  sessions.clear();
  runs.length = 0;
  changes.length = 0;
  saved.length = 0;
  turns.clear();
  if (withDemo) seedDemo();
}

resetState(typeof location === "undefined" || new URLSearchParams(location.search).get("fresh") !== "1");

// ---------- setup changes (copy-on-write) ----------

function applySetupInternal(
  sessionId: string,
  values: Record<string, ParamValue>,
  meta: { source: Change["source"]; leverId?: string; symptomId?: string; coachRunId?: string },
): { setup: Setup; changes: Change[] } {
  const s = sessions.get(sessionId);
  if (!s) throw new MockError("session not found", 404);
  const before = setups.get(s.currentSetupId)!;
  const next: Setup = {
    id: nid("setup"),
    values: { ...before.values, ...values },
    parentId: before.id,
    createdAt: now(),
  };
  setups.set(next.id, next);
  const made: Change[] = [];
  for (const [param, to] of Object.entries(values)) {
    if (before.values[param] === to) continue;
    made.push({
      id: nid("change"),
      sessionId,
      beforeSetupId: before.id,
      afterSetupId: next.id,
      param,
      from: before.values[param] ?? null,
      to,
      leverId: meta.leverId,
      symptomId: meta.symptomId,
      source: meta.source,
      coachRunId: meta.coachRunId,
      createdAt: now(),
    });
  }
  changes.push(...made);
  s.currentSetupId = next.id;
  return { setup: next, changes: made };
}

// ---------- stand-in lever selection (the real one is server/engine/levers.ts) ----------

function selectLevers(symptomId: string, session: Session): Suggestion {
  const values = setups.get(session.currentSetupId)!.values;
  const recent = changes.filter((c) => c.sessionId === session.id).slice(-3);
  const skipped: Suggestion["skipped"] = [];
  const picks: LeverSuggestion[] = [];
  const rows = levers.filter((l) => l.symptomId === symptomId).sort((x, y) => x.priority - y.priority);
  for (const row of rows) {
    if (settings.reviewedOnly && row.status !== "reviewed") {
      skipped.push({ leverId: row.id, reason: "draft-hidden" });
      continue;
    }
    if (row.grip && !row.grip.includes(session.conditions.grip)) {
      skipped.push({ leverId: row.id, reason: "grip-mismatch" });
      continue;
    }
    const tried = recent.find((c) => c.leverId === row.id && (c.outcome === "worse" || c.outcome === "same"));
    if (tried) {
      skipped.push({ leverId: row.id, reason: tried.outcome === "worse" ? "tried-worse" : "tried-same" });
      continue;
    }
    if (row.kind === "qualitative" || !row.param) {
      picks.push({ lever: row, from: null, to: null, atLimit: false, needsCurrentValue: false });
      continue;
    }
    const p = paramById.get(row.param);
    const current = values[row.param];
    if (typeof current !== "number") {
      picks.push({ lever: row, from: null, to: null, atLimit: false, needsCurrentValue: true });
      continue;
    }
    const dir = row.direction === "decrease" ? -1 : 1;
    const lo = Math.max(row.min ?? -Infinity, p?.min ?? -Infinity);
    const hi = Math.min(row.max ?? Infinity, p?.max ?? Infinity);
    const to = round(Math.min(hi, Math.max(lo, current + dir * (row.step ?? p?.step ?? 1))));
    if (to === current) {
      skipped.push({ leverId: row.id, reason: "at-limit" });
      continue;
    }
    const scene =
      p?.explainer && typeof to === "number"
        ? { explainer: p.explainer, param: row.param, from: current, to }
        : undefined;
    picks.push({ lever: row, from: current, to, atLimit: false, needsCurrentValue: false, scene });
  }
  const sug: Suggestion = { primary: picks[0] ?? null, alternatives: picks.slice(1, 3), skipped };
  if (!sug.primary) {
    sug.noLeverReason =
      "Every option in my notes for this is at its limit or already tried. Re-check the basics, or log what you changed by hand.";
  }
  const sym = symptoms.find((s) => s.id === symptomId);
  if (sym?.precheckOnly) {
    sug.primary = null;
    sug.alternatives = [];
    sug.noLeverReason =
      "This one never gets a setup change from me. Walk the checks above: tweak, weight and steering are the usual cause.";
  }
  return sug;
}

function templateText(s: LeverSuggestion): string {
  const l = s.lever;
  const move =
    s.from !== null && s.to !== null ? `: ${s.from} to ${s.to}${l.unit ? ` ${l.unit}` : ""}` : "";
  return `${l.action}${move}. ${l.effect} Trade-off: ${l.tradeOff} Check: ${l.verify}`;
}

// ---------- coach turn (SSE stand-in) ----------

const REFUSALS: { re: RegExp; reason: "tyre-compound-gap" | "electronics" | "other-car-type"; message: string; citations: string[] }[] = [
  {
    re: /shore|compound|insert|foam|tyre hardness|tire hardness/i,
    reason: "tyre-compound-gap",
    message:
      "My notes have no tyre compound, shore or insert data, so I will not guess. Tyre choice is a real gap in my notes.",
    citations: ["touring-car-traction-and-tire-management#a-real-gap-not-an-extraction-failure"],
  },
  {
    re: /\besc\b|timing|boost|motor|lipo|charger/i,
    reason: "electronics",
    message: "Electronics (ESC, motor timing, batteries) are outside what my notes cover.",
    citations: [],
  },
  {
    re: /nitro|glow|buggy|off-?road|crawler|drift/i,
    reason: "other-car-type",
    message: "My notes are for a 1/10 electric touring car only.",
    citations: [],
  },
];

function keywordClassify(text: string): { id: string; confidence: number } | null {
  const words = new Set(text.toLowerCase().match(/[a-z']+/g) ?? []);
  let best: { id: string; score: number } | null = null;
  for (const s of symptoms) {
    if (s.id === "out-of-scope") continue;
    let score = 0;
    for (const phrase of [...s.synonyms, s.label]) {
      const pw = phrase.toLowerCase().match(/[a-z']+/g) ?? [];
      score += pw.filter((w) => w.length > 3 && words.has(w)).length / Math.max(pw.length, 1);
    }
    if (text.toLowerCase().includes("snap") || text.toLowerCase().includes("rear") || text.toLowerCase().includes("loose")) {
      if (s.id === "exit-oversteer" && /power|trigger|throttle|punch|exit|gas/i.test(text)) score += 2;
    }
    if (!best || score > best.score) best = { id: s.id, score };
  }
  if (!best || best.score <= 0) return null;
  return { id: best.id, confidence: Math.min(0.95, round(0.45 + best.score / 4)) };
}

export async function* mockCoachTurn(input: CoachTurnInput, signal?: AbortSignal): AsyncGenerator<CoachEvent> {
  const session = sessions.get(input.sessionId);
  if (!session) throw new MockError("session not found", 404);
  const t0 = performance.now();
  let symptomId: string;
  let confidence = 1;
  let source: "chip" | "keyword" = "chip";
  if (input.symptomId) {
    symptomId = input.symptomId;
  } else {
    const text = input.utterance ?? "";
    await sleep(900, signal); // pretend the classify call takes a moment
    const refusal = REFUSALS.find((r) => r.re.test(text));
    if (refusal) {
      yield { event: "classified", data: { symptomId: "out-of-scope", altId: "none", phase: "none", confidence: 0.9, source: "keyword", ms: Math.round(performance.now() - t0) } };
      yield { event: "refusal", data: { reason: refusal.reason, message: refusal.message, citations: refusal.citations } };
      return;
    }
    const hit = keywordClassify(text);
    if (!hit) {
      yield { event: "classified", data: { symptomId: "out-of-scope", altId: "none", phase: "none", confidence: 0.6, source: "keyword" } };
      yield {
        event: "refusal",
        data: { reason: "out-of-scope", message: "I could not match that to something in my notes. Tap the closest symptom below.", citations: [] },
      };
      return;
    }
    symptomId = hit.id;
    confidence = hit.confidence;
    source = "keyword";
  }
  const sym = symptoms.find((s) => s.id === symptomId);
  if (!sym) throw new MockError(`unknown symptom ${symptomId}`);
  const alt = symptoms.find((s) => s.id !== symptomId && s.phase === sym.phase && s.id !== "out-of-scope" && !s.precheckOnly);
  yield {
    event: "classified",
    data: {
      symptomId,
      altId: source === "chip" ? "none" : (alt?.id ?? "none"),
      phase: input.phase ?? sym.phase,
      confidence,
      source,
      ms: source === "chip" ? 0 : Math.round(performance.now() - t0),
    },
  };
  yield { event: "precheck", data: sym.prechecks.map((id) => prechecks.find((p) => p.id === id)).filter((p): p is PrecheckDef => !!p) };
  const suggestion = selectLevers(symptomId, session);
  yield { event: "suggestion", data: suggestion };

  let explanation = { text: "", source: "llm" as const, ms: 0 };
  if (suggestion.primary) {
    const text = templateText(suggestion.primary);
    const t1 = performance.now();
    for (const word of text.split(/(?<=\s)/)) {
      await sleep(30, signal);
      yield { event: "token", data: { text: word } };
    }
    explanation = { text, source: "llm", ms: Math.round(performance.now() - t1) };
    yield { event: "explained", data: explanation };
  }
  const runId = nid("turn");
  const state: TurnState = {
    runId,
    input,
    classification: { symptomId, altId: "none", phase: input.phase ?? sym.phase, confidence, source },
    prechecks: [],
    suggestion,
    explanation: suggestion.primary ? explanation : undefined,
    status: suggestion.primary ? "awaiting-decision" : "done",
  };
  turns.set(runId, { state, symptomId, phase: input.phase ?? sym.phase });
  yield { event: "suspended", data: { runId, status: state.status } };
}

function decide(runId: string, body: Endpoints["POST /api/coach/:runId/decide"]["body"]): TurnState {
  const t = turns.get(runId);
  if (!t) throw new MockError("unknown run", 404);
  const { state } = t;
  state.decision = body.decision;
  if (body.decision === "skip") {
    state.status = "done";
    return clone(state);
  }
  const sug = state.suggestion!;
  const pick = body.decision === "alternative" ? sug.alternatives[body.alternativeIndex ?? 0] : sug.primary;
  if (!pick) throw new MockError("no such option", 400);
  if (pick.lever.param && pick.to !== null) {
    const r = applySetupInternal(state.input.sessionId, { [pick.lever.param]: pick.to }, {
      source: "coach",
      leverId: pick.lever.id,
      symptomId: t.symptomId,
      coachRunId: runId,
    });
    state.appliedChangeId = r.changes[0]?.id;
  } else {
    // Qualitative lever or needs-current-value: log a note-only change so the outcome has something to attach to.
    const s = sessions.get(state.input.sessionId)!;
    const ch: Change = {
      id: nid("change"),
      sessionId: s.id,
      beforeSetupId: s.currentSetupId,
      afterSetupId: s.currentSetupId,
      param: pick.lever.param ?? pick.lever.id,
      from: null,
      to: null,
      leverId: pick.lever.id,
      symptomId: t.symptomId,
      source: "coach",
      coachRunId: runId,
      createdAt: now(),
    };
    changes.push(ch);
    state.appliedChangeId = ch.id;
  }
  state.status = "awaiting-outcome";
  return clone(state);
}

function outcome(runId: string, body: Endpoints["POST /api/coach/:runId/outcome"]["body"]): OutcomeResult {
  const t = turns.get(runId);
  if (!t) throw new MockError("unknown run", 404);
  const ch = changes.find((c) => c.id === t.state.appliedChangeId);
  if (!ch) throw new MockError("nothing was applied", 400);
  ch.outcome = body.outcome;
  ch.outcomeRunId = body.runRef;
  t.state.outcome = body.outcome;
  t.state.status = "done";
  const session = sessions.get(t.state.input.sessionId)!;
  if (body.outcome === "better") return { change: clone(ch), prompt: "save-setup" };
  const next = selectLevers(t.symptomId, session);
  if (body.outcome === "worse") {
    return { change: clone(ch), prompt: "offer-revert", revert: { param: ch.param, to: ch.from }, next };
  }
  return { change: clone(ch), prompt: "next-lever", next };
}

export async function* mockPull(model: string, signal?: AbortSignal): AsyncGenerator<PullEvent> {
  yield { event: "progress", data: { status: "pulling manifest" } };
  const total = 4_300_000_000;
  for (let i = 1; i <= 10; i++) {
    await sleep(200, signal);
    yield { event: "progress", data: { status: "pulling model", completed: (total * i) / 10, total } };
  }
  yield { event: "done", data: { model } };
}

// ---------- kb ----------

function kbSearch(q: string, limit: number): KbChunk[] {
  const tokens = (q.toLowerCase().match(/[a-z0-9]+/g) ?? []).filter((t) => t.length > 2);
  if (!tokens.length) return [];
  return kb.chunks
    .map((c) => {
      const head = `${c.lead} ${c.pageTitle}`.toLowerCase();
      const body = c.text.toLowerCase();
      let score = 0;
      for (const t of tokens) score += (head.split(t).length - 1) * 3 + (body.split(t).length - 1);
      return { c, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((x) => x.c);
}

// ---------- request dispatcher ----------

function bundle(id: string): SessionBundle {
  const s = sessions.get(id);
  if (!s) throw new MockError("session not found", 404);
  const sessionRuns = runs.filter((r) => r.sessionId === id);
  const sessionChanges = changes.filter((c) => c.sessionId === id);
  const ids = new Set<string>([s.currentSetupId]);
  for (const r of sessionRuns) ids.add(r.setupId);
  for (const c of sessionChanges) {
    ids.add(c.beforeSetupId);
    ids.add(c.afterSetupId);
  }
  return {
    session: clone(s),
    runs: clone(sessionRuns),
    changes: clone(sessionChanges),
    setups: [...ids].map((i) => clone(setups.get(i)!)).filter(Boolean),
  };
}

function diffs(a: SetupValues, b: SetupValues) {
  return Object.keys({ ...a, ...b })
    .filter((k) => a[k] !== b[k] && !(a[k] == null && b[k] == null))
    .map((param) => {
      const from = a[param] ?? null;
      const to = b[param] ?? null;
      const direction: "increase" | "decrease" | "changed" =
        typeof from === "number" && typeof to === "number" ? (to > from ? "increase" : "decrease") : "changed";
      return { param, from, to, direction };
    });
}

export async function mockRequest<K extends keyof Endpoints>(
  key: K,
  body?: Endpoints[K]["body"],
  opts?: RequestOptions,
): Promise<Endpoints[K]["res"]> {
  await sleep(25, opts?.signal);
  const p = opts?.params ?? {};
  const q = opts?.query ?? {};
  const b = body as never as Record<string, unknown>;
  const out = (v: unknown) => clone(v) as Endpoints[K]["res"];
  switch (key as string) {
    case "GET /api/health":
      return out({ ok: true, version: "mock" });
    case "GET /api/meta": {
      const meta: MetaResponse = {
        car: paramsFile.car,
        baselineRule: paramsFile.baselineRule,
        conventions: paramsFile.conventions,
        params: paramsFile.params,
        symptoms,
        levers,
        prechecks,
        kbStats: { pages: kb.pages.length, chunks: kb.chunks.length, contentHash: kb.contentHash },
      };
      return out(meta);
    }
    case "GET /api/settings":
      return out(settings);
    case "PUT /api/settings":
      Object.assign(settings, b);
      return out(settings);
    case "POST /api/sessions": {
      const s = makeSession(b as never);
      return out(s);
    }
    case "GET /api/sessions":
      return out([...sessions.values()].sort((a, c) => c.createdAt - a.createdAt));
    case "GET /api/sessions/:id":
      return out(bundle(p.id));
    case "PATCH /api/sessions/:id": {
      const s = sessions.get(p.id);
      if (!s) throw new MockError("session not found", 404);
      if (b.conditions) s.conditions = b.conditions as Session["conditions"];
      if (typeof b.notes === "string") s.notes = b.notes;
      return out(s);
    }
    case "POST /api/sessions/:id/setup": {
      const r = applySetupInternal(p.id, b.values as Record<string, ParamValue>, {
        source: b.source as Change["source"],
        leverId: b.leverId as string | undefined,
        symptomId: b.symptomId as string | undefined,
        coachRunId: b.coachRunId as string | undefined,
      });
      return out(r);
    }
    case "POST /api/sessions/:id/runs": {
      const s = sessions.get(p.id);
      if (!s) throw new MockError("session not found", 404);
      const seq = runs.filter((r) => r.sessionId === p.id).length + 1;
      const run: Run = { ...(b as object), id: nid("run"), sessionId: p.id, seq, setupId: s.currentSetupId, createdAt: now() } as Run;
      runs.push(run);
      return out(run);
    }
    case "PATCH /api/changes/:id": {
      const c = changes.find((x) => x.id === p.id);
      if (!c) throw new MockError("change not found", 404);
      c.outcome = b.outcome as Change["outcome"];
      c.outcomeRunId = b.outcomeRunId as string | undefined;
      return out(c);
    }
    case "GET /api/saved":
      return out(saved);
    case "POST /api/saved": {
      const s: SavedSetup = { ...(b as object), id: nid("saved"), createdAt: now() } as SavedSetup;
      saved.push(s);
      return out(s);
    }
    case "DELETE /api/saved/:id": {
      const i = saved.findIndex((s) => s.id === p.id);
      if (i >= 0) saved.splice(i, 1);
      return out({ ok: true });
    }
    case "GET /api/setups/:id": {
      const su = setups.get(p.id);
      if (!su) throw new MockError("setup not found", 404);
      return out(su);
    }
    case "GET /api/export":
      return out({
        schemaVersion: 1,
        exportedAt: now(),
        tables: {
          settings: Object.entries(settings).map(([k, value]) => ({ key: k, value })),
          setups: [...setups.values()],
          sessions: [...sessions.values()],
          runs,
          changes,
          savedSetups: saved,
        },
      });
    case "POST /api/import": {
      const t = (b as { tables: Record<string, unknown[]> }).tables;
      resetState(false);
      for (const s of (t.setups ?? []) as Setup[]) setups.set(s.id, s);
      for (const s of (t.sessions ?? []) as Session[]) sessions.set(s.id, s);
      runs.push(...((t.runs ?? []) as Run[]));
      changes.push(...((t.changes ?? []) as Change[]));
      saved.push(...((t.savedSetups ?? []) as SavedSetup[]));
      return out({
        ok: true,
        counts: {
          settings: t.settings?.length ?? 0,
          setups: setups.size,
          sessions: sessions.size,
          runs: runs.length,
          changes: changes.length,
          savedSetups: saved.length,
        },
      });
    }
    case "POST /api/reset":
      resetState(false);
      return out({ ok: true });
    case "GET /api/kb/search":
      return out(kbSearch(String(q.q ?? ""), Number(q.limit ?? 3)));
    case "GET /api/kb/chunk/:id": {
      const c = kb.chunks.find((x) => x.id === p.id);
      if (!c) throw new MockError("chunk not found", 404);
      return out(c);
    }
    case "POST /api/coach/:runId/decide":
      return out(decide(p.runId, b as never));
    case "POST /api/coach/:runId/outcome":
      return out(outcome(p.runId, b as never));
    case "GET /api/llm/status":
      return out({ reachable: true, url: settings.ollamaUrl, model: settings.model, present: true, loaded: true, numCtx: settings.numCtx, lastLatencyMs: 1840 });
    case "POST /api/llm/warmup":
      return out({ ms: 420 });
    case "GET /api/analysis/similar": {
      const s = sessions.get(String(q.sessionId));
      return out(
        saved.map((sv) => ({
          saved: sv,
          score: s && sv.conditions.trackName === s.conditions.trackName ? 92 : 40,
          reasons: s && sv.conditions.trackName === s.conditions.trackName ? ["same track", "same surface"] : ["different track"],
          surfaceMismatch: !!s && sv.conditions.surface !== s.conditions.surface,
          diffVsCurrent: s ? diffs(setups.get(s.currentSetupId)!.values, setups.get(sv.setupId)?.values ?? {}) : [],
        })),
      );
    }
    case "GET /api/analysis/compare": {
      const ra = runs.find((r) => r.id === q.runA);
      const rb = runs.find((r) => r.id === q.runB);
      if (!ra || !rb) throw new MockError("run not found", 404);
      const d = diffs(setups.get(ra.setupId)!.values, setups.get(rb.setupId)!.values);
      return out({
        runA: ra.id,
        runB: rb.id,
        setupDiffs: d.map((x) => ({ ...x, citations: [] as string[] })),
        conditionDiffs: [],
        lapStats: { status: "insufficient-data", text: "Mock comparison: no lap statistics computed.", citations: [] as string[] },
        confounded: d.length > 1,
      });
    }
    case "GET /api/analysis/history": {
      const rows = new Map<string, { param: string; direction: string; tries: number; better: number; same: number; worse: number }>();
      for (const c of changes) {
        if (!c.outcome) continue;
        const dir = typeof c.from === "number" && typeof c.to === "number" ? (c.to > c.from ? "increase" : "decrease") : "changed";
        const k = `${c.param}:${dir}`;
        const r = rows.get(k) ?? { param: c.param, direction: dir, tries: 0, better: 0, same: 0, worse: 0 };
        r.tries++;
        r[c.outcome]++;
        rows.set(k, r);
      }
      return out([...rows.values()]);
    }
    case "POST /api/speak":
      return out({ ok: true });
    default:
      throw new MockError(`mock: no handler for ${key}`, 501);
  }
}
