---
name: prototype-box
description: Build one Skunkworks Sloth card as a small prototype inside a hard time box, in the repo the runner prepared. Use when the task says "Skunkworks Sloth card".
---

# Prototype box (Skunkworks Sloth Worker)

You are the Worker. The runner (`sloth work <card_id>`) has already created a git repo from the prototype template and started a timer. You build; code around you holds the clock, the database, Discord and GitHub.

## Where you work

- Only inside the repo directory named in the task. Do not read or write anything outside it.
- `TASK.md` is the card: learning goal, hypothesis, done-means, kill criteria, source links. Read it first.
- Python 3.12+ with `uv`. Add dependencies with `uv add <pkg>` only when the card needs them; prefer the standard library. No Docker, no sudo, no global installs.
- Local models, if the card needs one, are on Ollama at `http://localhost:11434` (`ollama list` shows what is installed; do not pull models larger than 1 GB).

## What done means

1. `make test` passes, with real tests for the done-means (delete `tests/test_placeholder.py`).
2. `make demo` runs and shows the done-means in under a minute, without network keys.
3. `NOTES.md` is filled: **Built** (what exists, how to run it), **Learned** (hypothesis confirmed, refuted or unclear, and why), **Next** (one next step), **Links used** (keep the list, mark which links you actually used).
4. `README.md` placeholders still read well; adjust the "Run it" section if commands changed.
5. Commit your work locally with clear messages (`git add -A && git commit -m ...`). Commit at least every 30 minutes.

## Rules

- Never `git push`, never run `gh`, never create remotes. Publishing happens only after the author approves in Discord, and code does it.
- Never put keys, tokens or personal data in the repo.
- Small and working beats big and broken. Cut scope to fit the box; say what you cut in NOTES.md.
- If the kill criteria are met, stop, write NOTES.md honestly (what failed and why) and commit.
- When you get the wrap-up notice (80% of the box), stop building: finish NOTES.md, commit, and answer.

## Your final answer

Reply with exactly one line of JSON and nothing else:

```json
{"status": "done" | "partial" | "killed", "summary": "<= 300 chars: what was built and whether done-means is met", "tests": "<make test result in a few words>", "learned": "<= 200 chars"}
```

The runner checks `make test` itself; your answer is the human summary, not the verdict.
