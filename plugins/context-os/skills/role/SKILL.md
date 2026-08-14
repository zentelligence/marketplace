---
name: role
description: "Loads a cognitive-posture role definition from `registry/roles/` in the vault registry and adopts it for the current session, or authors a new one. Fires only on the explicit inline trigger `<slug>:role` appearing anywhere in a prompt (e.g. 'As architect:role, evaluate this schema.', 'Acting as engineer:role, review this PR.'), or the explicit command `/role create <slug>` / `/role create <slug>` to define a new role. Does not fire for `<slug>:hat` or `<slug>:agent` (owned by the sibling hat and agent skills), for `prompt draft/create/list` (owned by the prompt skill), or for `/vault <command>` and vault-content requests (owned by the vault skill). Does not infer or auto-adopt a role from task phrasing, tone requests, or persona language alone ('act like a lawyer', 'be more concise') without the literal `:role` suffix naming a registry slug."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "create <slug>"
arguments: ["command"]
---

# Skill: role

Loads a role definition from `registry/roles/` and adopts its cognitive posture. Activated when the operator uses `<slug>:role` anywhere in their prompt. Also handles `/role create <slug>` to author new role definitions.

---

## MCP awareness

If a ContextOS MCP server is configured for this vault, the creation flow (Step 4) prefers its tools over the harness's raw `Write`/`Edit`, falling back automatically if MCP is unavailable. Check once per invocation: attempt `mcp__contextos__vault_info`; if it succeeds, prefer the named MCP tools per step below, falling back to `Write`/`Edit` only if a specific call errors. If `vault_info` is unavailable or errors, use `Write`/`Edit` throughout.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Role slug | Inline `<slug>:role` or `/role create <slug>` | Yes |
| `registry/roles/<slug>.md` | Vault registry | For activation |
| `registry/roles/index.md` | Vault registry | For available-roles listing |
| `memory/operating/vault-conduct.md` | Vault | For creation flow only |

---

## Outputs

| Output | Notes |
| --- | --- |
| Adopted cognitive posture | Applied in-session; no file written |
| Role-not-found report | Lists available roles and offers creation |
| New role file | `registry/roles/<slug>.md` (creation flow only) |

---

## Flow

### Step 1: extract slug

Extract the role slug from the trigger. Strip any preposition ("As ", "as a ", etc.) before the slug. Normalise to lowercase-hyphenated form (e.g. "Code Reviewer" becomes "code-reviewer").

Detect the trigger type:

- `<slug>:role` in a larger prompt → **activation flow** (Steps 2-3).
- `/role create <slug>` as a standalone command → **creation flow** (Step 4).

Run the lookup for either trigger:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/registry_lookup.py \
  --vault-root . \
  --type role \
  --slug "<slug>"
```

### Step 2: activation - role found

If `found` is true:

1. Read the role definition at `file`.
2. Adopt the posture defined in `## Cognitive Posture`. Internalise `## Prioritises`, `## Characteristic questions`, and `## Avoids`.
3. Do not narrate or quote the role definition back to the operator. Simply apply it.
4. The adopted role applies for the remainder of the current session unless the operator explicitly switches to another role via a new `<slug>:role` trigger.
5. Proceed with the operator's task.

### Step 3: activation - role not found

If `found` is false:

1. Report to the operator:
   > "No role definition found for `<slug>`. Available roles: [list from `available`, or 'none yet'].
   > Run `/role create <slug>` to define a new one, or continue without a role definition."
2. Ask whether to proceed without a role, use the closest available one, or create a new one.

### Step 4: creation flow

When the operator requests `/role create <slug>`:

1. Read `memory/operating/vault-conduct.md`.
2. Check whether `registry/roles/<slug>.md` already exists. If so, confirm before overwriting.
3. Interview the operator sequentially (wait for each answer):
   - `"Display name: what is the full display name for this role? (e.g. 'Architect', 'Code Reviewer')"`
   - `"Cognitive posture: in 2-3 sentences, how does this role reason and what does it prioritise over other concerns?"`
   - `"Prioritises: list 3-5 things this role puts first."`
   - `"Characteristic questions: 3-5 questions this role always asks when engaging with a task."`
   - `"Avoids: what does this role actively resist or deprioritise?"`
4. Check whether `templates/registry-role.md` exists in the vault. If it does, read it and use its content as the template, substituting the interview answers from Step 3 into its placeholders by matching section headings. If the custom template contains a section this skill has no interview answer for, leave its placeholder in place and flag it to the operator in the confirmation message (Step 7) rather than inventing content. If `templates/registry-role.md` does not exist, use the fallback template below verbatim. Write `registry/roles/<slug>.md` with the resulting content. The role template carries no frontmatter block, so prefer `mcp__contextos__fs_write_file` with the full templated content when MCP is available; otherwise use the `Write` tool directly.
5. Add a row to `registry/roles/index.md`: `| [<Display Name>](<slug>.md) | <slug> | <one-line cognitive signature> |`  If MCP is available, prefer `mcp__contextos__fs_edit_file` anchored on the table's last existing row; otherwise use the `Edit` tool.
6. Append to the daily log. If MCP is available, call `mcp__contextos__vault_log_append` with `entry: "role create | Created role definition: <slug>"` and `files: ["registry/roles/<slug>.md"]`. Otherwise, append to `memory/log/YYYY/MM/YYYY-MM-DD.md`:
   ```
   HH:MM | agent | role create | Created role definition: <slug> | files: registry/roles/<slug>.md
   ```
7. Confirm to the operator:
   > "Role `<slug>` created at `registry/roles/<slug>.md`. Use `<slug>:role` in any future prompt to activate it."

---

## Role file template (fallback)

Used only when `templates/registry-role.md` is not present in the vault.

```markdown
# Role: <Display Name>

## Cognitive Posture

<2-3 sentences defining how this role reasons and what it prioritises.>

## Prioritises

- <item>
- <item>
- <item>

## Characteristic questions

- <question>
- <question>
- <question>

## Avoids

- <pattern or approach this role resists>
- <pattern or approach this role resists>
```

---

## Invariants

- Activate only on explicit `<slug>:role` trigger. Never auto-activate from task keywords.
- Do not narrate or surface the role definition to the operator after adoption.
- The adopted role is session-scoped: it persists until a new `<slug>:role` trigger replaces it.
- Never invent role content. If a slug is not found, report it and ask.
- Creation writes only `registry/roles/<slug>.md` and updates `registry/roles/index.md`. No other files.
