---
name: vault
description: "Personal knowledge vault operations. Router skill that dispatches to the appropriate sub-skill based on the operator's command."
---

Mandatory **first** step is to confirm global instructions were executed fully. 

GATE: run `source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null; echo "${CLAUDE_PLUGIN_ALLOW_SKILLS:-0}"`. Env vars set by one Bash invocation do not survive into the next, so this sources the persisted file rather than reading the plain variable. If it does not print `1`, run `session-start` directly, then re-run the check before proceeding.

# Vault: Router Skill

Routes vault commands to the appropriate sub-skill workflow. Load this file first, then load the relevant sub-skill based on the operator's command.

### MCP awareness

If a ContextOS MCP server is configured for this vault, prefer its tools over the equivalent Python script wherever the sub-skill flow below names one. Each affected step in a sub-skill names the specific `mcp__contextos__<tool>` to try first and the script to fall back to.

**Availability check** (once per skill invocation, not once per operation): attempt `mcp__contextos__vault_info`. If it succeeds, prefer named MCP tools for the rest of this invocation, falling back to that step's script only if a specific tool call errors or is not registered — tool catalogues vary by server version and vault configuration (for example, `query_semantic` requires `[vault.search] semantic = true` and errors otherwise if that is not configured). If `vault_info` is unavailable or errors, skip straight to running the scripts named below for the rest of this invocation.

Scripts with bespoke logic the MCP catalogue does not replicate (registry slug resolution in `registry_lookup.py`, the interview-driven scaffolding in `vault_scaffold.py`, shim generation in `agent_shim.py`, and the deterministic templating in `copy_markdown_to_raw.py` and `write_session_capture.py`) have no MCP equivalent and always run as scripts, MCP or not.

---

## Available commands

| Command | Sub-skill | Purpose |
| --- | --- | --- |
| `init` | [init.md](init.md) | First-run: scaffold structure and personalise vault |
| `ingest` | [ingest.md](ingest.md) | Process inbox files into memory |
| `research <topic>` | [research.md](research.md) | Web research → memory/research/ → wiki |
| `query <question>` | [query.md](query.md) | Answer questions from vault knowledge |
| `capture` | [capture.md](capture.md) | End-of-session memory capture |
| `consolidate` | [consolidate.md](consolidate.md) | Apply approved memory updates |
| `lint` | [lint.md](lint.md) | Audit wiki for quality issues |
| `distil-transcript` | [distil-transcript.md](distil-transcript.md) | Extract transcript to memory/raw/ |
| `log <entry>` | [log.md](log.md) | Append one manual entry to the daily operation log |
| `update` | [update.md](update.md) | Sync vault against the installed plugin after an upgrade |

---

## Routing

Run the router script with the operator's command:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_router.py --vault-root . --command "<operator command>"
```

The script returns JSON with:
- `skill`: matched skill name (or `null` if unrecognised)
- `skill_file`: path to the sub-skill file to load
- `args`: parsed arguments (e.g. `topic`, `question`)
- `preflight`: vault root and schema version checks
- `errors`: blocking errors; non-empty means do not proceed

If `errors` is non-empty, report them to the operator and stop.
If `skill` is matched, load `skill_file` and execute it, passing any `args`.
If `skill` is null but no preflight errors, ask one short clarifying question.

---

## Pre-flight checks (all skills)

Pre-flight is handled by `vault_router.py`. The script checks:

1. `CLAUDE.md` exists at the vault root.
2. Schema version in `CLAUDE.md` is 1.x or higher.

If either check fails, the `errors` field in the router output will be non-empty. Report the error and prompt the operator to run `vault init`.

---

## Invariants

- Never modify `memory/raw/` or `memory/research/` files. They are immutable after creation.
- Never write to inbox files. Inbox files are operator-placed source material.
- Always read `memory/operating/vault-conduct.md` before writing any vault file.
- Always append to the daily log file after each operation.
- Never apply memory updates directly during `vault capture`. Use `vault consolidate` for that.
