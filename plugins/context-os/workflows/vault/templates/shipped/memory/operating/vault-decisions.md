# Vault Decisions and Questions

How the vault records decisions and questions about itself: its design, schema, conventions, structure, and operation. Both live in one register, `memory/decisions/`, one note per record, never deleted or moved. When a schema or convention changes, the new rule applies from the next operation; content written under the old rule is listed in the decision's migration backlog rather than silently perpetuated or bulk-rewritten.

## What belongs here, and what does not

| Record | Where |
| --- | --- |
| A decision about how the vault itself works | A `VD-` decision in `memory/decisions/` |
| A question about how the vault itself works, that cannot be closed in the session that finds it | A `VQ-` question in `memory/decisions/` |
| A decision about the operator's own work, entities, or affairs outside the vault | A decision task (`task_type: decision`) in [../tasks/index.md](../tasks/index.md) |
| A question about the operator's own work outside the vault | A question task (`task_type: question`) in [../tasks/index.md](../tasks/index.md) |
| A gap in vault content that needs work to close: a source read only in part, a claim without a primary source, research awaiting confirmation | A question task in [../tasks/index.md](../tasks/index.md), noted where it was found under that note's `## Open Questions` |

## Where records live

- **Notes:** `memory/decisions/`, one per record. Created with the contextos MCP `base_record_create` tool against `memory/decisions.base`, which assigns the id from `memory/decisions.md`: `prefix: VD` for a decision, `prefix: VQ` for a question. Ids are sequential within each series and never reused.
- **Templates:** `templates/registry-vault-decision.md` and `templates/registry-vault-question.md`. Each closes with its full field reference.
- **Flat index:** the ContextOS MCP server keeps `memory/decisions/index.md` listing every record; never edit it by hand.
- **Obsidian Base:** `memory/decisions.base` shows adopted decisions, open questions, superseded decisions, resolved questions, and every record. Nothing in it needs upkeep when a record is added.

## Decisions

A decision has `type: decision`, a `title`, the `date` it was made, `status` (`adopted` or `superseded`), `applies_to` (what it governs), and `superseded_by`. Its body records Context, Options considered, Decision, Migration backlog, and Recorded in. A decision is never edited to change what it said: superseding it creates a new decision, and the old one's frontmatter changes to `status: superseded` and `superseded_by` the new id, its body untouched.

## Questions

A question has `type: question`, a `title`, the date it was `created`, `status` (`open` or `resolved`), `blocks` (what cannot proceed until it is answered, or "nothing"), `resolution_path` (primary source to read, research to run, operator to answer, or external party), `resolved`, and `decision`. Its body records the Question and, on resolution, the Answer with its source. On resolution, set `status: resolved` and `resolved` to the date, fill in the Answer, and carry the answer into every file that held the gap.

Most questions resolve with an answer alone. When resolving one does produce a decision, the question's `decision` field names the resulting `VD-` id. A decision does not need to name the question that prompted it; its `applies_to` already says what it governs.
