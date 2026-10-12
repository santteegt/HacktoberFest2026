# Demo video description (paste into the video's description)

Video: https://youtu.be/ikb7P_XMQAw (3 min 59 s). Current title: "Leash ambient agent demo".
Suggested title: "Idea Leash: walk the dog, keep the ideas (local model, open-source AI)"

Note for the author: replace the DEV post placeholder near the end with the real link, and delete the two TODO(author) timestamp lines, before pasting.

---

Walk the dog, keep the ideas: a local, open-source AI that turns my walks into a second brain.

This is a walkthrough of how I use the Leash app and its ambient agent to rest from work and touch grass: going out with my dog or out to exercise, while a second brain keeps what I learned and the ideas I had on the way. I built it for the Hacktoberfest 2026 Open-Source AI Challenge, Week 1: Touch Grass.

It is for anyone who walks with a podcast and wants to keep some of it, and for developers curious about running an agent on a local open model.

TODO(author): add timestamps
0:00 ...

How it works
1. Before the walk I send an episode link to a Telegram bot. My Mac transcribes it, writes notes into a markdown wiki and prepares a five question quiz. Every question quotes the transcript, and a script checks the quote.
2. On the walk the phone stays in my pocket. A small web app records the route, and one big button records voice ideas.
3. After the walk the Mac sends one Telegram message: distance, time, my ideas, and the top links for any note that asked for a web search.
4. I say "quiz me" and the questions arrive as Telegram buttons. The last one asks me to connect an idea from the episode to something I saw on the walk.
5. Badges for kilometers, time with the dog, streaks, voice ideas and quiz results are computed by code, not by the model.

Stack
Gemma 4 12B (QAT build) through Ollama, Hermes Agent, whisper.cpp, graphify, Piper, an OKF markdown wiki, a small Python tool server, a one-file web app in Chrome on Android, Telegram, Tailscale and SerpApi.

Open source
The model weights (Gemma 4, Apache 2.0), Ollama, Hermes Agent (MIT), whisper.cpp (MIT), graphify, Piper (GPL-3.0, spoken versions of the questions), Lume (MIT, runs the agent's VM) and all of this project's code (MIT). Not open: Telegram, Tailscale, SerpApi, the podcast host and macOS inside the VM.

Honest limits
The phone screen stays on during a walk, hidden behind a black cover, because a web page in Chrome gets no GPS while it is hidden. The AI runs on my Mac, not on the phone, so the Mac has to be awake for the bot to answer; walks and voice notes wait on the phone until it can reach the Mac. Tested by one person with one phone, in English only.

Code: https://github.com/santteegt/HacktoberFest2026/tree/main/challenges/02-week1-touch-grass
DEV post: https://dev.to/santteegt/idea-leash-an-open-source-walk-buddy-with-a-local-model-for-a-brain-499n

#hf26challenge #Hacktoberfest #OpenSourceAI #LocalAI #Gemma #TouchGrass
