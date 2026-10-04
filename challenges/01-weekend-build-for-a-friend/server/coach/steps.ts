// Coach steps shared by the Mastra and plain engines (T3; plan 2.5, 4.3).
// Only two steps may call the model: classify (skipped for chips and keyword refusals) and explain
// (skipped when "Coach phrasing" is off). Everything else is plain code over data/*.json and the vault.
// Every backend (lever engine, keyword classifier, vault repo, Ollama) comes through `CoachDeps`, so tests
// and the self-test can inject fakes; the defaults are the real T1/T2 modules.
import { z } from "zod";
import { defaultSettings } from "../config";
import * as S from "../../src/shared/schemas";
import type {
  Change,
  Classification,
  CoachTurnInput,
  Decision,
  Grip,
  KbChunk,
  LeverRow,
  LeverSuggestion,
  Outcome,
  OutcomeResult,
  Phase,
  ParamDef,
  ParamValue,
  PrecheckDef,
  Refusal,
  Settings,
  SetupValues,
  Suggestion,
  SymptomDef,
  TurnState,
} from "../../src/shared/types";
import type { ApplySetupResponse } from "../../src/shared/api";
import type { EmitFn } from "./engine";
import { ollamaFor, type OllamaClient } from "../llm/ollama";
import {
  CLASSIFIER_OPTIONS,
  CLASSIFIER_SCHEMA,
  CLASSIFIER_SYSTEM,
  EXPLAINER_OPTIONS,
  EXPLAINER_SYSTEM,
  explainerUser,
  type ExplainerCard,
} from "./prompts";
import { loadLevers, loadParams, loadPrechecks, loadSymptoms } from "../engine/data";
import { keywordClassify, refusalFor } from "../engine/keyword";
import { selectLevers, type SelectLeversArgs } from "../engine/levers";
import { getChunk } from "../kb/search";
import * as repo from "../vault/repo";

// ---------- dependencies ----------

export interface SessionContext {
  grip: Grip;
  setup: SetupValues;
  /** Changes in this session, oldest first. */
  history: Change[];
}

export interface CoachDeps {
  settings(): Promise<Settings>;
  /** Null disables the model (tests, or no client configured). */
  llm(s: Settings): OllamaClient | null;
  symptoms(): SymptomDef[];
  prechecks(): PrecheckDef[];
  levers(): LeverRow[];
  params(): ParamDef[];
  getChunk(id: string): KbChunk | undefined;
  keywordClassify(utterance: string, symptoms: SymptomDef[]): Classification | null;
  refusalFor(utterance: string): Refusal | null;
  selectLevers(args: SelectLeversArgs): Suggestion;
  sessionContext(sessionId: string): Promise<SessionContext>;
  applySetupChanges: typeof repo.applySetupChanges;
  setChangeOutcome: typeof repo.setChangeOutcome;
}

export const realDeps: CoachDeps = {
  async settings() {
    try {
      return await repo.getSettings();
    } catch {
      return defaultSettings; // vault not open (scripts) -> env defaults
    }
  },
  llm: (s) => ollamaFor(s),
  symptoms: loadSymptoms,
  prechecks: loadPrechecks,
  levers: loadLevers,
  params: () => loadParams().params,
  getChunk,
  keywordClassify,
  refusalFor,
  selectLevers,
  async sessionContext(sessionId) {
    const b = await repo.getSessionBundle(sessionId);
    const setup = b.setups.find((x) => x.id === b.session.currentSetupId);
    if (!setup) throw new CoachError(500, `current setup of session ${sessionId} not found`, "pickLever");
    return { grip: b.session.conditions.grip, setup: setup.values, history: [...b.changes].sort((a, z) => a.createdAt - z.createdAt) };
  },
  applySetupChanges: (...a) => repo.applySetupChanges(...a),
  setChangeOutcome: (...a) => repo.setChangeOutcome(...a),
};

let current: CoachDeps = realDeps;
/** Overrides some or all backends (tests, self-test); returns the previous bundle. */
export function setCoachDeps(patch: Partial<CoachDeps>): CoachDeps {
  const prev = current;
  current = { ...current, ...patch };
  return prev;
}
export const getCoachDeps = (): CoachDeps => current;

// ---------- state ----------

/** Error with an HTTP status and a stage, mapped by the routes to `{ error, stage }`. */
export class CoachError extends Error {
  constructor(
    readonly status: 400 | 404 | 409 | 500 | 502 | 503,
    message: string,
    readonly stage: string,
  ) {
    super(message);
    this.name = "CoachError";
  }
}

/** Internal workflow state: the contract TurnState plus a halt marker and the outcome result. */
export const CoachState = S.TurnState.extend({
  halted: z.object({ stage: z.string(), message: z.string() }).optional(),
  outcomeResult: S.OutcomeResult.optional(),
});
export type CoachStateT = z.infer<typeof CoachState>;

/** Strips internal fields so routes return exactly the contract shape. */
export function publicState(s: CoachStateT): TurnState {
  const { halted: _h, outcomeResult: _o, ...rest } = s;
  return rest;
}

export const initialState = (runId: string, input: CoachTurnInput): CoachStateT => ({ runId, input, prechecks: [], status: "awaiting-decision" });

/** True when later steps must do nothing (refusal, halt, or no classification). */
const stopped = (s: CoachStateT) => !!s.refusal || !!s.halted || !s.classification;

export const CLASSIFY_TIMEOUT_MS = 45_000;
export const EXPLAIN_TIMEOUT_MS = 90_000;

const OUT_OF_SCOPE: Refusal = {
  reason: "out-of-scope",
  message: "That is not something my setup notes cover, so I won't guess. Tell me how the car feels in a corner, or tap a symptom.",
  citations: [],
};
const PRECHECK_ONLY_REASON =
  "This one is not a setup change: walk the checks above first (tweak, left/right weight, steering throw, tyre rotation).";

// ---------- classify ----------

async function llmClassify(utterance: string, deps: CoachDeps): Promise<Classification | null> {
  const s = await deps.settings();
  const llm = deps.llm(s);
  if (!llm) return null;
  const r = await llm.chat({
    messages: [
      { role: "system", content: CLASSIFIER_SYSTEM },
      { role: "user", content: utterance.trim().slice(0, CLASSIFIER_OPTIONS.maxUserChars) },
    ],
    format: CLASSIFIER_SCHEMA,
    temperature: CLASSIFIER_OPTIONS.temperature,
    numPredict: CLASSIFIER_OPTIONS.numPredict,
    signal: AbortSignal.timeout(CLASSIFY_TIMEOUT_MS),
  });
  const j = JSON.parse(r.text) as { symptom_id?: string; alt_id?: string; phase?: string; confidence?: number };
  const ids = new Set(deps.symptoms().map((x) => x.id));
  if (!j.symptom_id || !ids.has(j.symptom_id)) return null;
  const phase = S.Phase.safeParse(j.phase);
  return {
    symptomId: j.symptom_id,
    altId: j.alt_id && ids.has(j.alt_id) && j.alt_id !== j.symptom_id ? j.alt_id : "none",
    phase: phase.success ? phase.data : "none",
    confidence: Math.max(0, Math.min(1, Number(j.confidence) || 0)),
    source: "llm",
    ms: r.ms,
  };
}

/** Symptom phases are fixed per id; the driver's explicit phase wins, then the symptom's, then the model's. */
function settlePhase(c: Classification, input: CoachTurnInput, deps: CoachDeps): Classification {
  const sym = deps.symptoms().find((x) => x.id === c.symptomId);
  const phase = input.phase ?? (sym && sym.phase !== "none" ? sym.phase : c.phase);
  return { ...c, phase };
}

/**
 * Chip passthrough, else keyword refusal check, else LLM (keyword fallback when Ollama is down or answers
 * garbage). Emits `classified` (and `refusal`). Returns neither field when nothing matched; an `error`
 * event has then been sent.
 */
export async function classify(
  input: CoachTurnInput,
  emit: EmitFn,
  deps: CoachDeps = current,
): Promise<{ classification?: Classification; refusal?: Refusal }> {
  let c: Classification | null = null;
  if (input.symptomId) {
    const sym = deps.symptoms().find((x) => x.id === input.symptomId);
    if (!sym) {
      await emit({ event: "error", data: { message: `unknown symptom id "${input.symptomId}"`, stage: "classify" } });
      return {};
    }
    c = { symptomId: sym.id, altId: "none", phase: input.phase ?? sym.phase, confidence: 1, source: "chip", ms: 0 };
  } else {
    const utterance = input.utterance ?? "";
    const t0 = performance.now();
    const kwRefusal = deps.refusalFor(utterance);
    if (kwRefusal) {
      const oc: Classification = { symptomId: "out-of-scope", altId: "none", phase: "none", confidence: 1, source: "keyword", ms: Math.round(performance.now() - t0) };
      await emit({ event: "classified", data: oc });
      await emit({ event: "refusal", data: kwRefusal });
      return { classification: oc, refusal: kwRefusal };
    }
    try {
      c = await llmClassify(utterance, deps);
    } catch (e) {
      console.warn(`[coach] classify LLM failed, using keywords: ${(e as Error).message}`);
    }
    if (!c) {
      const kw = deps.keywordClassify(utterance, deps.symptoms());
      if (kw) c = { ...kw, ms: Math.round(performance.now() - t0) };
    }
    if (!c) {
      await emit({
        event: "error",
        data: { message: "I couldn't reach the model or match your words to a symptom. Tap the symptom chip that fits best.", stage: "classify" },
      });
      return {};
    }
  }
  c = settlePhase(c, input, deps);
  await emit({ event: "classified", data: c });
  if (c.symptomId === "out-of-scope") {
    await emit({ event: "refusal", data: OUT_OF_SCOPE });
    return { classification: c, refusal: OUT_OF_SCOPE };
  }
  return { classification: c };
}

// ---------- precheck ----------

export function precheck(symptomId: string, deps: CoachDeps = current): PrecheckDef[] {
  const sym = deps.symptoms().find((x) => x.id === symptomId);
  if (!sym) return [];
  const all = new Map(deps.prechecks().map((p) => [p.id, p]));
  return sym.prechecks.map((id) => all.get(id)).filter((p): p is PrecheckDef => !!p);
}

// ---------- pickLever ----------

async function suggestFor(symptomId: string, phase: Phase, sessionId: string, deps: CoachDeps): Promise<Suggestion> {
  const sym = deps.symptoms().find((x) => x.id === symptomId);
  if (sym?.precheckOnly) return { primary: null, alternatives: [], skipped: [], noLeverReason: PRECHECK_ONLY_REASON };
  const [ctx, settings] = await Promise.all([deps.sessionContext(sessionId), deps.settings()]);
  return deps.selectLevers({
    symptomId,
    phase,
    grip: ctx.grip,
    setup: ctx.setup,
    params: deps.params(),
    levers: deps.levers(),
    history: ctx.history,
    reviewedOnly: settings.reviewedOnly,
  });
}

/** Calls the deterministic lever engine with today's grip, the current setup and this session's history. */
export async function pickLever(state: TurnState, emit: EmitFn, deps: CoachDeps = current): Promise<Suggestion> {
  const c = state.classification;
  if (!c) throw new CoachError(500, "pickLever before classify", "pickLever");
  const sug = await suggestFor(c.symptomId, c.phase, state.input.sessionId, deps);
  await emit({ event: "suggestion", data: sug });
  return sug;
}

// ---------- explain ----------

const NUMBER_WORDS: Record<string, number> = {
  two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12,
  twenty: 20, thirty: 30, forty: 40, fifty: 50, hundred: 100, thousand: 1000,
};

const DIGIT_WORDS: Record<string, number> = { zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9 };
const SPOKEN_DECIMAL = /\b(zero|one|two|three|four|five|six|seven|eight|nine|\d+) point (zero|one|two|three|four|five|six|seven|eight|nine|\d+)\b/gi;
const digitOf = (w: string) => (/^\d+$/.test(w) ? w : String(DIGIT_WORDS[w.toLowerCase()]));

/**
 * Every number in a text: digits (thousand separators folded), spoken decimals ("five point two" = 5.2,
 * seen from Gemma on 2026-10-04) and number words from two up. A bare "one" is ignored (it is usually a pronoun).
 */
export function numbersIn(text: string): number[] {
  const t = text.replace(/(\d),(?=\d{3}\b)/g, "$1").replace(SPOKEN_DECIMAL, (_m, a: string, b: string) => `${digitOf(a)}.${digitOf(b)}`);
  const out = (t.match(/\d+(?:\.\d+)?/g) ?? []).map(Number);
  for (const w of t.toLowerCase().match(/[a-z]+/g) ?? []) if (w in NUMBER_WORDS) out.push(NUMBER_WORDS[w]!);
  return out;
}

const unitOf = (s: LeverSuggestion) => s.lever.unit ?? "";

/** The CARD texts whose numbers the model may repeat. */
function cardTexts(s: LeverSuggestion, extra: string[] = []): string[] {
  const l = s.lever;
  return [String(s.from ?? ""), String(s.to ?? ""), l.action, l.effect, l.tradeOff, l.verify, ...extra];
}

/** True when every number in `text` appears in the card (from, to, action, effect, trade-off, verify, plus extra card strings). */
export function numberGuard(text: string, s: LeverSuggestion, extra: string[] = []): boolean {
  const allowed = new Set(cardTexts(s, extra).flatMap(numbersIn));
  return numbersIn(text).every((n) => allowed.has(n));
}

const sentence = (x: string) => {
  const t = x.trim();
  return !t ? "" : /[.!?]$/.test(t) ? t : `${t}.`;
};

/** "{action}: {from} to {to} {unit}. {effect} Trade-off: {tradeOff} Check: {verify}" (with honest variants for missing values). */
export function templateExplanation(s: LeverSuggestion): string {
  const l = s.lever;
  let head: string;
  if (s.from !== null && s.to !== null) head = `${l.action.replace(/[.\s]+$/, "")}: ${s.from} to ${s.to}${unitOf(s) ? ` ${unitOf(s)}` : ""}.`;
  else if (s.needsCurrentValue)
    head = `${l.action.replace(/[.\s]+$/, "")}: one step ${l.direction === "decrease" ? "down" : "up"}; enter your current value in Setup for the exact number.`;
  else head = sentence(l.action);
  return [head, sentence(l.effect), `Trade-off: ${sentence(l.tradeOff)}`, `Check: ${sentence(l.verify)}`].filter(Boolean).join(" ");
}

export interface ExplainContext {
  symptomLabel?: string;
  /** Plain-language line about levers the engine skipped (no model-made numbers). */
  skipped?: string;
}

/** LLM phrasing (streamed as `token` events), number guard, template fallback. Emits `explained`. */
export async function explain(
  s: LeverSuggestion,
  emit: EmitFn,
  ctx: ExplainContext = {},
  deps: CoachDeps = current,
): Promise<{ text: string; source: "llm" | "template"; ms?: number }> {
  const t0 = performance.now();
  const settings = await deps.settings();
  const llm = settings.llmPhrasing ? deps.llm(settings) : null;
  let result: { text: string; source: "llm" | "template"; ms?: number } | null = null;
  if (llm) {
    const card: ExplainerCard = {
      symptom: ctx.symptomLabel ?? s.lever.symptomId,
      action: s.lever.action,
      from: s.from,
      to: s.to,
      unit: unitOf(s),
      effect: s.lever.effect,
      tradeOff: s.lever.tradeOff,
      verify: s.lever.verify,
      ...(ctx.skipped ? { skipped: ctx.skipped } : {}),
    };
    const notes = s.lever.citations
      .slice(0, EXPLAINER_OPTIONS.notesChunks)
      .map((id) => deps.getChunk(id)?.text)
      .filter((t): t is string => !!t);
    try {
      const gen = llm.chatStream({
        messages: [
          { role: "system", content: EXPLAINER_SYSTEM },
          { role: "user", content: explainerUser(card, notes) },
        ],
        temperature: EXPLAINER_OPTIONS.temperature,
        numPredict: EXPLAINER_OPTIONS.numPredict,
        signal: AbortSignal.timeout(EXPLAIN_TIMEOUT_MS),
      });
      let text = "";
      for (;;) {
        const n = await gen.next();
        if (n.done) break;
        text += n.value;
        await emit({ event: "token", data: { text: n.value } });
      }
      text = text.trim();
      const extra = [card.symptom, card.skipped ?? ""];
      if (text && numberGuard(text, s, extra)) result = { text, source: "llm", ms: Math.round(performance.now() - t0) };
      else console.warn(`[coach] number guard rejected explanation for ${s.lever.id} (numbers ${JSON.stringify(numbersIn(text))}): ${JSON.stringify(text)}; using template`);
    } catch (e) {
      console.warn(`[coach] explain LLM failed, using template: ${(e as Error).message}`);
    }
  }
  result ??= { text: templateExplanation(s), source: "template", ms: Math.round(performance.now() - t0) };
  await emit({ event: "explained", data: result });
  return result;
}

// ---------- workflow-level steps (shared by both engines; each no-ops once the turn has stopped) ----------

export async function stepClassify(st: CoachStateT, emit: EmitFn, deps: CoachDeps = current): Promise<CoachStateT> {
  const r = await classify(st.input, emit, deps);
  if (!r.classification) return { ...st, halted: { stage: "classify", message: "no classification" }, status: "done" };
  return { ...st, ...r, status: r.refusal ? "done" : st.status };
}

export async function stepPrecheck(st: CoachStateT, emit: EmitFn, deps: CoachDeps = current): Promise<CoachStateT> {
  if (stopped(st)) return st;
  const prechecks = precheck(st.classification!.symptomId, deps);
  await emit({ event: "precheck", data: prechecks });
  return { ...st, prechecks };
}

export async function stepPickLever(st: CoachStateT, emit: EmitFn, deps: CoachDeps = current): Promise<CoachStateT> {
  if (stopped(st)) return st;
  try {
    const suggestion = await pickLever(publicState(st), emit, deps);
    return { ...st, suggestion };
  } catch (e) {
    const message = `could not pick a change: ${(e as Error).message}`;
    await emit({ event: "error", data: { message, stage: "pickLever" } });
    return { ...st, halted: { stage: "pickLever", message }, status: "done" };
  }
}

function skippedLine(sug: Suggestion, deps: CoachDeps): string | undefined {
  const byId = new Map(deps.levers().map((l) => [l.id, l]));
  const why: Record<string, string> = { "at-limit": "already at the limit in my notes", "tried-worse": "made it worse earlier today", "tried-same": "made no difference earlier today" };
  const parts = sug.skipped
    .filter((k) => k.reason in why)
    .slice(0, 2)
    .map((k) => `${byId.get(k.leverId)?.action ?? k.leverId}: ${why[k.reason]}`);
  return parts.length ? `Skipped ${parts.join("; ")}.` : undefined;
}

export async function stepExplain(st: CoachStateT, emit: EmitFn, deps: CoachDeps = current): Promise<CoachStateT> {
  if (stopped(st) || !st.suggestion) return st;
  const primary = st.suggestion.primary;
  if (!primary) {
    const explanation = { text: st.suggestion.noLeverReason ?? "No setup change to suggest for this.", source: "template" as const, ms: 0 };
    await emit({ event: "explained", data: explanation });
    return { ...st, explanation, status: "done" };
  }
  const label = deps.symptoms().find((x) => x.id === st.classification!.symptomId)?.label;
  const explanation = await explain(primary, emit, { symptomLabel: label, skipped: skippedLine(st.suggestion, deps) }, deps);
  return { ...st, explanation };
}

/** The suggestion a decision targets; throws a 409 CoachError when it cannot be applied. */
export function targetOf(st: CoachStateT, d: { decision: Decision; alternativeIndex?: number }): LeverSuggestion | null {
  if (st.status !== "awaiting-decision" || stopped(st) || !st.suggestion?.primary)
    throw new CoachError(409, `run ${st.runId} is not waiting for a decision (status ${st.status})`, "decide");
  if (d.decision === "skip") return null;
  const t = d.decision === "apply" ? st.suggestion.primary : st.suggestion.alternatives[d.alternativeIndex ?? 0];
  if (!t) throw new CoachError(400, `no alternative at index ${d.alternativeIndex ?? 0}`, "decide");
  if (!t.lever.param || t.to === null)
    throw new CoachError(
      409,
      t.needsCurrentValue
        ? "Enter your current value for this setting in Setup first, then ask again for the exact number."
        : "This change has no single setup value; make it by hand and log it in Setup.",
      "decide",
    );
  return t;
}

/** Writes the chosen change through the vault repo (one Change row) or ends the turn on skip. */
export async function stepApply(st: CoachStateT, d: { decision: Decision; alternativeIndex?: number }, deps: CoachDeps = current): Promise<CoachStateT> {
  const t = targetOf(st, d);
  if (!t) return { ...st, decision: "skip", status: "done" };
  const res: ApplySetupResponse = await deps.applySetupChanges(
    st.input.sessionId,
    { [t.lever.param!]: t.to as ParamValue },
    { source: "coach", leverId: t.lever.id, symptomId: st.classification!.symptomId, coachRunId: st.runId },
  );
  const change = res.changes.find((c) => c.param === t.lever.param);
  if (!change) throw new CoachError(409, `${t.lever.param} is already ${String(t.to)}; nothing to apply`, "apply");
  return { ...st, decision: d.decision, appliedChangeId: change.id, status: "awaiting-outcome" };
}

export function assertAwaitingOutcome(st: CoachStateT): void {
  if (st.status !== "awaiting-outcome" || !st.appliedChangeId)
    throw new CoachError(409, `run ${st.runId} is not waiting for an outcome (status ${st.status})`, "outcome");
}

/** Logs the outcome on the Change and computes the next prompt (save / next lever / offer revert + next). */
export async function stepLogOutcome(st: CoachStateT, o: { outcome: Outcome; runRef?: string }, deps: CoachDeps = current): Promise<CoachStateT> {
  assertAwaitingOutcome(st);
  const change = await deps.setChangeOutcome(st.appliedChangeId!, o.outcome, o.runRef);
  let result: OutcomeResult;
  if (o.outcome === "better") result = { change, prompt: "save-setup" };
  else {
    const c = st.classification!;
    const next = await suggestFor(c.symptomId, c.phase, st.input.sessionId, deps);
    result =
      o.outcome === "worse"
        ? { change, prompt: "offer-revert", revert: { param: change.param, to: change.from }, next }
        : { change, prompt: "next-lever", next };
  }
  return { ...st, outcome: o.outcome, outcomeResult: result, status: "done" };
}
