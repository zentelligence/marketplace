# Prompts: Index

Prompt library. Reusable assets organised by task category. Every effective prompt goes here, not in notes, not in chat history.

## Structure

| Path | Purpose |
| --- | --- |
| [framework.md](registry/prompts/framework.md) | KERNEL+V principles and the standard XML prompt structure |
| [general/](registry/prompts/general/index.md) | Blank scaffold and uncategorised prompts |
| [writing/](registry/prompts/writing/index.md) | Emails, reports, documentation |
| [analysis/](registry/prompts/analysis/index.md) | Data interpretation, problem solving |
| [planning/](registry/prompts/planning/index.md) | Project scoping, task breakdown |
| [learning/](registry/prompts/learning/index.md) | Explaining concepts, skill development |
| [deciding/](registry/prompts/deciding/index.md) | Weighing options, identifying risks |

## Root-level files pending migration

These predate the category sub-folders. Migrate when next editing.

| File | Suggested category |
| ---- | ------------------ |

---

## Prompt file metadata standard

Every prompt file carries a YAML frontmatter block. Copy this header when creating a new prompt.

```yaml
---
title: Human-readable name for this prompt
category: writing | analysis | planning | learning | deciding | general
purpose: One sentence -- what task does this prompt accomplish?
status: draft | tested | refined
effectiveness: 1-5
time-saved: ~X min per use
updated: YYYY-MM-DD
---
```

**Field definitions**

| Field | Notes |
| --- | --- |
| `title` | Descriptive, scannable. Prefer "Verb + Object" form (e.g. "Draft Professional Email"). |
| `category` | Matches the sub-folder. One value only. |
| `purpose` | One sentence. What task does this solve? No fluff. |
| `status` | `draft` = written, untested. `tested` = used on real work at least once. `refined` = iterated and reliable. |
| `effectiveness` | 1, 5, updated after use. 1 = rarely useful. 5 = saves significant time every time. |
| `time-saved` | Rough estimate per use. Update when you have a feel for it. |
| `updated` | Date of last meaningful edit to the prompt text or metadata. |

**Body structure** (after frontmatter)

```markdown
# {{Title}}

[One-paragraph description: what this prompt is for and when to reach for it.]

## When to use

- {{Trigger scenario 1}}
- {{Trigger scenario 2}}

## How to customise

Replace bracketed placeholders. Key variables: {{VAR1}}, {{VAR2}}.

## Prompt

```xml
{{Prompt content here, use the KERNEL+V structure from framework.md for complex prompts}}
```

## Notes

Tips, traps, known variations. Optional. Remove if empty.
```

## Drafting a prompt

Run `prompt draft <description>` to have Claude build a new KERNEL+V prompt from a plain-language description. The draft is grounded in vault context (entity details, priorities, voice profile) retrieved via `vault-query`, and checked against the KERNEL+V table in `framework.md` before it's returned. Nothing is saved to the registry unless you confirm a category and slug afterwards; alternatively add `to <file-path>` (e.g. `prompt draft <description> to drafts/weekly-status.md`) to have the draft written straight to a file of your choosing instead, as a plain file, not a registry entry.

## Adding a prompt

Run `prompt create <slug> in <category>` to open a guided interview that writes a new prompt file (or confirms one produced by `prompt draft`). Manually, the same result:

1. Choose the right sub-folder (or `general/` if it doesn't fit a category).
2. Create `prompts/<category>/<slug>.md` using the header above and body structure.
3. Add a row to the sub-folder's `index.md`.
4. Add a row to this index if the category is new.

## Retrieving a prompt

Run `prompt <slug>` to look up and return a saved prompt's content. Run `prompt list [<category>]` to browse what's available.

## Rationale

Prompts are assets, not disposable queries. Every tested prompt represents time spent learning what works. Organising them compounds that investment. See [../memory/designs/prompts-roles-hats.md](../memory/designs/prompts-roles-hats.md) for the design argument.

Roles and hats shape how Claude reasons. Prompts shape what the operator sends. These are orthogonal concerns.
