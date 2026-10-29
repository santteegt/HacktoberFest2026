# Lane L: first-visit welcome ("Hunt the ghost" / "Light the candle")

Owner: Opus worker. Coordinator: this session. Opened 2026-10-29 ~23:10 local.

## Why
Browsers only let audio start after a click. The author wants the first click to be part of the story so readers discover the music and the effects instead of a muted site. Decided design (author + coordinator, 2026-10-29): on the index, a dark page with a ghost to catch; on ghost pages, a candle to light; both first visit only.

## Owned paths
`template/header.html`, `template/header.css`, `template/header.js` (the welcome logic lives here because it owns Effects/Lights state), `template/ghost.html`, `template/ghost.css`, `template/ghost.js`, `template/panels.html` (candle hook only), `template/characters/storyteller.svg` (candle flame group only), `web/index.html` (markup outside the header markers only if needed), `web/assets/site.js`, `web/assets/site.css`, `ghosts/render.py` (template wiring only), `tests/test_l_*.py`. Do not touch the mp3s, data/, hermes/, the memory file, vercel.json.

## Spec
### Shared
- Flag `eg-welcomed` in localStorage (try/catch). Absent → first visit → welcome mode. Any completion of the welcome sets it. Returning visitors never see it: lights and Effects load from their stored state as today.
- Completing the welcome = (1) Lights on, (2) Effects on and stored, (3) ambient starts at volume 0 and fades to 0.6 over 2 s, (4) the ghost woo (`ghost.mp3`) plays once, (5) the welcome line fades out. All from the same click handler (the gesture).
- Any click anywhere on the page during welcome mode (a card, a link, a filter, the header switches) also completes the welcome, so nobody is trapped; the click's own action still happens (do not preventDefault). Exception: clicking the Effects switch while in welcome mode completes the welcome but honours the click (so if the reader turned Effects off, it stays off).
- After 8 s without a click the welcome line changes to "…or just click anywhere". After 20 s with no click, lights come back on silently (nothing plays), the line fades, and the flag is NOT set (next visit tries again once more; after a second timeout set the flag, key `eg-welcome-tries`).
- Reduced motion (`prefers-reduced-motion: reduce`): no chase. Index and ghost pages both show the candle variant (static target).
- Keyboard: the target is a `<button>` (focusable, Enter/Space work) with an `aria-label`; the welcome line is `aria-live="polite"` and reads the instruction once.
- No layout shift: the welcome elements overlay, they never push content.

### Index: "Hunt the ghost"
- Welcome mode loads with Lights off (the existing silhouette treatment) regardless of stored state. The flying ghost becomes the target: a `<button class="eg-hunt">` positioned over the ghost that follows it (the ghost animation already moves the SVG; put the button inside the same moving wrapper, or make the ghost wrapper itself the button). Hit area ≥ 56×56 px on phones, cursor: pointer, the ghost glows faintly on hover/focus.
- The floating line "Hunt the ghost" in the balloon font near the ghost (a speech-bubble-ish chip that trails the ghost or sits at a fixed spot below the header; your call, but it must stay readable at 375 px).
- Catching it (click) completes the welcome and plays a quick "caught" beat: the ghost pops to full colour as the lights come up. With Animation off (stored), the ghost is static, so the catch is a plain click.

### Ghost pages: "Light the candle"
- Welcome mode loads with Lights off. In the first panel, Doña Gwei's candle is unlit (hide the flame group in `storyteller.svg`: give the flame a class `flame` so CSS can hide it in welcome mode; do not change the SVG's geometry otherwise). The line "Light the candle" sits next to the candle; the candle (a button wrapping or overlaying the flame area, ≥ 44 px) is the target.
- Clicking it completes the welcome, shows the flame with a short flicker-in (CSS), reveals the first balloon, and the scream rule for bad ghosts keeps working afterwards since the gesture has happened.
- A reader who arrives on a ghost page already welcomed (from the index) sees no welcome.

### Done means
- `uv run pytest -q` green with new tests: header.js contains the `eg-welcomed` flag and the 8 s / 20 s timings; rendered ghost page contains the candle button and the "Light the candle" text; index contains the hunt markup; the storyteller SVG keeps its geometry (compare path data before/after).
- `uv run ghosts render-all` and `uv run ghosts gallery build` clean (26 ghosts).
- Playwright verification (headless Chromium, local server; reuse the lane J scripts in `/private/tmp/claude-501/-Users-santteegt-GitRepositories-HacktoberFest2026/fae46237-323a-4ae7-a2bf-dcde489921cb/scratchpad/laneJ/`): fresh context → index dark with the line; click the ghost → lights on, Effects on, ambient playing (check `audio.paused === false` and volume ramping), flag set; reload → no welcome. Same for a ghost page (candle). Second fresh context, no click for 21 s → lights on, nothing playing, flag absent. Reduced motion → candle variant on the index. Screenshots (index dark with line, index after catch, ghost page candle unlit, ghost page candle lit) in `/private/tmp/claude-501/-Users-santteegt-GitRepositories-HacktoberFest2026/fae46237-323a-4ae7-a2bf-dcde489921cb/scratchpad/laneL/`.
- Important: the pipeline's own Playwright screenshots (`ghosts og`, `face`, cover) and the lane verifications must not capture the dark welcome state. Automated visits (`navigator.webdriver`) skip the welcome entirely (lights on, no overlay), same as lane J's balloon rule. Keep the 1.5 s panel fallback intact.
- No deploy, no commit, no memory edits; log to `## Log` below.

## Log

### 2026-10-29, Lane L worker (Opus), M4 Max, local

**Where it lives.** All welcome logic is in `template/header.js` (it owns Lights/Effects state): flag `eg-welcomed`, give-up counter `eg-welcome-tries`, constants `WELCOME_HINT_MS = 8000`, `WELCOME_GIVE_UP_MS = 20000`, `FADE_MS = 2000`. The page tells it what the target is: the index has `<button class="eg-hunt">` inside the moving `.fly` wrapper (a sibling before `.bob`, so hover/focus glow is a `~` selector) plus a lone `<button class="eg-candle eg-candle-solo">` for reduced motion; ghost pages have `<button class="eg-candle">` in the title stage (panels.html hook). Each page has one `<p class="eg-line" id="eg-line" aria-live="polite">` carrying `data-hunt` / `data-candle` / `data-hint`; header.js writes the text 60 ms after load so the live region reads it once. On the index that markup sits right after `.haunt`, before the header markers, because the header script runs mid-body. `render.py` needed no change (the hook is static in panels.html).

**Decisions.**
- Welcome = no flag, a target exists, and not `navigator.webdriver`. In welcome mode Lights load off without storing, the autoplay attempt is skipped (so nothing plays before the click), and a capture-phase document click listener completes it. Completion stores the flag, Lights on (stored "on"), Effects on (stored "on"), ambient volume 0 → 0.6 over 2 s (50 ms steps, respects a duck), `EG.sfx("ghost")`, line fades, `html.eg-lit` for 2.2 s (flicker-in / ghost pop).
- Click on Effects during welcome: completes the welcome but leaves Effects to the switch's own handler (the switch shows "on" during welcome, so that click turns it off and it stays off). Click on Lights: same idea, the Lights handler turns them on and stores it (otherwise completion + toggle would leave the room dark). Every other click (cards, chips, links) completes the welcome and keeps its own action; nothing calls preventDefault. Lane J's bubble-phase "first gesture starts the music" handler ignores the welcome's click.
- Timeout (20 s): lights back on (not stored), nothing played, Effects switch shown off until the first click (lane J behaviour), `eg-welcome-tries` +1; at 2 the flag is set.
- Unlit candle: `storyteller.svg` already had `class="flame"` on both flame paths and `class="glow"` on the halo, so the SVG is untouched (geometry test pins the sha of its geometry attributes, same as commit 8823457). In welcome mode every `.flame`/`.glow` on the page is hidden (all chapter candles, not only the first panel, so the page is consistently unlit), Doña Gwei in the title stage is lifted above the dim (z-index 41) so she is visible in the dark, and the title tagline is hidden and fades in on lighting: I read "reveals the first balloon" as the title panel's tagline, the only balloon-font line in the first panel. Flicker-in only with Animation on (`.moving.eg-lit`), so a paused page never gets stuck on a 0-opacity frame.
- The candle button is positioned with CSS vars matching the teller (`--tl`, `--tw`; flame centre 98,95 of the 120×160 viewBox), 52×60 px with a dashed beckoning ring. The line is a speech balloon with a tail pointing at the candle.
- Index line: a fixed chip at the bottom centre (above the phone legend dock), not trailing the ghost: always readable at 375 px, no layout shift. Caught beat: the ghost drops the silhouette filter and pops (scale/rotate .7 s) while the lights come up, then settles back.
- Reduced motion: index hides the hunt and shows the lone candle (fixed, above the line); ghost pages show the candle as always.

**Results (2026-10-29).** `uv run pytest -q`: 260 passed (4 new in `tests/test_l_welcome.py`). `uv run ghosts render-all`: 26 pages, no warnings; `uv run ghosts gallery build`: 26 ghosts, header injected. KOTET page 87,617 bytes.

**Playwright** (headless Chromium, default autoplay policy, `navigator.webdriver` faked false, `python3 -m http.server` on 127.0.0.1; scripts `scratchpad/laneL/verify.py`, `verify_switches.py`):
- Index first visit: `eg-welcome`, lights off, line "Hunt the ghost", no audio object, hunt button 112×112 (84×84 at 375 px). Click on the ghost: 300 ms later lights on, ambient playing at volume 0.09 (ramping), ghost.mp3 played, flag "1", `eg-effects=on`; 2.3 s later volume 0.6, line gone. Reload: no welcome (Effects switch shows off until a click because the headless browser refuses autoplay on reload, lane J behaviour).
- Ghost page (KOTET) first visit: line "Light the candle", flame opacity 0, candle button 52×60. Click: lights on, ambient playing (0.36 at 1.2 s), woo played, flame opacity 1, tagline opacity 1, flag set; scrolling to the guilty snippet then played the scream. Reload: no welcome; index afterwards: no welcome.
- Timeout: at 9 s the line reads "…or just click anywhere"; at 21 s lights on, nothing played, flag absent, tries 1. Second visit shows it again; after the second timeout flag "1", tries 2; third visit no welcome.
- Reduced motion: index shows the candle variant (hunt hidden, candle shown, line "Light the candle"); clicking it completes the welcome with audio.
- During welcome: Effects click → welcome done, Effects off and stored off, nothing plays; Lights click → lights on, music on; filter chip click → welcome done and the filter applied; card click → welcome done and navigation to the ghost page with the ambient playing there.
- Real `navigator.webdriver` (unfaked): no welcome on either page, lights on, targets hidden. No console errors; no horizontal scroll at 375 px on either page.
Screenshots in `scratchpad/laneL/`: index-dark-hunt, index-after-catch, index-reduced-candle, index-mobile-hunt, ghost-candle-unlit (+ -page), ghost-candle-lit, ghost-mobile-candle.

**Not done.** Safari/Firefox and real touch devices not tested; screen-reader announcement not tested with a real reader (only markup). Not committed, not deployed.
