// 2D SVG explainers drawn over the 3D canvas (T5): roll centre (front view) and weight balance (top view).
// Directions come from kb/source: touring-car-suspension-tuning.md (roll centre, camber-link inner shim)
// and touring-car-weight-balance.md (front/rear bias). The geometry is schematic, not BD12 measurements;
// no derived number (roll-centre height) is printed because it would be an invented magnitude.

const NS = "http://www.w3.org/2000/svg";
const ACCENT = "#7fb2ff";
const GHOST = "rgba(223,230,238,0.35)";
const INK = "#9aa6b4";

export type SvgKind = "rollCentre" | "weight";

function el<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number>, parent?: Element): SVGElementTagNameMap[K] {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  parent?.appendChild(e);
  return e;
}

interface Pt {
  x: number;
  y: number;
}

/** Schematic front-view suspension (mm, y up). More inner shim raises the inner camber-link ball. */
function rollGeometry(shimMm: number) {
  const patch: Pt = { x: 84, y: 0 };
  const armIn: Pt = { x: 20, y: 8 };
  const armOut: Pt = { x: 70, y: 10.5 };
  const linkIn: Pt = { x: 24, y: 28 + shimMm };
  const linkOut: Pt = { x: 68, y: 42 };
  const m1 = (armOut.y - armIn.y) / (armOut.x - armIn.x);
  const m2 = (linkOut.y - linkIn.y) / (linkOut.x - linkIn.x);
  let ic: Pt | null = null;
  if (Math.abs(m2 - m1) > 1e-4) {
    const x = (linkIn.y - armIn.y + m1 * armIn.x - m2 * linkIn.x) / (m1 - m2);
    ic = { x, y: armIn.y + m1 * (x - armIn.x) };
  }
  // roll centre: line from the contact patch through the instant centre, where it crosses the centreline
  let rc: number;
  if (ic) rc = patch.y + ((ic.y - patch.y) * (0 - patch.x)) / (ic.x - patch.x);
  else rc = patch.y + m1 * (0 - patch.x); // parallel links: line through the patch parallel to them
  return { patch, armIn, armOut, linkIn, linkOut, ic, rc };
}

export class SvgDiagrams {
  readonly root: SVGSVGElement;

  constructor(parent: HTMLElement) {
    this.root = el("svg", { class: "cs-svg", role: "img" });
    this.root.style.cssText = "position:absolute;inset:0;width:100%;height:100%;background:#0d1218;display:none";
    parent.appendChild(this.root);
  }

  hide() {
    this.root.style.display = "none";
  }

  /** Draw a diagram; `from` is the ghost state, `now` the animated current value. */
  draw(kind: SvgKind, from: number, now: number, end: "front" | "rear") {
    const svg = this.root;
    svg.style.display = "block";
    svg.replaceChildren();
    if (kind === "rollCentre") this.drawRoll(from, now, end);
    else this.drawWeight(from, now);
  }

  private drawRoll(from: number, now: number, end: "front" | "rear") {
    const svg = this.root;
    svg.setAttribute("viewBox", "-125 -78 250 104");
    svg.setAttribute("aria-label", `${end} roll centre, schematic front view`);
    const g = el("g", { transform: "scale(1,-1)" }, svg); // y up
    el("line", { x1: -125, y1: 0, x2: 125, y2: 0, stroke: "#2c3846", "stroke-width": 0.8 }, g);
    el("line", { x1: 0, y1: -6, x2: 0, y2: 60, stroke: "#2c3846", "stroke-width": 0.5, "stroke-dasharray": "2 2" }, g);
    // tyres and chassis
    for (const s of [1, -1]) el("rect", { x: s > 0 ? 72 : -96, y: 0, width: 24, height: 64, fill: "#3a3f47", rx: 3 }, g);
    el("rect", { x: -48, y: 5, width: 96, height: 2.5, fill: "#5c6878" }, g);
    el("rect", { x: -27, y: 7.5, width: 54, height: 22, fill: "#5c6878", opacity: 0.8 }, g);

    const drawState = (shim: number, color: string, width: number, construct: boolean) => {
      const k = rollGeometry(shim);
      for (const s of [1, -1]) {
        el("line", { x1: s * k.armIn.x, y1: k.armIn.y, x2: s * k.armOut.x, y2: k.armOut.y, stroke: INK, "stroke-width": 2 }, g);
        el("line", { x1: s * k.linkIn.x, y1: k.linkIn.y, x2: s * k.linkOut.x, y2: k.linkOut.y, stroke: color, "stroke-width": width }, g);
        el("circle", { cx: s * k.linkIn.x, cy: k.linkIn.y, r: 1.6, fill: color }, g);
      }
      if (construct && k.ic) {
        // construction lines on the right-hand side of the drawing only, to keep it readable
        const dash = { stroke: color, "stroke-width": 0.6, "stroke-dasharray": "3 2", fill: "none" };
        el("line", { x1: k.armOut.x, y1: k.armOut.y, x2: k.ic.x, y2: k.ic.y, ...dash }, g);
        el("line", { x1: k.linkOut.x, y1: k.linkOut.y, x2: k.ic.x, y2: k.ic.y, ...dash }, g);
        el("line", { x1: k.patch.x, y1: k.patch.y, x2: 0, y2: k.rc, ...dash }, g);
        if (k.ic.x > -125) el("circle", { cx: k.ic.x, cy: k.ic.y, r: 1.8, fill: color }, g);
      }
      el("circle", { cx: 0, cy: k.rc, r: construct ? 3 : 2.4, fill: construct ? color : "none", stroke: color, "stroke-width": 1 }, g);
      el("line", { x1: -10, y1: k.rc, x2: 10, y2: k.rc, stroke: color, "stroke-width": 1 }, g);
    };
    drawState(from, GHOST, 1.6, false);
    drawState(now, ACCENT, 2.2, true);
    const t = el("text", { x: 4, y: 12, fill: "#e8edf2", "font-size": 6 }, svg);
    t.textContent = "Roll centre (RC): where the patch-to-instant-centre line crosses the middle";
    const t2 = el("text", { x: 4, y: 21, fill: INK, "font-size": 5.5 }, svg);
    t2.textContent = "More inner shim = flatter camber link = lower RC, less camber gain";
    for (const tt of [t, t2]) tt.setAttribute("text-anchor", "middle");
    t.setAttribute("x", "0");
    t2.setAttribute("x", "0");
  }

  private drawWeight(from: number, now: number) {
    const svg = this.root;
    svg.setAttribute("viewBox", "-230 -200 460 400");
    svg.setAttribute("aria-label", "Front/rear weight balance, schematic top view");
    const L = 261;
    const zF = -L / 2; // screen y: front at the top
    const zR = L / 2;
    el("rect", { x: -48, y: -170, width: 96, height: 340, rx: 10, fill: "#2a323d", stroke: "#5c6878" }, svg);
    for (const y of [zF, zR]) for (const s of [1, -1]) el("rect", { x: s * 84 - 12, y: y - 32, width: 24, height: 64, rx: 4, fill: "#3a3f47" }, svg);
    // CG sits a fraction `front%` of the wheelbase forward of the rear axle
    const cgY = (pct: number) => zR - (L * pct) / 100;
    el("circle", { cx: 0, cy: cgY(from), r: 8, fill: "none", stroke: GHOST, "stroke-width": 2 }, svg);
    el("circle", { cx: 0, cy: cgY(now), r: 9, fill: ACCENT }, svg);
    el("line", { x1: -30, y1: cgY(now), x2: 30, y2: cgY(now), stroke: ACCENT, "stroke-width": 1.5 }, svg);
    // braking transfer arrow: weight pitches forward under braking
    el("path", { d: `M -150 50 L -150 -50 M -160 -36 L -150 -52 L -140 -36`, stroke: "#ffd27a", "stroke-width": 3, fill: "none" }, svg);
    const mk = (x: number, y: number, text: string, size = 13, fill = "#e8edf2", anchor = "start") => {
      const t = el("text", { x, y, fill, "font-size": size, "text-anchor": anchor }, svg);
      t.textContent = text;
    };
    const dp = Number.isInteger(now) ? 0 : 1;
    mk(108, zF + 5, `Front ${now.toFixed(dp)}%`, 17, ACCENT);
    mk(108, zR + 5, `Rear ${(100 - now).toFixed(dp)}%`, 17, ACCENT);
    mk(108, cgY(now) + 4, "CG", 13, ACCENT);
    mk(0, -182, "▲ front", 12, "#8b98a5", "middle");
    mk(-150, 72, "braking:", 12, "#ffd27a", "middle");
    mk(-150, 88, "ΔW = m·a·h / L", 12, "#ffd27a", "middle");
  }
}
