# Idea Leash: design notes

Visual layer and information architecture for the phone web app (`app/index.html`). Scope: the screens used before and after a walk. The black walk cover is out of scope and stays as it is.

Assets that come with this spec:

| File | What | Size |
| --- | --- | --- |
| `app/assets/icons.svg` | 20 icon symbols, 24×24, stroke 1.75, round caps and joins, `currentColor` only | 6.7 KB |
| `app/assets/badges.svg` | 16 badge symbols, 96×96, colored by four CSS custom properties | 23 KB |
| `app/assets/preview.html` | Review page: every icon at 24 and 48 px, every badge earned at 96 px and locked at 64 and 48 px, palette, a nav bar and walk-kind cards in context | review only |

All three are well-formed XML (`xmllint --noout`). No fonts, images, scripts or network calls. Nothing in the SVGs runs code.

---

## 1. Principles

1. **The screen is the shortest part of the walk.** Every view answers one question in one glance: *what kind of walk, and go* (Walk), *how much have I been outside* (Activity), *what's next to earn* (Badges). No infinite lists, no counters that tick, no red dots, no "come back" nudges.
2. **Calm by default.** One accent green. Amber and dusk blue appear only where they carry meaning. Motion is optional, short, and never loops.
3. **Offline is normal.** "Your Mac is not reachable" is a status line, not an error. The phone keeps everything, so the copy says so.
4. **Readable at arm's length, at night.** Body text 17 px, nothing under 14 px, true black background, high-contrast text, 48 px minimum touch targets, 56 px for primary actions.

---

## 2. Design tokens

Paste into `:root`. All text pairs meet WCAG AA (4.5:1) on `--bg`, `--surface` and `--surface-2`; see the contrast table in section 11.

```css
:root {
  color-scheme: dark;

  /* surfaces */
  --bg:            #000000;  /* true black: AMOLED pixels off */
  --surface:       #0e1411;  /* cards */
  --surface-2:     #17211c;  /* raised: selected card bg alt, progress track, pressed state */
  --border:        #26332c;  /* hairlines, card outlines (decorative) */
  --border-strong: #566b5e;  /* input outlines, unselected radio ring (3.3:1 on surface) */

  /* text */
  --text:          #ecf3ee;  /* primary */
  --text-2:        #b7c6bd;  /* secondary */
  --muted:         #879a8e;  /* captions, units, inactive tab labels */

  /* accent family: moss green */
  --accent:        #2fae77;  /* fills: primary button, selected border, progress fill, current-week bar */
  --accent-text:   #4cc890;  /* accent used as text or icon color on dark */
  --accent-soft:   #12291e;  /* tinted background of a selected card */
  --on-accent:     #03140c;  /* text on --accent (6.7:1) */
  --chart-past:    #2a8a5f;  /* past-week bars (4.3:1 on surface, a non-text graphic) */

  /* supporting hues (only two) */
  --warn:          #f0b45a;  /* lantern amber: "needs you" states, never for offline */
  --dusk:          #9db6ff;  /* dusk blue: podcast, quiz and ideas ("mind") accents */
  --ok:            #7fd6a8;  /* pale green: "saved on your Mac", "tracked the whole walk" */

  /* type */
  --font: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --fs-cap:   14px;  /* captions, chart labels, nav labels; the floor */
  --fs-sm:    15px;  /* card sub-lines, badge names in the grid */
  --fs-body:  17px;  /* body, list rows, buttons */
  --fs-lg:    20px;  /* card titles, section headings */
  --fs-xl:    24px;  /* view titles */
  --fs-hero:  40px;  /* headline numbers (total km, last walk distance) */
  --lh-tight: 1.2;   /* numbers and headings */
  --lh-body:  1.45;
  --fw-reg: 400; --fw-semi: 600; --fw-bold: 700;

  /* spacing (4 px base) */
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 24px; --s-6: 32px; --s-7: 48px;
  --gutter: 16px;          /* side padding at 360 px */

  /* radii */
  --r-sm: 8px;             /* chips, small buttons, progress bars use 999px */
  --r-md: 14px;            /* cards, inputs, buttons */
  --r-lg: 20px;            /* bottom sheet top corners */
  --r-pill: 999px;

  /* sizes */
  --tap: 48px;             /* minimum touch target */
  --tap-primary: 56px;     /* Start, Resume */
  --nav-h: 64px;           /* bottom bar, excluding safe area */

  /* motion */
  --dur-1: 160ms;          /* press, selection */
  --dur-2: 240ms;          /* sheet, card enter */
  --ease: cubic-bezier(.2, .7, .2, 1);
}
@media (prefers-reduced-motion: reduce) {
  :root { --dur-1: 0ms; --dur-2: 0ms; }
}
```

Base rules worth carrying over:

```css
html, body { background: var(--bg); color: var(--text); font: var(--fs-body)/var(--lh-body) var(--font); }
:focus-visible { outline: 3px solid var(--accent-text); outline-offset: 2px; border-radius: var(--r-sm); }
.num { font-variant-numeric: tabular-nums; }   /* every distance, duration and count */
```

### Badge palette

Badges read four custom properties. Each symbol carries its own family colors as fallbacks, so **an earned badge needs no CSS at all**. Do not set these four on `:root` or on a parent of the grid, or every badge turns the same color.

| Property | Role | Move (green) | Care (amber) | Mind (dusk blue) | Locked |
| --- | --- | --- | --- | --- | --- |
| `--badge-a` | ring face | `#2fae77` | `#e3a54e` | `#86a6f5` | `#353f3a` |
| `--badge-b` | deep shade (rim, drop) | `#145a3c` | `#7a4e14` | `#2e4588` | `#1c2320` |
| `--badge-c` | glyph, number, sheen | `#d4f5e3` | `#fff0d6` | `#e6edff` | `#8a978f` |
| `--badge-d` | inner disc | `#03140c` | `#1a1004` | `#080e20` | `#0c100e` |

Families by hue: **Move** = first-walk, km-5/10/25/50, long-walk. **Care** = dog-1h, dog-5h, streak-3, streak-7. **Mind** = ideas-5/25, quiz-first, quiz-perfect, right-10/25.

---

## 3. Using the sprites

### Icons

```html
<svg class="icon" aria-hidden="true" focusable="false"><use href="assets/icons.svg#i-walk"/></svg>
```

```css
.icon { width: 24px; height: 24px; flex: none; }          /* color comes from the parent's `color` */
.icon--lg { width: 32px; height: 32px; }                  /* walk-kind cards */
.icon--sm { width: 18px; height: 18px; }                  /* inline in text rows, status chips */
```

- The stroke width scales with the size (1.75 at 24 px, 2.3 at 32 px). That is intended; do not set `stroke-width` from CSS.
- Icons next to a visible label are decorative: `aria-hidden="true"`. An icon that stands alone (the cloud in a list row) gets `role="img"` and `aria-label="Saved on your Mac"` or `"Waiting to be sent"` on the `<svg>`. The `<title>` inside each symbol is for tooling and the preview page; screen readers do not reliably read it through `<use>`.
- `i-chevron` points right. Rotate it with CSS for other directions: `transform: rotate(90deg)` for a disclosure that is open.
- The service worker must cache `assets/icons.svg` and `assets/badges.svg` (add them to its precache list), or icons vanish offline.
- External `<use>` does not work from `file://`. Served over http(s) it is fine. If you would rather inline the sprites into `index.html`, paste the `<svg>` with `style="display:none"` right after `<body>` and change hrefs to `#i-walk`; nothing else changes.

### Badges

```html
<svg class="badge" role="img" aria-label="5 km, earned"><use href="assets/badges.svg#b-km-5"/></svg>
<svg class="badge is-locked" role="img" aria-label="10 km, locked, 3.1 of 10 km"><use href="assets/badges.svg#b-km-10"/></svg>
```

**Locked state, exactly:**

```css
.badge { width: 64px; height: 64px; display: block; }
.badge.is-locked {
  --badge-a: #353f3a;
  --badge-b: #1c2320;
  --badge-c: #8a978f;
  --badge-d: #0c100e;
}
```

Custom properties inherit into the `<use>` shadow tree, so setting them on the outer `<svg>` is enough. This keeps the silhouette, tier ring and number fully legible (glyph 6.3:1 on its disc) while clearly dimmed. Color is not the only signal: a locked badge always also shows the lock chip (below) and a progress hint.

Fallback if a browser ignores `var()` inside SVG presentation attributes (none of the targets do; checked in Chromium): `.badge.is-locked { filter: grayscale(1) brightness(.55); }`. Do not combine both.

Lock chip, positioned over the badge's bottom-right:

```html
<span class="badge-wrap">
  <svg class="badge is-locked" ...></svg>
  <span class="lock-chip"><svg class="icon" aria-hidden="true"><use href="assets/icons.svg#i-lock"/></svg></span>
</span>
```
```css
.badge-wrap { position: relative; display: inline-block; line-height: 0; }
.lock-chip { position: absolute; right: -2px; bottom: -2px; width: 24px; height: 24px; border-radius: 50%;
  background: var(--bg); border: 1px solid var(--border-strong); color: var(--text-2); display: grid; place-items: center; }
.lock-chip .icon { width: 14px; height: 14px; }
```

**How the badges are built** (so new ones can match): a 96×96 medallion. Layers from back to front: silhouette in `--badge-b` offset 2.5 down (a drop), the same silhouette in `--badge-a` (the ring), a hairline `--badge-b` circle r 32.5, the inner disc `--badge-d` r 31, a sheen arc on the ring's top-left (`--badge-c` at 45 %), then the glyph in `--badge-c`. Glyphs reuse the icon drawings: singletons draw the glyph at 1.5× (36 units, centered); counted badges draw it at 1.2× near the top with the count as bold system-font text below.

**Tiers are carried by the silhouette, so a family reads at a glance:**

| Tier | Silhouette | Used by |
| --- | --- | --- |
| 1 | smooth circle | first-walk, km-5, long-walk, dog-1h, streak-3, ideas-5, quiz-first, right-10 |
| 2 | 12-lobe scalloped rosette | km-10, dog-5h, streak-7, ideas-25, quiz-perfect, right-25 |
| 3 | 24-tooth seal + inner ring line | km-25 |
| 4 | 24-tooth seal + inner ring + star crown and two side stars | km-50 |

Within a family the glyph and hue stay the same and the count changes (5 / 10 / 25 / 50; 1h / 5h; 3 / 7; 5 / 25; 10 / 25). The quiz pair shares the speech bubble: "?" for the first quiz, a star for a perfect one.

---

## 4. App shell and bottom navigation

```
┌────────────────────────────────────────┐ 360
│ (view content, scrolls)                │
│                                        │
├────────────────────────────────────────┤ ← 1px --border
│   ▔▔▔                                  │ ← 3px active indicator, 32px wide
│   [⌂]          [▥]           [◎]       │   icons 24px
│   Walk       Activity       Badges     │   labels 14px / 600
└────────────────────────────────────────┘ 64px + env(safe-area-inset-bottom)
```

- **Structure:** `<nav class="tabbar" aria-label="Main">` with three `<a>` or `<button>` items in a 3-column grid. Each item is the full column width and the full 64 px height (targets about 120×64).
- **Icons:** Walk `i-home`, Activity `i-stats`, Badges `i-badge`. `i-home` (not `i-walk`) for the tab so it isn't confused with the "Plain walk" card.
- **Layout:** icon above label, 2 px gap, centered. Label 14 px, weight 600, `--muted`.
- **Active:** icon and label `--accent-text`, label weight 700, and a 3×32 px `--accent` bar flush with the top edge of the bar (radius on the bottom corners). `aria-current="page"`. Color is not the only cue: the indicator bar and the weight change too.
- **Pressed:** background `--surface` for `--dur-1`.
- **Safe area:** `height: calc(var(--nav-h) + env(safe-area-inset-bottom)); padding-bottom: env(safe-area-inset-bottom);`. The page needs `<meta name="viewport" content="..., viewport-fit=cover">` (already there). Main content gets `padding-bottom: calc(var(--nav-h) + env(safe-area-inset-bottom) + var(--s-5))` so the last card clears the bar.
- **Background:** `--bg` (true black) with a top hairline. No blur, no translucency (costs battery, adds nothing at night).
- **Position:** `position: fixed; inset: auto 0 0 0; z-index: 5;` (below the cover's 10).
- **Hidden during a walk:** when the cover is on, set `hidden` on the nav (or `body.walking .tabbar { display: none; }`). Hiding it, not just covering it, keeps it out of the focus order and away from pocket touches. Show it again in `finish()` after the cover is removed. Keep it visible while the "A walk was still going" card is shown.
- **Routing:** three sibling `<section>`s, one visible. Use the hash (`#walk`, `#activity`, `#badges`) so the back button works and a reload keeps the tab. Default `#walk`. After a walk ends, always land on Walk.
- **Header:** each view starts with a 48 px header row: view title (24 px, 700) on the left; on Walk the brand mark and the connection chip (section 5).

---

## 5. Walk view (home)

### Layout at 360×740 (nav bar takes the bottom 64 px)

```
┌──────────────────────────────────────┐
│ ❦ Idea Leash          ☁✓ Mac connected│  header 48px; chip is a 48px-tall button
│                                      │
│ ┌──────────────────────────────────┐ │  RESUME CARD (only if a walk was cut off)
│ │ ⚠ A walk was still going         │ │  border --warn, 1px; icon i-alert --warn
│ │ Dog walk, started 19:32.         │ │
│ │ [ Resume walk ]  [ Finish & save ]│ │  56px primary + 48px secondary
│ └──────────────────────────────────┘ │
│                                      │
│ ┌──────────────────────────────────┐ │  JUST-WALKED CARD (after a walk; see 5.4)
│ │ ◎ New badge · 5 km               │ │
│ └──────────────────────────────────┘ │
│                                      │
│ Start a walk                         │  20px / 700
│ ┌──────────────────────────────────┐ │
│ │ 🎧  Podcast walk              (●) │ │  KIND CARD, 72px, selected
│ │     Listen, then get quizzed     │ │
│ └──────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │
│ │ 🐕  Dog walk                  ( ) │ │
│ │     Time together counts         │ │
│ └──────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │
│ │ 🚶  Plain walk                ( ) │ │
│ │     Just you and the air         │ │
│ └──────────────────────────────────┘ │
│ Episode                              │  14px label, only for Podcast
│ ┌──────────────────────────────────┐ │
│ │ How forests talk (31 min)     ⌄  │ │  56px select
│ └──────────────────────────────────┘ │
│ Quiz ready after the walk ✓          │  14px, --ok; or "Quiz still being made" --muted
│ ┌──────────────────────────────────┐ │
│ │        Start podcast walk        │ │  PRIMARY, 56px, --accent / --on-accent
│ └──────────────────────────────────┘ │
│ ▸ Before you start                   │  48px disclosure row
│                                      │
│ Last walk                            │
│ ┌──────────────────────────────────┐ │
│ │ 🐕 Dog walk · Tonight 19:32      │ │
│ │ 3.15 km   35 min                 │ │  40px numbers
│ │ ✓ Tracked the whole walk         │ │
│ │ 🎙 2 ideas · ☁✓ Saved on your Mac │ │
│ └──────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │
│ │ ☁… Waiting to be sent to the Mac │ │  QUEUE CARD (only if something is queued)
│ │ 1 walk, 3 voice notes.           │ │
│ │ Safe on this phone.   [Send now] │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

On a first screen of 676 px (740 minus the bar) the kind cards, the Start button and "Before you start" fit above the fold when there is no resume or just-walked card. The last-walk and queue cards sit below; they are for after a walk.

Order of blocks, top to bottom: header, resume card, just-walked card, "Start a walk" group, last walk, queue. The resume card is first because it is the only thing that can lose data.

### 5.1 Components

**Connection chip** (header right). A `<button>` 48 px tall, no border, 14 px text, icon 18 px.

| State | Icon | Text | Color |
| --- | --- | --- | --- |
| checking | `i-cloud-off` | Checking your Mac… | `--muted` |
| connected | `i-cloud-ok` | Mac connected | `--text-2`, icon `--ok` |
| not reachable | `i-cloud-off` | Mac not reachable | `--text-2`, icon `--muted` |
| token missing or wrong | `i-alert` | Connect your Mac | `--warn` |

Tap opens a small bottom sheet: for "not reachable", the calm explanation (copy in section 9) and "Try again"; for "Connect your Mac", the token field and "Save" (this replaces the always-visible token card). Only the token state uses `--warn`, because only that one needs the user.

**Kind cards** (radio group). Keep native radios for semantics: `<label class="kind"><input type="radio" name="kind" class="visually-hidden">…</label>` in a `role="radiogroup"` with a visible group heading.

- 72 px min height, full width, `--surface`, 2 px `--border`, radius `--r-md`, padding 12/14, gap 14.
- Left: icon 32 px (`i-podcast`, `i-dog`, `i-walk`), `--text-2`.
- Middle: label 17/700 `--text`; one line 15 px `--text-2`.
- Right: a 22 px radio ring (`--border-strong`).
- **Selected:** border `--accent`, background `--accent-soft`, icon `--accent-text`, ring filled with a 10 px `--accent` dot. Three cues besides hue: the dot, the border weight contrast, the icon color.
- Focus: `input:focus-visible + .kind-body` gets the global focus ring.
- Remember the last chosen kind in `localStorage` and preselect it. Most walks repeat the last kind.

**Episode picker** (Podcast only; hide the whole block for Dog and Plain, don't just disable it). A native `<select>`, 56 px, `--surface`, 1 px `--border-strong`, radius `--r-md`, a rotated `i-chevron` at the right. Above it a 14 px label "Episode". Under it one 14 px line with the quiz status of the chosen episode: `i-quiz` + "Quiz ready for after the walk" (`--ok`) or "Quiz still being made on your Mac" (`--muted`). Show titles plainly; move "(not ready)" out of the option text and into this line.
Empty: if the Mac sent no episodes, replace the select with a 15 px note: "No episodes yet. Send a link to your Mac and it will be here next time." Starting a podcast walk without an episode is allowed.

**Start button.** Full width, 56 px, `--accent` background, `--on-accent` text, 18/700. The label names the kind: "Start podcast walk", "Start dog walk", "Start walk". Disabled only while starting ("Starting…"), never because the Mac is unreachable.
Errors from start (no microphone, location denied) show inline under the button in `--warn` with `i-alert`, not in `alert()`.

**"Before you start"** (collapsed by default; open by default only until the first walk is finished). A `<details>` with a 48 px `<summary>`: rotating `i-chevron`, 17/600 text. Inside, a short list, 15 px `--text-2`:
1. When Chrome asks for location and microphone, choose **Allow while visiting the site**. "Only this time" is dropped when the screen turns off, and the walk stops tracking.
2. Keep the screen on. The page goes black; put the phone in your pocket. A hidden page gets no location.
3. To stop, hold the top-left corner for 3 seconds.
4. Optional: Android screen pinning stops pocket taps from switching apps (untested).

**Last walk card.** `--surface` card.
- Line 1: kind icon 18 px + "Dog walk · Tonight 19:32" (15 px `--text-2`). Use a friendly date: "Tonight" / "This morning" / "Yesterday 07:10" / "Tue 6 Oct". Never the raw kind id.
- Line 2: distance and duration in 40 px, 700, tabular nums: `3.15 km` and `35 min` side by side, units at 17 px `--text-2`.
- Line 3: `i-check` "Tracked the whole walk" (`--ok`) or `i-alert` "8 min could not be tracked. Distance counts only tracked time." (`--warn`, 15 px). Two lines max.
- Line 4: `i-idea` "2 ideas" · `i-cloud-ok` "Saved on your Mac" or `i-cloud-off` "Not sent yet".
- Tap anywhere: goes to the walk in Activity (later); keep the raw JSON "Technical details" out of this view (see section 10).

**Queue card.** Only when something is pending. `i-cloud-off` 24 px `--text-2`, title "Waiting to be sent to the Mac" (17/600), body "1 walk, 3 voice notes. Safe on this phone." (15 px `--text-2`). Right-aligned secondary button "Send now" (48 px, `--surface-2`, `--text`) only when the Mac answered recently; otherwise a line instead of the button: "They go by themselves when your Mac is reachable." While sending: button text "Sending…" and disabled. No percentages, no spinners.

### 5.2 Empty state (new user)

- No last-walk card, no queue card. The kind cards and Start are the whole screen.
- "Before you start" is open.
- One welcome line under the header, 17 px `--text-2`: "Pick a walk, press start, put the phone away. Ideas you say out loud go to your Mac."

### 5.3 Loading and offline

- On load, render immediately from what the phone knows (IndexedDB walks, cached episodes, cached medals). The network fills in later. Nothing on this view waits for the Mac.
- The chip shows "Checking your Mac…" for at most the length of the request; then one of the states above.
- Offline: the episode list comes from the last successful `/episodes` (cache it in `localStorage`); if none, the empty note. Start works the same.

### 5.4 The "new badge" moment (after a walk)

When a walk ends the app lands on Walk. If the refresh shows newly earned badges, a **just-walked card** sits above "Start a walk":

```
┌──────────────────────────────────────┐
│  [badge 72px]  New badge             │  14px --accent-text, uppercase off
│                5 km                  │  20px / 700
│                Walk 5 km in total.   │  15px --text-2
│  See all badges ›          [ OK ]    │  48px link + 48px button
└──────────────────────────────────────┘
```

- Detect new badges in plain code: keep the earned ids seen so far in `localStorage` (`leash.seenBadges`). New = `earned − seen`. If the key does not exist yet and some badges are already earned, store them silently (an existing user should not get six cards at once).
- More than one new badge: show the first, and "+1 more" next to the name; "See all badges" opens the Badges view.
- "OK" or visiting the Badges view marks them seen and removes the card.
- If the Mac is not reachable after the walk, there is no card yet; it appears on the next refresh that reaches the Mac. Never compute badges on the phone.
- No confetti, no sound, no vibration (the phone has just come out of a pocket; the walk cover already buzzed).

---

## 6. Activity view

Data: `GET /stats` (`weeks`, `by_kind`, `current_streak_days`, `totals`, `medals`, `recent`). Cache the last good response in `localStorage` (`leash.stats`, with the time it arrived).

### Layout at 360×740

```
┌──────────────────────────────────────┐
│ Activity                              │ header 48px
│                                      │
│ 42.6 km                              │ HEADLINE 40px/700, tabular
│ outside, in 18 walks · 9 h 40 min    │ 15px --text-2
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🔥 3 days in a row               │ │ STREAK ROW 17/600; flame --warn
│ │    Best: 7 days                  │ │ 15px --text-2
│ └──────────────────────────────────┘ │
│                                      │
│ Last 8 weeks                    km   │ 17/600 + 14px unit
│ ┌──────────────────────────────────┐ │
│ │                            6.4   │ │ value label above the current week
│ │        ▇                    █    │ │
│ │   ▅    █    ▃         ▆     █    │ │ bars: --chart-past, current --accent
│ │ ▂ █ ▁  █ ▄  █    ▂    █  ▃  █    │ │
│ │ ─────────────────────────────────│ │ baseline 1px --border
│ │ Aug 17        Sep 14     This wk │ │ 14px --muted
│ └──────────────────────────────────┘ │
│                                      │
│ By kind                              │
│ 🎧 Podcast   ████████░░░  8 · 21.0 km│ rows 48px
│ 🐕 Dog       █████░░░░░░  7 · 14.3 km│
│ 🚶 Plain     ██░░░░░░░░░  3 ·  7.3 km│
│                                      │
│ Recent walks                         │
│ ┌──────────────────────────────────┐ │
│ │ (🐕) Thu 8 Oct · 19:32       ☁✓  │ │ rows 64px
│ │      3.15 km · 35 min · 2 ideas  │ │
│ ├──────────────────────────────────┤ │
│ │ (🎧) Wed 7 Oct · 07:05       ☁…  │ │
│ │      2.40 km · 28 min · 0 ideas  │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### 6.1 Components

**Headline.** `totals.km` with one decimal at 40/700, unit "km" at 20 px `--text-2`. Sub-line: "outside, in {walks} walks · {minutes as h min}". This is the single number the view leads with.

**Streak row.** `i-flame` 24 px in `--warn` (amber reads as warmth, not alarm, next to a flame and paired with text). Title "{current_streak_days} days in a row" (1: "1 day so far"; 0: "No streak right now", flame `--muted`). Sub-line "Best: {best_streak_days} days". No "don't break your streak" pressure copy, ever. The server counts a streak as alive if you walked today or yesterday; say nothing more.

**8-week bar chart** (plain inline SVG, no library):
- `<svg viewBox="0 0 328 150" width="100%" role="img" aria-labelledby="wkTitle wkDesc">` inside a `--surface` card with 12 px padding.
- Plot area: x 0 to 328, bars area y 18 to 118 (100 units tall), baseline at y 118 (`--border`, 1 px), labels at y 140.
- 8 slots of 41 units; bar width 24, x = `i * 41 + 8.5`, radius `rx="4"` (top corners look rounded, the base sits on the line).
- Height: `h = max(3, km / maxKm * 100)` with `maxKm = max(1, ...weeks.km)`. A zero week shows a 3-unit stub in `--border` so the rhythm is visible.
- Past weeks `--chart-past`, current (last) week `--accent`. Not color-only: the current week has its value printed above it (14 px `--text`, e.g. "6.4") and "This wk" under it. The tallest past week also gets its value printed if it differs from the current one.
- X labels: first week (`weeks[0].start` as "Aug 17"), fifth week, and "This wk". Three labels at 14 px fit 328 px without crowding.
- Each bar has a `<title>`: "Week of Sep 14: 6.4 km, 3 walks, 1 h 52 min". Also render a visually hidden `<table>` with the same rows for screen readers; `aria-describedby` the table.
- Optional tap on a bar: show the week's numbers in the card header line. Not required.

**By kind.** Three rows, 48 px each: icon 24 (`i-podcast`, `i-dog`, `i-walk`), label 17 px, a 6 px progress bar (track `--surface-2`, fill `--accent`, width = share of km), then "{walks} · {km} km" right-aligned, 15 px tabular. Show all three rows even at zero so the shape is stable.

**Recent walks.** A list in a `--surface` card, rows 64 px, separated by `--border` hairlines. Row: 40 px circle (`--surface-2`) with the kind icon 22 px; line 1 "Thu 8 Oct · 19:32" 17/600; line 2 "3.15 km · 35 min · 2 ideas" 15 px `--text-2`; trailing 20 px cloud icon (`i-cloud-ok` in `--ok`, label "Saved on your Mac"; `i-cloud-off` in `--muted`, label "Waiting to be sent"). Show 10, then a 48 px "Show more" row (up to the 20 the server returns). Merge in walks that are still only on the phone (IndexedDB, `uploaded: false`) at the top with the cloud-off icon. `clips` 1 shows "1 idea".

### 6.2 States

- **Empty (no walks):** the headline reads "0 km" in `--muted`; under it "Your first walk will show up here." The chart card renders 8 stubs and the line "Weeks fill in as you walk." Hide "By kind" and "Recent walks". No illustration needed; the `i-leaf` mark at 32 px in `--accent-text` above the line is enough.
- **Loading:** first visit with no cache: static placeholders, a 40×160 px block for the headline and a 150 px card for the chart, in `--surface`. No shimmer. With a cache: show the cache at once and refresh silently.
- **Offline / Mac not reachable:** show the cached stats with a status line under the header: `i-cloud-off` "Your Mac is not reachable. Showing what this phone knows, from {time}." (15 px `--text-2`). Recent walks still list local walks. Never blank the view.
- **Token missing:** same as offline plus "Connect your Mac" button that opens the connection sheet.

---

## 7. Badges view

Data: `stats.medals` (16 items with `id, label, how, family, earned, progress, target, unit`). Falls back to the cached `leash.stats`; if that is missing too, the grid shows all 16 locked with no progress line and the offline status line.

### Layout at 360×740

```
┌──────────────────────────────────────┐
│ Badges                    6 of 16    │ header; count 15px --text-2
│ Next up: 5 km · 1.9 km to go      ›  │ 48px row, tap opens that sheet
│                                      │
│ Walking                              │ 15px/600 --text-2 section label
│ ┌─────────┐┌─────────┐┌─────────┐    │ 3 columns, gap 8
│ │  (◉)    ││  (◉)🔒  ││  (◉)🔒  │    │ badge 64px
│ │First    ││5 km     ││10 km    │    │ name 15px, 2 lines max
│ │walk     ││3.1 of 5 ││3.1 of 10│    │ hint 14px --muted
│ │✓ Earned ││▓▓▓▓░░░  ││▓▓░░░░░  │    │ 4px bar
│ └─────────┘└─────────┘└─────────┘    │
│ ┌─────────┐┌─────────┐┌─────────┐    │
│ │ 25 km   ││ 50 km   ││Long walk│    │
│ └─────────┘└─────────┘└─────────┘    │
│ With the dog                         │
│ [ dog-1h ] [ dog-5h ]                │
│ Habit                                │
│ [streak-3] [streak-7]                │
│ Ideas                                │
│ [ideas-5 ] [ideas-25]                │
│ Quiz                                 │
│ [quiz-1st] [perfect ] [right-10]     │
│ [right-25]                           │
└──────────────────────────────────────┘
```

### 7.1 Grouping and sort order

Group by family, in the order of the loop (walk, then companion, then habit, then mind). Within a group keep the tier order (the server's order), so a family reads left to right as a ladder. Earned badges are not moved to the front; the ladder is the point.

| Section | Server `family` values | Badges |
| --- | --- | --- |
| Walking | `first`, `distance`, `long` | first-walk, km-5, km-10, km-25, km-50, long-walk |
| With the dog | `dog` | dog-1h, dog-5h |
| Habit | `streak` | streak-3, streak-7 |
| Ideas | `ideas` | ideas-5, ideas-25 |
| Quiz | `quiz`, `answers` | quiz-first, quiz-perfect, right-10, right-25 |

**Next up** (one line under the header): the locked badge with the highest `progress / target`; ties go to server order. Hidden when all 16 are earned ("All 16 earned. Go for a walk anyway.").

### 7.2 Badge cell

- A `<button>` filling the grid column (104 px wide at 360), min-height 156 px, padding 10/6, radius `--r-md`, background `--surface`, 1 px `--border`. Centered stack, gap 6.
- Badge 64 px; locked uses `.is-locked` and the lock chip.
- Name: 15 px, 600, `--text` (earned) or `--text-2` (locked), at most 2 lines (`-webkit-line-clamp: 2`; full text in the sheet and in the `aria-label`).
- Earned: `i-check` 16 px + "Earned" 14 px `--ok`. No progress bar.
- Locked: hint 14 px `--muted`, tabular nums, then a 4 px bar (track `--surface-2`, fill `--accent`, radius 999px, width `progress/target`).
- Accessible name: "{label}, earned" or "{label}, locked, {hint}".

Progress hint formats (by `unit`):

| unit | Format | Example |
| --- | --- | --- |
| km | one decimal, "of" target | 3.1 of 5 km |
| min | under 60 min target: "40 of 60 min"; for 300: hours and minutes | 1 h 40 min of 5 h |
| days | "2 of 3 days" | 2 of 7 days |
| ideas | "3 of 5 ideas" | 18 of 25 ideas |
| points | "right answers" | 7 of 10 right |
| walks / quizzes | "Not yet" when 0 of 1 | Not yet |

### 7.3 Bottom sheet

A native `<dialog>` opened with `showModal()` (focus trap, Esc, inert background for free), styled as a sheet:

```
┌──────────────────────────────────────┐
│ ░░░░░░░░░ dimmed view ░░░░░░░░░░░░░░ │ scrim rgba(0,0,0,.7); tap closes
├──────────────────────────────────────┤ radius 20 top
│               ───                    │ 4×36 handle, decorative
│            [badge 96px]              │
│               5 km                   │ 22px/700, the dialog's label
│            🔒 Not yet                 │ or ✓ Earned (--ok)
│   Walk 5 km in total.                │ `how`, 17px --text-2
│   ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░  3.1 of 5 km   │ 8px bar + hint
│   1.9 km to go                       │ 15px --muted
│ ┌──────────────────────────────────┐ │
│ │              Close               │ │ 48px secondary
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘  + env(safe-area-inset-bottom)
```

- Width 100 %, max-height 70 vh, padding 24/16 plus safe area, background `--surface`, top border `--border`.
- Content only from the medal object; no share button, no "keep going!" copy.
- On close, focus returns to the cell that opened it.

### 7.4 States

- **Empty (new user):** every cell locked, "0 of 16" in the header, Next up "First walk · Finish one walk". A one-line intro above the first section: "Badges come from walking, not from the screen. They fill in on their own."
- **Loading:** cells render immediately as locked shells (badge art is local); progress lines show "…" until data arrives. No skeleton shimmer.
- **Offline:** cached medals, with the `i-cloud-off` status line "Your Mac is not reachable. Badges update when it is."

---

## 8. Micro-interactions

Rules: only `opacity` and `transform`; nothing loops; nothing runs while the cover is on. Under `prefers-reduced-motion: reduce` every transition below becomes an instant change (the tokens set the durations to 0), and transforms are dropped.

| What | Motion | Duration / easing | Reduced motion |
| --- | --- | --- | --- |
| Kind card select | border and background color crossfade; radio dot scales 0.6→1 | `--dur-1`, `--ease` | instant color change, no scale |
| Button press | background to a 10 % darker shade, `scale(.98)` | 100 ms | color only |
| Episode block show/hide (kind change) | `opacity` 0→1 and `translateY(-4px)`→0 | `--dur-1` | instant |
| "Before you start" | chevron rotates 0→90°; content appears | `--dur-1` | no rotation; content appears |
| Tab switch | none (instant). Views do not slide. | – | – |
| Bottom sheet open | `translateY(100%)`→0, scrim opacity 0→1 | `--dur-2`, `--ease` | fade scrim only, sheet appears in place |
| Bottom sheet close | reverse | 180 ms | instant |
| New-badge card enter | card `opacity` 0→1 + `translateY(8px)`→0; badge `scale(.92)`→1 starting 80 ms later | 240 ms + 320 ms, `--ease` | appears in place |
| New-badge sheen (optional) | one pass of a 20 %-white gradient across the badge, once, never repeated | 600 ms | omitted |
| Progress bars | width transitions from 0 on first paint | 300 ms | static |
| Queue sent | the queue card fades out after "Sent" shows for 2 s | `--dur-2` | removed after 2 s, no fade |

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition-duration: 0ms !important; animation: none !important; }
}
```

No haptics on these screens. The walk cover's vibrations stay as they are.

---

## 9. UX copy

Tone: plain, warm, short; second person; no exclamation marks; no streak guilt; offline is said as a fact.

**Navigation:** Walk · Activity · Badges

**Walk view**
- Header chip: "Mac connected" / "Mac not reachable" / "Checking your Mac…" / "Connect your Mac"
- Section: "Start a walk"
- Kinds: "Podcast walk" — "Listen, then get quizzed" · "Dog walk" — "Time together counts" · "Plain walk" — "Just you and the air"
- Episode label: "Episode"; quiz line: "Quiz ready for after the walk" / "Quiz still being made on your Mac"
- No episodes: "No episodes yet. Send a link to your Mac and it will be here next time."
- Buttons: "Start podcast walk" / "Start dog walk" / "Start walk"; while starting "Starting…"
- Disclosure: "Before you start"
- Resume card: "A walk was still going" — "Dog walk, started 19:32. 412 places saved." — "Resume walk" / "Finish and save"
- Last walk: "Last walk"; "Tracked the whole walk" / "8 min could not be tracked. Distance counts only tracked time." / "Saved on your Mac" / "Not sent yet"
- Queue: "Waiting to be sent to the Mac" — "1 walk, 3 voice notes. Safe on this phone." — "Send now" / "Sending…" / "Sent" / "They go by themselves when your Mac is reachable."
- New badge: "New badge" — "{label}" — "{how}." — "See all badges" / "OK"
- First run: "Pick a walk, press start, put the phone away. Ideas you say out loud go to your Mac."
- Start errors: "The microphone is blocked. Voice notes won't record. You can still walk." · "Location is blocked, so distance won't count. Allow it in Chrome's site settings."

**Offline / not reachable sheet**
- Title: "Your Mac is not reachable"
- Body: "That's fine. Walks and voice notes stay on this phone and go to your Mac by themselves next time it answers. Your Mac may be asleep, or this phone may be off your network."
- Buttons: "Try again" · "Close"

**Connect sheet (token)**
- Title: "Connect your Mac"
- Body: "Scan the pairing code on your Mac, or paste its token here. You only do this once."
- Field placeholder: "Leash token" · Button: "Save"
- Wrong token: "That token didn't work. Check it on your Mac and try again."

**Activity**
- Title: "Activity"; sub-line: "outside, in 18 walks · 9 h 40 min"
- Streak: "3 days in a row" / "1 day so far" / "No streak right now"; "Best: 7 days"
- Chart: "Last 8 weeks"; "This wk"
- Sections: "By kind", "Recent walks", "Show more"
- Empty: "Your first walk will show up here." · "Weeks fill in as you walk."
- Offline: "Your Mac is not reachable. Showing what this phone knows, from 19:40."

**Badges**
- Title: "Badges"; "6 of 16"; "Next up: 5 km · 1.9 km to go"
- Empty intro: "Badges come from walking, not from the screen. They fill in on their own."
- Cell: "Earned" / "3.1 of 5 km" / "Not yet"
- Sheet: "Earned" / "Not yet"; "{n} km to go" / "{n} more ideas" / "{n} more days in a row" / "{n} more right answers"; "Close"
- All done: "All 16 earned. Go for a walk anyway."
- Offline: "Your Mac is not reachable. Badges update when it is."

---

## 10. Where every asset is used

### Icons (`assets/icons.svg`)

| Id | Used in |
| --- | --- |
| `i-walk` | Walk view: "Plain walk" kind card; Activity: "By kind" row and recent-walk rows for kind `walk` |
| `i-dog` | Walk view: "Dog walk" card; last-walk line; Activity: by-kind row and recent rows for kind `dog` |
| `i-podcast` | Walk view: "Podcast walk" card; last-walk line; Activity: by-kind row and recent rows for kind `podcast` |
| `i-mic` | Things about recording: queue card ("3 voice notes", optional inline icon); the microphone-blocked start error |
| `i-quiz` | Walk view: quiz status line under the episode picker ("Quiz ready for after the walk"); a future "Take the quiz" entry after a podcast walk |
| `i-idea` | Counts of ideas said aloud: last-walk card ("2 ideas"), recent-walk rows (optional inline icon) |
| `i-home` | Bottom nav: Walk tab |
| `i-stats` | Bottom nav: Activity tab |
| `i-badge` | Bottom nav: Badges tab; new-badge card fallback if the badge art fails |
| `i-route` | Last-walk card: optional "View route" link (GPX on the Mac); Activity: distance unit in the headline (optional) |
| `i-clock` | Last-walk card and recent rows: duration (optional inline icon) |
| `i-flame` | Activity: streak row |
| `i-check` | "Tracked the whole walk"; "Earned" in badge cells and sheet |
| `i-alert` | Resume card; "could not be tracked" line; "Connect your Mac" chip; inline start errors |
| `i-cloud-off` | Connection chip (checking / not reachable); queue card; recent rows not yet sent; offline status lines |
| `i-cloud-ok` | Connection chip (connected); last-walk "Saved on your Mac"; recent rows that are saved |
| `i-battery` | Reserved: battery used on the last walk (`battery_start` - `battery_end`), in the walk details; not on the three main views |
| `i-leaf` | Header brand mark on Walk; empty state on Activity; optional app icon source |
| `i-chevron` | "Before you start" disclosure; episode select arrow (rotated 90°); "Next up" row; "See all badges" |
| `i-lock` | Lock chip on locked badges; "Not yet" in the badge sheet |

### Badges (`assets/badges.svg`)

All 16 appear in the Badges grid (64 px) and in the sheet (96 px). The new-badge card on the Walk view uses whichever was just earned (72 px).

| Id | Label | Family / section | Tier | Glyph |
| --- | --- | --- | --- | --- |
| `b-first-walk` | First walk | first / Walking | 1 | sprout |
| `b-km-5` | 5 km | distance / Walking | 1 | footprints + 5 |
| `b-km-10` | 10 km | distance / Walking | 2 | footprints + 10 |
| `b-km-25` | 25 km | distance / Walking | 3 | footprints + 25 |
| `b-km-50` | 50 km | distance / Walking | 4 | footprints + 50 |
| `b-long-walk` | Long walk | long / Walking | 1 | hills, trail and moon |
| `b-dog-1h` | An hour with the dog | dog / With the dog | 1 | dog head + 1h |
| `b-dog-5h` | Five hours with the dog | dog / With the dog | 2 | dog head + 5h |
| `b-streak-3` | Three days running | streak / Habit | 1 | flame + 3 |
| `b-streak-7` | A week running | streak / Habit | 2 | flame + 7 |
| `b-ideas-5` | Five ideas aloud | ideas / Ideas | 1 | bulb + 5 |
| `b-ideas-25` | Twenty-five ideas aloud | ideas / Ideas | 2 | bulb + 25 |
| `b-quiz-first` | First quiz | quiz / Quiz | 1 | bubble with ? |
| `b-quiz-perfect` | Perfect quiz | quiz / Quiz | 2 | bubble with star |
| `b-right-10` | Ten right answers | answers / Quiz | 1 | check + 10 |
| `b-right-25` | Twenty-five right answers | answers / Quiz | 2 | check + 25 |

Integration check: `grep -o 'id="[ib]-[a-z0-9-]*"' app/assets/*.svg` must list exactly the 36 ids above, and every `href="assets/...#id"` in `index.html` must be one of them. The medal ids from the server map to badge ids by prefixing `b-`.

---

## 11. Accessibility

Contrast (WCAG 2.x ratio), computed from the hex values:

| Foreground | on `--bg` #000 | on `--surface` | on `--surface-2` |
| --- | --- | --- | --- |
| `--text` #ecf3ee | 18.6 | 16.5 | 14.7 |
| `--text-2` #b7c6bd | 11.8 | 10.5 | 9.3 |
| `--muted` #879a8e | 7.0 | 6.3 | 5.5 |
| `--accent-text` #4cc890 | 10.0 | 8.9 | 7.9 |
| `--accent` #2fae77 (as text) | 7.4 | 6.6 | 5.9 |
| `--ok` #7fd6a8 | 12.1 | 10.7 | 9.5 |
| `--warn` #f0b45a | 11.4 | 10.1 | 9.0 |
| `--dusk` #9db6ff | 10.6 | 9.4 | 8.3 |
| `--on-accent` on `--accent` | 6.7 | | |
| `--border-strong` (UI outline) | 3.7 | 3.3 | 2.9 |
| `--chart-past` (graphic) | 4.9 | 4.4 | 3.9 |
| Locked badge glyph on its disc | 6.3 | | |

Also:
- Touch targets: tab items about 120×64; kind cards 72 px tall; primary buttons 56 px; every other button, row, chip and disclosure at least 48 px.
- State is never color-only: selected kind = dot + border + icon color; active tab = indicator bar + weight; earned vs locked = check/"Earned" vs lock chip + progress text; current week = printed value + "This wk"; saved vs pending = check vs dots inside the cloud, plus an `aria-label`.
- The type scale is written in px for clarity. When integrating, consider `rem` (with `html { font-size: 100% }`, 17 px = 1.0625rem) so Android's font-size setting is honored. Check the 3-column badge grid at 130 % text: names clamp at 2 lines, cells grow taller, nothing overflows.
- Respect `prefers-reduced-motion` (section 8). There is no auto-playing motion anywhere.
- The views use real headings (`h1` per view, `h2` per section) so screen-reader users can jump.

---

## 12. Usability concerns in the current `index.html`, and recommendations

1. **The token field sits on the home screen.** It is a once-ever action that occupies the most valuable spot. Move it into the "Connect your Mac" sheet, opened from the chip; show the chip in `--warn` only when the token is missing or wrong.
2. **"Your Mac is not reachable" is styled as a warning** (`.warn`, orange). Offline is the expected state on a walk. Use neutral text and `i-cloud-off`; reserve amber for things the user must act on.
3. **Permission guidance is two always-visible paragraphs of 13 px text.** Make it the "Before you start" disclosure, open only before the first finished walk; 15 px minimum.
4. **13 px `.fine` text** is too small at arm's length and at night. Floor is 14 px; captions 14, sub-lines 15, body 17.
5. **Walk kinds are text-only pills about 50 px tall in three columns.** At 360 px they are cramped and the selected state is border-and-color only. Use the stacked 72 px cards with icon, one line, and a radio dot. Remember the last kind.
6. **The radio inputs are visually hidden without a focus style** on their visible part. Add `:focus-visible` on the card body.
7. **The episode list prefixes "(not ready)"** to titles and preselects the first episode silently. Show the plain title and a separate quiz-status line; keep the preselection but make the choice visible in the Start label ("Start podcast walk").
8. **`alert()` on start failure** is jarring and blocks. Show inline messages under the Start button (copy in section 9).
9. **The last-walk card shows the raw kind id** ("podcast", "walk") and a full `toLocaleString()` timestamp. Use the kind label and a relative day ("Tonight 19:32").
10. **"Technical details of the last walk" (raw JSON)** is on the home screen. Move it to a walk-detail screen or behind a long-press on the last-walk card; it is a developer tool.
11. **The resume card appears below the Start button** in the DOM order. It is the only thing that can lose data; put it first and make "Resume walk" the primary button.
12. **"Send to the Mac now" is shown even when the Mac is not reachable**, and failure is silent. Show the button only after a successful contact; otherwise say the queue sends by itself.
13. **Medals as text chips with long "how" text** turn the home screen into a scoreboard. Move badges to their own tab; keep only the one-time new-badge card on Walk.
14. **`theme-color` is #000 but the page background is #0b0f0d.** With the new `--bg` #000 they match, and AMOLED pixels are off for most of the screen.
15. **No `font-variant-numeric: tabular-nums`.** Distances and times jitter while the status updates; add it to all numbers.
16. **The service worker must precache the two sprite files**; otherwise all icons disappear offline, which is exactly when the app is used.
17. On the walk cover (out of scope, noted only): the "Hold 3 s to stop" box has no visible progress while holding. A ring that fills over 3 s (or, with reduced motion, a text countdown "3, 2, 1") would make the hold less of a guess.

---

## 13. Decisions to preserve during integration

1. **True black background and one accent.** `--bg` #000, green as the only accent, amber only for "needs you", dusk blue only for mind/quiz. Offline is never amber.
2. **Badge color comes only from the four custom properties.** Earned = set nothing; locked = `.is-locked` sets all four. Do not set them globally, and always pair the locked art with the lock chip and the progress text.
3. **Nothing on these screens waits for the Mac, and nothing pulls the user back.** Render from local data first; no streak-loss warnings, no badges computed on the phone, no looping motion; the new-badge moment is one card, shown once.
