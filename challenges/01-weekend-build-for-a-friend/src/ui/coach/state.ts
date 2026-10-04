// Coach turn state machine (T4a). Module-level signals so the turn survives switching screens.
// Event order from the server is fixed (src/shared/events.ts):
//   classified, then refusal (stop) or precheck, suggestion, token*, explained, suspended.
// The suggestion card is shown as soon as `suggestion` arrives. The runId comes with `classified`/`suggestion` (T7),
// so Apply unlocks at the card; the server's decide waits for the turn to suspend before resuming it.
import { signal } from "@preact/signals";
import {
  applySetup,
  coachDecide,
  coachOutcome,
  coachTurn,
  getSession,
  patchSession,
} from "../../api/client";
import type {
  Classification,
  CoachTurnInput,
  Explanation,
  LeverSuggestion,
  Outcome,
  OutcomeResult,
  PrecheckDef,
  Refusal,
  Suggestion,
} from "../../shared/types";
import { openStartSession, refreshSession } from "../app/bootstrap";
import { meta, session, settings } from "../store";
import { getSpeechInput, getSpeechOutput, voiceModulePresent } from "./voice";

export type TurnStage = "classify" | "pick" | "phrase" | "done";
export type TurnStatus =
  | "thinking"
  | "awaiting-decision"
  | "awaiting-outcome"
  | "done"
  | "refused"
  | "error"
  | "cancelled";

export interface TurnView {
  localId: number;
  input: CoachTurnInput;
  heard: string;
  status: TurnStatus;
  stage: TurnStage;
  runId?: string;
  classification?: Classification;
  refusal?: Refusal;
  prechecks: PrecheckDef[];
  suggestion?: Suggestion;
  coachText: string;
  explanation?: Explanation;
  /** performance.now() marks for the live step timers. */
  t: { start: number; classified?: number; suggestion?: number; explained?: number };
  error?: string;
  applied?: LeverSuggestion;
  skipped?: boolean;
  outcomeChoice?: Outcome;
  outcomeResult?: OutcomeResult;
  reverted?: boolean;
}

export const turn = signal<TurnView | null>(null);
/** 0 = the primary suggestion, n = suggestion.alternatives[n - 1]. "Another option" cycles this. */
export const optionIndex = signal(0);
export const precheckMarks = signal<Record<string, "ok" | "problem">>({});
export const prechecksSkipped = signal(false);
export const showAnyway = signal(false);
/** A decide/outcome/revert call is in flight. */
export const busy = signal(false);
export const actionError = signal<string | null>(null);

export const listening = signal(false);
export const interim = signal("");
export const voiceHint = signal<string | null>(null);

let ctrl: AbortController | null = null;
let localCounter = 0;

function patch(p: Partial<TurnView>): void {
  if (turn.value) turn.value = { ...turn.value, ...p };
}

export function symptomLabel(id: string | undefined): string {
  if (!id) return "";
  return meta.value?.symptoms.find((s) => s.id === id)?.label ?? FALLBACK_CHIPS.find((c) => c.id === id)?.label ?? id;
}

/** Short labels for the quick chips (plan 5.1); ids are the stable symptom ids from data/symptoms.json. */
export const FALLBACK_CHIPS: { id: string; label: string }[] = [
  { id: "entry-understeer", label: "Push in" },
  { id: "mid-understeer", label: "Push mid" },
  { id: "exit-understeer", label: "Push on power" },
  { id: "entry-oversteer", label: "Loose in" },
  { id: "exit-oversteer", label: "Loose on power" },
  { id: "traction-roll", label: "Traction roll" },
  { id: "bumpy-track", label: "Bumpy" },
  { id: "nervous-twitchy", label: "Twitchy" },
  { id: "low-grip", label: "No grip" },
  { id: "fade-late-run", label: "Fades late" },
  { id: "left-right-difference", label: "Left vs right" },
];

export function resetTurn(): void {
  ctrl?.abort();
  ctrl = null;
  getSpeechOutput(settings.value)?.cancel();
  turn.value = null;
  optionIndex.value = 0;
  precheckMarks.value = {};
  prechecksSkipped.value = false;
  showAnyway.value = false;
  busy.value = false;
  actionError.value = null;
}

export async function startTurn(
  input: Omit<CoachTurnInput, "sessionId">,
  heard: string,
): Promise<void> {
  const s = session.value;
  if (!s) {
    openStartSession();
    return;
  }
  resetTurn();
  const c = new AbortController();
  ctrl = c;
  const full = { ...input, sessionId: s.id } as CoachTurnInput;
  turn.value = {
    localId: ++localCounter,
    input: full,
    heard,
    status: "thinking",
    stage: "classify",
    prechecks: [],
    coachText: "",
    t: { start: performance.now() },
  };
  const myId = turn.value.localId;
  const live = () => turn.value?.localId === myId && !c.signal.aborted;
  try {
    for await (const ev of coachTurn(full, c.signal)) {
      if (!live()) return;
      const nowMs = performance.now();
      switch (ev.event) {
        case "classified": {
          const { runId, ...classification } = ev.data;
          patch({ classification, runId: runId ?? turn.value!.runId, stage: "pick", t: { ...turn.value!.t, classified: nowMs } });
          break;
        }
        case "refusal":
          patch({ refusal: ev.data, status: "refused", stage: "done" });
          break;
        case "precheck":
          patch({ prechecks: ev.data });
          break;
        case "suggestion": {
          const { runId, ...suggestion } = ev.data;
          patch({ suggestion, runId: runId ?? turn.value!.runId, stage: "phrase", t: { ...turn.value!.t, suggestion: nowMs } });
          break;
        }
        case "token":
          patch({ coachText: turn.value!.coachText + ev.data.text });
          break;
        case "explained":
          patch({ explanation: ev.data, coachText: ev.data.text, t: { ...turn.value!.t, explained: nowMs } });
          void getSpeechOutput(settings.value)?.speak(ev.data.text).catch(() => {});
          break;
        case "suspended": {
          const cur = turn.value!;
          // The driver may have tapped Apply/Skip before the turn suspended: keep that status.
          const decided = !!cur.applied || !!cur.skipped || cur.status === "awaiting-outcome" || cur.status === "done";
          patch({
            runId: ev.data.runId,
            stage: "done",
            status: decided
              ? cur.status
              : ev.data.status === "awaiting-outcome" ? "awaiting-outcome" : ev.data.status === "done" ? "done" : "awaiting-decision",
            t: { ...turn.value!.t, explained: turn.value!.t.explained ?? nowMs },
          });
          break;
        }
        case "error":
          patch({ status: "error", stage: "done", error: `${ev.data.message}${ev.data.stage ? ` (${ev.data.stage})` : ""}` });
          break;
      }
    }
    // Stream closed without suspended/refusal/error.
    if (live() && turn.value!.status === "thinking") {
      patch({
        status: "error",
        stage: "done",
        error: "The coach stream ended early. The card above may still be useful, but Apply is unavailable for this run.",
      });
    }
  } catch (e) {
    if (c.signal.aborted || (e as Error).name === "AbortError") return;
    if (live()) patch({ status: "error", stage: "done", error: (e as Error).message });
  }
}

/** Cancel while thinking. Before the card exists this clears the turn; after it, the card stays readable. */
export function cancelTurn(): void {
  const t = turn.value;
  if (!t || t.status !== "thinking") return;
  ctrl?.abort();
  getSpeechOutput(settings.value)?.cancel();
  if (t.suggestion) {
    patch({ status: "cancelled", stage: "done" });
  } else {
    turn.value = null;
  }
}

export function currentOption(t: TurnView | null = turn.value): LeverSuggestion | null {
  const sug = t?.suggestion;
  if (!sug) return null;
  return optionIndex.value === 0 ? sug.primary : (sug.alternatives[optionIndex.value - 1] ?? null);
}

export function anotherOption(): void {
  const sug = turn.value?.suggestion;
  if (!sug) return;
  const n = 1 + sug.alternatives.length;
  optionIndex.value = (optionIndex.value + 1) % n;
}

async function guarded(fn: () => Promise<void>): Promise<void> {
  busy.value = true;
  actionError.value = null;
  try {
    await fn();
  } catch (e) {
    actionError.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}

export function applyOption(): Promise<void> {
  return guarded(async () => {
    const t = turn.value;
    const pick = currentOption(t);
    if (!t?.runId || !pick) return;
    const i = optionIndex.value;
    const st = await coachDecide(t.runId, i === 0 ? { decision: "apply" } : { decision: "alternative", alternativeIndex: i - 1 });
    getSpeechOutput(settings.value)?.cancel();
    patch({ applied: pick, status: st.status === "done" ? "done" : "awaiting-outcome" });
    await refreshSession();
  });
}

export function skipSuggestion(): Promise<void> {
  return guarded(async () => {
    const t = turn.value;
    if (!t?.runId) return;
    await coachDecide(t.runId, { decision: "skip" });
    getSpeechOutput(settings.value)?.cancel();
    patch({ skipped: true, status: "done" });
  });
}

export function sendOutcome(o: Outcome): Promise<void> {
  return guarded(async () => {
    const t = turn.value;
    if (!t?.runId) return;
    // Tie the outcome to the latest run logged after this turn started, when there is one (T7).
    let runRef: string | undefined;
    const sid = session.value?.id;
    if (sid) {
      const b = await getSession(sid).catch(() => null);
      const startedAt = Date.now() - (performance.now() - t.t.start);
      runRef = b?.runs.filter((r) => r.createdAt >= startedAt).sort((x, y) => y.seq - x.seq)[0]?.id;
    }
    const res = await coachOutcome(t.runId, runRef ? { outcome: o, runRef } : { outcome: o });
    patch({ outcomeChoice: o, outcomeResult: res, status: "done" });
    await refreshSession();
  });
}

export function revertChange(): Promise<void> {
  return guarded(async () => {
    const t = turn.value;
    const s = session.value;
    const rev = t?.outcomeResult?.revert;
    if (!t || !s || !rev) return;
    await applySetup(s.id, { values: { [rev.param]: rev.to }, source: "revert", coachRunId: t.runId });
    patch({ reverted: true });
    await refreshSession();
  });
}

export function markPrecheck(id: string, mark: "ok" | "problem"): void {
  const prev = precheckMarks.value[id];
  precheckMarks.value = { ...precheckMarks.value, [id]: mark };
  const s = session.value;
  const def = turn.value?.prechecks.find((p) => p.id === id);
  if (mark === "problem" && prev !== "problem" && s && def) {
    const line = `${new Date().toISOString().slice(0, 10)} pre-check problem: ${def.label}. Fix that first, then run again.`;
    patchSession(s.id, { notes: s.notes ? `${s.notes}\n${line}` : line })
      .then(() => refreshSession())
      .catch(() => {});
  }
}

export function problemCheck(): PrecheckDef | undefined {
  const t = turn.value;
  if (!t || prechecksSkipped.value) return undefined;
  return t.prechecks.find((p) => precheckMarks.value[p.id] === "problem");
}

// ---------- voice ----------

export async function startListening(): Promise<void> {
  if (listening.value) return;
  const s = settings.value;
  if (s?.voiceIn === "off") {
    voiceHint.value = "Voice input is off in Settings. Type or tap a chip.";
    return;
  }
  const input = getSpeechInput(s);
  if (!input) {
    voiceHint.value = voiceModulePresent
      ? "Voice input is not available. Type or tap a chip."
      : "Voice input is not installed in this build yet. Type or tap a chip.";
    return;
  }
  voiceHint.value = null;
  listening.value = true;
  interim.value = "";
  input.onInterim = (text) => (interim.value = text);
  try {
    const text = (await input.listen()).trim();
    if (text) await startTurn({ utterance: text }, text);
    else voiceHint.value = "I did not catch that. Hold the button and try again.";
  } catch (e) {
    // VoiceError (src/voice) carries a code (off|unsupported|no-local|pack-missing|pack-unavailable|permission|failed)
    // and a driver-facing message; show that message as is.
    const err = e as Error & { code?: string };
    voiceHint.value = err.code ? `${err.message} Type or tap a chip.` : `Voice input failed: ${err.message}. Type or tap a chip.`;
  } finally {
    listening.value = false;
    interim.value = "";
    input.onInterim = undefined;
  }
}

export function stopListening(): void {
  getSpeechInput(settings.value)?.stop?.();
}
