// TypeScript types inferred from the zod schemas in ./schemas.ts (the single source).
// FROZEN: only T0, T7 and T10 edit this file.
import type { z } from "zod";
import type * as S from "./schemas";

export type Grip = z.infer<typeof S.Grip>;
export type Phase = z.infer<typeof S.Phase>;
export type Outcome = z.infer<typeof S.Outcome>;
export type ParamValue = z.infer<typeof S.ParamValue>;
export type SetupValues = z.infer<typeof S.SetupValues>;
export type CarId = z.infer<typeof S.CarId>;
export type ExplainerId = z.infer<typeof S.ExplainerId>;
export type ParamGroup = z.infer<typeof S.ParamGroup>;

export type ParamDef = z.infer<typeof S.ParamDef>;
export type ParamsFile = z.infer<typeof S.ParamsFile>;
export type SymptomDef = z.infer<typeof S.SymptomDef>;
export type PrecheckDef = z.infer<typeof S.PrecheckDef>;
export type LeverRow = z.infer<typeof S.LeverRow>;

export type KbChunk = z.infer<typeof S.KbChunk>;
export type KbPage = z.infer<typeof S.KbPage>;
export type KbFile = z.infer<typeof S.KbFile>;
export type KbStats = z.infer<typeof S.KbStats>;

export type TrackConditions = z.infer<typeof S.TrackConditions>;
export type Setup = z.infer<typeof S.Setup>;
export type Session = z.infer<typeof S.Session>;
export type Rating = z.infer<typeof S.Rating>;
export type Run = z.infer<typeof S.Run>;
export type ChangeSource = z.infer<typeof S.ChangeSource>;
export type Change = z.infer<typeof S.Change>;
export type SavedSetup = z.infer<typeof S.SavedSetup>;

export type Settings = z.infer<typeof S.Settings>;
export type SettingsPatch = z.infer<typeof S.SettingsPatch>;

export type Classification = z.infer<typeof S.Classification>;
export type SceneBinding = z.infer<typeof S.SceneBinding>;
export type LeverSuggestion = z.infer<typeof S.LeverSuggestion>;
export type SkipReason = z.infer<typeof S.SkipReason>;
export type Suggestion = z.infer<typeof S.Suggestion>;
export type Refusal = z.infer<typeof S.Refusal>;
export type CoachTurnInput = z.infer<typeof S.CoachTurnInput>;
export type Explanation = z.infer<typeof S.Explanation>;
export type Decision = z.infer<typeof S.Decision>;
export type TurnStatus = z.infer<typeof S.TurnStatus>;
export type TurnState = z.infer<typeof S.TurnState>;
export type OutcomeResult = z.infer<typeof S.OutcomeResult>;

export type LlmStatus = z.infer<typeof S.LlmStatus>;
export type PullProgress = z.infer<typeof S.PullProgress>;

export type ParamDiff = z.infer<typeof S.ParamDiff>;
export type SimilarHit = z.infer<typeof S.SimilarHit>;
export type RunBundle = z.infer<typeof S.RunBundle>;
export type RunComparison = z.infer<typeof S.RunComparison>;
export type ParamHistoryRow = z.infer<typeof S.ParamHistoryRow>;

export type ExportDump = z.infer<typeof S.ExportDump>;
export type ApiError = z.infer<typeof S.ApiError>;
