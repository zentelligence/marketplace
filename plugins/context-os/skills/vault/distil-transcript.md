# Skill: vault distil transcript

---

## Purpose

High-fidelity extraction and structuring of conversational transcripts (masterclasses, webinars, coaching calls, training sessions, sales calls) into `memory/raw/`. Completeness over compression: the goal is a durable, referenceable extract, not a summary. Offers handoff to `/vault ingest` after writing.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Transcript file | `inbox/` or uploaded directly | Yes |
| `memory/operating/vault-conduct.md` | Vault | Yes |

---

## Outputs

| Output | Path |
| --- | --- |
| Distilled extract | `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md` |

---

## Flow

### Step 1: pre-flight

1. If no transcript was provided (a bare `vault distil-transcript` with nothing to process; not uploaded in this session and not found in `inbox/`), ask the operator to paste the transcript, upload it, or place it in `inbox/`, then wait for a response rather than stopping silently.
2. Read `memory/operating/vault-conduct.md`.
3. Confirm the source is a conversational transcript (not a document or export; those go through `/vault ingest` directly).
4. Identify: format (video transcript, audio transcript, structured Q&A, etc.), speaker(s), and date if available.

### Step 2: profile the file

Before reading any content, run a profiling pass to pick a safe reading strategy. Some transcript exports (raw JSON, SRT-style captions collapsed to one line, etc.) contain pathologically long lines that the `Read` tool will truncate if read naively. This must happen before any `Read` tool call on the transcript.

`$FILE` is the transcript's absolute path. For a file in the vault, that is the vault's `path` from `vault_info` joined with its vault-relative path. These commands only read; the extract is still written through ContextOS MCP. If this session's shell cannot reach the file, read it with `mcp__contextos__fs_read_text_file` instead, reading in byte parts instead of successive `range` parts: pass `offset` (from 0) and `length`, keep the first part's `version` and pass it as `expected_version` on every later part, and continue from each part's `next_offset` until it is -1. A part is read by seeking, so a transcript with very long lines is read completely. If a part fails with `io/conflict` the file changed: start again from the beginning.

```bash
wc -l -c "$FILE"
awk '{ if (length > max) max = length } END { print "max_line_chars=" max }' "$FILE"
```

Interpret the output and select a reading mode:

| Condition | Reading mode |
| --- | --- |
| Lines ≥ 20 and max line < 50,000 chars | **Normal**: `Read` the file in one pass |
| Lines < 5 and max line ≥ 50,000 chars | **Chunked**: file is a blob; use `awk` to extract 8,000-char windows |
| Lines ≥ 5 and max line ≥ 50,000 chars | **Hybrid**: read short lines normally; extract oversized lines in chunks |
| File not found or unreadable | Stop and ask the operator for the correct path before proceeding |

Record the chosen mode; note it in `## Open questions` if chunked or hybrid reading was required, since partial-window extraction risks missing context at window boundaries.

### Step 3: read the transcript

1. If the transcript content was pasted inline, proceed directly to Step 4.
2. If a path is given, apply the reading mode determined in Step 2:
   - **Normal**: read the file in full with the `Read` tool.
   - **Chunked**: extract successive 8,000-char windows from the longest line(s):
     ```bash
     awk 'NR==LINE{print substr($0, START, 8000)}' "$FILE"
     ```
     Increment `START` by 8,000 until the line is exhausted. Track position to avoid gaps.
   - **Hybrid**: use `Read` for standard lines; apply the chunked approach for any line exceeding 50,000 chars.

### Step 4: extract

Extract the transcript into a structured Markdown document. Completeness is the primary goal. Preserve the speaker's language and specific examples; do not paraphrase into summaries.

Check whether `templates/distil-transcript.md` exists in the vault. If it does, read it and use its frontmatter and section structure as the template. If it does not exist, use the fallback structure below. Write it with `mcp__contextos__note_create` to `<vault>://memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md`, passing the frontmatter as structured fields.

```markdown
---
origin: "<session title or topic>"
source_path: "<original filename>"
captured: "YYYY-MM-DD"
summary: "<one-line summary of what this session covers>"
type: "transcript"
speakers: "<names or roles>"
domain: "<best-fit wiki domain>"
---

# [Session Title or Topic]

## Context

[Who is speaking, to whom, in what setting. 2-4 sentences.]

## Key claims and insights

[Numbered list. Every significant claim, framework, story, or instruction extracted verbatim or near-verbatim. Do not paraphrase into summaries; preserve the speaker's language and specific examples.]

1. [Claim or insight]
2. ...

## Frameworks and models

[Any named frameworks, models, or structured methods introduced. Define each clearly.]

## Stories and examples

[Named stories, case studies, or examples used. Preserve enough detail to be referenceable.]

## Actionable instructions

[Specific steps, exercises, or practices the speaker recommended. Numbered. Exact language preferred.]

## Quotable lines

[Sentences worth preserving verbatim for their precision or impact.]

## Open questions

[Anything unclear, incomplete, or requiring follow-up from another source.]
```

`memory/raw/` is immutable after writing. Do not edit the raw extract after creation.

### Step 5: hand off

Tell the operator: "Transcript distilled to `memory/raw/...`. Run `/vault ingest` to compile into wiki articles, or run `/vault query` to search across this and other extracts."

---

## Invariants

- Completeness over compression. Preserve the speaker's exact language wherever possible.
- `memory/raw/` files are immutable after the session in which they were created. Never edit them.
- If the source is not a conversational transcript, redirect to `/vault ingest` instead.
