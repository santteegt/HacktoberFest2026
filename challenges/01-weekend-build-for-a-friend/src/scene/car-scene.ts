// three.js implementation of the CarScene API (T5). Loaded lazily by ./index.ts on first mount.
// Performance rules (plan section 6): one renderer per scene, pixel ratio <= 1.5, render on demand only
// (tweens and orbit drags), MeshLambertMaterial + one directional + one ambient light, no shadows,
// no post-processing, stop on visibilitychange, dispose everything on unmount.
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { DEFAULT_POSE, SchematicCar, type Factors } from "./car";
import { SvgDiagrams } from "./svg/diagrams";
import {
  DEFAULT_EXAGGERATION,
  DEFAULT_VIEW,
  EXAGGERATED_WHAT,
  FALLBACK_PARAM,
  PARAMS,
  SHIPPED,
  partsFor,
  type ParamInfo,
  type PoseKey,
} from "./params";
import type { CarScene, CarSceneOptions, ExplainerId, PartId, SceneBinding, ScenePose, SceneView } from "./types";

type Pose = Required<ScenePose>;
type CamView = Exclude<SceneView, "auto"> | "rear" | "casterClose" | "sideFront" | "sideRear" | "arbFront" | "arbRear" | "frontHigh";

interface Active {
  binding: SceneBinding;
  info: ParamInfo | null;
  factor: number;
  parts: PartId[];
  overrides: Partial<Pose>;
  animated: boolean;
}

const STYLE_ID = "car-scene-style";
const CSS = `
.cs-wrap{position:relative;width:100%;height:100%;min-height:220px;background:#0d1218;border-radius:10px;overflow:hidden;font:13px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif;color:#e8edf2}
.cs-wrap canvas{display:block;width:100%;height:100%;touch-action:none}
.cs-tl{position:absolute;left:8px;top:8px;display:flex;flex-direction:column;gap:4px;pointer-events:none;max-width:70%}
.cs-tag{background:rgba(15,20,25,.78);padding:2px 8px;border-radius:6px;width:fit-content}
.cs-exag{color:#ffd27a}
.cs-bl{position:absolute;left:8px;right:8px;bottom:8px;display:flex;gap:6px;align-items:flex-end;justify-content:space-between;pointer-events:none}
.cs-read{background:rgba(15,20,25,.82);padding:4px 8px;border-radius:6px;max-width:75%}
.cs-read b{color:#7fb2ff;font-weight:600}
.cs-btns{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;pointer-events:auto}
.cs-btn{min-height:44px;min-width:44px;padding:0 12px;border:0;border-radius:10px;background:rgba(26,34,43,.92);color:#e8edf2;font:inherit;cursor:pointer}
.cs-btn[aria-pressed="true"]{outline:2px solid #7fb2ff}
.cs-views{position:absolute;right:8px;top:8px;display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;max-width:55%}
.cs-small{font-size:11px}
.cs-small .cs-note{display:none}
.cs-msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:16px;text-align:center;color:#8b98a5}
`;

function fmt(v: number, decimals?: number): string {
  if (decimals !== undefined) return v.toFixed(decimals);
  return Number.isInteger(v) ? String(v) : String(Math.round(v * 100) / 100);
}

/** Decimals shared by a from/to pair so "1.5 -> 1.0" does not print as "1.5 -> 1". */
function pairDecimals(a: number, b: number): number {
  const d = (v: number) => (Number.isInteger(v) ? 0 : Math.min(2, String(Math.round(v * 100) / 100).split(".")[1]?.length ?? 0));
  return Math.max(d(a), d(b));
}

function ease(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export class ProceduralCarScene implements CarScene {
  /** Frames rendered since mount (dev page proves the loop stops when idle). */
  frames = 0;
  lastFrameMs = 0;
  maxTweenFrameMs = 0;

  private opts: CarSceneOptions;
  private el: HTMLElement | null = null;
  private wrap: HTMLDivElement | null = null;
  private renderer: THREE.WebGLRenderer | null = null;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(28, 1, 10, 4000);
  private controls: OrbitControls | null = null;
  private solid: SchematicCar | null = null;
  private ghost: SchematicCar | null = null;
  private grid: THREE.GridHelper | null = null;
  private svg: SvgDiagrams | null = null;
  private svgActive = false;
  private pose: Pose = { ...DEFAULT_POSE };
  private active: Active | null = null;
  private tween: { start: number; ms: number; key: PoseKey; from: number; to: number } | null = null;
  private viewMode: SceneView = "auto";
  private fit = 230;
  private raf = 0;
  private hidden = false;
  private disposed = false;
  private ro: ResizeObserver | null = null;
  private manualHighlight: PartId | null | undefined = undefined;
  private ui: { exag?: HTMLElement; read?: HTMLElement; note?: HTMLElement; lift?: HTMLButtonElement; replay?: HTMLButtonElement; views: HTMLButtonElement[] } = { views: [] };

  constructor(opts: CarSceneOptions = {}) {
    this.opts = opts;
  }

  mount(el: HTMLElement): void {
    if (this.disposed || this.el) return;
    this.el = el;
    if (!document.getElementById(STYLE_ID)) {
      const s = document.createElement("style");
      s.id = STYLE_ID;
      s.textContent = CSS;
      document.head.appendChild(s);
    }
    const wrap = document.createElement("div");
    wrap.className = "cs-wrap";
    this.wrap = wrap;
    el.appendChild(wrap);

    try {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "low-power" });
    } catch (e) {
      console.warn("[scene] WebGL unavailable", e);
      const msg = document.createElement("div");
      msg.className = "cs-msg";
      msg.textContent = "3D view unavailable on this browser (WebGL off). The values and notes still apply.";
      wrap.appendChild(msg);
      return;
    }
    const r = this.renderer;
    r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    r.setClearColor(0x0d1218, 1);
    wrap.appendChild(r.domElement);

    this.scene.add(new THREE.AmbientLight(0xffffff, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 2.0);
    sun.position.set(300, 600, 400);
    this.scene.add(sun);
    this.grid = new THREE.GridHelper(800, 16, 0x2c3846, 0x1b232c);
    this.scene.add(this.grid);

    this.solid = new SchematicCar(false);
    this.ghost = new SchematicCar(true);
    this.ghost.root.visible = false;
    this.scene.add(this.solid.root, this.ghost.root);

    const c = new OrbitControls(this.camera, r.domElement);
    c.enablePan = false;
    c.enableDamping = false; // damping needs a continuous loop; we render on demand
    c.minDistance = 120;
    c.maxDistance = 2400;
    c.maxPolarAngle = Math.PI * 0.495; // stay above the ground
    c.addEventListener("change", this.requestRender);
    this.controls = c;

    this.svg = new SvgDiagrams(wrap);
    this.buildOverlay(wrap);
    this.applyCamera(this.camViewFor());
    this.relayout();
    // compile both materials up front so the first ghost frame does not stall on shader compilation
    this.ghost.root.visible = true;
    r.compile(this.scene, this.camera);
    this.ghost.root.visible = false;
    this.refreshOverlay();

    this.ro = new ResizeObserver(this.resize);
    this.ro.observe(wrap);
    this.resize();
    document.addEventListener("visibilitychange", this.onVisibility);
    this.hidden = document.visibilityState === "hidden";
    this.requestRender();
  }

  setPose(pose: Partial<ScenePose>): void {
    if (this.disposed) return;
    for (const [k, v] of Object.entries(pose)) {
      if (k === "liftChassis") {
        if (typeof v === "boolean") this.pose.liftChassis = v;
      } else if (k in DEFAULT_POSE && typeof v === "number" && Number.isFinite(v)) {
        (this.pose as unknown as Record<string, number>)[k] = v;
      }
    }
    // A pose that moves the bound param away from the change's `to` makes the ghost stale: drop it.
    const a = this.active;
    if (a?.info) {
      const v = (pose as Record<string, unknown>)[a.info.pose];
      if (typeof v === "number" && v !== a.binding.to) this.clearActive();
    }
    this.tween = null;
    this.relayout();
    this.refreshOverlay();
    this.requestRender();
  }

  showChange(b: SceneBinding, opts: { exaggerate?: number; ms?: number } = {}): void {
    if (this.disposed) return;
    if (!b || !Number.isFinite(b.from) || !Number.isFinite(b.to)) return;
    const info = PARAMS[b.param] ?? (FALLBACK_PARAM[b.explainer] ? PARAMS[FALLBACK_PARAM[b.explainer]!] : undefined) ?? null;
    const explainer = b.explainer;
    const end = info?.end ?? "front";
    const parts = partsFor(explainer, end);
    const animated = SHIPPED.has(explainer) && !!info;
    const factor = Math.min(10, Math.max(1, opts.exaggerate ?? DEFAULT_EXAGGERATION[explainer] ?? 1));
    const overrides: Partial<Pose> = {};
    if (explainer === "droop") overrides.liftChassis = true;
    if (explainer === "bumpSteer") overrides.compressionMm = Math.max(this.pose.compressionMm, 3);
    if (explainer === "ackermann" && this.pose.steerDeg === 0) overrides.steerDeg = 27; // full lock 27-28 deg per side (setup procedure)
    this.active = { binding: b, info, factor: animated ? factor : 1, parts, overrides, animated };
    this.manualHighlight = undefined;

    if (animated && info) {
      this.pose[info.pose] = b.from;
      this.tween = { start: performance.now(), ms: Math.max(0, opts.ms ?? 600), key: info.pose, from: b.from, to: b.to };
    } else {
      this.tween = null;
    }
    if (this.viewMode === "auto") this.applyCamera(this.camViewFor());
    this.relayout();
    this.refreshOverlay();
    this.requestRender();
  }

  setView(v: SceneView): void {
    if (this.disposed) return;
    this.viewMode = v;
    this.applyCamera(this.camViewFor());
    this.refreshOverlay();
    this.requestRender();
  }

  highlight(part: PartId | null): void {
    if (this.disposed) return;
    this.manualHighlight = part;
    this.relayout();
    this.requestRender();
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    document.removeEventListener("visibilitychange", this.onVisibility);
    this.ro?.disconnect();
    this.controls?.removeEventListener("change", this.requestRender);
    this.controls?.dispose();
    this.solid?.dispose();
    this.ghost?.dispose();
    if (this.grid) {
      this.grid.geometry.dispose();
      (this.grid.material as THREE.Material).dispose();
    }
    this.scene.clear();
    this.renderer?.dispose();
    this.renderer?.domElement.remove();
    this.wrap?.remove();
    this.renderer = null;
    this.controls = null;
    this.solid = this.ghost = null;
    this.wrap = this.el = null;
  }

  /** Dev-page numbers. */
  stats() {
    return {
      frames: this.frames,
      lastFrameMs: this.lastFrameMs,
      maxTweenFrameMs: this.maxTweenFrameMs,
      looping: this.raf !== 0,
      triangles: this.renderer?.info.render.triangles ?? 0,
      calls: this.renderer?.info.render.calls ?? 0,
      geometries: this.renderer?.info.memory.geometries ?? 0,
    };
  }

  // ---- internals ----

  private factors(): Factors {
    const a = this.active;
    return a && a.animated ? { [a.binding.explainer]: a.factor } : {};
  }

  private solidPose(): Pose {
    return { ...this.pose, ...(this.active?.overrides ?? {}) };
  }

  private relayout() {
    if (!this.solid || !this.ghost) return;
    const a = this.active;
    const f = this.factors();
    const sp = this.solidPose();
    this.solid.layout(sp, f);
    const explainer = a?.binding.explainer ?? null;
    this.solid.setBodyVisible(explainer === null || explainer === "body");
    this.solid.setCasterMarkers(explainer === "caster");
    this.solid.setFrontSeeThrough(explainer === "caster");
    this.solid.setRideMarks(explainer === "rideHeight");
    this.solid.setDeckVisible(explainer !== "arb");
    const hl = this.manualHighlight !== undefined ? (this.manualHighlight ? [this.manualHighlight] : []) : (a?.parts ?? []);
    this.solid.highlight(hl);

    // 2D explainers draw an SVG over the canvas; the 3D frame is skipped while it is up
    const svgKind = explainer === "rollCentre" || explainer === "weight" ? explainer : null;
    this.svgActive = !!(svgKind && a?.info);
    if (svgKind && a?.info) this.svg?.draw(svgKind, a.binding.from, sp[a.info.pose] as number, a.info.end);
    else this.svg?.hide();

    if (a && a.animated && a.info && !svgKind) {
      this.ghost.root.visible = true;
      this.ghost.layout({ ...sp, [a.info.pose]: a.binding.from }, f);
      this.ghost.showOnly(a.parts);
      this.ghost.setBodyVisible(explainer === "body");
      this.ghost.setCasterMarkers(explainer === "caster");
      this.ghost.setRideMarks(false);
    } else {
      this.ghost.root.visible = false;
    }
  }

  private clearActive() {
    this.active = null;
    this.tween = null;
  }

  private camViewFor(): CamView {
    const a = this.active;
    if (this.viewMode !== "auto") {
      if (this.viewMode === "front" && a?.info?.end === "rear" && (a.binding.explainer === "shockAngle" || a.binding.explainer === "camber")) return "rear";
      return this.viewMode;
    }
    if (!a) return "iso";
    const e = a.binding.explainer;
    if (e === "caster") return "casterClose";
    if (e === "arb") return a.info?.end === "rear" ? "arbRear" : "arbFront";
    if (e === "bumpSteer") return "frontHigh";
    if (e === "rideHeight" || e === "droop") return a.info?.end === "rear" ? "sideRear" : "sideFront";
    const v = DEFAULT_VIEW[e];
    if (v === "front" && a.info?.end === "rear") return "rear";
    return v === "auto" ? "iso" : v;
  }

  private applyCamera(v: CamView) {
    const c = this.controls;
    const cam = this.camera;
    // direction (from target), target, and the radius of the region that must fit in the frame
    const presets: Record<CamView, { dir: [number, number, number]; target: [number, number, number]; r: number }> = {
      front: { dir: [0, 0.08, 1], target: [0, 30, 0], r: 112 },
      rear: { dir: [0, 0.08, -1], target: [0, 30, 0], r: 112 },
      side: { dir: [1, 0.08, 0], target: [0, 30, 0], r: 215 },
      top: { dir: [0, 1, -0.001], target: [0, 0, 0], r: 235 },
      iso: { dir: [0.62, 0.5, 0.68], target: [0, 18, 0], r: 230 },
      sideFront: { dir: [1, 0.06, 0], target: [0, 26, 85], r: 115 },
      sideRear: { dir: [1, 0.06, 0], target: [0, 26, -85], r: 115 },
      arbFront: { dir: [0.85, 0.8, -0.25], target: [0, 6, 108], r: 70 },
      arbRear: { dir: [0.85, 0.8, 0.25], target: [0, 6, -108], r: 70 },
      frontHigh: { dir: [0, 0.85, 0.55], target: [0, 18, 125], r: 115 },
      casterClose: { dir: [1, 0.05, 0], target: [60, 30, 130], r: 62 },
    };
    const p = presets[v];
    this.fit = p.r;
    const d = new THREE.Vector3(...p.dir).normalize();
    cam.position.set(p.target[0], p.target[1], p.target[2]).addScaledVector(d, this.fitDistance());
    if (c) {
      c.target.set(...p.target);
      c.update();
    } else cam.lookAt(...p.target);
  }

  /** Distance at which a sphere of radius `fit` fills the narrower of the two fields of view. */
  private fitDistance(): number {
    const vfov = this.camera.fov * THREE.MathUtils.DEG2RAD;
    const hfov = 2 * Math.atan(Math.tan(vfov / 2) * this.camera.aspect);
    return (this.fit / Math.sin(Math.min(vfov, hfov) / 2)) * 1.05;
  }

  private resize = () => {
    const r = this.renderer;
    const w = this.wrap;
    if (!r || !w) return;
    const width = Math.max(1, w.clientWidth);
    const height = Math.max(1, w.clientHeight);
    r.setSize(width, height, false);
    w.classList.toggle("cs-small", width < 460);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    // keep the framed region in view: move along the current view direction
    const c = this.controls;
    if (c) {
      const dir = this.camera.position.clone().sub(c.target).normalize();
      this.camera.position.copy(c.target).addScaledVector(dir, this.fitDistance());
      c.update();
    }
    this.requestRender();
  };

  private onVisibility = () => {
    this.hidden = document.visibilityState === "hidden";
    if (this.hidden) {
      if (this.raf) cancelAnimationFrame(this.raf);
      this.raf = 0;
    } else this.requestRender();
  };

  private requestRender = () => {
    if (this.raf || this.hidden || !this.renderer || this.disposed) return;
    this.raf = requestAnimationFrame(this.frame);
  };

  private frame = (now: number) => {
    this.raf = 0;
    const r = this.renderer;
    if (!r) return;
    const t0 = performance.now();
    const tw = this.tween;
    if (tw) {
      const t = tw.ms <= 0 ? 1 : Math.min(1, (now - tw.start) / tw.ms);
      this.pose[tw.key] = tw.from + (tw.to - tw.from) * ease(t);
      if (t >= 1) {
        this.pose[tw.key] = tw.to;
        this.tween = null;
      }
      this.relayout();
    }
    if (!this.svgActive) r.render(this.scene, this.camera);
    this.frames++;
    this.lastFrameMs = performance.now() - t0;
    if (tw) this.maxTweenFrameMs = Math.max(this.maxTweenFrameMs, this.lastFrameMs);
    if (this.tween) this.requestRender();
  };

  // ---- overlay ----

  private buildOverlay(wrap: HTMLElement) {
    const tl = document.createElement("div");
    tl.className = "cs-tl";
    const tag = document.createElement("div");
    tag.className = "cs-tag";
    tag.textContent = "Schematic, not to scale";
    const exag = document.createElement("div");
    exag.className = "cs-tag cs-exag";
    exag.setAttribute("data-testid", "exaggeration-label");
    tl.append(tag, exag);
    this.ui.exag = exag;

    const bl = document.createElement("div");
    bl.className = "cs-bl";
    const read = document.createElement("div");
    read.className = "cs-read";
    read.setAttribute("aria-live", "polite");
    this.ui.read = read;
    const btns = document.createElement("div");
    btns.className = "cs-btns";
    const replay = this.button("Replay", () => {
      const a = this.active;
      if (a?.animated) this.showChange(a.binding, { exaggerate: a.factor });
    });
    const lift = this.button("Lift car", () => {
      this.pose.liftChassis = !this.pose.liftChassis;
      if (this.active) delete this.active.overrides.liftChassis;
      this.relayout();
      this.refreshOverlay();
      this.requestRender();
    });
    this.ui.replay = replay;
    this.ui.lift = lift;
    btns.append(lift, replay);
    bl.append(read, btns);
    wrap.append(tl, bl);

    if (this.opts.viewButtons) {
      const views = document.createElement("div");
      views.className = "cs-views";
      for (const v of ["auto", "front", "side", "top", "iso"] as SceneView[]) {
        const b = this.button(v[0].toUpperCase() + v.slice(1), () => this.setView(v));
        b.dataset.view = v;
        views.append(b);
        this.ui.views.push(b);
      }
      wrap.append(views);
    }
  }

  private button(label: string, onClick: () => void): HTMLButtonElement {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "cs-btn";
    b.textContent = label;
    b.addEventListener("click", onClick);
    return b;
  }

  private refreshOverlay() {
    const a = this.active;
    const { exag, read, lift, replay } = this.ui;
    if (exag) {
      exag.textContent =
        a && a.animated
          ? `${EXAGGERATED_WHAT[a.binding.explainer]} exaggerated ×${fmt(a.factor)} for visibility`
          : "Angles exaggerated ×1 for visibility (true values)";
    }
    if (read) {
      if (!a) {
        read.textContent = "Pick a setting to see what it moves.";
      } else {
        const label = a.info?.label ?? a.binding.param;
        const unit = a.info?.unit ?? "";
        read.innerHTML = "";
        const head = document.createElement("div");
        const b = document.createElement("b");
        b.textContent = label;
        const dp = pairDecimals(a.binding.from, a.binding.to);
        head.append(b, document.createTextNode(`: ${fmt(a.binding.from, dp)} → ${fmt(a.binding.to, dp)} ${unit}`.trimEnd()));
        const sub = document.createElement("div");
        if (a.animated) {
          const note = document.createElement("span");
          note.className = "cs-note";
          note.textContent = ` ${this.noteFor(a.binding.explainer)}`;
          sub.append(document.createTextNode("Faint copy = before, blue = after."), note);
        } else sub.textContent = "No animation for this setting yet; the blue part is where it acts.";
        read.append(head, sub);
      }
    }
    const e = a?.binding.explainer;
    const lifted = this.solidPose().liftChassis;
    if (lift) {
      lift.hidden = !(e === "droop" || e === "rideHeight");
      lift.setAttribute("aria-pressed", String(lifted));
      lift.textContent = lifted ? "Set car down" : "Lift car";
    }
    if (replay) replay.hidden = !(a && a.animated);
    for (const b of this.ui.views) b.setAttribute("aria-pressed", String(b.dataset.view === this.viewMode));
  }

  private noteFor(e: ExplainerId): string {
    switch (e) {
      case "camber":
        return "Negative camber: top of the tyre leans in.";
      case "toe":
        return "Front toe-out points the wheel fronts out; rear toe-in points them in.";
      case "caster":
        return "Blue axis = steering axis, tilted back; where it meets the ground (blue dot) is ahead of the contact patch (orange dot).";
      case "rideHeight":
        return "Measured behind the front arm / in front of the rear arm. Reset droop after any change.";
      case "droop":
        return "Car lifted: a lower gauge number means more droop (more travel). Travel size is schematic.";
      case "shockAngle":
        return "Inner hole = laid down, outer hole = upright.";
      case "arb":
        return "Thicker bar = stiffer in roll.";
      case "bumpSteer":
        return "Suspension compressed: more shim adds toe-in under compression. Size is schematic.";
      case "ackermann":
        return "At lock the inner wheel steers more; more shim = closer to parallel. Size is schematic.";
      case "body":
        return "Shell forward = more front downforce and steering.";
      case "rollCentre":
        return "Raising the inner camber-link ball (more shim) flattens the link and lowers the roll centre. Geometry is schematic.";
      case "weight":
        return "Rearward bias: more weight pitches forward under braking (sharper turn-in). Forward bias calms entry.";
      default:
        return "";
    }
  }
}
