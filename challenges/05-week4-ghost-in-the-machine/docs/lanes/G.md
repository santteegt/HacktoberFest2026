# Lane G log: `ghosts haunt` and the bigger altar

Built and run 2026-10-29 (about 05:15-06:00 UTC), Sonnet 5.5 agent. Machine: M4 Max 64 GB, home network, Ollama `gemma4:12b-it-qat` (`think:false`, shared slot with Lane B), dRPC free tier, no API keys. Nothing committed. Tests: `uv run pytest tests/test_g_haunt.py` = 19 passed, no network, no model; whole suite 199 passed (3.97 s).

## CLI wiring (coordinator, in `ghosts/cli.py`)

```python
from .haunt import haunt_cmd; app.command("haunt")(haunt_cmd)
```

Until then: `uv run python -m ghosts.haunt [ADDRESS] [--source archive|incident|random] [--year N] [--seed daily|STR] [--site URL ...] [--deploy] [--force] [--skip-face] [--max-blocks N] [--json]`. `--max-blocks` is an addition (random picker's block budget; the default 120 failed for 2016-2017 in Lane D's log).

## What it does (`ghosts/haunt.py`)

Chain: pick (when no address) -> summon -> wounds -> classify -> face -> story -> render -> gallery build -> deploy (only with `--deploy`, through `scripts/deploy.sh`).

- **Resumable.** A step is skipped when its output exists (`facts.json`, `wounds.json`, `verdict.json`, `shots/index.json`, `story.json`, `web/ghosts/<a>/index.html`) unless `--force`. Skipped steps keep the earlier run's seconds in `haunt.json` with `skipped: true`. The gallery index is rebuilt on every run (it takes milliseconds). Verified live: re-running TerraNullius = 6 skipped steps + gallery, 0 model calls.
- **Failure.** A failed step stops the chain, leaves partial files, writes `haunt.json` with `ok:false` and `error`, prints `FAILED ...` and exits 1. Face never stops the chain. A missing site is not a failure: note "no site known, no screenshots" (my first version reported it as FAILED on seven ghosts; changed after the first batch).
- **haunt.json** (`data/ghosts/<address>/haunt.json`): `{address, started_at, finished_at, kind, title, name, ok, error, steps:[{name, ok, seconds, note[, skipped]}], options, picked{source, reason, name, year, hint}, incident_hint, skipped_picks, gallery_path}`. It is rewritten after every step, so a crash mid-run still shows progress (with `finished_at: null`). A re-run by address keeps `picked` and the pick step.
- **Alive skip, picked addresses only.** After classify, an alive verdict moves the whole folder to `data/skipped/<address>/` (its `haunt.json` has `alive_skipped: true` and the reasons) and the picker is asked again, 3 tries in all. Retry seeds are `<seed>#<n>`; `daily` is resolved to the UTC date first so retries stay deterministic. An address already under `data/skipped/` is not worked again. A pick error (`LookupError`) also costs a try. An address given by hand is never skipped. Why move instead of leaving it in `data/ghosts/`: `render-all` renders every folder with a `facts.json`, so a leftover alive folder would become a gallery page. This happened to me: two facts-only folders I made while checking the featured set were rendered by someone else's `render-all` and appeared in `index.json`; I deleted both pages and rebuilt the index.
- **Incident hint.** For an incident pick whose address is one of the victim addresses, the DeFiHackLabs entry (name, date, cause, loss text, PoC and references) becomes a catalog-shaped entry passed to `wounds.analyze(catalog=load_catalog()+[entry])`. `checks` is empty, so no Slither finding is "confirmed" by it; Lane A's `apply_catalog` adds one `catalog` finding (High, confirmed) that carries the repository's words. Consequence: every incident pick becomes `bad`, even a victim that is still in use (see limits). The hint is recorded under `incident_hint`.
- **Locks.** One `flock` per address (`data/locks/<a>.lock`, non-blocking: two cron runs cannot work on the same ghost) and one around the story step (`data/haunt-story.lock`, waits up to 45 min) so two hauntings never queue two model calls on the single Ollama slot. These do not coordinate with Lane B's own runs.
- Site hints: `--site` plus `extra.site(s)` from the pick when present (the pickers do not return any today; the archive's sites come from `facts.eh.links` inside `summon`).

Tests (`tests/test_g_haunt.py`, 19): step order and record; deploy only when asked; skip-when-exists with old timing kept; resume after a failure; `--force`; face failure not fatal; `--skip-face`; summon failure stops at once; explicit alive address kept; alive pick moved and re-picked (face/story never run for it); three alive picks give up; pick error costs a try; earlier-skipped address not reworked; retry seed derivation; incident hint reaches wounds and is ignored for other addresses; per-address lock; face with no site vs a real failure; re-run keeps pick info. Fixture: `tests/fixtures/g/incident_pick.json` (JAY, copied from `data/incidents/2022.json`).

## The batch (2026-10-29)

Gallery went from 4 to 25 ghosts (4 original + 21 new); `web/ghosts/index.json` has 25 rows. `uv run python -m ghosts.haunt ...` for each. Seeds: archive 2015 `--seed daily` (2026-10-29), archive 2016 `g-2016`, archive 2017 `g-2017`, `g-a1` (2017), `g-a2` (2016); incident `g-inc21`, `g-inc22`, `g-inc23`, `g-i2`..`g-i5`; random `g-rnd18`..`g-rnd23`, `g-r2`. Year in the table = birth year from the chain; for incident picks the requested year is the incident's year (for example `--year 2023` gave QUATERNION, born 2021).

| address | name | born | picker | kind | wounds: tier findings/confirmed/scars/fatal | story s | verifier grounded/repaired/dropped of N | face | page | fix compiled |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `0x6e38a457…` | TerraNullius | 2015 | archive daily | lingering | regex 0/0/0/0 | 34.9 | 31/1/0 of 32 | 3 shots | 51.9 KB | |
| `0xf4eced2f…` | MyToken (EH: MistCoin) | 2015 | explicit (featured) | lingering | regex 0/0/0/0 | 25.2 | 26/0/0 of 26 | no site | 49.5 KB | |
| `0xfb691609…` | FoundationTipJar | 2016 | explicit (featured) | lingering | regex 1/0/0/0 | 20.7 | 27/0/0 of 27 | no site | 48.9 KB | |
| `0xafe6851c…` | token | 2016 | archive `g-a2` | friendly | regex 0/0/0/0 | 14.0 | 26/0/0 of 26 | no site | 48.8 KB | |
| `0xfcb0818c…` | greeter | 2016 | archive `g-2016` | friendly | regex 1/0/0/0 | 22.2 | 22/0/0 of 22 | no site | 48.2 KB | |
| `0x5656913c…` | BlockSwapWrapperGolemNetworkToken | 2017 | archive `g-a1` | bad | slither 1/1/0/1 | 19.2 | 40/0/0 of 40 | no site | 57.8 KB | yes |
| `0x8a57d270…` | EtherVote | 2017 | archive `g-2017` | friendly | slither 0/0/0/0 | 25.2 | 28/0/0 of 28 | no site | 48.7 KB | |
| `0xb3215bf5…` | UserWallet | 2018 | random 2018 | bad | slither 1/1/0/1 | 41.8 | 36/0/0 of 36 | no site | 57.7 KB | yes |
| `0xf98f439b…` | HumanStandardToken | 2019 | random 2019 | friendly | regex 0/0/0/0 | 12.8 | 21/1/0 of 22 | no site | 48.2 KB | |
| `0xbe9a630c…` | TemplateCrowdsale | 2020 | random 2020 | bad | slither 12/12/1/1 | 25.2 | 33/0/1 of 34 | no site | 61.2 KB | yes |
| `0x3d5bc3c8…` | Unitroller (Cream) | 2020 | incident `g-i5` | bad | slither 23/23/21/2 | 23.0 | 33/1/0 of 34 | no site | 59.7 KB | none |
| `0xe11fc0b4…` | SushiMaker | 2021 | incident `g-i3` | bad | slither 1/1/0/1 | 15.2 | 31/1/0 of 32 | no site | 55.4 KB | none |
| `0x8f5e7888…` | AdminUpgradeabilityProxy | 2021 | random 2021 `g-r2` | friendly | slither 0/0/0/0 | 11.1 | 23/0/0 of 23 | no site | 48.3 KB | |
| `0x6b7a8789…` | AnyswapV4Router | 2021 | incident 2022 | bad | slither 2/2/0/1 | 27.6 | 25/2/0 of 27 | no site | 57.0 KB | none |
| `0x6b00da74…` | SaffronERC20StakingPool | 2021 | random 2021 | friendly | slither 5/5/1/0 | 27.2 | 21/0/0 of 21 | no site | 48.1 KB | |
| `0xc9fa8f4c…` | QUATERNION | 2021 | incident 2023 | bad | slither 2/2/0/1 | 16.3 | 29/0/0 of 29 | no site | 59.9 KB | none |
| `0xdc59ac4f…` | Bean | 2021 | incident `g-i2` (2022) | bad | slither 1/1/0/1 | 17.9 | 26/4/0 of 30 | no site | 55.5 KB | none |
| `0x2920f7d6…` | MonoToken | 2021 | incident 2021 | bad | slither 3/3/1/1 | 15.6 | 31/0/0 of 31 | no site | 59.6 KB | none |
| `0x5415238f…` | DSTP | 2022 | random 2022 | friendly | slither 0/0/0/0 | 10.2 | 21/0/0 of 21 | no site | 48.0 KB | |
| `0x007fe7c4…` | BondFixedExpiryTeller (Olympus) | 2022 | incident `g-i4` | bad | slither 8/8/1/4 | 24.2 | 33/0/0 of 33 | no site | 59.3 KB | none |
| `0x053407df…` | PolygonL1Switchboard | 2023 | random 2023 | lingering | slither 2/2/1/0 | 12.1 | 25/0/0 of 25 | no site | 48.4 KB | |

Totals: 21 stories, 599 sentences, 10 repaired, 1 dropped. Story seconds 10-42 (median 20.7), each run 4-9 model calls. A whole haunt took 20-80 s when the model was free: summon 4-13 s, Slither 2-15 s (0.15 s for the regex tier), face 28 s only for TerraNullius (the other 20 had no site), story the rest. Pick time: archive 1-6 s (cache) and 0.1 s for incidents; random 2-36 s (2019: 16 s, 2020: 36 s).

Skipped, alive (moved to `data/skipped/`): CryptoPunks `0x6ba6f220…` (421 calls in the last 12 months), MoonCatRescue `0x60cd862c…` (224), Etheria v0.9 `0xe468d267…` (499+, capped). The alive picker rule never fired live: none of the 19 automatic picks classified alive (the loop is covered by unit tests only). Reasons: random picks came from blocks of a given year and most are quiet; incident picks are forced to `bad`, which wins over `alive`.

### Does the story read well (one sentence each, my reading of `story.json`)

- TerraNullius: good, the historian prose and the live Wayback shots give it a real arc (claims and messages in an append-only array), though "it let people stake claims" is vague.
- MyToken/MistCoin: best of the batch, the historian text gives Fabian Vogelsteller, the ERC-20 prototype and the 16-day gap to the draft; the page title uses the Blockscout name "MyToken", not "MistCoin".
- FoundationTipJar: reads well for the first half (Unicorn token, Foundation tips), flat in the "silence" chapter.
- token / greeter / EtherVote: pleasant and accurate because the historians wrote about them (go-ethereum wiki greeter, DCS token, EtherVote redeployed by Alex Van de Sande), but "last call" is really the deployment for greeter (see data bug 1).
- BlockSwap Golem wrapper: good, 40 grounded sentences and a compiled fix; the "uninitialized owner" story is told with the Slither finding.
- UserWallet, TemplateCrowdsale: the haunting chapters are clear (unchecked token transfer return), the buster chapter is generic; "lived with 0 transactions" in the life chapter is wrong (data bug 1).
- HumanStandardToken, DSTP, AdminUpgradeabilityProxy, Saffron pool, Polygon switchboard: grammatical and grounded but thin; a random verified contract with no site, no historian and no known story gives the model only dates, methods and a balance, so it writes about silence in general ("sits like a stone in a river").
- Incident picks (Anyswap, MonoToken, Bean, SushiMaker, Unitroller, Olympus teller, QUATERNION): the hack is told (DeFiHackLabs name, date, cause, loss) but about the *protocol*, not the contract we hold; the buster chapter has no code (no fix recipe), so it says "Solidity 0.8.38 seals the breach" without showing any.

## Failures, with causes

1. Face reported FAILED for ghosts with no site (greeter, Anyswap router and QUATERNION, before the fix): my step turned `capture`'s "no shots" into an error. Fixed (no site is a note, a real CDX/Playwright error still raises); those 3 haunt.json files keep the old FAILED note, stories unaffected.
2. A facts-only folder (from my pre-check of Unicorns and MeatGrinders with `ghosts summon` + `classify`) was picked up by `render-all` and published to `web/ghosts/`. Removed; this is why haunt moves alive ones to `data/skipped/`. The pre-check of CryptoPunks, MoonCat and Etheria was done in `data/ghosts/` and then moved by hand to `data/skipped/` with a hand-written `haunt.json`.
3. A re-run of TerraNullius by address overwrote its `haunt.json` and lost the pick info (the first version did not carry it over). Fixed in code and test; I restored the TerraNullius record by hand (noted in the step).
4. No run of haunt itself crashed or exited non-zero in the batch (21 of 21 ok).

## Honest limits (what the pipeline does badly on strangers)

1. **Data bug, outside my paths (facts.py / Blockscout counters):** `life.tx_count` is Blockscout's `transactions_count`, which excludes the creation transaction, and `life.last_tx` falls back to it. For a contract never called, `tx_count` is 0 and `last_tx` is the deployment (checked on greeter: counters all `"0"`, newest tx has `to: null`, same hash as `birth.tx`). 9 of the 25 ghosts show `tx_count 0`. The stories then say "lived with 0 transactions" and "last call that day" (greeter, HumanStandardToken, UserWallet, TemplateCrowdsale, Saffron, EtherVote, BlockSwap, Olympus teller, AdminUpgradeabilityProxy). Lexically grounded, factually wrong. Fix: treat `last_tx.hash == birth.tx` as "never called" and say so.
2. **Incident victims are proxies, tokens and helpers, and the "story" is a hack.** The PoC's first address is the victim "usually"; here we got a token (MonoToken, Bean, QUATERNION), a router (Anyswap), a Comptroller proxy (Unitroller), a bond teller that was never called (0 txs). The page tells the hack of the protocol over a contract that is not the guilty code, and the Slither finding is not tied to the incident. The incident rule makes the ghost `bad` even when the contract is alive (Anyswap router: 237,477 txs, last call 2026-07-14; Unitroller; Bean: 35 calls in 12 months; MonoToken: 8). `bad` beats `alive` in classify, so the alive skip never applies to incident picks.
3. **Buster has no fix for any incident pick (7 of 7).** Lane B's recipes are keyed on Slither checks; the catalog finding has check `catalog` and the cause words ("Insufficient Token Validation", "business logic flaw", "price manipulation") match no recipe. `buster.fix` is `null`, but the buster chapter text still says a modern Solidity version "seals" the wound. Lane B/C1 should either hide the buster section or say "no generic fix".
4. **Random picks are mostly meme-free but story-poor**: the sampler needs a verified, named contract, so we got tokens, proxies, a staking pool, a bridge switchboard, a DSTP royalty contract. None has a site (0 of the 14 random and incident ghosts had one), so no face and no "dapp died" evidence; classification rests on activity alone (and "friendly" for 2021-2022 ghosts that are only 4-5 years silent).
5. **Frontier / historian ghosts are the best ones**: only the 5 archive picks and the 2 featured ones have historian prose, and only TerraNullius had a site with Wayback captures. `facts.eh.links` seldom contain a dapp site.
6. **Naming.** Gallery names come from Blockscout/Sourcify: MistCoin is "MyToken", the proxy picked as "stakedXYM" is "AdminUpgradeabilityProxy" (the picker and facts disagree on the name for a proxy), another is just "token".
7. **Verifier**: dropped 1 of 586 sentences in this batch, and it was a real catch: TemplateCrowdsale "I have eleven other scars, but this one is a quiet rot." (12 findings but only 1 scar; the spelled-out number was checked against the facts). Repairs: 10 (Bean 4, Anyswap 2, TerraNullius, HumanStandardToken, Unitroller, SushiMaker 1 each). Still lexical: it passes "0 transactions" and "last call" claims that the data bug above makes false.
8. **Slither** ran on all 15 verified-source ghosts of solc >= 0.4 in 2-15 s. TemplateCrowdsale returned 12 findings all marked confirmed; the `timestamp` check shows up as "confirmed" at Informational on two incident ghosts (Lane A's flag semantics, not mine).
9. Not tested live: the alive-skip loop with the real pickers (no automatic pick was alive), the `--deploy` step (not run by instruction), and the story-lock wait (single-process batch). Ollama showed no loaded model before the first run; I did not see Lane B's runs overlap mine, but cannot rule it out (story seconds are in line with Lane B's).

## Requests outside my paths

- Wire the `haunt` command (line above).
- Data bug 1 in `ghosts/facts.py` (Lane A/coordinator).
- Lane B: no-recipe case for catalog findings; naming for proxies; the buster text when `fix` is null.
- A gitignore line for `data/skipped/` and `data/locks/`, `data/haunt-story.lock` (the locks are empty files; skipped holds a copy of facts.json etc., 1 MB).
- `pyproject.toml`: nothing added.
