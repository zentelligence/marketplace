# ContextOS

Personal knowledge vault, powered by ContextOS.

---

## Quick start

| Step | Action |
| ---- | ------ |
| 1 | Install the ContextOS MCP server (`contextos`) and register this vault folder with it |
| 2 | Install ContextOS Web (`contextos-web`) and configure it with the ContextOS MCP server, named `contextos` |
| 3 | Add the ContextOS MCP server and this plugin to Claude Code or Codex |
| 4 | Run `/vault init` to complete first-run setup |
| 5 | Open this vault in Obsidian for human-readable access |

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
| `<entity>/` | per <entity> detail, organised however the operator prefers. |
| `registry/` | Prompts, roles, hats, agents, skills, apps, and workflows registry. |
| `standards/` | Referenceable operating standards. |
| `templates/` | Reusable file templates. |

---

## Vault operations

All vault operations are triggered via the `vault` skill command, which routes each to its workflow. Every operation reads and writes the vault through the ContextOS MCP server.

| Command | Purpose |
| ------- | ------- |
| `/vault init` | First-run setup. Run once on a fresh vault. |
| `/vault ingest` | Process files from inbox/ into memory. |
| `/vault research <topic>` | Research a topic and add findings to memory. |
| `/vault query <question>` | Answer a question using vault knowledge. |
| `/vault capture` | End-of-session capture. Proposes memory updates. |
| `/vault consolidate` | Apply approved memory updates from a capture file. |
| `/vault health` | Vault health from `doctor` plus knowledge quality. Runs unattended: fixes delegated to the librarian, decisions escalated to the chief of staff. |
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
| `/dispatch [<slug>]` | Work the task list: claim each actionable task assigned to an agent member and start that member's sub-agent on it, three at a time, until none remain. Built to run as a scheduled task from the member's workspace, `.contextos/workspaces/<slug>/`. |

Every vault ships with a generic V-sequence build set: the roles strategist, analyst, architect, engineer, and auditor, and the hats definer, planner, solver, critic, refiner, and synthesiser. Edit them freely; `/vault update` restores any that are missing.

ContextOS Web apps, workflows, and jobs are developed by their own skills. ContextOS Web serves the apps, and validates, schedules, and runs the workflows and jobs with no agent session involved:

| Command | Purpose |
| ------- | ------- |
| `/app list\|create\|update` | Build and maintain interactive apps in `registry/apps/`, verified on the ContextOS Web host. |
| `/workflow list\|create\|update` | Build and maintain workflows in `registry/workflows/`, or shared packages for the host's package store, proved with dry runs. |
| `/job list\|create\|update` | Author saved jobs, each owned by a team member, and take them through validation and a dry run to registration. The operator enables them. |

Agent definitions in `registry/agents/` are the source of truth; the `agent` skill reads a definition through ContextOS MCP each time it delegates. Plugin authors building on the agent skill: see [docs/01-agent-contract.md](docs/01-agent-contract.md) for the binding definition schema and invocation grammar.

---

## ContextOS MCP (required)

ContextOS Server (`contextos`) is the MCP server through which every skill reads and writes this vault: safe filesystem access, indexing, operation logging, Git recovery, and ranked or graph-based query, scoped to the vault roots it is configured with. It is distributed as a separate per-platform binary; installing this plugin does not install or register it.

The plugin works in Claude Code and Codex. Agent sessions usually reach the vault through the server rather than opening the vault as their working folder, so the server must be configured in each agent app you use. If a skill cannot reach it, the skill reports the error and stops; there is no fallback to writing vault files directly. `AGENTS.md` at the vault root holds the vault's instructions for every agent host, and `CLAUDE.md` imports it for Claude Code.

`/vault init`, `/vault update`, and `/vault health` do their deterministic work through the vault package, `contextos-vault`, which this plugin ships in `workflows/vault/`: the vault skill installs it into ContextOS Web from that folder and runs its `scaffold`, `update`, and `health` workflows as saved shared jobs with `contextos-web jobs run --shared`, so ContextOS Web's command line must be installed for those three commands. It is the one place a session runs ContextOS Web; everything else it runs on its own.

The `mcp-tools` skill (`/mcp-tools`) captures best practice for using the server's tools well: reading whole files with `fs_attach_file`, conflict-safe writes, choosing between the search tools, keyed records and frontmatter links, and what the server maintains on its own. It is informational, so it changes how tools are used, not what any vault command does.

---

## Obsidian usage

This vault is fully compatible with Obsidian. Recommended plugins:

- **Daily Notes** - for `journal/` integration
- **Unique Notes** - for `notes/` support
- **Templater** - for `templates/` support
- **Dataview** - for querying memory metadata

Obsidian advanced markdown, Bases, Canvases, mermaid diagrams are supported by ContextOS MCP tools, however use of `obsidian-skills` plugin is recommended to fully understand the supported file formats:

```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```

---

## Licence

Apache License 2.0. See [LICENSE](LICENSE).
