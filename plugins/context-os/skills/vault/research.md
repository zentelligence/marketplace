# Skill: vault research

---

## Purpose

Search the web for sources on a given topic, save AI-discovered sources to `memory/research/`, then hand off to vault-ingest to compile findings into wiki articles. The primary mechanism for adding externally-researched knowledge to the vault.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Research topic or question | Operator prompt | Yes |
| `memory/operating/vault-conduct.md` | Vault | Yes |
| `memory/wiki/index.md` | Vault | To check existing coverage before searching |

---

## Outputs

| Output | Path |
| --- | --- |
| Research source file(s) | `memory/research/YYYY/MM/YYYY-MM-DD-<slug>.md` |
| Distilled transcript extract(s) | `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md` (retrieved transcripts only, via `distil-transcript.md`) |
| Wiki article(s) | Via vault-ingest handoff |
| Log entry | `memory/log/YYYY/MM/YYYY-MM-DD.md` |

---

## Flow

### Step 1: pre-flight

1. If no topic or question was given (a bare `/vault research` with nothing to research), ask: `"What would you like me to research?"` and wait for an answer before proceeding.
2. Read `memory/operating/vault-conduct.md`.
3. Check existing coverage. If MCP is available (see the vault router's MCP awareness section), call `mcp__contextos__query_text` with `query` built from the topic keywords and `limit: 5`. Otherwise, run the query script:
   ```bash
   session-start >/dev/null 2>&1
   source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
   echo '{"keywords":["<topic keywords>"]}' \
     | python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_query.py --vault-root . --max-candidates 5
   ```
   If adequate coverage already exists, report this and ask the operator whether to proceed.

### Step 2: search and retrieve

1. Formulate 2 to 4 search queries targeting the topic from different angles.
2. Execute searches and evaluate results for relevance, recency, and credibility.
3. Fetch full text for the 3 to 5 most relevant sources.

### Step 3: save to research

For each retrieved source, first determine whether it is a conversational transcript (webinar, masterclass, talk, interview, training, coaching session, sales call, podcast, or YouTube transcript) rather than an article, report, or reference page.

- **Transcript**: do not save the unprocessed body to `memory/research/`. Follow `skills/vault/distil-transcript.md` to process it into `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md`, preserving provenance in the frontmatter (`origin: "web transcript"`, `source_path: "<URL>"`). Carry the resulting raw path forward as this source's reference for Step 4, in place of a `memory/research/` path.
- **Non-transcript source**: write to `memory/research/YYYY/MM/YYYY-MM-DD-<slug>.md`. Check whether `templates/research-article.md` exists in the vault. If it does, read it and use its frontmatter and body structure as the template. If it does not exist, use the fallback structure below:

  ```markdown
  ---
  source_url: "<URL>"
  source_title: "<Page or document title>"
  date_retrieved: "YYYY-MM-DD"
  domain: "<best-fit wiki domain>"
  relevance: "<brief note on why this source was selected>"
  ---

  [Full extracted text from the source]
  ```

`memory/research/` is immutable after writing. Do not edit research files. Never retain an unprocessed transcript body there; it is a `memory/raw/` source once distilled.

### Step 4: hand off to `/vault ingest`

Invoke `/vault ingest`, naming exactly the file path(s) written in Step 3 (both the `memory/research/YYYY/MM/YYYY-MM-DD-<slug>.md` files and any `memory/raw/YYYY/MM/YYYY-MM-DD-<slug>.md` files produced by distilling a transcript) so this run compiles only this session's findings, not any other unrelated backlog sitting in `memory/research/`. `/vault ingest` recognises `memory/research/` sources directly and cites them from their permanent location; the distilled transcript files are already-processed `memory/raw/` extracts and compile the same way any other raw extract does. Never move or copy the retrieved files into an inbox first; both locations are append-only and already in extracted, citable form.

### Step 5: log

If MCP is available, call `mcp__contextos__vault_log_append` with `entry: "research | topic: <topic> | sources: <n> | research: [slugs]"` and `files` set to the written research file paths. Otherwise, append to `memory/log/YYYY/MM/YYYY-MM-DD.md`:
```
HH:MM | agent | research | topic: <topic> | sources: <n> | research: [slugs]
```

---

## Invariants

- `memory/research/` files are immutable after creation. Never edit them.
- Retrieved transcripts are the exception: never retain an unprocessed transcript body in `memory/research/`. Route it through `distil-transcript.md` so the processed extract lands in `memory/raw/` instead.
- Check for existing vault coverage before searching; avoid duplicating known knowledge.
- Evaluate sources for credibility. Do not save low-quality or unreliable sources.
