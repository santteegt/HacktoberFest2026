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

Here is one real turn. Session on a low-grip carpet track, and I said: "the back steps out when I get on the power out of the hairpin." The model labelled it *loose on power* (confidence 0.95). A hand-written table then picked the lever: softer rear diff oil, toward 3,000 to 4,000 cSt. The model read it back as: "We are softening the rear diff oil to around 3,000 to 4,000 cSt to let the rear wheels turn independently for more side grip. This might feel looser into the corner, so check power-on exits over three to five laps while confirming turn-in hasn't gotten looser." The whole turn took 4.0 seconds on my Mac with the E4B model.

Here is the app from first launch to race day, on a clean database with the small E2B model that runs on his laptop, one screenshot per step. The track ("Club carpet") and the "better" verdict are made up for the screenshots. Nothing in the images is edited.

**1. Start a session.** It asks for the track, the surface and the grip, because some advice depends on them: the softer diff oil row only applies on low grip.

![The first-run form "Start a practice session" with the track name Club carpet, surface carpet and grip low selected](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/walkthrough/1-start-session.png)

**2. Say what the car feels like.** I typed "the back steps out when I get on the power out of the hairpin". It reads that as *loose on power*, lists three quick checks to do first (belts, tyres, cross-tweak), then offers one change with the trade-off, how to check it and the notes it came from. It doesn't know his current diff oil, so it tells him to enter it in Setup. It won't guess a number.

![The Coach screen after the typed sentence: Loose on power, three quick checks, and the suggestion Softer rear diff oil toward 3,000-4,000 cSt with its trade-off, check and note links, plus an Open Setup button](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/walkthrough/2-say-it.png)

**3. Or tap a chip.** Chips skip the model's understanding step, which makes them faster on his laptop. "Push in" gives "Reduce caster, 4 to 3 degrees", the trade-off ("more twitchy on the straight"), and the 3D view of the change.

![The Coach screen after tapping Push in: Reduce caster from 4 to 3 degrees with the trade-off and check, a schematic 3D view labelled "Schematic, not to scale", and the coach's spoken-style wording below](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/walkthrough/3-tap-a-chip.png)

**4. Apply it, drive 3 to 5 laps, say how it felt.**

![The Coach screen after pressing Apply, marked Applied, with the question "Run 3 to 5 laps, then tell me how the car felt compared with before" and Better, Same and Worse buttons](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/walkthrough/4-apply-and-rate.png)

**5. If it was better, save the setup with today's conditions.**

![The outcome panel after pressing Better, saying "Worth keeping: save this setup with today's track conditions so you can find it on race day", and a confirmation that it was saved](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/walkthrough/5-save-setup.png)

**6. Every change is kept with its outcome.**

![The Session screen listing the change "Caster 4 deg to 3 deg (coach)" with the outcome Better selected](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/walkthrough/6-session-log.png)

With runs logged, each run shows the change made before it, and "What affected run 3?" asks the app. This one is the demo data from `npm run seed:demo`, labelled DEMO in the app.

![The Session screen with three demo runs, their ratings and best laps, and the setup change recorded with each](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/session.png)

**7. On race day, rank the saved setups for the conditions he enters.** This frame was taken after loading the labelled DEMO setups, so my one live setup ("Club carpet", score 100) sits next to them. Setups saved on a different surface are listed separately and never rank above a matching one.

![The Race day screen: today's conditions, the saved setup Club carpet scored 100 for same track and same grip, a DEMO carpet setup scored 50, and a separate group for other surfaces](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/walkthrough/7-race-day.png)

The 3D view is how the app explains a setting, because a number like "rear shock position 2 to 3" doesn't mean much until you can see it. Each suggestion plays on a small schematic car: the faint copy is the setting before and the blue one is after. There are twelve of these explainers, ten in 3D and two flat diagrams. Four of them, captured from the scene's own test page:

![Front camber going from 1.5 to 1.0 degrees negative, seen from the front: the faint tyres lean in more and the blue ones lean in less. The label reads "Camber angles exaggerated x3 for visibility"](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/scenes/camber-front.png)

Camber, seen from the front. The tops of the tyres lean in less.

![Front toe-out going from 1.0 to 1.5 degrees, seen from above, with the front wheel fronts pointing slightly further apart. The label reads "Toe angles exaggerated x4 for visibility"](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/scenes/toe-front.png)

Toe, seen from above. Front toe-out points the wheel fronts out.

![Rear ride height going from 5.0 to 5.8 millimetres, seen from the side, with the chassis sitting higher on the rear. The label reads "Heights exaggerated x4 for visibility"](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/scenes/ride-height-rear.png)

Ride height, seen from the side.

![Rear shock position going from hole 2 to hole 3, seen from the front, with the blue shocks standing more upright than the faint ones. The label reads "Shock angles exaggerated x1.5 for visibility"](https://raw.githubusercontent.com/santteegt/HacktoberFest2026/main/challenges/01-weekend-build-for-a-friend/docs/screenshots/scenes/shock-angle-rear.png)

Shock position: the outer hole stands the shock more upright. This is the move behind one of the reviewed rows in the table.

Every frame is labelled "Schematic, not to scale" and says how much the movement is exaggerated, because a 0.5 degree change would be invisible at true size.

It is a laptop app. He would have preferred his phone, and I tried: Gemma 4 E2B downloaded in a phone browser, but it lagged too much to use. I wrote that down, dropped the phone, and built for the 2019 MacBook Pro he also has.

He hasn't tried it himself yet. I installed it on his laptop to test it, and I don't know what he thinks of it. <!-- TODO author: if he tries it before publishing, add what he said (he has OK'd being quoted). -->

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

- Gemma 4 E4B (QAT build) on my Mac, served by Ollama, using Ollama's JSON-schema output so the symptom label is always a valid id. His 2019 laptop has no usable GPU for this, so it runs on the CPU. I asked him for a raw speed test with the small E2B model (`gemma4:e2b-it-qat`) and got one reading: about 9 tokens per second writing and about 39 tokens per second reading a prompt. <!-- TODO author: add his macOS version if you want it in the post -->
- Mastra runs the coach as a workflow with two pause points: one waiting for him to accept the suggestion, one waiting for the outcome after the laps. There is a plain TypeScript fallback behind the same interface, in case the workflow misbehaves.
- A Hono server and Preact UI on localhost, three.js for the 3D scenes, one LibSQL file for the vault, MiniSearch for finding the right passage in the notes.
- Voice: push-to-talk in, speech out. I have not verified this works offline on his laptop (see below).

The touring-car notes are not new. They are a frozen snapshot of my earlier notes, which I distilled from other people's videos and manuals, and the repo credits that separately and checks it against a hash. All the code is new and written during the window. I did not reuse my earlier 3D guide or setup-sheet app.

On testing: the symptom test has 25 cases, 20 in my wording and 5 in my friend's. I ran it on the bigger E4B model first, and Gemma got 24 right. Then I installed it on my friend's laptop, which runs the smaller E2B model, and hit a bug my test had hidden: whatever I asked, the coach answered "reduce caster". When the small model can't place a sentence it falls back to the same symptom, even for "hello". On the same 25 cases E2B gets 21 right, and it refused only 6 of 12 off-topic sentences I tried.

I added a plain-code check in front of the model. A sentence with no word about driving or setup gets the refusal without calling the model at all, which also saves a few seconds on his laptop. With it E2B gets 23 of 25, and "hello", "what time is it" and "how should I run cli commands on a macbook" are all refused. A sentence that does contain a driving word, like "how many laps is the main race", still goes through to the model. I widened the word list once after it wrongly refused one of my slangy test cases, so that 23 is partly tuned on the test and not a clean number.

On his own five sentences E2B got 5 right and E4B got 4. The E4B miss was "it's understeering out of the corner": I'd labelled it as pushing on corner *entry*, the model said corner *exit*, and I think the model's reading is fair. A plain keyword matcher got 17 of 25. On 14 fresh phrasings I'd written down answers for before running them, E4B got 13. Finding the right passage in the notes hit 9 of 10 on questions I wrote before tuning the search. These are small tests, written by me, run on an Apple M4 Max with the model loaded. They say the app works for the sentences I tried; they do not say it understands everyone. His laptop is several times slower than my Mac, as the next list shows.

What fell short:

- It is slow on his laptop. A typed sentence goes through the model twice, and from his one speed reading I estimate about 25 seconds for a full answer, and about 15 seconds for a symptom chip, which skips one of the two model steps. Text streams in while it is written. That is an estimate from the speed test, not a timing of the app, which I haven't done on his laptop yet. There is a setting that turns the model's wording off and shows the plain template text instead: the advice and numbers are the same, a chip answers straight away, and a typed sentence only waits for the model to understand it.
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

- Gemma: Gemma 4 (E4B QAT on my machine, E2B QAT on his) is the model behind both language steps, served by Ollama.
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
