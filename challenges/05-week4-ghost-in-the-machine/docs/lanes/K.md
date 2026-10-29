# Lane K: favicon from the ghost character, gallery pagination

Owner: Sonnet worker. Coordinator: this session. Opened 2026-10-29 ~22:30 local.

## Owned paths
`web/favicon.*`, `web/icons/` (new), `web/site.webmanifest` (new, optional), `web/index.html` (head links + pagination markup), `web/assets/site.js`, `web/assets/site.css`, `template/ghost.html` (head links only), `ghosts/render.py` only if a template variable is needed for the icon path, `ghosts/gallery.py` only if the icon files need a build step, `tests/test_k_*.py`. Nothing else; do not touch `template/header.*`, the mp3s, data/, hermes/, the memory file.

## 1. Favicon from the designed ghost character
- Source of truth: `template/characters/ghost.svg` (the sheet ghost carrying its address tag; used on every page). Make a favicon version of THAT character, not the plain sheet ghost currently inlined as a data URI in `web/index.html` line 25 (replace that data URI).
- Produce: `web/favicon.svg` (hand-derived from ghost.svg: friendly face, the yellow address tag reading `0xB00`, cropped tight, no shadow ellipse, no `$uid`/`$tag` template variables, a dark rounded-square or transparent background so it reads on both light and dark tabs), `web/favicon.ico` (16+32+48 from the SVG, rendered with Playwright's Chromium to PNG then packed with Pillow, both already available in the uv env: check `uv run python -c "import PIL"`, add Pillow as a dev dependency if missing), `web/icons/apple-touch-icon.png` (180, opaque night-purple background `#1b0b2b`), `web/icons/icon-192.png`, `web/icons/icon-512.png`, and `web/site.webmanifest` (name "Ethereum Ghosts", short_name "Ghosts", theme_color `#1b0b2b`, background_color `#1b0b2b`, icons 192/512).
- Links in BOTH heads (index and `template/ghost.html`): `<link rel="icon" href="/favicon.ico" sizes="any">`, `<link rel="icon" type="image/svg+xml" href="/favicon.svg">`, `<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">`, `<link rel="manifest" href="/site.webmanifest">`. Use root-absolute paths (the site is served from the root of the Vercel project at web/); ghost pages live two levels down. Check `web/vercel.json` cache rules and add a long-cache rule for `/favicon.*` and `/icons/*` if the pattern there makes it natural (immutable assets are already covered by a rule or not: read it).
- Keep a small generator script `scripts/make_icons.py` (reads web/favicon.svg, writes the PNGs and the ICO) so the icons can be regenerated; document the command in its docstring.

## 2. Pagination on the index page
- 15 cards per page over the filtered + sorted list (`visible()` in site.js). Controls below the grid: Previous / Next buttons plus page numbers (1 … N, current marked with `aria-current="page"`), hidden when there is a single page. The count line becomes "Showing 1-15 of 26 ghosts" (adapt the existing `#count` text; keep `role="status"`).
- Any filter, search, sort or kind change resets to page 1. The page is kept in the URL hash or query (`?page=2`) so reload and back work; invalid or out-of-range pages clamp to 1 or last. Changing page scrolls to the top of the grid (respect reduced motion: no smooth scroll then).
- Keyboard: buttons are real `<button>`s; the page list is a `<nav aria-label="Pages">`.
- Style with the existing switch/button look in site.css (candle/ink palette, 2 px ink border, rounded).
- Tests: `tests/test_k_pagination.py` checking that site.js contains the page size constant 15 and the `aria-current` marker, that index.html has the nav; and a Playwright check in your verification (not in the suite) with the local 26 ghosts: page 1 shows 15 cards, page 2 shows 11, filter "bad" (13) shows one page and hides the nav, reload on `?page=2` keeps page 2.

## Done means
- `uv run pytest -q` green (add your tests), `uv run ghosts render-all` and `uv run ghosts gallery build` run clean (26 ghosts), both heads carry the four icon links, `/favicon.ico` and `/favicon.svg` exist.
- Playwright verification against a local server (serve `web/` with `python -m http.server` from the scratchpad or whatever the earlier lanes used; see docs/lanes/C3.md or J.md): screenshots of page 1, page 2 and the favicon rendered at 32 px, saved under `/private/tmp/claude-501/-Users-santteegt-GitRepositories-HacktoberFest2026/fae46237-323a-4ae7-a2bf-dcde489921cb/scratchpad/laneK/`.
- No deploy, no commit, no memory edits; log to `## Log` below.

## Log

### Lane K log (2026-10-29)
- Added web/favicon.svg (hand-derived friendly ghost + yellow `0xB00` tag on #1b0b2b rounded square), scripts/make_icons.py (Playwright Chromium render + Pillow; `uv run python scripts/make_icons.py`) -> web/favicon.ico (16/32/48 requested; 256 source), web/icons/{apple-touch-icon(180 opaque),icon-192,icon-512}.png, web/site.webmanifest. Pillow added as dev dependency.
- Four icon links in web/index.html (replaced the data URI) and template/ghost.html (render-all re-ran, ghost pages carry them). vercel.json: new 1-day cache rule for /favicon.* and /icons/*.
- Pagination in site.js (PAGE_SIZE = 15, `?page=N` via replaceState, clamps, popstate, reduced-motion-aware scroll), `<nav class="pager" id="pager" aria-label="Pages">` in index.html, pager styles in site.css. Count line: "Showing 1-15 of 26 ghosts".
- Tests: tests/test_k_pagination.py (4). Two older tests encoded the old data-URI icon / "no link except canonical" and were updated minimally (test_c1_render.py, test_c2_site.py).
- Playwright (headless, local http.server): p1 15 cards, p2 11, reload on ?page=2 keeps 11/page 2, "bad" filter 13 cards with nav hidden, ?page=99 clamps to last, ?page=abc -> 1, no console errors. pytest 256 passed.
