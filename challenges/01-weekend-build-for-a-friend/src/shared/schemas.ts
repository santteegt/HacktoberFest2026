// Shared contracts (plan section 2.2). zod is the single source of truth: the server validates
// requests and data files with these schemas, the UI uses the inferred types (src/shared/types.ts).
// FROZEN: only T0 and the integration tasks (T7, T10) edit this file. Request changes in your report.
import { z } from "zod";

// ---------- primitives ----------

export const Grip = z.enum(["low", "medium", "high"]);
export const Phase = z.enum(["entry", "mid", "exit", "none"]);
export const Outcome = z.enum(["better", "same", "worse"]);
export const ParamValue = z.union([z.number(), z.string(), z.null()]);
/** Keys are ParamDef.id. */
export const SetupValues = z.record(z.string(), ParamValue);
export const CarId = z.enum(["yokomo-bd12", "generic"]);
export const ExplainerId = z.enum([
  "camber",
  "toe",
  "caster",
  "rideHeight",
  "droop",
  "shockAngle",
  "arb",
  "ackermann",
  "bumpSteer",
  "rollCentre",
  "weight",
  "body",
]);
export const ParamGroup = z.enum(["alignment", "chassis", "steering", "damping", "drivetrain", "aero", "tyres"]);

// ---------- domain data (data/*.json, owned by T2) ----------

export const ParamDef = z.object({
  id: z.string(),
  label: z.string(),
  group: ParamGroup,
  unit: z.string(),
  kind: z.enum(["number", "enum", "text", "computed"]),
  min: z.number().optional(),
  max: z.number().optional(),
  step: z.number().optional(),
  options: z.array(z.number()).optional(),
  /** Only for kind "computed", e.g. "spurT / pinionT * 1.9". */
  formula: z.string().optional(),
  /** BD12 factory value; null when Yokomo gives none. Absent in the file (computed params) means null. */
  bd12: ParamValue.default(null),
  /** Generic (Xray-derived) value; null when unknown. */
  generic: ParamValue.default(null),
  /** Chunk ids in data/generated/kb.json. */
  src: z.array(z.string()),
  /** Human note on where the range comes from ("UNSOURCED" etc.). */
  range: z.string(),
  explainer: ExplainerId.optional(),
});

/** data/params.bd12.json */
export const ParamsFile = z.object({
  car: CarId,
  status: z.string(),
  baselineRule: z.string(),
  /** Sign conventions shown next to fields, keyed by topic (camber, frontToe, droop, ...). */
  conventions: z.record(z.string(), z.string()),
  params: z.array(ParamDef),
});

/** data/symptoms.json (array) */
export const SymptomDef = z.object({
  id: z.string(),
  label: z.string(),
  phase: Phase,
  /** True for symptoms that only walk pre-checks and never suggest a setup change. */
  precheckOnly: z.boolean().optional(),
  prechecks: z.array(z.string()),
  synonyms: z.array(z.string()),
});

/** data/prechecks.json (array) */
export const PrecheckDef = z.object({
  id: z.string(),
  label: z.string(),
  detail: z.string(),
  citations: z.array(z.string()),
});

/** data/levers.json (array) */
export const LeverRow = z.object({
  id: z.string(),
  symptomId: z.string(),
  phases: z.array(Phase),
  grip: z.array(Grip).optional(),
  kind: z.enum(["numeric", "qualitative"]),
  param: z.string().optional(),
  direction: z.enum(["increase", "decrease"]).optional(),
  step: z.number().optional(),
  min: z.number().optional(),
  max: z.number().optional(),
  unit: z.string().optional(),
  action: z.string(),
  effect: z.string(),
  tradeOff: z.string(),
  verify: z.string(),
  followUp: z.string().optional(),
  citations: z.array(z.string()),
  /** 1 = try first. */
  priority: z.number(),
  basis: z.enum(["stated", "inverse", "inferred"]),
  notes: z.string().optional(),
  status: z.enum(["draft", "reviewed"]),
});

// ---------- knowledge base (data/generated/kb.json, built by scripts/build-kb.mjs) ----------

export const KbChunk = z.object({
  /** "<page>#<slug of the bold lead>", referenced by citations. */
  id: z.string(),
  page: z.string(),
  pageTitle: z.string(),
  /** "snapshot" = the author's frozen pre-window notes (kb/source); "additions" = written in the window (kb/additions). */
  origin: z.enum(["snapshot", "additions"]),
  section: z.string(),
  lead: z.string(),
  text: z.string(),
});

export const KbPage = z.object({
  slug: z.string(),
  /** "source" (frozen pre-window snapshot) or "additions" (written in the window). */
  origin: z.string(),
  title: z.string(),
  description: z.string().optional(),
  tags: z.array(z.string()),
  related: z.array(z.string()),
});

export const KbFile = z.object({
  contentHash: z.string(),
  pages: z.array(KbPage),
  chunks: z.array(KbChunk),
});

export const KbStats = z.object({
  pages: z.number(),
  chunks: z.number(),
  contentHash: z.string(),
});

// ---------- vault (var/pit.db, owned by T1) ----------

export const TrackConditions = z.object({
  trackName: z.string(),
  surface: z.enum(["asphalt", "carpet", "concrete", "other"]),
  grip: Grip,
  bumpy: z.boolean(),
  layout: z.enum(["tight", "medium", "fast"]).optional(),
  airTempC: z.number().optional(),
  trackTempC: z.number().optional(),
  timeOfDay: z.enum(["morning", "midday", "evening"]).optional(),
  dusty: z.boolean().optional(),
  notes: z.string().optional(),
});

/** Copy-on-write: every change creates a new row. */
export const Setup = z.object({
  id: z.string(),
  values: SetupValues,
  parentId: z.string().optional(),
  createdAt: z.number(),
});

export const Session = z.object({
  id: z.string(),
  /** ISO date, e.g. "2026-10-04". */
  date: z.string(),
  car: CarId,
  conditions: TrackConditions,
  currentSetupId: z.string(),
  notes: z.string().optional(),
  createdAt: z.number(),
});

export const Rating = z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5)]);

export const Run = z.object({
  id: z.string(),
  sessionId: z.string(),
  seq: z.number().int(),
  setupId: z.string(),
  conditions: TrackConditions.partial().optional(),
  lapTimesMs: z.array(z.number()).optional(),
  bestLapMs: z.number().optional(),
  rating: Rating.optional(),
  /** Symptom ids. */
  feel: z.array(z.string()),
  notes: z.string().optional(),
  createdAt: z.number(),
});

export const ChangeSource = z.enum(["coach", "manual", "revert"]);

export const Change = z.object({
  id: z.string(),
  sessionId: z.string(),
  beforeSetupId: z.string(),
  afterSetupId: z.string(),
  param: z.string(),
  from: ParamValue,
  to: ParamValue,
  leverId: z.string().optional(),
  symptomId: z.string().optional(),
  source: ChangeSource,
  coachRunId: z.string().optional(),
  outcome: Outcome.optional(),
  outcomeRunId: z.string().optional(),
  createdAt: z.number(),
});

export const SavedSetup = z.object({
  id: z.string(),
  label: z.string(),
  setupId: z.string(),
  conditions: TrackConditions,
  sessionId: z.string().optional(),
  runId: z.string().optional(),
  eventName: z.string().optional(),
  verdict: z.string().optional(),
  createdAt: z.number(),
});

// ---------- settings (settings table) ----------

const settingsFields = {
  ollamaUrl: z.string(),
  model: z.string(),
  numCtx: z.number().int(),
  /** Coach phrasing (LLM explanations); off = template text only. */
  llmPhrasing: z.boolean(),
  reviewedOnly: z.boolean(),
  voiceIn: z.enum(["local", "cloud-optin", "off"]),
  voiceOut: z.enum(["browser", "say", "off"]),
  voiceName: z.string(),
  tempUnit: z.enum(["C", "F"]),
  car: CarId,
};

/** Full settings; parsing `{}` yields the defaults (server/config.ts overrides url/model/numCtx from env). */
export const Settings = z.object({
  ollamaUrl: settingsFields.ollamaUrl.default("http://localhost:11434"),
  model: settingsFields.model.default("gemma4:e4b-it-qat"),
  numCtx: settingsFields.numCtx.default(4096),
  llmPhrasing: settingsFields.llmPhrasing.default(true),
  reviewedOnly: settingsFields.reviewedOnly.default(false),
  voiceIn: settingsFields.voiceIn.default("off"),
  voiceOut: settingsFields.voiceOut.default("browser"),
  voiceName: settingsFields.voiceName.optional(),
  tempUnit: settingsFields.tempUnit.default("C"),
  car: settingsFields.car.default("yokomo-bd12"),
});

/** PUT /api/settings body: any subset; no defaults are filled in (zod's .partial() would fill them). */
export const SettingsPatch = z.object(settingsFields).partial();

// ---------- coach turn (T3) ----------

export const Classification = z.object({
  symptomId: z.string(),
  /** Second-best symptom id, or "none". */
  altId: z.string(),
  phase: Phase,
  confidence: z.number().min(0).max(1),
  source: z.enum(["llm", "chip", "keyword"]),
  ms: z.number().optional(),
});

export const SceneBinding = z.object({
  explainer: ExplainerId,
  param: z.string(),
  from: z.number(),
  to: z.number(),
});

export const LeverSuggestion = z.object({
  lever: LeverRow,
  from: ParamValue,
  to: ParamValue,
  atLimit: z.boolean(),
  needsCurrentValue: z.boolean(),
  scene: SceneBinding.optional(),
});

export const SkipReason = z.enum(["at-limit", "tried-worse", "tried-same", "grip-mismatch", "draft-hidden"]);

export const Suggestion = z.object({
  primary: LeverSuggestion.nullable(),
  alternatives: z.array(LeverSuggestion),
  skipped: z.array(z.object({ leverId: z.string(), reason: SkipReason })),
  noLeverReason: z.string().optional(),
});

export const Refusal = z.object({
  reason: z.enum(["out-of-scope", "tyre-compound-gap", "electronics", "other-car-type"]),
  message: z.string(),
  citations: z.array(z.string()),
});

/** Exactly one of `utterance` or `symptomId` (a tapped chip). */
export const CoachTurnInput = z
  .object({
    sessionId: z.string(),
    utterance: z.string().optional(),
    symptomId: z.string().optional(),
    phase: Phase.optional(),
  })
  .refine((v) => (v.utterance ? 1 : 0) + (v.symptomId ? 1 : 0) === 1, {
    message: "send exactly one of utterance or symptomId",
  });

export const Explanation = z.object({
  text: z.string(),
  source: z.enum(["llm", "template"]),
  ms: z.number().optional(),
});

export const Decision = z.enum(["apply", "skip", "alternative"]);
export const TurnStatus = z.enum(["awaiting-decision", "awaiting-outcome", "done"]);

export const TurnState = z.object({
  runId: z.string(),
  input: CoachTurnInput,
  classification: Classification.optional(),
  refusal: Refusal.optional(),
  prechecks: z.array(PrecheckDef),
  suggestion: Suggestion.optional(),
  explanation: Explanation.optional(),
  decision: Decision.optional(),
  appliedChangeId: z.string().optional(),
  outcome: Outcome.optional(),
  status: TurnStatus,
});

export const OutcomeResult = z.object({
  change: Change,
  prompt: z.enum(["save-setup", "next-lever", "offer-revert"]),
  revert: z.object({ param: z.string(), to: ParamValue }).optional(),
  next: Suggestion.optional(),
});

// ---------- LLM status (T3) ----------

export const LlmStatus = z.object({
  reachable: z.boolean(),
  url: z.string(),
  model: z.string(),
  /** Model is pulled (in /api/tags). */
  present: z.boolean(),
  /** Model is loaded in memory (in /api/ps). */
  loaded: z.boolean(),
  numCtx: z.number(),
  lastLatencyMs: z.number().optional(),
});

/** One frame of POST /api/llm/pull (SSE), forwarded from Ollama /api/pull. */
export const PullProgress = z.object({
  status: z.string(),
  completed: z.number().optional(),
  total: z.number().optional(),
});

// ---------- analysis (T8). PROVISIONAL: derived from plan 4.6/4.7; T8 may request changes via T7. ----------

export const ParamDiff = z.object({
  param: z.string(),
  from: ParamValue,
  to: ParamValue,
  direction: z.enum(["increase", "decrease", "changed"]),
});

export const SimilarHit = z.object({
  saved: SavedSetup,
  /** 0-100. */
  score: z.number(),
  /** e.g. "same track", "track 4 C warmer", "grip one step lower". */
  reasons: z.array(z.string()),
  surfaceMismatch: z.boolean(),
  diffVsCurrent: z.array(ParamDiff),
});

export const RunBundle = z.object({
  run: Run,
  setup: Setup,
  session: Session,
});

export const RunComparison = z.object({
  runA: z.string(),
  runB: z.string(),
  setupDiffs: z.array(
    ParamDiff.extend({
      effect: z.string().optional(),
      leverId: z.string().optional(),
      citations: z.array(z.string()),
    }),
  ),
  conditionDiffs: z.array(z.object({ text: z.string(), citations: z.array(z.string()) })),
  lapStats: z.object({
    status: z.enum(["insufficient-data", "within-noise", "above-noise"]),
    meanA: z.number().optional(),
    meanB: z.number().optional(),
    sigma: z.number().optional(),
    n: z.number().optional(),
    /** Noise floor in seconds: 2.8 * sigma * sqrt(2 / n). */
    delta: z.number().optional(),
    /** meanB - meanA in seconds (negative = B faster). */
    diffS: z.number().optional(),
    text: z.string(),
    citations: z.array(z.string()),
  }),
  confounded: z.boolean(),
  confoundText: z.string().optional(),
  /** Chunk ids behind the confounding note (one change at a time, back to back). */
  confoundCitations: z.array(z.string()).optional(),
});

export const ParamHistoryRow = z.object({
  param: z.string(),
  direction: z.string(),
  tries: z.number(),
  better: z.number(),
  same: z.number(),
  worse: z.number(),
  /** Shown next to the row, e.g. "your feel, not lap-time proof". */
  label: z.string(),
});

// ---------- export / import (T1) ----------

export const SCHEMA_VERSION = 1;

export const ExportDump = z.object({
  schemaVersion: z.number(),
  exportedAt: z.number().optional(),
  tables: z.object({
    settings: z.array(z.object({ key: z.string(), value: z.unknown() })),
    setups: z.array(Setup),
    sessions: z.array(Session),
    runs: z.array(Run),
    changes: z.array(Change),
    savedSetups: z.array(SavedSetup),
  }),
});

// ---------- errors ----------

export const ApiError = z.object({
  error: z.string(),
  stage: z.string().optional(),
});
