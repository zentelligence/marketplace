---
name: vault
description: "Routes a ContextOS personal-knowledge-vault command to its matching sub-skill: init (first-run setup or quick pass), ingest (inbox → memory), research <topic> (web research → memory/research, wiki), query <question> (answer from vault knowledge), capture (end-of-session memory capture), consolidate (apply approved memory updates), lint (audit wiki quality), health (alias for lint), distil-transcript (transcript → memory/raw), log <entry> (append operation-log line), update (sync after plugin upgrade). Fires on explicit `/vault <command>` invocations and on conversational requests to read, write, or maintain the operator's own vault memory, e.g. 'what do I know about X', 'find sources on X', 'process the inbox', 'audit the vault', 'save/capture this session', 'log that I did X', 'sync the vault after updating the plugin'. Does not fire for defining or invoking a role, hat, agent, or prompt (`<slug>:role`, `<slug>:hat`, `<slug>:agent`, `prompt draft/create/list`; owned by the sibling role, hat, agent, and prompt skills); does not fire for general web search, coding, or file-system tasks external to vault content."
license: Apache-2.0
when_to_use: "Trigger phrases without the word 'vault': 'check memory', 'look up in memory', 'apply the approved memory updates', 'log that <entry>', 'sync/update the vault against the plugin'."
user-invocable: true
disable-model-invocation: false
argument-hint: "<init [quick]|ingest|research <topic>|query <question>|capture|consolidate|lint|distil-transcript|log <entry>|update>"
arguments: ["command"]
---

Mandatory **first** step is to confirm global instructions were executed fully. 

GATE: run `source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null; echo "${CLAUDE_PLUGIN_ALLOW_SKILLS:-0}"`. Env vars set by one Bash invocation do not survive into the next, so this sources the persisted file rather than reading the plain variable. If it does not print `1`, run `scripts/session-start` from the ContextOS plugin directory, then re-run the check before proceeding.

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
| `init` | [init.md](init.md) | First-run: scaffold structure and personalise vault (`init quick` for a fast-start pass) |
| `ingest [files]` | [ingest.md](ingest.md) | Process inbox files into memory |
| `research <topic>` | [research.md](research.md) | Web research → memory/research/ → wiki |
| `query <question>` | [query.md](query.md) | Answer questions from vault knowledge |
| `capture` | [capture.md](capture.md) | End-of-session memory capture |
| `consolidate` | [consolidate.md](consolidate.md) | Apply approved memory updates |
| `lint` | [lint.md](lint.md) | Audit wiki for quality issues |
| `distil-transcript [files]` | [distil-transcript.md](distil-transcript.md) | Extract transcript to memory/raw/ |
| `log <entry>` | [log.md](log.md) | Append one manual entry to the daily operation log |
| `update` | [update.md](update.md) | Sync vault against the installed plugin after an upgrade |

---

## Routing

Run the router script with the operator's command: the declared `command` argument (everything after `/vault` when invoked via slash syntax), or the operator's own words that triggered this skill when invoked conversationally with no explicit `/vault` prefix.

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_router.py --vault-root . --command "<operator command>"
```

The script returns JSON with:
- `skill`: matched skill name (or `null` if unrecognised)
- `skill_file`: path to the sub-skill file to load
- `args`: parsed arguments (e.g. `topic`, `question`)
- `preflight`: vault root check plus advisory plugin-sync status (`synced_plugin_version`, `current_plugin_version`, `update_recommended`)
- `errors`: blocking errors; non-empty means do not proceed
- `warnings`: non-blocking advisories (e.g. `/vault update` recommended)

If `errors` is non-empty, report them to the operator and stop.
If `skill` is matched, load `skill_file` and execute it, passing any `args`.
If `skill` is null but no preflight errors, ask one short clarifying question.
If `warnings` is non-empty, mention it to the operator once (e.g. "this vault is behind the installed plugin version; run `/vault update` when convenient") and proceed with the matched skill regardless — it is a nudge, not a gate.

---

## Pre-flight checks (all skills)

Pre-flight is handled by `vault_router.py`. The only hard-blocking check is:

1. `CLAUDE.md` exists at the vault root.

If that fails, the `errors` field in the router output will be non-empty. Report the error and prompt the operator to run `/vault init`. Plugin-sync status (whether `.contextos/state.json` is missing or behind the installed plugin's version) is advisory only, surfaced via `warnings`, since `/vault update`'s scaffold step is additive and skills do not depend on a specific plugin version to function.

---

## Invariants

- Never modify `memory/raw/` or `memory/research/` files. They are immutable after creation.
- Never write to inbox files. Inbox files are operator-placed source material.
- Always read `memory/operating/vault-conduct.md` before writing any vault file.
- Always append to the daily log file after each operation.
- Never apply memory updates directly during `/vault capture`. Use `/vault consolidate` for that.
