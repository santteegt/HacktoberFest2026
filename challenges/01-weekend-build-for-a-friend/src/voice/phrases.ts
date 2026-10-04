// Contextual-biasing phrases for on-device recognition (SpeechRecognition.phrases, Chrome 142+).
// Terms a RC touring-car racer says that a general model tends to mishear.
export const PIT_PHRASES: readonly string[] = [
  "droop",
  "Ackermann",
  "caster",
  "camber",
  "toe",
  "bump steer",
  "anti-roll bar",
  "understeer",
  "oversteer",
  "traction roll",
  "ride height",
  "diff oil",
];

/** Boost value per phrase. MDN shows 1 to 5 in its example; the valid range was not confirmed, so stay modest. */
export const PHRASE_BOOST = 3;
