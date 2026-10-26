---
type: tool
title: "Tiger Data"
description: "Managed Postgres with TimescaleDB, pgvector and BM25 search (Tiger Cloud); a $100 prize category."
tags: [tools]
timestamp: "2026-10-25T00:00:00Z"
---

## Definition

Tiger Cloud is managed PostgreSQL with TimescaleDB hypertables, continuous aggregates, columnar compression and retention policies.

## Key Points

- Docs [docs]: hypertables, continuous aggregates, compression up to 95%, pgvector, BM25 via pg_textsearch; free 30-day trial without a card; paid tiers shown from about $30 to $36 per month.
- Report: pgvectorscale and pgai are open source; a free plan (beta) exists. The pages fetched did not mention pgvectorscale, pgai or an MCP server [unverified].
- Fits: time-series logs of one person's life (sleep, symptoms, spending, sensors); pairs with TabPFN.
- First-hand (Week 2): Postgres 18.6 with TimescaleDB 2.30.2 on a free service; `vector`, `pg_trgm`, `pg_textsearch` and `unaccent` all available. Used as the listings and orders database with full-text matching plus `pg_trgm` and `unaccent`; Tiger MCP (`tiger mcp start`) loaded in a Hermes profile with only `db_query` enabled, which needs the service id in every call.
- First-hand: `tiger db connection-string --with-password` returns the URL with the keyring password; a saved URL without the password fails with "no password supplied".
- First-hand (Week 3): a second free service held 9 tables (links, enrichment, triage, Valhalla, focus, cards, runs, events, reading picks) with a partial unique index for one reading pick per day. `tiger db uri --with-password` cannot read the keychain from a cron run while the session is locked; crons read the URL from an owner-only `.env` instead.

## Related Concepts

- [TabPFN](tabpfn.md)
- [MongoDB Atlas](mongodb-atlas.md)
- [Partner tools catalog](partner-tools-catalog.md)
- [Cognee](cognee.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)
- [Week 3 challenge: Slow and Steady](week3-challenge-slow-and-steady.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
- [Retrospective: Week 3 Slow and Steady (Skunkworks Sloth)](sources/retrospective-week3-slow-and-steady.md)
