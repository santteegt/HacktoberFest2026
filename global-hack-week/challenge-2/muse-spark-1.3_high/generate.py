#!/usr/bin/env python3
"""Generate three-perspective 2D sprites for a 1/10 FWD touring-car body shell.

Reads nothing, needs nothing: Python 3 stdlib only (no pip installs).
Outputs (into this folder):
  side.svg / top.svg / rear.svg   - detailed vector sprites (master art)
  side.png / top.png / rear.png   - flat game-ready raster sprites (pure-python PNG encoder)
  preview.html                    - side-by-side viewer with spec checklist

Geometry source: ../BASE_PROMPT.md (station tables + plan-view table + rear-view spec)
Reference blueprints: ../schematics/*.jpg (Bittydesign CA45, ignored by git, not bundled)

Raster sprites use Pillow (the best-fit library for programmatic sprite work:
software drawing + export in one stable API), vendored under .deps/ so the
folder is self-contained. If Pillow is ever missing, the script falls back to
the built-in stdlib scanline renderer (same geometry, flat fills).

Real dims: L=440mm, W=190mm, H=125mm.  Nose at x=0, tail at x=1.
Model: Muse Spark 1.3, reasoning high (strength 256).
"""
import math
import os
import struct
import sys as _sys
import zlib
import binascii

sys_path_here = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir(os.path.join(sys_path_here, ".deps")) and os.path.join(sys_path_here, ".deps") not in _sys.path:
    _sys.path.insert(0, os.path.join(sys_path_here, ".deps"))
try:
    from PIL import Image, ImageDraw, ImageFont
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------- real dimensions (mm) ----------------
L, W, H = 440.0, 190.0, 125.0
XF = lambda xf: xf * L          # fraction of length -> mm
ZF = lambda zf: zf * H          # fraction of height -> mm
YF = lambda yf: yf * W          # fraction of width  -> mm (signed, centre 0)

AX_F, AX_R = 0.235, 0.84        # axle positions (fraction of L)
AX_Z = 0.26                     # axle height (fraction of H)
ARCH_R = 0.085 * L              # arch cut-out radius, mm (1.15x tyre radius)
TYRE_R = 32.0                   # 64mm diameter wheels
SILL_Z = 0.14 * H
SPLIT_Z = 0.05 * H

# ---------------- livery ----------------
BODY, BODY_D, BODY_L = "#1d5fd6", "#0e3079", "#6b9bf0"
INK = "#0d1526"
GLASS, GLASS_D = "#accdee", "#587da8"
ROOF = "#f3f6fc"
DARK = "#14171d"
YEL = "#ffd21f"
RED = "#e0244a"
LAMP_F = "#fdf3c0"
TYRE, RIM = "#22262d", "#ccd4e3"

# ================================================================= SIDE SVG ====
def side_svg():
    S, OX, GY = 1.8, 60.0, 300.0
    CW, CH = 920, 360
    X = lambda xf: OX + xf * L * S
    Z = lambda zf: GY - zf * H * S

    # --- top-run stations (nose -> tail), smoothed with Catmull-Rom ---
    top = [
        (0.000, 0.100), (0.030, 0.100), (0.040, 0.220), (0.045, 0.375),
        (0.060, 0.450), (0.080, 0.490), (0.150, 0.545), (0.220, 0.605),
        (0.300, 0.675), (0.360, 0.725), (0.370, 0.730), (0.390, 0.790),
        (0.405, 0.830), (0.440, 0.930), (0.480, 0.958), (0.530, 0.978),
        (0.580, 0.993), (0.630, 1.000), (0.680, 0.992), (0.730, 0.972),
        (0.780, 0.940), (0.820, 0.910), (0.860, 0.830), (0.890, 0.740),
        (0.930, 0.660), (0.950, 0.560), (0.970, 0.450), (0.985, 0.300),
        (1.000, 0.120),
    ]

    def catmull(pts):
        P = [(X(x), Z(z)) for x, z in pts]
        d = f"M {P[0][0]:.1f} {P[0][1]:.1f} "
        for i in range(len(P) - 1):
            p0 = P[max(0, i - 1)]
            p1 = P[i]
            p2 = P[i + 1]
            p3 = P[min(len(P) - 1, i + 2)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
            d += (f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} "
                  f"{p2[0]:.1f} {p2[1]:.1f} ")
        return d

    # arch / sill geometry in mm, then mapped
    ax_f, ax_r, ax_z = AX_F * L, AX_R * L, AX_Z * H
    sill = SILL_Z
    dx = math.sqrt(max(1.0, ARCH_R ** 2 - (ax_z - sill) ** 2))
    fL, fR = ax_f - dx, ax_f + dx
    rL, rR = ax_r - dx, ax_r + dx
    r = ARCH_R * S

    body_d = (catmull(top)
              + f"L {X(1.0):.1f} {Z(0.12):.1f} "
              + f"L {X(rR / L):.1f} {Z(sill / H):.1f} "
              + f"A {r:.1f} {r:.1f} 0 0 1 {X(rL / L):.1f} {Z(sill / H):.1f} "
              + f"L {X(fR / L):.1f} {Z(sill / H):.1f} "
              + f"A {r:.1f} {r:.1f} 0 0 1 {X(fL / L):.1f} {Z(sill / H):.1f} "
              + f"L {X(0.030):.1f} {Z(0.10):.1f} "
              + f"L {X(0.0):.1f} {Z(0.10):.1f} "
              + f"L {X(0.0):.1f} {Z(0.05):.1f} "
              + f"L {X(0.030):.1f} {Z(0.05):.1f} Z")

    # roof arc lookup for glass band (reuse smoothed top points, sample roof zone)
    def roof_z(xf):
        # piecewise-linear on the station list (roof zone only)
        for i in range(len(top) - 1):
            x0, z0 = top[i]
            x1, z1 = top[i + 1]
            if x0 <= xf <= x1 and x0 >= 0.43 and x1 <= 0.83:
                t = (xf - x0) / max(1e-9, (x1 - x0))
                return z0 + t * (z1 - z0)
        return 0.95

    belt = 0.64
    gx = [0.40, 0.46, 0.52, 0.58, 0.60, 0.66, 0.72, 0.76, 0.80, 0.83]
    glass_top = " ".join(f"L {X(x):.1f} {Z(roof_z(x) - 0.015):.1f}" for x in gx)
    glass_d = (f"M {X(0.40):.1f} {Z(belt):.1f} {glass_top} "
               f"L {X(0.83):.1f} {Z(belt):.1f} Z")

    def wheel(cx_mm, label):
        cx, cy = OX + cx_mm * S, GY - (AX_Z * H) * S
        rr = TYRE_R * S
        s = [f'<g id="{label}">',
             f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{TYRE}" stroke="{INK}" stroke-width="2"/>',
             f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr*0.62:.1f}" fill="{RIM}" stroke="{INK}" stroke-width="2"/>']
        for k in range(5):  # five paired spokes = 10 spokes
            for off in (-7, 7):
                a = math.radians(k * 72 + off)
                s.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + math.cos(a)*rr*0.58:.1f}" '
                         f'y2="{cy + math.sin(a)*rr*0.58:.1f}" stroke="#5b6472" stroke-width="4" stroke-linecap="round"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr*0.80:.1f}" fill="none" stroke="#8b95a7" stroke-width="1.5"/>')
        for k in range(5):  # lug dots around the hub
            a = math.radians(k * 72 + 36)
            s.append(f'<circle cx="{cx + math.cos(a)*rr*0.30:.1f}" cy="{cy + math.sin(a)*rr*0.30:.1f}" r="3" fill="#5b6472"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr*0.14:.1f}" fill="{INK}"/>')
        s.append('</g>')
        return "\n".join(s)

    # wing (side): plank + endplate + pylon
    wx0, wx1 = X(0.89), X(0.96)
    wy_top, wy_bot = Z(1.10), Z(1.055)
    pyl = (f"M {X(0.905):.1f} {Z(0.60):.1f} L {X(0.920):.1f} {Z(0.60):.1f} "
           f"L {X(0.945):.1f} {Z(1.055):.1f} L {X(0.930):.1f} {Z(1.055):.1f} Z")

    parts = [
        f'<ellipse cx="{X(0.5):.1f}" cy="{GY + 14:.1f}" rx="{L*S*0.48:.1f}" ry="12" fill="#0b1220" opacity="0.18"/>',
        f'<line x1="20" y1="{GY}" x2="{CW-20}" y2="{GY}" stroke="#94a3b8" stroke-width="1.5"/>',
        wheel(ax_f, "wheel-f"), wheel(ax_r, "wheel-r"),
        f'<path d="{body_d}" fill="url(#bodyG)" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>',
        # splitter plate + vertical end fence at its leading edge
        f'<rect x="{X(0.0):.1f}" y="{Z(0.10):.1f}" width="{(X(0.035)-X(0.0)):.1f}" height="{(Z(0.05)-Z(0.10)):.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{X(0.0):.1f}" y="{Z(0.13):.1f}" width="7" height="{(Z(0.05)-Z(0.13)):.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        # side skirt lip
        f'<rect x="{X(0.36):.1f}" y="{Z(sill/H):.1f}" width="{(X(0.70)-X(0.36)):.1f}" height="{0.02*H*S:.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.2"/>',
        # arch flare lips
        f'<path d="M {X(fL/L)-r*0.12:.1f} {Z(sill/H):.1f} A {r:.1f} {r:.1f} 0 0 1 {X(fR/L)+r*0.12:.1f} {Z(sill/H):.1f}" fill="none" stroke="{INK}" stroke-width="4" opacity="0.85"/>',
        f'<path d="M {X(rL/L)-r*0.12:.1f} {Z(sill/H):.1f} A {r:.1f} {r:.1f} 0 0 1 {X(rR/L)+r*0.12:.1f} {Z(sill/H):.1f}" fill="none" stroke="{INK}" stroke-width="4" opacity="0.85"/>',
        # glass band
        f'<path d="{glass_d}" fill="url(#glassG)" stroke="{INK}" stroke-width="2"/>',
        # quarter-light triangle at A-pillar base
        f'<path d="M {X(0.40):.1f} {Z(belt):.1f} L {X(0.445):.1f} {Z(belt):.1f} L {X(0.415):.1f} {Z(0.72):.1f} Z" fill="{GLASS_D}" stroke="{INK}" stroke-width="1.5"/>',
        # B-pillar + thick C-pillar
        f'<line x1="{X(0.60):.1f}" y1="{Z(roof_z(0.60)-0.015):.1f}" x2="{X(0.60):.1f}" y2="{Z(belt):.1f}" stroke="{INK}" stroke-width="2.5"/>',
        f'<line x1="{X(0.76):.1f}" y1="{Z(roof_z(0.76)-0.015):.1f}" x2="{X(0.76):.1f}" y2="{Z(belt):.1f}" stroke="{INK}" stroke-width="2"/>',
        f'<path d="M {X(0.795):.1f} {Z(roof_z(0.795)-0.015):.1f} L {X(0.825):.1f} {Z(roof_z(0.825)-0.015):.1f} L {X(0.83):.1f} {Z(belt):.1f} L {X(0.80):.1f} {Z(belt):.1f} Z" fill="{BODY_D}" stroke="{INK}" stroke-width="1.5"/>',
        # A-pillar band
        f'<line x1="{X(0.40):.1f}" y1="{Z(belt):.1f}" x2="{X(0.375):.1f}" y2="{Z(0.735):.1f}" stroke="{BODY_D}" stroke-width="5"/>',
        # belt line
        f'<line x1="{X(0.40):.1f}" y1="{Z(belt):.1f}" x2="{X(0.93):.1f}" y2="{Z(belt):.1f}" stroke="{INK}" stroke-width="2"/>',
        # door shut lines
        f'<line x1="{X(0.35):.1f}" y1="{Z(belt):.1f}" x2="{X(0.35):.1f}" y2="{Z(sill/H):.1f}" stroke="{INK}" stroke-width="1.5"/>',
        f'<line x1="{X(0.60):.1f}" y1="{Z(belt):.1f}" x2="{X(0.585):.1f}" y2="{Z(sill/H):.1f}" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {X(0.79):.1f} {Z(belt):.1f} C {X(0.77):.1f} {Z(0.45):.1f} {X(0.74):.1f} {Z(0.30):.1f} {X(0.72):.1f} {Z(sill/H):.1f}" fill="none" stroke="{INK}" stroke-width="1.5"/>',
        # handles (flush ovals 0.04L x 0.015H at z=0.57)
        f'<ellipse cx="{X(0.51):.1f}" cy="{Z(0.57):.1f}" rx="{0.02*L*S:.1f}" ry="{0.0075*H*S:.1f}" fill="{ROOF}" stroke="{INK}" stroke-width="1.5"/>',
        f'<ellipse cx="{X(0.74):.1f}" cy="{Z(0.57):.1f}" rx="{0.02*L*S:.1f}" ry="{0.0075*H*S:.1f}" fill="{ROOF}" stroke="{INK}" stroke-width="1.5"/>',
        # shoulder crease: handle -> tail lamp
        f'<path d="M {X(0.51):.1f} {Z(0.575):.1f} C {X(0.62):.1f} {Z(0.60):.1f} {X(0.75):.1f} {Z(0.585):.1f} {X(0.945):.1f} {Z(0.60):.1f}" fill="none" stroke="{YEL}" stroke-width="3" opacity="0.9"/>',
        # bonnet shut line
        f'<path d="M {X(0.10):.1f} {Z(0.52):.1f} C {X(0.20):.1f} {Z(0.55):.1f} {X(0.30):.1f} {Z(0.63):.1f} {X(0.37):.1f} {Z(0.72):.1f}" fill="none" stroke="{INK}" stroke-width="1.5"/>',
        # front wing vent: louvered slab with two slats, behind the front arch
        f'<rect x="{X(0.33):.1f}" y="{Z(0.52):.1f}" width="{(X(0.36)-X(0.33)):.1f}" height="{(Z(sill/H)-Z(0.52)):.1f}" rx="3" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        f'<line x1="{X(0.332):.1f}" y1="{Z(0.44):.1f}" x2="{X(0.358):.1f}" y2="{Z(0.44):.1f}" stroke="#8b95a7" stroke-width="2"/>',
        f'<line x1="{X(0.332):.1f}" y1="{Z(0.34):.1f}" x2="{X(0.358):.1f}" y2="{Z(0.34):.1f}" stroke="#8b95a7" stroke-width="2"/>',
        # fuel cap (ONE side only, per blueprint)
        f'<rect x="{X(0.84)-0.0125*L*S:.1f}" y="{Z(0.63)-0.0125*L*S:.1f}" width="{0.025*L*S:.1f}" height="{0.025*L*S:.1f}" rx="4" fill="{BODY_L}" stroke="{INK}" stroke-width="1.5"/>',
        # headlamp: long swept lens with pointed tip reaching back to x = 0.20
        f'<path d="M {X(0.04):.1f} {Z(0.42):.1f} L {X(0.20):.1f} {Z(0.505):.1f} L {X(0.195):.1f} {Z(0.55):.1f} L {X(0.05):.1f} {Z(0.49):.1f} Z" fill="{LAMP_F}" stroke="{INK}" stroke-width="1.5"/>',
        # tail lamp: larger, wrapping the corner with a pointed lead onto the quarter
        f'<path d="M {X(0.905):.1f} {Z(0.615):.1f} L {X(0.94):.1f} {Z(0.63):.1f} L {X(0.968):.1f} {Z(0.605):.1f} L {X(0.963):.1f} {Z(0.49):.1f} L {X(0.925):.1f} {Z(0.505):.1f} Z" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>',
        # number roundel (touring-car dress)
        f'<circle cx="{X(0.475):.1f}" cy="{Z(0.42):.1f}" r="17" fill="{ROOF}" stroke="{INK}" stroke-width="2"/>',
        f'<text x="{X(0.475):.1f}" y="{Z(0.42)+6:.1f}" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="18" fill="{INK}">45</text>',
        # wing pylon + plank + endplate + fin hint
        f'<path d="{pyl}" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{wx0:.1f}" y="{wy_top:.1f}" width="{wx1-wx0:.1f}" height="{wy_bot-wy_top:.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{wx0-5:.1f}" y="{wy_top:.1f}" width="12" height="{(wy_bot-wy_top)*4.5:.1f}" fill="{YEL}" stroke="{INK}" stroke-width="1.5"/>',
        f'<line x1="{(wx0+wx1)/2:.1f}" y1="{wy_top:.1f}" x2="{(wx0+wx1)/2:.1f}" y2="{wy_top-9:.1f}" stroke="{INK}" stroke-width="2.5"/>',
        # diffuser band + exhaust slot hint at tail
        f'<line x1="{X(0.965):.1f}" y1="{Z(0.22):.1f}" x2="{X(1.0):.1f}" y2="{Z(0.22):.1f}" stroke="{INK}" stroke-width="1.5"/>',
    ]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">'
           f'<title>1/10 FWD touring hatchback body shell - side view</title>'
           f'<defs><linearGradient id="bodyG" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{BODY_L}"/><stop offset="0.45" stop-color="{BODY}"/>'
           f'<stop offset="1" stop-color="{BODY_D}"/></linearGradient>'
           f'<linearGradient id="glassG" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="#d3e7fa"/><stop offset="1" stop-color="{GLASS_D}"/></linearGradient></defs>'
           f'<rect width="{CW}" height="{CH}" fill="none"/>' + "\n".join(parts) + '</svg>')
    return svg

# ================================================================== TOP SVG ====
def top_svg():
    S, OX, OY = 1.8, 60.0, 230.0
    CW, CH = 920, 460
    X = lambda xf: OX + xf * L * S
    Y = lambda yf: OY + yf * W * S  # yf signed half-width fraction

    def hw(xf):  # half-width ratio of W (plan table)
        if xf <= 0.0:
            return 0.15
        if xf <= 0.12:
            t = xf / 0.12
            s = t * t * (3 - 2 * t)
            return 0.15 + (0.50 - 0.15) * s
        if xf <= 0.32:
            return 0.50
        if xf <= 0.74:
            waist = 0.005 * math.sin(math.pi * (xf - 0.32) / 0.42)
            return 0.49 - waist
        if xf <= 0.92:
            return 0.50
        if xf <= 1.0:
            t = (xf - 0.92) / 0.08
            return 0.50 - 0.05 * t
        return 0.40

    xs = [i / 100 for i in range(0, 101)]
    right = [(X(x), Y(hw(x))) for x in xs]
    left = [(X(x), Y(-hw(x))) for x in reversed(xs)]
    outline = ("M " + " L ".join(f"{a:.1f} {b:.1f}" for a, b in right)
               + " L " + " L ".join(f"{a:.1f} {b:.1f}" for a, b in left) + " Z")
    # rear flat face (half-width 0.40 at x=1)
    rear_face = f"M {X(1.0):.1f} {Y(-0.40):.1f} L {X(1.0):.1f} {Y(0.40):.1f}"

    def trapezoid(x0, x1, hw0, hw1):
        return (f"M {X(x0):.1f} {Y(-hw0):.1f} L {X(x1):.1f} {Y(-hw1):.1f} "
                f"L {X(x1):.1f} {Y(hw1):.1f} L {X(x0):.1f} {Y(hw0):.1f} Z")

    # bonnet vents: parallelogram slots x=0.12-0.24, rear edge shifted
    # outward (~20 deg), four short slats each clipped inside the slot
    vents = []
    for side in (-1, 1):
        cx0, cx1 = X(0.12), X(0.24)
        spill = math.tan(math.radians(20)) * (cx1 - cx0) * 0.45
        yc = OY + side * 0.21 * W * S
        wdt = 0.055 * W * S
        yo = yc - side * wdt * 0.28
        slot = [(cx0, yo), (cx1, yo + side * spill),
                (cx1, yo + side * spill + 7), (cx0, yo + 7)]
        vents.append('<polygon points="{}" fill="{}" stroke="{}" stroke-width="1.5"/>'.format(
            " ".join(f"{a:.1f},{b:.1f}" for a, b in slot), DARK, INK))
        for k in range(4):  # four slats across the slot
            t = (k + 0.5) / 4
            xt = cx0 + t * (cx1 - cx0)
            yt = yo + side * spill * t
            vents.append(f'<line x1="{xt:.1f}" y1="{yt:.1f}" x2="{xt + 5:.1f}" '
                         f'y2="{yt + 7:.1f}" stroke="{RIM}" stroke-width="2"/>')

    # wing: chord 0.066L at x=0.89-0.96, span 0.97W, endplates 0.08L x 0.03W
    wing = trapezoid(0.89, 0.956, 0.485, 0.485)
    fins = []
    for f in (0.25, 0.50, 0.75):
        fx = X(0.945)
        fy = Y(-0.485 + f * 0.97)
        fins.append(f'<ellipse cx="{fx:.1f}" cy="{fy:.1f}" rx="10" ry="4" fill="{DARK}" stroke="{INK}" stroke-width="1"/>')

    parts = [
        f'<ellipse cx="{X(0.5):.1f}" cy="{OY:.1f}" rx="{L*S*0.49:.1f}" ry="{W*S*0.52:.1f}" fill="#0b1220" opacity="0.14"/>',
        f'<path d="{outline}" fill="url(#tBody)" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>',
        # splitter lip double line (~0.01W outside bumper)
        f'<path d="M {X(0.0)-8:.1f} {Y(-0.16):.1f} L {X(0.06):.1f} {Y(-0.51):.1f} L {X(0.12):.1f} {Y(-0.51):.1f}" fill="none" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {X(0.0)-8:.1f} {Y(0.16):.1f} L {X(0.06):.1f} {Y(0.51):.1f} L {X(0.12):.1f} {Y(0.51):.1f}" fill="none" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="{rear_face}" stroke="{INK}" stroke-width="2.5"/>',
        # headlamps: swept lenses to x~0.20
        f'<path d="M {X(0.045):.1f} {Y(-0.44):.1f} L {X(0.20):.1f} {Y(-0.40):.1f} L {X(0.20):.1f} {Y(-0.33):.1f} L {X(0.05):.1f} {Y(-0.36):.1f} Z" fill="{LAMP_F}" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {X(0.045):.1f} {Y(0.44):.1f} L {X(0.20):.1f} {Y(0.40):.1f} L {X(0.20):.1f} {Y(0.33):.1f} L {X(0.05):.1f} {Y(0.36):.1f} Z" fill="{LAMP_F}" stroke="{INK}" stroke-width="1.5"/>',
        # nose badge boss (oval 0.02L)
        f'<ellipse cx="{X(0.02):.1f}" cy="{OY:.1f}" rx="{0.01*L*S:.1f}" ry="6" fill="{BODY_L}" stroke="{INK}" stroke-width="1.5"/>',
        # bonnet panel (rear edge bows rearward in the middle)
        f'<path d="M {X(0.08):.1f} {Y(-0.36):.1f} L {X(0.08):.1f} {Y(0.36):.1f} L {X(0.31):.1f} {Y(0.42):.1f} Q {X(0.335):.1f} {OY:.1f} {X(0.31):.1f} {Y(-0.42):.1f} Z" fill="{BODY}" stroke="{INK}" stroke-width="2"/>',
        *vents,
        # cowl band
        f'<path d="{trapezoid(0.31, 0.37, 0.42, 0.42)}" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        # wiper hint
        f'<line x1="{X(0.335):.1f}" y1="{Y(-0.25):.1f}" x2="{X(0.36):.1f}" y2="{Y(0.05):.1f}" stroke="#8b95a7" stroke-width="2"/>',
        f'<line x1="{X(0.335):.1f}" y1="{Y(0.25):.1f}" x2="{X(0.36):.1f}" y2="{Y(-0.05):.1f}" stroke="#8b95a7" stroke-width="2"/>',
        # windscreen trapezoid
        f'<path d="{trapezoid(0.37, 0.44, 0.42, 0.30)}" fill="url(#tGlass)" stroke="{INK}" stroke-width="2"/>',
        # side glass bands (foreshortened, to body outline)
        f'<path d="M {X(0.44):.1f} {Y(-0.30):.1f} L {X(0.82):.1f} {Y(-0.235):.1f} L {X(0.82):.1f} {Y(-0.47):.1f} L {X(0.44):.1f} {Y(-0.47):.1f} Z" fill="url(#tGlass)" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {X(0.44):.1f} {Y(0.30):.1f} L {X(0.82):.1f} {Y(0.235):.1f} L {X(0.82):.1f} {Y(0.47):.1f} L {X(0.44):.1f} {Y(0.47):.1f} Z" fill="url(#tGlass)" stroke="{INK}" stroke-width="1.5"/>',
        # door shut ticks where the cuts meet the body side in plan
        *[f'<line x1="{X(sx):.1f}" y1="{Y(sgn*0.495):.1f}" x2="{X(sx):.1f}" y2="{Y(sgn*0.44):.1f}" stroke="{INK}" stroke-width="1.5"/>'
          for sx in (0.35, 0.60, 0.76) for sgn in (-1, 1)],
        # roof island (half-width 0.235)
        f'<path d="{trapezoid(0.44, 0.82, 0.235, 0.21)}" fill="{ROOF}" stroke="{INK}" stroke-width="2"/>',
        # roof vent / antenna slot marker (0.03L x 0.27W centred, behind header)
        f'<rect x="{X(0.47):.1f}" y="{Y(-0.135):.1f}" width="{0.03*L*S:.1f}" height="{0.27*W*S:.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.2"/>',
        # roof number
        f'<text x="{X(0.63):.1f}" y="{OY+8:.1f}" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="20" fill="{INK}">45</text>',
        # hatch glass rounded trapezoid + D-pillars
        f'<path d="{trapezoid(0.82, 0.89, 0.30, 0.27)}" fill="url(#tGlass)" stroke="{INK}" stroke-width="2"/>',
        # rear lamps either side of glass lower corners (x=0.82-0.88, wrapping)
        f'<rect x="{X(0.82):.1f}" y="{Y(-0.42):.1f}" width="{(X(0.88)-X(0.82)):.1f}" height="{0.10*W*S:.1f}" rx="4" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{X(0.82):.1f}" y="{Y(0.32):.1f}" width="{(X(0.88)-X(0.82)):.1f}" height="{0.10*W*S:.1f}" rx="4" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>',
        # hatch shut line: across below the glass + short runs up the D-pillars
        f'<line x1="{X(0.905):.1f}" y1="{Y(-0.33):.1f}" x2="{X(0.905):.1f}" y2="{Y(0.33):.1f}" stroke="{INK}" stroke-width="1.5"/>',
        f'<line x1="{X(0.905):.1f}" y1="{Y(-0.33):.1f}" x2="{X(0.86):.1f}" y2="{Y(-0.40):.1f}" stroke="{INK}" stroke-width="1.5"/>',
        f'<line x1="{X(0.905):.1f}" y1="{Y(0.33):.1f}" x2="{X(0.86):.1f}" y2="{Y(0.40):.1f}" stroke="{INK}" stroke-width="1.5"/>',
        # rear wing plank + endplates + fins
        f'<path d="{wing}" fill="{DARK}" stroke="{INK}" stroke-width="2"/>',
        f'<rect x="{X(0.885):.1f}" y="{Y(-0.515):.1f}" width="{0.08*L*S:.1f}" height="{0.03*W*S:.1f}" fill="{YEL}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{X(0.885):.1f}" y="{Y(0.485):.1f}" width="{0.08*L*S:.1f}" height="{0.03*W*S:.1f}" fill="{YEL}" stroke="{INK}" stroke-width="1.5"/>',
        *fins,
        # number-plate recess (dashed, on rear face)
        f'<rect x="{X(0.985):.1f}" y="{Y(-0.125):.1f}" width="10" height="{0.25*W*S:.1f}" fill="none" stroke="{INK}" stroke-width="1.2" stroke-dasharray="4 3"/>',
        # grille slats at nose centre
        *[
            f'<line x1="{X(0.035):.1f}" y1="{Y(-0.06 + k*0.03):.1f}" x2="{X(0.055):.1f}" y2="{Y(-0.06 + k*0.03):.1f}" stroke="{DARK}" stroke-width="2"/>'
            for k in range(5)
        ],
    ]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">'
           f'<title>1/10 FWD touring hatchback body shell - plan (top) view</title>'
           f'<defs><linearGradient id="tBody" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{BODY}"/><stop offset="0.5" stop-color="{BODY_L}"/>'
           f'<stop offset="1" stop-color="{BODY}"/></linearGradient>'
           f'<linearGradient id="tGlass" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="#c4dcf4"/><stop offset="1" stop-color="{GLASS_D}"/></linearGradient></defs>'
           + "\n".join(parts) + '</svg>')
    return svg

# ================================================================= REAR SVG ====
def rear_svg():
    S, CX, GY = 1.8, 240.0, 340.0
    CW, CH = 480, 420
    Y = lambda yf: CX + yf * W * S
    Z = lambda zf: GY - zf * H * S

    tl, tr = Y(-0.5), Y(0.5)  # full-width extremes
    parts = [
        f'<ellipse cx="{CX:.1f}" cy="{GY + 12:.1f}" rx="{W*S*0.48:.1f}" ry="10" fill="#0b1220" opacity="0.18"/>',
        # tyre hints at the bottom corners (reference only)
        f'<circle cx="{Y(-82/190):.1f}" cy="{GY - 0.26*H*S:.1f}" r="{TYRE_R*S:.1f}" fill="{TYRE}" stroke="{INK}" stroke-width="2"/>',
        f'<circle cx="{Y(82/190):.1f}" cy="{GY - 0.26*H*S:.1f}" r="{TYRE_R*S:.1f}" fill="{TYRE}" stroke="{INK}" stroke-width="2"/>',
        f'<circle cx="{Y(-82/190):.1f}" cy="{GY - 0.26*H*S:.1f}" r="{TYRE_R*S*0.6:.1f}" fill="{RIM}" stroke="{INK}" stroke-width="1.5"/>',
        f'<circle cx="{Y(82/190):.1f}" cy="{GY - 0.26*H*S:.1f}" r="{TYRE_R*S*0.6:.1f}" fill="{RIM}" stroke="{INK}" stroke-width="1.5"/>',
        # bumper mass: tall face lamp line -> 0.12H
        f'<path d="M {Y(-0.45):.1f} {Z(0.50):.1f} L {Y(0.45):.1f} {Z(0.50):.1f} L {Y(0.47):.1f} {Z(0.12):.1f} L {Y(-0.47):.1f} {Z(0.12):.1f} Z" fill="url(#rBody)" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>',
        # side glass tumblehome + cabin (tumblehome ~15deg)
        f'<path d="M {Y(-0.49):.1f} {Z(0.64):.1f} L {Y(-0.30):.1f} {Z(0.90):.1f} Q {CX:.1f} {Z(1.02):.1f} {Y(0.30):.1f} {Z(0.90):.1f} L {Y(0.49):.1f} {Z(0.64):.1f} L {Y(0.44):.1f} {Z(0.64):.1f} L {Y(0.27):.1f} {Z(0.88):.1f} Q {CX:.1f} {Z(0.97):.1f} {Y(-0.27):.1f} {Z(0.88):.1f} L {Y(-0.44):.1f} {Z(0.64):.1f} Z" fill="{BODY}" stroke="{INK}" stroke-width="2"/>',
        # hatch glass (wide, raked) + roof lip spoiler overhang
        f'<path d="M {Y(-0.26):.1f} {Z(0.66):.1f} L {Y(-0.28):.1f} {Z(0.875):.1f} Q {CX:.1f} {Z(0.93):.1f} {Y(0.28):.1f} {Z(0.875):.1f} L {Y(0.26):.1f} {Z(0.66):.1f} Z" fill="url(#rGlass)" stroke="{INK}" stroke-width="2"/>',
        f'<rect x="{Y(-0.30):.1f}" y="{Z(0.925):.1f}" width="{0.60*W*S:.1f}" height="7" rx="3" fill="{BODY_D}" stroke="{INK}" stroke-width="1.5"/>',
        # roof dome cap
        f'<path d="M {Y(-0.235):.1f} {Z(0.93):.1f} Q {CX:.1f} {Z(1.03):.1f} {Y(0.235):.1f} {Z(0.93):.1f} L {Y(0.235):.1f} {Z(0.90):.1f} Q {CX:.1f} {Z(0.99):.1f} {Y(-0.235):.1f} {Z(0.90):.1f} Z" fill="{ROOF}" stroke="{INK}" stroke-width="2"/>',
        # tail lamps: inner triangle + larger outer swept lobe, z 0.50-0.62
        f'<path d="M {Y(-0.20):.1f} {Z(0.56):.1f} L {Y(-0.08):.1f} {Z(0.60):.1f} L {Y(-0.10):.1f} {Z(0.51):.1f} Z" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {Y(-0.33):.1f} {Z(0.625):.1f} Q {Y(-0.455):.1f} {Z(0.605):.1f} {Y(-0.435):.1f} {Z(0.505):.1f} L {Y(-0.325):.1f} {Z(0.515):.1f} Z" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {Y(0.20):.1f} {Z(0.56):.1f} L {Y(0.08):.1f} {Z(0.60):.1f} L {Y(0.10):.1f} {Z(0.51):.1f} Z" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {Y(0.33):.1f} {Z(0.625):.1f} Q {Y(0.455):.1f} {Z(0.605):.1f} {Y(0.435):.1f} {Z(0.505):.1f} L {Y(0.325):.1f} {Z(0.515):.1f} Z" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>',
        # hatch shut lines: short verticals from the lamp bottoms to the bumper step
        f'<line x1="{Y(-0.20):.1f}" y1="{Z(0.50):.1f}" x2="{Y(-0.20):.1f}" y2="{Z(0.30):.1f}" stroke="{INK}" stroke-width="1.2"/>',
        f'<line x1="{Y(0.20):.1f}" y1="{Z(0.50):.1f}" x2="{Y(0.20):.1f}" y2="{Z(0.30):.1f}" stroke="{INK}" stroke-width="1.2"/>',
        # number-plate recess 0.25W x 0.07H at z~0.45
        f'<rect x="{Y(-0.125):.1f}" y="{Z(0.485):.1f}" width="{0.25*W*S:.1f}" height="{0.07*H*S:.1f}" rx="3" fill="{ROOF}" stroke="{INK}" stroke-width="1.8"/>',
        f'<text x="{CX:.1f}" y="{Z(0.485)+11:.1f}" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="11" fill="{INK}">CA-45</text>',
        # diffuser step line + strakes + corner slots 0.03W x 0.12H
        f'<line x1="{Y(-0.44):.1f}" y1="{Z(0.24):.1f}" x2="{Y(0.44):.1f}" y2="{Z(0.24):.1f}" stroke="{INK}" stroke-width="1.8"/>',
        f'<line x1="{Y(-0.15):.1f}" y1="{Z(0.235):.1f}" x2="{Y(-0.15):.1f}" y2="{Z(0.13):.1f}" stroke="{INK}" stroke-width="1.2"/>',
        f'<line x1="{Y(0.0):.1f}" y1="{Z(0.235):.1f}" x2="{Y(0.0):.1f}" y2="{Z(0.13):.1f}" stroke="{INK}" stroke-width="1.2"/>',
        f'<line x1="{Y(0.15):.1f}" y1="{Z(0.235):.1f}" x2="{Y(0.15):.1f}" y2="{Z(0.13):.1f}" stroke="{INK}" stroke-width="1.2"/>',
        f'<rect x="{Y(-0.45):.1f}" y="{Z(0.24):.1f}" width="{0.03*W*S:.1f}" height="{0.12*H*S:.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{Y(0.45)-0.03*W*S:.1f}" y="{Z(0.24):.1f}" width="{0.03*W*S:.1f}" height="{0.12*H*S:.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        # side-skirt lips at bottom corners
        f'<rect x="{Y(-0.50):.1f}" y="{GY-8:.1f}" width="{0.03*W*S:.1f}" height="8" fill="{DARK}" stroke="{INK}" stroke-width="1"/>',
        f'<rect x="{Y(0.50)-0.03*W*S:.1f}" y="{GY-8:.1f}" width="{0.03*W*S:.1f}" height="8" fill="{DARK}" stroke="{INK}" stroke-width="1"/>',
        # pylons (two, swept outward going up, third of span apart, centred)
        f'<path d="M {Y(-0.10):.1f} {Z(0.52):.1f} L {Y(-0.06):.1f} {Z(0.52):.1f} L {Y(-0.115):.1f} {Z(1.02):.1f} L {Y(-0.155):.1f} {Z(1.02):.1f} Z" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {Y(0.10):.1f} {Z(0.52):.1f} L {Y(0.06):.1f} {Z(0.52):.1f} L {Y(0.115):.1f} {Z(1.02):.1f} L {Y(0.155):.1f} {Z(1.02):.1f} Z" fill="{DARK}" stroke="{INK}" stroke-width="1.5"/>',
        # wing plank (span 0.97W, thickness 1/7 chord) + endplates + 3 fins
        f'<rect x="{Y(-0.485):.1f}" y="{Z(1.075):.1f}" width="{0.97*W*S:.1f}" height="{(0.066*L/7)*S:.1f}" fill="{DARK}" stroke="{INK}" stroke-width="1.8"/>',
        f'<rect x="{Y(-0.515):.1f}" y="{Z(1.075):.1f}" width="8" height="{(0.066*L/7)*S + 2*(0.066*L/7)*S:.1f}" fill="{YEL}" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{Y(0.515)-8:.1f}" y="{Z(1.075):.1f}" width="8" height="{(0.066*L/7)*S + 2*(0.066*L/7)*S:.1f}" fill="{YEL}" stroke="{INK}" stroke-width="1.5"/>',
        f'<path d="M {Y(-0.24):.1f} {Z(1.075):.1f} l 6 -10 l 6 10 Z" fill="{DARK}" stroke="{INK}" stroke-width="1.2"/>',
        f'<path d="M {Y(0.0)-6:.1f} {Z(1.075):.1f} l 6 -10 l 6 10 Z" fill="{DARK}" stroke="{INK}" stroke-width="1.2"/>',
        f'<path d="M {Y(0.24):.1f} {Z(1.075):.1f} l 6 -10 l 6 10 Z" fill="{DARK}" stroke="{INK}" stroke-width="1.2"/>',
    ]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">'
           f'<title>1/10 FWD touring hatchback body shell - rear view</title>'
           f'<defs><linearGradient id="rBody" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{BODY}"/><stop offset="1" stop-color="{BODY_D}"/></linearGradient>'
           f'<linearGradient id="rGlass" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="#c9e0f5"/><stop offset="1" stop-color="{GLASS_D}"/></linearGradient></defs>'
           + "\n".join(parts) + '</svg>')
    return svg

# ============================================================ PURE-PYTHON PNG ==
def _png_chunk(ctype, data):
    c = struct.pack(">I", len(data)) + ctype + data
    c += struct.pack(">I", binascii.crc32(ctype + data) & 0xFFFFFFFF)
    return c

def save_png(path, w, h, rgba):
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr)
           + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _png_chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)

class FB:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 4)

    @staticmethod
    def hex(c):
        c = c.lstrip("#")
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)

    def dot(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            r, g, b, a = c
            i = (y * self.w + x) * 4
            if a >= 255:
                self.px[i:i + 4] = bytes((r, g, b, 255))
            else:  # alpha blend over dst
                dr, dg, db, da = self.px[i], self.px[i + 1], self.px[i + 2], self.px[i + 3]
                t = a / 255.0
                self.px[i:i + 4] = bytes((int(r * t + dr * (1 - t)), int(g * t + dg * (1 - t)),
                                          int(b * t + db * (1 - t)), 255))

    def line(self, x0, y0, x1, y1, c, w=1):
        dx, dy = x1 - x0, y1 - y0
        n = int(max(abs(dx), abs(dy)) * 1.5) + 1
        rr = w / 2.0
        for i in range(n + 1):
            t = i / max(1, n)
            cx, cy = x0 + dx * t, y0 + dy * t
            for oy in range(int(-rr), int(rr) + 1):
                for ox in range(int(-rr), int(rr) + 1):
                    if ox * ox + oy * oy <= rr * rr + 0.5:
                        self.dot(cx + ox, cy + oy, c)

    def circle(self, cx, cy, r, c, fill=True):
        r = int(r)
        for y in range(int(cy) - r - 1, int(cy) + r + 2):
            for x in range(int(cx) - r - 1, int(cx) + r + 2):
                d = math.hypot(x - cx, y - cy)
                if fill and d <= r:
                    self.dot(x, y, c)
                elif not fill and abs(d - r) < 1.0:
                    self.dot(x, y, c)

    def poly(self, pts, c):
        ys = sorted(set(int(round(p[1])) for p in pts))
        n = len(pts)
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0 + 1e-12)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[i])), min(self.w, int(xs[i + 1]) + 1)):
                    self.dot(x, y, c)

    def save(self, path):
        save_png(path, self.w, self.h, self.px)

def png_side(path):
    S, OX, GY, CW, CH = 2.0, 40, 285, 920, 300
    X = lambda xf: OX + xf * L * S
    Z = lambda zf: GY - zf * H * S
    fb = FB(CW, CH)
    B = FB.hex(BODY); D = FB.hex(BODY_D); I = FB.hex(INK); G = FB.hex(GLASS)
    T = FB.hex(TYRE); R = FB.hex(RIM); DK = FB.hex(DARK); RD = FB.hex(RED)
    LF = FB.hex(LAMP_F); YW = FB.hex(YEL); RF = FB.hex(ROOF)
    ax_f, ax_r = X(AX_F), X(AX_R)
    wy = Z(AX_Z)
    for cx in (ax_f, ax_r):
        fb.circle(cx, wy, TYRE_R * S, T)
        fb.circle(cx, wy, TYRE_R * S * 0.62, R)
        for k in range(5):
            for off in (-8, 8):
                a = math.radians(k * 72 + off)
                fb.line(cx, wy, cx + math.cos(a) * TYRE_R * S * 0.58,
                        wy + math.sin(a) * TYRE_R * S * 0.58, FB.hex("#5b6472"), 3)
    body = [(X(0.0), Z(0.10)), (X(0.045), Z(0.375)), (X(0.08), Z(0.49)),
            (X(0.22), Z(0.605)), (X(0.36), Z(0.725)), (X(0.40), Z(0.815)),
            (X(0.44), Z(0.93)), (X(0.53), Z(0.978)), (X(0.63), Z(1.0)),
            (X(0.73), Z(0.972)), (X(0.82), Z(0.91)), (X(0.875), Z(0.785)),
            (X(0.93), Z(0.66)), (X(0.97), Z(0.45)), (X(1.0), Z(0.12)),
            (X(0.918), Z(0.14)), (X(0.86), Z(0.42)), (X(0.84), Z(0.555)),
            (X(0.82), Z(0.42)), (X(0.762), Z(0.14)), (X(0.313), Z(0.14)),
            (X(0.26), Z(0.40)), (X(0.235), Z(0.53)), (X(0.21), Z(0.40)),
            (X(0.157), Z(0.14)), (X(0.03), Z(0.10))]
    fb.poly(body, B)
    fb.poly([(X(0.40), Z(0.64)), (X(0.44), Z(0.925)), (X(0.63), Z(0.995)),
             (X(0.82), Z(0.905)), (X(0.83), Z(0.64))], G)
    fb.line(X(0.60), Z(0.97), X(0.60), Z(0.64), I, 2)
    fb.poly([(X(0.795), Z(0.945)), (X(0.825), Z(0.92)), (X(0.83), Z(0.64)),
             (X(0.795), Z(0.64))], D)
    fb.line(X(0.40), Z(0.64), X(0.93), Z(0.64), I, 2)
    fb.poly([(X(0.08), Z(0.49)), (X(0.08), Z(0.42)), (X(0.31), Z(0.63)),
             (X(0.31), Z(0.70))], D)
    fb.poly([(X(0.0), Z(0.10)), (X(0.035), Z(0.10)), (X(0.035), Z(0.05)),
             (X(0.0), Z(0.05))], DK)
    fb.poly([(X(0.36), Z(0.14)), (X(0.70), Z(0.14)), (X(0.70), Z(0.12)),
             (X(0.36), Z(0.12))], DK)
    fb.poly([(X(0.33), Z(0.52)), (X(0.36), Z(0.52)), (X(0.36), Z(0.14)),
             (X(0.33), Z(0.14))], DK)
    fb.poly([(X(0.84) - 11, Z(0.63) - 11), (X(0.84) + 11, Z(0.63) - 11),
             (X(0.84) + 11, Z(0.63) + 11), (X(0.84) - 11, Z(0.63) + 11)],
            FB.hex("#6b9bf0"))
    fb.poly([(X(0.035), Z(0.50)), (X(0.12), Z(0.545)), (X(0.115), Z(0.49)),
             (X(0.035), Z(0.45))], LF)
    fb.poly([(X(0.925), Z(0.62)), (X(0.965), Z(0.60)), (X(0.96), Z(0.50)),
             (X(0.925), Z(0.52))], RD)
    for k in range(2):
        fb.circle(X(0.12 + k * 0.05), Z(0.60 - k * 0.02), 4, DK)
    fb.poly([(X(0.905), Z(0.60)), (X(0.92), Z(0.60)), (X(0.945), Z(1.055)),
             (X(0.93), Z(1.055))], DK)
    fb.poly([(X(0.89), Z(1.10)), (X(0.96), Z(1.10)), (X(0.96), Z(1.055)),
             (X(0.89), Z(1.055))], DK)
    fb.poly([(X(0.888), Z(1.13)), (X(0.896), Z(1.13)), (X(0.896), Z(1.03)),
             (X(0.888), Z(1.03))], YW)
    fb.circle(X(0.475), Z(0.42), 15, RF)
    fb.circle(X(0.475), Z(0.42), 15, I, fill=False)
    n = len(body)
    for i in range(n):
        fb.line(body[i][0], body[i][1], body[(i + 1) % n][0], body[(i + 1) % n][1], I, 2)
    fb.save(path)

def png_top(path):
    S, OX, OY, CW, CH = 2.0, 30, 210, 920, 420
    X = lambda xf: OX + xf * L * S
    Y = lambda yf: OY + yf * W * S
    fb = FB(CW, CH)
    B = FB.hex(BODY); I = FB.hex(INK); G = FB.hex(GLASS); DK = FB.hex(DARK)
    RF = FB.hex(ROOF); RD = FB.hex(RED); LF = FB.hex(LAMP_F); YW = FB.hex(YEL)

    def hw(xf):
        if xf <= 0.0:
            return 0.15
        if xf <= 0.12:
            t = xf / 0.12
            return 0.15 + 0.35 * t * t * (3 - 2 * t)
        if xf <= 0.32:
            return 0.50
        if xf <= 0.74:
            return 0.49 - 0.005 * math.sin(math.pi * (xf - 0.32) / 0.42)
        if xf <= 0.92:
            return 0.50
        return max(0.40, 0.50 - 0.05 * (xf - 0.92) / 0.08)
    xs = [i / 50 for i in range(51)]
    fb.poly([(X(x), Y(hw(x))) for x in xs] + [(X(x), Y(-hw(x))) for x in reversed(xs)], B)
    fb.poly([(X(0.44), Y(0.30)), (X(0.82), Y(0.235)), (X(0.82), Y(0.47)),
             (X(0.44), Y(0.47))], G)
    fb.poly([(X(0.44), Y(-0.30)), (X(0.82), Y(-0.235)), (X(0.82), Y(-0.47)),
             (X(0.44), Y(-0.47))], G)
    fb.poly([(X(0.44), Y(0.235)), (X(0.82), Y(0.21)), (X(0.82), Y(-0.21)),
             (X(0.44), Y(-0.235))], RF)
    fb.poly([(X(0.37), Y(0.42)), (X(0.44), Y(0.30)), (X(0.44), Y(-0.30)),
             (X(0.37), Y(-0.42))], G)
    fb.poly([(X(0.08), Y(0.36)), (X(0.31), Y(0.42)), (X(0.31), Y(-0.42)),
             (X(0.08), Y(-0.36))], FB.hex("#2765d8"))
    for sgn in (-1, 1):
        fb.line(X(0.12), OY + sgn * 0.16 * W * S, X(0.24), OY + sgn * 0.26 * W * S, DK, 6)
    fb.poly([(X(0.045), Y(0.44)), (X(0.20), Y(0.40)), (X(0.20), Y(0.33)),
             (X(0.05), Y(0.36))], LF)
    fb.poly([(X(0.045), Y(-0.44)), (X(0.20), Y(-0.40)), (X(0.20), Y(-0.33)),
             (X(0.05), Y(-0.36))], LF)
    fb.poly([(X(0.82), Y(0.27)), (X(0.89), Y(0.27)), (X(0.89), Y(-0.27)),
             (X(0.82), Y(-0.27))], G)
    fb.poly([(X(0.82), Y(0.42)), (X(0.88), Y(0.42)), (X(0.88), Y(0.32)),
             (X(0.82), Y(0.32))], RD)
    fb.poly([(X(0.82), Y(-0.32)), (X(0.88), Y(-0.32)), (X(0.88), Y(-0.42)),
             (X(0.82), Y(-0.42))], RD)
    fb.poly([(X(0.89), Y(0.485)), (X(0.956), Y(0.485)), (X(0.956), Y(-0.485)),
             (X(0.89), Y(-0.485))], DK)
    fb.poly([(X(0.885), Y(0.515)), (X(0.965), Y(0.515)), (X(0.965), Y(0.485)),
             (X(0.885), Y(0.485))], YW)
    fb.poly([(X(0.885), Y(-0.485)), (X(0.965), Y(-0.485)), (X(0.965), Y(-0.515)),
             (X(0.885), Y(-0.515))], YW)
    for f in (0.25, 0.5, 0.75):
        fb.circle(X(0.945), Y(-0.485 + f * 0.97), 4, DK)
    xs2 = [i / 50 for i in range(51)]
    out = [(X(x), Y(hw(x))) for x in xs2] + [(X(x), Y(-hw(x))) for x in reversed(xs2)]
    for i in range(len(out)):
        fb.line(out[i][0], out[i][1], out[(i + 1) % len(out)][0], out[(i + 1) % len(out)][1], I, 2)
    fb.save(path)

def png_rear(path):
    S, CX, GY, CW, CH = 2.0, 200, 290, 400, 330
    Y = lambda yf: CX + yf * W * S
    Z = lambda zf: GY - zf * H * S
    fb = FB(CW, CH)
    B = FB.hex(BODY); D = FB.hex(BODY_D); I = FB.hex(INK); G = FB.hex(GLASS)
    DK = FB.hex(DARK); RD = FB.hex(RED); RF = FB.hex(ROOF); YW = FB.hex(YEL)
    T = FB.hex(TYRE); R = FB.hex(RIM)
    for sgn in (-1, 1):
        fb.circle(CX + sgn * 82 * S, GY - 32 * S, TYRE_R * S, T)
        fb.circle(CX + sgn * 82 * S, GY - 32 * S, TYRE_R * S * 0.6, R)
    fb.poly([(Y(-0.45), Z(0.50)), (Y(0.45), Z(0.50)), (Y(0.47), Z(0.12)),
             (Y(-0.47), Z(0.12))], B)
    fb.poly([(Y(-0.49), Z(0.64)), (Y(-0.30), Z(0.90)), (Y(0.30), Z(0.90)),
             (Y(0.49), Z(0.64)), (Y(0.44), Z(0.64)), (Y(0.27), Z(0.88)),
             (Y(-0.27), Z(0.88)), (Y(-0.44), Z(0.64))], B)
    fb.poly([(Y(-0.26), Z(0.66)), (Y(-0.28), Z(0.875)), (Y(0.28), Z(0.875)),
             (Y(0.26), Z(0.66))], G)
    fb.poly([(Y(-0.235), Z(0.93)), (Y(0.235), Z(0.93)), (Y(0.235), Z(0.90)),
             (Y(-0.235), Z(0.90))], RF)
    for sgn in (-1, 1):
        fb.poly([(Y(sgn * 0.08), Z(0.60)), (Y(sgn * 0.20), Z(0.56)),
                 (Y(sgn * 0.10), Z(0.51))], RD)
        fb.poly([(Y(sgn * 0.33), Z(0.62)), (Y(sgn * 0.42), Z(0.60)),
                 (Y(sgn * 0.42), Z(0.51)), (Y(sgn * 0.33), Z(0.52))], RD)
    fb.poly([(Y(-0.125), Z(0.485)), (Y(0.125), Z(0.485)), (Y(0.125), Z(0.415)),
             (Y(-0.125), Z(0.415))], RF)
    fb.line(Y(-0.44), Z(0.24), Y(0.44), Z(0.24), I, 2)
    fb.poly([(Y(-0.45), Z(0.24)), (Y(-0.42), Z(0.24)), (Y(-0.42), Z(0.12)),
             (Y(-0.45), Z(0.12))], DK)
    fb.poly([(Y(0.42), Z(0.24)), (Y(0.45), Z(0.24)), (Y(0.45), Z(0.12)),
             (Y(0.42), Z(0.12))], DK)
    fb.poly([(Y(-0.10), Z(0.52)), (Y(-0.06), Z(0.52)), (Y(-0.10), Z(1.02)),
             (Y(-0.14), Z(1.02))], DK)
    fb.poly([(Y(0.10), Z(0.52)), (Y(0.06), Z(0.52)), (Y(0.10), Z(1.02)),
             (Y(0.14), Z(1.02))], DK)
    fb.poly([(Y(-0.485), Z(1.075)), (Y(0.485), Z(1.075)),
             (Y(0.485), Z(1.045)), (Y(-0.485), Z(1.045))], DK)
    fb.poly([(Y(-0.515), Z(1.075)), (Y(-0.50), Z(1.075)), (Y(-0.50), Z(1.0)),
             (Y(-0.515), Z(1.0))], YW)
    fb.poly([(Y(0.50), Z(1.075)), (Y(0.515), Z(1.075)), (Y(0.515), Z(1.0)),
             (Y(0.50), Z(1.0))], YW)
    for f in (-0.24, 0.0, 0.24):
        fb.poly([(Y(f) - 4, Z(1.075)), (Y(f) + 4, Z(1.075)), (Y(f), Z(1.11))], DK)
    fb.save(path)

# ================================================== PILLOW RENDERERS ==
# Best-fit library for programmatic sprite design: Pillow (ImageDraw +
# LANCZOS-supersampled export). All coordinates below are final PNG pixels.
PSS = 3  # supersample factor -> smooth anti-aliased edges after downscale


def _hex(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


def _font(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, int(sz * PSS))
        except Exception:
            continue
    return ImageFont.load_default()


def _ramp(stops, n):
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        for k in range(len(stops) - 1):
            if stops[k][0] <= t <= stops[k + 1][0]:
                u = (t - stops[k][0]) / max(1e-9, stops[k + 1][0] - stops[k][0])
                a, b = stops[k][1], stops[k + 1][1]
                out.append(tuple(int(a[j] + (b[j] - a[j]) * u) for j in range(3)) + (255,))
                break
    return out


def _grad_img(w, h, stops, horizontal=False):
    n = w if horizontal else h
    ramp = _ramp(stops, n)
    im = Image.new("RGBA", (w, h))
    px = im.load()
    if horizontal:
        for x in range(w):
            for y in range(h):
                px[x, y] = ramp[x]
    else:
        for y in range(h):
            for x in range(w):
                px[x, y] = ramp[y]
    return im


class PR:
    """Supersampled sprite layer (all coords in final PNG pixels)."""

    def __init__(self, w, h):
        self.w, self.h, self.ss = w, h, PSS
        self.img = Image.new("RGBA", (w * PSS, h * PSS), (0, 0, 0, 0))
        self.dr = ImageDraw.Draw(self.img)

    def _p(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def poly(self, pts, fill=None, outline=None, width=2, grad=None, horiz=False):
        pts = self._p(pts)
        if grad is not None:
            m = Image.new("L", self.img.size, 0)
            ImageDraw.Draw(m).polygon(pts, fill=255)
            g = _grad_img(self.img.size[0], self.img.size[1], grad, horiz)
            self.img.paste(g, (0, 0), m)
        elif fill is not None:
            self.dr.polygon(pts, fill=fill)
        if outline is not None:
            self.dr.line(pts + [pts[0]], fill=outline,
                         width=max(1, int(width * self.ss)), joint="curve")

    def line(self, pts, fill, width=2):
        self.dr.line(self._p(pts), fill=fill,
                     width=max(1, int(width * self.ss)), joint="curve")

    def circle(self, cx, cy, r, fill=None, outline=None, width=2, ry=None):
        if ry is None:
            ry = r
        b = [(cx - r) * self.ss, (cy - ry) * self.ss,
             (cx + r) * self.ss, (cy + ry) * self.ss]
        if fill is not None:
            self.dr.ellipse(b, fill=fill)
        if outline is not None:
            self.dr.ellipse(b, outline=outline, width=max(1, int(width * self.ss)))

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=2, radius=0):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        b = [x0 * self.ss, y0 * self.ss, x1 * self.ss, y1 * self.ss]
        if radius > 0:
            self.dr.rounded_rectangle(b, radius=int(radius * self.ss),
                                      fill=fill, outline=outline,
                                      width=max(1, int(width * self.ss)))
        else:
            self.dr.rectangle(b, fill=fill, outline=outline,
                              width=max(1, int(width * self.ss)))

    def text(self, x, y, s, size, fill):
        self.dr.text((x * self.ss, y * self.ss), s, font=_font(size),
                     fill=fill, anchor="mm")

    def save(self, path):
        self.img.resize((self.w, self.h), Image.LANCZOS).save(path)


def _catmull(pts, per=12):
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(len(pts) - 1, i + 2)]
        for j in range(per):
            t = j / per
            t2, t3 = t * t, t * t * t
            out.append((0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    out.append(pts[-1])
    return out


def _arc_over(ax, ay, r, x_right, x_left, y_sill, step=4):
    """Sampled arc over an arch (right sill point -> left, passing the top)."""
    import math as _m
    a0 = _m.degrees(_m.atan2(y_sill - ay, x_right - ax))     # ~ +20
    a1 = _m.degrees(_m.atan2(y_sill - ay, x_left - ax))      # ~ +160
    a1 = a1 - 360 if a1 > a0 else a1                          # sweep via top (-90)
    pts, a = [], a0
    while a >= a1:
        q = _m.radians(a)
        pts.append((ax + r * _m.cos(q), ay + r * _m.sin(q)))
        a -= step
    return pts


_BODY_GRAD = [(0.0, _hex(BODY_L)[:3]), (0.45, _hex(BODY)[:3]), (1.0, _hex(BODY_D)[:3])]
_GLASS_GRAD = [(0.0, (211, 231, 250)), (1.0, _hex(GLASS_D)[:3])]
_HGRAD = [(0.0, _hex(BODY)[:3]), (0.5, _hex(BODY_L)[:3]), (1.0, _hex(BODY)[:3])]

_SIDE_TOP = [
    (0.000, 0.100), (0.030, 0.100), (0.040, 0.220), (0.045, 0.375),
    (0.060, 0.450), (0.080, 0.490), (0.150, 0.545), (0.220, 0.605),
    (0.300, 0.675), (0.360, 0.725), (0.370, 0.730), (0.390, 0.790),
    (0.405, 0.830), (0.440, 0.930), (0.480, 0.958), (0.530, 0.978),
    (0.580, 0.993), (0.630, 1.000), (0.680, 0.992), (0.730, 0.972),
    (0.780, 0.940), (0.820, 0.910), (0.860, 0.830), (0.890, 0.740),
    (0.930, 0.660), (0.950, 0.560), (0.970, 0.450), (0.985, 0.300),
    (1.000, 0.120),
]


def p_side(path):
    import math as _m
    S, OX, GY, CW, CH = 2.0, 40.0, 285.0, 920, 300
    X = lambda xf: OX + xf * L * S
    Z = lambda zf: GY - zf * H * S
    I, G, DK = _hex(INK), _hex(GLASS), _hex(DARK)
    RF, RD, LF, YW = _hex(ROOF), _hex(RED), _hex(LAMP_F), _hex(YEL)
    fb = PR(CW, CH)
    fb.dr.ellipse([10 * PSS, (GY + 4) * PSS, (CW - 10) * PSS, (GY + 22) * PSS],
                  fill=(11, 18, 32, 46))
    ax_f, ax_r, zax = X(AX_F), X(AX_R), Z(AX_Z)
    for cx in (ax_f, ax_r):  # reference wheels: 10 spokes = five pairs
        fb.circle(cx, zax, TYRE_R * S, fill=_hex(TYRE), outline=I, width=3)
        fb.circle(cx, zax, TYRE_R * S * 0.62, fill=_hex(RIM), outline=I, width=2.5)
        for k in range(5):
            for off in (-7, 7):
                a = _m.radians(k * 72 + off)
                fb.line([(cx, zax), (cx + _m.cos(a) * TYRE_R * S * 0.58,
                                     zax + _m.sin(a) * TYRE_R * S * 0.58)],
                        fill=_hex("#5b6472"), width=5)
        fb.circle(cx, zax, TYRE_R * S * 0.80, outline=_hex("#8b95a7"), width=2)
        for k in range(5):  # lug dots around the hub
            a = _m.radians(k * 72 + 36)
            fb.circle(cx + _m.cos(a) * TYRE_R * S * 0.30,
                      zax + _m.sin(a) * TYRE_R * S * 0.30, 3, fill=_hex("#5b6472"))
        fb.circle(cx, zax, TYRE_R * S * 0.14, fill=I)
    top = _catmull([(X(x), Z(z)) for x, z in _SIDE_TOP])
    sill_y = Z(SILL_Z / H)
    r = ARCH_R * S
    dx = _m.sqrt(max(1.0, ARCH_R ** 2 - (AX_Z * H - SILL_Z) ** 2)) * S
    body = (top + [(X(1.0), Z(0.12))]
            + _arc_over(ax_r, zax, r, ax_r + dx, ax_r - dx, sill_y)
            + _arc_over(ax_f, zax, r, ax_f + dx, ax_f - dx, sill_y)
            + [(X(0.030), Z(0.10)), (X(0.0), Z(0.10)),
               (X(0.0), Z(0.05)), (X(0.030), Z(0.05))])
    fb.poly(body, outline=I, width=3, grad=_BODY_GRAD)

    def roof_z(xf):
        for i in range(len(_SIDE_TOP) - 1):
            x0, z0 = _SIDE_TOP[i]
            x1, z1 = _SIDE_TOP[i + 1]
            if x0 <= xf <= x1 and x0 >= 0.43:
                t = (xf - x0) / max(1e-9, x1 - x0)
                return z0 + t * (z1 - z0)
        return 0.95
    belt = 0.64
    xs = [0.40 + i * (0.43 / 30) for i in range(31)]
    glass = [(X(0.40), Z(belt))] + [(X(x), Z(roof_z(x) - 0.015)) for x in xs] \
        + [(X(0.83), Z(belt))]
    fb.poly(glass, outline=I, width=2, grad=_GLASS_GRAD)
    fb.poly([(X(0.40), Z(belt)), (X(0.445), Z(belt)), (X(0.415), Z(0.72))],
            fill=_hex(GLASS_D), outline=I, width=1.5)
    fb.line([(X(0.40), Z(belt)), (X(0.375), Z(0.735))], fill=_hex(BODY_D), width=7)
    fb.line([(X(0.60), Z(roof_z(0.60) - 0.015)), (X(0.60), Z(belt))], fill=I, width=3)
    fb.line([(X(0.76), Z(roof_z(0.76) - 0.015)), (X(0.76), Z(belt))], fill=I, width=2)
    fb.poly([(X(0.795), Z(roof_z(0.795) - 0.015)), (X(0.825), Z(roof_z(0.825) - 0.015)),
             (X(0.83), Z(belt)), (X(0.80), Z(belt))], fill=_hex(BODY_D), outline=I, width=1.5)
    fb.line([(X(0.40), Z(belt)), (X(0.93), Z(belt))], fill=I, width=2.5)
    fb.line([(X(0.35), Z(belt)), (X(0.35), Z(SILL_Z / H))], fill=I, width=2)
    fb.line([(X(0.60), Z(belt)), (X(0.585), Z(SILL_Z / H))], fill=I, width=2)
    fb.line([(X(0.79), Z(belt)), (X(0.77), Z(0.45)), (X(0.74), Z(0.30)),
             (X(0.72), Z(SILL_Z / H))], fill=I, width=2)
    for hx in (0.51, 0.74):
        fb.rect(X(hx) - 17.6, Z(0.57) - 3, X(hx) + 17.6, Z(0.57) + 3,
                fill=RF, outline=I, width=1.5, radius=3)
    fb.line([(X(0.51), Z(0.575)), (X(0.62), Z(0.60)), (X(0.75), Z(0.585)),
             (X(0.945), Z(0.60))], fill=YW, width=4)
    fb.line([(X(0.10), Z(0.52)), (X(0.20), Z(0.55)), (X(0.30), Z(0.63)),
             (X(0.37), Z(0.72))], fill=I, width=2)
    fb.rect(X(0.0), Z(0.10), X(0.035), Z(0.05), fill=DK, outline=I, width=2)
    fb.rect(X(0.0), Z(0.13), X(0.0) + 7, Z(0.05), fill=DK, outline=I, width=2)
    fb.rect(X(0.36), sill_y, X(0.70), sill_y + 0.02 * H * S, fill=DK, outline=I, width=1.5)
    fb.rect(X(0.33), Z(0.52), X(0.36), sill_y, fill=DK, outline=I, width=2, radius=4)
    fb.line([(X(0.332), Z(0.44)), (X(0.358), Z(0.44))], fill=_hex("#8b95a7"), width=2.5)
    fb.line([(X(0.332), Z(0.34)), (X(0.358), Z(0.34))], fill=_hex("#8b95a7"), width=2.5)
    fb.rect(X(0.84) - 11, Z(0.63) - 11, X(0.84) + 11, Z(0.63) + 11,
            fill=_hex(BODY_L), outline=I, width=2, radius=5)
    fb.line(_arc_over(ax_f, zax, r + 4, ax_f + dx + 6, ax_f - dx - 6, sill_y), fill=I, width=7)
    fb.line(_arc_over(ax_r, zax, r + 4, ax_r + dx + 6, ax_r - dx - 6, sill_y), fill=I, width=7)
    fb.poly([(X(0.04), Z(0.42)), (X(0.20), Z(0.505)), (X(0.195), Z(0.55)),
             (X(0.05), Z(0.49))], fill=LF, outline=I, width=2)
    fb.poly([(X(0.905), Z(0.615)), (X(0.94), Z(0.63)), (X(0.968), Z(0.605)),
             (X(0.963), Z(0.49)), (X(0.925), Z(0.505))], fill=RD, outline=I, width=2)
    fb.circle(X(0.475), Z(0.42), 17, fill=RF, outline=I, width=2.5)
    fb.text(X(0.475), Z(0.42) + 1, "45", 20, I)
    fb.poly([(X(0.905), Z(0.60)), (X(0.920), Z(0.60)), (X(0.945), Z(1.055)),
             (X(0.930), Z(1.055))], fill=DK, outline=I, width=2)
    fb.rect(X(0.89), Z(1.10), X(0.96), Z(1.055), fill=DK, outline=I, width=2)
    fb.rect(X(0.886), Z(1.10), X(0.898), Z(1.10) + 50, fill=YW, outline=I, width=2)
    fb.poly([((X(0.89) + X(0.96)) / 2 - 5, Z(1.10)),
             ((X(0.89) + X(0.96)) / 2 + 5, Z(1.10)),
             ((X(0.89) + X(0.96)) / 2, Z(1.10) - 10)], fill=DK, outline=I, width=1.5)
    fb.line([(X(0.965), Z(0.22)), (X(1.0), Z(0.22))], fill=I, width=2)
    fb.save(path)


def _plan_hw(xf):
    import math as _m
    if xf <= 0.0:
        return 0.15
    if xf <= 0.12:
        t = xf / 0.12
        return 0.15 + 0.35 * t * t * (3 - 2 * t)
    if xf <= 0.32:
        return 0.50
    if xf <= 0.74:
        return 0.49 - 0.005 * _m.sin(_m.pi * (xf - 0.32) / 0.42)
    if xf <= 0.92:
        return 0.50
    return max(0.40, 0.50 - 0.05 * (xf - 0.92) / 0.08)


def p_top(path):
    import math as _m
    S, OX, OY, CW, CH = 2.0, 30.0, 210.0, 920, 420
    X = lambda xf: OX + xf * L * S
    Y = lambda yf: OY + yf * W * S
    I, DK = _hex(INK), _hex(DARK)
    RF, RD, LF, YW = _hex(ROOF), _hex(RED), _hex(LAMP_F), _hex(YEL)
    fb = PR(CW, CH)
    fb.dr.ellipse([10 * PSS, (OY - W * S * 0.52) * PSS, (CW - 10) * PSS,
                   (OY + W * S * 0.52) * PSS], fill=(11, 18, 32, 36))
    xs = [i / 100 for i in range(101)]
    fb.poly([(X(x), Y(_plan_hw(x))) for x in xs]
            + [(X(x), Y(-_plan_hw(x))) for x in reversed(xs)],
            outline=I, width=3, grad=_HGRAD, horiz=True)
    fb.line([(X(0.0) - 8, Y(-0.16)), (X(0.06), Y(-0.51)), (X(0.12), Y(-0.51))], fill=I, width=2)
    fb.line([(X(0.0) - 8, Y(0.16)), (X(0.06), Y(0.51)), (X(0.12), Y(0.51))], fill=I, width=2)
    fb.line([(X(1.0), Y(-0.40)), (X(1.0), Y(0.40))], fill=I, width=3)
    for sgn in (-1, 1):
        fb.poly([(X(0.045), Y(sgn * 0.44)), (X(0.20), Y(sgn * 0.40)),
                 (X(0.20), Y(sgn * 0.33)), (X(0.05), Y(sgn * 0.36))],
                fill=LF, outline=I, width=2)
    fb.circle(X(0.02), OY, 8, fill=_hex(BODY_L), outline=I, width=2)
    fb.poly([(X(0.08), Y(-0.36)), (X(0.08), Y(0.36)), (X(0.31), Y(0.42)),
             (X(0.335), OY), (X(0.31), Y(-0.42))], fill=_hex("#2765d8"), outline=I, width=2.5)
    for sgn in (-1, 1):  # slanted 4-slat louvres, rear edge shifted outward
        cx0, cx1 = X(0.12), X(0.24)
        spill = _m.tan(_m.radians(20)) * (cx1 - cx0) * 0.45
        yc = OY + sgn * 0.21 * W * S
        wdt = 0.055 * W * S
        yo = yc - sgn * wdt * 0.28
        fb.poly([(cx0, yo), (cx1, yo + sgn * spill),
                 (cx1, yo + sgn * spill + 7), (cx0, yo + 7)], fill=DK, outline=I, width=2)
        for k in range(4):
            t = (k + 0.5) / 4
            xt = cx0 + t * (cx1 - cx0)
            yt = yo + sgn * spill * t
            fb.line([(xt, yt), (xt + 5, yt + 7)], fill=_hex(RIM), width=2.5)
    fb.poly([(X(0.31), Y(0.42)), (X(0.37), Y(0.42)), (X(0.37), Y(-0.42)),
             (X(0.31), Y(-0.42))], fill=DK, outline=I, width=2)
    fb.line([(X(0.335), Y(-0.25)), (X(0.36), Y(0.05))], fill=_hex("#8b95a7"), width=2.5)
    fb.line([(X(0.335), Y(0.25)), (X(0.36), Y(-0.05))], fill=_hex("#8b95a7"), width=2.5)
    fb.poly([(X(0.37), Y(0.42)), (X(0.44), Y(0.30)), (X(0.44), Y(-0.30)),
             (X(0.37), Y(-0.42))], outline=I, width=2, grad=_GLASS_GRAD)
    for sgn in (-1, 1):
        fb.poly([(X(0.44), Y(sgn * 0.30)), (X(0.82), Y(sgn * 0.235)),
                 (X(0.82), Y(sgn * 0.47)), (X(0.44), Y(sgn * 0.47))],
                outline=I, width=2, grad=_GLASS_GRAD)
    for sx in (0.35, 0.60, 0.76):  # door shut ticks at the body side
        for sgn in (-1, 1):
            fb.line([(X(sx), Y(sgn * 0.495)), (X(sx), Y(sgn * 0.44))], fill=I, width=2)
    fb.poly([(X(0.44), Y(0.235)), (X(0.82), Y(0.21)), (X(0.82), Y(-0.21)),
             (X(0.44), Y(-0.235))], fill=RF, outline=I, width=2.5)
    fb.rect(X(0.47), Y(-0.135), X(0.50), Y(0.135), fill=DK, outline=I, width=1.5)
    fb.text(X(0.63), OY + 1, "45", 22, I)
    fb.poly([(X(0.82), Y(0.30)), (X(0.89), Y(0.27)), (X(0.89), Y(-0.27)),
             (X(0.82), Y(-0.30))], outline=I, width=2, grad=_GLASS_GRAD)
    for sgn in (-1, 1):
        fb.rect(X(0.82), Y(sgn * 0.42), X(0.88), Y(sgn * 0.32),
                fill=RD, outline=I, width=2, radius=5)
    fb.line([(X(0.905), Y(-0.33)), (X(0.905), Y(0.33))], fill=I, width=2)
    fb.line([(X(0.905), Y(-0.33)), (X(0.86), Y(-0.40))], fill=I, width=2)
    fb.line([(X(0.905), Y(0.33)), (X(0.86), Y(0.40))], fill=I, width=2)
    fb.rect(X(0.89), Y(-0.485), X(0.956), Y(0.485), fill=DK, outline=I, width=2.5)
    fb.rect(X(0.885), Y(-0.515), X(0.965), Y(-0.485), fill=YW, outline=I, width=2)
    fb.rect(X(0.885), Y(0.485), X(0.965), Y(0.515), fill=YW, outline=I, width=2)
    for f in (0.25, 0.50, 0.75):
        fb.circle(X(0.945), Y(-0.485 + f * 0.97), 10, fill=DK, outline=I, width=1.5, ry=4)
    for k in range(5):  # nose grille slats
        y = Y(-0.06 + k * 0.03)
        fb.line([(X(0.035), y), (X(0.055), y)], fill=DK, width=2.5)
    fb.save(path)


def p_rear(path):
    S, CX, GY, CW, CH = 2.0, 200.0, 290.0, 400, 330
    Y = lambda yf: CX + yf * W * S
    Z = lambda zf: GY - zf * H * S
    I, B, D = _hex(INK), _hex(BODY), _hex(BODY_D)
    DK = _hex(DARK)
    RF, RD, YW = _hex(ROOF), _hex(RED), _hex(YEL)
    fb = PR(CW, CH)
    fb.dr.ellipse([(CX - W * S * 0.48) * PSS, (GY + 4) * PSS,
                   (CX + W * S * 0.48) * PSS, (GY + 20) * PSS],
                  fill=(11, 18, 32, 46))
    for sgn in (-1, 1):
        wx = CX + sgn * 82 * S
        wy = GY - 32 * S
        fb.circle(wx, wy, TYRE_R * S, fill=_hex(TYRE), outline=I, width=3)
        fb.circle(wx, wy, TYRE_R * S * 0.6, fill=_hex(RIM), outline=I, width=2)
    fb.poly([(Y(-0.45), Z(0.50)), (Y(0.45), Z(0.50)), (Y(0.47), Z(0.12)),
             (Y(-0.47), Z(0.12))], outline=I, width=3, grad=_BODY_GRAD)
    fb.poly([(Y(-0.49), Z(0.64)), (Y(-0.30), Z(0.90)), (Y(0.30), Z(0.90)),
             (Y(0.49), Z(0.64)), (Y(0.44), Z(0.64)), (Y(0.27), Z(0.88)),
             (Y(-0.27), Z(0.88)), (Y(-0.44), Z(0.64))], fill=B, outline=I, width=2.5)
    fb.poly([(Y(-0.26), Z(0.66)), (Y(-0.28), Z(0.875)), (Y(0.28), Z(0.875)),
             (Y(0.26), Z(0.66))], outline=I, width=2, grad=_GLASS_GRAD)
    fb.rect(Y(-0.30), Z(0.925), Y(0.30), Z(0.925) + 7, fill=D, outline=I, width=2, radius=3)
    fb.poly([(Y(-0.235), Z(0.93)), (Y(0.235), Z(0.93)), (Y(0.235), Z(0.90)),
             (Y(-0.235), Z(0.90))], fill=RF, outline=I, width=2.5)
    for sgn in (-1, 1):
        fb.poly([(Y(sgn * 0.08), Z(0.60)), (Y(sgn * 0.20), Z(0.56)),
                 (Y(sgn * 0.10), Z(0.51))], fill=RD, outline=I, width=2)
        fb.poly([(Y(sgn * 0.33), Z(0.625)), (Y(sgn * 0.455), Z(0.605)),
                 (Y(sgn * 0.435), Z(0.505)), (Y(sgn * 0.325), Z(0.515))],
                fill=RD, outline=I, width=2)
    fb.line([(Y(-0.20), Z(0.50)), (Y(-0.20), Z(0.30))], fill=I, width=1.5)
    fb.line([(Y(0.20), Z(0.50)), (Y(0.20), Z(0.30))], fill=I, width=1.5)
    fb.rect(Y(-0.125), Z(0.485), Y(0.125), Z(0.415), fill=RF, outline=I, width=2, radius=4)
    fb.text(CX, (Z(0.485) + Z(0.415)) / 2 + 1, "CA-45", 13, I)
    fb.line([(Y(-0.44), Z(0.24)), (Y(0.44), Z(0.24))], fill=I, width=2.5)
    for sx in (-0.15, 0.0, 0.15):
        fb.line([(Y(sx), Z(0.235)), (Y(sx), Z(0.13))], fill=I, width=1.5)
    fb.rect(Y(-0.45), Z(0.24), Y(-0.42), Z(0.12), fill=DK, outline=I, width=2)
    fb.rect(Y(0.42), Z(0.24), Y(0.45), Z(0.12), fill=DK, outline=I, width=2)
    fb.rect(Y(-0.50), GY - 8, Y(-0.47), GY, fill=DK, outline=I, width=1.5)
    fb.rect(Y(0.47), GY - 8, Y(0.50), GY, fill=DK, outline=I, width=1.5)
    fb.poly([(Y(-0.10), Z(0.52)), (Y(-0.06), Z(0.52)), (Y(-0.115), Z(1.02)),
             (Y(-0.155), Z(1.02))], fill=DK, outline=I, width=2)
    fb.poly([(Y(0.10), Z(0.52)), (Y(0.06), Z(0.52)), (Y(0.115), Z(1.02)),
             (Y(0.155), Z(1.02))], fill=DK, outline=I, width=2)
    fb.rect(Y(-0.485), Z(1.075), Y(0.485), Z(1.045), fill=DK, outline=I, width=2.5)
    fb.rect(Y(-0.515), Z(1.075), Y(-0.50), Z(1.0), fill=YW, outline=I, width=2)
    fb.rect(Y(0.50), Z(1.075), Y(0.515), Z(1.0), fill=YW, outline=I, width=2)
    for f in (-0.24, 0.0, 0.24):
        fb.poly([(Y(f) - 5, Z(1.075)), (Y(f) + 5, Z(1.075)), (Y(f), Z(1.11))],
                fill=DK, outline=I, width=1.5)
    fb.save(path)


# ================================================================== MAIN ====
PREVIEW = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>FWD touring shell sprites - muse-spark-1.3_high</title>
<style>body{font-family:sans-serif;background:#0b1220;color:#e2e8f0;margin:24px}
img{background:#f1f5f9;border-radius:8px;max-width:100%}table{border-collapse:collapse}
td,th{border:1px solid #334155;padding:6px 10px;font-size:14px;text-align:left}th{background:#1e293b}</style>
</head><body><h1>1/10 FWD touring-car body shell - 2D sprites (muse-spark-1.3_high)</h1>
<h2>Side</h2><img src="side.svg" alt="side sprite"><h2>Top (plan)</h2>
<img src="top.svg" alt="top sprite"><h2>Rear</h2><img src="rear.svg" alt="rear sprite">
<h2>Checklist vs BASE_PROMPT</h2><table>
<tr><th>Tell</th><th>Where</th></tr>
<tr><td>Hatchback stance: short bonnet, roof peak 0.60-0.66L, steep tail, no boot deck</td><td>side.svg roof peak at 0.63L; top.svg roof island 0.44-0.82</td></tr>
<tr><td>Glass ring: 3-pane side glass, thick C-pillar, wide raked hatch glass</td><td>side.svg glass band 0.40-0.83 + C-pillar block; rear.svg hatch glass</td></tr>
<tr><td>Full-width rear wing on 2 pylons over hatch glass, endplates + 3 fins</td><td>all three; side x=0.89-0.96, top span 0.97W, rear pylons at +/-0.10W</td></tr>
<tr><td>Bonnet vents: 2 slanted 4-slat louvres, front half of bonnet</td><td>top.svg x=0.12-0.24 at 20 deg</td></tr>
<tr><td>Splitter under tall wide nose, lip wraps both front corners</td><td>side.svg z=0.05-0.10H; top.svg double lip line</td></tr>
<tr><td>Flared arches (r=0.085L) on straight sides; sill + skirt lips</td><td>side.svg arches at 0.235/0.84L; top.svg 0.50W flares, 0.49W waist</td></tr>
</table><p>Flat PNG game sprites: side.png, top.png, rear.png (pure-stdlib encoder).</p>
</body></html>
"""

def main():
    with open(os.path.join(OUT, "side.svg"), "w") as f:
        f.write(side_svg())
    with open(os.path.join(OUT, "top.svg"), "w") as f:
        f.write(top_svg())
    with open(os.path.join(OUT, "rear.svg"), "w") as f:
        f.write(rear_svg())
    if HAVE_PIL:
        p_side(os.path.join(OUT, "side.png"))
        p_top(os.path.join(OUT, "top.png"))
        p_rear(os.path.join(OUT, "rear.png"))
    else:
        png_side(os.path.join(OUT, "side.png"))
        png_top(os.path.join(OUT, "top.png"))
        png_rear(os.path.join(OUT, "rear.png"))
    with open(os.path.join(OUT, "preview.html"), "w") as f:
        f.write(PREVIEW)
    for n in ("side.svg", "top.svg", "rear.svg", "side.png", "top.png", "rear.png"):
        print(n, os.path.getsize(os.path.join(OUT, n)), "bytes")

if __name__ == "__main__":
    main()
