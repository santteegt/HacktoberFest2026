# Lane H log: README and .env.example (2026-10-29, Claude Opus agent)

Owned: `README.md`, `.env.example`, this file. Nothing committed, nothing deployed, no code, test, doc or memory edited.

## Built

- `README.md` (about 148 lines) replaces the template: title, pitch, gallery link, challenge line; what it does (facts, wounds, the five kinds in prose, story and lexical verifier, fix recipes and the 0.8.38 gate, comic page, gallery, three pickers, Hermes profile); why open matters plus the honest counterweight; a numbers table with method per row; run steps (uv sync, Playwright Chromium, solc 0.8.38 install, Ollama, optional env, `haunt`, step commands, `gallery build`, `scripts/deploy.sh`, pytest, Hermes); how it was built; limits; credits; post-deadline placeholder; MIT.
- `.env.example` corrected against `ghosts/config.py`, `ghosts/llm.py`, `ghosts/fixes/compile.py` and `scripts/deploy.sh`.

## Sources for every number

All from `docs/CHALLENGE-MEMORY.md` (claims table, 07:50Z, 10:40Z, 12:10Z entries) and lane logs A, B, C1, D, G. Kind counts re-tallied from `data/ghosts/*/verdict.json` on 2026-10-29: 13 bad, 7 friendly, 5 lingering, 8 scarred, 9 historian, 3 never called (matches the memory). Page sizes 48-61 KB from Lane G's table.

## Findings

- `.env.example` said `ETHERSCAN_API_KEY` is a "fallback source of verified code when Sourcify has none". No code reads it beyond `config.py`; now commented out and labelled unused.
- Nothing loads `.env` automatically (no dotenv); the README and `.env.example` say to export it with `set -a; source .env; set +a`. Checked that the file sources cleanly in bash.
- Added optional `GHOSTS_NUM_CTX`, `GHOSTS_LLM_TIMEOUT` (llm.py) and `SOLC_0838` (compile.py) as commented lines; Discord names pointed to `hermes/.env.example`.
- The compile gate does not install solc 0.8.38 itself (it prints the install command), so the README lists `uv tool run --from solc-select solc-select install 0.8.38` as a setup step. Slither's own 0.4.x compilers are installed on demand by `wounds.py`.

## Not sourced in the repo

- "Ethereum History by cartoonitunes" comes from the coordinator's brief; the only trace in the repo is a historian link to `github.com/cartoonitunes/koth-v04-verification`.
- No test count is stated (the memory says 217, Lane C1's log says 223 later).

## Follow-up (2026-10-29, coordinator): Hermes ran live

Source: memory entries 17:45Z, 18:00Z (MEASURE, FAILED) and 18:20Z. README updated in three places: the agent paragraph (launchd host, bot connected, crons active, sloth profiles parked, first haunt deployed "The Silent Small Half" 0xc820… as the 26th ghost and featured story, report posted to Discord); the Numbers table (26 ghosts; the kinds row now says "first 25" with the old counts kept and notes the 26th is friendly and never called, re-tallied 13/8/5 from verdict.json; new row: first live haunt 28 s, method `last-haunt.txt` and the live index); the agent Limits bullet (chat path and MCP-from-Hermes untested; Discord 403 "Missing Access", code 50001, when the bot lacks channel access). The Run-it step 8 also names the channel permissions. Whether the first haunt was fired by the cron scheduler or by hand is not stated in the memory, so the README says only that it ran through the profile's script.
