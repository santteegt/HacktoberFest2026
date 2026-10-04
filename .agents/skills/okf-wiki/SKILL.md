---
name: okf-wiki
description: "Bootstrap and incrementally maintain a topic-focused knowledge base ('second brain') for ANY project as a directory of markdown files conformant with Google's Open Knowledge Format (OKF) v0.1 — the generalized, config-driven counterpart to a project-local 'LLM wiki' pattern. Use this whenever the user wants to build a personal or team knowledge base from a pile of source documents (articles, papers, notes, transcripts, PDFs-as-markdown) and have an agent read them once and keep a structured, cross-linked, queryable wiki current over time — not just re-search the same files on every question. Trigger on requests like 'help me build a knowledge base for X', 'turn these notes into a wiki', 'I want a second brain for this research', 'set up something like NotebookLM but that an agent maintains', or 'ingest these sources and keep a wiki updated' — even if the user doesn't say 'OKF' or 'wiki-builder' by name. Also use this to lint/health-check an existing OKF-style vault for broken conformance, stale hashes, or orphan pages."
trigger: /okf-wiki
---

# /okf-wiki

Turn a folder of raw source documents into a persistent, incrementally-maintained knowledge base — a directory of interlinked markdown pages with YAML frontmatter, conformant by default with the [Open Knowledge Format (OKF) v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). This is the portable, project-agnostic version of the "LLM wiki" pattern: point it at any pile of sources for any topic, and it builds and maintains the wiki the same way, regardless of domain.

## What this is for

Most RAG setups re-derive knowledge from scratch on every question. This skill instead builds a **compounding artifact**: each source is read once, synthesized into cross-linked pages, and the wiki gets richer with every new source and question. You curate sources and ask questions; the agent does the ingesting, cross-referencing, and bookkeeping.

Every vault this skill produces satisfies OKF's only mandatory rule (every page's frontmatter has a non-empty `type`) and carries OKF's recommended fields (`title`, `description`, `resource`, `tags`, `timestamp`) — which means any OKF-aware tool (a generic graph visualizer, another agent, a future version of this same skill) can read a vault built by this skill without special-casing it.

**Not what this is**: not a database, not a RAG/embedding pipeline, not a framework requiring an SDK. It's markdown files plus a lightweight procedure. If you can `cat` a file, you can read the output.

## Trigger

`/okf-wiki` — run with no arguments to process all new/changed sources in the current project's configured vault (see Step 0 for how the vault is located/initialized).

## When to use

- Starting a new topic-focused knowledge base for a project (research deep-dive, competitive analysis, course notes, team wiki, book companion notes, personal tracking — any domain).
- After adding new files to an existing vault's `raw/` directory, or editing one already ingested.
- Periodically, to lint/health-check an existing vault (see Lint procedure).

## Relationship to project-local wiki-builder skills

Some projects (e.g. the AI×Web3 School repo) have their own project-local wiki-builder skill, hand-tuned to that project's specific taxonomy and already containing months of content. **Do not touch or reference those** — a project-local skill of the same trigger shadows this global one for that project, which is correct and intentional. Use this skill for projects that don't already have their own wiki-building skill.

## Step 0 — Locate or initialize the vault

1. Look for a vault config at `<vault-root>/wiki/.wiki-config.json`, where `<vault-root>` defaults to `knowledge-base/<project-name>/` relative to the current working directory, but ask the user if it's ambiguous or if they've mentioned a different location.
2. **If `.wiki-config.json` exists**: read it, use its values for everything below, skip to Step 1.
3. **If it doesn't exist (first run for this vault)**: this is a new vault. Do not silently invent a taxonomy — ask the user briefly for:
   - Vault/project name
   - What kind of pages this vault will have (`type` vocabulary) — default to `["concept", "topic", "source"]` if they don't have opinions
   - Rough domain groupings for organizing the index later (e.g. for a research vault: `["methods", "findings", "background"]`) — this can start small and grow
   - Whether they want OKF path-links (default, recommended for portability/GitHub-rendering) or Obsidian-style `[[wikilinks]]` (only if they specifically use Obsidian and prefer that convention)

   Then create the directory structure and write the config:
   ```
   <vault-root>/
   ├── AGENTS.md
   ├── CLAUDE.md -> AGENTS.md
   ├── raw/
   └── wiki/
       ├── .wiki-config.json
       └── sources/
   ```
   ```json
   {
     "okf_version": "0.1",
     "vault_name": "<name>",
     "type_vocabulary": ["concept", "topic", "source"],
     "domain_tags": ["<domain-a>", "<domain-b>"],
     "subtopic_tags": [],
     "link_style": "okf-path"
   }
   ```

   Also write `<vault-root>/AGENTS.md` from `references/agents-template.md`, filling in `<Vault Name>`. This isn't consumed by the ingest procedure itself (that's this skill file's job) — it's a portable, tool-agnostic pointer so a human or a different agent harness landing in this vault cold knows the `okf-wiki` skill is required and where to look for it (default `~/.agents/skills/okf-wiki`, falling back to the current harness's own skills folder, e.g. `~/.claude/skills/okf-wiki` for Claude Code). Symlink `CLAUDE.md -> AGENTS.md` next to it so Claude Code picks up the same content automatically.

   Tell the user where you created everything and that they should drop source files into `raw/` before the next run.

## Step 1 — Load existing hashes

Read `wiki/.hashes.json`. If missing, treat as `{}`.

## Step 2 — Detect changes

For each `*.md` file in `raw/`, compute SHA256:
```bash
shasum -a 256 "<vault-root>/raw/<filename>"
```
Compare against the stored hash. Skip files with matching hashes. Queue new/changed files for processing. If nothing is queued, report that the vault is up to date and stop here — don't rewrite `index.md`/`log.md` for no reason.

## Step 3 — Process each queued source

For each source file to process:

**3a. Create/overwrite the source summary page** at `wiki/sources/<slug>.md` (`<slug>` = lowercase filename, spaces → hyphens, no extension):
```yaml
---
type: source
title: "<Source Title>"
description: "<one sentence summarizing what this source covers>"
resource: "raw/<filename>.md"
tags: [<2–5 topic tags, drawn from the vault's domain_tags where they fit, plus specific subtopic tags as needed>]
timestamp: "<YYYY-MM-DD>T00:00:00Z"
source_hash: "sha256:<hash>"
---
```
(`resource` — not `source_file` — is OKF's standard field name for a URI/path to the underlying asset. `source_hash` is a useful non-OKF extra field OKF explicitly allows producers to add; consumers must preserve it.)

Body: `## Summary` (3–5 sentences), `## Key Concepts` (bulleted list, path-linked to concept pages — see 3c), `## Notable Points` (2–3 significant claims or quotes from the source).

**3b. Extract concepts/topics** — identify distinct concepts, entities, or named ideas in the source. For each:
- Check `wiki/index.md` for an existing page.
- If it exists: read it, integrate the new information, bump any tracking field (e.g. a `source_count` extra field, if the vault uses one), add a link to this new source in its `## Sources` section.
- If it's new, create `wiki/<concept-slug>.md`:
  ```yaml
  ---
  type: concept          # or whatever type from the vault's type_vocabulary fits best
  title: "<Concept Name>"
  description: "<one sentence — reuse/trim the ## Definition opening line, don't author it separately>"
  tags: [<domain + subtopic tags>]
  timestamp: "<YYYY-MM-DD>T00:00:00Z"
  ---
  ```
  Body: `## Definition` (1–3 sentences), `## Key Points` (bulleted list), `## Related Concepts` (path-links to co-appearing concepts), `## Sources` (path-links to source pages covering this concept).

**3c. Add links** — use OKF markdown path-links for every cross-reference: `[Concept Name](concept-slug.md)` for a page in `wiki/`, `[Source Title](sources/source-slug.md)` for a source page (unless the vault's config specifies `"link_style": "wikilink"`, in which case use `[[concept-slug]]` throughout instead — pick one style per vault and stay consistent, don't mix within a single vault unless you have a specific, stated reason). Ensure no orphan pages: every new page should be linked from at least one other page.

**3d. Reconcile new domain tags** — while tagging sources/concepts in 3a/3b, you'll sometimes hit a topic that doesn't cleanly fit any entry already in the vault's `domain_tags`. Don't silently force it into the closest existing tag, and don't leave it untagged at the domain level either — tag it provisionally with whatever's closest for now, and keep a running list of these "doesn't quite fit" candidates as you go through the queue.

Once every queued source has been processed, if that candidate list is non-empty, ask the user **once** (batched, not per-concept — interrupting mid-ingest for every mismatch would be disruptive): something like "This ingest touched topics that don't cleanly fit your current domain tags — `<candidate-a>`, `<candidate-b>`. Add any of these as new domain tags?" For whichever ones they approve, append them to `domain_tags` in `wiki/.wiki-config.json` and retag the affected pages to use the new domain tag instead of the provisional one. If nothing was queued this run (Step 2 found no changes), skip this sub-step entirely.

This keeps `domain_tags` an honest, current reflection of the vault's real taxonomy instead of a static list frozen at whatever the user guessed during Step 0's init questions.

## Step 4 — Update `wiki/index.md`

Rewrite the index. It carries root frontmatter declaring `okf_version` (the one place OKF permits frontmatter on an index file), then bulleted, described links grouped by section:
```markdown
---
okf_version: "0.1"
---

# <Vault Name> — Wiki Index

_Last updated: YYYY-MM-DD — N pages_

## Topics
- [Topic Title](topic-slug.md) — one-line description

## Sources
- [Source Title](sources/source-slug.md) — one-line description

## Concepts — <Domain A>
- [Concept Title](concept-slug.md) — one-line description

## Concepts — <Domain B>
...
```
Group Concepts by the vault's `domain_tags` from config (including any just added in 3d). If the vault only has a handful of concepts so far, don't force domain subsections yet — a single flat `## Concepts` list is fine until there's enough content to make grouping worthwhile.

## Step 5 — Append to `wiki/log.md`

Append one entry per processed source. This log is **oldest-first, append-only** (a deliberate deviation from OKF's own newest-first example convention — append-only keeps diffs small and conflict-free in a git-tracked vault):
```markdown
## [YYYY-MM-DD] ingest | <Source Title>

- **Ingest**: <Source Title> processed from `raw/<filename>.md`
- Source: `raw/<filename>.md`
- Hash: `sha256:<hash>`
- Pages created/updated: N
- New concepts: <comma-separated list>
```

## Step 6 — Save updated hashes

Write `wiki/.hashes.json` with entries for **all** raw files (not just the ones just processed), so the full state is always reflected:
```json
{
  "raw/<filename>.md": "sha256:<hash>",
  ...
}
```

## Lint procedure

Run on request, or periodically, to health-check a vault. Two modes:

**Base (OKF conformance — always applicable to any OKF vault, including ones this skill didn't build):**
- Every non-reserved `.md` file has parseable YAML frontmatter with a non-empty `type`.
- `index.md`/`log.md` carry no frontmatter except `index.md`'s optional root `okf_version` block.
- Broken cross-links are informational only — OKF explicitly tolerates them by design; never report them as errors.

**Strict (opt-in, for vaults that want stronger hygiene — enable via `"strict_lint": true` in `.wiki-config.json`):**
- Stale `.hashes.json` entries: recompute live SHA256 for each `raw/*.md` and compare to the stored hash.
- Orphan pages: every page should be linked from at least one other page.
- Tag drift: report any tag used on exactly one page as a possible one-off worth consolidating — informational, not an error, since tag vocabularies are expected to grow organically.

## Model guidance

Run with **Sonnet**, not Haiku — building a wiki requires synthesis, cross-referencing, and multi-step reasoning across source files, not templated single-shot generation.

## Verification

After running, confirm:
- `wiki/.hashes.json` has one entry per raw file.
- `wiki/index.md` has root `okf_version` frontmatter and lists every current page.
- Re-running immediately with no new/changed raw files reports "up to date" and makes no edits.
- No orphan pages (every page linked from at least one other).
