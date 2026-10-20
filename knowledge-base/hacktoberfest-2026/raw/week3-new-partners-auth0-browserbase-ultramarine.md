# Week 3 new partner categories: Auth0 for AI Agents, Browserbase, Ultramarine

Researched 2026-10-20 for the Week 3 (Slow and Steady) challenge, DEV event 81. Three partner categories ($100 each) are new compared with Week 2. No sponsor Agent Skills were published for the Week 3 MLH event.

## Auth0 for AI Agents

- Category text: "sign users in to an agent, call tools on a user's behalf with Token Vault, ask a person to approve a risky action before the agent takes it, or limit what a RAG pipeline can retrieve with fine-grained authorization." Docs: https://auth0.com/ai/docs
- Four capabilities: user login (OIDC, Universal Login, account linking); Token Vault (agent gets Google / Microsoft / GitHub / Slack / Box / custom OIDC tokens, Auth0 refreshes them); asynchronous authorization (CIBA backchannel + Rich Authorization Requests, push approval via Guardian; email/SMS "coming soon"); FGA for RAG (OpenFGA relationship checks on retrieved documents).
- Framework SDKs: LangChain, LlamaIndex, Vercel AI SDK, Genkit, Cloudflare Agents and MCP servers.
- Free plan: 25,000 MAU, no card; includes 2 Token Vault connected apps and async authorization (per Auth0's DEV post on GA).
- Fit for an open-source AI project: it is identity plumbing, not AI. Honest use is "agent acts on my Google/GitHub account and asks me before anything risky", with the open model doing the reasoning.

## Browserbase (Stagehand)

- Category text: "Give your agent a real browser: drive a live site end to end using Stagehand's SDK, pull the context an open-weight model reasons over, or turn a one-off agent run into a repeatable workflow." Docs: https://docs.stagehand.dev/v4/first-steps/quickstart
- Stagehand v4 is MIT, TypeScript + Python (+ Go). Primitives act / extract / observe, every one needs JSON-schema structured output from the model.
- Runs against local Chrome (`localBrowser.launch()`) without a Browserbase key; then you must pass a model with your own provider key or a custom LLM callback. Browserbase cloud (`browserbase.launch()`) adds stealth, proxies, session recordings and the Model Gateway (auto model selection), which only works on Browserbase-hosted browsers.
- Known providers: OpenAI, Anthropic, Google, Groq, Cerebras. Ollama is not a first-class provider in v4; it goes through a custom callback (older docs showed an OpenAI-compatible client at http://localhost:11434/v1) or the Vercel AI SDK route (TS only). Docs warn small Ollama models give inconsistent structured output and are not recommended.
- Fit: strong for "do the dreaded web chore for me" (forms, portals, scraping into a local model's context). The open-weight model is a real risk here: plan a feasibility check of Gemma 4 through a callback on the first day, and keep a Groq/Gemma hosted fallback.

## Ultramarine 1 Flash (Paper Instruments)

- Category text: "Put Ultramarine ... to work on something real: research, analysis, drafting, or an agent that reasons over a pile of documents. Call it with the OpenAI or Anthropic SDKs, and say what your run actually cost. Claim $5 of free credit at hacktoberfest.com/my/promos." Docs: https://docs.paperinstruments.com/docs
- Released 2026-10-14. Post-trained from GLM-5.3 Flash (Z.ai) for knowledge work: memos, decks, spreadsheets, document reasoning; open-source `paper-docx` / `paper-pptx` / `paper-xlsx` packages and MIT "Feather" training code. 131k training context, up to 250 agent turns.
- API: model `ultramarine-1-flash`, base URL https://api.paperinstruments.com/v1 (OpenAI SDK) or https://api.paperinstruments.com (Anthropic SDK). Chat Completions, Responses and Messages; streaming, function tools, JSON schema. Reasoning mandatory: low / high / max (no medium), default max; 32,768 output tokens including reasoning. Recommended temperature 1, top_p 0.95. No vision training; Responses rejects images, Messages rejects PDF blocks. HTTP 200 can carry an incomplete result; check finish_reason.
- Pricing: $0.15/M input, $0.03/M cached input, $0.50/M output (reasoning billed as output). Vendor claims $0.13 per task on its own suite; unverified.
- Weights: "coming soon", promised about two weeks after launch; not on Hugging Face as of 2026-10-15. Until then it is a hosted, paid, closed model; do not call it open-weight or local. Re-check before publishing.
- Fit: a document-pile reasoner ("read my inbox / PDFs and draft the reply") where the post reports the exact cost; must sit next to a real open core (Gemma local, etc.).

## Takeaways for Week 3 ideation

- All three are additive, not core. The open-source core still has to be a local or open-weight model plus an open harness.
- Browserbase is the one that unlocks new lazy-theme ideas (web chores). Auth0 is the one that makes a "do things on my accounts" agent honest. Ultramarine is a cheap second brain for document-heavy drafting with a cost figure to report.
