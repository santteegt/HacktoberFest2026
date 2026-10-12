---
title: "Idea Leash: an open-source walk buddy with a local model for a brain"
published: false
tags: devchallenge, hf26challenge
---

<!-- DRAFT v6 (v5: author's review applied: template order, architecture, short demo summary; fact-checked by the orchestrator. v6: the author edited the Code section and the Telegram sentence on DEV on 2026-10-11, synced here; architecture diagram redone with less text), 2026-10-11. Every fact checked against docs/CHALLENGE-MEMORY.md and README.md. Not staged, not published; the author decides. -->

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

Idea Leash is how I take a break from work and touch grass. I go out with my dog, or for an evening walk with a podcast in my ears, and I wanted those walks to leave something behind: what I heard, the ideas that show up while I'm moving, and a small reward for going out. It is for anyone who walks with a podcast and wants to keep some of it.

The AI runs on open models on my Mac: Gemma 4 12B through Ollama, the Hermes agent, and whisper.cpp for speech. On the phone I use two apps. The Leash app records the route and my voice, and Telegram is where I talk to the Leash agent.

The Leash agent is an ambient agent: it speaks first. When a podcast is ready, when a walk has been saved and when I answer a quiz question, the Mac messages me in Telegram without being asked, and I reply there. It can also bring back one concept and one older note from my wiki when I ask. I have not built scheduled nudges, so it speaks when something happened, not on a timer.

The loop:

1. Before the walk I send an episode link to a Telegram bot. The Mac transcribes it, writes notes into a markdown wiki (my second brain) and prepares a five question quiz. Every question quotes the transcript, and a script checks the quote.
2. I walk with the phone in my pocket and listen in my usual podcast player. The web app records the route, and one big button records a voice idea.
3. When I stop, the Mac sends one Telegram message: distance, time, my ideas, and the top links for any note that started with "search the web for...".
4. I say "quiz me". Four multiple choice questions arrive as Telegram buttons. A podcast competes with the street for my attention, so the fifth asks me to connect an idea from the episode to something I saw on the walk.
5. Sixteen badges reward kilometers, time with the dog, streaks, voice ideas and quiz results. Code computes them, not the model.

The theme asks for the screen to be the shortest part. On the walk I touch the phone only to start, to record a note and to stop. The screen does stay on behind a black cover, because in Chrome a hidden web page gets no GPS.

## Demo

{% embed https://youtu.be/ikb7P_XMQAw %}

A walkthrough of how I use the Leash app and its ambient agent to rest from work and touch grass, going out with my dog or out to exercise. Along the way it keeps a second brain of what I learned and the ideas I had, with the AI running on my Mac.

I pick the kind of walk (podcast, dog or plain), pocket the phone behind the black cover, and hold a corner for three seconds to stop.

![The Walk view of the Idea Leash app at phone width](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/02-week1-touch-grass/docs/screens/walk.png)

Afterwards the Activity view shows my totals, the streak and recent walks.

![The Activity view of the Idea Leash app at phone width, with walk totals and recent walks](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/02-week1-touch-grass/docs/screens/activity.png)

The Badges view shows what I have earned and how far I am from the next badge.

![The Badges view of the Idea Leash app at phone width, with earned and locked badges](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/02-week1-touch-grass/docs/screens/badges.png)

This is the Telegram message I've got from the agent after Sunday morning's offline dog walk:

```plaintext
Dog walk saved: 921 m in 24 min.
The phone could not track 2 min of it (screen off or another app in front).
2 voice ideas saved:
  - Remind me to check out the milestones of the project as we are back f…
  - Search on the web about libraries for 2D gaming and physics engine.
Searched "libraries for 2D gaming and physics engine":
  1. Most Popular C[++] Open-Source Physics Engines
     https://www.reddit.com/r/gamedev/comments/qu1y2y/most_popular_c_opensource_physics_engines/
  2. physics-engine · GitHub Topics
     https://github.com/topics/physics-engine
  3. Free 2D game engine library for teaching purposes
     https://www.facebook.com/groups/132728896890594/posts/2143324715830992/
```

Test walks in Cuenca, on my Redmi Note 11 with Chrome:

| Session (2026) | The number that matters | Result |
| --- | --- | --- |
| Four test walks, Oct 8 and 9 | page visible: no gap over 5 s between GPS fixes; page hidden: zero fixes | the screen stays on behind a black cover |
| First walk with the app, Oct 9, 35 min | 2,116 of 2,117 s tracked, 3.15 km | tracked with no gaps |
| Offline dog walk, Oct 10, 19 min, 3 voice notes | uploaded about 30 s after the phone was back online | notes transcribed, Telegram message followed |
| Podcast walk and quiz, Oct 10, 2.86 km | a 57 minute episode ready in 18 min; quiz 3 of 6 | the agent called a wrong answer right, so grades moved to the Mac |
| Dog walk with an interruption, Oct 11, 24 min | page hidden for 139 s | gap stated, walk saved, nothing lost |

On the podcast walk I listened to that episode, then took the quiz in Telegram when I got back.

<!-- TODO(author): the three screenshots above are the app rendered at phone width in a desktop browser with real data (docs/screens/README.md). Swap in phone screenshots with the same file names if you have them. -->

## Code

{% github santteegt/HacktoberFest2026 %}

The code, the setup steps and the dated log of everything can be found in the `challenges/02-week1-touch-grass` folder. MIT licensed.

## How I Built It

![Architecture diagram in three columns. Phone: the Leash app records route, voice notes and taps, with an offline queue, and reaches the Mac over Tailscale. Mac: a tool server that computes km, scores, badges and streaks, calls whisper.cpp, graphify, Piper and Gemma 4 on Ollama, and writes the wiki; a macOS VM run by Lume holds the Hermes agent and leashctl, linked to the Mac by an SSH tunnel. Internet: podcast host, SerpApi and Telegram. Numbered badges 1 to 6 mark the steps listed below](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/8c46836e6fd7042e354e2af8eff1d6ed3b0e560e/challenges/02-week1-touch-grass/docs/architecture.png)

The numbers in the diagram follow one loop:

1. A link I send in Telegram reaches the Hermes agent in a macOS VM. The agent runs `leashctl`, which calls the tool server on the Mac through an SSH reverse tunnel. The server fetches the audio from the podcast host, graphify transcribes it, Gemma writes the notes and the quiz, the notes go into the wiki, and Piper makes spoken versions of the questions (not used in the Telegram quiz yet).
2. The same tool server serves the phone app over Tailscale HTTPS, reachable only from my tailnet. A finished walk uploads its GPS track, and the Mac recomputes distance and time.
3. Voice clips travel with the walk. whisper.cpp transcribes each voice note (a 15 second clip in 0.95 s) and it is saved as an idea in the wiki. A note that starts with a search phrase becomes one SerpApi search.
4. Code builds the after-walk message, and the Mac sends it to Telegram.
5. "Quiz me" goes to the agent, which asks each multiple choice question as buttons.
6. Each answer goes back through `leashctl`. The Mac grades it and sends the grade itself.

The stack:

| Job | What runs it | License | Where |
| --- | --- | --- | --- |
| Language model (notes, quiz, grading wording, chat) | Gemma 4 12B, 4 bit QAT build, through Ollama | Apache 2.0 | my Mac |
| Agent in Telegram | Hermes Agent v0.21.6, one profile | MIT | a macOS VM on the Mac, run by Lume (MIT) |
| Speech to text for voice notes | whisper.cpp with Whisper large-v3-turbo | MIT | my Mac |
| Podcast transcripts | graphify with faster-whisper | Apache 2.0 / MIT | my Mac |
| Spoken versions of the quiz questions (made at ingest, not used in the Telegram quiz yet) | Piper, run as a separate process | GPL-3.0-or-later | my Mac |
| Tool server: walks, badges, quiz checks, messages | Python, standard library only | MIT (this project) | my Mac |
| Phone app | one HTML file, no framework | MIT (this project) | Chrome on Android |
| Phone to Mac link | Tailscale HTTPS, tailnet only | not open | phone and Mac |
| The second brain | an OKF markdown wiki | plain files I own | my Mac |

### The second brain is an OKF wiki

OKF is Google's Open Knowledge Format: a folder of markdown files with YAML front matter, where the one hard rule is that every page declares a `type`. An agent reads each source once and folds it into linked pages, with an index and an append-only log, so the wiki grows instead of searching the raw files again. It is not a database and has no embeddings, so anything that can read a file can read it.

In Idea Leash, each episode becomes a source page and a few concept pages that keep a verbatim quote, and each voice idea becomes a note page linked to the concepts it shares words with. The procedure comes from my repo's `okf-wiki` skill, committed before the challenge window opened (prior work), and the Mac's ingest code writes the same layout.

### Two agent skills

The agent's behavior lives in two skills in the repo's `skills/` folder. A skill is a `SKILL.md` of instructions plus scripts the agent can run.

- `podcast-quiz` turns a transcript into four multiple choice questions and one field-link question, and grades spoken answers afterwards. Its scripts check every question's quote against the transcript, the spoken length and the answer-length bias, and shuffle the answer positions.
- `leash-tools` tells the agent how to reach the Mac with one command, `leashctl`: `ingest`, `next`, `answer`, `idea`, `search`, `resurface`, `walks` and `audio`.

The method was the skill-creator workflow: write the skill, run it on three test transcripts with the local Gemma model, read the failures, change the skill, run again. It took four rounds. The checking script did more than the prose: with it the skill passed 27 of 27 checks, against 20 of 27 for a plain prompt.

Telegram taught me the second lesson. The 12B model did not follow a paragraph in a skill and wrote a question as plain text instead of calling the buttons tool. So the instruction moved into the tool's reply, in an `action` field the agent only has to follow. `agent/setup-profile.sh` installs the Hermes profile with both skills.

launchd services on the Mac keep the VM, the tool server and the tunnel running, and the Hermes gateway is a launchd service inside the VM. When I killed the server and the tunnel by hand, both were back within 25 seconds.

The rule I ended up with: the model does language jobs, and code does everything else. Distances, scores, badges, streaks, scheduling, and every message that has to be true.

What the tests changed:

- A hidden page gets no GPS, so the screen stays on behind a black cover, and any gap is stated, not counted as distance.
- The 12B model praised a wrong answer and called a quiz ready when it was not, so the Mac now sends grades and the "podcast ready" message itself.
- A quiz that failed its format checks was served with every correct answer in position A, so code now always shuffles, labels such a quiz "partial", and never serves an unverified quote.
- The agent and the server asked Ollama for two model names and context sizes, which reloaded the model at every hand-off, so both now use one alias with 64K context.

### Where it ended up

Every part of the loop has run on a real phone and a real walk: the link and the notes, the walk, the offline upload, the after-walk message, the quiz in Telegram and voice search. In one quiz retake after the grades moved to the Mac, the model stayed silent after each multiple choice answer. By Sunday the app had counted four walks: 7.66 km, 112 minutes, nine voice ideas, a three day streak and 7 of 16 badges. That is one person and one phone.

Limits:

- The 12B model is not a reliable tool user. In my tests it sometimes skipped a command and described it as done.
- Grading of the open question is unmeasured. I have three data points.
- English only, and speech recognition mishears names.
- The Mac has to be awake. While it sleeps the bot is offline and a finished walk waits on the phone.
- The screen stays on during a walk, behind the black cover.

## Why Does Open Innovation Matter?

My voice and my route stay on my machine. Voice notes are transcribed on the Mac, the GPS track is stored there, and the wiki is plain files. Ollama's request log from the agent's first day, tests included, shows 183 chat requests, all to the local model; no hosted model was configured or called.

It costs nothing per use, so the quiz repair loop can spend up to three generations on one quiz. The one metered service is the optional web search, on a free plan and capped at eight a day in my code.

I could look inside it. Ollama told me which model was loaded and with what context, which is how I found the reloads, and the agent's chat history in SQLite showed what the model actually did.

Parts are swappable: the model is one alias in one file, and the speech model, the voice and the agent harness can each be replaced. I stayed with the 12B because bigger models do not run reliably on my Mac, so I cannot say whether a larger one would do better.

Where open did not help: tool use. The open model I could run followed a tool's output worse than I wanted, and the fix was to take that job away from it.

Not everything is open or local: Telegram carries my messages and voice notes, Tailscale connects the phone to the Mac, search words go to SerpApi, the audio comes from the podcast host, and the agent's VM runs macOS (Lume, which runs the VM, is MIT licensed).

## My Agent Session

I built this with Claude Code, with subagents for brainstorming and for the app's icon, badge and layout design. The session below is an abridged transcript of 106 messages: my prompts and the final reply of each turn, shortened, with tool calls and private details removed. The first Telegram tests are the most useful part: a token the shell tool never got, and an old error the model replayed from its chat history.

<!-- TODO(author): make session 786 public on DEV first; unpublished sessions can only be embedded by their author. -->

{% agent_session 786 %}

## Prize Categories

- Gemma: Gemma 4 12B QAT, served by Ollama on my Mac, writes the notes, the quiz and the grading wording, and is the model behind the Telegram agent.
- SerpApi: voice-requested web search. A walk note that starts with "search the web for..." runs one search after the walk and puts the top three links in the Telegram message (the example above); a Telegram voice note can ask too. The key stays on the Mac, and a daily cap lives in code.

I did not use the other partners, so I left them out.

<!-- Thanks for participating! -->

<!--
PRE-SUBMISSION CHECKLIST (delete before publishing)
- [ ] Demo video embed renders (Demo section)
- [ ] Video description from docs/demo-video-description.md pasted on the video (DEV post link filled in)
- [ ] Screenshots in docs/screens are real phone screenshots and are pushed; the three image links and the diagram open
- [ ] Session 786 made public on DEV; the embed renders
- [ ] Repo pushed; the Code link opens the folder
- [ ] Claims re-read against docs/CHALLENGE-MEMORY.md "may claim / must NOT claim"
- [ ] No YouTube or yt-dlp wording in the post apart from the demo video's own link (the README keeps it)
- [ ] Numbers re-checked; the abridged-session caveat kept
- [ ] Posted with the default ai_disclosure_level; tag hf26challenge present
- [ ] Posted before the deadline: Oct 12, 2026 06:59 UTC (Sun Oct 11, 11:59 PM PDT; Mon Oct 12 01:59 local)
-->
