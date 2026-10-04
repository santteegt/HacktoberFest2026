# <Vault Name> — Knowledge Base

A topic-focused knowledge base built and maintained by an AI agent, following the "LLM wiki" pattern and conformant with Google's [Open Knowledge Format (OKF) v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

## Requirement

**Any agent working in this vault must use the `okf-wiki` skill** to ingest sources and maintain `wiki/` — don't hand-write pages, invent frontmatter fields, or edit `wiki/index.md`/`wiki/log.md` ad hoc. The skill's procedure is the schema-of-record for this vault, not this file.

Default cross-tool location: `~/.agents/skills/okf-wiki`

If that path doesn't exist, check your harness's own skills directory instead — e.g. Claude Code stores it at `~/.claude/skills/okf-wiki`. Different agent harnesses keep skills/tools in different conventional locations; look for `okf-wiki` in whichever one your current harness uses before assuming it's unavailable.

## Structure

- `raw/` — immutable source files. The agent reads these but never edits them.
- `wiki/` — agent-maintained pages:
  - `index.md` — catalog of every page, with root `okf_version` frontmatter
  - `log.md` — append-only, oldest-first ingest history
  - `sources/` — one summary page per raw source
  - one page per concept/topic
  - `.wiki-config.json` — this vault's taxonomy (type vocabulary, domain tags, link style)
  - `.hashes.json` — sha256 per raw file, for incremental re-ingest

## Origin

This vault follows the "LLM wiki" pattern: instead of re-searching the same documents on every question, an agent reads each source once and folds it into a persistent, cross-linked wiki that compounds with every new source and question. The `okf-wiki` skill carries out the full ingest → index → log procedure and keeps every page OKF-conformant.
