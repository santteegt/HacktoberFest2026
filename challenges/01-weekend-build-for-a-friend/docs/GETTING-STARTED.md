# Getting started

RC Pit Companion runs on your laptop. This page gets it running, then shows how to use it at the pit table. About 15 minutes the first time, with internet needed once for downloads. (The same guide as an HTML page, with a model switch that rewrites the commands: [getting-started.html](getting-started.html), download it and open it in a browser.)

## 1. Before you start

- A Mac on macOS 14 or newer.
- Node 22.13 or newer. Check with `node -v`; install from nodejs.org if it is older or missing.
- [Ollama](https://ollama.com/download) installed and open (its icon shows in the menu bar).
- Git, or use the green Code button on GitHub and download the ZIP.

## 2. Install

Pick the model first. The small one (E2B, about 4.3 GB) is the safe choice for an older Intel laptop. The larger one (E4B, about 6.1 GB) gives nicer wording if the laptop is fast.

```bash
git clone https://github.com/santteegt/HacktoberFest2026.git
cd HacktoberFest2026/challenges/01-weekend-build-for-a-friend
ollama pull gemma4:e2b-it-qat
npm ci
```

Then tell the app which model you pulled. This edits the `.env` file:

```bash
cp .env.example .env
sed -i '' 's|^OLLAMA_MODEL=.*|OLLAMA_MODEL=gemma4:e2b-it-qat|' .env
```

(For E4B use `gemma4:e4b-it-qat` in both places.) `ollama pull` is the slow part. `npm ci` installs packages and builds the offline notes index.

## 3. Start it

```bash
npm start
```

Wait for the line saying the server is running, then open <http://localhost:8787> in Chrome. Leave the terminal open while you use the app; press Ctrl+C in it to stop.

The first launch asks three things: which car (pick the Yokomo BD12), the first practice session (track name, surface, grip, bumpy or not, temperature if you know it), and a model check that tells you if Ollama is not running or the model is not pulled.

To look around with example data first, run `npm run seed:demo`. Everything it adds is labelled DEMO.

## 4. A practice day

1. **Coach:** tap a symptom chip, or type or say how the car feels.
2. **Apply:** it suggests one change with what to expect. Accept it, then make the change on the car.
3. **Drive** the 3 to 5 laps it asks for, on the same corners.
4. **Rate:** Better, Same or Worse. The change is saved in the Session log.
5. **Save setup:** if it was better, save the setup with today's track conditions.
6. **Race day:** enter the conditions and see your saved setups ranked by how close they are.

Good to know:

- It changes one thing at a time on purpose. If you change two, you cannot tell which one helped.
- Every answer lists the notes it came from; tap a citation to read the source.
- Questions outside the notes get a refusal. That is by design.
- Chips and typed keywords work even if Ollama is off. The model only improves how it understands and words things.
- Most adjustment rows are marked draft. Treat those as a starting point.

## 5. Voice

Push-to-talk works in desktop Chrome when it can recognise speech on the device.

1. Open **Settings**, then the voice section. Voice input should read **On this computer (Chrome on-device)**. If it says **Off**, pick that option.
2. If it says the speech pack is missing, press **Install speech pack** (needs internet once).
3. Press **Test voice input** and say a sentence. If nothing happens, use chips or type; nothing else depends on voice.

## 6. Try it with Wi-Fi off

Once the model is pulled and `npm start` is running, turn Wi-Fi off and do one coach turn. It should still answer. For a raw speed reading of the model on your laptop:

```bash
ollama run gemma4:e2b-it-qat --verbose
```

Ask it one short thing. At the end it prints "prompt eval rate" and "eval rate" in tokens per second.

## 7. If something goes wrong

- **"Ollama not reachable":** open the Ollama app so its menu bar icon appears, then reload. Chips and typed keywords still work without it.
- **The model "is not pulled":** run the pull command from step 2 for the model you chose, and check the name in `.env` matches (`ollama list` shows what you have).
- **`npm start` stops with a message about `kb.json`:** run `npm run kb:build`, then start again.
- **The port is already in use:** another copy is still running. Close its terminal, or set `PORT=8790` in `.env` and open that address.
- **Answers are slow:** on an older CPU-only laptop the model writes only a few words a second (about 9 tokens/s on the one laptop measured), so a full answer can take 15 to 25 seconds, and the first one after starting is slowest. Use the E2B model, close other heavy apps, and try **Settings, Coach phrasing (LLM explanations)**: switch it off and the coach shows its plain template text instead. The advice and numbers are the same, a chip answers right away, and a typed sentence only waits for the model to understand it.
- **It misread what I said:** tap the right chip instead, and tell the author the exact words you used.

Your setups and sessions live in one file on this laptop, in the project's `var` folder. Nothing is sent anywhere. Settings has an export button for a JSON backup. To start from scratch: Settings, Data, type `RESET`; or stop the app and delete the `var` folder.
