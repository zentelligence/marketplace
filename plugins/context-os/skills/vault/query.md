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
  "keywords": ["<2-5 free terms likely to appear in article titles or summaries>"]
}
```

Rules:
- `domains`: match against first-level folder names in `memory/wiki/`. Empty = all domains.
- `topics`: match against second-level folder names. Empty = all topics within matched domains.
- `keywords`: 2-5 terms covering the core concepts being queried.
- If the query is vague or cross-domain, prefer empty `domains`/`topics` and rely on `keywords`.

### Step 2: retrieve candidates

Search with the ContextOS MCP query tools (see the [mcp-tools](../mcp-tools/search.md) search guide):

1. Call `mcp__contextos__query_blended` with a short phrase describing the question, folding `domains` and `topics` into `path_prefix` where they map cleanly to a `memory/wiki/` folder. It fuses keyword and semantic ranking, and answers from one index with a warning if the other is off.
2. Use `mcp__contextos__query_text` instead when the question turns on exact terms or a property filter (`tags`, `fields`, `note_type`).
3. Call `mcp__contextos__query_graph` (`backlinks` or `neighbours`) from the strongest articles to pull in linked context a ranked search alone would miss.
4. Search `memory/entities/` and `memory/insights/` the same way when the question touches an entity or a working principle.

If a search fails, report it. Keep the results of any search that succeeded, and say which method failed rather than discarding everything.

### Step 3: review candidates

Triage each hit from its `title`, `metadata` (description, summary, status, note type), and snippet before reading anything.

**Wiki articles:**
1. Select the articles with the strongest fit.
2. Read each selected article in full with `mcp__contextos__fs_attach_file`.
3. Use its `sources` field for provenance without opening raw files first.

**Entity files:** read any that bear on the question.

**Insight notes:**
1. Select insights with `status: adopted` or `status: proposed` that bear on the question.
2. Read each selected insight in full.
3. `status: dismissed` insights are excluded by default.

### Step 4: synthesise answer

- Answer from the full article and insight text.
- For wiki articles: cite with relative-path link plus the sources in the article's frontmatter `sources`.
- For insight notes: cite with relative-path link; note `confidence` level and `status`.
- If an insight is `status: proposed`, flag this: it has not yet been adopted as a working principle.
- If the answer is substantial and reusable, offer to file it as a new wiki article.
- If the question cannot be answered from vault content: state what is known, identify the gap, and suggest `/vault research` if external sources are needed.

---

## Token discipline

- Triage from search results first; read in full only the notes the answer depends on.
- Do not read the full wiki tree, and do not walk folders by hand.
- Do not read raw or research files unless the answer needs primary-source evidence or the operator asks for it.
