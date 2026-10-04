# Partner report and idea shortlist: Build for a Friend

**Date:** 2026-10-04 · **Deadline:** Oct 5, 2026 06:59 UTC · Rules: [CHALLENGE.md](CHALLENGE.md)

**TL;DR**
1. Easiest strong fits with open AI at the core: **Gemma** (Apache 2.0, runs local via Ollama), **TabPFN** (open weights, CPU-OK on small data), **Tinker** (hosted LoRA training of open models, adapters downloadable).
2. Most $100 partners (ElevenLabs, Backboard, SerpApi, Atlas, Sentry) are closed/hosted services. Use them *around* an open model and say so honestly in the post.
3. Pick: **Idea 1 (Carta, Gemma local)**. Lowest risk, no data dependency, clearest "why open" story. Reserve 2-3 h for the post.

## Partner cheat sheet

| Partner | Prize tier | What it gives you | Open angle | Effort | Gotcha / credits |
| --- | --- | --- | --- | --- | --- |
| Render | Featured $200 | PaaS: web services, Postgres, Key Value, Workflows (beta) for agent jobs | Closed host; runs your OSS app. No GPU offering found | Low | Free web svc spins down after 15 min idle; free Postgres expires in 30 days. Promo: yes |
| TabPFN (Prior Labs) | Featured $200 | Tabular foundation model: fit/predict on small tables, no tuning | Code Apache 2.0; v2.5+ weights non-commercial; local `pip install tabpfn` | Low-Med | Accept license / `TABPFN_TOKEN`; CPU OK to ~5k rows. API free tier has daily limits |
| Tinker (Thinking Machines) | Featured $200 | Hosted LoRA fine-tuning + sampling of open-weight models | Trains open weights (Qwen3.5-4B/9B, Qwen3-8B, gpt-oss-20B, Nemotron...); export PEFT/HF | Med | No Gemma; LoRA only. Qwen3.5-4B ~$0.74/M train tokens. Promo: yes |
| Arduino | Featured $200 | UNO Q (Debian MPU + MCU), App Lab "bricks", Edge Impulse custom models | Open hardware/tooling; on-device AI | High | Needs a board in hand today |
| DigitalOcean | Featured $200 | Serverless inference, agent platform, GPU Droplets | Hosts open weights: gemma-4-31B-it, gpt-oss, Llama, Qwen, Mistral | Low-Med | Pricing page shows $5/90-day new-account credit; Hacktoberfest promo unverified |
| Gemma | Featured $200 | Gemma 4: E2B, E4B, 12B, 26B A4B, 31B; vision; audio on small sizes | Apache 2.0 open weights; `ollama run gemma4:e4b` | Low | e4b ~7-10 GB download; likely most crowded category (my guess) |
| Backboard | $100 | One API: memory, RAG, threads, 17k+ models | Closed platform; routes to open models via Featherless/OpenRouter | Low | $5 credits / 30 days + promo. Data leaves device |
| ElevenLabs | $100 | TTS, STT, voice agents | Closed; Agents accept a custom OpenAI-compatible LLM (e.g. llama.cpp via tunnel) | Low | Free 10k credits/mo, no commercial use. Promo: yes |
| Entire | $100 | CLI that links agent sessions to git commits as checkpoints | CLI is MIT; supports OpenCode, Codex, Claude Code, Gemini, Copilot CLI | Low | Dev-process tool: post must show why it mattered; scrub transcripts |
| GitHub Copilot | $100 | Coding assistant | Closed; VS Code chat can use local models (Ollama extension) offline | Low | Completions/embeddings still need Copilot service; Free limits unverified |
| Mastra | $100 | TS agents, workflows, memory, RAG, evals | Apache 2.0 core; any OpenAI-compatible local endpoint | Med | TypeScript only; `npm create mastra@latest` |
| MongoDB Atlas | $100 | Document DB + Vector Search | Hosted; local Atlas via CLI; bring open embeddings | Low-Med | M0 free = 0.5 GB; vector index limits on M0 unverified |
| SerpApi | $100 | Search results as JSON (agent web tool) | Closed API; grounds an open model | Low | Free: 250 searches/mo, 50/h |
| Sentry Agent Tracing | $100 | Traces agent runs, tool calls, tokens | Hosted; auto-instruments OpenAI SDK, LiteLLM, Pydantic AI, LangGraph; `@mastra/sentry` | Low | Free Dev plan: 5M spans, 1 user. Prompts go to Sentry, scrub PII |
| Temporal | $100 | Durable workflows; agent loops survive crashes | Server MIT; `temporal server start-dev` local; OpenAI Agents SDK / Pydantic AI plugins | Med | Determinism rules; model calls must be Activities. Cloud $150 / 90 days |
| Tiger Data | $100 | Managed Postgres + TimescaleDB, pgvector | TimescaleDB, pgvectorscale, pgai are open source | Low-Med | Free plan (beta), us-east-1, read-only at limit; 30-day trial, no card |

## Ideas

### Idea 1: Carta, an offline mail explainer for Mom
- **Friend/problem:** My mom reads Spanish, but insurance, school and city letters arrive in dense English, and she waits days for me to explain them.
- **Open core:** Gemma 4 E4B (vision) via Ollama on her own laptop. Letters hold IDs, diagnoses and account numbers; nothing leaves the machine, no API bill, works without Wi-Fi.
- **Partners:** Gemma (strongest). ElevenLabs optional: reads only the *summary* aloud in a warm voice (weak fit: conflicts with offline, so make it a toggle). Entire to record the build sessions for the post.
- **Build plan:** (1) photo upload page plus prompt that returns JSON {what is it, deadline, amount, what to do} in Spanish, 3 h; (2) "Is this a scam?" check and calendar-ready deadline, 2 h. **Cut line:** MVP = step 1 plus local TTS. Nice-to-have: ElevenLabs voice, multi-page PDFs, history.
- **Risk:** OCR quality on phone photos of small print; test 5 real letters early.
- **Writing angle:** before/after of one real (redacted) letter and Mom's reaction. "Why open" is concrete: her data, her laptop.

### Idea 2: Sounds Like Sam, a reply drafter fine-tuned on a friend's own voice
- **Friend/problem:** Sam runs a one-person dog-walking business and spends every evening answering the same booking and price questions on WhatsApp.
- **Open core:** Qwen3.5-4B LoRA trained on Tinker from ~200 of Sam's past replies, downloaded and served locally. He owns the weights, can retrain, pays nothing per message.
- **Partners:** Tinker (strongest). Mastra agent with tools (price list, availability JSON) against the local OpenAI-compatible endpoint. Sentry Agent Tracing via `@mastra/sentry` to compare base vs fine-tuned drafts. Weak for Render.
- **Build plan:** data export and PII scrub 2 h; Tinker SFT run under 1 h; Mastra agent plus simple UI 3 h. **Cut line:** MVP = fine-tune plus side-by-side "base vs Sam-tuned" demo. Nice-to-have: tools, tracing dashboard.
- **Risk:** serving the adapter locally (Qwen3.5 support in llama.cpp/LM Studio unverified); fallback is Qwen3-8B or Tinker's sampler.
- **Writing angle:** blind test: Sam guesses which replies he wrote.

### Idea 3: Aura Log, a migraine pattern finder for a friend
- **Friend/problem:** Lucía logs sleep, coffee and migraines in a spreadsheet but cannot see which combinations precede a bad day.
- **Open core:** TabPFN run locally on her 40-200 rows (no training loop), plus Gemma 4 E2B to turn "slept 5h, 3 coffees" into a row and explain tomorrow's risk in plain words. Health data stays local.
- **Partners:** TabPFN (strongest, likely small pool). Tiger Data hypertable for the daily log and weekly aggregates (or local TimescaleDB). Render for a phone logging page (weak: privacy trade-off).
- **Build plan:** CSV import plus TabPFN predict 2 h; Gemma logging/explainer 2 h; Tiger Data storage 1.5 h. **Cut line:** MVP = CSV in, risk plus top factors out. Nice-to-have: Render page, weather join.
- **Risk:** too few rows for a real signal; non-commercial weight license. Frame as "notes for her doctor", not advice.
- **Writing angle:** what the model found (or honestly did not) in one real person's year.

## Recommendation and brainstorm questions

Build **Idea 1**. It needs no data handover, runs in one demo without credits, and puts the open model where it is unarguable: private documents on a laptop Mom controls. Its weakness is category competition in Gemma. If a friend can send a chat export or diary within the hour, Idea 2 (Tinker) or Idea 3 (TabPFN) likely face smaller pools.

1. Who is the real person, and can you reach them today for a 10-minute handover and a quote?
2. What machine will they use (OS, RAM, GPU)? That decides E2B vs E4B, or a DigitalOcean fallback.
3. Do you have real inputs right now (letters, chat export, spreadsheet), and may you show them redacted?
4. Python or TypeScript? Mastra pushes TS; Sentry/Temporal auto-instrumentation is broadest in Python.
5. Which one or two promo codes do you actually need (ElevenLabs, Tinker)? Claim only those.
6. Will you record sessions with Entire/DevRelay, and who checks transcripts for personal data before publishing?

## Sources

- https://ai.google.dev/gemma/docs/releases · https://ollama.com/library/gemma4
- https://tinker-docs.thinkingmachines.ai · https://tinker-docs.thinkingmachines.ai/tinker/models/models_and_pricing/index.md · https://tinker-docs.thinkingmachines.ai/cookbook/api-reference/weights/download/index.md
- https://docs.priorlabs.ai/quickstart · https://github.com/PriorLabs/TabPFN · https://priorlabs.ai/pricing
- https://render.com/docs/free · https://render.com/tutorials/deploy-ai-agents-on-render/deploy-the-workflow-agents
- https://docs.digitalocean.com/products/gradient-ai-platform/details/models/ · https://www.digitalocean.com/pricing
- https://docs.arduino.cc/hardware/uno-q/ · https://docs.arduino.cc/software/app-lab/ · https://blog.arduino.cc/2026/03/04/train-and-deploy-your-own-ai-models-in-arduino-app-lab-now-fully-integrated-with-edge-impulse/
- https://docs.backboard.io/faq
- https://elevenlabs.io/pricing · https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm
- https://docs.entire.io/platforms/cli · https://github.com/entireio/cli
- https://code.visualstudio.com/docs/copilot/customization/language-models
- https://github.com/mastra-ai/mastra · https://mastra.ai/docs/getting-started/model-providers
- https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/ · https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/
- https://serpapi.com/pricing
- https://docs.sentry.io/platforms/python/tracing/instrumentation/custom-instrumentation/ai-agents-module/ · https://docs.sentry.io/platforms/javascript/guides/nextjs/agent-tracing/mastra/ · https://sentry.io/pricing/
- https://github.com/temporalio/temporal · https://temporal.io/pricing · https://docs.temporal.io/develop/python/integrations/openai-agents
- https://www.tigerdata.com/pricing · https://www.tigerdata.com/docs/use-timescale/latest/services
- Challenge rules: DEV event 78 `full_details` (fetched 2026-10-04)

**Unverified:** Hacktoberfest promo amounts for any partner (not logged in); DigitalOcean Hacktoberfest credit; Copilot Free limits; Atlas Vector Search index limits on M0; Tiger Data free-plan storage size (a secondary source says 2 services x 750 MB); Render GPU availability; Qwen3.5 LoRA support in llama.cpp/LM Studio; Ollama audio input for Gemma 4; Sentry auto-tracing of an OpenAI client pointed at a local endpoint (expected, untested); relative crowding of categories.
