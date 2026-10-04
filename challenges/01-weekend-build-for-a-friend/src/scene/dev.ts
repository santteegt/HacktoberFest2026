// Dev page for the scene (T5). Not linked from the app or included in the build.
// Open with: UI_PORT=5186 npx vite, then http://localhost:5186/src/scene/dev.html
import { ProceduralCarScene } from "./car-scene";
import { createCarScene, explainerFor } from "./index";
import type { SceneBinding, SceneView } from "./types";

const host = document.getElementById("host")!;
const statsEl = document.getElementById("stats")!;

// Sample bindings: realistic one-step changes inside the A.1 ranges.
const SAMPLES: [string, SceneBinding][] = [
  ["camber F 1.5→1.0", { explainer: "camber", param: "frontCamberDeg", from: 1.5, to: 1.0 }],
  ["camber R 2.5→3.0", { explainer: "camber", param: "rearCamberDeg", from: 2.5, to: 3.0 }],
  ["toe-out F 1.0→1.5", { explainer: "toe", param: "frontToeOutDeg", from: 1.0, to: 1.5 }],
  ["toe-in R 3.5→3.0", { explainer: "toe", param: "rearToeInDeg", from: 3.5, to: 3.0 }],
  ["caster 4→5", { explainer: "caster", param: "casterDeg", from: 4, to: 5 }],
  ["caster 4→2", { explainer: "caster", param: "casterDeg", from: 4, to: 2 }],
  ["ride F 5.0→5.4", { explainer: "rideHeight", param: "rideHeightFrontMm", from: 5.0, to: 5.4 }],
  ["ride R 5.0→5.8", { explainer: "rideHeight", param: "rideHeightRearMm", from: 5.0, to: 5.8 }],
  ["droop F 5.6→5.0", { explainer: "droop", param: "droopFrontGaugeMm", from: 5.6, to: 5.0 }],
  ["droop R 4.6→4.0", { explainer: "droop", param: "droopRearGaugeMm", from: 4.6, to: 4.0 }],
  ["shock F 3→5", { explainer: "shockAngle", param: "frontShockPos", from: 3, to: 5 }],
  ["shock F 3→1", { explainer: "shockAngle", param: "frontShockPos", from: 3, to: 1 }],
  ["shock R 2→3 (xo-rear-shocks-up)", { explainer: "shockAngle", param: "rearShockPos", from: 2, to: 3 }],
  ["arb F 1.3→1.5", { explainer: "arb", param: "frontArbMm", from: 1.3, to: 1.5 }],
  ["bump steer 1.0→2.0", { explainer: "bumpSteer", param: "bumpSteerShimMm", from: 1.0, to: 2.0 }],
  ["ackermann 0→1.0", { explainer: "ackermann", param: "ackermannShimMm", from: 0, to: 1.0 }],
  ["body 0→4", { explainer: "body", param: "bodyForwardMm", from: 0, to: 4 }],
  ["roll centre shim 0→3 (SVG)", { explainer: "rollCentre", param: "frontCamberLinkInnerShimMm", from: 0, to: 3 }],
  ["weight F 50→52 (SVG)", { explainer: "weight", param: "weightFrontPct", from: 50, to: 52 }],
  ["unknown param (fallback)", { explainer: "camber", param: "nope", from: 1, to: 2 }],
];

let scene = new ProceduralCarScene({ viewButtons: true });
scene.mount(host);
(window as unknown as { scene: ProceduralCarScene }).scene = scene;

const ex = document.getElementById("explainers")!;
for (const [label, b] of SAMPLES) {
  const btn = document.createElement("button");
  btn.textContent = label;
  btn.onclick = () => scene.showChange(b);
  ex.append(btn);
}

const ctl = document.getElementById("controls")!;
const add = (label: string, fn: () => void) => {
  const b = document.createElement("button");
  b.textContent = label;
  b.onclick = fn;
  ctl.append(b);
};
for (const v of ["front", "side", "top", "iso", "auto"] as SceneView[]) add(`view ${v}`, () => scene.setView(v));
add("highlight shocks", () => scene.highlight("frontShocks"));
add("highlight none", () => scene.highlight(null));
add("setPose stock", () => scene.setPose({ frontCamberDeg: 1.5, rearCamberDeg: 2.5, frontShockPos: 3, rearShockPos: 2 }));
add("remount (dispose test)", () => {
  scene.dispose();
  scene = new ProceduralCarScene({ viewButtons: true });
  scene.mount(host);
  (window as unknown as { scene: ProceduralCarScene }).scene = scene;
});
add("facade test", () => {
  // exercise the lazy facade used by src/ui/*
  scene.dispose();
  host.innerHTML = "";
  const f = createCarScene();
  f.setPose({ rearShockPos: 3 });
  f.showChange({ explainer: "shockAngle", param: "rearShockPos", from: 2, to: 3 });
  f.mount(host);
  console.log("[dev] explainerFor rearShockPos =", explainerFor("rearShockPos"), "fdr =", explainerFor("fdr"));
});

setInterval(() => {
  const s = scene.stats();
  statsEl.textContent =
    `frames=${s.frames} looping=${s.looping} lastFrameMs=${s.lastFrameMs.toFixed(2)} maxTweenFrameMs=${s.maxTweenFrameMs.toFixed(2)}\n` +
    `triangles=${s.triangles} drawCalls=${s.calls} geometries=${s.geometries} t=${new Date().toISOString()}`;
}, 500);
setInterval(() => console.log("[dev] frames", scene.stats().frames, new Date().toISOString()), 10000);
