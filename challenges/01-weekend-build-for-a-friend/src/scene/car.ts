// Procedural schematic touring car built from primitives (T5). Schematic, not to scale.
// New for this project: not derived from any earlier model. Units are millimetres.
// Frame: +y up, +z forward (front of car), +x = car's left. Ground is y = 0.
// Proportions from kb/source/yokomo-bd12.md: wheelbase ~261 mm, ~192 mm over the tyres,
// front shocks ~14-17 mm ahead of the front axle, rear shocks ~14-19 mm behind the rear axle,
// lower-arm inner hinges ~18-20 mm off centre and low, camber-link inner balls ~40 mm up.
import * as THREE from "three";
import type { ExplainerId, PartId, ScenePose } from "./types";

export const ACCENT = 0x7fb2ff;
const WHEELBASE = 261;
const HALF_WB = WHEELBASE / 2;
const TYRE_R = 32;
const TYRE_W = 24;
const WHEEL_X = 192 / 2 - TYRE_W / 2; // 84
const PLATE = { w: 96, l: 340, t: 2.5 };
const DEG = Math.PI / 180;

/** Visible lift when the "lift" toggle is on (droop check), display mm, not a setup value. */
const LIFT_MM = 40;

export const DEFAULT_POSE: Required<ScenePose> = {
  frontCamberDeg: 1.5, // BD12 factory (yokomo-bd12#factory-baseline-alignment)
  rearCamberDeg: 2.5,
  frontToeOutDeg: 1.0,
  rearToeInDeg: 3.5,
  casterDeg: 4, // generic baseline (touring-car-steering-geometry#caster)
  rideHeightFrontMm: 5.0,
  rideHeightRearMm: 5.0,
  droopFrontGaugeMm: 5.6, // generic gauge baselines (touring-car-setup-procedure#droop-baselines)
  droopRearGaugeMm: 4.6,
  frontShockPos: 3,
  rearShockPos: 2,
  frontArbMm: 1.3,
  rearArbMm: 1.2,
  steerDeg: 0,
  compressionMm: 0,
  liftChassis: false,
  ackermannShimMm: 0.5,
  bumpSteerShimMm: 1.0,
  bodyForwardMm: 0,
  frontCamberLinkInnerShimMm: 1.0, // no baseline in the snapshot: schematic mid value for the 2D diagram
  rearCamberLinkInnerShimMm: 1.0,
  weightFrontPct: 50, // generic target (touring-car-weight-balance#front-rear-target)
};

export const FRONT_HOLES = 5;
export const REAR_HOLES = 3;

/** Exaggeration factors per explainer; 1 = true value. */
export type Factors = Partial<Record<ExplainerId, number>>;

const BASE_COLORS: Record<PartId, number> = {
  chassis: 0x5c6878,
  frontWheels: 0x3a3f47,
  rearWheels: 0x3a3f47,
  frontShocks: 0xc8a24a,
  rearShocks: 0xc8a24a,
  frontArb: 0x9aa6b4,
  rearArb: 0x9aa6b4,
  steering: 0x9ca3ad,
  body: 0x9fb4c8,
  camberLinks: 0xa7b0bc,
  kingpin: 0xe6e9ee,
};

interface Corner {
  side: 1 | -1;
  front: boolean;
  zA: number;
  wheel: THREE.Group;
  upright: THREE.Group;
  armA: THREE.Mesh;
  armB: THREE.Mesh;
  camberLink: THREE.Mesh;
  shockBody: THREE.Mesh;
  shockShaft: THREE.Mesh;
  holes: THREE.Mesh[];
  arbLink: THREE.Mesh;
  tieRod?: THREE.Mesh;
  kingpin?: THREE.Mesh;
  kingpinRef?: THREE.Mesh;
  pivotMark?: THREE.Mesh;
  patchMark?: THREE.Mesh;
}

const UP = new THREE.Vector3(0, 1, 0);

export class SchematicCar {
  readonly root = new THREE.Group();
  readonly chassis = new THREE.Group();
  private corners: Corner[] = [];
  private frontHubs: THREE.Mesh[] = [];
  private rhMarks: THREE.Mesh[] = [];
  private deck: THREE.Mesh | null = null;
  private arbBars: { front: boolean; bar: THREE.Mesh; arms: THREE.Mesh[] }[] = [];
  private body!: THREE.LineSegments;
  private bodyMat: THREE.LineBasicMaterial | null = null;
  private materials = new Map<PartId, THREE.MeshLambertMaterial>();
  private ghostMat: THREE.MeshLambertMaterial | null = null;
  private geoms: THREE.BufferGeometry[] = [];
  private ownedMats: THREE.Material[] = [];
  private link: THREE.CylinderGeometry;
  private holeGeo: THREE.BoxGeometry;
  private sphereGeo: THREE.SphereGeometry;
  private tmpA = new THREE.Vector3();
  private tmpB = new THREE.Vector3();

  constructor(readonly ghost: boolean) {
    if (ghost) {
      this.ghostMat = new THREE.MeshLambertMaterial({ color: 0xdfe6ee, transparent: true, opacity: 0.35, depthWrite: false });
      this.ownedMats.push(this.ghostMat);
    }
    this.link = this.geo(new THREE.CylinderGeometry(1, 1, 1, 6, 1, true));
    this.holeGeo = this.geo(new THREE.BoxGeometry(3.2, 3.2, 4));
    this.sphereGeo = this.geo(new THREE.SphereGeometry(1, 8, 6));
    this.root.add(this.chassis);
    this.buildChassis();
    for (const front of [true, false]) for (const side of [1, -1] as const) this.corners.push(this.buildCorner(side, front));
    for (const front of [true, false]) this.buildArb(front);
    // ride-height gauge marks at the two measuring points (behind the front arm, in front of the rear arm)
    this.rhMarks = [this.mesh(this.link, "kingpin", this.root), this.mesh(this.link, "kingpin", this.root)];
    this.buildBody();
  }

  private holeMatShared: THREE.Material | null = null;
  private holeMat(): THREE.Material {
    if (this.ghost) return this.mat("chassis");
    if (!this.holeMatShared) {
      this.holeMatShared = new THREE.MeshLambertMaterial({ color: 0x20252c });
      this.ownedMats.push(this.holeMatShared);
    }
    return this.holeMatShared;
  }

  private geo<T extends THREE.BufferGeometry>(g: T): T {
    this.geoms.push(g);
    return g;
  }

  mat(part: PartId): THREE.MeshLambertMaterial {
    if (this.ghostMat) return this.ghostMat;
    let m = this.materials.get(part);
    if (!m) {
      // the steering axis is drawn on top of everything so it reads through the upright and tyre
      m = new THREE.MeshLambertMaterial({ color: BASE_COLORS[part], depthTest: part !== "kingpin" });
      this.materials.set(part, m);
      this.ownedMats.push(m);
    }
    return m;
  }

  private mesh(g: THREE.BufferGeometry, part: PartId, parent: THREE.Object3D): THREE.Mesh {
    const m = new THREE.Mesh(g, this.mat(part));
    m.userData.part = part;
    parent.add(m);
    return m;
  }

  private box(w: number, h: number, d: number, x: number, y: number, z: number, part: PartId, parent: THREE.Object3D) {
    const m = this.mesh(this.geo(new THREE.BoxGeometry(w, h, d)), part, parent);
    m.position.set(x, y, z);
    return m;
  }

  private buildChassis() {
    const c = this.chassis;
    // chassis plate (local y = 0 is the plate bottom)
    this.box(PLATE.w, PLATE.t, PLATE.l, 0, PLATE.t / 2, 0, "chassis", c);
    // top deck
    this.deck = this.box(36, 2, 250, 0, 30, 0, "chassis", c);
    for (const front of [true, false]) {
      const zA = front ? HALF_WB : -HALF_WB;
      // bulkhead block; camber-link inner balls sit on its top, ~40 mm up
      this.box(54, 36, 22, 0, PLATE.t + 18, zA, "chassis", c);
      // independent left/right shock towers
      const tz = front ? zA + 15 : zA - 16;
      for (const side of [1, -1]) this.box(38, 50, 3, side * 45, 31, tz, "chassis", c);
    }
  }

  private linkMesh(part: PartId, parent: THREE.Object3D = this.root) {
    return this.mesh(this.link, part, parent);
  }

  private buildCorner(side: 1 | -1, front: boolean): Corner {
    const zA = front ? HALF_WB : -HALF_WB;
    const wheel = new THREE.Group();
    wheel.rotation.order = "YZX";
    this.root.add(wheel);
    const wheelPart: PartId = front ? "frontWheels" : "rearWheels";
    const tyreGeo = this.geo(new THREE.CylinderGeometry(TYRE_R, TYRE_R, TYRE_W, 18));
    tyreGeo.rotateZ(Math.PI / 2);
    this.mesh(tyreGeo, wheelPart, wheel);
    // light hub face on the outside so camber and toe read clearly
    const hubGeo = this.geo(new THREE.CylinderGeometry(19, 19, 2, 10));
    hubGeo.rotateZ(Math.PI / 2);
    const hub = new THREE.Mesh(hubGeo, this.ghost ? this.mat(wheelPart) : this.mat("steering"));
    hub.userData.part = wheelPart;
    hub.position.x = side * (TYRE_W / 2 + 0.6);
    wheel.add(hub);
    if (front) this.frontHubs.push(hub);
    const upright = new THREE.Group();
    wheel.add(upright);
    const up = this.box(6, 30, 10, -side * 15, 1, 0, front ? "steering" : "chassis", upright);
    up.userData.part = wheelPart;
    const corner: Corner = {
      side,
      front,
      zA,
      wheel,
      upright,
      armA: this.linkMesh("chassis"),
      armB: this.linkMesh("chassis"),
      camberLink: this.linkMesh("camberLinks"),
      shockBody: this.linkMesh(front ? "frontShocks" : "rearShocks"),
      shockShaft: this.linkMesh(front ? "frontShocks" : "rearShocks"),
      holes: [],
      arbLink: this.linkMesh(front ? "frontArb" : "rearArb"),
    };
    const nHoles = front ? FRONT_HOLES : REAR_HOLES;
    for (let i = 0; i < nHoles; i++) {
      const h = new THREE.Mesh(this.holeGeo, this.holeMat());
      h.userData.part = front ? "frontShocks" : "rearShocks";
      this.chassis.add(h);
      corner.holes.push(h);
    }
    if (front) {
      corner.tieRod = this.linkMesh("steering");
      corner.kingpin = this.linkMesh("kingpin");
      corner.kingpinRef = this.linkMesh("chassis");
      corner.kingpin.renderOrder = 10;
      corner.pivotMark = this.mesh(this.sphereGeo, "kingpin", this.root);
      corner.pivotMark.renderOrder = 10;
      const patchMat = this.ghost ? this.mat("kingpin") : new THREE.MeshLambertMaterial({ color: 0xffa64d });
      if (!this.ghost) this.ownedMats.push(patchMat);
      corner.patchMark = new THREE.Mesh(this.sphereGeo, patchMat);
      corner.patchMark.userData.part = "kingpin";
      this.root.add(corner.patchMark);
    }
    return corner;
  }

  private buildArb(front: boolean) {
    const part: PartId = front ? "frontArb" : "rearArb";
    const bar = this.linkMesh(part, this.chassis);
    const arms = [this.linkMesh(part, this.chassis), this.linkMesh(part, this.chassis)];
    this.arbBars.push({ front, bar, arms });
  }

  private buildBody() {
    const g = new THREE.BoxGeometry(188, 46, 400, 1, 1, 2);
    const pos = g.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < pos.count; i++) {
      if (pos.getY(i) > 0) {
        pos.setX(i, pos.getX(i) * 0.7);
        pos.setZ(i, pos.getZ(i) * 0.62 - 20);
      }
    }
    const edges = this.geo(new THREE.EdgesGeometry(g, 1));
    g.dispose();
    const lip = new THREE.LineBasicMaterial({ color: BASE_COLORS.body, transparent: true, opacity: this.ghost ? 0.25 : 0.5 });
    this.ownedMats.push(lip);
    this.bodyMat = lip;
    this.body = new THREE.LineSegments(edges, lip);
    this.body.userData.part = "body";
    this.chassis.add(this.body);
  }

  /** Recompute every transform from a pose; factors scale the quantities of the active explainer. */
  layout(p: Required<ScenePose>, f: Factors) {
    const k = (e: ExplainerId) => f[e] ?? 1;
    const lift = p.liftChassis ? LIFT_MM : 0;
    const rhF = Math.max(0.5, p.rideHeightFrontMm * k("rideHeight") - p.compressionMm);
    const rhR = Math.max(0.5, p.rideHeightRearMm * k("rideHeight") - p.compressionMm);
    // ride height is measured near the axles, so pitch comes from the front/rear difference
    this.chassis.position.set(0, (rhF + rhR) / 2 + lift, 0);
    this.chassis.rotation.set(-Math.atan2(rhF - rhR, WHEELBASE), 0, 0);
    this.body.position.set(0, 8 + 23, p.bodyForwardMm * k("body"));
    this.chassis.updateMatrixWorld(true);

    for (const c of this.corners) {
      const { side, front, zA } = c;
      // droop: a LOWER gauge number means MORE travel (touring-car-setup-procedure#droop-baselines).
      // Travel magnitude here is schematic: 2 mm at the generic baseline gauge reading.
      let hang = 0;
      if (p.liftChassis) {
        const gauge = front ? p.droopFrontGaugeMm : p.droopRearGaugeMm;
        const base = front ? DEFAULT_POSE.droopFrontGaugeMm : DEFAULT_POSE.droopRearGaugeMm;
        const travel = Math.max(0.2, base - gauge + 2);
        hang = travel * k("droop");
      }
      // wheel centre: on the ground normally; when lifted it hangs below its ride-height position
      const yC = p.liftChassis ? TYRE_R + lift - hang : TYRE_R;
      c.wheel.position.set(side * WHEEL_X, yC, zA);
      // camber: stored as degrees NEGATIVE; top of the tyre leans in toward the chassis
      const camber = (front ? p.frontCamberDeg : p.rearCamberDeg) * k("camber");
      // toe: front toe-OUT (front of the wheel points out), rear toe-IN (points in)
      let yaw = front ? side * p.frontToeOutDeg * k("toe") : -side * p.rearToeInDeg * k("toe");
      if (front) {
        // steering: + = turning to the car's left (+x). Ackermann: the inner wheel steers more than the outer;
        // more rack shim = less Ackermann, wheels closer to parallel (touring-car-steering-geometry#ackermann-effect).
        // Magnitude schematic: 1.5 deg per wheel at 0 mm shim, 0 at the ~1.0 mm ceiling.
        if (p.steerDeg !== 0) {
          const ackHalf = Math.max(0, 1.0 - p.ackermannShimMm) * 1.5 * k("ackermann");
          yaw += p.steerDeg + Math.sign(p.steerDeg) * side * ackHalf;
        }
        // bump steer: toe-IN appears under compression; more outer-block shim = more of it
        // (touring-car-steering-geometry#bump-steer). Magnitude schematic: 0.4 deg per mm shim at 3 mm compression.
        if (p.compressionMm > 0) {
          const toeIn = p.bumpSteerShimMm * 0.4 * (p.compressionMm / 3) * k("bumpSteer");
          yaw -= side * toeIn;
        }
      }
      c.wheel.rotation.set(0, yaw * DEG, side * camber * DEG);
      // caster: steering axis tilted back (top toward the rear), pivot ahead of the contact patch
      // (touring-car-steering-geometry#caster)
      c.upright.rotation.set(front ? -p.casterDeg * k("caster") * DEG : 0, 0, 0);
      c.wheel.updateMatrixWorld(true);

      const lowerBall = c.upright.localToWorld(new THREE.Vector3(-side * 15, -12, 0));
      const upperBall = c.upright.localToWorld(new THREE.Vector3(-side * 15, 13, 0));
      const dz = front ? 15 : -16; // tower side of the axle
      const innerA = this.cw(side * 19, 4, zA + dz);
      const innerB = this.cw(side * 19, 4, zA - dz * 0.7);
      this.setLink(c.armA, innerA, lowerBall, 2);
      this.setLink(c.armB, innerB, lowerBall, 2);
      this.setLink(c.camberLink, this.cw(side * 24, 40, zA), upperBall, 1.4);

      // shocks: top between tower holes (1 = inner = most laid down ... n = outer = most upright)
      const n = front ? FRONT_HOLES : REAR_HOLES;
      const pos = Math.min(n, Math.max(1, front ? p.frontShockPos : p.rearShockPos));
      const span = 22 * k("shockAngle");
      const holeX = (i: number) => 45 + ((i - 1) / (n - 1) - 0.5) * span;
      const tz = zA + dz;
      c.holes.forEach((h, i) => h.position.set(side * holeX(i + 1), 52, tz + (front ? 2.2 : -2.2)));
      const top = this.cw(side * holeX(pos), 52, tz);
      const bottom = innerA.clone().lerp(lowerBall, 0.8);
      bottom.z = this.cw(0, 0, tz).z;
      const bodyEnd = top.clone().lerp(bottom, 0.55);
      this.setLink(c.shockBody, top, bodyEnd, 5);
      this.setLink(c.shockShaft, bodyEnd, bottom, 1.6);

      // anti-roll bar drop link to the lower arm (bar is underslung on the plate)
      const arbEnd = this.cw(side * 30, 4, zA + (front ? -30 : 30) + (front ? 22 : -22));
      this.setLink(c.arbLink, arbEnd, innerB.clone().lerp(lowerBall, 0.45), 1);

      if (front && c.tieRod && c.kingpin && c.kingpinRef && c.pivotMark && c.patchMark) {
        const arm = c.upright.localToWorld(new THREE.Vector3(-side * 13, 0, -17)); // steering arms trail the axle
        this.setLink(c.tieRod, this.cw(side * 22, 14, zA - 17), arm, 1.2);
        // kingpin axis through both balls, extended to the ground
        const dir = upperBall.clone().sub(lowerBall).normalize();
        const tGround = -lowerBall.y / dir.y;
        const ground = lowerBall.clone().addScaledVector(dir, tGround);
        const above = upperBall.clone().addScaledVector(dir, 14);
        this.setLink(c.kingpin, ground, above, 1.3);
        this.setLink(c.kingpinRef, new THREE.Vector3(ground.x, 0, ground.z), new THREE.Vector3(ground.x, above.y, ground.z), 0.4);
        c.pivotMark.position.copy(ground);
        c.pivotMark.scale.setScalar(3);
        const patch = c.wheel.localToWorld(new THREE.Vector3(0, -TYRE_R, 0));
        patch.y = 0;
        c.patchMark.position.copy(patch);
        c.patchMark.scale.setScalar(3);
      }
    }

    this.rhMarks.forEach((m, i) => {
      const z = i === 0 ? HALF_WB - 34 : -HALF_WB + 34;
      const top = this.cw(PLATE.w / 2 + 2, 0, z);
      this.setLink(m, new THREE.Vector3(top.x, 0, top.z), top, 1.2);
    });

    for (const a of this.arbBars) {
      const zA = a.front ? HALF_WB : -HALF_WB;
      const zBar = zA + (a.front ? -30 : 30);
      const r = (a.front ? p.frontArbMm : p.rearArbMm) * 0.5 * k("arb");
      this.setLink(a.bar, new THREE.Vector3(-30, 4, zBar), new THREE.Vector3(30, 4, zBar), r);
      a.arms.forEach((arm, i) => {
        const x = i === 0 ? -30 : 30;
        this.setLink(arm, new THREE.Vector3(x, 4, zBar), new THREE.Vector3(x, 4, zBar + (a.front ? 22 : -22)), r);
      });
    }
  }

  /** Chassis-local point to world. */
  private cw(x: number, y: number, z: number) {
    return this.chassis.localToWorld(new THREE.Vector3(x, y, z));
  }

  /** Place a unit cylinder between two points in its parent's frame (world for root, local for chassis). */
  private setLink(m: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3, r: number) {
    const d = this.tmpA.copy(b).sub(a);
    const len = Math.max(0.01, d.length());
    m.position.copy(this.tmpB.copy(a).add(b).multiplyScalar(0.5));
    m.quaternion.setFromUnitVectors(UP, d.normalize());
    m.scale.set(r, len, r);
  }

  /** Show only the given parts (ghost use); null shows everything. */
  showOnly(parts: PartId[] | null) {
    const set = parts ? new Set(parts) : null;
    this.root.traverse((o) => {
      const part = o.userData.part as PartId | undefined;
      if (!part) return;
      o.visible = !set || set.has(part);
    });
  }

  setBodyVisible(v: boolean) {
    this.body.visible = v;
  }

  /** The top deck hides the underslung anti-roll bars from above; the ARB explainer hides it. */
  setDeckVisible(v: boolean) {
    if (this.deck) this.deck.visible = v;
  }

  setRideMarks(v: boolean) {
    for (const m of this.rhMarks) m.visible = v;
  }

  setCasterMarkers(v: boolean) {
    for (const c of this.corners) {
      for (const m of [c.kingpin, c.kingpinRef, c.pivotMark, c.patchMark]) if (m) m.visible = v;
    }
  }

  /** Caster explainer: front tyres turn see-through so the steering axis inside the wheel is visible. */
  setFrontSeeThrough(v: boolean) {
    if (this.ghost) return;
    const m = this.mat("frontWheels");
    m.transparent = v;
    m.opacity = v ? 0.28 : 1;
    m.depthWrite = !v;
    m.needsUpdate = true;
    for (const h of this.frontHubs) h.visible = !v;
  }

  highlight(parts: PartId[]) {
    if (this.ghost) return;
    const set = new Set(parts);
    for (const [part, m] of this.materials) {
      m.color.setHex(set.has(part) ? ACCENT : BASE_COLORS[part]);
      m.emissive.setHex(set.has(part) ? 0x1a2a40 : 0x000000);
    }
    if (this.bodyMat) {
      this.bodyMat.color.setHex(set.has("body") ? ACCENT : BASE_COLORS.body);
      this.bodyMat.opacity = set.has("body") ? 0.9 : 0.5;
    }
  }

  triangles(): number {
    let t = 0;
    this.root.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh || !o.visible) return;
      const g = m.geometry;
      t += (g.index ? g.index.count : g.attributes.position.count) / 3;
    });
    return t;
  }

  dispose() {
    for (const g of this.geoms) g.dispose();
    for (const m of this.ownedMats) m.dispose();
    this.geoms = [];
    this.ownedMats = [];
    this.root.removeFromParent();
  }
}
