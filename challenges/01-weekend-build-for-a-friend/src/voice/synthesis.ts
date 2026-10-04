// Speech output (T6). Browser speechSynthesis restricted to voices with localService === true (no network fetch),
// speaking sentence by sentence; or the macOS `say` route (POST /api/speak) when settings.voiceOut is "say".
import type { Settings } from "../shared/types";
import { SentenceStream, splitSentences } from "./sentences";
import type { SpeechOutput, VoiceChoice } from "./types";

function synth(): SpeechSynthesis | null {
  return typeof speechSynthesis === "undefined" ? null : speechSynthesis;
}

/** Voices load asynchronously in Chrome; resolves with whatever exists after `voiceschanged` or a short wait. */
function loadVoices(timeoutMs = 1500): Promise<SpeechSynthesisVoice[]> {
  const s = synth();
  if (!s) return Promise.resolve([]);
  const now = s.getVoices();
  if (now.length) return Promise.resolve(now);
  return new Promise((resolve) => {
    const done = () => {
      s.removeEventListener("voiceschanged", done);
      clearTimeout(t);
      resolve(s.getVoices());
    };
    const t = setTimeout(done, timeoutMs);
    s.addEventListener("voiceschanged", done);
  });
}

/** Local voices for the Settings dropdown (English first). Empty when the browser has none. */
export async function listLocalVoices(): Promise<VoiceChoice[]> {
  const voices = (await loadVoices()).filter((v) => v.localService);
  return voices
    .map((v) => ({ name: v.name, lang: v.lang, default: v.default }))
    .sort((a, b) => Number(b.lang.startsWith("en")) - Number(a.lang.startsWith("en")) || a.name.localeCompare(b.name));
}

function pickVoice(voices: SpeechSynthesisVoice[], name?: string): SpeechSynthesisVoice | null {
  const local = voices.filter((v) => v.localService);
  if (!local.length) return null;
  return (
    (name ? local.find((v) => v.name === name) : undefined) ??
    local.find((v) => v.default && v.lang.startsWith("en")) ??
    local.find((v) => v.lang.startsWith("en")) ??
    local[0]!
  );
}

class BrowserSpeechOutput implements SpeechOutput {
  readonly local = true;
  private gen = 0; // bumped by cancel() so queued sentences of an older call are dropped
  private stream = new SentenceStream();
  private tail: Promise<void> = Promise.resolve();

  constructor(private readonly voiceName?: string) {}

  private enqueue(sentences: string[]): Promise<void> {
    const s = synth();
    if (!s || !sentences.length) return this.tail;
    const gen = this.gen;
    this.tail = this.tail.catch(() => {}); // an earlier failure must not block new text
    for (const sentence of sentences) {
      this.tail = this.tail.then(async () => {
        if (gen !== this.gen) return;
        const voice = pickVoice(await loadVoices(), this.voiceName);
        if (!voice) throw new Error("no local voice installed");
        await new Promise<void>((resolve) => {
          const u = new SpeechSynthesisUtterance(sentence);
          u.voice = voice;
          u.lang = voice.lang;
          u.onend = () => resolve();
          u.onerror = () => resolve(); // "canceled"/"interrupted" on cancel(), or an engine error: move on
          s.speak(u);
        });
      });
    }
    return this.tail;
  }

  speak(text: string): Promise<void> {
    return this.enqueue(splitSentences(text));
  }

  speakChunk(delta: string): void {
    void this.enqueue(this.stream.push(delta)).catch(() => {});
  }

  flush(): Promise<void> {
    return this.enqueue(this.stream.flush());
  }

  cancel(): void {
    this.gen++;
    this.stream.reset();
    this.tail = Promise.resolve();
    synth()?.cancel();
  }
}

class SaySpeechOutput implements SpeechOutput {
  readonly local = true; // macOS `say` runs on this machine
  private stream = new SentenceStream();
  constructor(private readonly voiceName?: string) {}

  async speak(text: string): Promise<void> {
    const res = await fetch("/api/speak", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, ...(this.voiceName ? { voice: this.voiceName } : {}) }),
    });
    if (!res.ok) throw new Error(`/api/speak ${res.status}`);
  }

  // `say` is one process that a new request replaces, so streamed text is spoken once, at flush().
  speakChunk(delta: string): void {
    this.stream.push(delta);
  }
  async flush(): Promise<void> {
    const rest = this.stream.flush().join(" ");
    if (rest) await this.speak(rest);
  }

  cancel(): void {
    this.stream.reset();
    void fetch("/api/speak", { method: "DELETE" }).catch(() => {});
  }
}

/** Inert output for voiceOut "off". */
class OffOutput implements SpeechOutput {
  readonly local = true;
  speak(): Promise<void> {
    return Promise.resolve();
  }
  cancel(): void {}
}

export function createSpeechOutput(settings: Pick<Settings, "voiceOut" | "voiceName"> | null): SpeechOutput {
  const mode = settings?.voiceOut ?? "off";
  if (mode === "say") return new SaySpeechOutput(settings?.voiceName);
  if (mode === "browser") return new BrowserSpeechOutput(settings?.voiceName);
  return new OffOutput();
}
