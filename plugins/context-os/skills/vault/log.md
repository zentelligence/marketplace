# Skill: vault log

---

## Purpose

Append one manual entry to the shared daily operation log. This is the shared, routable entry point for recording an operation: every built-in vault skill's own "log" step (see `ingest.md`, `research.md`, `consolidate.md`, and so on) writes to the same file in the same format, and any other skill, including a custom, operator-authored one living outside this plugin, can call `vault log` instead of re-implementing the MCP-or-fallback logic itself.

Mirrors the manual entry path of the ContextOS MCP server's operation log (see `mcp__contextos__vault_log_append` and, upstream of that tool, the `OperationLog::append_manual` function in the `contextos-oplog` crate): a caller-authored entry, a set of touched files, and a trusted timestamp.

---

## Triggers

```
vault log <entry> | log <entry> | vault log <entry> files: <file1>, <file2>
```

Invoked directly by the operator, or by another skill via `Skill(vault, "log <entry> files: <paths>")` as its own logging step.

---

## Tools required

`Read`, `Edit`, `Bash`

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| `entry` | Router `args.entry`: the free-text summary of what happened | Yes |
| `files` | Router `args.files`: comma-separated vault-relative paths touched by the action | No |

If the router did not extract `entry` (bare `vault log` with nothing to say), ask the caller for the entry text before proceeding. Never write an empty entry.

---

## Outputs

| Output | Path |
| --- | --- |
| Log entry | `memory/log/YYYY/MM/YYYY-MM-DD.md` |

No other vault files are written by this skill.

---

## Flow

### Step 1: resolve entry and files

Use `args.entry` and `args.files` (comma-separated) from the router. If `files` was supplied, split on commas and trim whitespace from each path.

### Step 2: append

If MCP is available (see the vault router's MCP awareness section), call `mcp__contextos__vault_log_append` with `entry` set to the resolved entry text and `files` set to the resolved file list (empty array if none).

Otherwise, append directly to `memory/log/YYYY/MM/YYYY-MM-DD.md` following the format in `memory/operating/vault-conduct.md`. If this is the first entry of the day, create the file first with the daily stub from `memory/operating/vault-operations.md`:

```markdown
# Log: YYYY-MM-DD

```

Then append the entry line. The origin is always `manual`, matching what the MCP server's own manual-entry path stamps regardless of caller (see Purpose above); this is the one skill where that never varies. Render the files field in bracketed list notation so a downstream parser can distinguish it from the free-text entry unambiguously, even when the entry itself contains commas; omit the `files:` segment entirely when no files were given:

```
HH:MM | manual | log | <entry> | files: [<file1>, <file2>]
```

```
HH:MM | manual | log | <entry>
```

### Step 3: confirm

State the entry as written. Do not report anything further; this skill has no other side effects.

---

## Invariants

- `memory/log/` is append-only. Never edit or delete an existing line.
- Never write an empty entry.
- This skill only ever touches the current day's log file. It never reads or summarises historical log files.
