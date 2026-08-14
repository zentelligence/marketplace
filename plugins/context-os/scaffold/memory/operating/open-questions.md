# Open Questions

Decision-recording process for questions: gaps in information the vault cannot yet close. As shipped, a question lands here whenever a gap cannot be closed in the session that finds it: a source read only in part, a claim that lacks a primary source, an ambiguity only the operator can resolve, or speculation from `memory/research/` awaiting confirmation. Unlike [vault-decisions.md](vault-decisions.md), whose as-built scope is vault schema and process, this register's as-built scope already spans both: the vault's own operation and the content it holds. In-file `## Open Questions` sections in raw and research extracts acknowledge a gap at the point it's found; this register is where those gaps are tracked to resolution.

Not for decisions. A choice awaiting the operator's word is a `#decision-pending` task in [active-tasks.md](active-tasks.md). A structural or process choice, once made, is a decision in [../decisions/index.md](../decisions/index.md), not a question. A question belongs here when the missing piece is information, not commitment.

## Relationship to decisions

Most questions resolve with just an answer: no new rule, no schema change, nothing for `memory/decisions/` to record. Occasionally, resolving a question does prompt a decision, for example, an ambiguity about how a folder should be organised gets settled by adopting a convention. When that happens, the question's `decision` field records the resulting VD id; every other resolved question leaves it blank. The reverse link does not exist: a decision file does not need to name the question that prompted it, `applies_to` already states what the decision governs.

## Where questions live

- **File:** `memory/questions/<slug>.md`, one file per question, lowercase-hyphenated.
- **Template:** `templates/registry-question.md`.
- **Flat index:** `memory/questions/index.md` catalogues every question as a table row; update it in the same edit that adds or resolves a file.
- **Obsidian Base:** `memory/questions.base` provides live table views (all questions, open only, resolved only) built from each file's frontmatter. It reads the files under `memory/questions/`; nothing in it needs manual upkeep when a question is added, only when a view or filter itself changes.

## Frontmatter

```yaml
---
raised: {{YYYY-MM-DD}}
entity: {{#entity tag, or blank}}
status: open | resolved
blocks: {{what cannot proceed or be asserted until resolved, or "nothing"}}
resolution_path: {{primary source to read | research to run | operator to answer | external party}}
resolved: {{YYYY-MM-DD, blank while open}}
decision: {{VD-{{NNN}}, blank unless resolving this produced a decision}}
---
```

## Body sections

```markdown
## Question

{{The precise question, one or two sentences}}

## Answer

{{Filled in on resolution, with the source. Blank while status: open}}
```

On resolution: set `status: resolved`, `resolved` to the date, and fill in `## Answer`. The file is never deleted or moved, it accumulates in place the same way a superseded decision does; only its frontmatter and `## Answer` section change. Propagate the answer to every file that carried the gap before closing the operation. Add every new or resolved question to `memory/questions/index.md`'s table.

---

*Questions predating this file live where they were raised (e.g. inline `## Open Questions` sections); migrate them here only if a question needs to be tracked to resolution or cited.*
