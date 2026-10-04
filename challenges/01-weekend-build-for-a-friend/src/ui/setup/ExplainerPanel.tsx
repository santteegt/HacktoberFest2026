// Right-hand explainer slot of the Setup editor (T4b). Renders T5's CarScene for params that have an explainer.
// Everything that touches src/scene is wrapped in try/catch: the scene module is a no-op stub until T5 lands.
import { useEffect, useRef, useState } from "preact/hooks";
import { createCarScene, explainerFor } from "../../scene";
import type { CarScene, SceneView, ScenePose } from "../../scene";
import type { ParamDef, ParamValue, SetupValues } from "../../shared/types";
import { conventionKey, formatValue } from "./logic";

const POSE_KEYS: (keyof ScenePose)[] = [
  "frontCamberDeg",
  "rearCamberDeg",
  "frontToeOutDeg",
  "rearToeInDeg",
  "casterDeg",
  "rideHeightFrontMm",
  "rideHeightRearMm",
  "droopFrontGaugeMm",
  "droopRearGaugeMm",
  "frontShockPos",
  "rearShockPos",
  "frontArbMm",
  "rearArbMm",
];

/** ScenePose fields are named like param ids, so the pose is a straight pick of the numeric values. */
export function poseFrom(values: SetupValues): Partial<ScenePose> {
  const pose: Partial<ScenePose> = {};
  for (const k of POSE_KEYS) {
    const v = values[k];
    if (typeof v === "number") (pose as Record<string, number>)[k] = v;
  }
  return pose;
}

const VIEWS: { v: SceneView; label: string }[] = [
  { v: "auto", label: "Auto" },
  { v: "front", label: "Front" },
  { v: "side", label: "Side" },
  { v: "top", label: "Top" },
  { v: "iso", label: "Iso" },
];

export interface ExplainerPanelProps {
  param: ParamDef | null;
  committed: SetupValues;
  effective: SetupValues;
  conventions: Record<string, string>;
  onClose: () => void;
}

export function ExplainerPanel({ param, committed, effective, conventions, onClose }: ExplainerPanelProps) {
  const host = useRef<HTMLDivElement>(null);
  const scene = useRef<CarScene | null>(null);
  const [view, setView] = useState<SceneView>("auto");
  const [sceneOk, setSceneOk] = useState(true);

  const explainer = param ? (param.explainer ?? safeExplainerFor(param.id)) : null;
  const from = param ? committed[param.id] : null;
  const to = param ? effective[param.id] : null;
  const pose = poseFrom(effective);
  const poseKey = JSON.stringify(pose);
  const hasScene = !!param && !!explainer;

  // Mount a scene whenever the host div exists (a param with an explainer is selected); it lives until the
  // panel goes back to "no param" or "no 3D view". T7 fix: the old mount ran once with [] while param was
  // still null, so the host div did not exist yet and no canvas was ever created.
  useEffect(() => {
    if (!hasScene || !host.current) return;
    let s: CarScene | null = null;
    try {
      s = createCarScene();
      s.mount(host.current);
      scene.current = s;
    } catch (e) {
      console.warn("explainer scene unavailable", e);
      setSceneOk(false);
    }
    return () => {
      try {
        s?.dispose();
      } catch {
        /* ignore */
      }
      if (scene.current === s) scene.current = null;
    };
  }, [hasScene]);

  useEffect(() => {
    const s = scene.current;
    if (!s || !param || !explainer) return;
    try {
      s.setPose(pose);
      if (typeof from === "number" && typeof to === "number" && from !== to) {
        s.showChange({ explainer, param: param.id, from, to });
      }
    } catch (e) {
      console.warn("explainer scene error", e);
      setSceneOk(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [param?.id, explainer, poseKey, from, to, hasScene]);

  useEffect(() => {
    try {
      scene.current?.setView(view);
    } catch {
      /* ignore */
    }
  }, [view, hasScene]);

  const key = param ? conventionKey(param.id) : null;
  const convention = key ? conventions[key] : undefined;

  return (
    <aside class="su-explainer" aria-label="Explainer">
      <div class="pc-row" style="justify-content:space-between">
        <h3>{param ? param.label : "Explainer"}</h3>
        <button type="button" class="pc-btn" onClick={onClose} aria-label="Close explainer">
          Close
        </button>
      </div>
      {!param && <p class="pc-muted">Tap the ? on a row, or a row with a car icon, to see what it moves on the car.</p>}
      {param && (
        <>
          <div ref={host} class="su-scene" data-active={explainer && sceneOk ? "1" : "0"} />
          {(!explainer || !sceneOk) && (
            <p class="pc-muted pc-small">
              {explainer
                ? "The 3D view is not available in this build; values and conventions below still apply."
                : "No 3D view for this setting."}
            </p>
          )}
          {explainer && sceneOk && (
            <div class="pc-chips" role="group" aria-label="Camera view">
              {VIEWS.map((o) => (
                <button key={o.v} type="button" class="pc-chip" aria-pressed={view === o.v} onClick={() => setView(o.v)}>
                  {o.label}
                </button>
              ))}
            </div>
          )}
          <p>
            <strong>Now:</strong> {formatValue(from as ParamValue, param.unit)}
            {from !== to && (
              <>
                {" "}
                <strong>Staged:</strong> <span style="color:var(--c-warn)">{formatValue(to as ParamValue, param.unit)}</span>
              </>
            )}
          </p>
          {convention && <p class="pc-small">{convention}</p>}
          <p class="pc-small pc-muted">Range source: {param.range}</p>
          {param.src.length > 0 && <p class="pc-small pc-muted">Notes: {param.src.join(", ")}</p>}
          <p class="pc-small pc-muted">Schematic, not to scale. Angles may be exaggerated.</p>
        </>
      )}
    </aside>
  );
}

function safeExplainerFor(id: string) {
  try {
    return explainerFor(id);
  } catch {
    return null;
  }
}
