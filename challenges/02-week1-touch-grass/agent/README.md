# leash: the Hermes agent for Idea Leash

This folder is a [Hermes profile distribution](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions): the agent's persona, model config and (later) cron jobs and MCP connections, plus a script that installs it on any Hermes instance together with this project's skills.

| File | What it is |
| --- | --- |
| `distribution.yaml` | manifest: name, version, env vars the agent can use (values are never shipped) |
| `config.yaml` | model: open-weight Gemma through Ollama (`provider: custom`, `base_url`) |
| `SOUL.md` | persona, what it does, and the rules it keeps (version 1) |
| `Modelfile.leash` | `leash-gemma4-12b`: `gemma4:12b-it-qat` with the 64K context Hermes needs |
| `setup-profile.sh` | stages this folder plus `../skills/*` and runs `hermes profile install` |
| `cron/jobs.json`, `mcp.json` | not written yet |

## Set it up

You need Hermes (`scripts/vm/install-hermes.sh` installs it inside the Lume VM), the project skills next to this folder, and a model server.

1. **Model on the host.** `ollama create leash-gemma4-12b -f agent/Modelfile.leash`
2. **Let the VM reach the Mac's services without exposing them.** From the Mac, keep this running: `ssh -N -R 127.0.0.1:11434:127.0.0.1:11434 -R 127.0.0.1:8787:127.0.0.1:8787 leash-hermes`. Inside the VM, Ollama then answers on `127.0.0.1:11434` and the Leash tool server on `127.0.0.1:8787`.
   Start the tool server on the Mac with `PYTHONPATH=src .venv/bin/python -m leash.server` (needs `LEASH_UPLOAD_TOKEN` in `.env`).
3. **Copy the project to the VM.** `rsync -a --exclude evals agent skills leash-hermes:leash/`
4. **Install the profile (inside the VM).** `bash ~/leash/agent/setup-profile.sh`
   Optional: `--env-file path/to/.env` copies only the keys named in `distribution.yaml` into the profile's `.env`. Keep tokens out of the VM until you need the Telegram gateway.
5. **Telegram.** Put `TELEGRAM_BOT_TOKEN` (from @BotFather) and `TELEGRAM_ALLOWED_USERS` (your numeric id, from @userinfobot) in the repo `.env`, then `agent/setup-profile.sh --env-file ... --reset-config` copies only those keys into the profile. Hermes runs **one gateway per host** that serves every profile, so start it from the default profile (`hermes gateway run` in a terminal, or `hermes gateway install` for a launchd service; `../ops/leash-stack gateway-install` does the latter and `../ops/README.md` covers the rest of the stack); `hermes gateway list` should show `leash` as "served by the default multiplexer". Hermes asks once to install its optional `telegram` library; answer yes (`echo y | hermes gateway run` when scripting). Voice notes are transcribed on the Mac: `stt.providers.mac_whisper` in config.yaml runs `leashctl transcribe`, which sends the audio through the tunnel to whisper.cpp on the host (faster-whisper is not installed in the VM).
6. **Try it.** `leash chat` or `hermes -p leash chat`. For a one-shot test: `hermes -p leash chat -Q --query-file prompt.txt -t terminal,file,skills`.

Re-running `setup-profile.sh` updates the profile (user data such as memories and sessions is kept).

## Using the skills somewhere else

The skills live in `../skills/`. `scripts/install-skills.sh --target agents` links them for Claude Code and similar tools; `--target hermes --profile leash` copies them into a profile on the same machine.

## Status

Installed and tested once on Hermes v0.21.6 in the Lume VM: the agent found `podcast-quiz`, wrote a quiz, ran the verifier and the shuffle script (3 min 14 s, `--yolo` approvals, tools limited to terminal, file and skills). Behavior v1 is written (SOUL.md plus the `leash-tools` skill and its `leashctl` command). The Telegram gateway connects and serves the profile. Cron jobs are still to do.

Measured with a 12B model (see docs/CHALLENGE-MEMORY.md): about 8 of 10 test messages made the right tool call on the first try, driving and cycling requests were refused 5 of 5 times, and one search phrasing still got a made-up "I searched" reply about one time in three. The server log (`data/logs/server.log`) is the ground truth for what was really called.
