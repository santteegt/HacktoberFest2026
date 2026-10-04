// Param id -> explainer, pose field and display metadata (T5).
// Ids, units and sign conventions mirror plan Appendix A.1 / data/params.bd12.json.
// Directions come only from the snapshot pages cited there; magnitudes on screen are schematic.
import type { ExplainerId, PartId, ScenePose, SceneView } from "./types";

export type PoseKey = Exclude<keyof ScenePose, "liftChassis">;

export interface ParamInfo {
  explainer: ExplainerId;
  pose: PoseKey;
  label: string;
  unit: string;
  end: "front" | "rear";
}

export const PARAMS: Record<string, ParamInfo> = {
  frontCamberDeg: { explainer: "camber", pose: "frontCamberDeg", label: "Front camber", unit: "deg neg", end: "front" },
  rearCamberDeg: { explainer: "camber", pose: "rearCamberDeg", label: "Rear camber", unit: "deg neg", end: "rear" },
  frontToeOutDeg: { explainer: "toe", pose: "frontToeOutDeg", label: "Front toe-out", unit: "deg", end: "front" },
  rearToeInDeg: { explainer: "toe", pose: "rearToeInDeg", label: "Rear toe-in", unit: "deg", end: "rear" },
  casterDeg: { explainer: "caster", pose: "casterDeg", label: "Caster", unit: "deg", end: "front" },
  rideHeightFrontMm: { explainer: "rideHeight", pose: "rideHeightFrontMm", label: "Ride height front", unit: "mm", end: "front" },
  rideHeightRearMm: { explainer: "rideHeight", pose: "rideHeightRearMm", label: "Ride height rear", unit: "mm", end: "rear" },
  droopFrontGaugeMm: { explainer: "droop", pose: "droopFrontGaugeMm", label: "Droop front (gauge)", unit: "mm", end: "front" },
  droopRearGaugeMm: { explainer: "droop", pose: "droopRearGaugeMm", label: "Droop rear (gauge)", unit: "mm", end: "rear" },
  frontShockPos: { explainer: "shockAngle", pose: "frontShockPos", label: "Front shock top hole", unit: "hole", end: "front" },
  rearShockPos: { explainer: "shockAngle", pose: "rearShockPos", label: "Rear shock position", unit: "pos", end: "rear" },
  frontArbMm: { explainer: "arb", pose: "frontArbMm", label: "Front anti-roll bar", unit: "mm", end: "front" },
  rearArbMm: { explainer: "arb", pose: "rearArbMm", label: "Rear anti-roll bar", unit: "mm", end: "rear" },
  bumpSteerShimMm: { explainer: "bumpSteer", pose: "bumpSteerShimMm", label: "Bump-steer shim", unit: "mm", end: "front" },
  ackermannShimMm: { explainer: "ackermann", pose: "ackermannShimMm", label: "Ackermann shim", unit: "mm", end: "front" },
  bodyForwardMm: { explainer: "body", pose: "bodyForwardMm", label: "Body shell forward offset", unit: "mm", end: "front" },
  frontCamberLinkInnerShimMm: { explainer: "rollCentre", pose: "frontCamberLinkInnerShimMm", label: "Front camber-link inner shim", unit: "mm", end: "front" },
  rearCamberLinkInnerShimMm: { explainer: "rollCentre", pose: "rearCamberLinkInnerShimMm", label: "Rear camber-link inner shim", unit: "mm", end: "rear" },
  weightFrontPct: { explainer: "weight", pose: "weightFrontPct", label: "Front weight", unit: "%", end: "front" },
};

/** Explainers that actually animate in this build (others fall back to a highlight and a note). */
export const SHIPPED: ReadonlySet<ExplainerId> = new Set<ExplainerId>([
  "camber",
  "toe",
  "caster",
  "rideHeight",
  "droop",
  "shockAngle",
  "arb",
  "bumpSteer",
  "ackermann",
  "body",
  "rollCentre", // SVG
  "weight", // SVG
]);

/** Default exaggeration per explainer (plan section 6 table). */
export const DEFAULT_EXAGGERATION: Record<ExplainerId, number> = {
  camber: 3,
  toe: 4,
  caster: 2,
  rideHeight: 4,
  droop: 4,
  shockAngle: 1.5,
  arb: 3,
  ackermann: 2,
  bumpSteer: 5,
  rollCentre: 1,
  weight: 1,
  body: 2,
};

/** What the exaggeration label calls the scaled quantity. */
export const EXAGGERATED_WHAT: Record<ExplainerId, string> = {
  camber: "Camber angles",
  toe: "Toe angles",
  caster: "Caster angles",
  rideHeight: "Heights",
  droop: "Travel",
  shockAngle: "Shock angles",
  arb: "Bar thickness and twist",
  ackermann: "Steering angles",
  bumpSteer: "Toe angles",
  rollCentre: "Link angles",
  weight: "Positions",
  body: "Shell offset",
};

export const DEFAULT_VIEW: Record<ExplainerId, SceneView> = {
  camber: "front",
  toe: "top",
  caster: "side",
  rideHeight: "side",
  droop: "side",
  shockAngle: "front",
  arb: "iso",
  ackermann: "top",
  bumpSteer: "front",
  rollCentre: "front",
  weight: "top",
  body: "side",
};

/** Parts highlighted (and ghosted) for a change. */
export function partsFor(explainer: ExplainerId, end: "front" | "rear"): PartId[] {
  const wheels: PartId = end === "front" ? "frontWheels" : "rearWheels";
  switch (explainer) {
    case "camber":
    case "toe":
    case "droop":
      return [wheels];
    case "caster":
      return ["kingpin"];
    case "rideHeight":
      return ["chassis"];
    case "shockAngle":
      return [end === "front" ? "frontShocks" : "rearShocks"];
    case "arb":
      return [end === "front" ? "frontArb" : "rearArb"];
    case "bumpSteer":
    case "ackermann":
      return ["steering", "frontWheels"];
    case "body":
      return ["body"];
    case "rollCentre":
      return ["camberLinks"];
    case "weight":
      return ["chassis"];
  }
}

/** Fallback param for a binding whose param id is unknown. */
export const FALLBACK_PARAM: Partial<Record<ExplainerId, string>> = {
  camber: "frontCamberDeg",
  toe: "frontToeOutDeg",
  caster: "casterDeg",
  rideHeight: "rideHeightFrontMm",
  droop: "droopFrontGaugeMm",
  shockAngle: "frontShockPos",
  arb: "frontArbMm",
  bumpSteer: "bumpSteerShimMm",
  ackermann: "ackermannShimMm",
  body: "bodyForwardMm",
  rollCentre: "frontCamberLinkInnerShimMm",
  weight: "weightFrontPct",
};

/** Explainer for a param id, or null. Only returns explainers that animate in this build. */
export function explainerForParam(param: string): ExplainerId | null {
  const info = PARAMS[param];
  return info && SHIPPED.has(info.explainer) ? info.explainer : null;
}
