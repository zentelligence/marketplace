---
status: proposed
created: <% tp.date.now("YYYY-MM-DD") %>
related: []
sources: [memory/raw/YYYY/MM/YYYY-MM-DD-slug.md]
---

# [Insight title: state the claim plainly, not the topic]

## Claim

[One or two sentences. A single atomic claim, not a summary of a topic or article.]

## Evidence

[Why this claim holds, drawing on the sources in the frontmatter.]

## Relations

- [<related insight title>](<related-slug>.md): <supports | contradicts | extends | depends on>

<!--
One file per insight. Zettelkasten-style semantic layer parallel to the wiki, memory/insights/. Every note has frontmatter, and `sources` lists the raw extracts, research, or wiki articles the claim rests on, as vault paths; never a **Source:** line in the body. `status` must be one of: proposed, adopted, dismissed. `confidence` (optional) must be one of: low, medium, high. Raise anything unresolved about the claim as a question task (base_record_create against memory/tasks.base, prefix Q) and add an `## Open Questions` section holding only links to them. Relative-path links only. The ContextOS MCP server lists it in its folder's index.md; never edit that file.
-->
