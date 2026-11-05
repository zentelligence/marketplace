# {{OperatorName}}'s ContextOS

Personal knowledge vault, operated through the ContextOS MCP server. These are the vault's instructions for every agent session, in Claude Code and Codex alike. `CLAUDE.md` beside this file only imports it.

A session usually reaches this vault through ContextOS MCP rather than opening it as its working folder. Read this file through MCP before working in the vault, and address its files as `<vault>://<path>`, where `<vault>` is the vault's name in `vault_info`.

---

## Vault structure

```
<vault>/
├── AGENTS.md                  Vault instructions. This file.
├── CLAUDE.md                  One-line import of AGENTS.md for Claude Code.
├── README.md                  Navigation and setup guide.
├── .contextos/                Plugin and server bookkeeping (state.json: synced version, file hashes). Never vault content.
│   └── workspaces/            One working folder per agent member, for scheduled sessions (/dispatch). Never vault content.
│
├── journal/                   Daily notes. Obsidian-facing. Not authoritative.
│
├── memory/
│   ├── index.md               Entry point. Token-efficient map of all memory.
│   ├── glossary.md            Common terms, nicknames, and abbreviations.
│   ├── decisions/             Decisions and questions about the vault itself. One note per record.
│   ├── decisions.base         Live views of them; decisions.md beside it issues VD- and VQ- ids.
│   ├── designs/               Design decisions, artefacts, and roadmaps.
│   ├── identity/              Who the operator is.
│   │   ├── identity.md        Core identity: name, location, values, interests.
│   │   ├── who-am-i.md        Compact self-description.
│   │   ├── communication-style.md  How to communicate with the operator.
│   │   └── voice-profile.md   Messaging themes and on-brand examples.
│   ├── events/                Events written only by ContextOS MCP. Record one with base_record_create against events.base.
│   ├── events.base            Live event views; events.md beside it issues run ids.
│   ├── insights/              Zettelkasten-style atomic claims and relations. One file per insight.
│   ├── log/                   Append-only operation log, written by ContextOS MCP.
│   ├── operating/             How the vault and the operator operate.
│   │   ├── vault-conduct.md   Rules for writing vault files. Load before writing.
│   │   ├── vault-operations.md  Log format and operation index.
│   │   ├── quality-standards.md  Quality bar for every edit.
│   │   ├── autonomy-policy.md What may be done without the operator's sign-off.
│   │   ├── anti-patterns.md   Patterns to avoid in conduct and advice.
│   │   ├── rhythm.md          Planning horizon names, scope, and status taxonomy.
│   │   └── current-priorities.md  Current-period outcomes and non-negotiables per horizon.
│   ├── entities/              Entities overviews and summary tracking.
│   ├── raw/                   Processed source extracts (immutable).
│   ├── research/              AI-discovered sources (immutable).
│   ├── sessions/              Per-session captures (append-only).
│   ├── tasks/                 One note per task. Nested folders allowed. See Tasks below.
│   ├── tasks.base             Live task views; tasks.md beside it issues task ids.
│   └── wiki/                  Compiled topical knowledge. Multi-level structure.
│
├── notes/                     Scratch notes. Obsidian-facing. Not authoritative.
│
├── inbox/                     Drop zone for inbound files.
├── processed/                 Avoid re-processing files.
├── outbox/                    Drop zone for outbound files.
│
├── <entity>/                  <entity>-specific files.
│
├── registry/                  Operator-curated prompts, roles, hats, agents, instructions, skills, apps, event kinds, and workflows.
│   ├── agents/                Operator agent definitions. Delegate to one with <slug>:agent.
│   ├── apps/                  ContextOS Web apps.
│   ├── events/                Definitions of the event kinds a client may record.
│   ├── hats/                  Invoke with <slug>:hat in a prompt.
│   ├── instructions/          global.md: the orientation the server places in every agent host.
│   ├── prompts/               Reusable prompt templates.
│   ├── roles/                 Invoke with <slug>:role in a prompt.
│   ├── skills/
│   └── workflows/             ContextOS Web workflows, each with its saved jobs.
│
├── standards/                 Writing and engineering standards.
└── templates/                 Reusable file templates.
```

---

## Working in this vault

- **ContextOS MCP is the only route to vault files.** Read and write through the `mcp__contextos__*` tools, never the host's own file tools. If a tool is unavailable or fails, report the error and stop. The `mcp-tools` skill is the guide to choosing and using them.
- **The server maintains** every folder's managed `index.md` block, the search indexes, the operation log, and Git commits for its own writes. Do not repeat that work by hand.
- **Before acting for the operator**, read `memory/operating/autonomy-policy.md`, `memory/identity/communication-style.md`, and `memory/operating/anti-patterns.md`. For anything external-facing, also read `memory/identity/voice-profile.md`. Before editing existing files, read `memory/operating/quality-standards.md`.
- **Who the operator is and what matters now** live in `memory/identity/` and `memory/operating/current-priorities.md`. Read them when the work depends on them; do not guess.

---

## Operations

Vault operations run through the `vault` skill, which routes each command to its workflow. Load only the one needed.

| Command | When |
| --- | --- |
| `/vault init` | First-run setup. Scaffolds the full structure and personalises vault files. |
| `/vault ingest [files]` | Files in inbox/, or as specified → memory/raw/ → wiki. |
| `/vault research <topic>` | Research a topic. Web search → memory/research/ → wiki. |
| `/vault query <question>` | Answer any question from vault knowledge. **Always use this before navigating memory/wiki/ manually.** |
| `/vault capture` | End of any meaningful session. Record decisions, outcomes, proposed updates. |
| `/vault consolidate` | After reviewing a capture file. Apply approved memory updates. |
| `/vault health` | Periodic health check: `doctor` plus knowledge quality. Runs unattended: fixes delegated to the librarian, decisions escalated to the chief of staff. |
| `/vault distil-transcript [files]` | Process a conversational transcript to memory/raw/. |
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

## Tasks

Work the operator and the team are doing lives in `memory/tasks/`, one note per task, created with the ContextOS MCP `base_record_create` tool against `memory/tasks.base` so the id is assigned for you (`A-` action, `D-` decision, `Q-` question). Use `templates/task.md`; its closing comment is the full field reference.

- `state` is the only lifecycle field, and each type has its own: an action is `backlog`, `next`, `doing`, `waiting`, `review`, `done`, or `dropped`; a decision `proposed`, `adopted`, or `dropped`; a question `open`, `answered`, or `dropped`. That is the starting set; `.contextos/tasks.toml` holds this vault's own, which may differ. There is no `status`.
- `assignee` is a team member's slug. An agent finishes its work into `review`; a person moves it to `done`.
- A task is blocked while any task in its `depends_on` is open. Do not start it.
- Stuck on something only the operator can answer? Write the question under `## Questions`, set `state: waiting` and `waiting_on` to the operator's slug, and stop.
- Record what you did under `## Outcome` before moving a task to `review` or `done`.
- You may research a decision or a question and write your recommendation or answer under `## Outcome`, leaving it open. Only the operator or a human assignee adopts, answers, or drops it.
- A decision or question about the operator's own work is a task (`task_type: decision` or `question`). Only decisions and questions about the vault itself, its design and operation, go in `memory/decisions/` (see `memory/operating/vault-decisions.md`).

---

## Quality mandate

Correcting work after the fact costs far more than getting it right the first time. Catch deviations early and correct them immediately; an error that already exists is no excuse for perpetuating it. Primary-source fidelity outranks summarisation efficiency.

1. Derive from the primary source, always: read the document or transcript itself, in full (in parts if long), never a session summary or an earlier description of it.
2. Verify attribution: confirm content actually appears in a file or session before attributing it there. File names, session order, and prior labels are hypotheses, not evidence.
3. Completeness means in entirety unless the gap is explicit. If an extract covers only part of a source, say so in the file; presenting partial work as complete is an integrity failure.
4. Internal consistency is non-negotiable: propagate corrections and update links before asserting completion.
5. Actionability from zero context is the reproducibility test.

## Conduct

- Use `/vault query` for content questions; minimise direct folder walks and broad reads, and start from indexes.
- Never silently edit existing memory from a session capture; propose the change, wait for approval, and apply it with `/vault consolidate`.
- Never overwrite `memory/raw/` or `memory/research/`; both are immutable beyond the session in which they were created.
- Never invent a claim to fill a gap; raise it as a question task and link it under the note's `## Open Questions`.
- Never let a hedged speculation from `memory/research/` surface in a wiki article as stated fact; it stays flagged until a primary source confirms it.
- Never soften an unsourced claim into a tendency ("often", "typically", "usually", "tends to"); attribute it to a source or observation, or flag it unknown.
- Audit every wiki file produced against `memory/operating/anti-patterns.md` before closing the session.
- Never track activity, progress, decisions, session notes, or history in `registry/instructions/global.md`: it is projected into every session and holds only the operator's standing profile and rules (see `memory/operating/vault-conduct.md`).
- Never edit the operation log to fix a misplaced entry; record a correction with `/vault log` and leave the original where it landed.
- When a schema or convention changes, apply it from the next operation; record old non-compliant content as a migration backlog rather than perpetuating the superseded pattern.
- Never declare a review complete on partial verification; check every file in scope against its primary source, or state exactly what was and was not checked.

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
- **Double-moustache placeholders** (`{{name}}`) for template variables.
- **Every note has frontmatter.**
- **Citations required.** Every wiki article and insight note lists its sources in its frontmatter's `sources`, never in the body. Every claim traces to a source, or is raised as a question task and linked under `## Open Questions`, which holds only links to tasks and vault decisions.
- **Bullets over paragraphs** in memory files. Long narrative goes in a `## Details` section.
- **Wiki is multi-level.** Structure: `memory/wiki/<domain>/<topic>/article.md` minimum.
- **Inbox is ephemeral.** Process to memory/raw/ first; never cite inbox files directly.
- **Token discipline.** Index files summarise. Articles hold content. Raw sources hold evidence. Start at indexes, descend to specific articles.
- **Word wrap** none for markdown or 120 characters for code files, never 80.
