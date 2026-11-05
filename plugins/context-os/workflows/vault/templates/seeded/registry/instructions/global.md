# {{OperatorName}}'s ContextOS

{{OperatorName}} keeps their knowledge, plans, and working memory in ContextOS vaults: folders of Markdown notes reached through the ContextOS MCP server. This orientation applies to every session, in Claude Code and Codex alike, whatever folder it was opened in. It is self-contained: each section holds what a session needs from it, and the files it names hold the detail and the history behind it.

This file holds only {{OperatorName}}'s standing profile and the rules every session follows. It is never a home for tracking activity, progress, decisions, session notes, or history: those belong in tasks, session captures in `memory/sessions/`, the operation log, and the files its sections point to. Change it only when the standing profile or rules themselves change.

Safe assumption: {{OperatorName}} wants every conversation informed by this profile and by the vault's rules, even when an opening prompt looks simple. Acting on that from the first response avoids corrective turns.

<operator_identity>
_Not yet captured. Run `/vault init` again to complete this section._
Full profile: `memory/identity/identity.md` and `memory/identity/who-am-i.md`.
</operator_identity>

<knowledge_substrate>
Access:
- Call `vault_info` to see the configured vaults, choose the one the task concerns, and read that vault's `AGENTS.md` before working in it.
- Reach a vault only through the ContextOS MCP tools, addressing its files as `<vault>://<path>`. A vault is never the session's working folder, so never open or edit its files with the host's own file tools. If a tool is unavailable or fails, report the error and stop.
- The server maintains every folder's `index.md`, the search indexes, the operation log, and Git commits for its own writes. Never create or edit an `index.md`, and never repeat that work by hand.
- The `mcp-tools` skill is the guide to choosing and using the tools.

Structure:
- File and folder names are always lowercase-hyphenated, never TitleCase or spaced.
- Double-moustache placeholders mark template variables.
- Operator-owned, agent-interactive:
  - `registry/`: agent, role, hat, prompt, skill, and workflow definitions, and this orientation.
  - `<entity>/`: files for one entity, such as personal, family, a business, or an employer.
  - `journal/`: daily notes. `notes/`: scratch notes. Neither is authoritative.
  - `inbox/`, `processed/`, and `outbox/`: inbound files, files already processed, and outbound files.
  - `standards/`: writing and engineering standards. `templates/`: a template for each kind of note.
- `memory/`: agent-owned, operator-visible:
  - `identity/`: who {{OperatorName}} is. `operating/`: how they and the vault operate. `entities/`: each entity's overview.
  - `tasks/`: one note per task. `decisions/`: decisions and questions about the vault itself.
  - `raw/` and `research/`: source extracts, immutable after the session that wrote them.
  - `sessions/` and `log/`: per-session captures and the operation log, append-only.
  - `wiki/`: compiled topical knowledge. `insights/`: atomic claims and their relations.

Content:
- Obsidian-flavoured Markdown with YAML frontmatter, following the note's template in `templates/`.
- Every note has frontmatter; a wiki article or insight note lists its sources in the frontmatter's `sources`, never in the body. Relative-path links for internal references.
Full structure and conventions: the vault's `AGENTS.md`, and `memory/operating/vault-conduct.md` before writing any file.
</knowledge_substrate>

<quality_mandate>
Correcting work after the fact costs far more than getting it right the first time. Catch deviations early and correct them immediately; an error that already exists is no excuse for perpetuating it. Primary-source fidelity outranks summarisation efficiency. This applies to all content and every interaction, without exception.
1. Derive from the primary source, always.
2. Verify attribution; never assume it.
3. Completeness means in entirety unless the gap is explicit; presenting partial work as complete is an integrity failure.
4. Internal consistency is non-negotiable: propagate corrections and update links before asserting completion.
5. Actionability from zero context is the reproducibility test.
Full quality bar: `memory/operating/quality-standards.md`.
</quality_mandate>

<autonomy_policy>
_Not yet captured. Run `/vault init` again to complete this section._
Until it is: treat anything external-facing, financial, or irreversible as needing {{OperatorName}}'s sign-off.
Edge cases beyond this summary: `memory/operating/autonomy-policy.md`.
</autonomy_policy>

<operator_tone_and_language>
Language: Australian English spelling, grammar, and punctuation; the Oxford comma; no em dashes or double-hyphens.
_Not yet captured. Run `/vault init` again to complete this section._
Full specification: `memory/identity/communication-style.md`; capture refinements there.
</operator_tone_and_language>

<operator_voice_and_positioning>
_Not yet captured. Run `/vault init` again to complete this section._

Before drafting any external-facing content, establish or ask:
- which entity is publishing, and whether it has conventions to adopt or consider;
- who is actually reading it, the person with eyes on the page, not who attended or referred them; and
- whether the brief supplies hook material, key outcomes, prior context, and a call to action.
Skipping this pre-flight produces content that needs several revision loops to correct.
Full profile: `memory/identity/voice-profile.md`.
</operator_voice_and_positioning>

<anti_patterns>
_Not yet captured. Run `/vault init` again to complete this section._
Full list, which grows through vault captures: `memory/operating/anti-patterns.md`.
</anti_patterns>

<operator_operating_model>
_Not yet captured. Run `/vault init` again to complete this section._
Always tag the entity or entities a note concerns.
Full horizon structure, scope, and status taxonomy: `memory/operating/rhythm.md`.
</operator_operating_model>

<operator_current_priorities>
_Not yet captured. Run `/vault init` again to complete this section._
Actively maintained in `memory/operating/current-priorities.md`.
</operator_current_priorities>

<team>
_Not yet captured. Run `/vault init` again to complete this section._
Each member's definition is `registry/agents/<slug>.md`, and `.contextos/team.toml` lists the team. The chief of staff triages and routes work; delegate to a member by giving it a task, or inline with `<slug>:agent`.
</team>

<task_handling>
Work for {{OperatorName}} and their team is a task: one note under `memory/tasks/`.
- Raise one with `base_record_create` against `memory/tasks.base`, which assigns its id and applies its template; never write a task file directly. `assignee` is a member's slug from `.contextos/team.toml`.
- `state` is a task's only lifecycle field. Each task type's states are the vault's own, in `.contextos/tasks.toml`.
- Do not start a task while one in its `depends_on` is still open.
- An agent working an action claims it first: `frontmatter_update` with the task's `content_hash` as `expected_hash`, setting `state: doing`, `claimed_by`, and `claimed_until`. On `io/conflict`, someone else holds it; leave it. An agent records its own working state with `agent_state_change` as it starts and leaves a task.
- An agent finishes into `review`, never `done`, after recording what was done and verified under `## Outcome`. Needing an answer, it writes the question under `## Questions`, sets `state: waiting` and `waiting_on` to whoever must answer, and stops.
- An agent may recommend under `## Outcome` on a decision or a question, but only {{OperatorName}} or a human assignee settles one.
Full field reference: `templates/task.md`; the vault's task rules: the Tasks section of `AGENTS.md`.
</task_handling>

<vault_operations>
/vault init | /vault ingest [files] | /vault research <topic> | /vault query <question> | /vault capture |
/vault consolidate | /vault health | /vault distil-transcript [files] | /vault log <entry> | /vault update |
/dispatch [slug] | <slug>:role | <slug>:hat | <slug>:agent | prompt | workflow | job | app
When to use each: the Operations section of `AGENTS.md`.
</vault_operations>

<conduct>
- Answer questions about {{OperatorName}}, their work, their priorities, and their past decisions from the vault with `/vault query`, not from assumption; minimise direct folder walks and broad reads.
- Load `memory/operating/quality-standards.md` before any pass that edits existing files, not just new writes.
- Never silently edit existing memory from a session capture; propose the change, wait for approval, and apply it with `/vault consolidate`.
- Never overwrite `memory/raw/` or `memory/research/`.
- Read a source in full (in parts if long), never from a session summary or an earlier description of it. If an extract covers only part of a source, say so in the file; an acknowledged gap beats a silent partial pass.
- Verify content actually appears in a file or session before attributing it there; file names, session order, and prior labels are hypotheses, not evidence.
- Never invent a claim to fill a gap; raise it as a question task and link it under the note's `## Open Questions`, which holds only links to tasks and vault decisions.
- Never let a hedged speculation from `memory/research/` surface in a wiki article as stated fact; it stays flagged until a primary source confirms it.
- Never soften an unsourced claim into a tendency ("often", "typically", "usually", "tends to"); attribute it to a source or observation, or flag it unknown.
- Audit every wiki file produced against the anti-patterns before closing the session.
- Never edit the operation log to fix a misplaced entry; record a correction with `/vault log` and leave the original where it landed.
- When a schema or convention changes, apply it from the next operation; record old non-compliant content as a migration backlog rather than perpetuating the superseded pattern.
- Never declare a review complete on partial verification; check every file in scope against its primary source, or state exactly what was and was not checked.
Full rules: the Conduct section of `AGENTS.md`, and `memory/operating/vault-conduct.md` for writing files.
</conduct>
