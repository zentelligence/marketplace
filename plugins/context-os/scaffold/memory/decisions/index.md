# Decisions: Index

One file per decision about how the vault itself works: schema, conventions, structure, and process, as shipped. Business and life decisions default instead to tasks (`#decision-pending`) in [../operating/active-tasks.md](../operating/active-tasks.md), and questions awaiting information default to [../operating/open-questions.md](../operating/open-questions.md), though an individual deployment may route differently. See [../operating/vault-decisions.md](../operating/vault-decisions.md) for the full entry format and the rules for adding, superseding, and citing a decision.

| ID | Date | Decision | Status |
| --- | --- | --- | --- |
| [VD-001](vd-001-one-file-per-decision-or-question.md) | 2026-08-07 | Decisions and questions are one file per record, with a companion Base | adopted |

## Browsing

- **In Obsidian:** open [../decisions.base](../decisions.base) for live table views (all decisions, adopted only, superseded only), sorted and filtered from each file's frontmatter.
- **In plain Markdown:** the table above is the authoritative flat index; update it in the same edit that adds or supersedes a decision file.

## Adding a decision

Copy `templates/registry-decision.md` to `memory/decisions/<id>-<slug>.md` (lowercase-hyphenated, e.g. `vd-002-example-slug.md`), fill it in, and add a row to the table above. IDs are sequential and never reused.
