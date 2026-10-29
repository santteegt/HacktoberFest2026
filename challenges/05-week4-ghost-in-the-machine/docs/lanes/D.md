# Lane D log: pickers and faces

Built 2026-10-29 (Wed night, local) by a Sonnet agent. Machine: M4 Max 64 GB, home network, no API keys. Nothing committed. Tests: `uv run pytest tests/test_d_*.py` = 20 passed, no network. The one dependency added: `playwright` 1.64.1 (`uv add playwright`, then `uv run playwright install chromium`, which fetched Chrome Headless Shell 156 into `~/Library/Caches/ms-playwright/chromium_headless_shell-1248`, 99 MiB).

## CLI wiring (coordinator, in `ghosts/cli.py`)

```python
from .pick import pick_cmd;               app.command("pick")(pick_cmd)
from .incidents import app as incidents_app;  app.add_typer(incidents_app, name="incidents")
from .face import face_cmd;               app.command("face")(face_cmd)
```

- `ghosts pick --source archive|incident|random [--year 2016] [--seed daily|<str>] [--n 3] [--max-blocks 120] [--dry-run]`. Prints the pick as JSON; `--dry-run` prints only the address(es). A pick never summons; chain `ghosts summon $(ghosts pick ... --dry-run)`. Exit 1 with a message when nothing is found.
- `ghosts incidents fetch [--year 2022] [--verify/--no-verify]` (default: 2021, 2022, 2023, verified).
- `ghosts face <address> [--site bounties.network --site gitcoin.co]`.

Python API: `pick.pick(source, year, seed)`, `pick.pick_many(source, n, year, seed)`, `pick.pick_address(...)`, `incidents.fetch(year)`, `incidents.load(year)`, `face.capture(address, sites)`.

## 1. Incidents (`ghosts/incidents.py`, `data/incidents/`)

Source: DeFiHackLabs `past/<year>/README.md` (raw.githubusercontent.com), every PoC `.sol` fetched through `get_text` (cached). The coordinator's counts (65 / 192 / 436) were `###` headings, which also include "Lost" and "Link reference" lines (the formats drift: `### Lost:` vs `#### Lost:`). Real entries (headings `### yyyymmdd Name - Cause`): 2021 page 51, 2022 page 129, 2023 page 214. The 2021 page also lists 14 older incidents (2017: 2, 2018: 3, 2020: 9); they are written to their own year files.

### Schema of an entry in `data/incidents/<year>.json` (hint passed to Lane A)

```json
{"date": "2021-12-21", "name": "Visor Finance", "cause": "Reentrancy",
 "loss_usd": 8200000, "loss_text": "$8.2 million",
 "poc_path": "src/test/2021-12/Visor_exp.sol", "poc_url": "https://github.com/SunWeb3Sec/DeFiHackLabs/blob/main/src/test/2021-12/Visor_exp.sol", "extra_pocs": [],
 "references": ["https://beosin.medium.com/…", "…"],
 "victim_addresses": ["0xc9f2…", "0x3a84…"], "ignored_well_known": ["0x7109…", "0xc02a…"],
 "primary": "0xc9f27a50f82571c1c8423a42970613b8dbda14ef", "primary_verified": true, "primary_name": "RewardsHypervisor",
 "chains": ["mainnet"], "chain": "mainnet|unspecified", "source": "DeFiHackLabs", "page": "…/past/2021/README.md"}
```

- `loss_usd` is only set when the text carries a dollar figure (`$8.2 million`, `~$4.4K`, `152M US$`, `535,706 USDT`, bare `365K`); `390 ETH`, `12BNB`, `$2.3 ETH` stay `null`, with the raw text in `loss_text`. Not guessed from coin prices.
- `victim_addresses`: every `0x…40` address in the PoC, lowercase, deduplicated, order of appearance, **minus a hard-coded well-known list** (Foundry cheatcode address, WETH, USDC, USDT, DAI, WBTC, UNI, LINK, stETH, Uniswap V2/V3 routers and factories, Sushi router/factory, Balancer vault, Aave V2/V3 pools, Permit2, Multicall3, zero/dead). Justification: these appear in nearly every PoC, are never the victim, and the first of them (the cheatcode address) used to rank first. They are listed in `ignored_well_known` so nothing is hidden. `primary` starts as the first remaining address; `verify_primary` then walks the first 3 candidates, asks Blockscout (`is_contract`, `is_verified`, `name`), and promotes the first verified one. `primary` is a hint, not proof: in a PoC the first address is usually the victim but can be a helper (for example a proxy or a pair). Lane A should still run Slither and treat the incident as `reference`.
- Chain filter: kept when the PoC's `createSelectFork("…")` names only `mainnet`, or names no chain and no reference points to another chain's explorer (bscscan, polygonscan, arbiscan, blocksec `/explorer/tx/bsc/` …). Dropped entries are listed in `<year>.dropped.json` with the reason.
- Everything here is parsed from public text by code; no model is involved.

### Counts (run 2026-10-29)

| page | entries | mainnet kept | dropped (other chain) | loss_usd parsed | primary victim verified on Blockscout |
| --- | --- | --- | --- | --- | --- |
| 2017 (from 2021 page) | 2 | 2 | 0 | n/a | 0 |
| 2018 (from 2021 page) | 3 | 3 | 0 | n/a | 3 |
| 2020 (from 2021 page) | 9 | 9 | 0 | n/a | 9 |
| 2021 | 37 | 18 | 19 | 13 | 16 |
| 2022 | 129 | 48 | 81 | 35 | 44 |
| 2023 | 214 | 77 | 137 | 57 | 64 |

Total of 157 usable entries for 2021-2023; 124 with a verified primary. Most DeFiHackLabs incidents are BSC (about 63 % dropped), so the "bad ghost by incident" pool is modest. Fetch time cold: 2021 11 s, 2022 37 s, 2023 61 s (PoC downloads), then Blockscout checks 18 s / 49 s / 119 s.

Honest limits: the chain filter trusts the fork name in the PoC; a PoC that forks mainnet but attacks a BSC address would pass (Blockscout is_verified then fails, which is why verification matters). `cause` and `loss` are the repository's words, not ours.

## 2. Pickers (`ghosts/pick.py`)

Return `{address, source, reason, name, year, extra}`. `seed`: `None` = random, `"daily"` = the UTC date, any other string = deterministic.

- **archive**: Ethereum History REST has no "documented" filter (`documented_only`, `has_short_description` params are ignored: checked), rows come in timestamp order. So the picker opens a random 200-row window inside the year (`from_timestamp` random day, `to_timestamp` year end), keeps rows with `has_short_description`, chooses one with the seeded PRNG; up to 10 windows, then falls back to the `featured` set (13 rows). Year default: 2015-2017 (where the historians wrote). This **mimics** `get_contract_of_the_day` (deterministic per UTC date) but is not the same rotation as the MCP server's, which enumerates the full documented set server-side; the same day gives the same pick only while EH data is unchanged (EH calls are cached 24 h). Tested 2026-10-29: 2015 (daily): TerraNullius, 2016 (daily): `Crowdsale`, one window each (3-5 s).
- **incident**: shuffles entries with the seed, takes the first whose primary victim is verified (stored flag, else a live Blockscout check). `extra.incident` carries the whole incident hint (name, date, cause, loss, poc_url, references, victim_addresses).
- **random**: random block in the year's range (block ranges: first block of each UTC year, checked against dRPC timestamps), `eth_getBlockByNumber(full)` on dRPC, every tx with `to == null` → receipt `contractAddress` → Blockscout `is_contract and is_verified and name`; stops at the first hit or after `max_blocks` (120). Reports `blocks_tried`, `creations_seen`, `rpc_errors`. Block bodies are cached by `ghosts.http` (data/cache is gitignored; 27 MB after this session's tests).

### Random picker, one try per year (seed `lane-d-<year>`, 2026-10-29, dRPC free tier, this machine)

| year | result | blocks tried | creations seen | seconds |
| --- | --- | --- | --- | --- |
| 2016 | DepositWallet (120-block cap hit first: 4 creations, none verified; rerun with `max_blocks=1000`) | 886 | 23 | 351 (first 120 blocks cached) |
| 2017 | ApprovedTokenDone (120-block cap hit first: 27 creations; rerun with 1000) | 181 | 52 | 115 (first 120 cached) |
| 2018 | LockToken | 9 | 13 | 17 |
| 2019 | NiftyWallet | 1 | 1 | 1 |
| 2020 | LunoDepositForwarder | 2 | 5 | 5 |
| 2021 | Little PikaInu | 17 | 16 | 28 |
| 2022 | Elf Made | 11 | 1 | 6 |
| 2023 | cryptopepe | 14 | 4 | 9 |

One try each, so the numbers show a spread, not a mean. With the 120-block cap, 2016 and 2017 each failed on the first try (4 and 27 creations seen, none verified and named). The same seeds with `--max-blocks 1000` succeeded at 886 and 181 blocks. Early years are sparse: about 1 creation per 30 blocks in 2016, and few are verified. For 2016-2017 prefer the archive picker or pass `--max-blocks 1000` (about 6 minutes in 2016). 2015 is rejected by the random picker's default year choice (2016-2023 drawn) but a year may still be passed.

## 3. Faces (`ghosts/face.py`)

Sites come from `facts.json` (`sites[].host`) or `--site`. For each site: `wayback.captures(site)` (CDX, one capture per month), first 200-status capture and last 200-status capture not after the ghost's last transaction (fallback: latest 200). Rendered with Playwright headless Chromium (Chrome Headless Shell) at 1200×800, the Wayback toolbar hidden (`#wm-ipp-base`, `#wm-ipp`), 2.5 s settle, one viewport screenshot. A shot under 8 KB counts as blank; then up to 2 neighbouring 200 captures are tried. Output `shots/<ts>.png`, `shots/index.json` (LANES.md schema plus a `site` key; the `cover` entry repeats the first site's first shot, same file) and `shots/report.json` (failures, timings, notes). Failures never raise.

Run 2026-10-29:

| ghost | site | role | capture | PNG size |
| --- | --- | --- | --- | --- |
| KingOfTheEtherThrone `0xb336…` | kingoftheether.com | first = last (only 200 capture before the last tx 2016-02-19) | 2016-02-11 | 90,374 B |
| StandardBounties `0x2af4…` | bounties.network | first (the 2017-09-23 capture rendered blank at 7,658 B, retried) | 2018-01-11 | 731,279 B |
| | bounties.network | last | 2026-06-07 | 262,803 B |
| | gitcoin.co | first | 2017-10-05 | 91,376 B |
| | gitcoin.co | last | 2026-10-07 | 100,503 B |

Cover for StandardBounties = bounties.network 2018-01-11 (first site, first shot). Render time 5-11 s per shot. Eyeballed: KOTET shot is the real kingoftheether.com warning page ("Odd behaviour has been reported on the blockchain since around 2016-02-06"), the gitcoin.co 2017 shot is the original landing page; toolbar not visible.

Limits: StandardBounties is **not silent**: its last successful call is today (`killBounty`, 2026-10-29), so "last capture before the last transaction" is the newest capture, and both bounties.network and gitcoin.co are alive sites; a "last" shot of a dead site only means something for ghosts whose dapp died. The CDX query is the site root only (`wayback.captures` normalizes to the host), not the `postmortem.html` path in the KOTET facts. Wayback replays pages with JavaScript, so some captures render partially (images missing on archived CDN assets). Pages that need a long load may show a spinner; the 2.5 s settle is a guess. No screenshot is faked or edited.

## Requests outside my paths

- Wire the three CLI lines above in `ghosts/cli.py`.
- `pyproject.toml` / `uv.lock` already carry `playwright`; fresh clones need `uv run playwright install chromium` (a line for README / install script).
- `ghosts/http.py` caches every JSON response, including full blocks (100-300 KB each for 2021+); `data/cache` is ignored, fine, but a `--no-cache` ttl for blocks would keep it small.
