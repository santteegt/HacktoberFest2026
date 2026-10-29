# Lane I log: DEV post draft (2026-10-29, Claude Opus 5.5)

Owned: `SUBMISSION.md`, `docs/post-assets/`, this file. Nothing committed, nothing staged or published on DEV, no other file edited.

## Read first

CHALLENGE-MEMORY.md (whole log, claims table, post-material table, including Lane H's 13:40Z entry that landed mid-lane), CHALLENGE.md, AGENTS.md, BRAINSTORM.md, ASSESSMENT.md, LANES.md, lane logs A, B, C1, C2, D, E, G; the Week 1-3 posts for house style; the Wayback Séance post (fetched with the DEV API) for structure only; the humanizer skill.

## Delivered

- `SUBMISSION.md`: the post, with the official template headings and front matter (`published: false`, tags `devchallenge, hf26challenge`), the "This is a submission for…" line, and the template's checklist kept at the bottom plus two lines for the image URLs and the session embed. About 1,930 prose words (alt text, comments and liquid tags excluded). No em or en dashes, straight quotes only.
- `docs/post-assets/01-05*.png` and `captions.md` (method, alt text, placement).

## Checks

- 223 tests: `uv run pytest -q --co` collected 223 on 2026-10-29.
- Live gallery `ghosts/index.json`: 25 ghosts; kinds 13 bad, 7 friendly, 5 lingering; 3 never called. Matches the memory.
- Quotes from model output in the post are verbatim from `story.json` (StandardBounties knocking chapter; the greeter's "Hello from Blokur!" comes from its source, quoted by the story). "eleven other scars", "18 million tokens" and "last call on the day it was born" are verbatim from the lane logs / memory.

## Left out on purpose (memory forbids or does not support)

- StandardBounties is never called hacked; its findings are called scars.
- No claim that the project works offline, that the verifier proves truth, that Hermes ran live, that the deny rules are a sandbox, or that the daily pick equals the MCP's contract of the day.
- No whole-build timing; only the structure of the lanes.
- No "silenced lines" panel claim on the live pages: the one real drop (TemplateCrowdsale) was in the first batch, and that ghost was re-told since, so its page may no longer show it.
- No ElevenLabs or Tiger Data mention.

## Notes for the coordinator

- The live gallery still shows the name "MyToken" for 0xf4ec…95dd although Lane A's follow-up renamed it MistCoin in facts.json; the gallery name seems to come from story.json. The post does not name it.
- "Two later lanes wrote the README and the first draft of this post" is in the build paragraph; cut it if the author prefers.
- The brainstorm-night `eth_call` of CryptoKitties' `name()` was run by an agent; the post says "I asked", in the author's voice.

## Follow-up (2026-10-29, after 18:20Z)

- Folded in the live Hermes run (memory 17:45Z, 18:00Z, 18:20Z): service host, older profiles parked, both crons named, one 28 s haunt via the profile script that deployed the 26th ghost (featured) and posted to Discord after the 403 "Missing Access" fix; still untested: Discord conversation and the MCP call from inside Hermes.
- Counts now 26 ghosts: 8 friendly, 5 lingering, 13 bad, 4 never called, 8 scarred (live index), 10 with a historian (live index `historian` flags; not yet in the memory).
- Stale: `01-gallery.png` and its alt text show the 25-ghost gallery (friendly 7) before gallery v2; retake if the post should match the live page.
- About 1,990 prose words.
- Retook `01-gallery.png` on the redesigned gallery (1100x1400 viewport, networkidle + 1.5 s); alt text in SUBMISSION.md and captions.md updated; one Demo sentence names the story-of-the-day card and the Lights / Ghost flies toggles.
