# Provenance of the offline knowledge

Status: **placeholder. The snapshot has not been imported yet.**

This project's code is new work started in the Hacktoberfest 2026 Weekend Challenge window (see `git log`). The setup knowledge it retrieves comes from earlier notes by the author, which predate the window and are credited here rather than presented as new:

- **Source:** a personal touring-car wiki (OKF/markdown), written September 2026 as part of a separate project, distilled from public videos and manuals (to be named per page when imported).
- **Import plan:** copy only the touring-car concept pages into `kb/source/` as a frozen, read-only snapshot in its own commit, with this file listing each page, its sha256, and its original last-modified date. Corrections go in new files, never edits to the snapshot.
- **Not reused:** the author's earlier 3D dynamics guide app, its BD12 3D model, and its setup-sheet app. The visualizer, symptom/lever tables, retrieval, agent, voice loop, PWA shell and setup vault are written fresh in this repository.
