# Skill: vault capture

---

## Purpose

Write an end-of-session capture file that records decisions, outcomes, and proposed memory updates from the current session. Proposes updates only; never applies them. Application is handled by `/vault consolidate` after operator review.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Current conversation context | Session | Yes |
| `memory/sessions/index.md` | Vault | For naming context |
| `memory/operating/vault-conduct.md` | Vault | Yes |

---

## Outputs

| Output | Path |
| --- | --- |
| Session capture file | `memory/sessions/YYYY/MM/YYYY-MM-DD-HHMM-<slug>.md` |
| Coding lesson (optional) | `coding/YYYY/MM/YYYY-MM-DD-<agent>.md`, only if the vault has a `coding/` folder and the session produced one |

No other vault files are written during capture.

---

## Flow

### Step 1: pre-flight

Read `memory/operating/vault-conduct.md`.

### Step 2: synthesise session

From the current conversation, identify and record:

- **Decisions made**: explicit choices, directions chosen.
- **Outcomes produced**: artefacts created, tasks completed, problems resolved.
- **New knowledge**: anything learned that should enter the wiki.
- **Open threads**: unresolved questions, deferred decisions, follow-up tasks.
- **Proposed memory updates**: specific changes to existing vault files or new files to create.

### Step 3: capture coding lesson (if applicable)

If the session involved coding work and the vault has a top-level `coding/` folder (an optional personal extension, not part of the shipped schema; skip this step if the vault has no `coding/` folder), check whether the session produced a reusable lesson:

- project-agnostic enough to help future coding work,
- a concrete failure mode, fix pattern, tool behaviour, or verification lesson,
- specific enough to understand without rereading the whole session.

If so, append it with ContextOS MCP to `<vault>://coding/YYYY/MM/YYYY-MM-DD-<agent>.md` (`note_create` for a new day file, `fs_edit_file` to append to an existing one) using the format defined in `coding/index.md`. Reference this file's path in Step 4 below rather than inlining the lesson into the session capture.

### Step 4: write capture file

Write the capture with `mcp__contextos__note_create` to `<vault>://memory/sessions/YYYY/MM/YYYY-MM-DD-HHMM-<slug>.md`, using the operator's local date and time from `vault_info`'s `time_zone`. `note_create` never overwrites, so a refusal because the path exists means a capture with that name is already there: choose another slug rather than replacing it.

Pass these frontmatter fields as structured values:

| Field | Value |
| --- | --- |
| `type` | `session` |
| `session_type` | `planning`, `research`, `build`, `review`, or `other` |
| `primary_role` | The role in use, if any |
| `primary_hats` | List of hats used, if any |
| `entities_touched` | List of entity slugs |
| `projects_touched` | List of project slugs, if any |

Use this body, writing "None recorded." or "None proposed." under any empty section rather than omitting it:

```markdown
## Outcome

<one paragraph summary>

## Decisions

- <decision>

## Open threads

- <open thread>

## Memory updates proposed

### <target file path>

> <Proposed change: what to add, update, or remove>

## Coding lesson

- <coding/YYYY/MM/YYYY-MM-DD-<agent>.md, only if Step 3 recorded one; otherwise omit this section>
```

### Step 5: hand off

Tell the operator:
> "Session captured. Review the proposed updates in [capture file path], then run
> `/vault consolidate` when ready to apply them."

Do not apply any proposed updates during this step.

---

## Proposed memory update format

Each proposed update in the capture file should specify:
- The exact file path to update
- What to add, change, or remove
- Enough context for consolidate to act without re-reading the full session

Example:
```markdown
### memory/identity/who-am-i.md

> Add new goal under ## Current goals: "Complete ContextOS v1.0 plugin by 30 June 2026"

### memory/wiki/technology/ai-tools/claude.md

> Create new article on the vault's task delegation model. Source: this session.
> Key takeaways: [...]
```

---

## Invariants

- Never apply memory updates directly in this skill. Propose only.
- Never overwrite existing session capture files. Each capture is append-only per session.
- Do not write to any vault file except the session capture file and, where applicable, a new coding lesson file under `coding/`.
