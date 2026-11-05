# What the Server Maintains, and When to Step In

Every mutating tool hands its write to the same set of downstream services: the managed `index.md` files, the search indexes, the operation log, and Git. The write itself is atomic and is the contract. Most of the follow-up is automatic, so the common mistake is doing it again by hand. That holds for a managed vault with each service enabled. On an unmanaged vault, or where an operator has disabled a service, the follow-up does not happen, and `vault_info` reports which services are on.

## Managed `index.md` files

- Every folder that is not excluded carries an `index.md` whose managed block lists its contents. It is reconciled whenever a write changes the folder, so do not call `vault_index_rebuild` after writing files, and do not edit inside a managed block. Text outside the block is left alone.
- Use `vault_index_rebuild` after a bulk change made outside MCP (a restore, a large import, an Obsidian reorganisation), or when the health check reports index drift. Scope it to a subtree with `path` rather than the whole vault, and run it once with `dry_run` first to see what would change.
- The `repair` option corrects frontmatter that an earlier defective rebuild wrote wrongly. It can override values set on purpose, so use it only when the operator asks, run `dry_run` first, and make sure the vault is committed beforehand.

## Events

- The server fires events for task changes (including a task moved to another folder), member state changes, and vault health as the calls that cause them complete, under the vault's write lock, and writes them under `memory/events/`. Do not record those yourself, and do not write under that folder. See Events in [notes.md](notes.md).
- A secondary-service failure on a write (Git, the index, search, projection) is recorded as a `vault.degraded` event the first time its warning code appears, and `vault.recovered` when a later write completes without it. The warning on the write is still the signal to act on.

## Operation log

- Mutations made through the tools are recorded in the daily operation log automatically, when the vault has it enabled. Do not log individual tool calls.
- `vault_log_append` is for a deliberate entry that describes something meaningful the tools cannot know, such as "ingested the inbox" or a decision the operator asked to record. Follow the calling skill's instruction on when to add one. The entry becomes part of the append-only log, so write it carefully.

## Git

- With Git enabled, each change is staged as it is made and committed once the vault has been quiet for the configured window (30 seconds by default). Changes made within one window share a commit, named for the tools that made them. Continuous activity does not defer a commit forever, because a batch open for ten windows is committed by the next change.
- Do not call `git_commit` after each write. Call it when you need a commit boundary now: before a risky bulk change or a `git_restore`, or when the operator asks for a commit at the end of the work. It takes an optional `message`.
- `git_status` shows the branch, staged, unstaged, and untracked paths, and the paths the server has pending. It also reports a `commit_failure` (with `code`, `message`, and `attempts`) when the automatic commit is failing. `git_log` reads history, optionally for one path, and `git_diff` returns a size-capped diff between refs or against the working tree.
- `git_restore` brings back historical content as a new forward change, and it never rewrites history. Run it with `dry_run` first, and commit pending work before you restore. It skips the paths the operator has excluded, which always include the operation log.
- Edits the operator makes outside MCP, in Obsidian for example, are never committed by the server. Do not assume a clean `git_status` covers them.
- `git_init` starts recoverable history for a vault that has none. Offer it rather than assuming it.

## Host projection

- A write under `registry/agents/`, `registry/skills/`, or `registry/instructions/global.md` is projected into Claude Code and Codex automatically (their agent and skill folders, and a marked orientation block in each host's global instructions). It is derived data, like the index. Never write a host folder or a host's global instructions yourself, and never repeat the projection by hand. Edit the definition in the vault and the server does the rest.
- Projection runs only when the operator's configuration enables it (the `[projection]` section; on by default only for the configuration at the platform default location), and only for hosts that are installed. A write on a vault with projection off simply has no projection warnings.
- `vault_info` lists `vaults` in the operator's configuration order. That order decides precedence: when several vaults define the same agent or skill slug, the first wins, for projection and for lookups. Do not reorder, and do not assume the active vault wins. A later vault's divergent copy is shadowed.
- An agent definition projects only with `tier` set to `fast`, `balanced`, or `deep`, an optional `access` of `all` (the default) or `read-only`, and a non-empty `description` and body. A definition with a `model` or `tools` field is refused with `projection/invalid-definition` naming the field, because those are host field names. `access: read-only` is best effort, not a guarantee: the server classifies only ContextOS's own tools, a read-only Claude Code agent gets an allowlist of read and search tools plus ContextOS's non-mutating tools and no third-party MCP tools, and Codex can only switch off its shell, apps, and plugins, so MCP tools stay available to the agent there. `access` is interim and is expected to become a list of allowed tools with `*` wildcards.
- Projection problems arrive as `warnings` on an otherwise successful write. The write stands, so do not retry or roll it back. Tell the operator and act as follows:

| Warning code | Meaning | What to do |
| --- | --- | --- |
| `projection/invalid-definition` | The definition fails the projection contract (the warning names the field) | Fix the definition in the vault. Any earlier projection of that slug is left in place |
| `projection/write-failed` | A host folder could not be written | Report it; the operator checks permissions and storage, then `doctor_resolve` re-projects |
| `projection/unowned-collision` | A file or folder the server did not project sits at that slug | The server never touches it. Ask the operator to rename or remove theirs, or choose another slug |
| `projection/foreign-owner` | Another configuration projected that entry | Leave it; the operator decides which configuration owns the host |
| `projection/path-rejected` | A link or unusual entry sits in a host target, or the source is a link | Ask the operator to remove the link or entry, or replace the vault link with the real file |
| `projection/hand-edited-replaced` | The definition changed, so the server replaced a projection the operator had edited by hand in the host folder | Tell the operator their host-side edit was replaced; edits belong in the vault definition |
| `projection/reparse-point` | On Windows, an entry in a host target is a reparse point that is not a link, such as a OneDrive cloud placeholder | Ask the operator to make it available offline or move it; the server never writes through it |
| `projection/read-failed` | An entry in a host target, or the ownership record, could not be read | Report it; the operator checks permissions and storage, then `doctor_resolve` re-projects |
| `projection/cleanup-incomplete` | A skill was installed but the previous copy of its folder could not be removed | Nothing to do now; the leftover is removed on the next projection or server start |
| `projection/busy` | Another process held the host-level projection lock for 5 seconds | Nothing was projected; the write stands. Run `doctor_resolve` (without `path`) later to re-project |
| `projection/lock-failed` | The host-level projection lock could not be opened | Nothing was projected; the write stands. The operator checks that the server's state folder is on a local disk it can write |
| `projection/malformed-block` | The orientation markers in a host's global instructions are damaged | Ask the operator to fix the block by hand; the server will not repair a malformed block |
| `projection/manifest-malformed` | The server's ownership record is unreadable | Report it to the operator; do not try to repair state files |

## Health checks

- `doctor` is a read-only report on configuration, indexes, Git recovery, and each derived store (`text_index_store`, `link_graph_store`, `vector_store`): whether it opens, is intact, and how many other contextos processes hold it. It is the first stop when writes return warnings, searches look wrong, or `git_status` shows a `commit_failure`. Each check carries a stable `kind` code and, unless it is the global configuration check, the `vault_name` it concerns, so group and route findings by those and never by parsing `subject` or `message`. Pass `path` to assess one vault (plus the global check) instead of every vault, which also skips the costly scans of the others.
- `doctor`'s `record_conformance` check ("Record conformance", which replaced the old base property check) is reported and never repaired, and `doctor_resolve` leaves it alone. It lists, at most 10 each with the rest counted, records whose fixed fields differ from their series template (fields, series, and template path, never values), notes whose `base` property names a base that does not select them (naming the one base that does, or `no base selects it`, or how many do), and sidecars whose template cannot be used. Do not correct these in bulk on your own: which value is right, or whether a note belongs elsewhere, is a decision per note, and repairs specific to one vault's history are that vault's own work, planned with the operator and applied through `frontmatter_update` with each note's hash.
- `doctor`'s `link_integrity` check ("Link integrity") passes with the number of links checked, or fails with the numbers of not-found links, ambiguous links, unreadable notes, and notes affected, listing the first 10 as `source:line -> target (kind)` and counting the rest. It is reported and never repaired, and `doctor_resolve` leaves it alone: giving an ambiguous link a path, and correcting or removing a broken one, is the author's decision. It asks the same link graph as `query_graph` `unresolved`, after bringing it up to date with the vault, and checks the same sources, so on a failure list the whole set with `query_graph` and `operation: "unresolved"` (see [search.md](search.md#the-link-graph)). It passes with `not checked` when the vault's link graph is off or its search state could not be opened.
- `doctor`'s `team_config` check also fails, never auto-fixably, when `.contextos/team.toml` cannot be used by the vault's jobs: it does not parse, is not text, has a slug that is not lowercase letters, digits, and hyphens or shares one, has no member at all (`team-empty`), or does not have exactly one member with `chief_of_staff = true` (the message names the rule and never a member). A vault with a saved job and no `team.toml` fails it too, and a vault with no job passes with an advisory. The operator corrects the file; scheduled jobs in that vault are paused until then.
- When projection is on, `doctor` also reports projection findings: `projection_stale`, `projection_hand_edited`, `projection_orphaned`, `orientation_block` (auto-fixable), and `projection_invalid_definition`, `projection_shadowed`, `projection_unowned_collision`, `projection_foreign_owner`, `codex_read_only_unenforced`, `codex_override_hides_agents` (reported only; the operator or the definition's author fixes those). `projection_busy` or `projection_lock_failed` means projection could not be assessed this time; the vault checks are still complete. A finding names its stable repair in `remediation`, and `remediation_tool` only when a callable MCP tool performs it. The projection repairs (`reproject`, `withdraw_projection`, `restore_orientation`) are done by the server itself and so have no `remediation_tool`: do not look for a tool of that name.
- `doctor_resolve` acts on every auto-fixable finding: a stale or missing managed index (it runs `vault_index_rebuild`), a Git repository that is absent or has no commits yet (it runs `git_init`), MCP changes left uncommitted, re-projection of a stale or hand-edited agent or skill, withdrawal of an orphaned projection, restoration of the orientation block, and a derived store that is damaged, holds an undecodable record, or was written by another version (it runs `query_index_rebuild`, which moves a damaged store aside, keeping it, before rebuilding). A damaged store another contextos process still holds is not auto-fixable: the finding names how many hold it, and the operator decides. Run `doctor` first, then `doctor_resolve` with `dry_run` to see exactly what it would do, and scope it to one vault with `path`, except that a `path`-scoped run does not repair projection: projection is host-level, so omit `path` to repair it (with `path`, `doctor` lists the findings that name that vault and `doctor_resolve` leaves them). Each outcome names its `kind` and, where a configured vault applies, its `vault_name` and the vault's `vault_path`; a host-level projection outcome names neither.
- Initialising Git is a standing change, because it starts automatic commits on every future mutation. If `doctor` reports an absent repository, get the operator's agreement before resolving it, exactly as you would before calling `git_init` yourself.

## Warnings

A mutation result with `warnings` means the write succeeded and a downstream service (the index, the log, Git, search, or a reciprocal link) did not keep up. Do not retry the write. The retry may duplicate work, and the completed write is never rolled back. Tell the operator what the warning says, and use `doctor` to find the cause. The warning `events/write-failed` is the same kind of signal: the write that should have fired an event succeeded, but the event itself was not written. A repeat of an idempotent call such as `frontmatter_link` is the exception, because repeating it is how a failed reciprocal is repaired.

## Errors

- A failed call returns a stable `code` (for example `io/conflict`, `index/invalid-query`, or `link/undeclared-field`), a `message`, and a `remediation`. The code is for deciding what to do and the remediation says how, so act on the remediation instead of retrying the same call.
- Batch tools (`fs_read_multiple_files`, `fs_delete_file` with `paths`) succeed as a whole and report failures per item. Check every item, not only the overall result.
- Unknown or malformed parameters are rejected rather than ignored or repaired, so a refusal about a parameter means the call is wrong, not that the server is unwell.

## Other tools

- `agent_state_change` records an agent's working, blocked, idle, or awaiting-input transition. Use it only when a skill or the operator has told you to act as a registered agent.
- The `ephemeris_*` tools (moon phase, solar events, and so on) appear only when the operator has enabled them. Do not expect them in every catalogue.
