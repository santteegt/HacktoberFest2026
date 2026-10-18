# Generates the PartsPaddock logo (logo.svg) and the horizontal lockup (logo-lockup.svg) in this folder.
# Render to PNG with headless Chrome, as in docs: run from docs/logo with `python3 generate.py`.
import math, sys
BLUE='#0B5C8E'; ORANGE='#E8590C'; CREAM='#FFF7EC'; INK='#0F2A3D'
def gear(cx, cy, r_out, r_in, teeth, frac=0.5):
    pts=[]; step=2*math.pi/teeth
    for i in range(teeth):
        a=i*step-math.pi/2
        for ang,r in ((a,r_in),(a+step*frac*0.18,r_out),(a+step*frac*0.82,r_out),(a+step*frac,r_in)):
            pts.append((cx+r*math.cos(ang), cy+r*math.sin(ang)))
        for k in range(1,5):
            ang=a+step*frac+(step-step*frac)*k/5
            pts.append((cx+r_in*math.cos(ang), cy+r_in*math.sin(ang)))
    return 'M'+' L'.join(f'{x:.1f},{y:.1f}' for x,y in pts)+' Z'
def wheel(cx,cy,r,col=ORANGE,hub=CREAM):
    return (f'<path d="{gear(cx,cy,r,r*0.82,10)}" fill="{col}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*0.5:.1f}" fill="{hub}"/><circle cx="{cx}" cy="{cy}" r="{r*0.2:.1f}" fill="{INK}"/>')
def bot(cx,cy,s,body=CREAM,ink=BLUE):
    w=s; h=s*0.8; x=cx-w/2; y=cy-h/2
    return (f'<line x1="{cx}" y1="{y}" x2="{cx}" y2="{y-s*0.22:.1f}" stroke="{ink}" stroke-width="{s*0.07:.1f}" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{y-s*0.26:.1f}" r="{s*0.08:.1f}" fill="{ORANGE}"/>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s*0.22:.1f}" fill="{body}" stroke="{ink}" stroke-width="{s*0.07:.1f}"/>'
            f'<rect x="{x-s*0.1:.1f}" y="{cy-s*0.12:.1f}" width="{s*0.1:.1f}" height="{s*0.24:.1f}" rx="{s*0.04:.1f}" fill="{ink}"/>'
            f'<rect x="{x+w:.1f}" y="{cy-s*0.12:.1f}" width="{s*0.1:.1f}" height="{s*0.24:.1f}" rx="{s*0.04:.1f}" fill="{ink}"/>'
            f'<circle cx="{cx-s*0.2:.1f}" cy="{cy-s*0.05:.1f}" r="{s*0.09:.1f}" fill="{ink}"/><circle cx="{cx+s*0.2:.1f}" cy="{cy-s*0.05:.1f}" r="{s*0.09:.1f}" fill="{ink}"/>'
            f'<path d="M{cx-s*0.16:.1f},{cy+s*0.16:.1f} Q{cx},{cy+s*0.28:.1f} {cx+s*0.16:.1f},{cy+s*0.16:.1f}" stroke="{ink}" stroke-width="{s*0.06:.1f}" fill="none" stroke-linecap="round"/>')
def car(x,y,sc,col=INK,hub=CREAM,win=CREAM):
    # Low supercar-style touring silhouette, nose on the left, rear wing on the right; ~740x200 units.
    body=("M26,174 L30,140 Q58,112 120,100 L230,84 Q290,40 340,26 Q420,12 520,22 L640,50 L700,62 "
          "Q716,96 714,140 L710,174 L654.9,174 A50,50 0 1 0 565.1,174 L212.7,174 A48,48 0 1 0 127.3,174 Z")
    wing=(f'<path d="M598,16 L702,6 L706,22 L610,30 Z" fill="{col}"/>'
          f'<path d="M640,28 L654,28 L648,56 L632,56 Z" fill="{col}"/>')
    glass=(f'<path d="M296,82 Q326,50 358,38 L420,33 L414,80 Z" fill="{win}"/>'
           f'<path d="M428,33 L470,32 Q500,38 522,58 L424,78 Z" fill="{win}"/>')
    trim=(f'<path d="M292,116 Q380,104 482,98 L472,108 Q384,114 300,124 Z" fill="{win}" opacity="0.85"/>'
          f'<path d="M58,122 Q80,110 108,106 L102,115 Q82,119 62,127 Z" fill="{win}"/>'
          f'<path d="M686,72 L700,74 L702,86 L690,84 Z" fill="{win}"/>')
    return (f'<g transform="translate({x},{y}) scale({sc})"><path d="{body}" fill="{col}"/>{wing}{glass}{trim}'
            f'{wheel(170,152,44,hub=hub)}{wheel(610,152,44,hub=hub)}</g>')
def tx(x,y,sc,col=INK):
    body=("M60,40 L150,40 Q170,40 172,60 L176,120 Q178,140 160,146 L120,156 L132,250 Q134,262 120,262 L92,262 "
          "Q80,262 78,250 L66,150 Q40,140 40,110 L44,60 Q46,40 60,40 Z")
    return (f'<g transform="translate({x},{y}) scale({sc})">'
            f'<line x1="70" y1="40" x2="56" y2="-30" stroke="{col}" stroke-width="10" stroke-linecap="round"/><circle cx="55" cy="-34" r="9" fill="{ORANGE}"/>'
            f'<path d="{body}" fill="{col}"/><rect x="64" y="62" width="70" height="30" rx="6" fill="{CREAM}"/>'
            f'<path d="M86,150 q-10,26 4,40" stroke="{CREAM}" stroke-width="8" fill="none" stroke-linecap="round"/>{wheel(190,110,48)}</g>')
def bubble(x,y,w,h,tail_x,fill=CREAM,r=40):
    return (f'<path d="M{x+r},{y} h{w-2*r} a{r},{r} 0 0 1 {r},{r} v{h-2*r} a{r},{r} 0 0 1 -{r},{r} '
            f'h-{x+w-r-(tail_x+60)} l-60,50 v-50 h-{tail_x-x-r} a{r},{r} 0 0 1 -{r},-{r} v-{h-2*r} a{r},{r} 0 0 1 {r},-{r} z" fill="{fill}"/>')
BG=f'<rect width="512" height="512" fill="{BLUE}"/>'
DESC = ("PartsPaddock logo: a cream chat bubble on a blue square with a friendly bot head above a low "
        "touring-car silhouette with a rear wing, whose wheels are orange spur gears.")
MARK = BG + bubble(62, 104, 388, 278, 150) + bot(256, 182, 96) + car(86, 246, 0.46)

open("logo.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">'
    f'<title>PartsPaddock</title><desc>{DESC}</desc>{MARK}</svg>')

inner = MARK.replace(BG, "")
open("logo-lockup.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 200" width="860" height="200" '
    f'font-family="-apple-system, \'Segoe UI\', Helvetica, Arial, sans-serif">'
    f'<title>PartsPaddock</title><desc>{DESC} Next to it, the word PartsPaddock, with Paddock in orange, '
    f'and the tagline "the parts desk of your RC club".</desc>'
    f'<rect width="860" height="200" fill="#FFFFFF"/>'
    f'<clipPath id="r"><rect x="20" y="20" width="160" height="160" rx="36"/></clipPath>'
    f'<g clip-path="url(#r)"><g transform="translate(20,20) scale(0.3125)">'
    f'<rect width="512" height="512" fill="{BLUE}"/>{inner}</g></g>'
    f'<text x="210" y="112" font-size="70" font-weight="800" fill="{INK}">Parts<tspan fill="{ORANGE}">Paddock</tspan></text>'
    f'<text x="214" y="152" font-size="24" fill="#4B5563">the parts desk of your RC club</text></svg>')

# PNGs: render with headless Chrome at 2x (logo.png 1024, logo-lockup.png 1720x400) and 1.25x
# (whatsapp-profile-640.png), e.g.
#   chrome --headless=new --force-device-scale-factor=2 --window-size=512,512 --screenshot=logo.png logo.html
