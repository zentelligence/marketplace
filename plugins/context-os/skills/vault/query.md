# Skill: vault query

---

## Purpose

Answer questions from vault knowledge. Uses indexes as the retrieval layer; minimal file reads. Does not grep or scan the full wiki tree.

Mandatory: invoke vault-query any time the operator asks a question about vault content. Do not navigate `memory/wiki/` manually before running this skill.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Question or topic | Operator prompt or calling skill | Yes |
| `memory/index.md` | Vault | Yes, entry point |

---

## Outputs

| Output | Notes |
| --- | --- |
| Answer or retrieved content | Drawn from wiki articles; cites source file paths |
| Suggested follow-ups | Where knowledge gaps or open questions were found |

---

## Flow

### Step 1: pre-process query

Extract structured arguments from the operator's natural-language query. Output as JSON only (do not display this to the operator):

```json
{
  "domains": ["<wiki domain folder names, e.g. personal-development, technology>"],
  "topics":  ["<topic folder names or substrings>"],
  "keywords": ["<2-5 free terms likely to appear in article titles or Key Takeaways>"]
}
```

Rules:
- `domains`: match against first-level folder names in `memory/wiki/`. Empty = all domains.
- `topics`: match against second-level folder names. Empty = all topics within matched domains.
- `keywords`: 2-5 terms covering the core concepts being queried.
- If the query is vague or cross-domain, prefer empty `domains`/`topics` and rely on `keywords`.

### Step 2: retrieve candidates

If MCP is available (see the vault router's MCP awareness section):

1. Call `mcp__contextos__query_text` with `query` built from the `keywords` (fold `domains`/`topics` into `path_prefix` where they map cleanly to a wiki folder), returning ranked hits with heading-aware snippets. Treat each hit like a    `candidate_article` in Step 3: still read the file in full before citing it.
2. Call `mcp__contextos__query_graph` with `operation: "backlinks"` (or `"neighbours"`) from any article `query_text` surfaced, to pull in linked context `query_text` alone would miss, and `operation: "orphans"` to help identify gaps.
3. If `[vault.search] semantic = true` is configured, also try `mcp__contextos__query_semantic` for broader-recall hits a keyword match would  miss. If it errors (semantic search not enabled for this vault), skip it silently — there is no script equivalent for this part specifically.
4. If any of the above errors or the tools are not registered, fall back to the script below for the whole retrieval step rather than mixing partial results.

Otherwise, run the retrieval script:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
echo '<JSON from Step 1>' | python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_query.py --vault-root .
```

The script runs index traversal, a YAML-based full-vault scan, an entities scan, and
an insights scan. Returns a JSON payload with:
- `candidate_articles`: ranked wiki articles
- `candidate_entities`: ranked entity files
- `candidate_insights`: ranked insight notes

### Step 3: review candidates

The review discipline below applies the same way regardless of whether candidates came from the MCP tools or the script in Step 2.

**candidate_articles** (ranked by `relevance_score`):
1. Select 1 to 3 articles with highest score and best semantic fit.
2. Read each selected article in full using the Read tool.
3. Use `sources` field for provenance without opening raw files first.

**candidate_entities** (ranked by `relevance_score`):
1. Select any entity files with score > 0.3 relevant to the query.
2. Read each selected file in full.

**candidate_insights** (ranked by `relevance_score`):
1. Select any insights with score > 0.3 and `status: adopted` or `status: proposed`.
2. Read each selected insight file in full.
3. Note: `status: dismissed` insights are excluded by default.

If `missing_indexes` is non-empty, surface each as a vault hygiene note.

### Step 4: synthesise answer

- Answer from the full article and insight text.
- For wiki articles: cite with relative-path link plus the article's `**Source:**` line.
- For insight notes: cite with relative-path link; note `confidence` level and `status`.
- If an insight is `status: proposed`, flag this: it has not yet been adopted as a working principle.
- If the answer is substantial and reusable, offer to file it as a new wiki article.
- If the question cannot be answered from vault content: state what is known, identify the gap, and suggest `/vault research` if external sources are needed.

---

## Token discipline

- Total file reads: script output + 1-3 article reads + 0-2 entity reads + 0-2 insight reads.
- Do not read the full wiki tree.
- Do not open articles not identified via index traversal or the retrieval script.
- Do not read raw or research files unless the operator specifically requests primary source evidence.
