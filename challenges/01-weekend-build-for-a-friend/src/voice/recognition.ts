// Speech input (T6). Chrome on-device recognition via SpeechRecognition.processLocally.
// Signatures per MDN (checked 2026-10-04): static available({langs, quality?, processLocally?}) resolves to
// "available" | "downloading" | "downloadable" | "unavailable"; static install({langs, processLocally}) resolves a boolean;
// instance phrases is an ObservableArray of SpeechRecognitionPhrase(phrase, boost).
// Local mode NEVER falls back to cloud: if the browser cannot guarantee on-device processing the input errors out
// and the UI uses typing and chips. Cloud only when the setting is "cloud-optin".
import type { Settings } from "../shared/types";
import { PHRASE_BOOST, PIT_PHRASES } from "./phrases";
import { VoiceError, type SpeechInput, type SpeechInputStatus } from "./types";

const LANG = "en-US";
const MAX_LISTEN_MS = 30_000;

// Minimal structural types: the TS DOM lib does not ship these newer members.
interface RecAlternative {
  transcript: string;
}
interface RecResult {
  readonly isFinal: boolean;
  readonly length: number;
  [i: number]: RecAlternative;
}
interface RecEvent {
  readonly resultIndex: number;
  readonly results: { readonly length: number; [i: number]: RecResult };
}
interface Rec {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  processLocally?: boolean;
  phrases?: unknown;
  onresult: ((e: RecEvent) => void) | null;
  onerror: ((e: { error: string; message?: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
interface RecCtor {
  new (): Rec;
  available?: (o: { langs: string[]; quality?: string; processLocally?: boolean }) => Promise<string>;
  install?: (o: { langs: string[]; processLocally?: boolean }) => Promise<boolean>;
}

function getCtor(): RecCtor | null {
  const w = globalThis as unknown as { SpeechRecognition?: RecCtor; webkitSpeechRecognition?: RecCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

/** True when this browser exposes the on-device API (Chrome desktop 139+). */
function hasLocalApi(C: RecCtor): boolean {
  return typeof C.available === "function" && typeof C.install === "function" && "processLocally" in C.prototype;
}

/** Live on-device status for Settings (never opens the microphone). */
export async function getSpeechInputStatus(mode: "local" | "cloud-optin" | "off"): Promise<SpeechInputStatus> {
  if (mode === "off") return { mode, state: "off", onDeviceReady: false, detail: "Voice input is off." };
  const C = getCtor();
  if (!C) {
    return { mode, state: "unsupported", onDeviceReady: false, detail: "This browser has no speech recognition. Type or tap a chip." };
  }
  if (mode === "cloud-optin") {
    return {
      mode,
      state: "cloud",
      onDeviceReady: false,
      detail: "Chrome online recognition: your audio is sent to Google. It needs the internet.",
    };
  }
  if (!hasLocalApi(C)) {
    return {
      mode,
      state: "no-local",
      onDeviceReady: false,
      detail: "This browser cannot guarantee on-device recognition (needs desktop Chrome 139 or newer). Type or tap a chip.",
    };
  }
  try {
    const s = await C.available!({ langs: [LANG], processLocally: true });
    const state = s === "available" || s === "downloadable" || s === "downloading" ? s : "unavailable";
    const detail =
      state === "available"
        ? "On-device speech pack for en-US is installed."
        : state === "downloadable"
          ? "On-device en-US speech pack is not installed yet. Use Install speech pack (needs internet once)."
          : state === "downloading"
            ? "On-device en-US speech pack is downloading."
            : "This browser reports on-device en-US recognition as unavailable. Type or tap a chip.";
    return { mode, state, onDeviceReady: state === "available", detail };
  } catch (e) {
    return { mode, state: "unavailable", onDeviceReady: false, detail: `available() failed: ${(e as Error).message}` };
  }
}

/** Downloads the on-device en-US pack. Call from a click handler; needs internet once. */
export async function installSpeechPack(): Promise<boolean> {
  const C = getCtor();
  if (!C || !hasLocalApi(C)) return false;
  try {
    return !!(await C.install!({ langs: [LANG], processLocally: true }));
  } catch {
    return false;
  }
}

function applyPhrases(rec: Rec): void {
  const P = (globalThis as unknown as { SpeechRecognitionPhrase?: new (p: string, b: number) => unknown }).SpeechRecognitionPhrase;
  if (!P || !("phrases" in rec)) return; // phrases: Chrome 142+; older Chrome just recognises without biasing
  try {
    const list = PIT_PHRASES.map((p) => new P(p, PHRASE_BOOST));
    const arr = rec.phrases as { push?: (...x: unknown[]) => void } | undefined;
    if (arr && typeof arr.push === "function") arr.push(...list);
    else rec.phrases = list;
  } catch {
    /* biasing is optional */
  }
}

const ERRORS: Record<string, [VoiceError["code"], string]> = {
  "not-allowed": ["permission", "Microphone permission was denied."],
  "service-not-allowed": ["permission", "Speech service is not allowed in this browser."],
  "audio-capture": ["failed", "No microphone found."],
  "language-not-supported": ["pack-unavailable", "The en-US speech pack is not available on-device."],
  network: ["failed", "Recognition needs the internet in this mode."],
};

class WebSpeechInput implements SpeechInput {
  readonly onDevice: boolean;
  readonly label: string;
  onInterim?: (text: string) => void;
  private active: { rec: Rec; promise: Promise<string> } | null = null;

  constructor(private readonly mode: "local" | "cloud-optin") {
    this.onDevice = mode === "local";
    this.label = this.onDevice ? "Chrome on-device" : "Chrome online (audio goes to Google)";
  }

  status(): Promise<SpeechInputStatus> {
    return getSpeechInputStatus(this.mode);
  }

  install(): Promise<boolean> {
    return installSpeechPack();
  }

  stop(): void {
    try {
      this.active?.rec.stop();
    } catch {
      /* already stopped */
    }
  }

  listen(): Promise<string> {
    if (this.active) return this.active.promise;
    return this.start();
  }

  private async start(): Promise<string> {
    const C = getCtor();
    if (!C) throw new VoiceError("unsupported", "This browser has no speech recognition.");
    if (this.onDevice) {
      if (!hasLocalApi(C)) throw new VoiceError("no-local", "This browser cannot guarantee on-device recognition.");
      const s = await C.available!({ langs: [LANG], processLocally: true });
      if (s === "downloadable" || s === "downloading") {
        throw new VoiceError("pack-missing", "The on-device speech pack is not installed. Install it in Settings.");
      }
      if (s !== "available") throw new VoiceError("pack-unavailable", "On-device en-US recognition is unavailable here.");
    }

    const rec = new C();
    rec.lang = LANG;
    rec.continuous = true; // push-to-talk: keep going until stop()
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    if (this.onDevice) {
      rec.processLocally = true;
      applyPhrases(rec);
    }

    const promise = new Promise<string>((resolve, reject) => {
      let finals = "";
      let interim = "";
      let failure: VoiceError | null = null;
      const timer = setTimeout(() => {
        try {
          rec.stop();
        } catch {
          /* ignore */
        }
      }, MAX_LISTEN_MS);
      rec.onresult = (e) => {
        interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const r = e.results[i]!;
          const t = r[0]?.transcript ?? "";
          if (r.isFinal) finals += (finals ? " " : "") + t.trim();
          else interim += t;
        }
        this.onInterim?.(`${finals} ${interim}`.trim());
      };
      rec.onerror = (e) => {
        if (e.error === "no-speech" || e.error === "aborted") return; // end with an empty or partial transcript
        const [code, msg] = ERRORS[e.error] ?? ["failed" as const, `Recognition error: ${e.error}`];
        failure = new VoiceError(code, msg);
      };
      rec.onend = () => {
        clearTimeout(timer);
        this.active = null;
        if (failure) reject(failure);
        else resolve(`${finals} ${interim}`.trim());
      };
      try {
        rec.start();
      } catch (e) {
        clearTimeout(timer);
        this.active = null;
        reject(new VoiceError("failed", (e as Error).message));
      }
    });
    this.active = { rec, promise };
    return promise;
  }
}

/** Inert input for voiceIn "off": never opens the microphone. */
class OffInput implements SpeechInput {
  readonly onDevice = false;
  readonly label = "Voice input off";
  onInterim?: (text: string) => void;
  listen(): Promise<string> {
    return Promise.reject(new VoiceError("off", "Voice input is off in Settings."));
  }
  stop(): void {}
  status(): Promise<SpeechInputStatus> {
    return getSpeechInputStatus("off");
  }
  install(): Promise<boolean> {
    return Promise.resolve(false);
  }
}

export function createSpeechInput(settings: Pick<Settings, "voiceIn"> | null): SpeechInput {
  const mode = settings?.voiceIn ?? "off";
  return mode === "off" ? new OffInput() : new WebSpeechInput(mode);
}
