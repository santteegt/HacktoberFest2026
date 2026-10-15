# HF26 FWD touring-hatch sprites

Three orthographic 2D sprites for a 1/10-scale FWD RC touring-car body shell,
based on [`../BASE_PROMPT.md`](../BASE_PROMPT.md) and refined against the
local `../schematics/tc_fwd_{side,top,back}.jpg` CA45 painter blueprints.

- Model: **GPT-5.6 Sol**
- Reasoning level: **medium**
- Output folder convention: `{llmModel}_{reasoning}`
- External skills: **none**
- Graphics library: Pillow 12.3.0, loaded from the challenge's existing
  `.vendor` directory

## Files

- `side.png` — left-facing side profile with reference wheels behind the shell
- `top.png` — top-down view, nose left
- `back.png` — rear view
- `sprite-sheet.png` — presentation sheet combining all three views
- `generate.py` — deterministic source for all PNGs

The individual sprites have transparent backgrounds. They use a pearl-silver,
cyan and magenta HF26 livery with dark aero parts and `26` race numbering.

## Geometry represented

- 440 × 190 × 125 mm body proportions
- Axles at 0.235 L and 0.84 L, with 64 mm reference wheels
- Short bonnet, long five-door glass ring and rear-peaked hatchback roof
- Open flared arches, splitter, side skirt and front-wing vent
- Twin four-slat bonnet louvres
- Blueprint-derived deep front intake, shoulder channels and body-panel seams
- Wide hatch glass, two-lobe rear lamps and diffuser slots
- Full-width rear wing with endplates, swept pylons and three fins

The wheels are placement references, not part of the body shell. This is a
concept sprite set, not a manufacturing drawing or a track-tested shell.

## Regenerate

From the repository root:

```bash
python3 global-hack-week/challenge-2/gpt-5.6-sol_medium/generate.py
```

## License

MIT. See `LICENSE`.
