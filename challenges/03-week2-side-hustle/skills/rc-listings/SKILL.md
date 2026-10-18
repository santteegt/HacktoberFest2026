---
name: rc-listings
description: "Record what a club member HAS or NEEDS (RC car parts), find matches in the club, answer who-has-what questions."
version: 0.1.0
author: Santiago Gonzalez
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [RC, parts, club, listings, WhatsApp]
    related_skills: [rc-quote]
---

# RC listings: HAVE / NEED

## When to use

A member tells the bot they have a spare part, kit or accessory (HAVE), or that they are looking for one (NEED), or asks who in the club has something. Also when a member answers a clarifying question you asked about a listing.

## How it works

Everything that must be correct is done by the `rcparts` command: validation, normalization, saving, matching and the direct messages to matched members. Your job is to turn the member's words into one JSON listing, run the command, and relay its `reply`.

Run commands with the `terminal` tool from `$RCPARTS_HOME` (the working directory is already set):

```bash
uv run rcparts listing add --json '<LISTING_JSON>'
```

Never pass `--phone`: the command reads who wrote the message from the session itself (in a group, the person, not the group). Never look up phone numbers or names in the database.

### The listing JSON you write

```json
{"kind": "HAVE", "brand": "tamiya", "chassis": "tt-02", "part_number": "TAM54500",
 "description": "68T high speed spur gear set", "condition": "new", "price_usd": 10, "qty": 1}
```

- `kind`: `HAVE` or `NEED`. Required.
- `part_number`: only if the member wrote one; copy it as written (the command normalizes it). Never invent one.
- `brand`, `chassis`, `description`: what the member said, in their words; leave out what they did not say.
- `condition` (`new`, `used`, `unknown`), `price_usd` and `qty`: HAVE only, only if stated. `qty` defaults to 1.
- Spanish or English input both work; keep `description` in the member's language.

### What the command returns (JSON on stdout)

- `ok: true`: the listing is saved. `reply` is the confirmation (it echoes the parsed fields); send it verbatim. `matches` lists any matches; if non-empty, the command already sent direct messages to both members (`notified: true`); in a group, add one line saying there is a match and that both members were written to. Do not post phone numbers in the group.
- `ok: false` with `error: missing_fields` and `missing`: ask the member exactly the question in `reply`, wait for the answer, then run the command again with the completed JSON.
- `ok: false` with `error: not_member`: send `reply` (it tells them how to register) and stop.
- `ok: false` with `error: bad_json`: fix the JSON you wrote and run it again; do not ask the member.
- `action`: the next step. Follow it.

### Other commands

```bash
uv run rcparts search --club <CLUB_ID> --text "<what they ask for>" --kind HAVE   # who has X? (open HAVE listings, best first)
uv run rcparts listing list                       # a member's own listings
uv run rcparts listing close --id <LISTING_ID>    # when the member says it is sold or no longer needed (owner only)
uv run rcparts member get                         # club id, name, class, brands
```

For `search`, relay the `reply` (it lists the matching HAVE listings with their owners' first names, never phone numbers in a group).

## Rules

- One listing per command call. A message with two parts is two calls.
- Never add, round or convert numbers. If the member wrote "$10", `price_usd` is 10; if they wrote nothing, leave it out.
- If the command fails (non-zero exit or no JSON), tell the member the parts desk has a problem and that the maintainer was notified. Do not make up a result.
