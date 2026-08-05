# Skill: vault consolidate

---

## Purpose

Apply approved memory updates from session capture files. This is the second half of the capture cycle: `vault capture` proposes, `vault consolidate` applies. The operator reviews and approves before consolidate runs.

---

## Triggers

```
vault consolidate | consolidate | apply updates | apply memory updates | consolidate memory
```

---

## Tools required

`Read`, `Write`, `Edit`

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Session capture file(s) | `memory/sessions/YYYY/MM/` | Yes |
| `memory/operating/vault-conduct.md` | Vault | Yes |
| Target vault files | Various | Per proposed updates |

---

## Outputs

| Output | Notes |
| --- | --- |
| Updated vault files | Per each approved proposed update |
| Updated index.md files | At every level with new content |
| Marked capture file | Consolidation applied note appended |
| Log entry | `memory/log/YYYY/MM/YYYY-MM-DD.md` |

---

## Flow

### Step 1: pre-flight

1. Read `memory/operating/vault-conduct.md`.
2. Identify the capture file(s) to apply. If not specified, find the most recent unapplied capture in `memory/sessions/` (no "Consolidation applied:" footer).
3. Read the capture file(s) in full.
4. If no `## Memory updates proposed` section, or all updates already applied, report and stop.

### Step 2: operator confirmation

Present a summary of proposed updates. Ask the operator to confirm which to apply.

Default assumption: all proposed updates are approved unless the operator says otherwise. If the operator is explicitly triggering consolidate after reviewing, proceed without re-listing.

### Step 3: apply updates

For each approved proposed update:

1. Read the target file.
2. Apply the change: add, update, or remove content as specified. If MCP is available, prefer `mcp__contextos__fs_edit_file` for exact-match body edits and `mcp__contextos__frontmatter_update` for frontmatter-only changes, over the harness's raw `Read`/`Write`/`Edit`, for the same conflict-detection and atomic write guarantees. Fall back to `Write`/`Edit` if MCP is unavailable or a specific call errors.
3. If the change creates a new wiki article, update the index. If MCP is available, call `mcp__contextos__vault_index_rebuild` with `path: "memory/wiki/<domain>/<topic>"`. Otherwise, run the index updater:
   ```bash
   session-start >/dev/null 2>&1
   source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
   python $CONTEXT_OS_PLUGIN_ROOT/scripts/update_wiki_index.py \
     --vault-root . \
     --touched memory/wiki/<domain>/<topic>/<article>.md
   ```
4. If the change updates an existing article, preserve all sections not mentioned in the proposed update.
5. If a change conflicts with existing content, flag it and ask the operator before writing.

### Step 4: mark capture as applied

Append to the bottom of the capture file:

```markdown
---

**Consolidation applied:** YYYY-MM-DD HH:MM. Updates applied: [list]. Updates deferred: [list if any].
```

### Step 5: log

If MCP is available, call `mcp__contextos__vault_log_append` with `entry: "consolidate | session: <capture-slug> | updates applied: <n>"` and `files` set to the list of updated files. Otherwise, append to `memory/log/YYYY/MM/YYYY-MM-DD.md`:
```
HH:MM | agent | consolidate | session: <capture-slug> | updates applied: <n> | files: [list]
```

---

## Invariants

- Never apply updates that were not proposed in a capture file without explicit operator instruction.
- Preserve all existing sections not mentioned in a proposed update.
- If a conflict is detected, flag it and ask before writing.
- Do not apply updates to `memory/raw/` or `memory/research/` (these are immutable).
