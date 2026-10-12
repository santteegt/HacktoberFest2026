# Partner tools: feature catalog for ideation (Hacktoberfest 2026 Weekend list)

Compiled 2026-10-05 for the next challenges' ideation phase. The 16 prize-category partners of the Weekend Challenge ("Build for a Friend", DEV event 78) are listed with what each one actually offers, what is open and what is not, limits and credits, gotchas, and the kinds of idea each one fits. Weeks 1 to 4 reveal a new theme each Monday and may list different partners: re-fetch `get_challenge_details` for the challenge before relying on this list.

## How this was compiled (read before trusting a line)

- **Sources:** official docs pages fetched on 2026-10-05 (summarised by a small model from page excerpts, so some pages gave only partial detail); the 2026-10-04 partner report in `challenges/01-weekend-build-for-a-friend/PARTNER-REPORT.md` (researched by a subagent with cited URLs); and first-hand notes from building RC Pit Companion with Gemma 4, Ollama, Mastra and DevRelay (marked **First-hand**).
- **Tags:** [docs] confirmed on a fetched docs page today · [report] from the 2026-10-04 partner report, not re-checked · [first-hand] seen while building · [unverified] not confirmed anywhere. Prices and free tiers change; promo amounts need a login at hacktoberfest.com/my and were never checked.
- **Credits were not claimed** for any partner. Claims consume inventory: ask the author first.
- **Entered in the Weekend challenge:** Gemma, Mastra. Every other partner here is documented from docs only, not from use.

## The 16 partners at a glance

| Group | Partner | Tier (Weekend) | One-line role | Open? |
| --- | --- | --- | --- | --- |
| Models | Gemma | Featured $200 | Open-weight model family, runs locally | Weights Apache 2.0 |
| Models | Tinker | Featured $200 | Hosted fine-tuning/RL of open models, weights exportable | Trains open weights; service is hosted |
| Models | TabPFN | Featured $200 | Pretrained model for small tabular data | Code open; newer weights under a license to accept |
| Inference host | DigitalOcean | Featured $200 | Serverless and dedicated inference, agent platform, GPUs | Hosts open and closed models |
| App host | Render | Featured $200 | PaaS for web apps, workers, cron, Postgres | Closed host |
| Hardware | Arduino | Featured $200 | UNO Q: Linux + MCU board, App Lab | Open hardware/tools |
| Agent framework | Mastra | $100 | TypeScript agents, workflows, memory, evals | Apache 2.0 core |
| Orchestration | Temporal | $100 | Durable workflows, agent loops that survive crashes | Server MIT |
| Memory/API | Backboard | $100 | One API: memory, RAG, threads, many models | Closed platform |
| Voice | ElevenLabs | $100 | TTS, STT, voice agents | Closed |
| Search | SerpApi | $100 | Search results as JSON | Closed API |
| Data | MongoDB Atlas | $100 | Document DB with vector search | Hosted; local deployment possible |
| Data | Tiger Data | $100 | Postgres with TimescaleDB, vectors | Core extensions open |
| Observability | Sentry Agent Tracing | $100 | Traces for agent runs, tool calls, tokens | Hosted service, open SDKs |
| Dev process | Entire | $100 | Links agent sessions to git commits | CLI open source |
| Dev process | GitHub Copilot | $100 | Coding assistant, can use bring-your-own models | Closed |

## Per-partner notes

### Gemma (Google) · Featured · USED
- **What it offers [docs]:** Gemma 4 released 2026-03-31: E2B, E4B, 26B A4B, 31B; a 12B unified model on 2026-06-03; multi-token-prediction variants on 2026-04-16. Text, image and (on the small models) audio input; up to 256K context (128K on E2B/E4B); configurable thinking modes; function calling; Apache 2.0.
- **Where it runs [docs]:** Ollama, llama.cpp, MLX, Hugging Face Transformers, Google Cloud. Ollama tags `gemma4:e2b` (about 4.6 to 7.5 GB), `e4b` (6.6 to 9.5 GB), `12b`, `26b`, `31b`, plus MLX variants for Apple Silicon.
- **First-hand:** we used the QAT builds, `gemma4:e4b-it-qat` (6.1 GB) on an M4 Max and `gemma4:e2b-it-qat` (4.3 GB) on a 2019 Intel MacBook Pro. E2B on that CPU-only laptop: about 9.2 tokens/s writing and 38.7 tokens/s reading a prompt, which makes a two-call turn about 25 s. Ollama's JSON-schema `format` gave valid JSON every time, but the schema is invisible to the model (a schema-only prompt scored 3/25), so labels and their meanings must be in the prompt text. Ollama did not reuse a shared prompt prefix when the user text differed, so prompt length sets latency (389 to 252 tokens cut time to first token about 35%). The small model E2B falls back to one label on input it cannot place; do not trust it to refuse off-topic input (E4B refused 12/12 off-topic sentences, E2B 6/12): gate in code.
- **Good fits:** private or offline assistants on a laptop, structured extraction from documents or speech, classifiers with a tiny prompt, vision on photos of documents (E4B). **Weak fits:** anything needing fast generation on old CPUs.
- **Crowding:** likely the busiest category [report guess].

### Mastra · $100 · USED
- **What it offers [docs]:** TypeScript framework: `Agent` class (model as `provider/model`), tools via `createTool()` with Zod input schemas (plain objects silently fail), integrations with Next.js, React, Astro, Express, SvelteKit and Hono, `npm create mastra@latest`. Model providers via environment variables; any OpenAI-compatible endpoint works [report]. Docs say Node 22.18+ for getting started while the packages declare `>=22.13`.
- **Also [report]:** workflows, memory, RAG, evals, MCP, observability; Sentry integration via `@mastra/observability` with Sentry Node SDK v11+ and Mastra core 1.63.2+ [docs, from the Sentry page].
- **First-hand (Mastra core 1.74.0, libsql 1.25.0):** we used only workflows. A workflow with two suspend points (wait for the driver's choice, then for the outcome) was suspended and resumed across three separate processes with LibSQL snapshots. Traps: a Workflow object has a `.then()` method, so returning it bare from an async function hangs `await` and Node exits silently (wrap it as `{ wf }`); telemetry is on by default (set `MASTRA_TELEMETRY_DISABLED=1` for any offline claim); using Mastra means a Node process, not a static page. We kept the model calls on Ollama's native API instead of Mastra's model router because the router could not set `num_ctx`, and kept a plain-TypeScript fallback behind the same interface.
- **Good fits:** human-in-the-loop flows (suspend/resume), agent workflows with persistence, anything that is already TypeScript.

### Tinker (Thinking Machines) · Featured
- **What it offers [docs]:** a training API: you write the training loop locally, GPUs run remotely. Supervised fine-tuning, reinforcement learning (GRPO, PPO), DPO, distillation, LoRA from 1B to 1T+ parameters; 28+ base models; Python SDK clients (`ServiceClient`, `TrainingClient`, `SamplingClient`, `RestClient`); sampling returns log-probabilities; weights can be saved and exported, with cookbook utilities to build Hugging Face models, create PEFT LoRA adapters and publish to the Hub; 15+ recipes (math and code RL, tool use, multi-agent, prompt distillation, rubric grading).
- **Also [report]:** no Gemma; LoRA only; Qwen3.5-4B about $0.74 per million training tokens; promo available.
- **Gotcha [unverified]:** whether a downloaded adapter can be served locally (Qwen3.5 in llama.cpp or LM Studio) was never checked. Test serving before committing to an idea.
- **Good fits:** "sounds like my friend" writing assistants, small specialised classifiers or graders, anything where a swapped-in tuned open model is the point of the "why open" section.

### TabPFN (Prior Labs) · Featured
- **What it offers [docs]:** classification and regression on tabular data with no training loop; handles categorical strings, raw text and missing values automatically; TabPFN-3 and later claim up to 1,000,000 rows (subject to feature and checkpoint/API limits), with a sample-subsampling setting; local package `tabpfn` (TabPFN-3.5) with a GPU recommended past about 1,000 rows, or the `tabpfn-client` API (TabPFN-3.5-Plus) that needs only internet.
- **License [docs + report]:** you must accept the license and download weights before first use; newer weights are non-commercial [report]. The report said CPU is fine to about 5k rows, the docs recommend a GPU past 1,000 rows: treat CPU use as a test, not a given.
- **Good fits:** a friend's small spreadsheet (health log, habits, small business numbers) where you want predictions and top factors without ML plumbing; likely a small prize pool [report guess].

### DigitalOcean · Featured
- **What it offers [docs]:** Gradient AI Platform: serverless inference with an OpenAI-compatible API, agents with knowledge bases for RAG, multi-agent routing and guardrails, dedicated inference on GPUs for open-source and commercial LLMs. Docs note the Agent Development Kit is deprecated as of Oct 2026 and a new prepay "Inference and Agents balance" ($5 to $500, no expiry).
- **Also [report]:** serverless catalog includes open models such as gemma-4-31B-it, gpt-oss, Llama, Qwen, Mistral; GPU Droplets; a new-account credit around $5 for 90 days. Hacktoberfest promo [unverified].
- **Good fits:** when the user's machine is too weak for a model (host an open-weight model for them), or a hosted fallback next to a local-first design. Costs the offline story; say so.

### Render · Featured
- **What it offers [docs]:** web services, static sites, background workers, cron jobs, Workflows (task orchestration), Render Postgres, Render Key Value (Redis-compatible); deploys from Git or Docker.
- **Free tier [docs]:** 750 free instance hours per month per workspace; web services spin down after 15 minutes idle and take about a minute to restart; free Postgres expires 30 days after creation, 1 GB, one free Postgres or Key Value per workspace; Key Value is in-memory only; no persistent disk on free web services; no SSH; SMTP ports blocked. GPU offering not found [report]. Promo available.
- **Good fits:** hosting the web UI or webhook of an open-model project when a public demo link is needed; weak for a privacy-first story.

### Arduino (UNO Q) · Featured
- **What it offers [docs]:** UNO Q board: Qualcomm QRB2210 (quad Cortex-A53 at 2.0 GHz, Adreno GPU) running Debian, plus an STM32U585 microcontroller (Cortex-M33 at 160 MHz, 2 MB flash, 786 KB SRAM); Wi-Fi 5, Bluetooth 5.1; Qwiic connectors, UNO headers, MIPI-CSI/DSI; an RPC library bridging the Linux side and the MCU. Arduino App Lab composes apps from reusable "Bricks".
- **Also [report]:** Edge Impulse integration for custom on-device models (Arduino blog, March 2026). The docs pages fetched did not confirm AI brick details: [unverified].
- **Gotcha:** needs the board in hand; high effort in a 3-day window.
- **Good fits:** a physical, sensor-driven helper for a friend (camera, microphone, motion) with on-device inference.

### Backboard · $100
- **What it offers [docs]:** one API and key for 17,000+ models (OpenAI, Anthropic, Google, X.ai, Cohere and others), stateful threads, a hybrid persistent memory system that extracts facts when `memory="Auto"` (shared across threads at the assistant level), built-in RAG over PDF and text, mid-conversation model switching, Python and JS/TS SDKs plus REST; $5 free credits for 30 days.
- **Open angle:** closed platform; it can route to open models [report]. Data leaves the device.
- **Good fits:** companions and tutors that need long-term memory about one person; trade-off against a local-first "why open" story.

### ElevenLabs · $100
- **What it offers [docs]:** TTS (Eleven v4 most expressive, v4 Turbo about 100 ms, Flash v2.5 about 75 ms, 32 languages, Multilingual v2), a 10,000+ voice library and voice cloning; speech-to-text Scribe v2 (90+ languages, up to 32 speakers diarised, word timestamps), a realtime variant (about 150 ms) and a medical variant; ElevenAgents for voice agents (visual builder or code); music, sound effects, dubbing, voice isolation; Python and TypeScript SDKs; credits reset monthly and roll over up to two months, one credit per TTS character.
- **Also [report]:** agents accept a custom OpenAI-compatible LLM (for example llama.cpp through a tunnel); free 10k credits per month, no commercial use; promo available.
- **Gotcha:** closed and online, so it conflicts with an offline claim; make it an opt-in toggle if used. (First-hand: browser on-device speech recognition worked for push-to-talk without it, but needs desktop Chrome and a one-time speech-pack download.)
- **Good fits:** voice-first helpers for people who cannot type; storytelling and read-aloud tools.

### SerpApi · $100
- **What it offers [docs]:** real-time search results as JSON or Markdown with CAPTCHA solving and location targeting. APIs: Google (Search, Light Search, AI Mode, AI Overview, Ads, Autocomplete, Events, Finance, Flights, Hotels, Images, Jobs, Lens, Local, Maps, News, Patents, Play Store, Scholar, Shopping, Sports, Travel Explore, Trends, Videos) and others (Amazon, Apple App Store, Baidu, Bing, Brave, DuckDuckGo, eBay, Facebook, Home Depot, Instagram, Naver, OpenTable, Tripadvisor, Walmart, Yahoo, Yandex, Yelp, YouTube, Zillow). Free: 250 searches per month, 50 per hour; paid from $25 per month; ZeroTrace (no data retention) mode; SOC 2 Type II and ISO 27001.
- **Not stated on the pages [unverified]:** SDK languages and MCP integrations.
- **Good fits:** grounding a local model with current facts (prices, local businesses, flights, jobs); online by nature.

### MongoDB Atlas · $100
- **What it offers [docs]:** Atlas Vector Search (ANN with HNSW, or exact ENN) next to your documents, with pre-filtering, hybrid search combined with full-text, automated embedding using Voyage AI models or bring-your-own embeddings, up to 8192 dimensions, drivers for JavaScript, Python, Java, Go, C#, Ruby and more; works on Atlas, self-managed and local Atlas deployments via the Atlas CLI (exact command not confirmed).
- **Unclear [unverified]:** vector index limits on the free M0 cluster.
- **Good fits:** flexible-schema data with semantic search, RAG over a friend's notes; the free tier is hosted, so data leaves the device unless run locally.

### Tiger Data (Tiger Cloud) · $100
- **What it offers [docs]:** managed PostgreSQL with TimescaleDB: hypertables (automatic time partitioning), continuous aggregates, columnar compression (up to 95% storage reduction), retention policies, pgvector for embeddings, BM25 full-text via pg_textsearch. Free 30-day trial without a card; paid tiers shown from about $30 to $36 per month.
- **Also [report]:** pgvectorscale and pgai are open source; a free plan (beta) in one region, read-only at its limit. The docs pages did not mention pgvectorscale, pgai, an MCP server or agent-specific features [unverified].
- **Good fits:** time-series logs of one person's life (sleep, symptoms, spending, sensors) with dashboards and weekly aggregates; pairs naturally with TabPFN.

### Sentry Agent Tracing · $100
- **What it offers [docs]:** tracing for agent and workflow invocations, model generations, tool executions, token usage and latency, embeddings and RAG operations, HTTP requests and errors. The Mastra integration needs Sentry Node SDK v11+ and `@mastra/observability`; multi-turn chats are grouped automatically (thread ID becomes conversation ID); LLM inputs and outputs are sent by default and can be turned off per category with `dataCollection`; sensitive keys are filtered.
- **Also [report]:** auto-instruments the OpenAI SDK, LiteLLM, Pydantic AI and LangGraph in Python; free Developer plan around 5M spans and one user.
- **Gotcha:** prompts go to a hosted service: scrub PII, and it undercuts a "nothing leaves the device" claim. Tracing an OpenAI client pointed at a local endpoint is expected to work but is untested [report].
- **Good fits:** showing, with real traces, why a fine-tuned or smaller model behaved differently; debugging multi-step agents.

### Temporal · $100
- **What it offers [docs]:** durable execution: workflows orchestrate, activities do the non-deterministic work (model calls, I/O) with automatic retries; signals, human-in-the-loop approvals, continue-as-new for long conversations, streaming, MCP integration, sandboxes for agents with shell access; `temporalio-openai-agents` plugin turns OpenAI Agents SDK code into durable workflows; SDKs for Python, Go, Java and TypeScript; local dev server; Temporal Cloud free credits.
- **Also [report]:** server is MIT; `temporal server start-dev`; Cloud $150 for 90 days.
- **Gotcha:** workflow code must be deterministic (no direct I/O, randomness or clock); model calls must be activities.
- **Good fits:** long-running or scheduled agents that must not lose state (reminders, multi-day processes, approvals).

### Entire · $100 · dropped
- **What it offers [docs]:** a CLI that records agent sessions as checkpoints linked to git commits (prompts, transcripts, file changes), so any change can be traced to the session that made it. `entire enable --yes --agent <name>` inside a repo; commands include `entire blame` / `entire why`, `entire session resume`, `entire review` / `recap`, `entire search`; mirrors sync to GitHub across US, EU, India and Australia regions. Agents named in the docs: Codex, Claude Code, Antigravity; the report also lists OpenCode, Gemini and Copilot CLI. CLI is MIT [report]. Secret redaction not covered on the page fetched: scrub transcripts yourself.
- **Why we dropped it:** workload. We used DevRelay's agent-session tool instead (curated session embedded in the post).
- **Good fits:** a "process" angle for the post; it must be shown to matter, not just listed.

### GitHub Copilot · $100
- **What it offers [docs]:** in VS Code, bring-your-own-key language models without needing a Copilot plan; the Ollama provider is replaced by the official Ollama extension; a Custom Endpoint provider speaks Chat Completions, Responses or the Anthropic Messages API (self-hosted models, gateways); agent mode with tools for models that support tool calling, custom instructions, prompt files and MCP servers work with local models.
- **Needs the Copilot service [docs]:** semantic search, inline code suggestions and embedding-dependent features.
- **Good fits:** using Copilot as the build tool around an open model (say how it mattered); weak as a product feature.

## Pairing recipes seen in this list

- **Local-first assistant (what we built):** Gemma via Ollama + Mastra workflow + local SQLite/LibSQL + plain-code rules. All open; add Sentry only if "data stays local" is not the claim.
- **Traced agent:** Mastra + `@mastra/observability` + Sentry; compare base and tuned model behaviour with real traces.
- **Personalised voice or style:** Tinker fine-tune to a PEFT adapter, serve locally (test serving first), Mastra agent with tools.
- **Small-data predictor:** TabPFN on a friend's spreadsheet + Tiger Data for the log + a small Gemma for natural-language input and explanations.
- **Weak machine fallback:** local-first design with DigitalOcean serverless inference as an opt-in fallback.
- **Durable agent:** Temporal workflow whose activities call a local or hosted open model; human approval as a signal.
- **Grounded answers:** local model + SerpApi for current facts (online by design).
- **Memory-heavy companion:** Backboard memory/RAG with an open model routed through it (data leaves the device).

## Questions to ask during ideation

1. Who is the one real person, and can the demo run on **their** hardware? (First-hand: this decided the model and the whole latency budget; test the smallest candidate model on their machine on day one.)
2. Which claim is the "why open" answer (offline, private, swappable, tuned, free to run), and does every chosen partner support or contradict it?
3. Which partners does the code **really** use? Entering a category means a meaningful use, and the post must say which parts are not open.
4. What can be plain code instead of a model call? (It made small CPU-only models workable and numbers trustworthy.)
5. Is there a credit or promo worth claiming? Ask the author before claiming; none were claimed in the Weekend challenge.
6. What breaks without internet, and is each such partner an opt-in toggle?

## Unverified or conflicting items

- Hacktoberfest promo amounts for every partner; DigitalOcean's Hacktoberfest credit; Copilot Free limits; Atlas Vector Search limits on M0 and the exact local-deployment command; Tiger Data free-plan storage and whether pgai, pgvectorscale and an MCP server are offered; Render GPU availability; whether Tinker adapters (Qwen3.5) can be served in llama.cpp or LM Studio; AI brick and Edge Impulse details for the UNO Q; SerpApi SDK languages and MCP support; Ollama audio input for Gemma 4; TabPFN CPU limits (report: about 5k rows; docs: GPU recommended past 1,000 rows); Mastra's Node requirement (docs say 22.18+, package engines say 22.13+).
- Several docs summaries above came from page excerpts; if an idea depends on a detail, open the partner's docs and confirm it.

## Sources

Fetched 2026-10-05: https://render.com/docs/free · https://docs.priorlabs.ai/quickstart · https://tinker-docs.thinkingmachines.ai · https://docs.arduino.cc/hardware/uno-q/ · https://docs.arduino.cc/software/app-lab/ · https://docs.digitalocean.com/products/gradient-ai-platform/ · https://ai.google.dev/gemma/docs/releases · https://ollama.com/library/gemma4 · https://docs.backboard.io/faq · https://elevenlabs.io/docs/overview · https://docs.entire.io/platforms/cli · https://code.visualstudio.com/docs/copilot/customization/language-models · https://mastra.ai/docs · https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/ · https://serpapi.com and /pricing · https://docs.sentry.io/platforms/javascript/guides/nextjs/agent-tracing/mastra/ · https://docs.temporal.io/develop/python/integrations/openai-agents · https://www.tigerdata.com/pricing and /docs.
Earlier report (2026-10-04): `challenges/01-weekend-build-for-a-friend/PARTNER-REPORT.md` and its source list. Challenge rules: DEV event 78 `full_details` (fetched 2026-10-05). First-hand notes: `challenges/01-weekend-build-for-a-friend/docs/CHALLENGE-MEMORY.md`.
