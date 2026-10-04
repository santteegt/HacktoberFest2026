// Authored decision data: the model picks ids from these tables; it never invents numbers.
// Rows live in data/symptoms.json and data/levers.json and are reviewed by hand.

export type Phase = "entry" | "mid" | "exit";

export interface Symptom {
  id: string; // e.g. "exit-oversteer"
  label: string;
  phase: Phase | "any";
  examples: string[]; // driver phrasings, also used for the mini eval
}

export interface Lever {
  id: string;
  symptomId: string;
  phases: Array<Phase | "any">;
  grip?: Array<"low" | "medium" | "high">;
  param: string; // key into SetupValues
  direction: "increase" | "decrease";
  step: number;
  min: number;
  max: number;
  unit: string;
  expectedEffect: string;
  verify: string; // how to check it worked, e.g. "3-5 laps, compare feel on exit"
  citations: string[]; // chunk ids in public/kb.json; build fails if any is missing
}
