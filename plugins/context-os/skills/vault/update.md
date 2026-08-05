# Skill: vault update

---

## Purpose

Bring an existing vault back in step with the installed context-os plugin after an upgrade. Adds anything new the current plugin version's scaffold introduces (directories, stub files, seed content) and refreshes plugin-shipped files the operator has not customised (registry index scaffolds, templates, `memory/designs/`, `scripts/utility/`). Files the operator has edited are never silently overwritten, they are reported for manual review instead.

Not a first-run skill. `vault init` scaffolds and personalises a fresh vault; `vault update` maintains an already-personalised one across plugin upgrades.

---

## Triggers

```
vault update | update vault | sync vault | apply plugin update
```

---

## Tools required

`Read`, `Bash`

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| `.contextos/state.json` | Vault (created on first run if absent) | No |
| Plugin's own `scripts/`, `scaffold/registry/`, `scaffold/templates/`, `scaffold/memory/designs/` | Installed plugin | Yes |

---

## Outputs

| Output | Notes |
| --- | --- |
| New directories and stub files | Anything the vault is missing that the current scaffold defines. Never overwrites existing files. |
| Refreshed shipped files | Only files unchanged by the operator since the last sync, where the plugin's copy has since changed. |
| `.contextos/state.json` | Updated plugin version, sync timestamp, and per-file hash baseline. |
| Conflict report | Files changed both by the operator and upstream; listed, not touched. |

---

## Flow

### Step 1: preview

Run a dry run first so the operator sees what would change before anything is written:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_update.py --vault-root . --dry-run --json
```

If the vault has no `.contextos/state.json` yet, this run establishes the baseline only; report that plainly, no files are refreshed on a vault's first `vault update` run (new directories and stub files are still added, since that reuses the same additive logic as `vault init`'s scaffold step and carries no risk of clobbering operator content).

### Step 2: confirm

Summarise for the operator: directories and files that would be added, files that would be refreshed (and are safe to, being unmodified since the last sync), and any conflicts (locally edited files where the plugin's copy has also changed). Ask before proceeding if there is anything to refresh or any conflicts to review; adding brand-new files needs no confirmation, since that step is purely additive and identical in risk to `vault init`'s scaffold step.

### Step 3: apply

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_update.py --vault-root . --json
```

### Step 4: report conflicts

For each conflicting file, tell the operator its path and that both they and the plugin have changed it since the last sync. Do not resolve conflicts automatically; offer to show a diff (`mcp__contextos__git_diff` if the vault is a git repository, otherwise read both versions) and let the operator decide whether to keep their version, take the plugin's, or merge manually.

### Step 5: log

If MCP is available, call `mcp__contextos__vault_log_append` with `entry: "update | synced to plugin v<version> | <n> added, <n> updated, <n> conflicts"` and `files` set to the added and updated paths. Otherwise, append to `memory/log/YYYY/MM/YYYY-MM-DD.md`:
```
HH:MM | agent | update | synced to plugin v<version> | <n> added, <n> updated, <n> conflicts | files: [<paths>]
```

---

## Invariants

- Never overwrite a file the operator has edited since the last sync. Report it as a conflict instead.
- A vault's first `vault update` run only baselines shipped-file hashes and adds what is missing; it never refreshes an existing file, since there is no prior baseline yet to tell an operator edit from an upstream one. 
- Never touch content outside the plugin's shipped, replaceable set: identity, entities, priorities, registry content the operator authored themselves, and `CLAUDE.md` are exclusively operator-owned and are never part of this skill's   refresh pass.
- `.contextos/` holds plugin bookkeeping only. Never store vault content there, and never treat it as citable vault knowledge.
