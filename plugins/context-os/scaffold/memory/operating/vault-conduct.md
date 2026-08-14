# Vault Conduct

Rules for writing and editing vault files. Load this file before writing any vault file.

---

## Immutability rules

- `memory/raw/` and `memory/research/` are **append-only**. Files written there are never overwritten, edited, or deleted.
- `memory/sessions/` is **append-only**. Session captures are never overwritten.
- `memory/log/` is **append-only**. Log entries are never deleted.
- `inbox/`, `processed/`, and `outbox/` are **ephemeral**. Shared across all entities, not scoped per entity. Files there are processed, then archived or removed. Never cited directly.

## Writing rules

- Write in Australian English with Oxford commas.
- File and folder names: lowercase-hyphenated. No spaces. No TitleCase.
- Every folder must have an `index.md` that catalogues its contents.
- Every wiki article must have `## Key Takeaways` and a `**Source:**` line.
- Never invent claims. Flag unknowns in `## Open Questions`.
- Flag contradictions in `## Open Questions` and note the conflicting sources.
- Do not write content to `inbox/` files. Inbox files are operator-placed source material.

## Index maintenance

- When a new article is created in `memory/wiki/`, update the parent `index.md`.
- When a new domain or topic folder is created, create its `index.md` and update the parent `index.md`.
- Master wiki `index.md` is updated by the operator or by skills; do not auto-update it without surfacing the change.

## Frontmatter conventions

Wiki articles use YAML frontmatter with these standard fields:

```yaml
---
domain: <domain-folder-name>
topic: <topic-folder-name>
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
sources: [memory/raw/YYYY/MM/YYYY-MM-DD-slug.md]
---
```

Raw and research files use:

```yaml
---
origin: <original title or filename>
source_path: <original path or URL>
captured: YYYY-MM-DD
summary: <one-line summary>
type: <document | transcript | export | note | research>
domain: <best-fit domain>
---
```

## Prohibited patterns

- No em dashes or double-hyphens under any circumstances, no exceptions. 
- No empty section headings (headings with no content below them).
- No links to files that do not exist.
- Do not duplicate content across layers (index files summarise; articles hold content; raw sources hold evidence).

## Log format

Every vault operation appends to `memory/log/YYYY/MM/YYYY-MM-DD.md`. The date is carried by the file path and the daily stub header alone; entries do not repeat it:

```
HH:MM | <origin> | <operation> | <summary> | files: <comma-separated list>
```

`<origin>` is one of:
- `manual` — an explicitly composed entry: the `vault log` skill, or any call
  through the MCP server's `vault_log_append` tool (its manual-entry path always
  stamps `manual`, regardless of caller).
- `/agent` — a skill logging its own routine operation directly, in the no-MCP
  fallback path only.
- `<mcp-tool-name>` — stamped automatically by the MCP server itself when a
  `fs_*` tool call mutates a vault file. No skill writes this directly.

Example:
```
14:32 | agent | ingest | 2 file(s) processed | files: memory/raw/2026/2026-06/2026-06-19-article.md, memory/wiki/technology/ai/article.md
```
