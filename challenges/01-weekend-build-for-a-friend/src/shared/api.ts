// HTTP API contract (plan section 2.4): request body schemas (zod, validated by the server) and the
// request/response types the UI client (src/api/client.ts) uses. All paths are under /api.
// Errors are `ApiError` ({ error, stage? }) with a 4xx/5xx status.
// FROZEN: only T0, T7 and T10 edit this file. Request changes in your task report.
import { z } from "zod";
import {
  CarId,
  ChangeSource,
  Decision,
  ExportDump,
  Outcome,
  ParamValue,
  Run,
  SavedSetup,
  SettingsPatch,
  TrackConditions,
} from "./schemas";
import type {
  Change,
  CoachTurnInput,
  ExportDump as ExportDumpT,
  KbChunk,
  KbStats,
  LeverRow,
  LlmStatus,
  OutcomeResult,
  ParamDef,
  ParamHistoryRow,
  PrecheckDef,
  RunComparison,
  SavedSetup as SavedSetupT,
  Session,
  Setup,
  Settings,
  SettingsPatch as SettingsPatchT,
  SimilarHit,
  SymptomDef,
  TurnState,
  Run as RunT,
} from "./types";

// ---------- request body schemas ----------

/** PUT /api/settings: any subset of Settings. */
export const PutSettingsBody = SettingsPatch;

/** POST /api/sessions (creates the baseline setup row: BD12 value, else generic). */
export const CreateSessionBody = z.object({
  date: z.string(),
  car: CarId,
  conditions: TrackConditions,
  notes: z.string().optional(),
});

/** PATCH /api/sessions/:id */
export const PatchSessionBody = z.object({
  conditions: TrackConditions.optional(),
  notes: z.string().optional(),
});

/** POST /api/sessions/:id/setup (copy-on-write; one Change per changed param). */
export const ApplySetupBody = z.object({
  values: z.record(z.string(), ParamValue),
  source: ChangeSource,
  leverId: z.string().optional(),
  symptomId: z.string().optional(),
  coachRunId: z.string().optional(),
});

/** POST /api/sessions/:id/runs (setupId = session.currentSetupId; seq and createdAt set by the server). */
export const AddRunBody = Run.omit({ id: true, seq: true, createdAt: true, setupId: true });

/** PATCH /api/changes/:id */
export const PatchChangeBody = z.object({
  outcome: Outcome,
  outcomeRunId: z.string().optional(),
});

/** POST /api/saved */
export const SaveSetupBody = SavedSetup.omit({ id: true, createdAt: true });

/** POST /api/import (writes var/backups/<ts>.json first) */
export const ImportBody = ExportDump;

/** POST /api/reset */
export const ResetBody = z.object({ confirm: z.literal("RESET") });

/** POST /api/coach/:runId/decide */
export const DecideBody = z.object({
  decision: Decision,
  alternativeIndex: z.number().int().min(0).optional(),
});

/** POST /api/coach/:runId/outcome */
export const OutcomeBody = z.object({
  outcome: Outcome,
  /** Run id the driver judged the change on, when logged. */
  runRef: z.string().optional(),
});

/** POST /api/llm/pull (SSE) */
export const PullBody = z.object({ model: z.string() });

/** POST /api/speak (macOS `say` fallback) */
export const SpeakBody = z.object({
  text: z.string(),
  voice: z.string().optional(),
});

export type CreateSessionBody = z.infer<typeof CreateSessionBody>;
export type PatchSessionBody = z.infer<typeof PatchSessionBody>;
export type ApplySetupBody = z.infer<typeof ApplySetupBody>;
export type AddRunBody = z.infer<typeof AddRunBody>;
export type PatchChangeBody = z.infer<typeof PatchChangeBody>;
export type SaveSetupBody = z.infer<typeof SaveSetupBody>;
export type ImportBody = z.infer<typeof ImportBody>;
export type ResetBody = z.infer<typeof ResetBody>;
export type DecideBody = z.infer<typeof DecideBody>;
export type OutcomeBody = z.infer<typeof OutcomeBody>;
export type PullBody = z.infer<typeof PullBody>;
export type SpeakBody = z.infer<typeof SpeakBody>;

// ---------- responses ----------

export interface HealthResponse {
  ok: true;
  version: string;
}

/** GET /api/meta */
export interface MetaResponse {
  car: z.infer<typeof CarId>;
  baselineRule: string;
  /** Sign conventions shown next to fields (camber, frontToe, droop, ...). */
  conventions: Record<string, string>;
  params: ParamDef[];
  symptoms: SymptomDef[];
  levers: LeverRow[];
  prechecks: PrecheckDef[];
  kbStats: KbStats;
}

/** GET /api/sessions/:id */
export interface SessionBundle {
  session: Session;
  runs: RunT[];
  changes: Change[];
  /** Every setup row referenced by the session (current, run setups, change before/after). */
  setups: Setup[];
}

export interface ApplySetupResponse {
  setup: Setup;
  changes: Change[];
}

export interface ImportResponse {
  ok: true;
  counts: Record<keyof ExportDumpT["tables"], number>;
}

export interface OkResponse {
  ok: true;
}

export interface WarmupResponse {
  ms: number;
}

/** Endpoint table: method + path -> request body and response. Used by the typed client. */
export interface Endpoints {
  "GET /api/health": { body: never; res: HealthResponse };
  "GET /api/meta": { body: never; res: MetaResponse };
  "GET /api/settings": { body: never; res: Settings };
  "PUT /api/settings": { body: SettingsPatchT; res: Settings };
  "POST /api/sessions": { body: CreateSessionBody; res: Session };
  "GET /api/sessions": { body: never; res: Session[] };
  "GET /api/sessions/:id": { body: never; res: SessionBundle };
  "PATCH /api/sessions/:id": { body: PatchSessionBody; res: Session };
  "POST /api/sessions/:id/setup": { body: ApplySetupBody; res: ApplySetupResponse };
  "POST /api/sessions/:id/runs": { body: AddRunBody; res: RunT };
  "PATCH /api/changes/:id": { body: PatchChangeBody; res: Change };
  "GET /api/saved": { body: never; res: SavedSetupT[] };
  "POST /api/saved": { body: SaveSetupBody; res: SavedSetupT };
  "DELETE /api/saved/:id": { body: never; res: OkResponse };
  "GET /api/export": { body: never; res: ExportDumpT };
  "POST /api/import": { body: ImportBody; res: ImportResponse };
  "POST /api/reset": { body: ResetBody; res: OkResponse };
  /** query: q, limit (default 3) */
  "GET /api/kb/search": { body: never; res: KbChunk[] };
  "GET /api/kb/chunk/:id": { body: never; res: KbChunk };
  /** SSE: see src/shared/events.ts (CoachEvent). */
  "POST /api/coach/turn": { body: CoachTurnInput; res: never };
  "POST /api/coach/:runId/decide": { body: DecideBody; res: TurnState };
  "POST /api/coach/:runId/outcome": { body: OutcomeBody; res: OutcomeResult };
  "GET /api/llm/status": { body: never; res: LlmStatus };
  /** SSE: see src/shared/events.ts (PullEvent). */
  "POST /api/llm/pull": { body: PullBody; res: never };
  "POST /api/llm/warmup": { body: never; res: WarmupResponse };
  /** query: sessionId */
  "GET /api/analysis/similar": { body: never; res: SimilarHit[] };
  /** query: runA, runB */
  "GET /api/analysis/compare": { body: never; res: RunComparison };
  "GET /api/analysis/history": { body: never; res: ParamHistoryRow[] };
  "POST /api/speak": { body: SpeakBody; res: OkResponse };
}

export type EndpointKey = keyof Endpoints;
