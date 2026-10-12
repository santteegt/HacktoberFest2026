# Running the Idea Leash stack

Two machines are involved: the **Mac** (the host) and a **Lume macOS VM** (`leash-hermes`) that holds the Hermes agent. This folder starts, supervises and checks both. Nothing here needs `sudo`; everything is per-user launchd.

## What runs where

| Component | Where | Started by | Notes |
| --- | --- | --- | --- |
| **Ollama** + the open model `leash-gemma4-12b` (Gemma 4 12B, 64K context) | Mac | Ollama app (login item) | Loopback only. The only place the language model runs. |
| **whisper.cpp** (Whisper large-v3-turbo, Metal) | Mac | called by the tool server | Podcast ingest and Telegram voice notes. |
| **Piper TTS**, **ffmpeg**, **yt-dlp**, **graphify** | Mac | called by the tool server | Spoken questions, audio download, transcription pipeline. |
| **Leash tool server** (`src/leash/server.py`, 127.0.0.1:8787) | Mac | `com.leash.server` LaunchAgent | Ingest, quiz, grading, ideas, search (SerpApi key stays here), transcribe. Writes the second-brain wiki. |
| **Second-brain vault** (OKF wiki), episodes, sessions | Mac | n/a | Files under `second-brain/` (or the vault path chosen at install) and `data/`. All gitignored. |
| **SSH reverse tunnel** | Mac, into the VM | `com.leash.tunnel` LaunchAgent | VM `127.0.0.1:11434` is Ollama, VM `127.0.0.1:8787` is the tool server. |
| **Lume VM** `leash-hermes` (macOS, 4 CPU, 8 GB) | Mac | `com.leash.vm` LaunchAgent (checks every 2 min) | Exclusive to this project. |
| **Hermes gateway** (Telegram, profile `leash`) | VM | Hermes' own launchd service (`ai.hermes.gateway`) | One gateway per host serves the profile. |
| **Hermes agent** with `SOUL.md`, `leash-tools` skill, `leashctl` | VM | the gateway | Decides which tool to call; contains no model weights. |
| **Phone app** (`app/`, an installable web page) | served by the tool server at `/app/`, reached over Tailscale HTTPS | by the tool server | Walk recording, voice notes, offline queue, medals. Data lives on the phone until the Mac is reachable. |
| **Old phone walk test page** (`phone-test/`) | Vercel copy; local copy removed from service | n/a | Kept only for its recorded results. |
| **Tailscale** | Mac, phone | Tailscale app | Private HTTPS to the Mac. |

What does not exist anywhere in this stack: a hosted model API. The agent's chat turns go to the local Ollama (checked in Ollama's request log, 2026-10-09).

```
phone (Telegram) --> Telegram servers --> [VM] Hermes gateway --> Hermes agent (SOUL + skill)
                                                     |  leashctl over the tunnel
                                                     v
                              [Mac] Leash server --> Ollama (Gemma 12B), whisper.cpp, Piper, vault
```

## Install

On the Mac, from this challenge folder:

```bash
ops/leash-stack install --vault "$PWD/data/test-vault"
```

Leave `--vault` out to use `second-brain/` if it exists, else the test vault (it prints which). The command writes three LaunchAgents into `~/Library/LaunchAgents` and starts them: `com.leash.vm`, `com.leash.server`, `com.leash.tunnel`.

Then install the gateway service inside the VM (once, or after changing Hermes):

```bash
ops/leash-stack gateway-install
```

Check everything:

```bash
ops/leash-stack status
```

Expected: Ollama and its API answering, the three agents loaded, the server answering, the VM running, `tunnel-ollama:ok`, `tunnel-server:ok`, and the profile `leash` "served by the default multiplexer".

Other commands: `restart [server|tunnel|vm]`, `logs [server|tunnel|vm|gateway]`, `uninstall`.

## Phone app

The app is a web page served by the tool server and reached through Tailscale (private HTTPS, tailnet devices only).

1. Turn **Tailscale on** on the Mac and on the phone.
2. `ops/leash-stack phone-serve` publishes `127.0.0.1:8787` on your tailnet name (`tailscale serve`). This replaces whatever was served on port 443 before (the old walk-test page).
3. `ops/leash-stack pair` prints a QR code in the terminal. Scan it with the phone camera: it opens the app and hands it the token, which lives in the address *fragment* (never sent to the server) and is removed from the address bar. The token is never printed as text.
4. In Chrome, choose "Install app" or "Add to Home screen" (optional), and allow **location and microphone while visiting the site**, not "this time only".

What the app does on a walk (from the four recorded walks on 2026-10-09, see `docs/CHALLENGE-MEMORY.md`): a web page gets **no GPS while it is hidden**, so the screen stays on behind a black cover, the wake lock is held, and the stop control needs a 3 second hold. If the page is interrupted anyway it keeps the fixes it has, says how long it could not track, and picks the walk back up (also after a reload). Everything is stored on the phone first and sent to the Mac when it can reach it.

## Prerequisites

- `.env` in the challenge folder with `LEASH_UPLOAD_TOKEN` (see `.env.example`). The server refuses to start without it.
- The agent profile deployed to the VM (`agent/README.md`, step 4).
- SSH alias `leash-hermes` in `~/.ssh/config` (key-based, no password).
- macOS **Local Network** access allowed for the terminal you run `ops/leash-stack status` from. The LaunchAgents themselves reached the VM without any extra setting on this Mac (tested 2026-10-09).

## After a restart or a sleep

| Event | What happens |
| --- | --- |
| Mac sleeps and wakes | The bot is offline while the Mac sleeps. On wake the tunnel's SSH connection is dead; `com.leash.tunnel` is designed to notice (keepalives), restart, free stale forwards in the VM and reconnect, and the gateway reconnects to Telegram by itself (it did after the host slept on 2026-10-09, per its log). The full sleep/wake path of the new services has not been tested yet. |
| Mac reboots | The three LaunchAgents start at login. `com.leash.vm` starts the VM; the tunnel waits for the VM's SSH. |
| VM restarts | The gateway service starts when user `hermes` logs in. **Automatic login is enabled** for `hermes` in the VM (checked 2026-10-10: `autoLoginUser` is `hermes`), so the service should come back by itself after a VM reboot. A reboot has not been tested yet. Without automatic login a reboot leaves the bot down until someone logs in on the VM's screen. |
| Tool server crashes | launchd restarts it within 10 seconds. |

To keep the bot answering while you are away from the Mac, stop the Mac from sleeping on power (System Settings > Battery > Options > "Prevent automatic sleeping on power adapter when the display is off"), or run `caffeinate -s` in a terminal. This is a choice for you; the scripts do not change power settings.

## Files

| File | Purpose |
| --- | --- |
| `leash-stack` | install, uninstall, status, restart, logs, gateway-install |
| `vm-up.sh` | starts the VM if it is not running (run by `com.leash.vm`) |
| `tunnel.sh` | waits for the VM's SSH, frees stale forwards, opens the reverse tunnel |
| `vm-run.sh` | runs one command in the VM through a login shell |

Logs go to `data/logs/{server,tunnel,vm}.out`; the gateway logs inside the VM at `~/.hermes/logs/gateway.log` (`ops/leash-stack logs gateway`).

## Security notes

- The tool server and Ollama listen on `127.0.0.1` only. The VM sees them only through the tunnel. Every server route except `/health` needs the bearer token.
- The tunnel is outbound from the Mac into the VM. The VM has no way to open a shell on the Mac.
- The SerpApi key and the vault never leave the Mac; the VM holds only the Telegram bot token, the allowed user id and the tool-server token.
