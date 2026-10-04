// Scene API for the visual explainers (plan section 6; T5 owns src/scene/**).
// The LLM never emits scene values: a SceneBinding comes only from the server's
// LeverSuggestion.scene or from the Setup editor's own values.
import type { ExplainerId, SceneBinding } from "../shared/types";

export type { ExplainerId, SceneBinding };

export type SceneView = "front" | "side" | "top" | "iso" | "auto";

/** Highlightable parts of the schematic car. T5 may extend this list. */
export type PartId =
  | "chassis"
  | "frontWheels"
  | "rearWheels"
  | "frontShocks"
  | "rearShocks"
  | "frontArb"
  | "rearArb"
  | "steering"
  | "body"
  | "camberLinks"
  // T5 additions (additive):
  | "kingpin";

/** Sign conventions follow data/params.bd12.json (camber = degrees negative; droop gauge: lower = more droop; shock pos 1 = most laid down). */
export interface ScenePose {
  frontCamberDeg: number;
  rearCamberDeg: number;
  frontToeOutDeg: number;
  rearToeInDeg: number;
  casterDeg: number;
  rideHeightFrontMm: number;
  rideHeightRearMm: number;
  droopFrontGaugeMm: number;
  droopRearGaugeMm: number;
  frontShockPos: number;
  rearShockPos: number;
  frontArbMm: number;
  rearArbMm: number;
  steerDeg: number;
  compressionMm: number;
  liftChassis: boolean;
  // T5 additions (optional, additive): params with stretch explainers.
  ackermannShimMm?: number;
  bumpSteerShimMm?: number;
  bodyForwardMm?: number;
  frontCamberLinkInnerShimMm?: number;
  rearCamberLinkInnerShimMm?: number;
  weightFrontPct?: number;
}

/** Options for createCarScene (additive; all optional). */
export interface CarSceneOptions {
  /** Show the scene's own camera-preset buttons inside the canvas (default false: hosts usually render their own). */
  viewButtons?: boolean;
}

export interface CarScene {
  mount(el: HTMLElement): void;
  /** Immediate, no animation. */
  setPose(pose: Partial<ScenePose>): void;
  /** Ghost at `from`, solid lerps to `to`, highlights the part. */
  showChange(b: SceneBinding, opts?: { exaggerate?: number; ms?: number }): void;
  /** "auto" = the explainer's default view. */
  setView(v: SceneView): void;
  highlight(part: PartId | null): void;
  dispose(): void;
}
