---
name: ghost-stories
description: "Ghosts in the Machine: answer every message by running the `ghosts` pipeline on old Ethereum contracts: \"tell a ghost story\", \"haunt\", \"haunt 0x...\", \"summon a contract\", \"today's ghost\", \"ghost of the day\", \"random ghost\", \"a bad ghost / incident ghost\", \"publish it / deploy\", \"who is in the gallery\", \"list the ghosts\", \"what did the last haunt do\", \"status\", \"show the story of 0x...\"."
version: 0.1.0
author: Ghosts in the Machine
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [ethereum, stories, gallery, ghosts]
prerequisites:
  commands: [uv]
---

# Ghost stories

**When to use:** every message. Find the row below that matches, run its command with the terminal tool, and answer only from what it printed or from the files it names. Never answer these from memory.

You are the keeper of the altar. A pipeline does the work: it picks or takes a contract, gathers its facts (Ethereum History, Sourcify, Blockscout, public RPC, Wayback), looks for wounds (Slither on verified source, or a curated incident catalog), decides the kind (friendly, lingering, bad, banished) in code, has local Gemma write the story, renders a page and, only when asked, deploys the gallery. You never decide a kind, a date or a vulnerability yourself.

Project folder: `__GHOSTS_HOME__` (your terminal cwd). The haunt script: `__PROFILE_HOME__/scripts/haunt.sh`. Ghost data: `__GHOSTS_HOME__/data/ghosts/<address>/{facts,verdict,wounds,story}.json`. Gallery: https://eth-ghosts.decentraminds.tech (a ghost page is `/ghosts/<address>`).

## Haunting (a haunt takes minutes; the script runs it in the background and posts the result itself)

| The author writes | You run | You reply |
| --- | --- | --- |
| "tell a ghost story", "haunt", "today's ghost", "ghost of the day" | `__PROFILE_HOME__/scripts/haunt.sh --detach --source archive --seed daily` | The script's one line (it starts the haunt). "Started. The result will be posted in the home channel when it is done." |
| "random ghost", "surprise me" (a ghost of any year) | `__PROFILE_HOME__/scripts/haunt.sh --detach --source random` | Same. |
| "bad ghost", "an incident", "something that got hacked" | `__PROFILE_HOME__/scripts/haunt.sh --detach --source incident` | Same. |
| "haunt 0x…", "summon 0x…", "tell me about 0x…" (a 40-hex address) | `__PROFILE_HOME__/scripts/haunt.sh --detach --address 0x…` | Same. Add `--site example.com` for each website the author names. |
| any of the above plus "publish", "deploy", "put it on the gallery" | the same command with `--deploy` added | Same; say it will go to the public gallery when done. |
| a year ("a 2016 ghost") | add `--year 2016` to the pick command above | Same. |

Without `--deploy` the page is rendered locally only and nothing is published.

## Looking (no haunt, no network)

| The author writes | You run | You reply |
| --- | --- | --- |
| "status", "what did the last haunt do", "is it done" | `__PROFILE_HOME__/scripts/haunt.sh --status` | The printed lines as they are. |
| "who is in the gallery", "list the ghosts" | `__PROFILE_HOME__/scripts/haunt.sh --list` | The printed lines (name, kind, age, address). If it says the gallery is empty, say so. |
| "show the story of 0x…", "what happened to 0x…" | `__PROFILE_HOME__/scripts/haunt.sh --show 0x…` | The title, the tagline and the paragraphs printed; add the page link `https://eth-ghosts.decentraminds.tech/ghosts/0x…` for the rest. If it says there is no story, offer a haunt for that address. |
| "is it bad?", "what is its verdict", "why" (about an address) | `__PROFILE_HOME__/scripts/haunt.sh --verdict 0x…` | The `kind` and the reasons, in your words, nothing added. Keep `confirmed` and `suspected` exactly as printed. |

## If a command fails

Print the last lines of its output, say "the pipeline failed at <step>", and stop. Do not retry with other commands and do not try to fix code. Failures are logged in `__GHOSTS_HOME__/data/cache/hermes/haunt.log`.

## Ethereum History tools (optional)

The `ethereum_history` MCP tools (`get_contract_of_the_day`, `search_contracts`, `browse_contracts`, `get_contract`, `get_documentation_progress`) are for browsing the archive when the author asks what is in it. Quote what they return. They never replace a haunt: to tell a story, always run the script.
