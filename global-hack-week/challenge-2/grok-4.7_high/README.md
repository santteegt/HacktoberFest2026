# FWD touring-hatch sprites

Three orthographic 2D sprites of a 1/10-scale FWD RC touring-car body shell:
a short-bonnet five-door hatch with flared arches, a splitter, side skirts, and a
full-width rear wing. Geometry follows [`../BASE_PROMPT.md`](../BASE_PROMPT.md). Detail that the station
table leaves open — endplate height, headlamp shape, splitter fence, louvre
drawing, wheel lip — was matched to the CA45 sheets in `../schematics/`.

- Model: **grok-4.7**
- Reasoning effort: **high**
- Output folder: `{llmModel}_{reasoning}` → `grok-4.7_high`
- External skills: none
- Graphics library: Pillow 12.3.0, loaded from the challenge's existing `.vendor` directory

## Files

| File | What |
| --- | --- |
| `side.png` | Left side, nose to the left. Reference wheels sit in the arch cut-outs. |
| `top.png` | Top-down, nose to the left. |
| `back.png` | Rear view. The car's left side, the one with the filler cap, is on the image left. |
| `sprite-sheet.png` | The three views on one sheet. |
| `generate.py` | Deterministic source for the PNGs. |

The individual sprites have transparent backgrounds. Final scale is 2 pixels per millimetre,
drawn at 3× and downscaled. The livery is racing green with an ivory roof, copper graphics,
and the number 47.

## Geometry represented

- 440 × 190 × 125 mm body
- Axles at 0.235 L and 0.84 L, 64 mm reference wheels, arch radius 0.085 L
- Short bonnet, roof peak at 0.63 L, steep hatch, no boot deck
- Three-pane side glass, thick C-pillar, belt line at 0.64 H
- Open flared arches, splitter, side skirt, front-wing vent
- Two slanted four-slat bonnet louvres
- Wide hatch glass, two-lobe rear lamps, plate recess, diffuser slots
- Rear wing of chord 0.066 L on two swept pylons, with endplates and three fins
- Filler cap on the car's left side only

The wheels are placement references, not part of the shell. This is a concept sprite set,
not a manufacturing drawing or a track-tested shell.

## Regenerate

From the repository root:

```bash
python3 global-hack-week/challenge-2/grok-4.7_high/generate.py
```

## License

MIT. See `LICENSE`.
