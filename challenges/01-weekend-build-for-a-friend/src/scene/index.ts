// Scene entry points (T5). The three.js implementation is code-split: createCarScene() returns a light
// facade that loads ./car-scene on first mount and replays any calls made before it arrived.
import type { CarScene, CarSceneOptions, ExplainerId, PartId, SceneBinding, ScenePose, SceneView } from "./types";
import { explainerForParam } from "./params";

export type * from "./types";

type Call = (s: CarScene) => void;

export function createCarScene(opts: CarSceneOptions = {}): CarScene {
  let impl: CarScene | null = null;
  let queue: Call[] = [];
  let disposed = false;
  let loading = false;
  const run = (c: Call) => {
    if (disposed) return;
    if (impl) c(impl);
    else queue.push(c);
  };
  return {
    mount(el: HTMLElement) {
      if (disposed || loading || impl) return;
      loading = true;
      import("./car-scene")
        .then(({ ProceduralCarScene }) => {
          if (disposed) return;
          const s = new ProceduralCarScene(opts);
          s.mount(el);
          impl = s;
          const q = queue;
          queue = [];
          for (const c of q) c(s);
        })
        .catch((e) => console.warn("[scene] failed to load the 3D view", e));
    },
    setPose: (p: Partial<ScenePose>) => run((s) => s.setPose(p)),
    showChange: (b: SceneBinding, o?: { exaggerate?: number; ms?: number }) => run((s) => s.showChange(b, o)),
    setView: (v: SceneView) => run((s) => s.setView(v)),
    highlight: (p: PartId | null) => run((s) => s.highlight(p)),
    dispose() {
      if (disposed) return;
      disposed = true;
      queue = [];
      impl?.dispose();
      impl = null;
    },
  };
}

/** Explainer for a setup param id, or null when it has none in this build. */
export function explainerFor(param: string): ExplainerId | null {
  return explainerForParam(param);
}
