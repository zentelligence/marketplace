---
name: role
description: "Loads a cognitive-posture role definition from `registry/roles/` in the vault registry and adopts it for the current session, or authors a new one. Fires only on the explicit inline trigger `SLUG:role` appearing anywhere in a prompt (e.g. 'As architect:role, evaluate this schema.', 'Acting as engineer:role, review this PR.'), or the explicit command `role create SLUG` / `/role create SLUG` to define a new role. Does not fire for `SLUG:hat` or `SLUG:agent` (owned by the sibling hat and agent skills), for `prompt draft/create/list` (owned by the prompt skill), or for `/vault COMMAND` and vault-content requests (owned by the vault skill). Does not infer or auto-adopt a role from task phrasing, tone requests, or persona language alone ('act like a lawyer', 'be more concise') without the literal `:role` suffix naming a registry slug."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "create <slug>"
arguments: ["command"]
---

# Skill: role

Loads a role definition from `registry/roles/` and adopts its cognitive posture. Activated when the operator uses `<slug>:role` anywhere in their prompt. Also handles `/role create <slug>` to author new role definitions.

---

## ContextOS MCP

This skill reads and writes the vault only through ContextOS MCP. Before the first lookup, follow steps 1 and 4 of the vault router's [Before any command](../vault/SKILL.md#before-any-command) section: confirm the server with `mcp__contextos__vault_info`, which also gives the vault order. A lookup searches every vault in that order and takes the first definition found, as [Resolving a registry slug](../vault/SKILL.md#resolving-a-registry-slug) sets out; only creation asks the operator to choose a vault (step 2). If the server is unavailable, report it and stop; never fall back to the host's own file tools. Paths below are addressed as `<vault>://...`.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Role slug | Inline `<slug>:role` or `/role create <slug>` | Yes |
| `registry/roles/<slug>.md` | Vault registry | For activation |
| `registry/roles/` | Vault registry | For available-roles listing: the `.md` files in the folder, never its server-managed `index.md` |
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

Resolve the slug through ContextOS MCP in configured vault order, as [Resolving a registry slug](../vault/SKILL.md#resolving-a-registry-slug) sets out: in each vault from `vault_info`, `<vault>://registry/roles/<slug>.md`, then `<vault>://registry/roles/<slug>/SKILL.md`, first found wins. The full `<vault>://` path found is the definition's `file` (`found` is true). If no vault has it, `found` is false: `available` is the role slugs across all vaults, each once, with the vault that would supply it. Never prefer the active vault over this order, and never use the host's own file tools.

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
   > "No role definition found for `<slug>`. Available roles: [list from `available`, each slug once with the vault that supplies it, or 'none yet'].
   > Run `/role create <slug>` to define a new one, or continue without a role definition."
2. Ask whether to proceed without a role, use the closest available one, or create a new one.

### Step 4: creation flow

When the operator requests `/role create <slug>`:

1. Choose the vault to write to (see step 2 below), then read that vault's `memory/operating/vault-conduct.md`.
2. Choose the vault to write to (step 2 of the vault router's Before any command; the operator's choice, never assumed). Resolve `<slug>` across all vaults in `vault_info` order as in Step 1. If it exists in the chosen vault, confirm before overwriting. If an earlier vault than the chosen one already defines it, warn the operator that the earlier vault's definition wins every lookup, so the new one would be shadowed, and ask whether to continue, choose another slug, or choose another vault.
3. Interview the operator sequentially (wait for each answer):
   - `"Display name: what is the full display name for this role? (e.g. 'Architect', 'Code Reviewer')"`
   - `"Cognitive posture: in 2-3 sentences, how does this role reason and what does it prioritise over other concerns?"`
   - `"Prioritises: list 3-5 things this role puts first."`
   - `"Characteristic questions: 3-5 questions this role always asks when engaging with a task."`
   - `"Avoids: what does this role actively resist or deprioritise?"`
4. Check whether `templates/registry-role.md` exists in the vault. If it does, read it and use its content as the template, substituting the interview answers from Step 3 into its placeholders by matching section headings. If the custom template contains a section this skill has no interview answer for, leave its placeholder in place and flag it to the operator in the confirmation message (Step 7) rather than inventing content. If `templates/registry-role.md` does not exist, use the fallback template below verbatim. Write `registry/roles/<slug>.md` with the resulting content. The role template carries no frontmatter block, so write the full templated content with `mcp__contextos__fs_write_file`.
5. Leave `registry/roles/index.md` alone: the ContextOS MCP server lists the new file in it.
6. Add a log summary: call `mcp__contextos__vault_log_append` with `entry: "role create | Created role definition: <slug>"` and `files: ["registry/roles/<slug>.md"]`.
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
- Creation writes only `registry/roles/<slug>.md`. No other files, and never an `index.md`.
