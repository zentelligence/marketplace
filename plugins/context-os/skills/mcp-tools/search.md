# Search and Navigation

## Choosing a tool

| You have | Use | Notes |
| --- | --- | --- |
| Words the note contains, or a tag or frontmatter value to filter on | `query_text` | The only search that accepts `tags` and `fields` filters. Always available unless the operator disabled the text index |
| An idea, but not the words | `query_semantic` | Needs semantic search enabled for the vault, which `vault_info` reports. Otherwise it errors |
| Either, or you are unsure | `query_blended` | Fuses both rankings. If one index is off or fails, it answers from the other and adds a warning instead of failing |
| A file name or glob | `fs_search_files` | See [files.md](files.md) |
| A note and want its neighbours, backlinks, or the path between two notes | `query_graph` | See below |
| Every broken or ambiguous link in the vault, or the notes nothing links to | `query_graph` with `unresolved` or `unlinked` | See below |

When both indexes are enabled, `query_blended` is the sensible default for an open question. Reach for `query_text` when you need exact terms or a property filter.

## Writing a query

- Full-text search reads a colon as a field search, and it reads parentheses and quotes as grouping. A natural-language question such as `why did we pick sqlite: notes` does not parse and `query_text` returns `index/invalid-query`. Rephrase it as keywords, or use `query_blended` (which falls back to meaning and warns) or `query_semantic` (which embeds the text exactly as written).
- `query_semantic` and the semantic half of `query_blended` work best on a short natural-language phrase describing the idea, not on a keyword list.

## Reading the results

- Each hit carries the note's `title`, a `metadata` object (`description`, `summary`, `excerpt`, `status`, `updated`, `note_type`, each omitted when the note does not declare it), a `modified` time, and a snippet. Triage from these first. Read a note only when the hit is not enough to decide, and then read it with `fs_attach_file`.
- `score` is comparable only within one result set. `relevance` runs from 0 to 1, but what it measures depends on the tool. In `query_text` it is the hit's score as a fraction of the best hit's, so the top hit is always 1 and even a weak result set passes any threshold. Use it to trim the tail relative to the best hit, not to judge whether anything matched. In `query_semantic` it is cosine similarity, which is absolute. `query_blended` follows its `mode`, and in `blended` mode it is the fused rank score as a fraction of the best a file could reach. Do not carry a threshold from one tool to another.
- `query_blended` hits list `matched_by`. A hit found by both indexes is usually the strongest.

## Narrowing instead of paging

Paging is bounded: `limit` is at most 100 and `offset + limit` cannot exceed 200, so a request beyond that is rejected with `index/invalid-query`. Narrow the search instead of paging deeper.

- `path_prefix` scopes to a folder and `exclude_paths` removes folders (whole path segments, so `old` excludes `old/` but not `oldstuff.md`). Use `exclude_paths` to keep an archive or a superseded draft from biasing the answer.
- `note_type` keeps notes whose frontmatter `type` matches.
- `min_relevance` drops weak hits.
- `sort` of `modified` finds recent notes, and `title` gives an alphabetical listing.
- `limit` of 0 returns only the total, which is a cheap way to size a query before fetching it.
- `query_text` reports an exact `total`. For `query_semantic` and `query_blended` the total counts a pool of at most 200 candidates, and `total_capped` says when more exist.

## Index freshness

Queries refresh the index for changed files as part of the call, so do not rebuild after your own writes. If results look stale, or you know large numbers of files changed outside the server, `query_index_status` reports per-index document counts, staleness, and the last build time. Use `query_index_rebuild` only after bulk changes made outside MCP, and pass a `budget_seconds` that fits your host's tool time limit, because the semantic phase is the slow part and some hosts restart the server if a call runs past their ceiling.

Every session on a vault shares its indexes, and each sees what the others write. A write that meets another session's index write waits for it briefly; if it still cannot get in, the write itself succeeds with an `index/busy` warning, and that note's index entry catches up on its next write or a rebuild. Do not rewrite the note to force it.

A rebuild never puts back an entry older than a write made while it ran, so rebuilding while other sessions write is safe.

`query_index_status`, and `vault_info`'s `indexes`, report each store's `health`: the text index (`text`), the link graph (`graph`), and the vector store (`semantic`). A store that cannot be read is reported, never a failed call, and the rest of search keeps working. A top-level `failure` means the vault could not be scanned for staleness; each store's own health still stands.

- `ready`: nothing to do.
- `empty` or `incompatible` (link graph only): the graph has not been rebuilt from the vault, or was built by another version, so it holds at most the notes written since and its link answers are incomplete. Rebuild it with `query_index_rebuild` and `index: graph`.
- `unreadable`: `failure` gives the `code`, `message`, and `remediation`, and queries against that store are refused with the same code.
  - `index/busy`: another process held the store. Retry shortly.
  - `index/undecodable`: rebuild that index.
  - `index/corrupt`: the store's files are damaged. The server moves a damaged store aside and rebuilds it by itself when it opens the vault; `query_index_rebuild` for that index, or `doctor_resolve`, does it on demand. Run it once, never in a loop.
  - `index/in-use`: the damaged store is still open, in another contextos process or in a call still running, so it cannot be moved aside yet. Retry once shortly; if it persists, pass the remediation to the operator: the other processes must stop or release it first.
  - `index/storage`: a disk or permissions problem for the operator.
- `last_recovery` says when a damaged store was moved aside and where (`moved_to`). Its files are kept for diagnosis. Tell the operator once, and never delete them yourself. A rebuild that recovered a store lists it in `recovered`.

## The link graph

The graph holds every link in every indexed note: wikilinks, embeds, and Markdown links (`[text](path)`, `![alt](path)`, reference-style links, a path in angle brackets or URL encoded). A link inside code, a `%%` comment, or a template placeholder (`{{...}}`, or a wikilink whose whole target is in angle brackets) is not a link. Every link is resolved by the rule Obsidian uses, from the linking note's folder and each folder above it, then by file name, against every file in the vault, so a link to an image, a PDF, a canvas, a base, or a note in a search-excluded folder resolves. A target ending in `/` names a folder and resolves to its `index.md`.

The graph reconciles with the vault before it answers, so edits made outside the server (Obsidian, a sync client, a shell) are seen without a rebuild.

`query_graph` takes an `operation`:

- `backlinks`: what links to a note. Run it before moving, renaming, or deleting a note.
- `neighbours`: notes linked from, to, or around a note, with `direction` and `depth`. Keep `depth` small, because the result grows quickly.
- `path`: the shortest link path between two notes (`from` and `to`).
- `orphans`: notes with no links in or out. A note whose links could not be read is never listed, since its outgoing links are unknown.
- `unresolved`: every link in the vault that finds no file or several, sorted by `source` then `line`.
- `unlinked`: every note that no other note links to, whatever it links out to.

For the links of one known note, `links_read` is cheaper than a graph query: `direction: out` for its outgoing links, `in` for the links to it, and `both` for all. `backlinks` returns the same incoming links as graph nodes and edges.

### Reading a graph result

`neighbours`, `backlinks`, `path`, and `orphans` return `nodes` and `edges`. Group nodes by `kind`, never by `phantom` alone:

- `note`: an indexed note.
- `file`: an existing file that is not an indexed note, such as an image, a PDF, a canvas, a base, or a note in an excluded folder. It appears only while a link reaches it.
- `not-found`: a link target no file answers to. Its `path` is the target as written.
- `ambiguous`: a target several files answer to. `candidates` lists them. `phantom` is `true` for these last two.
- `unreadable` (a field, not a kind) on a `note` node says why the note's links could not be read, for example an unclosed `[[`. Such a note has no outgoing edges in the graph.

An edge's `kind` is the form the link was written in: `wikilink`, `wikilink-embed`, `markdown`, or `markdown-embed`. A note linked only by a Markdown link has a backlink.

### Finding broken links and unlinked notes

- Use `unresolved` for an audit or a repair pass. Each entry has `source`, `line`, `text` (the link exactly as written), `target` (heading and block reference removed, angle brackets and URL encoding undone), `form`, `kind`, and `candidates` for an ambiguous link. `kind` is `not-found`, `ambiguous`, or `unreadable`. An `unreadable` entry is a note whose links cannot be parsed, listed once with the reason in `text` and no `line`, `target`, or `form`: fix that note first, because its other links are unknown. A missing entry always means a sound link.
- Fix an `ambiguous` link by giving it a path that names one file. Fix a `not-found` link by correcting the target or removing the link; never guess at the intended file when more than one is plausible, and ask the operator.
- The list is complete and paged: `offset`, `limit` (default 200, at most 1000), and `total`. Walk it by advancing `offset` by the entries returned until `offset` reaches `total`. `path` limits it to a folder and is written like any other `path` parameter, such as `memory/wiki` or `{vault}://memory/wiki`. It must name an existing folder of the vault being queried: a folder that does not exist is refused with `path/not-found`, a file with `path/not-a-directory`, and a folder of another vault with `index/invalid-query`, so a mistyped scope can never read as a clean audit.
- `unlinked` returns `notes` (`path`, `title`) with the same `offset`, `limit`, `total`, and `path`. Use it to find notes to link from somewhere, not as a defect list: a note is often legitimately linked from nowhere. `index.md` files never appear, and a note listed only in its folder's managed `index.md` is unlinked. `orphans` is narrower, because a note with outgoing links is never an orphan.
- Notes in `[vault.links] exclude` folders (by default `templates`, `memory/events`, `memory/jobs`, and `.contextos`, plus the search exclusions) are never checked as link sources, and a link from one does not count against `unlinked`, although `backlinks` and `links_read` with `in` still list it. Links into those folders still resolve.
- `from`, `to`, `depth`, and `direction` belong to the traversal operations, and `path`, `offset`, and `limit` to `unresolved` and `unlinked`. Mixing them is rejected with `index/invalid-query`.

## Querying by property

To find notes by their frontmatter, `query_text` accepts `fields` (equality filters), `tags`, and `note_type`, and returns ranked hits with metadata. `query` is still required, so pair the filters with a term the notes share. To evaluate a Base's view, use `base_query` (see [notes.md](notes.md)).
