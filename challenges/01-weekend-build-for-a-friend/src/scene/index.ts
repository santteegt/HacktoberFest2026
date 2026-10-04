// Scene entry points (T5). T0 stub: a no-op scene so the UI can bind to it before T5 lands.
import type { CarScene, ExplainerId } from "./types";

export type * from "./types";

export function createCarScene(): CarScene {
  return {
    mount() {},
    setPose() {},
    showChange() {},
    setView() {},
    highlight() {},
    dispose() {},
  };
}

/** Explainer for a setup param id, or null when it has none. T0 stub: always null. */
export function explainerFor(_param: string): ExplainerId | null {
  return null;
}
