---
name: rc-quote
description: "Quote an import of an RC part from a whitelisted US hobby shop (price + weight-based fee) and record accepted quotes for the daily order."
version: 0.1.0
author: Santiago Gonzalez
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [RC, parts, import, quote, WhatsApp]
    related_skills: [rc-listings]
---

# RC import quote

## When to use

- A NEED listing was saved and the command reported no match (`matches` empty) and the member wants to buy it.
- A member asks directly how much it would cost to bring a part ("cuánto sale traer un TAM54500", "can you quote a BD12 front bumper").
- A member answers YES (sí, dale, ok, listo) to a quote you sent.

## Commands

Run with the `terminal` tool from `$RCPARTS_HOME`:

```bash
uv run rcparts quote --phone <SENDER_PHONE> --query "<part number or the member's words>"
uv run rcparts quote --phone <SENDER_PHONE> --listing <LISTING_ID>        # quote an existing NEED listing
uv run rcparts quote accept --phone <SENDER_PHONE> --quote <QUOTE_ID>     # the member said YES: we order it for them (processing fee)
uv run rcparts quote accept --phone <SENDER_PHONE> --quote <QUOTE_ID> --self-order   # the member will order it themselves and only ship through us (weight fee only)
uv run rcparts quote list --phone <SENDER_PHONE>                          # their open quotes
```

Prefer `--query` with the part number when the member gave one; otherwise pass their words as they wrote them. `SENDER_PHONE` is the digits before `@s.whatsapp.net` in the session's `user_id`; if you cannot see it, omit `--phone` and the command reads it from the session. Never query the database for it.

## What the command returns

- `ok: true`: `reply` contains the store item, price, weight as listed by the store, the import fee, the optional processing fee, both totals, stock status, the store link and the instruction to answer YES. Send it verbatim, in a direct message when the request came from the group (say in the group that you sent the quote by DM).
- `ok: false` with `error: not_found`: send `reply` (it suggests sending the exact part number). `no_weight`: the store lists no weight, so no quote; send `reply`. `store_unavailable`: the shop did not answer; send `reply` and suggest trying later.
- Every quote has **two totals**: "we order it for you" (store price + weight fee + processing fee) and "self-order" (the member buys it and ships it to our US address; weight fee only). A plain YES means the first; if the member says they will buy it themselves, use `--self-order`.
- `quote accept` returns `ok: true` and a `reply` confirming the item is in today's order; send it verbatim.
- `action`: the next step. Follow it.

## Rules

- The store search goes only to the whitelisted shop built into the command. Do not browse, search the web or quote any other store.
- Every number comes from the command. Do not estimate shipping, taxes, exchange rates or delivery times.
- A quote is not an order. Only `quote accept` after an explicit YES from the same member records it, and the maintainer places the order from the daily batch (`orders daily --send`, run by cron, never by you).
- If the member asks for a part that is out of stock, say so with the command's `reply`; do not promise a restock date.
