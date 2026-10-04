// Voice loop: push-to-talk speech in, spoken answer out. Both must work with the radio off.

export interface SpeechInput {
  /** True only when recognition runs on-device (e.g. SpeechRecognition.processLocally). */
  readonly onDevice: boolean;
  listen(): Promise<string>;
}

export interface SpeechOutput {
  /** True only for local voices (no network fetch). */
  readonly local: boolean;
  speak(text: string): Promise<void>;
  cancel(): void;
}
