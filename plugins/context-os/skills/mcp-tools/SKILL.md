---
name: mcp-tools
description: "Best-practice guide for using the ContextOS MCP server tools (mcp__contextos__*) efficiently and safely: whole-file reads with fs_attach_file rather than paged reads, conflict-safe writes with expected_hash, edit versus rewrite, batching, choosing between text, semantic, blended, and graph search, notes, Bases, keyed records, events and frontmatter links, and what the server maintains automatically (index.md, operation log, Git, and the projection of registry agents, skills, and global instructions into Claude Code and Codex). Fires on explicit `/mcp-tools` invocation, and when a task is about to make several mcp__contextos__ calls, a call failed or returned a warning, or the best tool or sequence is unclear. Does not fire for tool schemas or parameter lists (read those from the MCP catalogue), for `/vault COMMAND` routing, or for `SLUG:role`, `SLUG:hat`, `SLUG:agent`, and the app, workflow, and job skills, which name their own tools."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "[files|search|notes|maintenance]"
arguments: ["topic"]
---

# MCP Tools: Best Practice

This skill teaches judgement, not syntax. Tool names, parameters, and schemas come from the MCP catalogue the harness already gives you, and they are always the authority on what a call accepts. What the catalogue cannot tell you is which tool is cheapest for a job, which sequence is safe, and which work the server already does for you. That is what follows.

Tools are named here without a prefix. In Claude Code and Codex they appear as `mcp__contextos__NAME`. The steps below describe the tools present in the catalogue today. If the catalogue lists a tool or parameter this skill does not mention, read its schema and use it. If a documented tool is missing from the catalogue, the server is an older version: tell the operator which tool is missing and stop the step that needs it.

## Orientation

- Call `vault_info` once per task, not once per operation. It reports the vault names, whether each is managed, which search indexes are enabled, and the size limits. Skip it if a calling skill has already made its availability check. If it errors or is not registered, no ContextOS server is reachable: report that and stop. There is no fallback to the host's own file tools.
- **Dates are the operator's local time.** Every `created` and `updated` stamp the server writes, and the day an operation log entry is filed under, is in the zone `vault_info` reports as `time_zone` (its IANA `name`, or POSIX `rules` for a host zone without one, its `source`, and current `offset`, daylight saving included), never UTC. When you choose a date yourself (a dated file name, a journal entry, a `date` property), use that zone's date, not UTC's: late in the operator's evening UTC is often still the previous day, and early in their morning it is.
- A vault's `managed` flag, reported by `vault_info` and `fs_list_allowed_directories`, decides whether the server runs its services for that vault. On an unmanaged vault the tools still read and write files, but there is no `index.md` maintenance, operation log, Git recovery, or search there, so do not rely on any of them. `vault_info` also shows which services are enabled for each vault, because an operator can switch them off individually.
- `vaults` in `vault_info` is in the operator's configuration order, and that order decides which vault's agent and skill definitions win. Keep it; see host projection in [maintenance.md](maintenance.md).
- Paths are vault-relative. With one vault configured a bare relative path works. With several, address a file as `NAME://relative/path`, and a vault's root as `NAME://.`. Absolute paths are accepted only inside a configured vault.
- Vault selectors are not uniform. The `vault` parameter of the query tools (`query_text`, `query_semantic`, `query_blended`, `query_graph`) and of `base_query` takes `NAME://.` and rejects a bare name, while `vault_index_rebuild` and the `git_*` tools accept a bare name. When a call is refused over a vault argument, read that parameter's own description first.

## Habits that matter most

1. **Read a whole file with `fs_attach_file`.** Paging through a file with repeated `fs_read_text_file` calls costs a round trip per page, and any text read whose result reaches the server's inline threshold (5 KB by default), slices included, comes back as a truncated preview. The rest of a file too large to attach is read in parts with `offset`, `next_offset`, and `expected_version`. See [files.md](files.md).
2. **Carry the content hash.** Overwriting an existing file needs the `expected_hash` from your last read, and every successful write returns the new hash, so chain writes without re-reading. Never reach for `force` to get past a conflict.
3. **Change a file with the narrowest tool.** `fs_edit_file` for a text change, `frontmatter_update` for properties, `note_update` for properties and body together, `frontmatter_link` for cross-references, `base_apply` for a Base. Rewrite a file whole only when most of it changes.
4. **Batch, and issue independent calls together.** Many tools take lists (`fs_read_multiple_files`, `fs_delete_file`, `base_apply`, `frontmatter_link`, `fs_edit_file`). Independent reads can go in one response. Writes to the same vault are serialised by the server, and writes to the same file depend on each other's hash, so run those in order.
5. **Search first, then read only what you need.** Search hits carry a title, description, summary, excerpt, and status, which is often enough to decide without opening the note. See [search.md](search.md).
6. **Let the server maintain what it maintains.** It keeps `index.md` files current, records tool mutations in the operation log, fires task, member, and vault health events, commits to Git after a quiet period, and projects `registry/agents/`, `registry/skills/`, and `registry/instructions/global.md` into the hosts' own folders. Do not repeat that work by hand, and never write a host folder directly. See [maintenance.md](maintenance.md).
7. **Read results, not just success.** A successful mutation can still carry `warnings`, and batch tools report failures per item. Errors carry a stable `code` and a `remediation`, so act on the remediation instead of retrying blindly.

## Which tool for which job

| Job | Use | Not |
| --- | --- | --- |
| Read one whole file | `fs_attach_file` | Repeated `fs_read_text_file` pages |
| Read a note with every link resolved to a vault path | `fs_attach_file` with `expand_links` | Searching for each link's target |
| Read part of a file, the end of a log, or a known line range | `fs_read_text_file` with `head`, `tail`, or `range` | Attaching a very large file |
| Read a file above 10 MiB, or one with a very long line, inline | `fs_read_text_file` with `offset` and `length`, following `next_offset` until it is -1 (a part has no `content_hash`) | Paging with `range` |
| Read several small files | `fs_read_multiple_files`, or parallel `fs_attach_file` calls for large ones | One `fs_read_text_file` call each |
| Check existence, size, or the current hash | `fs_get_file_info` | Reading the content |
| Read a note's properties | `frontmatter_read` | Reading the whole note |
| Change text in an existing file | `fs_edit_file` | `fs_write_file` of the whole file |
| Create a plain file | `fs_write_file` | Guessing an existing path is free |
| Create a note | `note_create` | `fs_write_file` with hand-built frontmatter |
| Copy a vault file into a new note (filing a source into `memory/raw/`) | `note_create` with `content_from` | Reading the file and writing its text back out |
| Change note properties | `frontmatter_update` | Editing the YAML with `fs_edit_file` |
| Change a note's properties and body together | `note_update` | `frontmatter_update` then `fs_write_file` |
| Add or remove a cross-reference | `frontmatter_link` | `frontmatter_update` on a list field |
| Create a record in a Base | `base_record_create` | `note_create` with a guessed next id |
| Read records whose ids you know | `base_query` with `ids` | A view query, then a read per record |
| Raise a record that may already exist | `base_record_create` with `unique_fields` | Searching first, then creating if absent |
| Record that something happened, for a kind the vault declares | `base_record_create` on `memory/events.base` | `note_create` or any write under `memory/events/` |
| Find a path by name | `fs_search_files` with a `**/` pattern | `fs_directory_tree` of the whole vault |
| Find notes by content or meaning | `query_blended`, `query_text`, `query_semantic` | Reading directories to look |
| Find what links to a note | `query_graph` (`backlinks`) or `links_read` | Searching for the note's name |
| Rename or move | `fs_move_file`, after checking backlinks (never `memory/events` or a folder that holds it: refused with `events/server-owned`) | Write then delete |
| Remove a file | `fs_delete_file` (trash by default; refused for `memory/events` and any folder that holds it) | `hard` unless the operator asked |
| Record a meaningful event in the daily log | `vault_log_append` | Logging each tool call |
| Force a commit now | `git_commit` | A commit after every write |

## Topic files

Load the one that matches the task. With a topic argument, load only that file.

| Topic | File | Covers |
| --- | --- | --- |
| `files` | [files.md](files.md) | Reading, hashing, editing, writing, moving, deleting, listing |
| `search` | [search.md](search.md) | Choosing a search tool, query syntax, narrowing, the link graph |
| `notes` | [notes.md](notes.md) | Notes, frontmatter, Bases, keyed records, events, cross-reference links, Canvas, diagrams |
| `maintenance` | [maintenance.md](maintenance.md) | `index.md`, operation log, Git, host projection, health checks, warnings, errors |
