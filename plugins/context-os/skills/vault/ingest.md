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
| Uncited files in `memory/research/` | `/vault research` output | Research files not yet referenced by a `**Source:**` line in any wiki article |
| `memory/operating/vault-conduct.md` | Vault | Read before writing any file |
| `memory/index.md` and relevant subtree indexes | Vault | For determining where to write |

---

## Outputs

| Output | Path |
| --- | --- |
| Processed source extract | `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md` (skipped for `memory/research/` sources) |
| Wiki article(s) | `memory/wiki/<domain>/<topic>/<article>.md` (new or updated) |
| Updated wiki index(es) | `memory/wiki/<domain>/index.md`, `memory/wiki/index.md` |
| Archived inbox file | `processed/<filename>` (inbox-sourced files only) |
| Log entry | `memory/log/YYYY/MM/YYYY-MM-DD.md` |

---

## Flow

### Step 1: pre-flight

1. Read `memory/operating/vault-conduct.md`.
2. If the router passed `args.files` (the operator named specific file(s) in the command, e.g. `/vault ingest ~/Downloads/notes.md`), split on commas or whitespace and resolve each path (`~`-expand, or resolve relative to the vault root). Check each exists.
   - If at least one resolves, process exactly this set for the rest of this run — skip the inbox and `memory/research/` scans in steps 3 to 4 below.
   - If none resolve to an existing file, tell the operator the named path(s) could not be found and ask them to confirm the path, or place the file in `inbox/`, then wait for a response rather than falling silently through to the scans below.
3. Otherwise, scan `inbox/` for files.
4. Otherwise, also scan `memory/research/` for research files not yet cited by any wiki article. List candidates, then for each check whether it is already cited:
   ```bash
   find memory/research -name "*.md" ! -name "index.md"
   # for each result <path>:
   grep -rlF "<path>" memory/wiki/
   ```
   A research file with no match is pending; treat it as an available source.
5. If no `args.files` were given, `inbox/` is empty, and no uncited research files exist (a bare `/vault ingest` with nothing to process), ask the operator which file(s) to ingest: paste the content directly, upload a file, place it in    `inbox/`, or name a path directly, then wait for a response rather than stopping silently.
6. For each file, determine: format, source type (operator-named path, inbox, or `memory/research/`), likely domain, and whether a raw extract already exists for this source.

### Step 2: extract to raw

Files sourced from `memory/research/` are already in extracted, citable form (per `vault_lint.py`'s citation check, which resolves `**Source:**` lines against `memory/raw/` or `memory/research/` equally) — skip this step for them entirely and carry the research file's own path forward as the source reference into Step 3. Never copy or move `memory/research/` content into `memory/raw/` or an inbox; it is append-only at its original path.

For each remaining file (inbox-sourced or an operator-named path from `args.files`):

1. Determine whether the source is a conversational transcript (masterclass, webinar, coaching call, training session, sales call) rather than a document or export. If so, follow `skills/vault/distil-transcript.md`'s Steps 2 to 4 (profile, read, and extract, which handle the long-line truncation risk in raw transcript exports) to produce the structured extract at `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md`, then carry that file forward as this source's raw extract into Step 3 below, skipping the Markdown/non-Markdown check that follows for this file.

2. Otherwise, if the file is a Markdown document, use the copy script:
   ```bash
   session-start >/dev/null 2>&1
   source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
   python $CONTEXT_OS_PLUGIN_ROOT/scripts/copy_markdown_to_raw.py \
     --vault-root . \
     --source inbox/<filename>.md \
     --type document \
     --domain <best-fit-domain>
   ```

3. For non-Markdown, non-transcript sources (PDF, DOCX, TXT, etc.), extract all substantive content to clean Markdown, then write manually to `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md`. Check whether `templates/raw-article.md` exists in the vault. If it does, read it and use its frontmatter and body structure as the template. If it does not exist, use the fallback frontmatter below:
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

1. Find existing articles on the same topic. If MCP is available (see the vault router's MCP awareness section), call `mcp__contextos__query_text` with `query` built from the keywords and `path_prefix: "memory/wiki/<domain>/<topic>"`.   Otherwise, run the query script:
   ```bash
   session-start >/dev/null 2>&1
   source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
   echo '{"domains":["<domain>"],"topics":["<topic>"],"keywords":["<keywords>"]}' \
     | python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_query.py --vault-root . --max-candidates 5
   ```

2. If an existing article covers the topic: read it and integrate new claims.
   - Add new `**Source:**` entries.
   - Update `## Key Takeaways` with new insights.
   - Flag contradictions in `## Open Questions`.

3. If no existing article: create `memory/wiki/<domain>/<topic>/<slug>.md`. Check whether `templates/wiki-article.md` exists in the vault. If it does, read it and use its frontmatter and section structure as the template. If it does not exist, use the fallback structure below:
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

   ## Key Takeaways

   - [Bullet]

   ## Details

   [Substantive content.]

   ## Open Questions

   - [Gaps, unresolved contradictions]

   **Source:** [memory/raw/...](../../raw/...)
   ```
   When the source is a `memory/research/` file, cite it directly in `sources:` and `**Source:**` instead of a `memory/raw/` path.

4. Update wiki indexes. If MCP is available, call `mcp__contextos__vault_index_rebuild` with `path: "memory/wiki/<domain>/<topic>"`. Otherwise, run the index updater as a single command as each `Bash` call is a separate shell invocation:
   ```bash
   session-start >/dev/null 2>&1
   source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
   python $CONTEXT_OS_PLUGIN_ROOT/scripts/update_wiki_index.py \
     --vault-root . \
     --touched memory/wiki/<domain>/<topic>/<article>.md
   ```

### Step 4: archive inbox file

This step only applies to files sourced from `inbox/`. `memory/research/` files are never archived or moved (append-only at their original path per `vault-conduct.md`); operator-named files from `args.files` that live outside `inbox/` are left exactly where the operator put them.

Once an inbox file has been fully processed (raw extract written, wiki updated), move it from `inbox/` to `processed/` and update both index files.

If MCP is available: call `mcp__contextos__fs_move_file` with `source: "inbox/<filename>"` and `destination: "processed/<filename>"`, then call `mcp__contextos__vault_index_rebuild` with `path: "inbox"` and again with `path: "processed"` to refresh both indexes. Otherwise, run the inbox script:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_inbox.py \
  --vault-root . \
  --file <filename>
```

Repeat for each inbox file processed in this session. Do not archive files that failed to process; leave them in the inbox and report the failure in Step 6.

### Step 5: log

If MCP is available, call `mcp__contextos__vault_log_append` with `entry: "ingest | <n> file(s) processed"` and `files` set to the raw and wiki paths written. Otherwise, append to `memory/log/YYYY/MM/YYYY-MM-DD.md`:
```
HH:MM | agent | ingest | <n> file(s) processed | files: [raw slugs], [wiki paths]
```

### Step 6: report

State: files processed, raw extracts written, wiki articles created or updated, any inbox files that could not be processed and why.

---

## Invariants

- `memory/raw/` and `memory/research/` files are immutable after creation. Never edit them.
- Never cite inbox files directly in wiki articles. Always process to raw first. `memory/research/` files are the exception: cite them directly, never copy or move them into `memory/raw/` or an inbox.
- Update the parent index.md whenever a new wiki article or folder is created.
