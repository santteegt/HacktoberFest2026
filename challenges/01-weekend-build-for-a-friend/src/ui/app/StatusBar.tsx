// Top status bar (T4a): session summary, model status (polled every 15 s), online/offline.
import { signal } from "@preact/signals";
import { useEffect } from "preact/hooks";
import { isMock } from "../../api/client";
import { llmStatus, session, settings } from "../store";
import { openStartSession, pollLlmStatus, serverReachable } from "./bootstrap";
import { Button } from "./components";

const online = signal(typeof navigator === "undefined" ? true : navigator.onLine);
const POLL_MS = 15_000;

/** "gemma4:e2b-it-qat" -> "Gemma E2B". Falls back to the raw tag. */
export function modelShortName(tag: string): string {
  const m = /^gemma(\d*):?([a-z0-9]+)/i.exec(tag);
  return m ? `Gemma ${m[2].toUpperCase()}` : tag || "model";
}

function llmPill(): { tone: "ok" | "warn" | "danger" | "idle"; text: string } {
  if (!serverReachable.value) return { tone: "danger", text: "Pit server not reachable" };
  const s = llmStatus.value;
  if (!s) return { tone: "idle", text: "Checking model…" };
  const name = modelShortName(s.model);
  if (!s.reachable) return { tone: "warn", text: `${name}: Ollama not reachable (chips still work)` };
  if (!s.present) return { tone: "warn", text: `${name}: not pulled yet` };
  if (!s.loaded) return { tone: "warn", text: `${name}: loads on first use` };
  return { tone: "ok", text: `${name}: ready` };
}

export function summarizeSession(tempUnit: "C" | "F"): string[] | null {
  const s = session.value;
  if (!s) return null;
  const c = s.conditions;
  const parts = [c.trackName || "Untitled track", c.surface, `${c.grip} grip`];
  if (typeof c.trackTempC === "number") {
    parts.push(tempUnit === "F" ? `${Math.round((c.trackTempC * 9) / 5 + 32)} F` : `${c.trackTempC} C`);
  }
  return parts;
}

export function StatusBar() {
  useEffect(() => {
    const on = () => (online.value = true);
    const off = () => (online.value = false);
    addEventListener("online", on);
    addEventListener("offline", off);
    const t = setInterval(() => void pollLlmStatus(), POLL_MS);
    return () => {
      removeEventListener("online", on);
      removeEventListener("offline", off);
      clearInterval(t);
    };
  }, []);
  const pill = llmPill();
  const parts = summarizeSession(settings.value?.tempUnit ?? "C");
  return (
    <header class="statusbar">
      <span class="brand">RC PIT COMPANION</span>
      {isMock() && <span class="mock-flag" title="Canned in-memory data; no server involved">MOCK DATA</span>}
      <div class="session-summary">
        {parts ? (
          <>
            Session: <b>{parts[0]}</b> | {parts.slice(1).join(" | ")}
          </>
        ) : (
          <Button size="md" onClick={openStartSession}>
            Start a session
          </Button>
        )}
      </div>
      <span class="status-pill" data-tone={pill.tone === "idle" ? undefined : pill.tone} title={llmStatus.value?.url}>
        {pill.text}
      </span>
      <span
        class="status-pill"
        data-tone={online.value ? "ok" : "warn"}
        title={online.value ? "Network is up. Nothing here needs it." : "Offline is fine: the coach, notes and vault all run on this laptop."}
      >
        {online.value ? "online" : "offline"}
      </span>
    </header>
  );
}
