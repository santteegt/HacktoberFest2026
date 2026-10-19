---
type: tool
title: "Tiger Data"
description: "Managed Postgres with TimescaleDB, pgvector and BM25 search (Tiger Cloud); a $100 prize category."
tags: [tools]
timestamp: "2026-10-18T00:00:00Z"
---

## Definition

Tiger Cloud is managed PostgreSQL with TimescaleDB hypertables, continuous aggregates, columnar compression and retention policies.

## Key Points

- Docs [docs]: hypertables, continuous aggregates, compression up to 95%, pgvector, BM25 via pg_textsearch; free 30-day trial without a card; paid tiers shown from about $30 to $36 per month.
- Report: pgvectorscale and pgai are open source; a free plan (beta) exists. The pages fetched did not mention pgvectorscale, pgai or an MCP server [unverified].
- Fits: time-series logs of one person's life (sleep, symptoms, spending, sensors); pairs with TabPFN.
- First-hand (Week 2): Postgres 18.6 with TimescaleDB 2.30.2 on a free service; `vector`, `pg_trgm`, `pg_textsearch` and `unaccent` all available. Used as the listings and orders database with full-text matching plus `pg_trgm` and `unaccent`; Tiger MCP (`tiger mcp start`) loaded in a Hermes profile with only `db_query` enabled, which needs the service id in every call.
- First-hand: `tiger db connection-string --with-password` returns the URL with the keyring password; a saved URL without the password fails with "no password supplied".

## Related Concepts

- [TabPFN](tabpfn.md)
- [MongoDB Atlas](mongodb-atlas.md)
- [Partner tools catalog](partner-tools-catalog.md)
- [Cognee](cognee.md)
- [Week 2 challenge: Side Hustle](week2-challenge-side-hustle.md)

## Sources

- [Partner tools feature catalog](sources/partner-tools-feature-catalog.md)
- [Retrospective: Week 2 Side Hustle (PartsPaddock)](sources/retrospective-week2-side-hustle.md)
