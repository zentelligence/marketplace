# Questions: Index

One file per open question: a gap that cannot be closed in the session that finds it, whether about the vault's own schema and process or about vault content, a source read only in part, a claim that lacks a primary source, an ambiguity only the operator can resolve, or speculation from `memory/research/` awaiting confirmation. See [../operating/open-questions.md](../operating/open-questions.md) for the full entry format and the resolution rule.

Not every question resolves into a decision. A question is a gap in information; a decision is a commitment. When resolving a question does produce a vault decision, the question's `decision` field records the resulting [VD id](../decisions/index.md); most resolved questions carry no such field. See [../operating/open-questions.md#relationship-to-decisions](../operating/open-questions.md#relationship-to-decisions).

Not for decisions about how the vault works: those are [../decisions/index.md](../decisions/index.md). Not for business or life decisions: those are `#decision-pending` tasks in [../operating/active-tasks.md](../operating/active-tasks.md).

| Question | Status | Raised | Blocks |
| --- | --- | --- | --- |

## Browsing

- **In Obsidian:** open [../questions.base](../questions.base) for live table views (all questions, open only, resolved only), sorted and filtered from each file's frontmatter.
- **In plain Markdown:** the table above is the authoritative flat index; update it in the same edit that adds or resolves a question file.

## Adding a question

Copy `templates/registry-question.md` to `memory/questions/<slug>.md` (lowercase-hyphenated), fill it in, and add a row to the table above.
