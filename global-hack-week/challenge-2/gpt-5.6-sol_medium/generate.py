#!/usr/bin/env python3
"""Render three orthographic sprites for a 1/10 FWD touring-car shell.

Model: GPT-5.6 Sol
Reasoning level: medium
Geometry source: ../BASE_PROMPT.md
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE.parent / ".vendor"
if VENDOR.is_dir():
    sys.path.insert(0, str(VENDOR))

from PIL import Image, ImageDraw, ImageFont

SS = 3
INK = "#111827"
INK2 = "#263449"
WHITE = "#f7f8f4"
SILVER = "#cbd5df"
CYAN = "#00d7d7"
CYAN_D = "#008f9b"
MAGENTA = "#ed2b78"
AMBER = "#ffcc33"
RED = "#ff315b"
GLASS = "#17283d"
GLASS_HI = "#7898ad"
TYRE = "#171a20"
RIM = "#9eabb8"


def U(value):
    return int(round(value * SS))


def pts(values):
    return [(U(x), U(y)) for x, y in values]


def box(values):
    return tuple(U(v) for v in values)


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, U(size))
        except OSError:
            pass
    return ImageFont.load_default()


def new_canvas(size):
    return Image.new("RGBA", (U(size[0]), U(size[1])), (0, 0, 0, 0))


def downsample(image):
    return image.resize((image.width // SS, image.height // SS), Image.Resampling.LANCZOS)


def gradient_layer(size, top, bottom, horizontal=False):
    im = new_canvas(size)
    a = Image.new("RGBA", (1 if horizontal else im.width, im.height if horizontal else 1))
    d = ImageDraw.Draw(a)
    count = a.height if horizontal else a.width
    # A one-pixel strip is expanded; interpolation gives a smooth deterministic gradient.
    c0 = ImageColor.getrgb(top)
    c1 = ImageColor.getrgb(bottom)
    for i in range(count):
        t = i / max(1, count - 1)
        c = tuple(round(c0[j] * (1 - t) + c1[j] * t) for j in range(3))
        if horizontal:
            d.point((0, i), fill=(*c, 255))
        else:
            d.point((i, 0), fill=(*c, 255))
    return a.resize(im.size, Image.Resampling.BILINEAR)


# Pillow keeps ImageColor separate from ImageDraw.
from PIL import ImageColor


def composite_mask(base, fill, mask):
    base.alpha_composite(Image.composite(fill, Image.new("RGBA", base.size), mask))


def catmull(points, steps=10):
    out = []
    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]
        for n in range(steps):
            t = n / steps
            t2, t3 = t * t, t * t * t
            x = .5 * ((2*p1[0]) + (-p0[0]+p2[0])*t +
                      (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 +
                      (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y = .5 * ((2*p1[1]) + (-p0[1]+p2[1])*t +
                      (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 +
                      (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            out.append((x, y))
    out.append(points[-1])
    return out


def line(draw, values, fill=INK, width=2, joint="curve"):
    draw.line(pts(values), fill=fill, width=U(width), joint=joint)


def polygon(draw, values, fill, outline=None, width=1):
    draw.polygon(pts(values), fill=fill)
    if outline:
        line(draw, values + [values[0]], outline, width)


def rounded(draw, values, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box(values), radius=U(radius), fill=fill,
                           outline=outline, width=U(width))


def ellipse(draw, values, fill, outline=None, width=1):
    draw.ellipse(box(values), fill=fill, outline=outline, width=U(width))


def wheel(canvas, cx, cy, radius=51):
    d = ImageDraw.Draw(canvas)
    ellipse(d, (cx-radius, cy-radius, cx+radius, cy+radius), TYRE, INK, 2)
    ellipse(d, (cx-radius*.67, cy-radius*.67, cx+radius*.67, cy+radius*.67),
            RIM, "#4c5967", 2)
    ellipse(d, (cx-radius*.52, cy-radius*.52, cx+radius*.52, cy+radius*.52),
            "#25303c", "#d5dde5", 1)
    for k in range(5):
        a = math.radians(k*72-90)
        for off in (-.09, .09):
            aa = a + off
            p0 = (cx+math.cos(aa)*radius*.13, cy+math.sin(aa)*radius*.13)
            p1 = (cx+math.cos(aa-.055)*radius*.49, cy+math.sin(aa-.055)*radius*.49)
            p2 = (cx+math.cos(aa+.055)*radius*.49, cy+math.sin(aa+.055)*radius*.49)
            polygon(d, [p0, p1, p2], "#9aa7b4")
    ellipse(d, (cx-8, cy-8, cx+8, cy+8), "#d8dee5", INK, 1)
    ellipse(d, (cx-3, cy-3, cx+3, cy+3), MAGENTA)


def side_sprite():
    size = (1000, 430)
    im = new_canvas(size)
    d = ImageDraw.Draw(im)
    x0, ground, length, height = 70, 351, 850, 242
    X = lambda f: x0 + f*length
    Z = lambda f: ground - f*height

    # Soft grounding shadow.
    ellipse(d, (X(.02), ground-2, X(.99), ground+27), (8, 16, 28, 45))

    # Wheels are placement reference and sit behind the shell.
    wheel(im, X(.235), Z(.26), 62)
    wheel(im, X(.84), Z(.26), 62)

    stations = [
        (0, .10), (.03, .10), (.045, .34), (.08, .49), (.20, .59),
        (.36, .73), (.37, .73), (.44, .93), (.53, .98), (.63, 1),
        (.72, .97), (.82, .91), (.93, .66), (.97, .45), (1, .12)
    ]
    roof = catmull([(X(x), Z(z)) for x, z in stations], 12)
    sill = Z(.14)
    body_poly = roof + [(X(1), Z(.12)), (X(.91), sill), (X(.12), sill),
                        (X(.03), Z(.10)), (X(0), Z(.05))]
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    md.polygon(pts(body_poly), fill=255)
    arch_r = .085*length
    for axle in (.235, .84):
        md.ellipse(box((X(axle)-arch_r, Z(.26)-arch_r,
                        X(axle)+arch_r, Z(.26)+arch_r)), fill=0)
    fill = gradient_layer(size, "#ffffff", "#a9b6c2", horizontal=True)
    composite_mask(im, fill, mask)
    d = ImageDraw.Draw(im)
    line(d, body_poly + [body_poly[0]], INK, 3)

    # Splitter, skirt and arch flare lips.
    polygon(d, [(X(-.012), Z(.05)), (X(.055), Z(.05)), (X(.055), Z(.10)),
                (X(0), Z(.10)), (X(0), Z(.14)), (X(-.012), Z(.14))], INK, INK, 1)
    rounded(d, (X(.33), sill-1, X(.74), sill+9), 3, INK, "#05080e", 1)
    for axle in (.235, .84):
        a = []
        for n in range(31):
            ang = math.pi + n*math.pi/30
            a.append((X(axle)+math.cos(ang)*arch_r,
                      Z(.26)+math.sin(ang)*arch_r))
        line(d, a, "#506070", 7)
        line(d, a, INK, 2)

    # Glass ring split into three panes.
    glass_top = [(X(.40), Z(.75)), (X(.44), Z(.91)), (X(.54), Z(.965)),
                 (X(.63), Z(.98)), (X(.74), Z(.955)), (X(.82), Z(.90))]
    glass_poly = catmull(glass_top, 10) + [(X(.83), Z(.64)), (X(.40), Z(.64))]
    polygon(d, glass_poly, GLASS, INK, 2)
    polygon(d, [(X(.405), Z(.64)), (X(.447), Z(.64)), (X(.418), Z(.745))],
            GLASS_HI, INK2, 1)
    line(d, [(X(.60), Z(.974)), (X(.60), Z(.64))], INK, 4)
    line(d, [(X(.76), Z(.945)), (X(.76), Z(.64))], INK, 3)
    polygon(d, [(X(.795), Z(.918)), (X(.825), Z(.89)), (X(.83), Z(.64)),
                (X(.80), Z(.64))], INK2)
    line(d, [(X(.40), Z(.64)), (X(.93), Z(.64))], INK, 2)

    # Body panels and aero details.
    line(d, [(X(.10), Z(.52)), (X(.23), Z(.58)), (X(.37), Z(.72))], "#526270", 2)
    line(d, [(X(.12), Z(.47)), (X(.22), Z(.51)), (X(.34), Z(.61))], "#8996a2", 1)
    line(d, [(X(.35), Z(.64)), (X(.35), sill)], "#697785", 1.5)
    line(d, [(X(.60), Z(.64)), (X(.59), sill)], "#697785", 1.5)
    line(d, [(X(.79), Z(.64)), (X(.76), Z(.42)), (X(.72), sill)], "#697785", 1.5)
    line(d, [(X(.83), Z(.89)), (X(.855), Z(.82)), (X(.93), Z(.66))], "#526270", 2)
    line(d, [(X(.91), Z(.42)), (X(.97), Z(.40)), (X(.99), Z(.29))], "#697785", 1.5)
    line(d, [(X(.48), Z(.575)), (X(.66), Z(.59)), (X(.91), Z(.61))], CYAN_D, 3)
    for hx in (.51, .74):
        rounded(d, (X(hx-.018), Z(.578), X(hx+.018), Z(.562)), 3, WHITE, INK, 1)
    rounded(d, (X(.332), Z(.52), X(.36), sill), 4, INK2, INK, 1)
    for z in (.29, .38, .47):
        line(d, [(X(.337), Z(z)), (X(.356), Z(z+.025))], CYAN, 2)
    # Donor-shell fuel cap, shown on this side only.
    rounded(d, (X(.825), Z(.675), X(.855), Z(.595)), 5, "#dce3e5", INK2, 1.5)

    # Lamps and two-tone race livery.
    polygon(d, [(X(.04), Z(.42)), (X(.20), Z(.55)), (X(.19), Z(.50)),
                (X(.06), Z(.46))], "#e9faff", INK, 2)
    # Blueprint-style deep lower mouth and brake duct in the tall front bumper.
    rounded(d, (X(.004), Z(.285), X(.125), Z(.12)), 12, INK2, INK, 2)
    rounded(d, (X(.018), Z(.255), X(.105), Z(.145)), 10, "#090d13", "#657483", 1)
    for xf in (.035, .052, .069, .086):
        line(d, [(X(xf), Z(.235)), (X(xf+.018), Z(.16))], "#5d6c7a", 1.5)
    rounded(d, (X(.005), Z(.38), X(.035), Z(.29)), 5, GLASS, INK, 1)
    polygon(d, [(X(.905), Z(.61)), (X(.944), Z(.63)), (X(.97), Z(.59)),
                (X(.962), Z(.49)), (X(.925), Z(.51))], RED, INK, 2)
    polygon(d, [(X(.18), Z(.18)), (X(.49), Z(.18)), (X(.68), Z(.53)),
                (X(.42), Z(.38))], CYAN, None)
    polygon(d, [(X(.43), Z(.18)), (X(.67), Z(.18)), (X(.79), Z(.42)),
                (X(.66), Z(.53))], MAGENTA, None)
    line(d, [(X(.18), Z(.18)), (X(.49), Z(.18)), (X(.68), Z(.53))], INK2, 1)
    # Small roof-lip spoiler above the steep hatch glass.
    polygon(d, [(X(.805), Z(.925)), (X(.845), Z(.895)), (X(.858), Z(.87)),
                (X(.818), Z(.89))], "#dce3e5", INK, 1)

    # Number disc.
    ellipse(d, (X(.42)-25, Z(.40)-25, X(.42)+25, Z(.40)+25), WHITE, INK, 2)
    label = "26"
    f = font(28, True)
    bb = d.textbbox((0, 0), label, font=f)
    d.text((U(X(.42))-((bb[2]-bb[0])//2), U(Z(.40))-((bb[3]-bb[1])//2)-U(2)),
           label, font=f, fill=INK)

    # Full-width wing projected in side view: pylon, plank, endplate and fin.
    polygon(d, [(X(.895), Z(.60)), (X(.916), Z(.60)), (X(.943), Z(1.055)),
                (X(.925), Z(1.055))], INK2, INK, 1)
    rounded(d, (X(.885), Z(1.105), X(.97), Z(1.055)), 3, INK, "#05080e", 1)
    rounded(d, (X(.882), Z(1.105), X(.899), Z(.99)), 2, MAGENTA, INK, 1)
    polygon(d, [(X(.925), Z(1.105)), (X(.94), Z(1.145)), (X(.95), Z(1.105))],
            CYAN, INK, 1)
    return downsample(im)


def half_width(x):
    table = [(0, .15), (.12, .50), (.32, .50), (.55, .49), (.74, .49),
             (.84, .50), (.92, .50), (1, .40)]
    for (x0, w0), (x1, w1) in zip(table, table[1:]):
        if x0 <= x <= x1:
            t = (x-x0)/(x1-x0)
            return w0*(1-t)+w1*t
    return table[-1][1]


def top_sprite():
    size = (1000, 470)
    im = new_canvas(size)
    d = ImageDraw.Draw(im)
    x0, length, cy, width = 70, 850, 235, 370
    X = lambda f: x0+f*length
    Y = lambda f: cy+f*width

    ellipse(d, (X(.01), Y(-.48)+10, X(.995), Y(.48)+18), (8, 16, 28, 35))
    samples = [i/80 for i in range(81)]
    outline = [(X(x), Y(-half_width(x))) for x in samples]
    outline += [(X(x), Y(half_width(x))) for x in reversed(samples)]
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(pts(outline), fill=255)
    composite_mask(im, gradient_layer(size, "#ffffff", "#a7b5c2"), mask)
    d = ImageDraw.Draw(im)
    line(d, outline+[outline[0]], INK, 3)

    # Front splitter double line and swept headlamps.
    front = [(X(-.008), Y(-.16)), (X(.02), Y(-.43)), (X(.10), Y(-.51)),
             (X(.10), Y(.51)), (X(.02), Y(.43)), (X(-.008), Y(.16))]
    line(d, front, INK, 7)
    line(d, front, CYAN_D, 2)
    for sign in (-1, 1):
        polygon(d, [(X(.025), Y(sign*.18)), (X(.07), Y(sign*.40)),
                    (X(.20), Y(sign*.47)), (X(.11), Y(sign*.30))],
                "#e9faff", INK, 2)

    # Bonnet with rearward-bowed scuttle.
    bonnet = [(X(.08), Y(-.36)), (X(.14), Y(-.39)), (X(.30), Y(-.42)),
              (X(.32), Y(0)), (X(.30), Y(.42)), (X(.14), Y(.39)),
              (X(.08), Y(.36))]
    polygon(d, bonnet, "#edf1ef", "#5b6875", 2)
    for sign in (-1, 1):
        vent = [(X(.12), Y(sign*.15)), (X(.145), Y(sign*.29)),
                (X(.24), Y(sign*.35)), (X(.215), Y(sign*.21))]
        polygon(d, vent, INK2, INK, 1)
        for i in range(4):
            xf = .14+i*.023
            line(d, [(X(xf), Y(sign*(.18+i*.015))),
                     (X(xf+.035), Y(sign*(.29+i*.015)))], CYAN, 2)

    # Cowl, windscreen, roof island, side glass and hatch glass.
    polygon(d, [(X(.31), Y(-.42)), (X(.37), Y(-.42)), (X(.37), Y(.42)),
                (X(.31), Y(.42))], INK2, INK, 1)
    polygon(d, [(X(.37), Y(-.42)), (X(.44), Y(-.30)), (X(.44), Y(.30)),
                (X(.37), Y(.42))], GLASS, INK, 2)
    polygon(d, [(X(.44), Y(-.42)), (X(.82), Y(-.42)), (X(.82), Y(.42)),
                (X(.44), Y(.42))], "#29415a", INK, 1)
    roof = [(X(.44), Y(-.235)), (X(.80), Y(-.22)), (X(.82), Y(-.19)),
            (X(.82), Y(.19)), (X(.80), Y(.22)), (X(.44), Y(.235))]
    polygon(d, roof, WHITE, INK, 2)
    # Roof race stripe and vent marker.
    polygon(d, [(X(.44), Y(-.035)), (X(.82), Y(-.035)),
                (X(.82), Y(.035)), (X(.44), Y(.035))], MAGENTA)
    rounded(d, (X(.465), Y(-.135), X(.495), Y(.135)), 4, INK2, INK, 1)
    polygon(d, [(X(.82), Y(-.30)), (X(.89), Y(-.27)), (X(.89), Y(.27)),
                (X(.82), Y(.30))], GLASS, INK, 2)

    # The schematic's pronounced shoulder channels frame the narrow roof island.
    for sign in (-1, 1):
        channel = [(X(.31), Y(sign*.42)), (X(.38), Y(sign*.45)),
                   (X(.47), Y(sign*.47)), (X(.74), Y(sign*.47)),
                   (X(.82), Y(sign*.43)), (X(.89), Y(sign*.35))]
        line(d, channel, "#536474", 3)
        highlight = [(x, y-sign*2) for x, y in channel]
        line(d, highlight, "#e8edef", 1)

    # Door and hatch shut lines visible from above.
    for xf in (.35, .60, .79):
        line(d, [(X(xf), Y(-.49)), (X(xf+.01), Y(-.41))], "#667584", 1.5)
        line(d, [(X(xf), Y(.49)), (X(xf+.01), Y(.41))], "#667584", 1.5)
    line(d, [(X(.89), Y(-.34)), (X(.93), Y(-.45))], "#667584", 1.5)
    line(d, [(X(.89), Y(.34)), (X(.93), Y(.45))], "#667584", 1.5)
    for sign in (-1, 1):
        for xf in (.51, .74):
            rounded(d, (X(xf-.015), Y(sign*.465)-3, X(xf+.015), Y(sign*.465)+3),
                    3, "#dce3e5", INK2, 1)
    # The fuel cap appears on one side only, matching the donor-shell blueprint.
    rounded(d, (X(.825), Y(.405), X(.855), Y(.475)), 4, "#dce3e5", INK2, 1)

    # Rear lamps under the wing.
    for sign in (-1, 1):
        polygon(d, [(X(.82), Y(sign*.31)), (X(.88), Y(sign*.43)),
                    (X(.90), Y(sign*.47)), (X(.845), Y(sign*.34))],
                RED, INK, 1)

    # Nearly full-width wing, endplates and three teardrop fins.
    rounded(d, (X(.89), Y(-.485), X(.956), Y(.485)), 3, INK, "#05080e", 2)
    rounded(d, (X(.882), Y(-.50), X(.965), Y(-.47)), 2, MAGENTA, INK, 1)
    rounded(d, (X(.882), Y(.47), X(.965), Y(.50)), 2, MAGENTA, INK, 1)
    for yf in (-.25, 0, .25):
        polygon(d, [(X(.925), Y(yf)-3), (X(.958), Y(yf)),
                    (X(.928), Y(yf)+3)], CYAN, INK, 1)

    # Front grille boss and graphic accents.
    ellipse(d, (X(.025)-7, cy-7, X(.025)+7, cy+7), MAGENTA, INK, 1)
    rounded(d, (X(.005), Y(-.11), X(.045), Y(.11)), 5, INK2, INK, 1)
    for yf in (-.07, -.035, 0, .035, .07):
        line(d, [(X(.013), Y(yf)), (X(.038), Y(yf))], "#738392", 1)
    for sign in (-1, 1):
        polygon(d, [(X(.48), Y(sign*.24)), (X(.73), Y(sign*.40)),
                    (X(.77), Y(sign*.42)), (X(.62), Y(sign*.24))], CYAN)
    return downsample(im)


def rear_sprite():
    size = (640, 560)
    im = new_canvas(size)
    d = ImageDraw.Draw(im)
    cx, ground, width, height = 320, 500, 500, 350
    Y = lambda f: cx+f*width
    Z = lambda f: ground-f*height

    ellipse(d, (Y(-.48), ground-3, Y(.48), ground+25), (8, 16, 28, 45))
    # Tyre edges, shown only as placement reference.
    rounded(d, (Y(-.53), Z(.34), Y(-.43), ground+4), 18, TYRE, INK, 2)
    rounded(d, (Y(.43), Z(.34), Y(.53), ground+4), 18, TYRE, INK, 2)

    # Tall domed shell with 15-degree tumblehome.
    shell = [(Y(-.50), Z(.12)), (Y(-.50), Z(.48)), (Y(-.45), Z(.66)),
             (Y(-.32), Z(.91)), (Y(-.20), Z(.99)), (cx, Z(1.02)),
             (Y(.20), Z(.99)), (Y(.32), Z(.91)), (Y(.45), Z(.66)),
             (Y(.50), Z(.48)), (Y(.50), Z(.12))]
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(pts(shell), fill=255)
    composite_mask(im, gradient_layer(size, "#ffffff", "#a8b5c0", horizontal=True), mask)
    d = ImageDraw.Draw(im)
    line(d, shell, INK, 3)

    # Wide raked hatch glass and roof lip.
    glass = [(Y(-.29), Z(.88)), (Y(-.20), Z(.96)), (Y(.20), Z(.96)),
             (Y(.29), Z(.88)), (Y(.34), Z(.63)), (Y(-.34), Z(.63))]
    polygon(d, glass, GLASS, INK, 3)
    line(d, [(Y(-.22), Z(.97)), (Y(.22), Z(.97))], INK, 9)
    line(d, [(Y(-.19), Z(.945)), (Y(.19), Z(.945))], GLASS_HI, 2)
    # Hatch aperture seams continue around the glass and into the lamp line.
    line(d, [(Y(-.34), Z(.63)), (Y(-.37), Z(.54)), (Y(-.30), Z(.45))],
         "#647483", 1.5)
    line(d, [(Y(.34), Z(.63)), (Y(.37), Z(.54)), (Y(.30), Z(.45))],
         "#647483", 1.5)
    line(d, [(Y(-.29), Z(.88)), (Y(-.20), Z(.96)), (Y(.20), Z(.96)),
             (Y(.29), Z(.88))], GLASS_HI, 1.5)

    # Twin two-lobe lamps.
    for sign in (-1, 1):
        inner = [(Y(sign*.08), Z(.60)), (Y(sign*.31), Z(.62)),
                 (Y(sign*.25), Z(.50)), (Y(sign*.08), Z(.52))]
        outer = [(Y(sign*.31), Z(.62)), (Y(sign*.47), Z(.58)),
                 (Y(sign*.46), Z(.49)), (Y(sign*.25), Z(.50))]
        polygon(d, inner, RED, INK, 2)
        polygon(d, outer, "#c71748", INK, 2)
        line(d, [(Y(sign*.16), Z(.57)), (Y(sign*.38), Z(.55))], "#ff9aae", 2)

    # Lower hatch, plate recess, diffuser and corner vents.
    rounded(d, (Y(-.125), Z(.49), Y(.125), Z(.42)), 5, INK2, INK, 2)
    label = "HF 26"
    f = font(19, True)
    bb = d.textbbox((0, 0), label, font=f)
    d.text((U(cx)-(bb[2]-bb[0])//2, U(Z(.455))-(bb[3]-bb[1])//2-U(1)),
           label, font=f, fill=WHITE)
    line(d, [(Y(-.48), Z(.30)), (Y(.48), Z(.30))], "#566575", 3)
    # Deep bumper shoulders from the three-quarter blueprint, flattened here
    # into a true orthographic rear view.
    line(d, [(Y(-.48), Z(.48)), (Y(-.43), Z(.38)), (Y(-.47), Z(.30))],
         "#697887", 2)
    line(d, [(Y(.48), Z(.48)), (Y(.43), Z(.38)), (Y(.47), Z(.30))],
         "#697887", 2)
    line(d, [(Y(-.37), Z(.38)), (Y(-.18), Z(.34)), (Y(.18), Z(.34)),
             (Y(.37), Z(.38))], "#86939e", 1.5)
    polygon(d, [(Y(-.47), Z(.28)), (Y(.47), Z(.28)), (Y(.43), Z(.12)),
                (Y(-.43), Z(.12))], INK2, INK, 2)
    for yf in (-.28, -.14, 0, .14, .28):
        line(d, [(Y(yf), Z(.13)), (Y(yf*.9), Z(.28))], "#718091", 2)
    for sign in (-1, 1):
        rounded(d, (Y(sign*.46-.018), Z(.25), Y(sign*.46+.018), Z(.13)),
                3, "#090c11", "#667584", 1)

    # Swept pylons and full-span wing with endplates and three fins.
    for sign in (-1, 1):
        polygon(d, [(Y(sign*.12-.025), Z(.56)), (Y(sign*.12+.025), Z(.56)),
                    (Y(sign*.20+.025), Z(.82)), (Y(sign*.20-.025), Z(.82))],
                INK2, INK, 2)
    rounded(d, (Y(-.485), Z(.88), Y(.485), Z(.81)), 5, INK, "#05080e", 2)
    rounded(d, (Y(-.50), Z(.90), Y(-.46), Z(.73)), 3, MAGENTA, INK, 2)
    rounded(d, (Y(.46), Z(.90), Y(.50), Z(.73)), 3, MAGENTA, INK, 2)
    for yf in (-.25, 0, .25):
        polygon(d, [(Y(yf-.025), Z(.88)), (Y(yf), Z(.94)),
                    (Y(yf+.025), Z(.88))], CYAN, INK, 1)

    # Cyan/magenta lower-quarter accents.
    polygon(d, [(Y(-.48), Z(.39)), (Y(-.12), Z(.38)), (Y(-.02), Z(.31)),
                (Y(-.46), Z(.31))], CYAN)
    polygon(d, [(Y(.48), Z(.39)), (Y(.12), Z(.38)), (Y(.02), Z(.31)),
                (Y(.46), Z(.31))], MAGENTA)
    return downsample(im)


def make_sheet(side, top, rear):
    sheet = Image.new("RGBA", (1740, 1070), (12, 18, 28, 255))
    # Checker-free dark presentation board; sprites remain transparent individually.
    sheet.alpha_composite(side, (30, 55))
    sheet.alpha_composite(top, (30, 520))
    sheet.alpha_composite(rear, (1080, 230))
    d = ImageDraw.Draw(sheet)
    title = font(28, True)
    small = font(16, True)
    d.text((32, 15), "HF26 // FWD TOURING HATCH", font=title, fill=WHITE)
    d.text((35, 465), "SIDE", font=small, fill=CYAN)
    d.text((35, 995), "TOP DOWN", font=small, fill=CYAN)
    d.text((1110, 800), "BACK", font=small, fill=CYAN)
    d.text((1085, 865), "1/10 • 440 × 190 × 125 mm", font=font(14), fill=SILVER)
    return sheet


def main():
    side = side_sprite()
    top = top_sprite()
    rear = rear_sprite()
    side.save(HERE / "side.png", optimize=True)
    top.save(HERE / "top.png", optimize=True)
    rear.save(HERE / "back.png", optimize=True)
    make_sheet(side, top, rear).save(HERE / "sprite-sheet.png", optimize=True)
    print("Rendered side.png, top.png, back.png and sprite-sheet.png")


if __name__ == "__main__":
    main()
