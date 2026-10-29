# Lane A log: verdicts and wounds

Owner: Lane A (Opus 5.5 agent). Not committed; the coordinator folds this into the memory.

## What was built (2026-10-29 UTC)

- `ghosts/facts.py`
  - `clean_name()` drops control/non-printable chars and whitespace; an empty result is "no name". Blockscout returns `"\u0001"` for TheDAO; `blockscout.name` is now normalized to the cleaned value or `null`, and `pick_name()` walks source → blockscout → EH etherscan name → EH token name → address. TheDAO now resolves to `TheDAO`.
  - `safe_relpath()` keeps Sourcify source paths relative under `src/` (no `..`, no absolute root). `source.files` lists the relative paths.
  - `add_activity()` adds `life.last_12m_txs`, `life.last_12m_capped`, `life.first_tx_timestamp`. `upgrade()` runs when a cached facts.json loads, so older files get the new keys without a full re-summon. No key was renamed or removed.
- `ghosts/sources/blockscout.py`: `recent_activity()` paginates `/addresses/{a}/transactions?filter=to` newest first through `next_page_params` and counts `status == "ok"`. It stops at the first tx older than 365 days, or after 10 pages (500 txs) with `capped=true`. `first_transaction()` makes one call with `sort=block_number&order=asc`, which Blockscout honors.
- `ghosts/activity.py`: pure functions with `now` injected: `silent_years`, `last_12m_share`, `is_alive` (≥ 100 calls, or ≥ 5 % of lifetime), `is_long_silent` (≥ 2 years), `site_dead` (no site, or every `last_ok` older than 2 years).
- `ghosts/classify.py`: `decide()` (pure), `verdict()` (schema), `classify(address)` writes `verdict.json`. It runs `wounds.analyze` when wounds.json is missing.
- `ghosts/wounds.py`: `analyze(address)` writes `wounds.json`, with `slither.json` (raw), `stdjson.json` (Sourcify standard JSON input) and `stdjson.slither.json` (same input, keys made safe-relative) next to it.
- `ghosts/catalog/incidents.json`: 10 entries, 2016-2020. A research subagent wrote it from fetched sources (URLs in each entry). I checked the KotET postmortem myself. I added the `line_hint` field (TheDAO: `withdrawRewardFor(msg.sender)`).
- Tests: `tests/test_a_activity.py`, `tests/test_a_classify.py`, `tests/test_a_wounds.py` (35 tests, offline, fixtures in `tests/fixtures/a/`; the Slither fixture is trimmed to detectors). `uv run pytest`: 137 passed in 0.67 s for the whole suite. The Lane A tests also pass with the proxy pointed at a dead port.

## Verdicts (2026-10-29 ~05:00 UTC, decided by `ghosts.classify`) (SUPERSEDED by the follow-up below: StandardBounties is now lingering)

| Ghost | Kind | Why (code) | Kind if it had no wounds |
| --- | --- | --- | --- |
| KingOfTheEtherThrone v0.4.0 `0xb336…` | **bad** | catalog incident `kotet-v040-2016` (98.043 ETH of failed sends, all refunded); 3 unchecked `send()` in `claimThrone` confirmed by it | friendly (silent 10.7 y, 0 calls in 12 m) |
| TheDAO `0xbb9b…` | **bad** | catalog incident `thedao-2016`; snippet = the end of `splitDAO` (lines 989-1014 of EH source) | alive (223 calls in 12 m) |
| Rubixi `0xe827…` | **bad** | catalog incident `rubixi-2016`; regex `constructor-name` (DynamicPyramid, lines 13-15) confirmed by it | alive (75 of 712 = 10.5 %) |
| StandardBounties `0x2af4…` | **bad** | Slither on verified 0.4.18 source: 4× `reentrancy-no-eth` (Medium/Medium), 1× `incorrect-equality` (Medium/High) | lingering (fallback: 27 calls in 12 m, sites still captured in 2026) |

Activity (Blockscout, 2026-10-29): KotET 21 lifetime / 0 in 12 m; TheDAO 175,183 / 223; Rubixi 712 / 75; StandardBounties 19,461 / 27. Nothing was capped.

## Findings in detail

- **KotET v0.4.0** (tier `catalog`, regex on solc 0.2.1): `claimThrone` lines 99-103, 106-110 and 119-123 (unchecked `send`) are confirmed by the postmortem. The `sweepCommission` send (166-168) stays suspected.
- **TheDAO** (tier `catalog`, regex on EH `source.eh.sol`, no compiler version and no pragma): w1 is the catalog finding at `splitDAO`. The 5 `call.value` and 1 unchecked `send` are suspected, including `payOut` (194-203), the real reentrant call in 2016. The catalog's `function_hint` is `splitDAO`, so only that function is confirmed.
- **Rubixi** (tier `catalog`, regex on 0.2.1): `DynamicPyramid()` is confirmed (SWC-118). 4 unchecked sends are suspected.
- **StandardBounties** (tier `slither`): 97 raw results; 5 kept after the shortlist. Dropped as off-shortlist: `controlled-array-length` (High/Medium ×3), `reentrancy-balance` (High/Medium ×2), naming and other informational results. The reentrancy paths call `tokenContracts[_bountyId].transferFrom` before writing state, so exploiting them needs a malicious token chosen by the bounty's own issuer. **No incident is documented for StandardBounties; it is "bad" only by the rule "Slither Medium+/Medium+".**

## Timings and tools (Apple M4 Max 64 GB, macOS 26.6.2, Python 3.14.0, 2026-10-29 UTC)

- Slither 0.11.6, crytic-compile 0.4.2, solc 0.4.18 via solc-select (`SOLC_VERSION` env, so the global version stays unchanged).
- StandardBounties, Slither on the standard JSON (`--compile-force-framework solc-json`, cwd = `src/`): 1.0-3.9 s per run, about 2.6 s wall for `wounds` end to end. Single-file fallback: 1.14 s, same 5 findings.
- Regex/catalog tier: about 0.15 s wall per ghost.
- facts upgrade (pagination + first tx) for all four: 10.4 s, network-bound (Blockscout).

## What failed and how it was fixed

- `slither std.json --compile-force-framework solc-json` run from another directory compiled, but then failed with `Invalid compilation: Unknown file: StandardBounties.sol`. Running Slither with cwd set to a folder that holds the sources at the stdjson's relative paths (we use `src/`) fixed it. This took about 5 minutes; the 30-minute fallback budget was not needed. The single-file fallback still exists and was exercised once.
- The first ad-hoc run used `solc-select use 0.4.18`, which writes `~/.solc-select/global-version` (it now reads 0.4.18). The code uses the `SOLC_VERSION` env instead.

## Honest limits

- **All four ghosts come out "bad".** Three are cataloged incidents. StandardBounties is bad only because Slither reports `reentrancy-no-eth` and `incorrect-equality` at Medium. No exploit is documented for it. The post must not call it "hacked".
- TheDAO, Rubixi and StandardBounties are still called in 2026 (223 / 75 / 27 successful calls in 12 months). Without their wounds they would be alive, alive and lingering, never friendly.
- KotET: the primary postmortem puts the failed payments on **v0.4.0 (0xb336…)** and never mentions v0.3.0. Ethereum History says the bug was v0.3.0's. The catalog follows the postmortem: v0.4.0 has `incident: true`, v0.3.0 (0xa9d1…) has `incident: false`. The loss is 98.043 ETH by the appendix vs "98.5 ether" in the timeline; all of it was refunded.
- Regex findings are suspected (confidence Low, `confirmed=false`) and never make a ghost bad on their own. A catalog entry confirms only matches inside its `function_hint`.
- TheDAO has no verified source on Sourcify or Blockscout. The regex and the snippet use Ethereum History's `source.eh.sol`, and nothing fetched proves it matches the deployed bytecode (catalog notes).
- `site_dead` cannot tell a dapp site from a reference link. facts.py adds every non-EH/etherscan/github link, so TheDAO's "sites" are Wikipedia, CoinDesk, EF blog and x.com, and bounties.network may now be a parked page. The Wayback data for x.com includes 1996 captures (a CDX prefix artifact). This matters only for lingering vs fallback.
- Taxonomy gaps, which the code covers with a fallback (stated in the reasons): (a) called in the last 12 months below the alive bar while a site still answers → lingering; (b) silent 1-2 years → lingering. The 5 % share rule makes small contracts "alive" with few calls (Rubixi: 75 calls).
- **Data bug found:** TheDAO `birth.timestamp` from Ethereum History is `2016-04-30T05:42:58Z`, but Blockscout says block 1,428,757 is `2016-04-30T01:42:58Z` (4 h earlier; the first tx to the contract is in that same block). The date is unchanged; the hour is wrong. Not fixed (outside the three facts.py fixes).
- Catalog loss figures disagree between sources for TheDAO ($50M Wikipedia vs ~$60M Atzei et al.); `loss_usd` carries 50,000,000 and `loss_note` says so. Fomo3D has no SWC and no check. The Lendf.Me address is verified only by Blockscout's contract name. The research agent's caveats are in each entry's `notes`.

## CLI wiring for the coordinator (tested from a scratch copy of the app)

```python
@app.command("classify")
def classify_cmd(address: str, rerun_wounds: bool = typer.Option(False, "--rerun-wounds", help="Re-run the wound analysis first")):
    """Decide the ghost's kind (banished > bad > alive > lingering > friendly) into verdict.json."""
    from .classify import classify as _classify
    v = _classify(address, rerun_wounds=rerun_wounds)
    typer.echo(f"{v['kind']}  {v['address']}")
    for r in v["reasons"]:
        typer.echo(f"  - {r}")


@app.command("wounds")
def wounds_cmd(address: str, no_slither: bool = typer.Option(False, "--no-slither", help="Skip Slither (regex + catalog only)")):
    """Find wounds (Slither on solc>=0.4 source, cited catalog, regex on older source) into wounds.json."""
    from .wounds import analyze
    w = analyze(address, use_slither=not no_slither)
    typer.echo(f"tier {w['tier']}  {len(w['findings'])} finding(s)  incident: {(w['incident'] or {}).get('name')}")
    for x in w["findings"]:
        typer.echo(f"  {x['id']} {x['check']} {x['impact']}/{x['confidence']} {'confirmed' if x['confirmed'] else 'suspected'} {x['file']}:{x['lines']} {x['title']}")
```

## Schema notes for other lanes

- `wounds.json` follows LANES.md and adds `source_origin` (`src|eh|none`), `catalog_entry` (id), `run` (method, seconds, errors, tools) and `analyzed_at`. `incident` adds `id, loss_eth, loss_note, cause, swc`. A catalog finding has `check: "catalog"`; when the source does not contain the hinted function, it may have `file/lines/snippet` set to null. Regex checks are named `call-value`, `unchecked-send`, `selfdestruct`, `tx-origin` and `constructor-name`. Slither's `timestamp` is reported as impact `Informational`.
- `verdict.json` follows the schema exactly.

## Follow-up (2026-10-29 UTC, coordinator's three changes)

1. **Scars vs fatal** (`ghosts/classify.py`). A wound is **fatal** when it is confirmed, impact High and confidence ≥ Medium. It is a **scar** when it is confirmed, impact ≥ Medium and not fatal. `bad` requires a catalog incident or a fatal wound. `verdict.wounds` gains `scars` and `fatal`. Reasons include a line like "5 scars (incorrect-equality, reentrancy-no-eth), none fatal". Suspected (regex) findings are never scars or fatal.
2. **Birth time from the chain** (`ghosts/facts.py` `fix_birth_time`). Sources tried in order: Blockscout's creation transaction, then archive RPC `eth_getBlockByNumber`. When the chain disagrees with Ethereum History, `birth.timestamp` takes the chain value and EH's value moves to `birth.timestamp_eh` with a `birth.note`. New key `birth.timestamp_source` = `blockscout|rpc`. TheDAO: chain `2016-04-30T01:42:58Z`, EH `05:42:58Z`. The other three agree to the second.
3. **Dapp sites only** (`collect_sites`, `is_reference`, `site_life`). Sites are the `--site` values plus EH links whose host is not a reference host. Reference hosts: wikipedia.org, coindesk.com, blog.ethereum.org, ethereum.org, x.com, twitter.com, medium.com, reddit.com, github.com, github.io, etherscan.io, ethereumhistory.com, youtube.com, youtu.be, archive.org. Excluded URLs are listed in the new top-level `sites_excluded`; `eh.links` is unchanged. Wayback rows are kept only when the capture's original host equals the site's host (without `www.` and port).
   - Diagnosis: the 1996 x.com captures were not a prefix match. `wayback.captures()` reduces a full URL to its host, so a tweet link was looked up as the bare `x.com` domain, which has existed since the 1990s.
   - The host guard lives in facts.py, because `ghosts/sources/wayback.py` is not a Lane A path.
   - Cached facts.json files are upgraded on load (`sites_excluded` missing → recompute; `timestamp_source` missing → fix birth).

### Verdicts after the follow-up (`uv run ghosts classify <addr> --rerun-wounds`, 2026-10-29)

| Ghost | Kind | Wounds (count / confirmed / scars / fatal) | Why |
| --- | --- | --- | --- |
| KotET v0.4.0 | **bad** | 4 / 3 / 3 / 0 | catalog incident; 3 scars (unchecked-send), none fatal |
| TheDAO | **bad** | 7 / 1 / 0 / 1 | catalog incident; fatal: catalog finding at `splitDAO` |
| Rubixi | **bad** | 5 / 1 / 0 / 1 | catalog incident; fatal: `constructor-name` DynamicPyramid |
| StandardBounties | **lingering** | 5 / 5 / 5 / 0 | 27 calls in 12 m; 5 scars (incorrect-equality, reentrancy-no-eth), none fatal; reached through the lingering fallback because bounties.network and gitcoin.co still had captures in 2026 |

Sites now: KotET keeps `http://www.kingoftheether.com/postmortem.html` (93 captures, host-filtered); TheDAO has none (7 reference links excluded); Rubixi none; StandardBounties keeps bounties.network and gitcoin.co (given with `--site`).

Tests: 44 Lane A tests (9 new) pass offline with the proxy pointed at a dead port. The full suite passes: 148 tests in 0.49 s. Fixtures under `tests/fixtures/a/*/facts.json` were refreshed from the upgraded files.

## Follow-up 2 (2026-10-29 UTC): calls vs transactions, generic names

**Calls vs transactions** (`facts.set_calls`, `blockscout.count_calls`, `newest_page`, `first_transaction(skip=)`, `recent_activity(skip=)`).
- Blockscout lists the creation tx under `filter=to`, and its `transactions_count` excludes it. Checked: KotET has 22 listed txs and a counter of 21; DSTP has 2 listed and a counter of 1.
- The counter answers "0" for contracts it never counted. 9 of the 25 ghosts had 0 although 6 of them have real calls: BondFixedExpiryTeller 103, SaffronERC20StakingPool 30, stakedXYM proxy 60, TemplateCrowdsale 4, EtherVote 1, HumanStandardToken 1. The new rule:
  - A counter > 0 is trusted.
  - A counter of 0 is checked against the tx list, minus the creation tx, paged up to 20 pages.
  - `tx_count` = `calls`.
  - `last_tx` is the newest *successful call* or null.
  - `never_called` is true when the contract has no calls at all.
  - `first_call_timestamp` is added.
  - `last_12m_txs` was recounted without the creation tx.
- Truly never called: greeter, UserWallet, BlockSwapWrapperGolemNetworkToken. classify makes a never-called contract with code `friendly` ("never called after its birth N years ago"), still below banished and bad. UserWallet and BlockSwap stay bad (fatal Slither finding); greeter stays friendly with the new reason.

**Names** (`GENERIC_NAMES`, `name_candidates`, `pick_name`, `set_names`). `name` is the first non-generic name in the order EH name → EH token name → Blockscout → verified source, else any name. `names` lists every candidate with its source. `proxy` is set from the EH heuristic or a candidate name containing "proxy". Changed display names:
- MyToken → **MistCoin**
- AdminUpgradeabilityProxy → **stakedXYM** (proxy: true)
- token → **DigitalCommunityShare**
- MonoToken → **MonoX Token** (Blockscout's name now outranks the source name)

greeter, HumanStandardToken and TemplateCrowdsale keep their generic names because no other name exists.

**Kinds:** reclassified with the existing wounds.json, as instructed. No kind changed among the 25. Only greeter's reason changed.

Tests: `tests/test_a_calls_names.py`, 12 new, offline (fixtures under `tests/fixtures/a/extra/`). Lane A has 56 tests; the full suite passes (212 in 3.8 s). LANES.md: only the "Lane A adds" paragraph of the facts section was edited, with the coordinator's permission.

Limit: a contract whose counter is 0 and whose newest 1,000 txs are all calls gets `calls_capped: true`, so its count is a floor. None of the 25 hit the cap.
