// Domain model for the setup vault: what the friend wants to keep between practice
// sessions and pull up on race day. Persisted in IndexedDB (no server, no account).

export type CarProfileId = "yokomo-bd12" | "generic-1-10-touring";

/** Setup values keyed by parameter id, e.g. { rearToeInDeg: 2.5, frontCamberDeg: -1.0 }. */
export type SetupValues = Record<string, number | string>;

export interface TrackConditions {
  trackName: string;
  surface: "asphalt" | "carpet" | "concrete" | "other";
  grip: "low" | "medium" | "high";
  bumpy: boolean;
  layout?: "tight" | "medium" | "fast";
  airTempC?: number;
  trackTempC?: number;
  notes?: string;
}

/** The driver's description of how the car feels, mapped by the LLM to a fixed symptom id. */
export interface FeelReport {
  symptomId: string;
  phase: "entry" | "mid" | "exit";
  confidence: number;
  utterance: string;
}

export interface ChangeLogEntry {
  ts: number;
  leverId: string;
  param: string;
  from: number | string;
  to: number | string;
  symptomId: string;
  outcome?: "better" | "same" | "worse";
}

/** One practice run-through at a track. */
export interface Session {
  id: string;
  date: string; // ISO date
  car: CarProfileId;
  conditions: TrackConditions;
  startSetup: SetupValues;
  changes: ChangeLogEntry[];
  endSetup: SetupValues;
}

/** A setup worth keeping, searchable by conditions on race day. */
export interface SavedSetup {
  id: string;
  label: string;
  car: CarProfileId;
  setup: SetupValues;
  conditions: TrackConditions;
  result?: { bestLapMs?: number; feeling: string; eventName?: string };
  sourceSessionId?: string;
  createdAt: number;
}
