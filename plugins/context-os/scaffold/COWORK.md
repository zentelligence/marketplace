# {{OperatorName}}'s ContextOS

Personal knowledge vault. Read at the start of every Cowork session.

---

## Vault structure

```
<vault>/
├── CLAUDE.md                  Vault operating schema. This file.
├── README.md                  Navigation and setup guide.
├── .contextos/                Plugin bookkeeping (state.json: synced version, file hashes). Never vault content.
│
├── journal/                   Daily notes. Obsidian-facing. Not authoritative.
│
├── memory/
│   ├── index.md               Entry point. Token-efficient map of all memory.
│   ├── glossary.md            Common terms, nicknames, and abbreviations.
│   ├── designs/               Design decisions, artefacts, and roadmaps.
│   ├── identity/              Who the operator is.
│   │   ├── identity.md        Core identity: name, location, values, interests.
│   │   ├── who-am-i.md        Compact self-description for Claude Settings.
│   │   └── voice-profile.md   Messaging themes and on-brand examples.
│   ├── insights/              Zettelkasten-style atomic claims and relations. One file per insight.
│   ├── log/                   Append-only operation log.
│   ├── operating/             How the vault operates.
│   │   ├── vault-conduct.md   Rules for writing vault files. Load before writing.
│   │   ├── vault-operations.md  Log format and operation index.
│   │   ├── rhythm.md           Planning horizon names, scope, and status taxonomy.
│   │   ├── current-priorities.md  Current-period outcomes and non-negotiables per horizon.
│   │   └── global-instructions.md  Comprehensive, self-contained Cowork paste block.
│   ├── entities/              Entities overviews and summary tracking.
│   ├── raw/                   Processed source extracts (immutable).
│   ├── research/              AI-discovered sources (immutable).
│   ├── sessions/              Per-session captures (append-only).
│   └── wiki/                  Compiled topical knowledge. Multi-level structure.
│
├── notes/                     Scratch notes. Obsidian-facing. Not authoritative.
|
├── inbox/                     Drop zone for inbound files.
├── processed/                 Avoid re-processing files.
├── outbox/                    Drop zone for outbound files.
│
├── <entity>/                  <entity>-specific files.
│
├── registry/                  Operator-curated prompts, roles, agents, and skills.
│   ├── agents/                Operator agent definitions. Run as sub-agents via <slug>:agent.
│   ├── hats/                  Invoke via "<slug>:hat" usage in a prompt
│   ├── prompts/
│   ├── roles/                 Invoke via "<slug>:role" usage in a prompt
│   ├── scripts/
│   └── skills/                
│
├── standards/                 Writing and engineering standards.
└── templates/                 Reusable file templates.
```

---

## Operations

Vault management operations are triggered via the `vault` skill command routed to appropriate workflow detail. Load only the one needed. Some operations are support by ContextOS MCP server where available, or Python scripts as a fallback.

| Command | When |
| --- | --- |
| `/vault init` | First-run setup. Scaffolds the full structure and personalises vault files. |
| `/vault ingest [files]` | Files in inbox/, or as specified → memory/raw/ → wiki. |
| `/vault research <topic>` | Research a topic. Web search → memory/research/ → wiki. |
| `/vault query <question>` | Answer any question from vault knowledge. **Always use this before navigating memory/wiki/ manually.** |
| `/vault capture` | End of any meaningful session. Record decisions, outcomes, proposed updates. |
| `/vault consolidate` | After reviewing a capture file. Apply approved memory updates. |
| `/vault lint` | Periodic quality audit. Report only, no edits. |
| `/vault distil transcript [files]` | Process a conversational transcript to memory/raw/. |
| `/vault log <entry>` | Append one manual entry to the daily operation log. |
| `/vault update` | After a plugin upgrade. Adds new scaffold content, refreshes unmodified shipped files. |

Registry operations run inline in any prompt:

| Command | Purpose |
| ------- | ------- |
| `<slug>:role` | Adopt a role's cognitive posture for the session. |
| `/role create <slug>` | Define a new operator role in `registry/roles/`. |
| `<slug>:hat` | Activate a hat's thinking mode for the current task. |
| `/hat create <slug>` | Define a new operator hat in `registry/hats/`. |
| `<slug>:agent` | Delegate the task to an operator agent, run as a sub-agent. |
| `/agent create <slug>` | Define a new operator agent in `registry/agents/`. |

---

## ContextOS MCP (optional)

The ContextOS MCP server (`mcp__contextos__*`) may be configured to operate vaults directly: safe filesystem access, indexing, operation logging, Git recovery, and ranked or graph-based query. If configured, plugin skills prefer its tools over equivalent Python script. Operations fall back to the script for anything the server does not cover or is not currently reachable for. Native direct filesystem operations are last resort as defined file frontmatter and structures maintain vault integrity. 

---

## Obsidian usage

This vault is fully compatible with Obsidian. Recommended Obsidian plugins:

- **Daily Notes** - for `journal/` integration
- **Unique Notes** - for `notes/` support
- **Templater** - for `templates/` support
- **Dataview** - for querying memory metadata

---

## Conventions

- **Australian English spelling, grammar, and punctuation. Oxford comma.** Always.
- **No em dashes or double-hyphens.** 
- **File and folder names are lowercase-hyphenated.** No spaces. No TitleCase.
- **Every folder has an index.md** that catalogues its contents with one-line summaries.
- **Relative-path markdown links** for internal references.
- **Citations required.** Every wiki article has a `**Source:**` line. Every claim traces to a source or is flagged in `## Open Questions`.
- **`## Key Takeaways` required** on every wiki article. Bullets, scannable.
- **Bullets over paragraphs** in memory files. Long narrative goes in a `## Details` section.
- **Never invent claims.** Ask questions and flag residual gaps in `## Open Questions`.
- **Wiki is multi-level.** Structure: `memory/wiki/<domain>/<topic>/article.md` minimum.
- **Inbox is ephemeral.** Process to memory/raw/ first; never cite inbox files directly.
- **Immutable sources.** `memory/raw/` and `memory/research/` are append-only. Never overwrite.
- **Token discipline.** Index files summarise. Articles hold content. Raw sources hold evidence. Start at indexes, descend to specific articles.
- **Word wrap** none for markdown or 120 characters for code files, never 80.
