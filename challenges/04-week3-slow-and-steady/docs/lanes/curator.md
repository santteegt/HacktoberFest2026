# Lane 1: Curator: lane log

Owned paths: `sloth/curator/`, `sloth/cli/curator.py`, `profiles/curator/`, `tests/curator/`, this file. Branch: `lane/curator`. Brief and checklist: [LANES.md](../LANES.md).

## Requests to the coordinator (newest first)

<!-- Contract changes, schema columns, new dependencies, CLI wiring, Hermes profile settings. Keep working on fixtures meanwhile. -->

## Checkpoint reports

<!-- At CP1 (Sat 16:00), CP2 (Sat 20:00), CP3 (Sun 12:00) local: done, measurements (with method), failures, requests. -->

## Log

<!-- Same format as docs/CHALLENGE-MEMORY.md: - YYYY-MM-DD HH:MMZ [TAG] text. Evidence: ... Timestamps from `date -u`. -->

Machine for every measurement below unless stated: the author's MacBook Pro, Apple M4 Max, 64 GB, macOS (Darwin 25.6), Ollama 0.40.10, model alias `sloth-gemma4-12b` (gemma4 12B, Q4_0 QAT, `num_ctx` 32768, `think: false`), Postgres on the Tiger service from `.sloth/config.toml` (schema `public`). The branch is `claude/lane-curator-222f8d` (the app named it; LANES.md says `lane/curator`).

- 2026-10-24 16:43Z [SETUP] `uv sync` + `uv run sloth doctor` all green in the lane worktree with `SLOTH_CONFIG` pointing at the main checkout's `.sloth/config.toml`; `links` was empty. `SLOTH_DRY_RUN` left at the default (1).
- 2026-10-24 16:47Z [MEASURE] Collect over the real Bookmarks file, `bookmark_bar` → "Reading List" (read-only): **1,017 bookmarks, 969 unique canonical URLs, 48 exact duplicates** (45 identical raw URLs saved twice, 3 that differ only by a trailing slash or `fbclid`/`utm_*`). Saved dates span 2025-03-26 to 2026-10-23 (427 in 2025, 542 in 2026 after dedupe). Method: `sloth curator collect`; canonical URL = lowercase host, twitter.com → x.com, tracking params dropped (`utm_*`, `fbclid`, `gclid`, x.com `s`/`t`, …), fragment dropped unless hash-routed, trailing slash dropped, GitHub owner/repo lowercased. Evidence: `.sloth/` run output (not committed).
- 2026-10-24 16:47Z [FINDING] The checklist's "1,017 expected" in `links` cannot hold: `links.canonical_url` is UNIQUE, so the table has 969 rows; the 48 extra Chrome entries are counted in the collect summary only. First collect took 90 s because each upsert was one ~90 ms round trip to Tiger; switched to `executemany` (pipelined).
- 2026-10-24 16:49Z [MEASURE] HTTP + GitHub enrich of all 969 links: **218 s wall for 939 links** (plus a 30-link warm-up in 8.5 s): 498 readable over HTTP (trafilatura), 215 GitHub repos via `gh api` (metadata + README), 226 failed: 137 browser-only hosts skipped (x.com, facebook.com, …), 42 HTTP 403, 18 HTTP 404, 9 DNS failures, 5 × 429, 5 × 5xx, 5 TLS errors, 2 timeouts, 2 GitHub 404, 1 × 402. 92 more pages were fetched but had < 200 readable characters (JS shells). Method: `sloth curator enrich --no-browser`, 8 concurrent HTTP, 4 concurrent `gh`, 10 s timeout, one retry for 404/410/DNS, User-Agent `SkunkworksSloth/0.1`. The Lane 3 browser was not used (stub returns None until `sloth.builder.browser` lands).
- 2026-10-24 16:58Z [DECISION] Dead = 404/410 or DNS failure, twice, 2 s apart. 403/429/5xx/TLS errors are **not** dead (bot walls and flaky hosts); those links go to the model with their title, and to the browser once Lane 3 lands. Rejected: "any 4xx/5xx is dead" from SPEC Workflow 3, because 42 pages answer 403 to any non-browser client.
- 2026-10-24 16:58Z [MEASURE] Code rules over all 969 enriched links (dry run, no writes): 50 go to Valhalla by code (29 dead, 14 duplicates, 6 archived repos, 1 repo with no push in 4 years); 919 go to the model. 338 of those have no readable text (login walls, JS shells, browser-only hosts) and are judged from the bookmark title (x.com titles carry the post text).
- 2026-10-24 17:00Z [DECISION] Duplicates: a loose key (no scheme, no `www.`, GitHub reduced to owner/repo, post-redirect URL counts too) maps every link to the earliest-saved one; later saves go to Valhalla as "duplicate of #id". Exact Chrome duplicates were already collapsed at collect.
- 2026-10-24 17:00Z [DECISION] The model's label never decides alone: code maps it to kept / Valhalla / unsure. Unverified after one retry → unsure. `still_relevant=false` on a link with no readable text and a title under 40 characters → unsure (no evidence the model could see). Login-wall text ("sign in", "verify you are human", … in < 1,500 chars) is hidden from the model; an early test had Gemma send an RC-car tutorial to Valhalla because it only saw a Google sign-in page.
- 2026-10-24 17:00Z [DECISION] Verifier: the `reason` must share at least one content word (≥ 4 letters, not in a generic list like "useful", "relevant", "article") or a number with the facts the model saw (title, site, folder, dates, stars, text excerpt); buildable ≥ 2 needs a `one_line_idea`. Field meanings and the enum values are spelled out in the system prompt because Ollama's `format` constrains output but the model never sees the schema.
- 2026-10-24 17:00Z [DECISION] Valhalla lists are numbered by **link id** (`#412`), not by position, so `restore 3, 7` stays unambiguous after other restores and across batches. `empty` marks rows `confirmed` and writes `.sloth/valhalla/removal-<ts>.md|json`; the Bookmarks file is never opened for writing.
