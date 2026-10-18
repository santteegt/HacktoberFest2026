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
- A member sends a **PDF** in a direct message after accepting a quote (the deposit receipt).
- The maintainer writes "confirmar <id>" or "rechazar <id> <motivo>".

## Commands

Run with the `terminal` tool from `$RCPARTS_HOME`:

```bash
uv run rcparts quote --query "<part number or the member's words>"
uv run rcparts quote --listing <LISTING_ID>        # quote an existing NEED listing
uv run rcparts quote accept --quote <QUOTE_ID>     # the member said YES: we order it for them (processing fee)
uv run rcparts quote accept --quote <QUOTE_ID> --self-order   # the member will order it themselves and only ship through us (weight fee only)
uv run rcparts quote list                          # their open quotes
```

Prefer `--query` with the part number when the member gave one; otherwise pass their words as they wrote them. Never pass `--phone`: the command knows who is writing.

## What the command returns

- `ok: true`: `reply` contains the store item, price, weight as listed by the store, the import fee, the optional processing fee, both totals, stock status, the store link and the instruction to answer YES. Send it verbatim, in a direct message when the request came from the group (say in the group that you sent the quote by DM).
- `ok: false` with `error: not_found`: send `reply` (it suggests sending the exact part number). `no_weight`: the store lists no weight, so no quote; send `reply`. `store_unavailable`: the shop did not answer; send `reply` and suggest trying later.
- Every quote has **two totals**: "we order it for you" (store price + weight fee + processing fee) and "self-order" (the member buys it and ships it to our US address; weight fee only). A plain YES means the first; if the member says they will buy it themselves, use `--self-order`.
- `quote accept` (we order it) returns `ok: true` and a `reply` with the amount to deposit, the reference `RC-Q<id>` and "envía el comprobante en PDF aquí"; send it verbatim. The item is **not** ordered until the maintainer confirms the deposit. `--self-order` keeps the old behavior: accepted, weight fee only.
- `action`: the next step. Follow it.

## Deposit receipt (PDF)

When a member sends a PDF in a direct message, the message you get starts with a note like:

```
[The user sent a document: 'comprobante.pdf'. It is saved at: /Users/.../.hermes/profiles/rc-parts/cache/documents/doc_1a2b3c4d5e6f_comprobante.pdf. Its text is not inlined here ...]
```

Do not read or summarize the PDF yourself. Pass that exact path to the command:

```bash
uv run rcparts deposit submit --file "<the path after 'It is saved at:'>"                 # the command finds their quote awaiting a deposit
uv run rcparts deposit submit --quote <QUOTE_ID> --file "<path>"                           # when they have several (after `error: ambiguous`)
```

- `ok: true`: send `reply` (received, waiting for confirmation). The command already sent the receipt and its checks to the maintainer. A wrong amount or reference does not block it; the maintainer decides.
- `error: ambiguous`: send `reply` (numbered list of their quotes awaiting a deposit), ask which one, run again with `--quote`.
- `error: no_awaiting_quote` / `quote_not_awaiting_deposit` / `not_pdf` / `no_file`: send `reply`.
- If you cannot find the path in the message, run the command without `--file`; it falls back to the newest PDF the gateway received in the last 15 minutes and tells the maintainer it did so.

### The maintainer confirms or rejects

Only when the **maintainer** writes it (the command checks who is writing and refuses anyone else with `error: not_maintainer`; send that `reply` and stop):

```bash
uv run rcparts deposit confirm --quote <ID>                    # "confirmar 3"  -> quote paid, member told "pago confirmado"
uv run rcparts deposit reject --quote <ID> --reason "<motivo>" # "rechazar 3 el monto no coincide" -> member asked for a new receipt
uv run rcparts deposit list                                    # "comprobantes pendientes" (add --status submitted)
```

Only paid quotes and self-orders with a tracking number go into the daily order batch.

## Self-order tracking number

After `quote accept --self-order`, the member buys the part themselves and ships it to the US address. The purchase only counts once they send the store's tracking number.

- When a member sends a tracking number (or a message that contains one: "ya lo compré, el tracking es 1Z…", "9400 1000 …", "fedex 1234…"), run:
  ```bash
  uv run rcparts tracking submit --text "<the member's message, as written>"
  ```
  The command finds the number, recognises the carrier (UPS, USPS, FedEx, DHL, Amazon), records it, moves the quote to in transit and sends the maintainer the number with a tracking link. Send `reply` verbatim.
- `error: ambiguous`: the member has several self-orders waiting; ask which one (the reply lists them) and run it again with `--quote <id>`.
- `error: no_tracking`: there was no number in the message; send `reply`.
- Never invent or correct a tracking number; pass the member's text as written.

## Rules

- The store search goes only to the whitelisted shop built into the command. Do not browse, search the web or quote any other store.
- Every number comes from the command. Do not estimate shipping, taxes, exchange rates or delivery times.
- A quote is not an order. Only `quote accept` after an explicit YES from the same member records it; a quote we order goes into the daily batch only after the maintainer confirms the deposit (`orders daily --send`, run by cron, never by you).
- Never say a payment is confirmed unless `deposit confirm` returned `ok: true`. Never generate, edit or describe a receipt for a member (`rcparts demo receipt` is a maintainer test tool).
- If the member asks for a part that is out of stock, say so with the command's `reply`; do not promise a restock date.
