---
id: VD-001
date: 2026-08-07
status: adopted
applies_to: [memory/decisions/, memory/questions/, memory/operating/vault-decisions.md, memory/operating/open-questions.md, memory/decisions.base, memory/questions.base]
superseded_by:
---

# VD-001: Decisions and questions are one file per record, with a companion Base

## Context

Vault-schema decisions and open questions both need a durable record that can be filtered, sorted, and cited without being deleted, relocated, or rewritten when their state changes (adopted or superseded; open or resolved). A single accumulating file per register, with the record's history moved between sections in place, was the original design for both.

## Options considered

- **Single accumulating file per register**, entries appended in place, moved between an open/active section and a resolved/superseded section. Simple, but every filter or sort has to be done by eye, and the file only grows.
- **Delete or archive a record once it is resolved or superseded.** Loses the audit trail of what was decided or asked, when, and why.
- **One file per record, status carried in frontmatter, the file never deleted or physically relocated, paired with an Obsidian Base for live filtered and sorted views.** Chosen: keeps the "never lose history" property of the original design, while making the register queryable without a script.

## Decision

Both registers use the same shape. `memory/decisions/<id>-<slug>.md` and `memory/questions/<slug>.md`: one file per record, lowercase-hyphenated. A record's status changes in its own frontmatter only (`status`, and for decisions `superseded_by`; for questions `resolved` and `decision`); the file itself is never deleted, archived, or moved. Each register keeps a plain-Markdown `index.md` as the flat, non-Obsidian fallback, and gains a companion Obsidian Base (`memory/decisions.base`, `memory/questions.base`) providing live table views over that frontmatter.

The two registers stay distinct. A question is a gap in information; a decision is a commitment. Resolving a question does not automatically create a decision: most resolved questions carry no `decision` reference, and a decision file never needs to name the question that prompted it.

## Migration backlog

None. Both registers were empty of real records at the time of this decision.

## Recorded in

`memory/operating/vault-decisions.md` and `memory/operating/open-questions.md`.
