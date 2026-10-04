# Phone feasibility spike: Gemma 4 E2B in the mobile browser

**Date:** 2026-10-04 · **Outcome:** not viable on the test phone → v1 is laptop-only.

## Question
The friend prefers to use the coach on his phone. Can Gemma 4 E2B (Apache-2.0, 2.0 GB `gemma-4-E2B-it-web.litertlm`) run on-device in a phone browser, with usable speed and offline?

## Method
A throwaway test page (`spike.html`, `src/spike/main.ts`), served from the laptop over HTTPS on the local network with a self-signed certificate (WebGPU needs a secure context). Steps run in order on the phone:

1. Device check: secure context, WebGPU adapter and the `shader-f16` / `subgroups` features, storage quota, on-device speech recognition.
2. Download the model once into Cache Storage.
3. Load the LiteRT-LM WASM runtime (self-hosted from the laptop, not a CDN).
4. Create the engine from the cached copy.
5. With Wi-Fi and mobile data off, run 10 symptom-classification utterances (8 touring-car symptoms, 2 out-of-scope) and record JSON validity, accuracy, time to first token and decode speed.

Desktop baseline for the harness (Chromium 152, Apple Silicon): WebGPU with `shader-f16` and `subgroups` present, runtime loads from the self-hosted files with no CDN request. On-device speech recognition reported "unavailable" in that embedded browser.

## Result
- The model downloaded on the phone.
- Steps 4 and 5 **lagged and ran too slowly to be usable** on the phone (reported by the tester).
- No numeric report was captured, so no timings or accuracy are claimed.
- **TODO for the write-up:** record the phone model and OS, and the browser used. Do not state them until confirmed.

## Decision
Stay with a consumer laptop (the friend also has one that runs a Gemma E2B/E4B). The phone is not a v1 target; the post says so plainly, with what was and wasn't measured.

## What this unlocks
With the model off the phone, the laptop can run a heavier stack: a local runtime such as Ollama (already supports JSON-schema output), an agent framework such as Mastra, and a proper local store for the field knowledge.

The agent session that produced this spike is saved privately on DEV (id 504); make it public from DEV before embedding it in the post.
