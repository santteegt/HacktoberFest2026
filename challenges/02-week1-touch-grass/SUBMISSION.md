---
title: "Idea Leash: an open-source walk buddy with a local model for a brain"
published: true
tags: devchallenge, hf26challenge
---

<!-- PUBLISHED by the author on DEV on 2026-10-11 23:30 local (2026-10-12T04:30:20Z), about 2.5 h before the deadline: https://dev.to/santteegt/idea-leash-an-open-source-walk-buddy-with-a-local-model-for-a-brain-499n (article id 4835517). This file is the body as published, synced from DEV after the author's final edits. What the author changed on DEV against the staged draft v8: removed the test-sessions table and its closing sentence, the "second brain is an OKF wiki" subsection, the launchd paragraph, the "What the tests changed" bullets and the closing "I did not use the other partners" line; reworded the skill-creator sentence; added a caffeinate note to the limits. DEV re-hosts the images, so the raw.githubusercontent links below are only the source. -->

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

## Code

{% github santteegt/HacktoberFest2026 %}

The code, the setup steps and the dated log of everything can be found in the `challenges/02-week1-touch-grass` folder. MIT licensed.

## How I Built It

![Architecture diagram in three columns. Phone: two apps. The Leash app records route, voice notes and taps, with an offline queue, and reaches the Mac over Tailscale. Telegram carries links, quiz answers and voice notes to the bot. Mac: a tool server that computes km, scores, badges and streaks, calls whisper.cpp, graphify, Piper and Gemma 4 on Ollama, and writes the wiki; a macOS VM run by Lume holds the Leash agent (a Hermes profile) and leashctl, linked to the Mac by an SSH tunnel. Internet: podcast host, SerpApi and the Telegram bot. Numbered badges 1 to 6 mark the steps listed below](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/0bb881cf9cdeb53a2c2e430a790c1e615540e032/challenges/02-week1-touch-grass/docs/architecture.png)

The numbers in the diagram follow one loop:

1. A link I send in Telegram reaches the Leash agent, a Hermes profile in a macOS VM. The agent runs `leashctl`, which calls the tool server on the Mac through an SSH reverse tunnel. The server fetches the audio from the podcast host, graphify transcribes it, Gemma writes the notes and the quiz, the notes go into the wiki, and Piper makes spoken versions of the questions (not used in the Telegram quiz yet).
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

### Two agent skills

The agent's behaviour lives in two skills in the repo's `skills/` folder. A skill is a `SKILL.md` of instructions plus scripts the agent can run.

- `podcast-quiz` turns a transcript into four multiple-choice questions and one field-link question, and grades spoken answers afterwards. Its scripts check every question's quote against the transcript, the spoken length and the answer-length bias, and shuffle the answer positions.
- `leash-tools` tells the agent how to reach the Mac with one command, `leashctl`: `ingest`, `next`, `answer`, `idea`, `search`, `resurface`, `walks` and `audio`.

I used the `skill-creator` skill workflow for implementing them: write the skill, run it on three test transcripts with the local Gemma model, read the failures, change the skill, run again. It took four rounds. The checking script did more than the prose: with it, the skill passed 27 of 27 checks, against 20 of 27 for a plain prompt.

Telegram taught me a second lesson. The 12B model did not follow a paragraph in a skill and wrote a question as plain text instead of calling the buttons tool. So the instruction moved into the tool's reply, in an `action` field the agent only has to follow. `agent/setup-profile.sh` installs the Hermes profile with both skills.

The rule I ended up with: the model does language jobs, and code does everything else. Distances, scores, badges, streaks, scheduling, and every message that has to be true.

### Where it ended up

Every part of the loop has run on a real phone and a real walk: the link and the notes, the walk, the offline upload, the after-walk message, the quiz in Telegram and voice search. In one quiz retake after the grades moved to the Mac, the model stayed silent after each multiple-choice answer. By Sunday, the app had counted four walks: 7.66 km, 112 minutes, nine voice ideas, a three-day streak and 7 of 16 badges. That is one person and one phone.

Limits:

- The 12B model is not a reliable tool user. In my tests, it sometimes skipped a command and described it as done.
- Grading of the open question is unmeasured. I have three data points.
- English only, and speech recognition mishears names.
- The Mac has to be awake. While it sleeps, the bot is offline, and a finished walk waits on the phone. Used `caffeinate` to keep my laptop awake while going out.
- The screen stays on during a walk, behind the black cover.

## Why Does Open Innovation Matter?

Idea Leash asks for a lot of trust. It hears my voice, keeps the routes I walk with my dog, and builds a private memory of what I learn. Open models and an open agent harness made it buildable on those terms, because every part that thinks runs on my own Mac, where I can look inside it and change it.

No hosted model hears my voice or sees my route. Gemma 4 12B answers through Ollama, whisper.cpp transcribes voice notes on the Mac (a 15-second clip in 0.95 s), and the GPS track is stored there. Ollama's log from the agent's first day, tests included, shows 183 chat requests, all to the local model. My reasoning, not a test: with a hosted model, every voice idea and episode transcript would pass through a server I do not control.

Free calls shaped the design. The quiz generator checks every quote against the transcript and regenerates up to three times when a check fails. With a bill per call, I would have weighed each retry and each test run against the cost, and I suspect I would have tested less.

I could open it up. Ollama shows which model is loaded and with what context, which is how I caught it reloading at every hand-off. Hermes keeps its chat history in SQLite, so I read what the model actually did instead of trusting its summary. The agent is a folder of files (persona, allowed tools, two skills), versioned and tested like code, so I decided which jobs the model gets. Grades now come from code. The model is one alias in one file, and the speech model, the voice and the harness can each be swapped.

The second brain is plain OKF markdown, so any tool or agent can read it, and nothing I learn is locked in a product. One script installs the agent profile with both skills on a Hermes instance. I have run it in one VM only, so "someone else could run their own Leash on their own Mac" is a design goal, not a result. It is also how one person put this together inside the challenge week, from open parts that each do one job.

Not all of it is open. Telegram carries my messages and voice notes, Tailscale links the phone to the Mac, search words go to SerpApi, the audio comes from the podcast host, and the agent's VM runs macOS.

## My Agent Session

I built this with Claude Code, with subagents for brainstorming and for the app's icon, badge and layout design. The session below is an abridged transcript of 106 messages: my prompts and the final reply of each turn, shortened, with tool calls and private details removed. The first Telegram tests are the most useful part: a token the shell tool never got, and an old error the model replayed from its chat history.

{% agent_session 786 %}

## Prize Categories

- Gemma: Gemma 4 12B QAT, served by Ollama on my Mac, writes the notes, the quiz and the grading wording, and is the model behind the Telegram agent.
- SerpApi: voice-requested web search. A walk note that starts with "search the web for..." runs one search after the walk and puts the top three links in the Telegram message (the example above); a Telegram voice note can ask too. The key stays on the Mac, and a daily cap lives in code.
