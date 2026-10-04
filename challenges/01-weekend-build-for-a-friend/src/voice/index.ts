// Voice module entry (T6). The coach UI finds createSpeechInput / createSpeechOutput here by name.
export { createSpeechInput, getSpeechInputStatus, installSpeechPack } from "./recognition";
export { createSpeechOutput, listLocalVoices } from "./synthesis";
export { PIT_PHRASES } from "./phrases";
export { splitSentences, SentenceStream } from "./sentences";
export { VoiceError } from "./types";
export type { SpeechInput, SpeechOutput, SpeechInputStatus, VoiceChoice, VoiceInErrorCode } from "./types";
