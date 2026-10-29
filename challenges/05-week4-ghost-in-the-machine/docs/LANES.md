# Lanes: who builds what, and the contracts between them

Coordinator: the main session (keeps this file, `docs/CHALLENGE-MEMORY.md`, `pyproject.toml`, `ghosts/config.py`, `ghosts/http.py`, `ghosts/cli.py` root wiring, commits). Lanes are worker agents. **A lane edits only its owned paths**, logs to `docs/lanes/<lane>.md` (what was built, measurements with date/machine/model/method, failures, honest limits), **never commits**, never edits the memory, and asks the coordinator (in its final report) for anything outside its paths. Adding a Typer sub-command: create `ghosts/<lane_module>.py` exposing `app = typer.Typer()` or plain functions, and tell the coordinator the one `app.add_typer(...)` / `@app.command()` line to wire; do not edit `ghosts/cli.py` yourself unless the brief says so.

Project: `uv` managed, Python ≥ 3.12, deps in `pyproject.toml` (ask before adding a dependency; `httpx`, `typer`, `pytest` are in). Run things with `uv run ghosts ...` and `uv run pytest`. Tests go in `tests/test_<lane>.py` and must not touch the network (use fixtures under `tests/fixtures/`; the four `data/ghosts/*/facts.json` files already on disk may be copied there).

Hardware and model: M4 Max 64 GB, Ollama at `http://127.0.0.1:11434`, model `gemma4:12b-it-qat` (open weights, Apache 2.0). Measured tonight: a schema-constrained one-sentence answer took 20 s because the model *thought* for about 1,000 tokens; pass `"think": false` in Ollama's `/api/chat` and keep `num_ctx` ≤ 16384 unless needed. Numbers from models are never trusted: every date, number and name the model writes must exist in the facts, or the sentence is repaired or dropped.

Honesty rules that bind every lane: the template is built once by a Claude agent (closed model) and the post says so; stories at runtime come from Gemma on the Mac; data sources are online services (Ethereum History, Blockscout, Sourcify, public RPC, Internet Archive); a vulnerability is `confirmed` only when Slither reports it on verified source or a catalog entry documents the incident with a reference, otherwise `suspected`; Hermes deny rules are not a sandbox; nothing from the author's wallet is ever written to disk in this folder.

## Files already in place (coordinator, M0)

- `ghosts/config.py` paths and URLs · `ghosts/http.py` `get_json`/`get_text` with file cache and per-host gaps · `ghosts/sources/{eh,sourcify,blockscout,rpc,wayback}.py` · `ghosts/hardforks.py` `age_of(block)` · `ghosts/facts.py` `summon(address, sites, force)` → `data/ghosts/<address>/facts.json` plus `decompiled.txt`, `source.eh.sol`, `abi*.json`, `src/*.sol` · `ghosts/cli.py` with `summon`, `show`.
- Known gaps for Lane A: `facts.py` name fallback printed blank for TheDAO (EH `etherscan_contract_name` is `TheDAO` in facts.json; check the fallback order and empty strings); `src/` flattens paths with `basename`, which breaks multi-file imports (keep relative paths); no recent-activity count yet.

## Ghost taxonomy (decided by code, Lane A)

| kind | rule |
| --- | --- |
| `banished` | `chain.code_present` is false (selfdestructed); gravestone only |
| `bad` | a catalog incident, or at least one Slither finding with impact **High** and confidence ≥ Medium on verified source; wins over every other kind except banished. **Medium-impact findings are scars, not a death sentence**: the kind is unchanged, `verdict.wounds.scars` counts them, and the story gets a short "scars" note with the buster's advice |
| `alive` | last-12-month successful calls ≥ 100, or ≥ 5 % of lifetime txs; not a ghost yet; the daily picker skips it |
| `lingering` | some calls in the last 12 months (below the alive bar) while the dapp is gone; "the platform died, people still knock" |
| `friendly` | no successful call for ≥ 2 years, no fatal wounds (scars allowed) |

## Schemas (contracts between lanes)

### `data/ghosts/<address>/facts.json` (exists; Lane A may add keys, never rename)
Top level: `address, chain_id, name, fetched_at, sources_used, birth{block,timestamp,tx,deployer}, age{hardfork,eh_era}, eh{...story fields, links, heuristics, has_source, has_abi}, blockscout{name,is_verified,creation_tx,creator}, life{tx_count, token_transfers, gas_used, last_tx{timestamp,method,status,hash}, recent_methods, recent_years, balance_wei, balance_eth}, chain{code_present, code_bytes, balance_wei, balance_eth}, source{provider, match, name, compiler_version, language, files, dir}, sites[{host, captures, first_capture, first_ok, last_ok, last_capture, years_alive}]`.
Lane A adds: `life.last_12m_txs` (int, successful calls, creation tx excluded), `life.last_12m_capped` (bool, true when pagination stopped at 500), `life.first_tx_timestamp` (oldest tx to the contract, usually the creation), `life.first_call_timestamp` (first call after the creation, null if none). **Calls, not transactions:** `life.tx_count` = `life.calls` = calls to the contract, the creation tx never counted (Blockscout's counter when it is > 0; its "0" is checked against the tx list, `life.calls_source` = `blockscout-counters|blockscout-txlist`, `life.calls_capped` when the list count stopped at 1,000); `life.last_tx` = newest successful call or **null**, never the creation; `life.never_called` (bool). `birth.timestamp` is the chain's block time (`birth.timestamp_source`), with `birth.timestamp_eh` and `birth.note` when the archive differs. `name` = first non-generic of Ethereum History name → EH token name → Blockscout → verified source (generic: MyToken, Token, Contract, Vyper_contract, AdminUpgradeabilityProxy, TransparentUpgradeableProxy, Proxy, ERC20, StandardToken, HumanStandardToken, Crowdsale, TemplateCrowdsale, greeter), else any name, else the address; `names` = `[{name, source}]` every candidate; `proxy` (bool). `sites` holds dapp sites only (`--site` + non-reference EH links, exact-host Wayback rows); `sites_excluded` lists the reference links left out. Cached facts.json files are upgraded on load.

### `data/ghosts/<address>/wounds.json` (Lane A)
```json
{"address": "0x…", "tier": "slither|catalog|regex|none", "compiler_version": "0.4.18+…", "analyzed_files": ["…"],
 "findings": [{"id": "w1", "check": "reentrancy-eth", "swc": "SWC-107", "title": "Reentrancy in withdraw()", "impact": "High", "confidence": "Medium",
   "confirmed": true, "file": "StandardBounties.sol", "lines": [120, 134], "snippet": "verbatim code of those lines", "description": "one paragraph, plain words", "reference_url": "…"}],
 "incident": {"name": "The DAO hack", "date": "2016-06-17", "loss_usd": 60000000, "summary": "…", "references": ["…"]} ,
 "slither_raw": "path to raw json or null"}
```
`incident` is null when none. `snippet` is cut by code from the file lines. Keep the shortlist of Slither checks: reentrancy-eth, reentrancy-no-eth, suicidal, arbitrary-send-eth, controlled-delegatecall, delegatecall-loop, uninitialized-state, uninitialized-storage, unchecked-transfer, unchecked-send, unchecked-lowlevel, locked-ether, weak-prng, tx-origin, msg-value-loop, unprotected-upgrade, incorrect-equality, shadowing-state, timestamp (Low → informational only).

### `data/ghosts/<address>/verdict.json` (Lane A)
```json
{"address": "0x…", "kind": "friendly|lingering|bad|banished|alive", "reasons": ["last successful call 2016-02-19, 10.7 years ago", "no wounds"],
 "activity": {"lifetime_txs": 21, "last_tx": "2016-02-19T21:51:14Z", "last_12m_txs": 0, "last_12m_capped": false, "silent_years": 10.7},
 "wounds": {"count": 0, "confirmed": 0, "worst_impact": null}, "labels": {"historian_story": true, "verified_source": true, "site_known": true}, "decided_at": "…"}
```

### `data/ghosts/<address>/story.json` (Lane B)
```json
{"address": "0x…", "name": "KingOfTheEtherThrone", "kind": "friendly", "title": "The throne that fell silent", "tagline": "one line",
 "chapters": [{"id": "birth|life|silence|haunting|buster", "heading": "…", "paragraphs": ["…"], "facts_cited": ["birth.timestamp", "life.tx_count"]}],
 "scary": {"paragraphs": ["…"], "snippet": {"file": "…", "lines": [a, b], "code": "…"}},
 "buster": {"paragraphs": ["…"], "fix": {"language": "solidity", "version": "0.8.38", "code": "…", "compiled": true, "compiler_output": "…"}},
 "model": {"id": "gemma4:12b-it-qat", "think": false, "seconds": 0.0, "prompt_tokens": 0, "output_tokens": 0},
 "verifier": {"sentences": 0, "grounded": 0, "repaired": 0, "dropped": 0, "dropped_text": ["…"]}, "generated_at": "…"}
```
`scary` and `buster` are null for non-bad ghosts. Chapters for friendly/lingering: birth, life, silence (lingering: silence becomes "the knocking"). For bad: birth, life, haunting (+ `scary`), buster (+ `buster`). For banished: birth, life, silence with a gravestone line.

### `web/ghosts/index.json` (Lane C2 builds; Lane C1 renders the pages it lists)
`[{"address": "0x…", "name": "…", "kind": "…", "age": "Byzantium", "born": "2017-12-18", "last_seen": "2026-10-29", "balance_eth": 83.0, "historian": true, "path": "ghosts/0x…/", "cover": "ghosts/0x…/cover.png|null", "title": "…", "tagline": "…"}]`

### `web/ghosts/featured.json` (Lane C3)
The newest index entry (same shape as an `index.json` entry plus `cover` and `generated_at`), or `null`; the gallery's story-of-the-day card reads it and falls back to `index[0]`. Cached 60 s on Vercel like `index.json`.

### Screenshots (Lane D)
`data/ghosts/<address>/shots/<ts>.png` and `shots/index.json` `[{"ts": "20160211005112", "site": "kingoftheether.com", "url": "https://web.archive.org/web/<ts>/<original>", "file": "shots/<ts>.png", "role": "first|last|cover"}]` (as Lane D wrote it; the renderer reads this shape). Lane C1 copies the cover into `web/ghosts/<address>/`.

## Lanes

| Lane | Model | Owns | Delivers |
| --- | --- | --- | --- |
| **A. Verdicts and wounds** | Opus | `ghosts/activity.py`, `ghosts/classify.py`, `ghosts/wounds.py`, `ghosts/catalog/` (YAML or JSON incidents 2016-2020), `ghosts/sources/blockscout.py` (extend), `ghosts/facts.py` (fix name fallback, keep relative source paths, add last_12m), `tests/test_a_*.py` | `ghosts classify <addr>`, `ghosts wounds <addr>`; Slither runner (solc-select per version; try Sourcify `stdJsonInput` with crytic-compile's solc-json platform, else the main `.sol` with the right base path); verdict.json and wounds.json for the four ghosts on disk |
| **B. Stories and fixes** | Opus | `ghosts/llm.py`, `ghosts/story.py`, `ghosts/verify.py`, `ghosts/fixes/` (recipes per check + 0.8.38 compile gate via solc-select), `tests/test_b_*.py` | `ghosts story <addr>`; story.json for the four ghosts, with the verifier numbers in the lane log; latency per ghost with `think:false` |
| **C1. Comic template and renderer** | Opus | `template/`, `ghosts/render.py`, `web/ghosts/` (output), `tests/test_c1_*.py` | `ghosts render <addr>` → `web/ghosts/<addr>/index.html` (self-contained: inline CSS/JS, no CDN at view time), storyteller + flying ghost, animated panels, summary card, snippet and fix panels; a sample page rendered from a fixture story.json |
| **C2. Gallery site and Vercel** | Sonnet | `web/index.html`, `web/assets/`, `web/vercel.json`, `ghosts/gallery.py`, `scripts/deploy.sh`, `tests/test_c2_*.py` | `ghosts gallery build` (writes `web/ghosts/index.json` and keeps `web/index.html` static with filters), Vercel project linked at root `web/` of this folder, first deploy, domain `eth-ghosts.decentraminds.tech` attached |
| **D. Pickers and faces** | Sonnet | `ghosts/pick.py`, `ghosts/incidents.py`, `ghosts/face.py`, `data/incidents/`, `tests/test_d_*.py` | `ghosts pick --source archive|incident|random [--year]` (archive: documented EH contracts, random or `get_contract_of_the_day` logic; incident: DeFiHackLabs `past/<year>/README.md` 2021-2023 parsed into `data/incidents/<year>.json` with victim addresses pulled from the PoC `.sol`; random: dRPC block sampler 2018-2023, verified+named via Blockscout) and `ghosts face <addr>` (Playwright screenshots of Wayback captures, toolbar hidden) |
| **E. Hermes profile** | Sonnet, starts after CP1 | `hermes/` (profile distribution: SOUL.md, skill, cron, config fragments, install script), `docs/HERMES.md` | daily `ghosts haunt` → render → gallery build → deploy; MCP server `https://www.ethereumhistory.com/mcp` configured; parking commands for the sloth profiles documented |

Checkpoint CP1: when lanes A-D report. The coordinator wires CLI commands, runs the pipeline end to end on the four ghosts, commits, and folds lane logs into the memory.
