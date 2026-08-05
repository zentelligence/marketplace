# ContextOS

Personal knowledge vault, powered by ContextOS.

---

## Quick start

| Step | Action |
| ---- | ------ |
| 1 | Open this vault in Obsidian for human-readable access |
| 2 | Open this vault in Claude Cowork for AI-operated access |
| 3 | Run `vault init` to complete first-run setup |
| 4 | After init, paste the block from `memory/operating/global-instructions.md` into Cowork Settings → Edit Global Instructions |

---

## Structure

| Folder | Purpose |
| ------ | ------- |
| `.contextos/` | Plugin bookkeeping (synced version, file hashes). Not vault content. |
| `journal/YYYY/MM/` | Daily notes. Obsidian-facing. Not authoritative. |
| `memory/` | All referenceable knowledge. Entry point: `memory/index.md`. |
| `memory/identity/` | Who the operator is. |
| `memory/log/YYYY/MM/` | Activity log. Append-only. `YYYY-MM-DD.md` |
| `memory/operating/` | How the vault operates. Conduct rules, log format, priorities. |
| `memory/raw/YYYY/MM/` | Processed source extracts. Immutable. `YYYY-MM-DD-<slug>.md` |
| `memory/research/YYYY/MM/` | AI-discovered sources. Immutable. `YYYY-MM-DD-<slug>.md` |
| `memory/sessions/YYYY/MM/` | Per-session captures. Append-only. `YYYY-MM-DD-<slug>.md` |
| `memory/wiki/` | Multi-level (3 minimum). Compiled topical knowledge. Organised by domain and topic. |
| `notes/` | Scratch notes. Obsidian-facing. Not authoritative. |
| `inbox/` | Drop zone for inbound files, shared across all entities. Ephemeral. |
| `outbox/` | Drop zone for outbound files, shared across all entities. Ephemeral. |
| `processed/` | Post-ingestion archive, shared across all entities. Ephemeral. |
| `<entity>/` | per <entity> detail (e.g. `projects/`). |
| `registry/` | Prompts, roles, hats, agents, scripts, and skills registry. |
| `standards/` | Referenceable operating standards. |
| `templates/` | Reusable file templates. |

---

## Vault operations

All vault operations are triggered via the `vault` skill command routed to appropriate workflow detail. Some operations are support by ContextOS MCP server where available, or Python scripts as a fallback. 

| Command | Purpose |
| ------- | ------- |
| `/vault init` | First-run setup. Run once on a fresh vault. |
| `/vault ingest` | Process files from inbox/ into memory. |
| `/vault research <topic>` | Research a topic and add findings to memory. |
| `/vault query <question>` | Answer a question using vault knowledge. |
| `/vault capture` | End-of-session capture. Proposes memory updates. |
| `/vault consolidate` | Apply approved memory updates from a capture file. |
| `/vault lint` | Audit wiki quality. Report only. |
| `/vault distil-transcript` | Extract a transcript to memory/raw/. |
| `/vault log <entry>` | Append one manual entry to the daily operation log. |
| `/vault update` | After a plugin upgrade. Add new scaffold content, refresh unmodified shipped files. |

Registry operations run inline in any prompt:

| Command | Purpose |
| ------- | ------- |
| `<slug>:role` | Adopt a role's cognitive posture for the session. |
| `/role create <slug>` | Define a new operator role in `registry/roles/`. |
| `<slug>:hat` | Activate a hat's thinking mode for the current task. |
| `/hat create <slug>` | Define a new operator hat in `registry/hats/`. |
| `<slug>:agent` | Delegate the task to an operator agent, run as a sub-agent. |
| `/agent create <slug>` | Define a new operator agent in `registry/agents/`. |

Agent definitions in `registry/agents/` are the source of truth; a generated shim in `.claude/agents/` makes each one harness-discoverable and is regenerated on drift. Plugin authors building on the agent skill: see [docs/01-agent-contract.md](docs/01-agent-contract.md) for the binding definition schema and invocation grammar.

---

## ContextOS MCP (optional)

ContextOS Server (`contextos`) is an optional MCP server that operates this vault directly: safe filesystem access, indexing, operation logging, Git recovery, and ranked or graph-based query, all scoped to this vault's root. It is distributed as a separate per-platform binary; installing this plugin does not install or register it.

If it is configured in Claude Desktop (for Claude Cowork access) or Claude Code's MCP settings against this vault, every vault skill automatically prefers its tools over the equivalent Python script, falling back to the script for anything the server does not cover or is not currently reachable for. Nothing above needs to change to take advantage of it, and nothing breaks without it: the vault operates exactly as described in this README either way. Configuring the server against a vault root is a manual step; this plugin does not automate it.

---

## Obsidian usage

This vault is fully compatible with Obsidian. Recommended plugins:

- **Daily Notes** - for `journal/` integration
- **Unique Notes** - for `notes/` support
- **Templater** - for `templates/` support
- **Dataview** - for querying memory metadata

Obsidian advanced markdown, Bases, Canvases, mermaid diagrams are supported by ContextOS MCP.
