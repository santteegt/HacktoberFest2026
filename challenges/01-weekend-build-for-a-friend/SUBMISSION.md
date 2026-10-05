---
title: A setup coach for my friend's RC car that stays on his laptop
published: false
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

My friend races a 1/10 touring car, a Yokomo BD12. On practice days he changes something, drives a few laps, changes something else, and by the afternoon he can't say which change helped. When the championship race comes he has no record of what worked at which track.

That is what he asked me for. In his words: "this app will be very useful for practice days so I can quickly store my settings and get feedback from what works, what might have affected my run."

RC Pit Companion does three things:

- The coach: he says how the car feels ("the track is very slippery", "once i hit the breaks into the corner the car oversteers"). It picks one change, says what to expect and how to check it over the next few laps, and shows the change on a small 3D car.
- The practice log: each change is stored with a better, same or worse outcome, next to the track conditions. It tells him whether a lap-time difference is bigger than the usual run-to-run noise.
- Race day: he enters the conditions and gets his saved setups ranked by how close the track was to the one he's racing.

Here is one real turn. Session on a low-grip carpet track, and I said: "the back steps out when I get on the power out of the hairpin." The model labelled it *loose on power* (confidence 0.95). A hand-written table then picked the lever: softer rear diff oil, toward 3,000 to 4,000 cSt. The model read it back as: "We are softening the rear diff oil to around 3,000 to 4,000 cSt to let the rear wheels turn independently for more side grip. This might feel looser into the corner, so check power-on exits over three to five laps while confirming turn-in hasn't gotten looser." The whole turn took 4.0 seconds on my Mac.

The screenshots below come from the app running on its labelled demo data (`npm run seed:demo`), not from real laps. This first one has my friend's own sentence typed in. The suggestion it gets comes from a row of the table that I haven't reviewed yet, and the card says "draft row (not reviewed)". The 3D view is labelled "Schematic, not to scale."

![The Coach screen after typing "once i hit the breaks into the corner the car oversteers": the app reads it as loose on entry, lists three quick checks, suggests one change with the trade-off and how to check it, and shows it on a schematic 3D view](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/coach.png)

The session log keeps each run with the change made before it. "What affected run 3?" is the question he asked for.

![The Session screen with three demo runs, their ratings and best laps, and the setup change recorded with each](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/session.png)

Race day ranks the saved setups against the conditions he enters.

![The Race day screen with today's conditions and a saved demo setup scored 100 for matching track, grip and temperature](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/race-day.png)

It is a laptop app. He would have preferred his phone, and I tried: Gemma 4 E2B downloaded in a phone browser, but it lagged too much to use. I wrote that down, dropped the phone, and built for the 2019 MacBook Pro he also has.

He hasn't used it yet. I don't know what he thinks of it, and I haven't run it on his machine. <!-- TODO author: if he tries it before publishing, add what he said and his OK to be quoted. -->

## Demo

<!-- TODO author: video link (record the Wi-Fi-off run) -->

## Code

{% github santteegt/HacktoberFest2026 %}

The project is in the `challenges/01-weekend-build-for-a-friend` folder of that repo. MIT licensed. The README has run steps (Node 22.13+, Ollama, two commands) and the full list of limits.

## How I Built It

The model does two small jobs. Everything else is plain code.

1. Gemma 4 turns what he said into one of 12 symptoms, or into "not something my notes cover."
2. After the advice is chosen, Gemma phrases it as a short spoken paragraph.

Between those two steps there is no model. A table of 61 adjustments (`levers.json`) says what to change, in which direction, by how much, and what it costs elsewhere on the car. I reviewed 12 of those rows by hand, and the app marks the other 49 as drafts. The model never makes up a number: a guard checks the wording against the table, and a template answer replaces the model's text if it strays. Every answer cites the notes it came from. A question outside the notes gets a refusal, not a guess.

The stack:

- Gemma 4 E4B (QAT build) served by Ollama, using Ollama's JSON-schema output so the symptom label is always a valid id. On a CPU-only 2019 laptop the likely choice is E2B; I don't know yet, because I haven't measured on his machine.
- Mastra runs the coach as a workflow with two pause points: one waiting for him to accept the suggestion, one waiting for the outcome after the laps. There is a plain TypeScript fallback behind the same interface, in case the workflow misbehaves.
- A Hono server and Preact UI on localhost, three.js for the 3D scenes, one LibSQL file for the vault, MiniSearch for finding the right passage in the notes.
- Voice: push-to-talk in, speech out. I have not verified this works offline on his laptop (see below).

The touring-car notes are not new. They are a frozen snapshot of my earlier notes, which I distilled from other people's videos and manuals, and the repo credits that separately and checks it against a hash. All the code is new and written during the window. I did not reuse my earlier 3D guide or setup-sheet app.

On testing: the symptom test has 25 cases; Gemma got 24 right. Twenty cases are in my wording. Five are in my friend's words, and Gemma got 4 of those 5 right as I'd labelled them. The miss was "it's understeering out of the corner": I'd labelled it as pushing on corner *entry*, the model said corner *exit*, and I think the model's reading is fair. A plain keyword matcher got 17 of 25. On 14 fresh phrasings I'd written down answers for before running them, Gemma got 13. Finding the right passage in the notes hit 9 of 10 on questions I wrote before tuning the search. These are small tests, written by me, run on an Apple M4 Max with a model loaded. They say the app works for the sentences I tried; they do not say it understands everyone. My friend's laptop will be slower, and I haven't timed it.

What fell short:

- The 3D scenes are schematic. The directions come from the notes and some sizes are exaggerated so you can see them. The label says so.
- On-device speech recognition said "unavailable" in the browser I tested with. Typing and tapping a symptom chip both work without it, but I can't tell you the voice path works offline until I run it with Wi-Fi off on a real desktop browser.
- Setup needs Node and Ollama. There's no installer.

## Why Does Open Innovation Matter?

Three things here depend on the model being open.

First, it runs where he races. A pit table is not a place I can count on a good connection. The model, the notes, the vault and the search are all on his laptop, so the app doesn't need a connection to answer. I checked that the server and Ollama opened only local connections during a full loop, but that is an audit, not a Wi-Fi-off test, and I'll say so plainly.

Second, his setups stay with him. What he runs at a track, and how it goes, is his own record. The vault is one file on his disk.

Third, it costs nothing per question, and I can see why it answers what it answers. A closed API would bill per turn and would send his habits somewhere. With open weights I could also shrink the prompt until it fit a slow CPU (252 tokens, down from 389, with accuracy unchanged on my 25 cases) and find out that Ollama's JSON schema doesn't reach the model: a version that relied on the schema alone scored 3 of 25. The advice itself isn't hidden in model weights either. It's in a table and a set of notes he or I can open and correct in an editor. I did not fine-tune Gemma, because tuned weights can't cite a source or be fixed by editing a file.

## My Agent Session

<!-- TODO author: after the DevRelay upload is made public, embed it here with the agent_session tag, or link it. -->
I built this with Claude Code: one planner agent, then builder and reviewer subagents working on separate parts of the code. The session shows the phone test that failed, the frozen-notes decision, and how I checked the agents' claims, including a fresh-clone test that found the project didn't install cleanly and led to a fix.

## Prize Categories

- Gemma: Gemma 4 (E4B QAT on my machine, E2B QAT planned for his) is the model behind both language steps, served by Ollama.
- Mastra: Mastra 1.74 runs the coach workflow, including the two pause points.

I looked at the other partners and left them out. Most would have meant a cloud service in a project that is meant to run on one person's laptop.

<!-- Thanks for participating! -->

<!--
PRE-SUBMISSION CHECKLIST (delete before publishing)
- [ ] Project started inside the window; later commits noted in README
- [ ] Open-source AI is the core; "Why open" is concrete (not generic)
- [ ] Public repo with LICENSE; demo link/video works
- [ ] Each prize category listed has a meaningful, real use in the code
- [ ] Agent session public (if embedded) and scrubbed of secrets
- [ ] Friend OK'd the quote (and whether to name him)
- [ ] English; no teammates
- [ ] All TODO comments above resolved
-->
