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

If so, append it to `coding/YYYY/MM/YYYY-MM-DD-<agent>.md` using the format defined in `coding/index.md`. Reference this file's path in Step 4 below rather than inlining the lesson into the session capture.

### Step 4: write capture file

Use the capture script for consistent structure:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/write_session_capture.py \
  --vault-root . \
  --slug "<session-slug>" \
  --session-type "<planning|research|build|review|other>" \
  --primary-role "<role if applicable>" \
  --entities-touched "<entity slugs if applicable>" \
  --outcome "<one paragraph summary>" \
  --decision "<decision 1>" \
  --decision "<decision 2>" \
  --open-thread "<open thread 1>" \
  --memory-update "<proposed update 1>" \
  --coding-lesson-file "<coding/YYYY/MM/YYYY-MM-DD-<agent>.md, if Step 3 recorded one>"
```

The script writes to `memory/sessions/YYYY/MM/YYYY-MM-DD-HHMM-<slug>.md`. Omit `--coding-lesson-file` entirely if Step 3 did not apply or found nothing worth recording.

For any additional proposed memory updates with specific file paths and changes, append them to the `## Memory updates proposed` section in this format. If MCP is available, prefer `mcp__contextos__fs_edit_file` for this append (anchor on the section heading), falling back to the `Edit` tool if MCP is unavailable or the call errors:

```markdown
### [target file path]

> [Proposed change: what to add, update, or remove]
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

> Create new article on Claude Cowork plugin architecture. Source: this session.
> Key takeaways: [...]
```

---

## Invariants

- Never apply memory updates directly in this skill. Propose only.
- Never overwrite existing session capture files. Each capture is append-only per session.
- Do not write to any vault file except the session capture file and, where applicable, a new coding lesson file under `coding/`.
