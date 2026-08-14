# Vault Decisions

Decision-recording process for the knowledge substrate itself: schema, conventions, structure, and process. One file per decision, in `memory/decisions/`, never edited to remove or rewrite prior content, only superseded. When a schema or convention changes, the new rule applies from the next operation immediately; content written under the old rule is recorded in the entry's migration backlog rather than silently perpetuated or bulk-rewritten.

As shipped, this register is used for decisions about how the vault itself works: schema, conventions, structure, and process. Business and life decisions default instead to tasks (`#decision-pending`) in [active-tasks.md](active-tasks.md), and questions awaiting information default to [open-questions.md](open-questions.md). That division is this vault's as-built convention, not an enforced boundary: an individual deployment is free to route business or life decisions through this same mechanism if that suits the operator better. Resolving a question does not automatically produce a decision here; see [open-questions.md#relationship-to-decisions](open-questions.md#relationship-to-decisions) for how the two registers relate.

## Where decisions live

- **File:** `memory/decisions/<id>-<slug>.md`, one file per decision, lowercase-hyphenated (e.g. `vd-001-one-file-per-decision-or-question.md`).
- **Template:** `templates/registry-decision.md`.
- **Flat index:** `memory/decisions/index.md` catalogues every decision as a table row; update it in the same edit that adds or supersedes a file.
- **Obsidian Base:** `memory/decisions.base` provides live table views (all decisions, adopted only, superseded only) built from each file's frontmatter. It reads the files under `memory/decisions/`; nothing in it needs manual upkeep when a decision is added, only when a view or filter itself changes.

## Frontmatter

```yaml
---
id: VD-{{NNN}}
date: {{YYYY-MM-DD}}
status: adopted | superseded
applies_to: [{{directories, file types, or operations governed}}]
superseded_by: {{VD-{{NNN}} or blank}}
---
```

## Body sections

```markdown
## Context

{{The situation or problem that forced a choice}}

## Options considered

{{Alternatives weighed, with the trade-off that settled it}}

## Decision

{{The rule now in force, stated precisely enough to apply without this entry's context}}

## Migration backlog

{{Existing non-compliant content, migrated opportunistically when next touched, or "none"}}

## Recorded in

{{Spec or standard file updated to carry the rule, e.g. memory/wiki/index.md, a standards/ file}}
```

IDs are sequential (VD-001, VD-002, ...) and never reused. Superseding a decision creates a new file; the old file's frontmatter is updated (`status: superseded`, `superseded_by: <new id>`), its body content untouched. Add every new or superseded decision to `memory/decisions/index.md`'s table.

---

*Decisions predating this file live where they were made; backfill as VD entries only if a decision needs to be cited or revisited.*
