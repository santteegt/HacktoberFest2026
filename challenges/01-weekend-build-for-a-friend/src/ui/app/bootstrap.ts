// App bootstrap and shared loaders (T4a). Fills the signals in ../store.ts from the API.
//   bootstrap()            load meta, settings, sessions; open the last session; decide on the first-run overlay
//   setActiveSession(id)   load a session bundle into `session` and `currentSetup` (and remember it)
//   refreshSession()       re-load the open session (call after a setup commit, a run, a coach apply)
//   pollLlmStatus()        GET /api/llm/status into `llmStatus` (the status bar calls it every 15 s)
//   firstRun               signal controlling the first-run overlay: { open, step }
import { signal } from "@preact/signals";
import { getLlmStatus, getMeta, getSession, getSettings, listSessions, warmupLlm } from "../../api/client";
import { currentSetup, llmStatus, meta, session, settings } from "../store";

export const bootState = signal<"loading" | "ready" | "error">("loading");
export const bootError = signal<string | null>(null);
/** False when the last API call failed to reach the server at all. */
export const serverReachable = signal(true);
export const firstRun = signal<{ open: boolean; step: 1 | 2 | 3 }>({ open: false, step: 1 });

const SESSION_KEY = "pit.sessionId";
const FIRST_RUN_KEY = "pit.firstRunDone";

function store(op: "get" | "set", key: string, value?: string): string | null {
  try {
    if (op === "set") localStorage.setItem(key, value ?? "");
    else return localStorage.getItem(key);
  } catch {
    /* storage blocked: fine */
  }
  return null;
}

export function markFirstRunDone(): void {
  store("set", FIRST_RUN_KEY, "1");
  firstRun.value = { open: false, step: 1 };
}

export function openStartSession(): void {
  firstRun.value = { open: true, step: 2 };
}

export async function setActiveSession(id: string): Promise<void> {
  const b = await getSession(id);
  session.value = b.session;
  currentSetup.value = b.setups.find((s) => s.id === b.session.currentSetupId) ?? null;
  store("set", SESSION_KEY, id);
}

export async function refreshSession(): Promise<void> {
  if (session.value) await setActiveSession(session.value.id);
}

let warmed = false;

export async function pollLlmStatus(): Promise<void> {
  try {
    const s = await getLlmStatus();
    llmStatus.value = s;
    serverReachable.value = true;
    if (!warmed && s.reachable && s.present && !s.loaded) {
      warmed = true;
      warmupLlm().catch(() => {}); // fire and forget: first answers are faster once the model is loaded
    }
  } catch {
    llmStatus.value = null;
    serverReachable.value = false;
  }
}

export async function bootstrap(): Promise<void> {
  bootState.value = "loading";
  try {
    const [m, s, sessions] = await Promise.all([getMeta(), getSettings(), listSessions()]);
    meta.value = m;
    settings.value = s;
    serverReachable.value = true;
    const sorted = [...sessions].sort((a, b) => b.createdAt - a.createdAt);
    const remembered = store("get", SESSION_KEY);
    const pick = sorted.find((x) => x.id === remembered) ?? sorted[0];
    if (pick) await setActiveSession(pick.id);
    else if (!store("get", FIRST_RUN_KEY)) firstRun.value = { open: true, step: 1 };
    bootState.value = "ready";
  } catch (e) {
    bootError.value = (e as Error).message;
    bootState.value = "error";
    serverReachable.value = false;
  }
  void pollLlmStatus();
}
