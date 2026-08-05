# Vault Decisions

Decision log for the knowledge substrate itself: schema, conventions, structure, and process. One entry per decision, append-only, newest at the top of the log. When a schema or convention changes, the new rule applies from the next operation immediately; content written under the old rule is recorded in the entry's migration backlog rather than silently perpetuated or bulk-rewritten.

Scope: decisions about how the vault works. Business and life decisions are tasks (`#decision-pending`) in [active-tasks.md](active-tasks.md); questions awaiting information go to [open-questions.md](open-questions.md).

## Decision index

| ID | Date | Decision | Status |
| --- | --- | --- | --- |
| [VD-001](#vd-001-resolved-open-questions-accumulate-in-place) | 2026-07-18 | Resolved open questions accumulate in place | adopted |

## Entry format

```markdown
## VD-{{NNN}}: {{Decision title}}

- **Date:** {{YYYY-MM-DD}}
- **Status:** adopted | superseded by VD-{{NNN}}
- **Context:** {{The situation or problem that forced a choice}}
- **Options considered:** {{Alternatives weighed, with the trade-off that settled it}}
- **Decision:** {{The rule now in force, stated precisely enough to apply without this entry's context}}
- **Applies to:** {{Directories, file types, or operations governed}}
- **Migration backlog:** {{Existing non-compliant content, migrated opportunistically when next touched, or "none"}}
- **Recorded in:** {{Spec or standard file updated to carry the rule, e.g. memory/wiki/index.md, a standards/ file}}
```

IDs are sequential (VD-001, VD-002, ...) and never reused. Superseding a decision gets a new entry; the old entry's status is updated to point at it, content untouched. Add every entry to the decision index table.

---

## Log


---

*Decisions predating this file live where they were made (e.g. `memory/designs/insights-schema.md`, `memory/designs/migration-notes.md`); backfill as VD entries only if a decision needs to be cited or revisited.*
