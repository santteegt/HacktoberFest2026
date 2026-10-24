---
name: skunkworks-board
description: "Keep the Skunkworks Sloth board: ask the weekly focus, post the daily prototype pick with buttons, move the picked card to Today, show the board."
version: 0.1.0
author: Santiago Gonzalez
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [skunkworks, board, prototypes, discord]
    related_skills: []
---

# Skunkworks board (Coordinator)

## When to use

- A cron job or the author asks for the **daily pick** ("what should I build today?", `/pick`, "pick").
- A cron job or the author asks for the **weekly focus** (`/focus`, "new week", "change my focus"), or the author tells you what they care about this week.
- The author taps a button you showed, or answers a question you asked with clarify.
- The author asks to see the board (`/board`, "what's on the board?").

## How it works

The `sloth` command does everything that has to be right: scoring the cards, choosing the options,
moving cards, writing the board files, syncing the GitHub Project and logging to `#sk-logs`.
Your job is to run it, show its buttons with clarify, pass the author's answer back verbatim,
and send its `reply`. You never pick a card yourself and never move one without the author's answer.

Run commands with the `terminal` tool (the working directory is already set). Every command below
prints one JSON object:

- `ok`: whether it worked.
- `reply`: the message for the author. Send it **exactly as given**, in full.
- `question` and `choices` (when present): call **clarify** with exactly this question and these
  choices, in this order. Do not reword, add or drop choices.
- `action`: the next step. Follow it.

## Daily pick

```bash
uv run sloth pick options --json
```

1. Send `reply` (it lists the options with one line each).
2. Call clarify with `question` and `choices`.
3. When the author answers, tapped or typed, run, with their answer copied verbatim:

```bash
uv run sloth pick choose --json "<the author's answer, verbatim>"
```

4. Send `reply`. The command already moved the card to Today, synced the board and told the Worker.

If `ok` is false, send `reply` and stop. Never call `pick choose` without an answer from the author.

## Weekly focus

```bash
uv run sloth focus --question --json
```

Call clarify with `question` and `choices`. When the author answers (a tapped choice or their own
words), run:

```bash
uv run sloth focus --json "<the author's answer, verbatim>"
```

Send `reply`. If the author tells you their focus without being asked ("this week: rust"), run the
same command with their words.

## Today's pick

```bash
uv run sloth pick show --json
```

`card` is today's card, or null when nothing is in Today. Send `reply`.

## Show the board

```bash
uv run sloth board show
```

Send the output as a code block, then one line with the Project link if the author asks for it
(it is in the README status block of the GitHub Project "Skunkworks Sloth").

## Rules

- Copy the author's words into commands verbatim, inside double quotes. Do not translate or summarize them.
- Never invent a card id, a title, a score or a cost. Everything you say about a card comes from a command's `reply`.
- Never run `sloth board init`, `sloth board seed-fixtures`, `sloth board sync --prune` or `sloth work`.
- If a command fails (non-zero exit or no JSON), say "The board command failed; the author's session will look at it." and stop. Do not retry more than once and do not make up a result.
