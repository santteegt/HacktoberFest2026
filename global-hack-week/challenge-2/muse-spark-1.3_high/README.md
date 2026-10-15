# Challenge-2 entry — `muse-spark-1.3_high`

Three-perspective 2D sprites of a **1/10 scale RC touring-car body shell, FWD class**
(modern five-door hatchback silhouette), drawn to the dimension tables in
[`../BASE_PROMPT.md`](../BASE_PROMPT.md).

- **Type:** Global Hack Week: Hacktoberfest challenge entry (not a DEV Challenge, no DEV post).
- **Source:** GHW challenge dashboard <https://ghw.mlh.io/challenges>;
  geometry from `challenge-2/BASE_PROMPT.md`; details cross-checked against
  the line-art reference `challenge-2/schematics/*.jpg` (Bittydesign CA45
  blueprint, git-ignored, not bundled).
- **Model:** Muse Spark 1.3 (`muse-spark-1.3`) — reasoning level **high** (strength 256).
  Folder name is `{llmModel}_{reasoning}` as requested.
- **No external skills used.** Raster sprites use **Pillow 12.3.0** (the
  best-fit library for programmatic sprite design: drawing + export in one
  stable API), vendored under `.deps/` via `pip install --target .deps`
  (see `requirements.txt`) — the sandbox Python is externally managed, so all
  dependency writes stay inside this working folder. `generate.py` puts
  `.deps/` on `sys.path` itself, no venv/activation needed; if Pillow is ever
  missing it falls back to a built-in stdlib scanline renderer (same geometry,
  flat fills). PNGs are rendered 3x supersampled and LANCZOS-downscaled for
  anti-aliased edges.

## Files

| File | What |
| --- | --- |
| `side.svg` | Side view master (nose left): silhouette from the station table, arch cut-outs r = 0.085 L at 0.235/0.84 L, 3-pane glass + thick C-pillar, splitter, skirt, wing + pylon + endplate + fin, 10-spoke reference wheels |
| `top.svg` | Plan view master: half-width table outline, bonnet + 2 slanted 4-slat vents, cowl, windscreen, roof island (0.235 W) + vent slot, hatch glass, lamps, 0.97 W wing + endplates + 3 fins |
| `rear.svg` | Rear view master: domed roof, tumblehome cabin, hatch glass + lip spoiler, 2-swept-pylon wing, two-lobe lamps, plate recess, diffuser step + slots |
| `side.png` / `top.png` / `rear.png` | Flat-shaded game-ready raster sprites (transparent), same geometry, simplified fills |
| `generate.py` | Reproducible generator — edit geometry here, re-run |
| `preview.html` | Local viewer + spec-checklist mapping |
| `LICENSE` | MIT |

## How to run

```bash
python3 generate.py   # rewrites the six sprites + preview.html; uses .deps/Pillow, stdlib fallback
```

## Geometry notes (all from `BASE_PROMPT.md`)

Real dims L = 440 mm, W = 190 mm, H = 125 mm. Roof peak at 0.63 L;
belt line z = 0.64 H; sill 0.14 H; splitter 0.05–0.10 H; axle height 0.26 H;
track centres ±82 mm (tyre outer face flush with the 0.50 W flare).
Fuel-filler cap (0.025 L rounded square at x = 0.84, z = 0.63) is drawn on
**one side only**, per the blueprint; the mirrored side omits it.
Wheels are reference placement only — not part of the shell.
Livery: racing blue shell, white roof island/roundels (`45`, nod to the CA45
blueprint), near-black splitter/skirt/wing/diffuser, yellow endplates +
shoulder crease, cream headlamps, red tail lamps.

PNGs are anti-aliased, gradient-shaded game sprites with real text
(roundels, plates); SVGs are the resolution-independent masters.

## Dependencies

Pillow 12.3.0, vendored in `.deps/` (`pillow/` + dist-info, ~15 MB —
kept inside the working folder per instructions, no venv needed).
Reinstall: `python3 -m pip install --break-system-packages --target .deps -r requirements.txt`.

## License

MIT — see `LICENSE`.
