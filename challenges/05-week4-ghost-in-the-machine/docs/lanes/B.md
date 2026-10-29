# Lane B: Stories and fixes (log)

Owner: Lane B worker (Claude Opus, build time). Runtime model: `gemma4:12b-it-qat` through Ollama on the author's M4 Max 64 GB.
Owned paths: `ghosts/llm.py`, `ghosts/story.py`, `ghosts/verify.py`, `ghosts/fixes/`, `tests/test_b_*.py`, `tests/fixtures/b/`, this file.

## What was built

| Piece | File | What it does |
| --- | --- | --- |
| Model client | `ghosts/llm.py` | `chat(messages, schema=None, think=False, temperature=0.6, num_ctx=8192)` → `(parsed_or_text, usage)` against Ollama `/api/chat`, non-streaming. `usage` = calls, seconds (Ollama `total_duration`), wall_seconds, prompt_tokens (`prompt_eval_count`), output_tokens (`eval_count`). With a schema, malformed JSON is retried once, then `LLMError`. One model name (`GHOSTS_MODEL`) and one `num_ctx` (`GHOSTS_NUM_CTX`, capped at 16384) for every call, so Ollama never reloads. |
| Verifier | `ghosts/verify.py` | Flattens facts.json + verdict.json + wounds.json + code-derived values (+ the fix recipe for the buster chapter) into leaves, then checks each sentence: years (exact), dates (month+day[+year], day+month, month+year, ISO; ranges like "Feb 6–8, 2016" in the historian text count), month names, every number with ≥ 2 digits (and number words ≥ 10, "twenty-one"), every ETH amount of any size, capitalized multi-word names, camelCase / `call()` identifiers, 0x hex, version strings, quoted phrases and back-ticked code. Number rules: exact first; else rounding the fact to the precision shown (83.0 ↔ 83.001304, 2.4 billion ↔ 2,425,858,453, "19,000" ↔ 19,461 because it shows two significant digits; "20,000" shows one and must be exact); else the floor of a whole number (10 years ↔ 10.7). Numbers inside timestamps, hashes, URLs and paths are not facts. Returns the matched fact paths, which become `facts_cited`. |
| Storyteller | `ghosts/story.py` | `tell(address)` → `data/ghosts/<address>/story.json` in the LANES.md schema. One model call per chapter with only that chapter's facts (empty keys pruned so the model is never shown a blank to fill). Plans: friendly/banished/lingering/alive → birth, life, silence (lingering: `variant: "the knocking"`; banished: `variant: "gravestone"`); bad → birth, life, haunting (first person, eerie), buster. Title and tagline are model-written and verified (code fallback if they fail). Each failing sentence gets one repair call (temperature 0.2); a clean rewrite counts as `repaired`, anything else is `dropped` and kept in `verifier.dropped_text` (plus `verifier.details` with the problems and the failed rewrite). `scary.snippet` is copied verbatim from wounds.json by code. Extra keys beyond the schema: `kind_source`, `derived`, `notes`, `verifier.details`, `verifier.method`, `model.calls`, `model.model_seconds`, `model.num_ctx`, `chapters[].variant`, `scary.finding`, `scary.incident`, `buster.recipe`, `buster.fix.{adapted, recipe, attempts, note, failed_attempts}`. |
| Fix recipes | `ghosts/fixes/recipes.py` | 14 recipes: reentrancy-eth, unchecked-lowlevel (alias unchecked-send, unchecked-transfer), suicidal, controlled-delegatecall, tx-origin, uninitialized-storage, weak-prng, constructor-name (aliases constructor-name-mismatch, wrong-constructor-name, …), locked-ether, arbitrary-send-eth, integer-overflow, msg-value-loop, incorrect-equality, shadowing-state. Each: a hand-written two-sentence explanation of what modern Solidity does (0.8 checked arithmetic, `constructor` keyword, CEI + lock, checked `call`, `selfdestruct` deprecated since 0.8.18 and neutered by EIP-6780 at Cancun, …) and a minimal `pragma solidity ^0.8.38;` snippet. Lookup by Slither check, alias, SWC id, or (last resort) keywords from the incident text. |
| Compile gate | `ghosts/fixes/compile.py` | Calls `~/.solc-select/artifacts/solc-0.8.38/solc-0.8.38 --bin` directly (no global `solc-select use`, so Lane A's 0.4.x Slither runs are never switched under them; `SOLC_0838` overrides; falls back to `uv tool run --from solc-select solc` with `SOLC_VERSION=0.8.38`). The model adapts the recipe to the ghost's identifiers; the code is accepted only if it compiles. Two failed attempts → the recipe's own snippet (also compiled) with `adapted: false` and a "generic" note; failed attempts and compiler errors are stored. |
| Tests | `tests/test_b_verify.py`, `test_b_llm.py`, `test_b_fixes.py`, `test_b_story.py` | Offline. Fake model that tells exactly one lie per chapter (a name + date, 777 ETH, a made-up quote, the year 1999, "42 years", 1987) and rewrites some cleanly (repaired) and some with a new lie (dropped); fake Ollama transport; mocked compile gate; real solc check of every recipe when solc 0.8.38 is installed (skipped otherwise). |

All 14 recipe snippets compile with solc 0.8.38+commit.1835d247 (2026-10-29, M4 Max, `solc --bin`).

## Measurements

Method: `tell(address)` from `uv run python`, Ollama 127.0.0.1:11434, `gemma4:12b-it-qat` (Q4_0, 11.9B), `think: false`, `num_ctx` 8192, temperature 0.6 for prose, 0.2 for repairs and code. Machine: the author's M4 Max 64 GB. Date 2026-10-29 (~05:10 UTC). Inputs: Lane A's verdict.json / wounds.json after its follow-up (05:05 UTC), and facts.json as upgraded by Lane A (chain birth times, dapp sites only). Seconds = wall time of the whole `tell` (model time is within 0.1 s of it; solc adds well under a second). Tokens are Ollama's `prompt_eval_count` and `eval_count` summed over every call (chapters, title, repairs, fix adaptation).

### Final run (the story.json files on disk)

| Ghost | Kind (Lane A) | Seconds | Calls | Prompt tok | Output tok | Sentences | Grounded | Repaired | Dropped | Fix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KingOfTheEtherThrone `0xb336…` | bad | 33.9 | 6 | 4,136 | 1,094 | 32 | 32 | 0 | 0 | unchecked-lowlevel, adapted, compiled 1st try |
| TheDAO `0xbb9b…` | bad | 38.0 | 6 | 4,162 | 1,176 | 29 | 29 | 0 | 0 | reentrancy-eth, adapted, compiled 1st try |
| Rubixi `0xe827…` | bad | 29.7 | 7 | 3,298 | 930 | 25 | 24 | 1 | 0 | constructor-name, adapted, compiled 1st try |
| StandardBounties `0x2af4…` | lingering | 22.6 | 4 | 2,458 | 740 | 23 | 23 | 0 | 0 | none (not bad) |

Output speed ≈ 30-35 tokens/s end to end including prompt processing (e.g. TheDAO 1,176 output tokens in 38 s); a single chapter call takes 4-10 s. The Rubixi repair was a verifier false positive ("Modern Solidity heals this wound forever." flagged "Modern Solidity" as an unknown name; the rewrite "Solidity version 0.8.38 cures this wound." passed). That false positive is fixed now, after the run.

### Every real-model run, for the verifier numbers

| Run (2026-10-29) | Inputs | Sentences | Flagged | Repaired | Dropped | Flagged sentences |
| --- | --- | --- | --- | --- | --- | --- |
| Dry runs before Lane A (KotE ×2, StandardBounties, Rubixi on a hand-made wounds fixture) | facts only / fixture | 89 | 1 | 0 | 1 | "Because I failed to rename my own birth, …" → "Because I" read as a name (false positive, fixed: pronoun "I") |
| Run 1 (all four, Lane A's first verdicts: all bad) | A v1 | 116 | 2 | 2 | 0 | "During the Turbulent Age, this wound bled out 98.043 ETH." (false positive: sentence-initial "During", fixed); "Some say the loss was $50 million, while others claim $60 million fell under the attacker's control." (false positive: the facts write "$60M", fixed) |
| Run 2 (overlapped Lane A's rewrite; discarded) | A v1/v2 mix | 107 | 0 | 0 | 0 | |
| Statistics round (aborted when StandardBounties turned lingering) | A v2 | 79 | 2 | 2 | 0 | details not kept |
| Final run | A v2 | 109 | 1 | 1 | 0 | "Modern Solidity …" (false positive, fixed) |
| Three statistics rounds (write=False) | A v2 | 338 | 0 | 0 | 0 | |
| **Total** | | **838** | **6** | **5** | **1** | |

Three-round statistics (seconds, prompt/output tokens, sentences; all grounded): KotE 33.0/34.6/35.0 s, 4,136 / ~1,040 tok, 30 sentences each; TheDAO 42.3/46.9/46.0 s, ~4,166 / ~1,250 tok, 28-31; Rubixi 30.4/33.8/33.2 s, ~3,023 / ~910 tok, 26-27; StandardBounties 27.2/23.2/22.8 s, 2,458 / ~720 tok, 20-26. Fix adaptation compiled on the first try in all 9 bad-ghost rounds. Earlier (before the prompt said "no `throw`, every function needs a visibility") TheDAO's adaptation failed twice (`throw` copied from the guilty code, then a truncated contract) and fell back to the generic recipe, and Rubixi's first try failed ("No visibility specified" on a copied `function DynamicPyramid()`).

### What this means (honest reading)

- **No dropped sentence in the final stories, so `verifier.dropped_text` is empty for all four.** The only real drop happened on a dry run and was a false positive. With `think:false`, one small prompt per chapter, empty keys pruned, and "copy dates and numbers exactly", the verifier flagged 6 of 838 sentences. The 4 flags whose details were kept were all verifier false positives, each fixed with a test; the 2 in the aborted round were repaired and their text was not kept. No inspected flag was a real invented date, number, name or quote from Gemma 4 12B. The verifier's ability to catch lies is shown by the offline tests (fake model, one lie per chapter: an invented person and date, 777 ETH, a made-up quote, the year 1999, "42 years", 1987; all caught, repaired or dropped).
- So the "silenced lines" panel (as in the Wayback Séance entry) has nothing real to show for these four ghosts. If the post wants that panel, it must show the test lies or the false positives, labeled as what they are. The model's real mistakes are **semantic**, and a lexical verifier cannot see them (examples below).
- Kinds: Lane A's final verdicts make KotE, TheDAO and Rubixi bad and StandardBounties lingering (with 5 non-fatal Slither "scars", which the life and knocking chapters mention). No friendly ghost exists among the four; the friendly path was exercised only on the KotE dry run with the heuristic kind (17.1 s, 4 calls, 2,673 + 616 tokens, 23/23 grounded).

### Semantic errors seen in real output (verifier passed them)

- KotE dry run: "It was created as a redesigned successor throne for Kieran Elby." (facts: deployed *by* him).
- KotE final, life: "it even featured a way to transfer ownership": nothing in the facts says so, and the sentence holds no checkable token.
- KotE dry run: "Not a single person has called to it in the last 12 months.": the "12" was grounded by a number in the historian's prose; the claim happens to be true but was not proven.
- TheDAO run 1 (before Lane A's sites fix): "Its legacy is preserved in 280 archive captures and numerous websites that have documented its rise and fall since 2003.": the 2003 came from Wikipedia/x.com captures that facts.py then listed as the dapp's sites. Lane A has since excluded reference hosts; `story.dapp_sites` filters them too (reference hosts, or sites first seen more than a year before the birth year).
- StandardBounties run 1: "I still hold 83.001304 ETH deep inside me, a weight I can never shed because my wound remains open.": the numbers are right; the "because" is invented.
- Rubixi final: "Now, I linger with only 4.022216 ETH left inside, a hollow shell haunted by the theft": the balance is real; the causal link to the 2016 theft is not.

## Honest limits

- **The verifier is lexical.** It proves that the checkable tokens (dates, numbers, names, quotes, identifiers) came from the facts, not that the sentence is true. Seen in the first dry run (2026-10-29, KotE, no verdict.json yet): "Not a single person has called to it in the last 12 months." passed because a "12" appears in the historian's description; it happens to be true (last call 2016) but was not proven. "It was created as a redesigned successor throne for Kieran Elby." passed although the facts say Kieran Elby deployed it ("for" should be "by"): the name is real, the relation is wrong.
- A number is checked against **every** fact, not the fact the sentence means: "10.7 years" is accepted whether the model meant age or silence.
- Single capitalized words ("Gitcoin", "Vitalik") and single-digit numbers are not checked; spelled-out numbers below ten are free.
- Title and chapter headings skip the multi-word-name rule (Title Case would flag every word); numbers, dates and quotes are still checked there.
- Month names "May" and "March" at the very start of a sentence are ignored (modal verb / verb).
- The repair step asks the same model; a repaired sentence is re-verified, never trusted.
- A name found anywhere in the facts passes in any role; "Vitalik Elby" at the start of a sentence would pass because "Elby" is in the facts (a sentence-initial word before a known single name is treated as ordinary capitalization so "Modern Solidity" passes).
- `today` is in the derived facts, so "today, October 29, 2026" is grounded by the clock, in UTC (the author's local date can differ by a day).
- The fix is a minimal pattern, not a patched copy of the whole old contract; "compiled" means solc 0.8.38 produced bytecode without errors, not that the fix is audited.

## Follow-up: writing quality and minimal fixes (2026-10-29, coordinator's five points)

### What changed

1. **No raw identifiers in prose.** The chapter views no longer carry the full address, the deployer, the commit string, the birth block or the list of years. Code passes short labels instead, built in `story.derive`: `deployer_short` "0xbfdb…7645", `compiler_label` "Solidity 0.4.18", `activity_label` "active every year since 2022", `site_labels` "bounties.network, online since 2017 and still online in 2026". The verifier accepts any `0xPREFIX…SUFFIX` form when a real hex fact starts and ends with those parts, and it accepts the digits at either end of an address ("a wallet ending in 7645"). A new **style gate** (`story.style_problems`) sends a sentence back for a rewrite when it holds a full 0x hex, a `+commit.` string, the birth block number or three or more years. A grounded sentence that stays non-compliant is removed and counted under `verifier.style.dropped`, not under `dropped_text`, because it is not a silenced lie.
2. **Voice.** The rules ask for mostly short sentences (under 18 words) with varied rhythm, an opening image, and no filler ("a testament to", "a set of rules"). "Contract" and "block" are glossed once, woven into the birth chapter; later chapters are told not to gloss. When `eh.description` exists, the life chapter is built from the historian's description and significance (prompt `life_historian`). When there is no historian text and the ghost has a catalog incident, the first sentence of the catalog summary is used (Rubixi: "a Ponzi-style contract whose leftover constructor…"). The knocking chapter says who still knocks in plain words, judged from the functions still called, and does not repeat lifetime counts, active years or websites.
3. **Haunting stays first person**, grounded in `wound` and `incident` only. Today's balance was removed from that view, since twice it had produced a false causal link. The incident date is passed as "April 2, 2016" so no ISO date reaches prose. Rubixi's "April 2, 2016" and "took the fees" come from Lane A's catalog (`incident.date` 2016-04-02; summary: "several accounts claimed ownership and withdrew the collected fees").
4. **Fixes: the model now only chooses names.** It returns a map from the recipe's renamable names to names in the ghost's source. Code applies the renames, outside strings and comments, to the hand-written recipe. A rename is refused when:
   - the target is not a declared name in the old source;
   - the target is the misnamed old constructor (`DynamicPyramid`);
   - the target is a keyword;
   - the recipe name already exists in the old contract (it keeps its own name, e.g. Rubixi's `changeOwner`);
   - the roles differ (function vs variable);
   - the argument counts differ;
   - the names share no word or listed synonym with the recipe name. Generic verbs (change, set, get, update) don't count, so `changeOwner` cannot become `changeFeePercentage` and `credit` cannot become `sweepCommission`.
   
   Then `meaning_problems` checks per-recipe must and must-not patterns (constructor-name: `constructor()` and an `external onlyOwner` function; reentrancy: `nonReentrant` used, balance zeroed before `.call{value:`, `require(ok`; unchecked: `(bool ok, ) =` and no `.send(`/`.transfer(`; incorrect-equality: `>=` and no `== address(this).balance`). Then solc 0.8.38 compiles it. After two failed tries, the recipe itself is used. The constructor-name recipe now shows `constructor()`, `onlyOwner` on `collectFees` and `changeOwner`, and no function named after the contract. Before this change the model rewrote whole contracts. The previous Rubixi fix kept a public `DynamicPyramid()` that reassigned the owner; TheDAO's subtracted a balance after zeroing it (`totalSupply -= balances[user]` after `balances[user] = 0`) and carried a "Simplified for example" comment; KotE's carried a misleading comment.
5. **Scars line** for non-bad ghosts with confirmed wounds: `scars_note` gives the knocking chapter the two worst distinct checks in plain words ("a balance check that demands an exact amount", "a door left open for a caller to step back in mid-call") with the buster's advice from the recipe. StandardBounties: "It bears two old scars: … Never wait for an exact balance and pay last to lock the door."

Tests: 79 Lane B tests (styled raw identifiers, short hex, address ends, the old constructor refused, role, argument and same-job guards, recipes compile with real solc and pass their own meaning checks). Full suite green.

### Final run after the follow-up (the story.json files on disk)

Same method as above (2026-10-29, M4 Max, `gemma4:12b-it-qat`, think false, num_ctx 8192). KotE and TheDAO were re-told after the argument-count guard landed. Each row is the run whose file is on disk.

| Ghost | Kind | Seconds | Calls | Prompt / output tok | Sentences | Grounded | Repaired | Dropped | Style rewritten / dropped | Fix (renames applied) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KingOfTheEtherThrone | bad | 35.1 | 7 | 4,882 / 861 | 44 | 44 | 0 | 0 | 0 / 0 | unchecked-lowlevel; contract name only (3 renames refused: `excessPaid`, `sweepCommission`, `claimThrone` wrong job or arguments) |
| TheDAO | bad | 40.5 | 7 | 5,779 / 831 | 45 | 45 | 0 | 0 | 0 / 0 | reentrancy-eth; `receiveEther`, `refund` (2nd try) |
| Rubixi | bad | 35.2 | 7 | 3,897 / 683 | 31 | 31 | 0 | 0 | 0 / 0 | constructor-name; `collectAllFees` (2nd try: `changeOwner` kept its own name) |
| StandardBounties | lingering | 14.1 | 4 | 2,079 / 446 | 25 | 25 | 0 | 0 | 0 / 0 | none |

Prose is ~20 % shorter in output tokens than before (e.g. KotE 1,094 → 861), and sentences are more numerous and shorter (KotE 32 → 44).

### Verifier and style flags across the follow-up runs (two dry runs, the final pass, two re-tells; 503 sentences)

- **First real catch on real output:** TheDAO, final pass before the re-tell: "Its crowdsale raised over 18 million tokens." `18 million` is not in the facts; the historian's short description is cut at "raised ov…". It was repaired to "Its April 2016 crowdsale raised tokens." (grounded, but flat). That story was later re-told, and the file on disk has no repairs.
- False positive, fixed: "A wallet ending in 7645 brought it into the world." (address ends as numbers).
- Style gate: KotE twice wrote "The contract lived at 0xb336a86e2feb…" (the full address, apparently copied from the historian prose); it was rewritten to a short form both times.
- Semantic slips the verifier cannot see, still present: KotE haunting says the developer paid "the victims by hand on February 19" (the date is in the facts as the last call, and the repayment comes from Lane A's loss note; the link between them is the model's own); Rubixi buster: "Anyone can call it to take the crown" in the present tense.

## Follow-up 2: never-called ghosts, honest busters, incident framing (2026-10-29, 25 ghosts on disk)

Input: Lane G's batch findings (`docs/lanes/G.md`) and Lane A's corrected `facts.py`. `life.tx_count` now counts calls with the creation excluded, and `life.never_called` landed at ~05:50 UTC. With it, **3** ghosts are never called: greeter, UserWallet, BlockSwapWrapperGolemNetworkToken. The other six that Lane G saw at 0 now have real counts and last calls (HumanStandardToken 1, EtherVote 1, TemplateCrowdsale 4, Saffron 30, stakedXYM 60, BondFixedExpiryTeller 103), and their verdicts were refreshed at 05:50.

### What changed

1. **Never called** (`story.never_called`: `life.never_called` when present, else `tx_count == 0`).
   - No life chapter, no `last_seen_on` in derived. The silence chapter becomes `variant: "never called"` (ask `nobody_knocked`: "nobody ever knocked").
   - Bad ghosts that were never called get birth, haunting, buster; the haunting is told that nobody ever called it.
   - The style gate rejects "last call / final call / last called / last time anyone…" for these ghosts, and the tagline fallback says "nobody ever called it".
2. **Honest busters.** When no recipe matches (7 DeFiHackLabs picks), the buster chapter uses `buster_nofix`: it says the wound is a design flaw that no compiler version and no Solidity upgrade fixes, then gives a two-sentence general mitigation.
   - **Flaw kinds:** `story.flaw_of` maps the record's cause to trade ordering, price oracle, governance, input validation, access control, bridge verification or economic logic.
   - **What the story carries:** `buster.fix` stays null, and `buster.fix_reason` says plainly that the advice is a hand-written general mitigation for that kind of flaw, not taken from the incident's references (the catalog carries no mitigation text, and we do not fetch the links). `buster.mitigation` holds `{flaw_kind, advice}`.
   - **Recipe lookup** now uses only the record's own words (cause, name, finding title) plus the finding's or incident's `swc`, never the long summary.
   - **Busters that do have a recipe:** each recipe carries `compiler_enforced` (true only for constructor-name, integer-overflow, uninitialized-storage, shadowing-state). When it is false, the buster must not say the compiler or the version fixes it ("The compiler does not stop this shadow by itself": TheDAO).
3. **Incident framing.** For `defihacklabs-*` incidents, the haunting view gets `my_part`:
   - `what_i_am`: from the contract name or an ERC-20 ABI, e.g. "a router", "a proxy, a front door that passes calls on to another contract", "a token".
   - "My address is named in the DeFiHackLabs record of the X incident. The record does not say what part I played."
   - "The loss belongs to X as a whole, not to me alone."
   
   The hand-written catalog entries (TheDAO, Rubixi, KotE) are about the contract itself and keep their first-person loss. **Still in use:** when a bad ghost passes the alive bar (≥ 100 calls in 12 months or ≥ 5 % of lifetime), the haunting gets `people_still_use_me` and one sentence with the counts. That is TheDAO (223 / 175,183) and Rubixi (75 / 712). The sentence says "People still use me…", not "every day": 75 calls a year is not daily.
4. **Verifier fixes found by this run:**
   - Punctuation now ends a name run: "Multichain (Anyswap)" had been read as the name "Multichain Anyswap", which dropped the two most important framing sentences of Anyswap's first re-tell, so it was re-told.
   - A number must end at a word boundary: the "24" in a hex tail "24c5" had been read as a number (3 repairs).
   - `derived.other_wounds` lets "11 other wounds" ground.
   - Titles: each capitalized word must be English (system word list `/usr/share/dict/words`) or appear in the facts, because titles skip the multi-word name rule. All 25 current titles pass; greeter's "Blokur" is real ("Hello from Blokur!").

Tests: 84 Lane B tests (never-called plan and style gate on a copy of greeter's files; the honest buster and `my_part` on a copy of Bean's; alive bar; flaw kinds; parentheses; hex tails; title words). Full suite: 217 passed.

### Re-told ghosts (18) and their numbers

Method as before (2026-10-29 ~06:00 UTC, M4 Max, `gemma4:12b-it-qat`, think false, num_ctx 8192). Chapters: B birth, L life, S silence, H haunting, B buster. Anyswap's row is its second re-tell, after the parentheses fix.

| Ghost | Kind | Chapters | Seconds | Prompt / output tok | Sentences | Grounded | Repaired | Dropped | Style rewritten | Fix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BlockSwapWrapperGolemNetworkToken (never called) | bad | B/H/B | 15.8 | 2,597 / 480 | 27 | 27 | 0 | 0 | 0 | uninitialized-storage |
| UserWallet (never called) | bad | B/H/B | 16.6 | 3,059 / 523 | 25 | 25 | 0 | 0 | 0 | unchecked-lowlevel |
| greeter (never called) | friendly | B/S | 8.4 | 1,264 / 271 | 14 | 14 | 0 | 0 | 0 | — |
| HumanStandardToken | friendly | B/L/S | 11.7 | 1,848 / 351 | 21 | 20 | 1 | 0 | 0 | — |
| TemplateCrowdsale | bad | B/L/H/B | 26.4 | 4,628 / 694 | 35 | 34 | 1 | 0 | 0 | unchecked-lowlevel |
| SaffronERC20StakingPool | friendly | B/L/S | 11.7 | 1,707 / 362 | 21 | 21 | 0 | 0 | 0 | — |
| EtherVote | friendly | B/L/S | 13.9 | 2,040 / 412 | 25 | 25 | 0 | 0 | 0 | — |
| stakedXYM (AdminUpgradeabilityProxy) | friendly | B/L/S | 12.1 | 1,694 / 353 | 23 | 23 | 0 | 0 | 0 | — |
| BondFixedExpiryTeller | bad | B/L/H/B | 19.2 | 2,887 / 577 | 34 | 33 | 1 | 0 | 0 | none (fix_reason: input validation) |
| MonoX Token | bad | B/L/H/B | 20.5 | 2,648 / 563 | 33 | 33 | 0 | 0 | 0 | none (price oracle) |
| Unitroller | bad | B/L/H/B | 23.0 | 2,660 / 572 | 38 | 38 | 0 | 0 | 0 | none (price oracle) |
| AnyswapV4Router | bad | B/L/H/B | 17.5 | 2,732 / 619 | 38 | 38 | 0 | 0 | 0 | none (input validation) |
| QUATERNION | bad | B/L/H/B | 24.8 | 2,629 / 524 | 33 | 33 | 0 | 0 | 0 | none (economic logic) |
| Bean | bad | B/L/H/B | 27.0 | 2,825 / 560 | 30 | 29 | 1 | 0 | 0 | none (governance) |
| SushiMaker | bad | B/L/H/B | 25.8 | 2,641 / 532 | 31 | 31 | 0 | 0 | 0 | none (trade ordering) |
| KingOfTheEtherThrone | bad | B/L/H/B | 41.2 | 6,003 / 841 | 41 | 41 | 0 | 0 | 1 | unchecked-lowlevel |
| TheDAO | bad | B/L/H/B | 36.4 | 5,972 / 800 | 38 | 38 | 0 | 0 | 0 | reentrancy-eth |
| Rubixi | bad | B/L/H/B | 30.1 | 4,094 / 717 | 33 | 33 | 0 | 0 | 0 | constructor-name |
| **Total** | | | | | **540** | **536** | **4** | **0** | **1** | |

All 4 repairs and Anyswap's 2 drops in the first re-tell were verifier false positives, now fixed: hex tails "51c4", "956c", "24c5"; "11 other wounds" (true: 12 findings minus 1); "Multichain (Anyswap)". The style gate caught KotE writing its full address again. Not re-told (unaffected): StandardBounties, TerraNullius, MyToken, FoundationTipJar, token, DSTP, PolygonL1Switchboard.

Sample lines:
- Anyswap: "I am the router. My address sits in the DeFiHackLabs record of the Multichain incident. The record stays silent on my part. The loss belongs to Multichain as a whole."
- Bean buster: "No compiler version and no Solidity upgrade can heal this wound. Count the voting power from a snapshot taken before a proposal opens…"
- greeter: "It waited in the quiet for 10.1 years. No one ever called it."

### Limits

- `what_i_am` comes from the name, so "a helper contract" for SushiMaker and "a teller contract" for BondFixedExpiryTeller are guesses from words, not facts about their role in the hack.
- The mitigations are hand-written per flaw kind; they are not taken from each incident's post-mortem.
- "Never called" counts only direct transactions; a contract called only by other contracts (internal calls) would count as never called.

### For the renderer (outside my paths)

`ghosts/render.py` already hides the code panel when `buster.fix` is null. It does not show `buster.fix_reason` or `buster.mitigation`, and its own fixed lines say "Last call: …" (timeline and "moment" text, around lines 422-452) even when `facts.life.never_called` is true and `last_tx` is null. It should print "Never called" instead. The silence chapter of a never-called ghost has `variant: "never called"`.
