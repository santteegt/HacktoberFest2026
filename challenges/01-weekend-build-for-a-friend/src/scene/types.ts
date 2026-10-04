// The LLM never emits scene values. A lever row {param, from, to} drives the car model.

export interface ScenePose {
  frontCamberDeg: number;
  rearCamberDeg: number;
  frontToeDeg: number; // + = toe-in
  rearToeDeg: number;
  rideHeightMm: number;
  casterDeg: number;
  shockAngleDeg: number;
}

export interface CarScene {
  /** Animate from the current pose to `to`, exaggerating by `exaggerate` for legibility. */
  apply(to: Partial<ScenePose>, opts?: { exaggerate?: number; ms?: number }): void;
  highlight(param: keyof ScenePose | null): void;
  dispose(): void;
}
