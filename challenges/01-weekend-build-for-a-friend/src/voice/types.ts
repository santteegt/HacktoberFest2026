// Voice loop: push-to-talk speech in, spoken answer out. Both must work with the radio off.
// Extended additively by T6: every new member is optional so existing callers keep compiling.

/** Why speech input could not run. The UI falls back to typing and chips for every code. */
export type VoiceInErrorCode =
  | "off" // voiceIn setting is "off"
  | "unsupported" // no SpeechRecognition at all (Firefox, some embedded browsers)
  | "no-local" // browser has recognition but cannot guarantee on-device processing (Safari, Chrome before 139, Android)
  | "pack-missing" // on-device language pack not installed yet (install it in Settings)
  | "pack-unavailable" // browser reports on-device en-US as unavailable
  | "permission" // microphone denied
  | "failed"; // anything else

export class VoiceError extends Error {
  constructor(
    readonly code: VoiceInErrorCode,
    message: string,
  ) {
    super(message);
    this.name = "VoiceError";
  }
}

/** Live status for the Settings screen and the offline checklist. */
export interface SpeechInputStatus {
  mode: "local" | "cloud-optin" | "off";
  /** Machine-readable state; "cloud" means on-device was not requested. */
  state: "available" | "downloadable" | "downloading" | "unavailable" | "unsupported" | "no-local" | "cloud" | "off";
  /** True only when `state === "available"` in local mode (the on-device pack is ready). */
  onDeviceReady: boolean;
  /** One line for the UI. */
  detail: string;
}

export interface SpeechInput {
  /** True only when recognition runs on-device (e.g. SpeechRecognition.processLocally). */
  readonly onDevice: boolean;
  /** Label to show next to the mic. Cloud mode says plainly that audio goes to Google. */
  readonly label?: string;
  /** Push-to-talk: starts listening; resolves with the transcript after stop() (or silence). Rejects with VoiceError. */
  listen(): Promise<string>;
  /** Ends listening now; listen() then resolves with what was heard. */
  stop?(): void;
  /** Assigned by the UI to show the interim transcript while listening. */
  onInterim?: (text: string) => void;
  /** Live availability check (never starts the microphone). */
  status?(): Promise<SpeechInputStatus>;
  /** Downloads the on-device speech pack (call from a click). Resolves true when installed. */
  install?(): Promise<boolean>;
}

export interface SpeechOutput {
  /** True only for local voices (no network fetch). */
  readonly local: boolean;
  /** Queues the text sentence by sentence; resolves when it has been spoken (or cancelled). */
  speak(text: string): Promise<void>;
  /** For streamed tokens: add a delta, complete sentences are spoken as they appear. */
  speakChunk?(delta: string): void;
  /** Speaks whatever remains of the streamed text. */
  flush?(): Promise<void>;
  cancel(): void;
}

/** One entry of the Settings voice dropdown. */
export interface VoiceChoice {
  name: string;
  lang: string;
  default: boolean;
}
