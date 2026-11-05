---
name: vault
description: "Routes a ContextOS vault command to its sub-skill: init (first-run setup or quick pass), ingest (inbox to memory), research TOPIC (web research to memory/research, wiki), query QUESTION (answer from vault knowledge), capture (end-of-session capture), consolidate (apply approved updates), health (unattended doctor and knowledge-quality check; fixes go to the librarian, decisions to the chief of staff), distil-transcript (transcript to memory/raw), log ENTRY (append op-log line), update (sync after plugin upgrade). Fires on explicit `/vault COMMAND` invocations and on conversational vault-memory requests, e.g. 'what do I know about X', 'process the inbox', 'check the vault's health', 'save this session', 'log that I did X', 'sync the vault after updating the plugin'. Does not fire for defining or invoking a role, hat, agent, or prompt (`SLUG:role`, `SLUG:hat`, `SLUG:agent`, `prompt draft/create/list`; owned by those sibling skills), or for web search, coding, or file tasks outside vault content."
license: Apache-2.0
when_to_use: "Trigger phrases without the word 'vault': 'check memory', 'look up in memory', 'apply the approved memory updates', 'log that <entry>', 'sync/update the vault against the plugin'."
user-invocable: true
disable-model-invocation: false
argument-hint: "<init [quick]|ingest|research <topic>|query <question>|capture|consolidate|health|distil-transcript|log <entry>|update>"
arguments: ["command"]
---

# Vault: Router Skill

Routes vault commands to the sub-skill that carries them out. Load this file first, then load only the sub-skill the command needs.

---

## Before any command

ContextOS vaults are reached through the ContextOS MCP server (`mcp__contextos__*`). The session's working folder is usually not the vault, so never assume it is, and never read or write vault files with the host's own file tools.

1. **Confirm the server.** Call `mcp__contextos__vault_info` once per invocation. If the tool is not available, or it fails, tell the operator that ContextOS MCP is required and is not reachable, quote the error, and stop. There is no fallback.
2. **Choose the vault.** From `vault_info`'s `vaults`:
   - Exactly one: use it.
   - Several: use the one the operator named. If they did not name one, list them and ask. Never choose the first by default.
   - None: for `init`, tell the operator to register the vault folder with ContextOS MCP first (see the ContextOS documentation), then stop. For any other command, say no vault is configured and stop.
   Address every file in that vault as `<vault>://<path>`, where `<vault>` is its configured name.
3. **Read the vault's instructions.** Before writing anything, read `<vault>://AGENTS.md` and `<vault>://memory/operating/vault-conduct.md` once in this session (`init` reads them after it has scaffolded a new vault). Follow them.
4. **Handle every result.** If a tool returns an error, a conflict, or warnings, report it plainly. Never retry a refused write by another route, and never claim an operation completed when part of it failed; say which part.

The [mcp-tools](../mcp-tools/SKILL.md) skill is the guide to choosing and using the ContextOS tools. Load it whenever a step needs more than the tool it names.

### Resolving a registry slug

The role, hat, prompt, and agent skills resolve a slug (`critic:role`, `critic:agent`, `prompt weekly-status`) the same way the server projects agents and skills into Claude Code and Codex, so a slug always names the same definition whichever vault is active:

1. Take the vaults from `vault_info`'s `vaults`, in the order it lists them. That is the operator's configuration order. Never put the active or chosen vault first, and never reorder.
2. In each vault in turn, call `mcp__contextos__fs_get_file_info` on `<vault>://registry/<type>/<slug>.md`, then, except for agents, on `<vault>://registry/<type>/<slug>/SKILL.md`. An agent is only ever `registry/agents/<slug>.md`, the one form the server projects, so the lookup and the hosts always agree. The first path that exists is the definition's `file`, and the first vault that has one wins. Stop at the first found; do not compare it with later vaults. A prompt lives in a category folder, so its path is `registry/prompts/<category>/<slug>.md`.
3. If no vault has the slug, list `registry/<type>/` in every vault with `mcp__contextos__fs_list_directory` and report the available slugs across all vaults, each slug once, with the vault that would supply it (the first vault in order that holds it).
4. Never read a definition with the host's own file tools, even when the host has a copy of it. Agents and skills are projected into the host's folders by the server, and those copies are not the source.

Creating a definition is the one step that uses the vault the operator chose (step 2 of Before any command). Before writing, resolve the slug as above; if an earlier vault than the chosen one already defines it, warn the operator that the earlier vault's definition wins every lookup and every host projection, so the new one will be shadowed, and let them choose another slug or vault before writing.

---

## Available commands

| Command | Sub-skill | Purpose |
| --- | --- | --- |
| `init` | [init.md](init.md) | First-run: scaffold structure and personalise the vault (`init quick` for a fast-start pass) |
| `ingest [files]` | [ingest.md](ingest.md) | Process inbox files into memory |
| `research <topic>` | [research.md](research.md) | Web research → memory/research/ → wiki |
| `query <question>` | [query.md](query.md) | Answer questions from vault knowledge |
| `capture` | [capture.md](capture.md) | End-of-session memory capture |
| `consolidate` | [consolidate.md](consolidate.md) | Apply approved memory updates |
| `health` | [health.md](health.md) | Vault health from `doctor` and knowledge quality, run unattended, with fixes delegated to the librarian and decisions escalated to the chief of staff |
| `distil-transcript [files]` | [distil-transcript.md](distil-transcript.md) | Extract a transcript to memory/raw/ |
| `log <entry>` | [log.md](log.md) | Append one manual entry to the operation log |
| `update` | [update.md](update.md) | Sync the vault against the installed plugin after an upgrade |

---

## Routing

Take the command from the declared `command` argument (everything after `/vault`), or from the operator's own words when the skill fired conversationally.

1. Match it to one row of the table above. Conversational requests map by intent: a question about what the vault knows is `query`, "process the inbox" is `ingest`, "audit", "lint", or "health check" is `health`, "save this session" is `capture`, "apply the approved updates" is `consolidate`, "log that ..." is `log`, and "sync after updating the plugin" is `update`.
2. Extract the command's arguments: file paths for `ingest` and `distil-transcript`, the topic for `research`, the question for `query`, the entry text for `log`, and `quick` for `init`.
3. If no row matches, or two do, ask one short clarifying question.
4. Load the matched sub-skill and carry it out with those arguments.

---

## The vault package

`init`, `update`, and `health` run their deterministic work as the vault package's saved shared jobs, through ContextOS Web's command line; [package.md](package.md) covers installing, registering, and running them. No vault command runs a plugin script.

---

## Invariants

- Every vault read and write goes through ContextOS MCP. Never fall back to the host's own file tools.
- Never modify `memory/raw/` or `memory/research/` files. They are immutable after creation.
- Never write to inbox files. Inbox files are operator-placed source material.
- Never apply memory updates during `/vault capture`. Use `/vault consolidate` for that.
- ContextOS MCP maintains every folder's `index.md`, the operation log, and Git commits for its own writes. Do not rebuild indexes after your own writes; record a `vault_log_append` summary at the end of an operation only where the sub-skill asks for one.
