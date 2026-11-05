# Vault Conduct

Rules for writing and editing vault files. Load this file before writing any vault file.

---

## Immutability rules

- `memory/raw/` and `memory/research/` are **append-only**. Files written there are never overwritten, edited, or deleted.
- `memory/sessions/` is **append-only**. Session captures are never overwritten.
- `memory/log/` is **append-only**. Log entries are never deleted.
- `memory/events/` is written only by the ContextOS MCP server. Record an event with `base_record_create` against `memory/events.base`, for a kind declared in `registry/events/`; every other write there is refused. By default `info` events are deleted after 90 days, and `warning` and `error` events are kept until deleted by hand.
- `memory/jobs/` holds run records written by ContextOS Web, which deletes a job's records once they pass its retention window (`[workflows] run_retention_days` in `web.toml`, 30 days by default). Never write there.
- `inbox/`, `processed/`, and `outbox/` are **ephemeral**. Shared across all entities, not scoped per entity. Files there are processed, then archived or removed. Never cited directly.

## Writing rules

- Write in Australian English with Oxford commas.
- File and folder names: lowercase-hyphenated. No spaces. No TitleCase.
- Every note has frontmatter. A wiki article or insight note lists every source it draws on in its frontmatter's `sources`, as vault paths; never in a `**Source:**` line in the body.
- Never invent claims. Raise an unknown as a question task (`base_record_create` against `memory/tasks.base`, `prefix: Q`), or, when it is about the vault itself, as a vault question (`memory/decisions.base`, `prefix: VQ`). Raise a contradiction the same way, naming the conflicting sources in the task.
- A note's `## Open Questions` section, when it has one, holds only links to those question and decision tasks and vault decisions and questions, never the questions themselves.
- Do not write content to `inbox/` files. Inbox files are operator-placed source material.
- `registry/instructions/global.md` is projected into every agent session, so it holds only the operator's standing profile and the rules every session follows, each section a condensed summary with a pointer to the file holding the detail. Never use it to track activity, progress, decisions, session notes, or history: those belong in tasks, session captures in `memory/sessions/`, the operation log, and the files its sections point to. Change it only when the standing profile or rules themselves change, and keep its XML-style sections.

## Folder indexes

- The ContextOS MCP server creates every folder's `index.md` and keeps the table between its `<!-- contextos:index:begin -->` and `<!-- contextos:index:end -->` markers current. Never create an `index.md`, and never add, edit, or remove rows in that table.
- A row's summary is the listed file's frontmatter `description` (or `summary`, then `excerpt`); for a folder, its own `index.md` frontmatter. Fill a note's `description` where its template has one, so it reads well in its folder's index.
- Text an operator writes outside the markers is theirs. Do not add to it unless asked.

## Templates

- A file in `templates/` always wins: any skill that writes one of the file types it covers checks for the matching template first, and uses its own built-in default only when the template is missing.

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

Insight notes use:

```yaml
---
status: proposed
created: YYYY-MM-DD
confidence: medium   # optional: low, medium, or high
related: []
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

ContextOS MCP appends every vault operation to `memory/log/YYYY/MM/YYYY-MM-DD.md`. Nothing else writes the log. The date is carried by the file path and the daily stub header alone; entries do not repeat it:

```
HH:MM | <origin> | <operation> | <summary> | files: <comma-separated list>
```

`<origin>` is one of:
- `manual`: an explicitly composed entry: the `vault log` skill, or any call
  through the MCP server's `vault_log_append` tool (its manual-entry path always
  stamps `manual`, regardless of caller).
- `<mcp-tool-name>`: stamped automatically by the MCP server itself when a
  tool call mutates a vault file. No skill writes this directly.

Example:
```
14:32 | manual | ingest | 2 file(s) processed | files: memory/raw/2026/2026-06/2026-06-19-article.md, memory/wiki/technology/ai/article.md
```
