# Week 4 brainstorm: Ghost in the Machine

Written 2026-10-26 23:10Z (Mon Oct 26, 18:10 local), about 4 hours after the challenge opened. Safe deadline Oct 31 06:59Z (Fri Oct 30, 01:59 local); page deadline one day later. That is **four evenings plus Friday night as margin**, less than Week 3 had. Sources: the wiki (playbook, partner catalog, Week 1-3 pages and retrospectives, Hermes, Gemma, Ollama, small-model patterns, parallel lanes), the Week 3 memory, the Week 4 brief, and a DEV search of what is already published for this theme.

## What is already on DEV for this theme (day one)

| Already published | What it is | Effect on us |
| --- | --- | --- |
| GhostShell, ECHOES, PhantomTerminal AI | Haunted terminals with local models (the brief's first example) | **Avoid.** Three entries in the first hours; the idea is the brief's own |
| Wayback Séance (ziwenqingshu) | Dead websites tell their life story from Wayback snapshots, local Gemma 3 4B, every sentence cited and checked by code, live ofrenda pages | **Avoid dead-link and dead-website ideas.** Very well executed; a bookmark-hoard version would read as derivative |
| Echoes of Memory | Offline oral history keeper (whisper + Gemma 2 via Ollama), no demo or code shown | Oral history is open but crowded (also the brief's example) |
| git-ofrenda | Epitaphs for files deleted from a repo's git history, local Gemma on CPU | Avoid "dead code" and "deleted files" ideas |
| GhostGPT | Horror story generator with Ollama | Avoid generic story generators |
| MergeMeter | TabPFN on closed PRs predicting merges | TabPFN category already has a strong early entry |
| Calavera Cabina, AI Buddies ofrenda | Tribute and ofrenda apps | Generic ofrenda builders are crowded |

Nothing published touches blockchain remains, RC racing, or a family WhatsApp group.

## Author's assets that a 4-evening build can lean on

- M4 Max (64 GB), Gemma 4 12B QAT on Ollama at 64k context, `embeddinggemma:300m`, whisper.cpp, Piper, Hermes Agent v0.22.5 with Discord and the Baileys WhatsApp bridge (parked), Stagehand on local Chrome, Postgres on Tiger Data, OpenRouter paid ids.
- 7,845 Chrome bookmarks going back to 2017 (2,830 from 2017 and 1,528 from 2018: the ICO era), Ethereum, Solidity and Noir interest, an Ethereum wallet history (private).
- An RC car club on WhatsApp with a racer who already tested Week 2's agent.
- Spanish and English. Nov 2 is a real family date in the author's region.

## Idea 1 (recommended): "The contract still answers": a séance for dead dapps

**Pitch.** A ghost in the machine, literally: a dapp whose website, team and Twitter died years ago, but whose contract is still on Ethereum, still holds state, and still answers any call. The tool finds those ghosts in your own past (your ICO-era bookmarks and, privately, the contracts your wallet touched), summons each one with its verified source code and on-chain remains, has a local Gemma write its obituary from facts that code verified, and lets you hold a séance: you ask in plain words, the model picks a read-only function from the ABI, code makes the `eth_call`, and the ghost answers with the raw result shown beside its words. Every ghost gets an ofrenda page: what it promised (archived site), when the site died (Wayback), what is still alive on chain (balance, holders, last transaction), and the séance transcript.

**Theme fit.** Spooky (things still moving in the dark with nobody behind them) and honoring the past (the 2017-2018 wave the author lived through, with its own "ofrenda" for projects that mattered to them). The brief's last example ("brings an abandoned open-source tool or a forgotten corner of internet history back to life") fits exactly; the twist is that these corners were never dead.

**Why open.** The strongest why-open story of the three: the contracts are open source and permanent by construction, the model is a file on disk, the RPC can be a node you run, and nothing in the pipeline needs a key or an account. A hosted assistant would disappear the way these dapps' front ends did. The author's wallet address and bookmarks never leave the Mac; only the ofrenda pages chosen for publication are public.

**Stack.** Python CLI (`ghost scan`, `ghost summon <address>`, `ghost seance <address>`, `ghost ofrenda`), Gemma 4 12B through Ollama for obituaries and function choice (JSON schema, labels in the prompt), Sourcify v2 for verified source and ABI (Etherscan API as fallback, free key), a public RPC (publicnode) with `eth_call`, `eth_getCode`, `eth_getBalance`, Wayback CDX for the site's death date, Postgres on Tiger Data with pgvector for "which ghost mentioned X" search over source and archived text, static HTML ofrenda (the same approach as Week 3's board pages). Hermes is optional (a `#seance` Discord channel) and should be cut if it costs more than an hour.

**Partner categories.** Gemma (core, real). Tiger Data (hybrid search over ghosts, real if `scan` stores them). .tech domain or Render only if the public ofrenda goes live (ask before claiming). No Browserbase, Auth0, Temporal, Sentry this week.

**Scope for four evenings.** Mon: feasibility and contracts (below). Tue: `summon` (Sourcify, RPC facts, Wayback dates, obituary with code-verified numbers). Wed: `seance` (ABI view functions only, gated in code; never `payable`, never signing; raw result always shown) and the ofrenda page. Thu: `scan` over the author's bookmarks and wallet, the Spirit-of-it moment, screenshots, post draft staged. Fri night: margin and publish.

**Day-one checks (Mon night, kill rule: any check failing by Tue 09:00 local moves to idea 2).**
1. Find at least **8 dead dapps with a contract address** from the 2017-2018 bookmarks (archived page text or ENS) or the wallet's transaction list. Fallback: a seeded list of well-known dead dapps, labelled as such. The agent could not run this probe (the permission classifier blocked reading the Chrome Bookmarks file), so the author runs it.
2. Sourcify coverage for 2017-era contracts. Verified today: CryptoKitties core (2017) returns a full `match` with a 66-entry ABI from `sourcify.dev/server/v2/contract/1/<address>`; a public RPC `eth_call` of `name()` returned "CryptoKitties" with no key.
3. Gemma 12B choosing a view function from an ABI given a plain question: measure on 20 questions across 3 contracts; gate in code (function must exist, be `view` or `pure`, arguments typed).

**Spirit-of-it moment.** The author's own: a contract their 2017 self sent a transaction to, with no website left, still answering `balanceOf(author)`. If it holds something, that is the post's opening line. Needs no other person, so it cannot slip.

**Risks.** Niche for non-crypto judges (mitigate with plain-language obituaries and the GeoCities-style framing, not jargon); public RPC rate limits (cache every call); Etherscan key if Sourcify misses too many (free tier is fine); the wallet is private, so the published ghosts must be chosen by the author.

**Name candidates.** Ofrenda On-Chain, Séance Chain, Still Answers, Ghost Dapps.

## Idea 2 (alternative if the author wants family in it): "Altar por WhatsApp"

**Pitch.** A family WhatsApp group becomes an ofrenda. Relatives send voice notes, photos and stories about a person who died; a Hermes profile on the Baileys bridge (the Week 2 setup, rebuilt fresh) collects them, whisper.cpp transcribes Spanish locally, Gemma 4 12B pulls out the names, dishes, songs, sayings and anecdotes and asks the group one gentle follow-up question a day ("¿Cuál era su plato favorito?"); the altar page (candles, marigolds, the photos, the favorite foods, the stories in the family's own words) is built locally and shown on a tablet on Nov 2. Nothing is uploaded anywhere except WhatsApp itself.

**Theme fit.** Día de los Muertos in the brief's own words, in Spanish, with a real family. Differentiated from Echoes of Memory by the group interview agent, the follow-up questions, and the real Nov 2 moment.

**Why open.** Family voices and photos on the family's own machine; works without internet once collected; a closed transcription or chat API would mean uploading a dead relative's stories to a vendor.

**Stack.** Hermes profile + Baileys (closed: WhatsApp, say so), whisper.cpp (Spanish), Gemma 12B via Ollama, local SQLite or Postgres on Tiger Data, static altar page. ElevenLabs only for narrating the demo, never for cloning a voice of the deceased.

**Partner categories.** Gemma, Tiger Data, possibly ElevenLabs (demo narration).

**Risks.** Depends on 2-3 relatives sending material by Thursday; the Baileys bridge restart quirks (documented in the wiki); emotional content means the post must be written with care and with the family's permission; the Spirit-of-it moment is the strongest of the three if it happens and the weakest if it does not.

**Day-one check.** The author asks the family tonight. If fewer than two relatives say yes by Tue, this idea is out.

## Idea 3 (long shot): "Ghost lap" for the RC club

**Pitch.** In racing games the ghost is your past best lap. Take the club's lap-timing exports, let TabPFN predict the next lap from your history (the ghost's forecast), and let Gemma + Piper whisper the ghost's commentary in your earbud during practice ("your August self was 0.3 s faster here"). Honors the past (your own, and the club's), spooky in the racing sense.

**Why it is third.** Needs lap-time data the club may not export, a phone-side audio loop that Week 1 showed is fiddly, and TabPFN already has a strong early entry. Keep as a fallback only if the author has lap data at hand.

## Rejected outright

- Haunted terminal (three entries already, the brief's own example).
- Bookmark dead-link ofrenda and anything Wayback-centered (Wayback Séance is already published and strong).
- Deleted-code or abandoned-repo revival (git-ofrenda, Deadline Necromancer).
- Horror story generators and smart-home ghost stories (generic, and the author has no sensor logs).
- Séance with a dead programming language (fun, thin, the brief's example).

## Recommendation

**Idea 1.** It is the only one that needs nobody else, has its data on the author's machine already, has a why-open answer that is literally the project's subject, and has no competitor on DEV as of tonight. Idea 2 wins only if the author wants to spend the week with family and two relatives say yes tonight. Decide Mon night; run idea 1's three checks before Tue 09:00 local.
