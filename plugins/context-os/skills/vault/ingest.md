# Skill: vault ingest

---

## Purpose

Process source material into the vault memory system: files placed in the shared `inbox/`, file(s) the operator names directly in the command, and research files awaiting compilation in `memory/research/`. Extracts and structures source content into `memory/raw/` (skipped for `memory/research/` sources, which are already in extracted, citable form), then compiles relevant knowledge into `memory/wiki/` articles. The primary mechanism for adding knowledge from external sources to the vault.

`inbox/` is a single vault-root folder shared across all entities, not scoped per entity. Where entity context (personal vs. a specific business entity) helps domain classification, infer it from the file's own content, not its location.

---

## Inputs

| Input | Source | Notes |
| --- | --- | --- |
| `args.files` | Router (operator named file(s) in the command, e.g. `/vault ingest ~/notes.md`) | One or more paths, comma- or space-separated; may be absolute, `~`-relative, or vault-relative; may or may not sit in an inbox |
| Files in `inbox/` | Operator-placed | Any format: md, txt, pdf, docx, csv, export |
| Uncited files in `memory/research/` | `/vault research` output | Research files not yet listed in any wiki article's frontmatter `sources` |
| `memory/operating/vault-conduct.md` | Vault | Read before writing any file |
| `memory/index.md` and relevant subtree indexes | Vault | For determining where to write |

---

## Outputs

| Output | Path |
| --- | --- |
| Processed source extract | `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md` (skipped for `memory/research/` sources) |
| Wiki article(s) | `memory/wiki/<domain>/<topic>/<article>.md` (new or updated) |
| Archived inbox file | `processed/<filename>` (inbox-sourced files only) |
| Log summary | `vault_log_append` |

---

## Flow

### Step 1: pre-flight

1. Read `memory/operating/vault-conduct.md`.
2. If the router passed `args.files` (the operator named specific file(s) in the command, e.g. `/vault ingest ~/Downloads/notes.md`), split on commas or whitespace and resolve each path. A vault-relative path is checked with `mcp__contextos__fs_get_file_info` (`<vault>://<path>`). ContextOS MCP can only copy a file that is inside a vault, so for a path outside the vault (absolute or `~`-relative), ask the operator to place the file in `inbox/` and continue with it from there. Only if the operator declines may you read it with the host's own file tools, which then pass its content through the model; say so, and still write only through ContextOS MCP.
   - If at least one resolves, process exactly this set for the rest of this run; skip the inbox and `memory/research/` scans in steps 3 to 4 below.
   - If none resolve to an existing file, tell the operator the named path(s) could not be found and ask them to confirm the path, or place the file in `inbox/`, then wait for a response rather than falling silently through to the scans below.
3. Otherwise, list `inbox/` with `mcp__contextos__fs_list_directory`.
4. Otherwise, also find research files not yet cited by any wiki article. List them with `mcp__contextos__fs_search_files` (`path: "<vault>://memory/research"`, `pattern: "**/*.md"`, excluding `index.md`), then ask `mcp__contextos__query_graph` for each file's backlinks. A research file with no backlink from `memory/wiki/` is pending; treat it as an available source.
5. If no `args.files` were given, `inbox/` is empty, and no uncited research files exist (a bare `/vault ingest` with nothing to process), ask the operator which file(s) to ingest: paste the content directly, upload a file, place it in    `inbox/`, or name a path directly, then wait for a response rather than stopping silently.
6. For each file, determine: format, source type (operator-named path, inbox, or `memory/research/`), likely domain, and whether a raw extract already exists for this source.

### Step 2: extract to raw

Files sourced from `memory/research/` are already in extracted, citable form (a wiki article's `sources` may list a `memory/raw/` or a `memory/research/` path equally); skip this step for them entirely and carry the research file's own path forward as the source reference into Step 3. Never copy or move `memory/research/` content into `memory/raw/` or an inbox; it is append-only at its original path.

For each remaining file (inbox-sourced or an operator-named path from `args.files`):

1. Determine whether the source is a conversational transcript (masterclass, webinar, coaching call, training session, sales call) rather than a document or export. If so, follow `skills/vault/distil-transcript.md`'s Steps 2 to 4 (profile, read, and extract, which handle the long-line truncation risk in raw transcript exports) to produce the structured extract at `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md`, then carry that file forward as this source's raw extract into Step 3 below, skipping the Markdown/non-Markdown check that follows for this file.

2. Otherwise, if the file is a Markdown document in the vault, copy it by reference so its content never passes through the model:
   1. Read its first heading cheaply with `mcp__contextos__fs_read_text_file` and `head: 20`; that gives `origin` (fall back to the file name) and the `slug`. Read any frontmatter it carries with `mcp__contextos__frontmatter_read`, which also returns its `content_hash`.
   2. Call `mcp__contextos__note_create` with `path: "<vault>://memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md"` (the operator's local date from `vault_info`), `content_from: {path: "<vault>://<source path>", expected_hash: "<content_hash>"}`, and `frontmatter` holding the source's own fields plus `origin`, `source_path` (the source's vault path), `captured` (today), `summary` (one line), `type: document`, and `domain` (best fit). The server copies the body verbatim and leaves the source's frontmatter behind, which is why its fields are passed on here.
   3. A refusal because the path exists means a raw extract of that name is already there: report it rather than choosing a new name, since the source may already have been ingested. An `io/conflict` means the source changed after you read it: read it again and retry once.

3. For non-Markdown, non-transcript sources (PDF, DOCX, TXT, etc.), extract all substantive content to clean Markdown, then write it with `mcp__contextos__note_create` to `<vault>://memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md`, passing the frontmatter as structured fields. Check whether `templates/raw-article.md` exists in the vault. If it does, read it and use its frontmatter and body structure as the template. If it does not exist, use the fallback frontmatter below:
   ```yaml
   ---
   origin: "<original title>"
   source_path: "<original path or URL>"
   captured: "YYYY-MM-DD"
   summary: "<one-line summary>"
   type: "<document | transcript | export | note | other>"
   domain: "<best-fit domain>"
   ---
   ```

4. `memory/raw/` is immutable after writing. Do not edit raw files.

### Step 3: compile to wiki

For each source (a raw extract written in Step 2, or a `memory/research/` file carried forward unchanged):

1. Find existing articles on the same topic with `mcp__contextos__query_blended`, using a short phrase describing the topic and `path_prefix: "memory/wiki"` (narrow to `memory/wiki/<domain>` when the domain is clear).

2. If an existing article covers the topic: read it and integrate new claims with `mcp__contextos__note_update` or `mcp__contextos__fs_edit_file`, carrying the hash you read.
   - Add each new source to the frontmatter's `sources`, and move any `**Source:**` line in the body into it.
   - Update the summary and `## Details` with the new claims.
   - Raise each contradiction as a question task with `mcp__contextos__base_record_create` against `memory/tasks.base` (`prefix: Q`, following `templates/task-question.md`, naming the conflicting sources), and link it under the article's `## Open Questions`, which holds only such links.

3. If no existing article: create `memory/wiki/<domain>/<topic>/<slug>.md` with `mcp__contextos__note_create`. Check whether `templates/wiki-article.md` exists in the vault. If it does, read it and use its frontmatter and section structure as the template. If it does not exist, use the fallback structure below:
   ```markdown
   ---
   domain: <domain>
   topic: <topic>
   updated: YYYY-MM-DD
   status: active
   sources: [memory/raw/YYYY/MM/YYYY-MM-DD-slug.md]
   ---

   # [Title]

   [One-paragraph summary.]

   ## Details

   [Substantive content.]
   ```
   When the source is a `memory/research/` file, list it directly in `sources` instead of a `memory/raw/` path. Raise any gap or unresolved contradiction as a question task, as above, and add an `## Open Questions` section holding only the links to them.


### Step 4: archive inbox file

This step only applies to files sourced from `inbox/`. `memory/research/` files are never archived or moved (append-only at their original path per `vault-conduct.md`); operator-named files from `args.files` that live outside `inbox/` are left exactly where the operator put them.

Once an inbox file has been fully processed (raw extract written, wiki updated), move it with `mcp__contextos__fs_move_file` from `<vault>://inbox/<filename>` to `<vault>://processed/<filename>`. The server updates both folders' indexes.

Repeat for each inbox file processed in this session. Do not archive files that failed to process; leave them in the inbox and report the failure in Step 6.

### Step 5: log

Call `mcp__contextos__vault_log_append` with `entry: "ingest | <n> file(s) processed"` and `files` set to the raw and wiki paths written.

### Step 6: report

State: files processed, raw extracts written, wiki articles created or updated, any inbox files that could not be processed and why.

---

## Invariants

- `memory/raw/` and `memory/research/` files are immutable after creation. Never edit them.
- Never cite inbox files directly in wiki articles. Always process to raw first. `memory/research/` files are the exception: cite them directly, never copy or move them into `memory/raw/` or an inbox.
