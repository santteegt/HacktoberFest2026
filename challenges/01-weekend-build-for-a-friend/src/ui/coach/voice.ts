// Voice bridge (T4a). The coach only touches voice through the interfaces in src/voice/types.ts.
// T6 delivers src/voice/index.ts; until it exists, speech is unavailable and everything falls back to typing/chips.
// Expected optional exports of src/voice/index.ts (looked up by name, so a missing one is harmless):
//   createSpeechInput(settings: Settings | null): SpeechInput      (may also expose stop() and onInterim)
//   createSpeechOutput(settings: Settings | null): SpeechOutput
import type { Settings } from "../../shared/types";
import type { SpeechInput, SpeechOutput } from "../../voice/types";

/** Optional extras a SpeechInput implementation may offer for hold-to-talk. */
export interface HoldableSpeechInput extends SpeechInput {
  /** Ends listening now and lets listen() resolve with what was heard. */
  stop?(): void;
  /** Assigned by the UI to show the interim transcript. */
  onInterim?: (text: string) => void;
}

interface VoiceModule {
  createSpeechInput?: (s: Settings | null) => SpeechInput;
  createSpeechOutput?: (s: Settings | null) => SpeechOutput;
}

const found = import.meta.glob("../../voice/index.ts", { eager: true }) as Record<string, VoiceModule>;
const mod: VoiceModule | undefined = Object.values(found)[0];

let inKey = "";
let inInst: HoldableSpeechInput | null = null;
let outKey = "";
let outInst: SpeechOutput | null = null;

export function getSpeechInput(s: Settings | null): HoldableSpeechInput | null {
  if (!mod?.createSpeechInput || !s || s.voiceIn === "off") return null;
  const key = s.voiceIn;
  if (inKey !== key || !inInst) {
    try {
      inInst = mod.createSpeechInput(s) as HoldableSpeechInput;
      inKey = key;
    } catch {
      inInst = null;
    }
  }
  return inInst;
}

export function getSpeechOutput(s: Settings | null): SpeechOutput | null {
  if (!mod?.createSpeechOutput || !s || s.voiceOut !== "browser") return null;
  const key = `${s.voiceOut}:${s.voiceName ?? ""}`;
  if (outKey !== key || !outInst) {
    try {
      outInst = mod.createSpeechOutput(s);
      outKey = key;
    } catch {
      outInst = null;
    }
  }
  return outInst;
}

/** True when a voice module is present at all (used to word the hint when a button is tapped). */
export const voiceModulePresent = !!mod;
