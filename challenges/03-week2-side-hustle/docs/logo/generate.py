# Generates the PartsPaddock logo directions (concept-A/B/C.svg and directions.svg) in this folder.
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
concepts={
 'A':('Bot in the bubble, car on the track', lambda: BG+bubble(96,70,320,220,180)+bot(256,182,130)+f'<rect x="80" y="430" width="352" height="6" rx="3" fill="{CREAM}" opacity="0.35"/>'+car(100,338,0.42,col=CREAM,hub=BLUE,win=BLUE)),
 'B':('Bot with the transmitter', lambda: BG+bubble(62,92,388,300,150)+bot(170,236,128)+tx(236,150,0.86)),
 'C':('Touring car with gear wheels', lambda: BG+bubble(62,104,388,278,150)+bot(256,182,96)+car(86,246,0.46)),
}
W,H=1280,600
b=[f'<rect width="{W}" height="{H}" fill="#fff"/>',f'<text x="48" y="64" font-size="26" font-weight="800" fill="{INK}">PartsPaddock: logo directions</text>',f'<text x="48" y="92" font-size="15" fill="#4B5563">Same palette and chat bubble; adds the bot and an RC touring car or a transmitter. Large = profile picture (round crop), small = 40 px.</text>']
for i,(k,(t,f)) in enumerate(concepts.items()):
    open(f'concept-{k}.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512"><title>PartsPaddock concept {k}</title><desc>{t}</desc>{f()}</svg>')
    x=48+i*410; y=124
    b.append(f'<rect x="{x}" y="{y}" width="380" height="440" rx="20" fill="#F8FAFC" stroke="#E2E8F0"/>')
    b.append(f'<clipPath id="k{i}"><circle cx="256" cy="256" r="256"/></clipPath><g transform="translate({x+90},{y+24}) scale(0.390625)"><g clip-path="url(#k{i})">{f()}</g></g>')
    b.append(f'<text x="{x+190}" y="{y+260}" font-size="20" font-weight="800" text-anchor="middle" fill="{INK}">{k}. {t}</text>')
    b.append(f'<g transform="translate({x+40},{y+300})"><clipPath id="s{i}"><rect width="512" height="512" rx="110"/></clipPath><g transform="scale(0.12)"><g clip-path="url(#s{i})">{f()}</g></g></g>')
    b.append(f'<text x="{x+112}" y="{y+342}" font-size="30" font-weight="800" fill="{INK}">Parts<tspan fill="{ORANGE}">Paddock</tspan></text>')
    b.append(f'<g transform="translate({x+40},{y+384})"><clipPath id="t{i}"><circle cx="256" cy="256" r="256"/></clipPath><g transform="scale(0.078)"><g clip-path="url(#t{i})">{f()}</g></g></g>')
    b.append(f'<text x="{x+90}" y="{y+410}" font-size="13" fill="#4B5563">40 px: WhatsApp chat list size</text>')
open('directions.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="-apple-system, \'Segoe UI\', Helvetica, Arial, sans-serif"><title>PartsPaddock logo directions</title><desc>Three logo directions on a blue square with a cream chat bubble: A, a friendly bot head in the bubble with a cream touring-car silhouette on a track line below; B, the bot next to a pistol-grip RC transmitter whose steering wheel is an orange gear; C, a dark touring-car silhouette with orange gear wheels under a smaller bot head.</desc>'+''.join(b)+'</svg>')
