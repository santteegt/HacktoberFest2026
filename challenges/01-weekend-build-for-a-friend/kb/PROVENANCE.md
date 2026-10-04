# Provenance of the offline knowledge

**Status:** snapshot imported 2026-10-04T20:30Z. Frozen: `npm run kb:verify` fails if any file in `kb/source/` changes.

## What this is

This project's **code** is new work started inside the Hacktoberfest 2026 Weekend Challenge window (see `git log`). The setup **knowledge** it retrieves comes from earlier notes by the author, written before the window, and is credited here instead of being presented as new.

- **Origin:** the author's personal touring-car wiki (OKF markdown), written in September 2026 as part of a separate project, distilled from a NotebookLM notebook named "Mastering RC Touring Car class".
- **Notebook sources (50, as described in the original notes):** mostly the ToniSport Newsfeed instructional series; also a Yokomo BD12 developer-comments video, a BD11 build series, Xray material (including driver Alexander Hagberg), and Yokomo's BD12 manual and setup-sheet drawings. The per-episode source list is not copied here; it can be added from the notebook later.
- **Form:** the pages are the author's own paraphrase and synthesis, not transcripts or copied manual text. The techniques and values belong to their original creators.
- **Gaps the notes themselves record:** for example, tyre shore hardness and foam inserts appear nowhere in the source notebook, so the coach must not advise on them.

## Files (11 of the wiki's 60+ pages)

Copied byte-for-byte from the original wiki; hashes in [snapshot-manifest.json](snapshot-manifest.json). Dates are those of the original files, all before 2026-10-02.

| File | Last modified | First committed (original repo) | sha256 |
| --- | --- | --- | --- |
| `source/touring-car-setup-procedure.md` | 2026-09-19 | 2026-09-18 | `77e119cc25fa…` |
| `source/touring-car-suspension-tuning.md` | 2026-09-30 | 2026-09-18 | `ed09d6cdb756…` |
| `source/touring-car-steering-geometry.md` | 2026-09-30 | 2026-09-18 | `4b7989fad427…` |
| `source/touring-car-weight-balance.md` | 2026-09-30 | 2026-09-18 | `c2da03d8e18e…` |
| `source/touring-car-traction-and-tire-management.md` | 2026-09-19 | 2026-09-18 | `43fc6e3ff062…` |
| `source/touring-car-drivetrain-tuning.md` | 2026-09-19 | 2026-09-18 | `7add18afc3e5…` |
| `source/touring-car-aerodynamics.md` | 2026-09-19 | not committed | `437606f290a9…` |
| `source/touring-car-radio-and-servo-setup.md` | 2026-09-19 | not committed | `88ba301db232…` |
| `source/vehicle-dynamics-fundamentals.md` | 2026-09-19 | 2026-09-18 | `9381d6cb74a7…` |
| `source/yokomo-bd12.md` | 2026-09-30 | 2026-09-18 | `443fa0efe062…` |
| `source/minimum-detectable-lap-time-difference.md` | 2026-08-26 | 2026-08-26 | `b72789ddb17c…` |

**Deliberately left out:** the wiki's ESC, motor, telemetry, logger, PCB and data-schema pages, and the `raw/` extraction documents.

## Known quirks of the frozen copy

- Pages say "the owner's BD12" and frame some content around telemetry; the coach must speak in the second person and ignore telemetry framing.
- `Related Concepts` and `Sources` sections link to wiki pages that are not part of this snapshot, so those links are dead here. They are kept as-is because the snapshot is not edited.
- `Sources` entries name pages of the original wiki, including two that describe the author's earlier 3D guide and setup-sheet app. Those apps are **not** used in this project.

## Rules

1. **Never edit `kb/source/`.** Corrections and new knowledge go in `kb/additions/` (OKF-style markdown with a `source` field), so prior work and new work stay visibly separate.
2. `npm run kb:build` compiles `kb/source/` and `kb/additions/` into `data/generated/kb.json` (106 chunks from the snapshot) and fails if any citation in `data/levers.json` does not resolve.
3. Later NotebookLM extraction (planned after the core loop works) lands in `kb/additions/` and is labelled as such: the notebook is pre-existing source material; the queries and structuring are done in the window.

## Not reused from the author's earlier project

The 3D dynamics guide app, its BD12 3D model, and the setup-sheet PWA. The visualizer, symptom and lever tables, retrieval, workflow, voice loop, UI and setup vault are written fresh here.

## License (to confirm)

Code: MIT. Snapshot text: the author's own wording; proposed CC BY 4.0 with the attribution above. The underlying third-party material is not relicensed.
