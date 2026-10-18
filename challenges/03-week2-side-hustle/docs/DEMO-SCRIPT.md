# PartsPaddock demo script

For the recording in the real test group. Reset first so ids and listings match this page:

```bash
scripts/demo-reset.sh --yes      # wipes only the rcparts tables and re-seeds from data/demo_catalog.json
```

Then send `/new` in the club group and in both private chats with the bot, so every chat starts with the current instructions.

## Who has what after the seed

Two clubs in Cuenca, two real members. Every listing is a real Xray part sold at Michael's RC Hobbies; the seed data is demo data and the post says so.

| Club | Member | HAVE (in the drawer) | NEED |
| --- | --- | --- | --- |
| RC Club Cuenca (the test group) | **Santiago** (maintainer) | #1 XRA302242 X4 aluminium steering block, new, $35 · #2 XRA308329 X4 XLP2 aluminium shock bodies (2), used, $17 · #3 XRA302842 X4 front anti-roll bar 1.2 mm, new, $12.97 · #4 XRA371201 X1 front bumper, used, $8 | #9 X1 aluminium body-post plate (no part number) |
| Cuenca Touring (no group; DMs only) | **Socio** | #5 XRA303187-H X4 rear lower arm, hard, left, new, $26.97 · #6 XRA371203-K X1 front wing, black, used, $22 · #7 XRA378102 X1 centre shock, new, $41.99 · #8 XRA372326 X1 2-dot camber bushings (2), used, $10 | #10 XRA302185-M X4 front lower arm, short, medium, left |

## Scenes to record (in this order)

| # | Who, where | Send | What should happen | Shows |
| --- | --- | --- | --- | --- |
| 1 | Santiago, **group** | `@bot I'm looking for a rear lower arm for the Xray X4` (English on purpose; the listing is in Spanish) | Group: one line, "match, I wrote to both". Both phones: a private match message naming the other member and "(de Cuenca Touring)" / "(de RC Club Cuenca)" | P2P across clubs and languages (glossary) |
| 2 | Socio, **DM** | `tengo una pletina portacarrocería de aluminio del Xray X1, usada, $15` | Confirmation, then a match with Santiago's NEED #9; both get the private match message | P2P text match (no part number) |
| 3 | Socio, **DM** | `quién tiene amortiguadores del X4?` | Lists Santiago's XLP2 shock bodies (#2), with no phone number | Search |
| 4 | Socio, **group** | `@bot busco la barra estabilizadora trasera XRA303843 del X4` | "Nobody in the club has it; want an import quote?" | No match → B2C |
| 5 | Socio, **group** | `@bot sí, cotízala` | Group: "Te envié la cotización por privado". Socio's DM: quote: store $12.47, 56 g as listed, 0.12 lb × $7/lb = $0.86, $13.33 if they order it, $14.83 if we order it (+12%, $1.50) | Every number from code |
| 6 | Socio, **DM** | `sí <id>` (the id is in the quote) | Deposit instructions: $14.83, reference RC-Q<id>, "send the PDF here" | Deposit gate |
| 7 | Socio, **DM** | send the PDF from `uv run rcparts demo receipt --quote <id>` (file `data/receipts/demo-RC-Q<id>.pdf`) as a document | Socio: "received, waiting for confirmation". Santiago: the PDF plus amount and reference checks and "confirmar <id> / rechazar <id>" | Human verification |
| 8 | Santiago, **DM** | `confirmar <id>` | Santiago: confirmed. Socio: "pago confirmado" | Only the maintainer can confirm |
| 9 | Santiago, **DM** | `cuánto me sale traer un kit Xray XB2D 2026?` then `lo compro yo <id>` | Quote for XRA320021 (found by name, no part number), then self-order instructions asking for the tracking number | Self-order branch; store search by name |
| 10 | Santiago, **DM** | `ya lo compré, el tracking es 1Z999AA10123456784` | "Tracking recorded (UPS)"; Santiago also gets the maintainer message with the UPS link | Tracking confirmation |
| 10b | Socio, **group** | `@bot mis pedidos` | Group one-liner; Socio's DM lists the paid anti-roll bar | "My purchases" |
| 11 | Socio, **DM** | `ya vendí el alerón delantero del X1` | Listing #6 closed as sold | Close by DM |
| 12 | (wait for the top of the hour, or run `scripts/install-cron.sh` timing) | — | Santiago gets the order batch: the paid stabiliser bar ($14.83) and the TAM54500 self-order (fee $1.74, tracking shown) | Order batch |

Optional, if time allows: Socio asks the group `@bot ya conseguí el brazo delantero, cierren mi búsqueda` to close NEED #10 ("found").

## Before you hit record

- **Blur:** phone numbers in the private match messages and the order batch, and the US forwarding address in quote replies.
- The bot answers in the group only when @mentioned.
- No "running tool…" messages should appear; if one does, stop and tell me.
- A turn takes 20 to 60 seconds; cut the waits in editing.
- The hourly batch runs at minute 0 (`ORDER_BATCH_SCHEDULE=0 * * * *`); set it back to daily (`0 18 * * *`) with `scripts/install-cron.sh` after recording.
- If WhatsApp disconnects: `scripts/gateway-restart.sh`.
