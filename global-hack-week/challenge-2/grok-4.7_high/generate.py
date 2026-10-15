#!/usr/bin/env python3
"""Three orthographic sprites of a 1/10 FWD touring-car body shell.

Model: grok-4.7
Reasoning effort: high
Geometry: ../BASE_PROMPT.md (station tables are the authority)

Pillow 12.3.0 is loaded from the challenge's existing .vendor directory.
No external skills. Wheels are placement references, not part of the shell.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE.parent / ".vendor"
if VENDOR.is_dir():
    sys.path.insert(0, str(VENDOR))

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Final sprites are 2 px per millimetre. Drawing is 3x supersampled.
SS = 3
S = 2 * SS

L, W, H = 440.0, 190.0, 125.0
AXLE_Z = 0.26 * H
TYRE_R = 32.0
TYRE_W = 26.0
ARCH_R = 0.085 * L
FRONT_X = 0.235 * L
REAR_X = 0.84 * L
SILL_Z = 0.14 * H
# Wing stations from the prompt. The CA45 sheet draws a taller endplate than
# "two wing thicknesses", down to the lamp line, so the plate uses that height.
WING_CHORD = 0.066 * L
WING_THICK = WING_CHORD / 7
WING_TE = 0.960 * L
WING_LE = WING_TE - WING_CHORD
WING_TOP_Z = 0.80 * H
WING_BOT_Z = WING_TOP_Z - WING_THICK
ENDPLATE_BOT_Z = 0.60 * H

# Racing green, ivory roof, copper graphics. Number 47.
GREEN_HI = (78, 140, 104, 255)
GREEN = (27, 92, 68, 255)
GREEN_LO = (12, 48, 36, 255)
GREEN_EDGE = (8, 28, 22, 255)
IVORY = (243, 236, 214, 255)
IVORY_DIM = (214, 204, 176, 255)
COPPER = (196, 98, 42, 255)
COPPER_HI = (232, 146, 78, 255)
INK = (16, 20, 18, 255)
GLASS = (22, 40, 48, 255)
GLASS_HI = (126, 168, 176, 255)
LENS = (236, 244, 236, 255)
AMBER = (242, 176, 48, 255)
LAMP = (196, 28, 36, 255)
LAMP_HI = (255, 92, 78, 255)
CARBON = (22, 24, 26, 255)
WELL = (10, 14, 12, 255)
TYRE = (22, 24, 26, 255)
RIM = (176, 184, 186, 255)
RIM_IN = (52, 60, 64, 255)


def mm(x_frac=None, z_frac=None, y_frac=None, x=None, z=None, y=None):
    """Scale a station. Fractions are of L, H, or W. Absolute mm override."""
    if x is None:
        x = x_frac * L
    if z is None and z_frac is not None:
        z = z_frac * H
    if y is None and y_frac is not None:
        y = y_frac * W
    return x, z, y


def smooth(points, steps=8):
    """Catmull-Rom sample. `points` are (x, y) pairs, x should increase."""
    if len(points) < 2:
        return list(points)
    out = []
    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]
        for n in range(steps):
            t = n / steps
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            out.append((x, y))
    out.append(points[-1])
    return out


def z_at(poly, x):
    if x <= poly[0][0]:
        return poly[0][1]
    for (x0, z0), (x1, z1) in zip(poly, poly[1:]):
        if x1 == x0:
            continue
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return z0 + (z1 - z0) * t
    return poly[-1][1]


def upper_profile():
    """Side silhouette crown, nose to tail, in millimetres. Peak sits at 0.63 L."""
    nose = smooth(
        [
            (0.000 * L, 0.100 * H),
            (0.030 * L, 0.100 * H),
            (0.036 * L, 0.220 * H),
            (0.046 * L, 0.360 * H),
            (0.058 * L, 0.450 * H),
        ],
        steps=6,
    )
    step = [
        (0.058 * L, 0.450 * H),
        (0.074 * L, 0.458 * H),
        (0.080 * L, 0.490 * H),
    ]
    cabin = smooth(
        [
            (0.080 * L, 0.490 * H),
            (0.160 * L, 0.578 * H),
            (0.260 * L, 0.662 * H),
            (0.360 * L, 0.724 * H),
            (0.370 * L, 0.730 * H),
            (0.405 * L, 0.840 * H),
            (0.440 * L, 0.930 * H),
            (0.530 * L, 0.980 * H),
            (0.630 * L, 1.000 * H),
            (0.730 * L, 0.970 * H),
            (0.820 * L, 0.910 * H),
            (0.875 * L, 0.782 * H),
            (0.930 * L, 0.660 * H),
            (0.952 * L, 0.545 * H),
            (0.970 * L, 0.450 * H),
            (0.986 * L, 0.260 * H),
            (1.000 * L, 0.120 * H),
        ],
        steps=8,
    )
    poly = nose + step + cabin
    # Roof peak is the maximum. Clamp tiny Catmull overshoot.
    return [(x, min(z, H)) for x, z in poly]


UPPER = upper_profile()


def side_body_mm():
    bottom = [
        (1.000 * L, 0.120 * H),
        (0.945 * L, 0.128 * H),
        (0.900 * L, SILL_Z),
        (0.120 * L, SILL_Z),
        (0.055 * L, 0.050 * H),
        (0.000 * L, 0.050 * H),
    ]
    return UPPER + bottom


def plan_outline_mm():
    half = smooth(
        [
            (0.000 * L, 0.150 * W),
            (0.025 * L, 0.260 * W),
            (0.060 * L, 0.400 * W),
            (0.100 * L, 0.480 * W),
            (0.120 * L, 0.500 * W),
            (0.180 * L, 0.500 * W),
            (0.235 * L, 0.500 * W),
            (0.320 * L, 0.500 * W),
            (0.420 * L, 0.493 * W),
            (0.560 * L, 0.490 * W),
            (0.680 * L, 0.494 * W),
            (0.740 * L, 0.500 * W),
            (0.840 * L, 0.500 * W),
            (0.920 * L, 0.500 * W),
            (0.960 * L, 0.470 * W),
            (0.985 * L, 0.445 * W),
            (1.000 * L, 0.400 * W),
        ],
        steps=8,
    )
    right = [(x, y) for x, y in half]
    left = [(x, -y) for x, y in reversed(half)]
    return right + left


def font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    px = max(8, int(round(size * S / 2)))
    for path in candidates:
        try:
            return ImageFont.truetype(path, px)
        except OSError:
            continue
    return ImageFont.load_default()


def new_canvas(w_mm, h_mm):
    return Image.new("RGBA", (int(math.ceil(w_mm * S)), int(math.ceil(h_mm * S))), (0, 0, 0, 0))


def down(image):
    return image.resize((image.width // SS, image.height // SS), Image.Resampling.LANCZOS)


def vgradient(size, top, bottom):
    strip = Image.new("RGBA", (1, size[1]))
    pix = strip.load()
    last = max(1, size[1] - 1)
    for i in range(size[1]):
        t = i / last
        pix[0, i] = tuple(int(top[k] * (1 - t) + bottom[k] * t) for k in range(4))
    return strip.resize(size, Image.Resampling.BILINEAR)


def paint(base, mask, color):
    """Composite a solid or an image through an L mask."""
    if isinstance(color, Image.Image):
        fill = color
    else:
        fill = Image.new("RGBA", base.size, color)
    base.alpha_composite(Image.composite(fill, Image.new("RGBA", base.size, (0, 0, 0, 0)), mask))


def poly_mask(size, points, holes=()):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(points, fill=255)
    for box in holes:
        draw.ellipse(box, fill=0)
    return mask


def shadow(base, box, alpha=80, blur=7):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(box, fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur * SS))
    base.alpha_composite(layer)


def text_center(draw, xy, text, face, fill):
    box = draw.textbbox((0, 0), text, font=face)
    w = box[2] - box[0]
    h = box[3] - box[1]
    draw.text((xy[0] - w / 2, xy[1] - h / 2 - box[1]), text, font=face, fill=fill)


def wheel_side(base, cx, cz):
    r = TYRE_R * S
    x = cx * S
    y = cz * S
    d = ImageDraw.Draw(base)
    d.ellipse((x - r, y - r, x + r, y + r), fill=TYRE)
    d.ellipse((x - r * 0.92, y - r * 0.92, x + r * 0.92, y + r * 0.92), outline=(70, 74, 76, 255), width=max(2, int(r * 0.06)))
    d.ellipse((x - r * 0.78, y - r * 0.78, x + r * 0.78, y + r * 0.78), fill=(48, 52, 54, 255))
    d.ellipse((x - r * 0.70, y - r * 0.70, x + r * 0.70, y + r * 0.70), fill=RIM, outline=INK, width=max(2, S // 2))
    d.ellipse((x - r * 0.52, y - r * 0.52, x + r * 0.52, y + r * 0.52), fill=RIM_IN)
    for k in range(5):
        base_a = math.radians(-90 + k * 72)
        for delta in (-0.07, 0.07):
            a = base_a + delta
            x0 = x + math.cos(a) * r * 0.18
            y0 = y + math.sin(a) * r * 0.18
            x1 = x + math.cos(a) * r * 0.64
            y1 = y + math.sin(a) * r * 0.64
            d.line((x0, y0, x1, y1), fill=(226, 230, 228, 255), width=max(2, int(r * 0.05)))
        lug = base_a + 0.35
        lx = x + math.cos(lug) * r * 0.24
        ly = y + math.sin(lug) * r * 0.24
        d.ellipse((lx - r * 0.045, ly - r * 0.045, lx + r * 0.045, ly + r * 0.045), fill=IVORY, outline=INK)
    d.ellipse((x - r * 0.12, y - r * 0.12, x + r * 0.12, y + r * 0.12), fill=COPPER)
    d.ellipse((x - r * 0.045, y - r * 0.045, x + r * 0.045, y + r * 0.045), fill=IVORY)


def arch_box(cx, cz, radius):
    return (
        (cx - radius) * S,
        (cz - radius) * S,
        (cx + radius) * S,
        (cz + radius) * S,
    )


def side_pt(origin, x_mm, z_mm):
    ox, oz = origin
    return ((ox + x_mm) * S, (oz - z_mm) * S)


def box2(a, b):
    """Axis-aligned box from two corners. Image y grows downward."""
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))


def render_side():
    pad_l, pad_r, pad_t, pad_b = 16.0, 20.0, 14.0, 18.0
    canvas = new_canvas(pad_l + L + pad_r, pad_t + H + pad_b)
    # origin: ground at the nose, image y grows downward, so z=0 is pad_t+H from the top.
    origin = (pad_l, pad_t + H)
    pts = [side_pt(origin, x, z) for x, z in side_body_mm()]
    wells = [arch_box(pad_l + ax, origin[1] - AXLE_Z, ARCH_R) for ax in (FRONT_X, REAR_X)]

    shadow(
        canvas,
        (
            (pad_l + 30) * S,
            (origin[1] - 2) * S,
            (pad_l + L - 20) * S,
            (origin[1] + 8) * S,
        ),
    )

    well_mask = Image.new("L", canvas.size, 0)
    wd = ImageDraw.Draw(well_mask)
    for box in wells:
        wd.ellipse(box, fill=255)
    # Keep the well inside the arch opening, not under the ground line.
    wd.rectangle((0, origin[1] * S, canvas.width, canvas.height), fill=0)
    paint(canvas, well_mask, WELL)

    for ax in (FRONT_X, REAR_X):
        wheel_side(canvas, pad_l + ax, origin[1] - AXLE_Z)

    body = poly_mask(canvas.size, pts, holes=wells)
    grad = vgradient(canvas.size, GREEN_HI, GREEN_LO)
    paint(canvas, body, grad)

    # Flare lip: a ring around each cut-out, stopped at the sill.
    lip = Image.new("L", canvas.size, 0)
    ld = ImageDraw.Draw(lip)
    lip_w = 0.010 * L * S
    for box in wells:
        outer = (box[0] - lip_w * 0.15, box[1] - lip_w * 0.15, box[2] + lip_w * 0.15, box[3] + lip_w * 0.15)
        inner = (box[0] + lip_w, box[1] + lip_w, box[2] - lip_w, box[3] - lip_w)
        ld.ellipse(outer, fill=255)
        ld.ellipse(inner, fill=0)
    sill_y = side_pt(origin, 0, SILL_Z)[1]
    ld.rectangle((0, sill_y, canvas.width, canvas.height), fill=0)
    paint(canvas, lip, (232, 236, 226, 255))

    draw = ImageDraw.Draw(canvas)
    draw.line(pts + [pts[0]], fill=GREEN_EDGE, width=max(2, S // 2), joint="curve")

    def P(x_frac, z_frac):
        return side_pt(origin, x_frac * L, z_frac * H)

    def XZ(x_mm, z_mm):
        return side_pt(origin, x_mm, z_mm)

    # Black aero: splitter plate and side skirt.
    splitter = [
        XZ(0, 0.05 * H),
        XZ(0, 0.100 * H),
        XZ(0.062 * L, 0.100 * H),
        XZ(0.078 * L, 0.050 * H),
    ]
    draw.polygon(splitter, fill=CARBON)
    # Splitter end fence from the CA45 side sheet: a vertical plate at the nose corner.
    draw.polygon(
        [
            XZ(0, 0.05 * H),
            XZ(0, 0.20 * H),
            XZ(0.014 * L, 0.17 * H),
            XZ(0.014 * L, 0.05 * H),
        ],
        fill=CARBON,
        outline=INK,
    )
    draw.polygon([P(0.018, 0.20), P(0.075, 0.25), P(0.075, 0.21), P(0.030, 0.18)], fill=CARBON)
    skirt_top = SILL_Z + 0.028 * H
    skirt = [
        XZ(0.32 * L, SILL_Z),
        XZ(0.32 * L, skirt_top),
        XZ(0.74 * L, skirt_top),
        XZ(0.74 * L, SILL_Z),
    ]
    skirt_mask = poly_mask(canvas.size, skirt)
    clipped = Image.new("L", canvas.size, 0)
    clipped.paste(skirt_mask, mask=body)
    paint(canvas, clipped, CARBON)

    # Lower intake on the bumper face.
    draw.rounded_rectangle(
        box2(P(0.012, 0.14), P(0.055, 0.30)),
        radius=int(3 * S),
        fill=(8, 12, 14, 255),
    )
    for i in range(4):
        x0 = 0.018 + i * 0.008
        draw.line([P(x0, 0.16), P(x0, 0.28)], fill=(70, 78, 76, 255), width=max(2, S // 3))

    # Headlamp: long pointed lens, sweeping back along the wing to x=0.20.
    lamp = smooth(
        [
            (0.032 * L, 0.30 * H),
            (0.060 * L, 0.44 * H),
            (0.120 * L, 0.50 * H),
            (0.200 * L, 0.515 * H),
            (0.168 * L, 0.445 * H),
            (0.090 * L, 0.36 * H),
            (0.048 * L, 0.30 * H),
        ],
        steps=5,
    )
    draw.polygon([XZ(x, z) for x, z in lamp], fill=LENS, outline=INK)
    draw.polygon(
        [P(0.055, 0.34), P(0.100, 0.46), P(0.155, 0.48), P(0.120, 0.38)],
        fill=AMBER,
    )

    # Bonnet shut line, from the lamp up to the A-pillar base.
    shut = smooth(
        [
            (0.100 * L, 0.520 * H),
            (0.200 * L, 0.600 * H),
            (0.300 * L, 0.670 * H),
            (0.370 * L, 0.720 * H),
        ],
        steps=6,
    )
    draw.line([XZ(x, z) for x, z in shut], fill=GREEN_EDGE, width=max(2, S // 2))

    # Glass band under the roof arc, belt line at 0.64 H.
    def glass_top(x_mm):
        return min(z_at(UPPER, x_mm) - 0.012 * H, 0.985 * H)

    belt = 0.64 * H
    front = [
        XZ(0.455 * L, belt),
        XZ(0.590 * L, belt),
        XZ(0.590 * L, glass_top(0.590 * L)),
        XZ(0.500 * L, glass_top(0.500 * L)),
        XZ(0.455 * L, glass_top(0.455 * L)),
    ]
    rear_door = [
        XZ(0.610 * L, belt),
        XZ(0.750 * L, belt),
        XZ(0.750 * L, glass_top(0.750 * L)),
        XZ(0.640 * L, glass_top(0.640 * L)),
        XZ(0.610 * L, glass_top(0.610 * L)),
    ]
    quarter = [
        XZ(0.758 * L, belt),
        XZ(0.758 * L, glass_top(0.758 * L) - 0.012 * H),
        XZ(0.798 * L, glass_top(0.798 * L) - 0.030 * H),
        XZ(0.824 * L, belt + 0.045 * H),
    ]
    quarter_light = [P(0.400, 0.64), P(0.448, 0.64), P(0.430, 0.705)]
    for pane in (front, rear_door, quarter, quarter_light):
        draw.polygon(pane, fill=GLASS)
    # Cool reflection along the header.
    reflect = [
        XZ(0.470 * L, glass_top(0.470 * L) - 0.01 * H),
        XZ(0.700 * L, glass_top(0.700 * L) - 0.012 * H),
        XZ(0.680 * L, glass_top(0.680 * L) - 0.045 * H),
        XZ(0.490 * L, glass_top(0.490 * L) - 0.04 * H),
    ]
    draw.polygon(reflect, fill=GLASS_HI)

    # A-pillar (thin, raked) and thick C-pillar.
    draw.line([P(0.395, 0.66), P(0.448, 0.93)], fill=GREEN_EDGE, width=int(0.012 * L * S))
    c_pillar = [
        XZ(0.818 * L, belt - 0.005 * H),
        XZ(0.848 * L, belt - 0.015 * H),
        XZ(0.852 * L, 0.80 * H),
        XZ(0.828 * L, glass_top(0.824 * L)),
    ]
    draw.polygon(c_pillar, fill=GREEN)
    draw.line(c_pillar + [c_pillar[0]], fill=GREEN_EDGE, width=max(2, S // 3))

    # B-pillar and the front-door shut, plus the rear door's swept trailing edge.
    draw.line([P(0.600, 0.64), XZ(0.600 * L, glass_top(0.600 * L))], fill=IVORY_DIM, width=max(2, S // 2))
    draw.line([P(0.350, 0.64), P(0.350, 0.14)], fill=GREEN_EDGE, width=max(2, S // 2))
    draw.line([P(0.600, 0.64), P(0.600, 0.16)], fill=GREEN_EDGE, width=max(2, S // 2))
    trail = smooth(
        [
            (0.790 * L, belt),
            (0.770 * L, 0.42 * H),
            (0.740 * L, 0.24 * H),
            (0.720 * L, SILL_Z),
        ],
        steps=6,
    )
    draw.line([XZ(x, z) for x, z in trail], fill=GREEN_EDGE, width=max(2, S // 2))

    # Belt line.
    draw.line([P(0.40, 0.64), P(0.93, 0.64)], fill=COPPER_HI, width=max(2, S // 2))

    # Door handles, flush ovals.
    for xf in (0.51, 0.74):
        draw.rounded_rectangle(
            box2(P(xf - 0.02, 0.577), P(xf + 0.02, 0.562)),
            radius=int(1.2 * S),
            fill=IVORY_DIM,
            outline=GREEN_EDGE,
            width=max(1, S // 4),
        )

    # Shoulder crease, handle back over the rear arch into the lamp.
    crease = smooth(
        [
            (0.51 * L, 0.57 * H),
            (0.66 * L, 0.60 * H),
            (0.84 * L, 0.64 * H),
            (0.95 * L, 0.58 * H),
        ],
        steps=6,
    )
    draw.line([XZ(x, z) for x, z in crease], fill=(186, 214, 196, 255), width=max(2, S // 3))

    # Front wing vent just behind the front arch.
    draw.rectangle(box2(P(0.332, 0.54), P(0.358, 0.16)), fill=(18, 32, 28, 255))
    for xf in (0.338, 0.346, 0.354):
        draw.line([P(xf, 0.50), P(xf, 0.20)], fill=(120, 140, 128, 255), width=max(1, S // 4))

    # Fuel filler, this side only (car's left, the side shown with the nose to the left).
    cap = 0.025 * L
    draw.rounded_rectangle(
        box2(XZ(0.84 * L - cap / 2, 0.63 * H + cap / 2), XZ(0.84 * L + cap / 2, 0.63 * H - cap / 2)),
        radius=int(1.4 * S),
        fill=IVORY,
        outline=INK,
        width=max(1, S // 3),
    )

    # Roof lip spoiler, overhanging the hatch glass by ~0.01 L.
    lip_poly = [P(0.800, 0.905), P(0.820, 0.912), P(0.832, 0.900), P(0.820, 0.888), P(0.805, 0.890)]
    draw.polygon(lip_poly, fill=CARBON)

    # Hatch shut line ahead of the lamp. The lamp itself is drawn after the wing.

    # Livery chevron and door roundel.
    chevron = [P(0.40, 0.30), P(0.70, 0.46), P(0.78, 0.40), P(0.72, 0.30), P(0.46, 0.22)]
    draw.polygon(chevron, fill=COPPER)
    draw.polygon(
        [P(0.42, 0.33), P(0.66, 0.44), P(0.70, 0.40), P(0.48, 0.30)],
        fill=COPPER_HI,
    )
    cx, cz = 0.47 * L, 0.36 * H
    rr = 0.034 * L
    draw.ellipse(
        box2(XZ(cx - rr, cz + rr), XZ(cx + rr, cz - rr)),
        fill=IVORY,
        outline=INK,
        width=max(2, S // 2),
    )
    text_center(draw, XZ(cx, cz), "47", font(11), INK)

    # Rear wing over the hatch glass. The endplate hangs below the chord; the
    # chord stays visible, matching the CA45 side sheet rather than a solid block.
    te, le = WING_TE, WING_LE
    wing_top, wing_bot = WING_TOP_Z, WING_BOT_Z
    ep_x0 = te - 0.080 * L
    pylon = [
        XZ(0.875 * L, 0.54 * H),
        XZ(0.892 * L, 0.52 * H),
        XZ(0.930 * L, wing_bot),
        XZ(0.910 * L, wing_bot),
    ]
    draw.polygon(pylon, fill=(78, 84, 88, 255), outline=INK)
    draw.rectangle(box2(XZ(ep_x0, wing_bot), XZ(te, ENDPLATE_BOT_Z)), fill=CARBON)
    draw.rectangle(
        box2(XZ(ep_x0, wing_top), XZ(te, ENDPLATE_BOT_Z)),
        outline=COPPER,
        width=max(2, S // 2),
    )
    draw.polygon(
        [
            XZ(le, wing_bot + WING_THICK * 0.35),
            XZ(le + 0.012 * L, wing_top),
            XZ(te, wing_top - 0.002 * H),
            XZ(te, wing_bot),
            XZ(le + 0.010 * L, wing_bot),
        ],
        fill=CARBON,
        outline=INK,
    )
    fin = [
        XZ(te - 0.026 * L, wing_top),
        XZ(te - 0.018 * L, wing_top + 0.040 * H),
        XZ(te - 0.008 * L, wing_top + 0.022 * H),
        XZ(te - 0.004 * L, wing_top),
    ]
    draw.polygon(fin, fill=COPPER_HI, outline=INK)
    tail = [P(0.860, 0.50), P(0.930, 0.64), P(1.000, 0.60), P(1.000, 0.46), P(0.910, 0.46)]
    draw.polygon(tail, fill=LAMP, outline=INK)
    draw.polygon([P(0.900, 0.52), P(0.960, 0.61), P(0.990, 0.56), P(0.940, 0.50)], fill=LAMP_HI)

    return down(canvas)


def bonnet_half(x_mm):
    """Bonnet panel half-width: 0.36 W at the leading edge, 0.42 W at the rear."""
    t = (x_mm - 0.08 * L) / (0.31 * L - 0.08 * L)
    t = max(0.0, min(1.0, t))
    return (0.36 + t * (0.42 - 0.36)) * W


def vent_polygon(side):
    """Parallelogram louvre. Front end nearer the centreline, rear end nearer the side, ~20°."""
    x0, x1 = 0.125 * L, 0.245 * L
    y_front = 0.50 * bonnet_half(x0)
    y_rear = min(y_front + math.tan(math.radians(20)) * (x1 - x0), 0.90 * bonnet_half(x1))
    dx = x1 - x0
    dy = (y_rear - y_front) * side
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    half = 6.5
    c0 = (x0, y_front * side)
    c1 = (x1, y_rear * side)
    corners = [
        (c0[0] + nx * half, c0[1] + ny * half),
        (c1[0] + nx * half, c1[1] + ny * half),
        (c1[0] - nx * half, c1[1] - ny * half),
        (c0[0] - nx * half, c0[1] - ny * half),
    ]
    return corners, c0, c1, (nx, ny)


def render_top():
    pad_x, pad_y = 18.0, 16.0
    canvas = new_canvas(pad_x + L + pad_x, pad_y + W + pad_y)
    origin_x = pad_x
    mid_y = pad_y + W / 2

    def PT(x_mm, y_mm):
        return ((origin_x + x_mm) * S, (mid_y - y_mm) * S)

    outline = [PT(x, y) for x, y in plan_outline_mm()]
    shadow(
        canvas,
        (
            (origin_x + 24) * S,
            (pad_y + W * 0.18) * S,
            (origin_x + L - 10) * S,
            (pad_y + W * 0.82) * S,
        ),
        alpha=60,
        blur=8,
    )

    body = poly_mask(canvas.size, outline)
    grad = vgradient(canvas.size, GREEN_HI, GREEN)
    paint(canvas, body, grad)
    draw = ImageDraw.Draw(canvas)
    draw.line(outline + [outline[0]], fill=GREEN_EDGE, width=max(2, S // 2), joint="curve")

    # Splitter lip, ~0.01 W outside the bumper face around the nose.
    lip = []
    for x, y in plan_outline_mm():
        if x > 0.16 * L:
            break
        scale = 1.0 + (0.010 * W) / max(y, 1.0)
        lip.append(PT(x, y * scale if y > 0 else y))
    # Rebuild both sides from the half table so the offset is outward.
    half = [(x, y) for x, y in plan_outline_mm() if y > 0 and x <= 0.16 * L]
    lip = [PT(x, y + 0.010 * W) for x, y in half]
    lip += [PT(x, -(y + 0.010 * W)) for x, y in reversed(half)]
    draw.line(lip, fill=CARBON, width=max(3, int(0.008 * W * S)), joint="curve")

    # Tyre slivers flush with the flare crowns.
    for ax in (FRONT_X, REAR_X):
        for sign in (1, -1):
            draw.rounded_rectangle(
                box2(
                    PT(ax - 18, sign * (0.50 * W + 1.5)),
                    PT(ax + 18, sign * (0.50 * W - TYRE_W * 0.35)),
                ),
                radius=int(3 * S),
                fill=TYRE,
            )

    # Side glass bands outside the roof island, foreshortened.
    glass = [
        PT(0.40 * L, 0.46 * W),
        PT(0.44 * L, 0.30 * W),
        PT(0.82 * L, 0.27 * W),
        PT(0.83 * L, 0.46 * W),
        PT(0.74 * L, 0.490 * W),
        PT(0.50 * L, 0.480 * W),
        PT(0.40 * L, 0.490 * W),
    ]
    for sign in (1, -1):
        draw.polygon([(p[0], mid_y * S - sign * (mid_y * S - p[1])) for p in glass], fill=GLASS)

    # Roof island, half-width 0.235 W, slight taper, ivory.
    roof = [
        PT(0.440 * L, 0.235 * W),
        PT(0.820 * L, 0.220 * W),
        PT(0.820 * L, -0.220 * W),
        PT(0.440 * L, -0.235 * W),
    ]
    draw.polygon(roof, fill=IVORY, outline=GREEN_EDGE)
    # Header vent / antenna slot: 0.03 L by 0.27 W, just behind the windscreen.
    draw.rounded_rectangle(
        box2(PT(0.455 * L, 0.135 * W), PT(0.485 * L, -0.135 * W)),
        radius=int(1.5 * S),
        fill=CARBON,
    )
    text_center(draw, PT(0.62 * L, 0), "47", font(14), GREEN_LO)

    # Windscreen trapezoid. Base half-width 0.42 W, top 0.30 W.
    screen = [
        PT(0.370 * L, 0.420 * W),
        PT(0.440 * L, 0.300 * W),
        PT(0.440 * L, -0.300 * W),
        PT(0.370 * L, -0.420 * W),
    ]
    draw.polygon(screen, fill=GLASS, outline=INK)
    draw.line([PT(0.385 * L, 0.28 * W), PT(0.430 * L, 0.20 * W)], fill=GLASS_HI, width=max(2, S // 2))

    # Cowl band between bonnet and screen.
    cowl = [
        PT(0.310 * L, 0.420 * W),
        PT(0.370 * L, 0.420 * W),
        PT(0.370 * L, -0.420 * W),
        PT(0.310 * L, -0.420 * W),
    ]
    draw.polygon(cowl, fill=(36, 78, 62, 255))

    # Bonnet panel. Rear edge bows rearward in the middle; leading edge is rounded.
    bonnet = []
    xs = [0.090 * L + (0.220 * L) * t / 16 for t in range(17)]
    for x in xs:
        bonnet.append(PT(x, bonnet_half(x)))
    bow = smooth(
        [
            (0.310 * L, 0.420 * W),
            (0.332 * L, 0.210 * W),
            (0.350 * L, 0.0),
        ],
        steps=5,
    )
    for x, y in bow:
        bonnet.append(PT(x, y))
    for x, y in reversed(bow[:-1]):
        bonnet.append(PT(x, -y))
    for x in reversed(xs):
        bonnet.append(PT(x, -bonnet_half(x)))
    nose_edge = smooth(
        [
            (0.090 * L, -0.360 * W),
            (0.070 * L, -0.200 * W),
            (0.060 * L, 0.0),
            (0.070 * L, 0.200 * W),
            (0.090 * L, 0.360 * W),
        ],
        steps=5,
    )
    for x, y in nose_edge:
        bonnet.append(PT(x, y))
    draw.polygon(bonnet, fill=(78, 158, 118, 255), outline=GREEN_EDGE)

    # Four louvers per vent. Each slat runs along the 20° slot, front end nearer the centreline.
    for side in (1, -1):
        corners, c0, c1, normal = vent_polygon(side)
        draw.polygon([PT(x, y) for x, y in corners], outline=COPPER, width=max(2, S // 3))
        nx, ny = normal
        for k in range(4):
            offset = (k - 1.5) * 3.0
            draw.line(
                [
                    PT(c0[0] + nx * offset, c0[1] + ny * offset),
                    PT(c1[0] + nx * offset, c1[1] + ny * offset),
                ],
                fill=INK,
                width=max(3, S // 2),
            )

    # Grille slats and the nose badge / tow boss.
    draw.rounded_rectangle(
        box2(PT(0.012 * L, 0.070 * W), PT(0.048 * L, -0.070 * W)),
        radius=int(2 * S),
        fill=(12, 16, 16, 255),
    )
    for i in range(5):
        y = -0.050 * W + i * (0.100 * W / 4)
        draw.line([PT(0.016 * L, y), PT(0.044 * L, y)], fill=(150, 158, 150, 255), width=max(1, S // 4))
    draw.ellipse(box2(PT(0.055 * L, 0.011 * L), PT(0.075 * L, -0.011 * L)), fill=COPPER, outline=IVORY)

    # Headlamps: long swept lenses between the bonnet edge and the bumper lip, back to x=0.20.
    for side in (1, -1):
        lamp = smooth(
            [
                (0.048 * L, side * 0.30 * W),
                (0.090 * L, side * 0.455 * W),
                (0.150 * L, side * 0.488 * W),
                (0.200 * L, side * 0.455 * W),
                (0.175 * L, side * 0.420 * W),
                (0.110 * L, side * 0.400 * W),
                (0.060 * L, side * 0.340 * W),
            ],
            steps=4,
        )
        draw.polygon([PT(x, y) for x, y in lamp], fill=LENS, outline=INK)
        draw.polygon(
            [
                PT(0.085 * L, side * 0.40 * W),
                PT(0.145 * L, side * 0.465 * W),
                PT(0.170 * L, side * 0.440 * W),
                PT(0.105 * L, side * 0.385 * W),
            ],
            fill=AMBER,
        )

    # Hatch glass, rounded trapezoid, half-width 0.30 → 0.27.
    hatch = [
        PT(0.820 * L, 0.300 * W),
        PT(0.860 * L, 0.285 * W),
        PT(0.890 * L, 0.270 * W),
        PT(0.890 * L, -0.270 * W),
        PT(0.860 * L, -0.285 * W),
        PT(0.820 * L, -0.300 * W),
    ]
    draw.polygon(hatch, fill=(36, 64, 74, 255), outline=INK)
    draw.line([PT(0.835 * L, 0.12 * W), PT(0.875 * L, -0.04 * W)], fill=GLASS_HI, width=max(2, S // 2))
    # D-pillar bands.
    for side in (1, -1):
        draw.polygon(
            [
                PT(0.820 * L, side * 0.300 * W),
                PT(0.890 * L, side * 0.270 * W),
                PT(0.890 * L, side * 0.340 * W),
                PT(0.820 * L, side * 0.380 * W),
            ],
            fill=GREEN_LO,
        )

    # Rear lamps wrapping the quarter at the lower corners of the glass.
    for side in (1, -1):
        draw.polygon(
            [
                PT(0.820 * L, side * 0.250 * W),
                PT(0.860 * L, side * 0.300 * W),
                PT(0.885 * L, side * 0.420 * W),
                PT(0.840 * L, side * 0.450 * W),
                PT(0.820 * L, side * 0.340 * W),
            ],
            fill=LAMP,
            outline=INK,
        )

    # Wing plank, span 0.97 W, chord 0.066 L, plus endplates and three fins.
    chord = 0.066 * L
    te = 0.960 * L
    le = te - chord
    span = 0.485 * W
    draw.rectangle(box2(PT(le, span), PT(te, -span)), fill=CARBON, outline=INK)
    draw.line([PT(le + chord * 0.15, span * 0.9), PT(le + chord * 0.15, -span * 0.9)], fill=(90, 94, 98, 255), width=max(2, S // 3))
    # Arch-flare lines, the inner contour the CA45 plan uses at each axle.
    for axle in (FRONT_X, REAR_X):
        for side in (1, -1):
            flare = smooth(
                [
                    (axle - 0.07 * L, side * 0.478 * W),
                    (axle, side * 0.448 * W),
                    (axle + 0.07 * L, side * 0.478 * W),
                ],
                steps=5,
            )
            draw.line([PT(x, y) for x, y in flare], fill=GREEN_EDGE, width=max(2, S // 3))

    ep_len = 0.080 * L
    ep_w = 0.032 * W
    for side in (1, -1):
        y_outer = side * 0.518 * W
        y_inner = side * (0.518 * W - ep_w)
        draw.rectangle(
            box2(PT(te - ep_len, y_outer), PT(te, y_inner)),
            fill=(48, 52, 56, 255),
            outline=COPPER,
            width=max(2, S // 2),
        )
    full = 0.97 * W
    for frac in (0.25, 0.50, 0.75):
        y = -full / 2 + frac * full
        nose_x = te - 0.028 * L
        tail_x = te - 0.006 * L
        fin = [
            PT(nose_x, y),
            PT(nose_x + 0.008 * L, y + 0.014 * W),
            PT(tail_x, y + 0.006 * W),
            PT(tail_x, y - 0.006 * W),
            PT(nose_x + 0.008 * L, y - 0.014 * W),
        ]
        draw.polygon(fin, fill=COPPER_HI, outline=INK)

    # Plate recess seen on the rear face, and door-shut ticks.
    draw.rectangle(box2(PT(0.978 * L, 0.125 * W), PT(L, -0.125 * W)), fill=(28, 32, 30, 255), outline=INK)
    for xf in (0.35, 0.60, 0.76):
        for side in (1, -1):
            draw.line(
                [PT(xf * L, side * 0.30 * W), PT(xf * L, side * 0.48 * W)],
                fill=GREEN_EDGE,
                width=max(2, S // 3),
            )

    # Fuel cap on the car's left only (negative y, bottom of this view).
    cap = 0.025 * L
    draw.rounded_rectangle(
        box2(PT(0.84 * L - cap / 2, -0.40 * W + cap / 2), PT(0.84 * L + cap / 2, -0.40 * W - cap / 2)),
        radius=int(1.5 * S),
        fill=IVORY,
        outline=INK,
        width=max(1, S // 3),
    )
    return down(canvas)


def render_back():
    pad_x, pad_t, pad_b = 22.0, 18.0, 20.0
    canvas = new_canvas(pad_x + W + pad_x, pad_t + H + pad_b)
    mid = pad_x + W / 2
    ground = pad_t + H

    def PT(y_mm, z_mm):
        # Car left (negative y) on the image left. This is the side with the filler cap.
        return ((mid + y_mm) * S, (ground - z_mm) * S)

    shadow(
        canvas,
        (
            (mid - 0.42 * W) * S,
            (ground - 1) * S,
            (mid + 0.42 * W) * S,
            (ground + 8) * S,
        ),
        alpha=75,
        blur=7,
    )

    # Rear tyres: we see the tread, not the rim face. The arch covers the upper half.
    tyre_draw = ImageDraw.Draw(canvas)
    for sign in (1, -1):
        outer = sign * (0.50 * W)
        inner = sign * (0.50 * W - TYRE_W)
        top = AXLE_Z + TYRE_R
        bot = AXLE_Z - TYRE_R
        box = [PT(inner, top), PT(outer, bot)]
        box = [min(box[0][0], box[1][0]), min(box[0][1], box[1][1]), max(box[0][0], box[1][0]), max(box[0][1], box[1][1])]
        tyre_draw.rounded_rectangle(box, radius=int(6 * S), fill=TYRE)

    # Shell silhouette. Roof is the ortho maximum (the peak, forward of this face).
    # Glasshouse narrows to the 0.235 W roof rail; tumblehome reads in that inset.
    half = smooth(
        [
            (0.400 * W, 0.120 * H),
            (0.455 * W, 0.150 * H),
            (0.500 * W, 0.230 * H),
            (0.500 * W, 0.520 * H),
            (0.470 * W, 0.640 * H),
            (0.390 * W, 0.760 * H),
            (0.300 * W, 0.880 * H),
            (0.235 * W, 0.955 * H),
            (0.120 * W, 0.990 * H),
            (0.000 * W, 1.000 * H),
        ],
        steps=8,
    )
    right = [PT(y, z) for y, z in half]
    left = [PT(-y, z) for y, z in reversed(half)]
    shell = right + left
    mask = poly_mask(canvas.size, shell)
    paint(canvas, mask, vgradient(canvas.size, IVORY, GREEN_LO))

    draw = ImageDraw.Draw(canvas)
    # Ivory only on the roof dome. Repaint the body below the belt in green.
    below = [
        PT(-0.50 * W, 0.86 * H),
        PT(0.50 * W, 0.86 * H),
        PT(0.50 * W, 0.0),
        PT(-0.50 * W, 0.0),
    ]
    below_mask = poly_mask(canvas.size, below)
    clipped = Image.new("L", canvas.size, 0)
    clipped.paste(below_mask, mask=mask)
    paint(canvas, clipped, vgradient(canvas.size, GREEN_HI, GREEN_LO))
    draw.line(shell + [shell[0]], fill=GREEN_EDGE, width=max(2, S // 2), joint="curve")

    # Roof lip above the glass.
    draw.polygon(
        [
            PT(-0.26 * W, 0.905 * H),
            PT(0.26 * W, 0.905 * H),
            PT(0.24 * W, 0.875 * H),
            PT(-0.24 * W, 0.875 * H),
        ],
        fill=CARBON,
    )

    # Hatch glass, wider at the belt, under the lip.
    glass = [
        PT(-0.21 * W, 0.875 * H),
        PT(0.21 * W, 0.875 * H),
        PT(0.30 * W, 0.66 * H),
        PT(-0.30 * W, 0.66 * H),
    ]
    draw.polygon(glass, fill=GLASS, outline=INK)
    draw.line([PT(-0.12 * W, 0.84 * H), PT(0.16 * W, 0.78 * H)], fill=GLASS_HI, width=max(2, S // 2))

    # Two-lobe tail lamps. Inner lobe on the hatch, outer lobe wrapping the quarter.
    for sign in (1, -1):
        inner = [
            PT(sign * 0.06 * W, 0.64 * H),
            PT(sign * 0.20 * W, 0.655 * H),
            PT(sign * 0.22 * W, 0.50 * H),
            PT(sign * 0.10 * W, 0.49 * H),
        ]
        outer = [
            PT(sign * 0.25 * W, 0.62 * H),
            PT(sign * 0.42 * W, 0.60 * H),
            PT(sign * 0.47 * W, 0.52 * H),
            PT(sign * 0.36 * W, 0.48 * H),
            PT(sign * 0.26 * W, 0.50 * H),
        ]
        draw.polygon(inner, fill=LAMP, outline=INK)
        draw.polygon(outer, fill=LAMP, outline=INK)
        draw.polygon(
            [
                PT(sign * 0.15 * W, 0.60 * H),
                PT(sign * 0.24 * W, 0.585 * H),
                PT(sign * 0.23 * W, 0.54 * H),
                PT(sign * 0.16 * W, 0.545 * H),
            ],
            fill=LAMP_HI,
        )

    # Number-plate recess, 0.25 W by 0.07 H, centred near 0.45 H.
    plate = [PT(-0.125 * W, 0.485 * H), PT(0.125 * W, 0.415 * H)]
    plate = [
        min(plate[0][0], plate[1][0]),
        min(plate[0][1], plate[1][1]),
        max(plate[0][0], plate[1][0]),
        max(plate[0][1], plate[1][1]),
    ]
    draw.rounded_rectangle(plate, radius=int(1.5 * S), fill=(232, 232, 226, 255), outline=INK, width=max(2, S // 3))
    text_center(draw, ((plate[0] + plate[2]) / 2, (plate[1] + plate[3]) / 2), "47", font(8), INK)

    # Bumper face and diffuser band, with a vertical slot in each lower corner.
    draw.rectangle(box2(PT(-0.42 * W, 0.42 * H), PT(0.42 * W, 0.12 * H)), outline=GREEN_EDGE, width=max(2, S // 3))
    step_z = 0.12 * H + (0.42 - 0.12) * H / 3
    draw.line([PT(-0.42 * W, step_z), PT(0.42 * W, step_z)], fill=CARBON, width=max(3, S // 2))
    draw.rectangle(box2(PT(-0.40 * W, step_z), PT(0.40 * W, 0.12 * H)), fill=(14, 16, 16, 255))
    for sign in (1, -1):
        outer_y = sign * 0.370 * W
        inner_y = sign * (0.370 * W - 0.030 * W)
        slot = box2(PT(outer_y, 0.125 * H), PT(inner_y, 0.125 * H + 0.115 * H))
        draw.rectangle(slot, fill=(232, 220, 190, 255), outline=INK, width=max(2, S // 3))
        draw.rectangle(
            (slot[0] + 2 * S, slot[1] + 2 * S, slot[2] - 2 * S, slot[3] - 2 * S),
            fill=(8, 8, 8, 255),
        )

    # Side-skirt lip at the outer edges.
    for sign in (1, -1):
        draw.polygon(
            [
                PT(sign * 0.50 * W, 0.20 * H),
                PT(sign * 0.50 * W, 0.145 * H),
                PT(sign * 0.40 * W, 0.130 * H),
                PT(sign * 0.42 * W, 0.20 * H),
            ],
            fill=CARBON,
        )

    # Filler cap hint on the car's left quarter only.
    cap = 0.018 * W
    draw.rounded_rectangle(
        box2(PT(-0.48 * W, 0.70 * H), PT(-0.48 * W + cap, 0.70 * H - cap)),
        radius=int(1.2 * S),
        fill=IVORY,
        outline=INK,
        width=max(1, S // 4),
    )

    # Wing plank over the glass. Endplates hang to the lamp line, as on the CA45 sheet.
    wing_top, wing_bot = WING_TOP_Z, WING_BOT_Z
    span = 0.485 * W
    draw.rectangle(box2(PT(-span, wing_top), PT(span, wing_bot)), fill=CARBON, outline=INK)
    draw.line(
        [PT(-span * 0.92, wing_top - WING_THICK * 0.35), PT(span * 0.92, wing_top - WING_THICK * 0.35)],
        fill=(90, 94, 98, 255),
        width=max(2, S // 3),
    )
    ep_w = 0.032 * W
    for sign in (1, -1):
        draw.rectangle(
            box2(PT(sign * 0.518 * W, wing_top), PT(sign * (0.518 * W - ep_w), ENDPLATE_BOT_Z)),
            fill=CARBON,
            outline=COPPER,
            width=max(2, S // 2),
        )
    # Fins at 25, 50 and 75 percent of the span.
    full = 0.97 * W
    for frac in (0.25, 0.50, 0.75):
        y = -full / 2 + frac * full
        draw.polygon(
            [
                PT(y - 0.016 * W, wing_top),
                PT(y, wing_top + 0.062 * H),
                PT(y + 0.016 * W, wing_top),
            ],
            fill=COPPER_HI,
            outline=INK,
        )
    # Two swept pylons, a third of the span apart, centred, from above the plate to the wing.
    gap = full / 3
    for sign in (1, -1):
        y = sign * gap / 2
        draw.polygon(
            [
                PT(y - 0.012 * W, 0.50 * H),
                PT(y + 0.016 * W, 0.50 * H),
                PT(y + 0.010 * W, wing_bot),
                PT(y - 0.006 * W, wing_bot),
            ],
            fill=(32, 36, 38, 255),
            outline=INK,
        )

    # Cover the upper half of each tyre with the arch so the shell reads as the cover.
    for sign in (1, -1):
        outer = sign * 0.50 * W
        inner = sign * (0.50 * W - TYRE_W - 2)
        cover = [
            PT(inner, AXLE_Z + TYRE_R + 2),
            PT(outer, AXLE_Z + TYRE_R + 2),
            PT(outer, AXLE_Z),
            PT(inner, AXLE_Z + 0.01 * H),
        ]
        # Only the part that is actually shell. Use the body mask.
        cover_mask = poly_mask(canvas.size, cover)
        hold = Image.new("L", canvas.size, 0)
        hold.paste(cover_mask, mask=mask)
        paint(canvas, hold, GREEN)

    return down(canvas)


def sheet(side, top, back):
    gap = 28
    label_h = 36
    width = max(side.width, top.width, back.width) + 48
    height = 64 + side.height + top.height + back.height + label_h * 3 + gap * 4
    board = Image.new("RGBA", (width, height), (14, 22, 20, 255))
    draw = ImageDraw.Draw(board)
    face = font(11)
    title = font(16)
    draw.text((24, 16), "FWD 1/10 touring hatch  ·  grok-4.7  ·  high", font=title, fill=IVORY)
    y = 64
    for image, caption in (
        (side, "Side  ·  nose left  ·  left side, filler cap visible"),
        (top, "Top  ·  nose left"),
        (back, "Back  ·  car left on the image left"),
    ):
        draw.text((24, y), caption, font=face, fill=COPPER_HI)
        y += label_h - 8
        x = (width - image.width) // 2
        board.alpha_composite(image, (x, y))
        y += image.height + gap
    return board


def main():
    side = render_side()
    top = render_top()
    back = render_back()
    side.save(HERE / "side.png")
    top.save(HERE / "top.png")
    back.save(HERE / "back.png")
    sheet(side, top, back).save(HERE / "sprite-sheet.png")
    for name, image in (("side", side), ("top", top), ("back", back)):
        print(f"{name}.png {image.size[0]}x{image.size[1]} mode={image.mode}")


if __name__ == "__main__":
    main()
