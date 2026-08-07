---
raised: <% tp.date.now("YYYY-MM-DD") %>
entity:
status: open
blocks: nothing
resolution_path:
resolved:
decision:
---

# {{Short question title}}

## Question

[The precise question, one or two sentences.]

## Answer

[Filled in on resolution, with the source. Blank while `status: open`.]

<!--
Filename: memory/questions/<slug>.md, lowercase-hyphenated, one file per question. `status`
must be one of: open, resolved. On resolution: set `status: resolved`, `resolved` to the date,
fill in `## Answer`, and propagate the answer to every file that carried the gap. The file is
never deleted or moved, only its frontmatter and `## Answer` change, a question accumulates in
place the same way a decision does when superseded. Not every question resolves into a vault
decision; set `decision` to the resulting VD id only when one is recorded, leave it blank
otherwise. `blocks` states what cannot proceed or be asserted until this is resolved, or
"nothing". `resolution_path` is one of: primary source to read, research to run, operator to
answer, external party. Add a row to memory/questions/index.md when new; memory/questions.base
(Obsidian Bases) needs no manual update.
-->
