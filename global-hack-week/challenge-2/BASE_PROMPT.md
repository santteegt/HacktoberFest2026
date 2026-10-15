## The prompt

You are drawing or modelling a **1/10 scale RC touring-car body shell for the FWD class**: a
modern compact **five-door hatchback** silhouette (short bonnet, long cabin, roof running almost
to the tail, steeply raked hatch), dressed as a touring-car racer with flared wheel arches, a
deep front splitter, side skirts, and a full-width rear wing on pylons. The shell is a thin,
hollow polycarbonate skin that covers the wheels: the wheels sit inside circular arch cut-outs
and are not part of the body.

### Coordinate frame and scale

- **X** runs nose to tail (nose at 0, tail at 1.0 of length L). **Y** runs across the car, centred
  on the centreline (half-width = 0.5 W). **Z** is up from the ground plane (0 at the ground).
- The body is **mirror-symmetric about the centreline** except for one detail noted below.
- Real dimensions: **W = 190 mm** (the class rule), **L ≈ 440 mm**, overall **H ≈ 125 mm** at the
  roof peak. Aspect ratios: **W / L = 0.43**, **H / L = 0.28**, **H / W = 0.66**.
- Wheels (for placement only): diameter **64 mm** (0.145 L, 0.51 H), width 26 mm, front axle at
  **x = 0.235 L**, rear axle at **x = 0.84 L** (axle spacing 0.60 L; the real chassis wheelbase is
  257–260 mm, the arch cut-outs are centred on these). Axle height 0.26 H. Track: the tyre's outer
  face sits flush with, or 1–2 mm inside, the arch flare at full width.
- Ground clearance of the shell: sills at **0.14 H**, splitter underside at **0.05 H**.

### Side profile (the silhouette, as a polyline of stations)

Read as (x as fraction of L, z as fraction of H). Join with smooth curves unless marked "sharp".

| Station | x | z | Note |
|---|---|---|---|
| Splitter leading edge | 0.00 | 0.05–0.10 | A flat plate ~0.02 L thick projecting ahead of the bumper; sharp |
| Bumper face, bottom | 0.03 | 0.10 | Vertical face rising from the splitter |
| Bumper face, top / grille | 0.03–0.05 | 0.30–0.45 | Nose rounds over here; near-vertical |
| Bonnet leading edge | 0.08 | 0.49 | Bumper top meets bonnet; a small step |
| Bonnet | 0.08 → 0.36 | 0.49 → 0.73 | Gently rising, slightly convex |
| Scuttle / windscreen base | 0.37 | 0.73 | Soft corner |
| Windscreen | 0.37 → 0.44 | 0.73 → 0.93 | About 55° from horizontal, slightly convex |
| Roof | 0.44 → 0.82 | 0.93 → 1.00 → 0.91 | One continuous arc; **peak at 0.60–0.66 L** |
| Hatch glass (rear window) | 0.82 → 0.93 | 0.91 → 0.66 | About 40° from horizontal; a small lip at its top edge |
| Hatch lower panel + lamps | 0.93 → 0.97 | 0.66 → 0.45 | Near vertical, lamps wrapping the corner |
| Rear bumper | 0.97 → 1.00 | 0.45 → 0.12 | Vertical face with a lower diffuser band; sharp bottom |
| Sill (both sides) | 0.12 → 0.90 | 0.14 | Straight line; a side-skirt lip ~0.02 H deep along it |

Other side-view lines:

- **Belt line** (bottom of the side glass): z = **0.64 H**, straight, from x = 0.40 to 0.93.
- **Side glass**: one continuous band between the belt line and the roof arc, from the A-pillar at
  x ≈ 0.40 to the C-pillar at x ≈ 0.83. It is divided by thin vertical bars into: front door
  glass 0.40–0.60 (with a small fixed triangular quarter-light at its front bottom corner by the
  A-pillar base); rear door glass 0.60–0.76; a fixed rear quarter glass 0.76–0.83 that tapers
  to a point at the C-pillar. The A-pillar is a thin raked band; the **C-pillar is thick** (0.03 L).
- **Door shut lines**: front wing / front door at x ≈ 0.35 (a vertical line from the belt line to
  the sill, sitting just behind the front arch); front / rear door at the B-pillar, x = 0.60;
  rear door's trailing edge at x ≈ 0.79 at the belt line, sweeping back and down around the
  front of the rear arch to the sill at x ≈ 0.72.
- **Door handles**: flush ovals, 0.04 L × 0.015 H, at z = 0.57 H, at the trailing edge of each
  door: x = 0.51 and x = 0.74.
- **No door mirrors** (an RC shell has none).
- **Shoulder crease**: a soft line from the front door handle running back and slightly up over
  the rear arch into the tail lamp.
- **Bonnet shut line**: from the top of the headlamp (x ≈ 0.10, z ≈ 0.52) sweeping back and up
  to the A-pillar base (x ≈ 0.37, z ≈ 0.72); the bonnet is a separate panel inset from the wings.
- **Wheel arches**: circular cut-outs centred on each axle, radius **0.085 L** (about 1.15 × the
  tyre radius) with a flared lip ~0.01 L wide; the sill line meets each arch at its lowest
  quarter. The arch is open at the bottom (the tyre's lower half shows below the body).
- **Front wing vent**: a shallow vertical slab/vent immediately behind the front arch,
  from the arch top down to the sill, at x = 0.33–0.36.
- **Rear quarter cap**: a small rounded square (0.025 L) on the rear quarter panel above the rear
  arch at x = 0.84, z = 0.63 — **on one side of the car only** in the blueprint (a fuel-filler
  cap on the donor car); mirror it or omit it.

### Plan view (widths, as half-width ratios of W, looking down with the nose to the left)

| Station | x | half-width | Note |
|---|---|---|---|
| Nose tip | 0.00 | 0.15 | A short flat centre to the bumper lip |
| Nose rounding | 0.00 → 0.12 | 0.15 → 0.50 | Nose rounds out to full width in 0.12 L; the lip/splitter outline runs ~0.01 W outside the bumper face |
| Front arches | 0.14 → 0.32 | 0.50 | Widest; the flare's crown is at the axle, x = 0.235 |
| Between the arches | 0.32 → 0.74 | 0.49 | Sides essentially **straight**, drawn in a lighter line (the sill seen from above); a very slight waist, no more than 0.01 W a side |
| Rear arches | 0.74 → 0.92 | 0.50 | Flare crown at the axle, x = 0.84 |
| Tail corners | 0.92 → 1.00 | 0.50 → 0.45 | Rounded, under the wing |
| Rear bumper rear face | 1.00 | 0.40 | Flat across the centre |

Top surfaces, from the nose:

- **Front bumper** (0.00–0.08): the outer lip is a double line around the nose. A small oval boss
  at the nose centre (badge / tow-hook position, 0.02 L). The **headlamps** are long swept lenses on
  the front corners, starting at the grille edge and sweeping back along the top of the wings to
  x ≈ 0.20, between the bonnet edge and the bumper lip.
- **Bonnet** (0.08–0.31): a separate panel, narrower than the car: half-width 0.36 W at its rounded
  leading edge, 0.42 W at its rear. Its rear edge (the scuttle) bows **rearward** in the middle.
  Two **slanted louvred vents**, one each side, out near the bonnet's edge in its front half:
  each a parallelogram slot from x = 0.12 to 0.24 with **four slats**, slanted so that its front
  end is nearer the centreline and its rear end nearer the side (angle ≈ 20° to the centreline).
- **Cowl** (0.31–0.37): a transverse band (wiper area) between the bonnet and the windscreen.
- **Windscreen** (0.37–0.44): a trapezoid, base half-width 0.42 W, top half-width 0.30 W.
- **Roof** (0.44–0.82): a long panel, half-width **0.235 W** (the roof island is just under half the
  car's width), nearly straight-sided, tapering slightly toward the rear. Outside it, the side
  glass shows as two foreshortened bands reaching to the body outline. Just behind the
  windscreen header there is a small centred **transverse rectangle** (0.03 L long × 0.27 W wide):
  a roof vent / antenna slot marker.
- **Hatch glass** (0.82–0.89): a rounded trapezoid narrowing rearward, half-width 0.30 → 0.27 W,
  with a visible D-pillar band each side. The **rear lamps** sit either side of the glass at its
  lower corners (x = 0.82–0.88), wrapping onto the quarter panels.
- **Rear wing** (0.89–0.96): a flat plank across **0.97 W** of span, chord **0.066 L**, with a
  rectangular **endplate** at each tip (0.08 L long × 0.03 W wide, i.e. slightly longer than the
  chord). On its top surface, **three small teardrop fins** at 25 %, 50 % and 75 % of the span,
  near the trailing edge.
- **Rear bumper** (0.96–1.00): rounded corners; the flat centre section carries the number-plate
  recess (seen in the rear view).

### Rear and three-quarter view (what the 3D form must show)

- The cabin is **tall and the glasshouse rounded**: the roof is domed across its width and the
  side glass tumbles inward (tumblehome ≈ 15°) from the belt line to the roof.
- The **hatch glass is strongly raked** (≈ 40°) and wide, with a slim **roof lip spoiler** at its
  top edge (the roof's trailing edge is thickened into a small lip that overhangs the glass by
  ~0.01 L).
- **Rear wing**: a single thick plank (thickness ≈ 1/7 of the chord), level, nearly full width,
  mounted on **two swept pylons** about a third of the span apart, centred, rising from the lower
  hatch panel (between the lamps, just above the number-plate recess) up and back to the wing's
  underside. The wing's **leading edge hangs over the lower half of the hatch glass** (x ≈ 0.89 to
  0.92 is over glass) and its trailing edge is at the tail (x ≈ 0.96). The endplates are
  rectangular, their top edge flush with the wing top and extending below the underside by
  about two wing thicknesses. The three small fins stand up from the top surface.
- **Tail lamps**: one each side, a two-lobe shape — an inner rounded triangle on the hatch
  panel and an outer swept lobe wrapping the corner onto the quarter panel, both at z ≈ 0.50–0.62 H.
- **Number-plate recess**: a landscape rectangle (0.25 W × 0.07 H) centred between the lamps
  at z ≈ 0.45 H.
- **Rear bumper**: a tall vertical face from the lamp line down to 0.12 H, with a horizontal
  step line across its lower third (the diffuser band) and a **vertical rectangular slot at
  each lower corner** (0.03 W × 0.12 H; exhaust / vent cut-outs).
- **Side skirts**: a flat lip running along the sills between the arches, flush with the body
  side, 0.02–0.03 W deep.
- **Front** (from a three-quarter front angle): a wide, low mouth — a lower rounded-rectangle
  intake across the bumper, a small slatted grille panel at the nose centre between the lamps
  (4–5 vertical slats), and the splitter plate projecting ahead and below.
- **Wheels** (reference only, not part of the shell): 10-spoke rims (five paired spokes), slick
  tyres; the arch lip covers the tyre's upper half.

### What makes it read as *this* body (check these before anything else)

1. **Hatchback stance**: short bonnet (0.28 L), the roof peaking **behind** the middle of the
   car (0.6 L) and running to a steep tail; no boot deck at all.
2. **Glass ring**: a long side-glass band divided into three panes, a thick C-pillar, and a wide
   raked hatch glass.
3. **Full-width rear wing on two pylons, over the hatch glass, with endplates and three fins**.
4. **Bonnet vents**: two slanted four-slat louvres in the bonnet's front half.
5. **Splitter under a tall, wide nose**; the bumper lip wraps round both front corners.
6. Flared arches on otherwise straight sides; sills with side-skirt lips.

### Suggested construction

- **2D (SVG / Canvas / sprite)**: build the side view from the station table as one closed path
  (cubic curves between stations), punch the two arch circles, then overlay the glass band,
  belt line, door and bonnet shut lines, handles, lamps, wing + endplate + pylons, splitter and
  skirt. Build the plan view from the half-width table mirrored about the centreline, then
  overlay bonnet (with vents), cowl, windscreen, roof island (with the rectangle), hatch glass,
  lamps, wing (with endplates and fins). For a top-down game sprite, the tells are the glass band
  around a roof island of ~0.47 W, the vents, the wing band across the tail with endplates, and
  front/rear value contrast (dark splitter lip and lamp dots at the nose).