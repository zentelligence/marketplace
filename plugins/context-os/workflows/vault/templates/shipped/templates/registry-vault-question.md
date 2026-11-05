---
type: question
title: "{{Short question title}}"
description:
created: <% tp.date.now("YYYY-MM-DD") %>
status: open
blocks: nothing
resolution_path:
resolved:
decision:
---

# {{Short question title}}

## Question

[The precise question about the vault's own design or operation, one or two sentences.]

## Answer

[Filled in on resolution, with the source. Blank while `status: open`.]

<!--
A question about the vault itself: its design, schema, conventions, structure, or operation, that
cannot be closed in the session that finds it. A question about the operator's own work outside
the vault, or a gap in vault content that needs work to close (a source read only in part, a
claim without a primary source, research awaiting confirmation), is a task (`task_type:
question`) in memory/tasks/, not a record here.

Create with the contextos MCP base_record_create tool against memory/decisions.base with
`prefix: VQ`, which assigns the next `VQ-` id and stamps `base`; never set either by hand. Give
the heading the id once assigned: `# VQ-NNN: Short question title`.

`status` is open or resolved. On resolution: set `status: resolved`, `resolved` to the date, fill
in Answer, and carry the answer into every file that held the gap. The record is never deleted
or moved. Not every question leads to a decision: set `decision` to the resulting VD id only when
one is recorded. `blocks` states what cannot proceed until this is resolved, or "nothing".
`resolution_path` is one of: primary source to read, research to run, operator to answer,
external party. The server lists it in memory/decisions/index.md; memory/decisions.base provides
live views.
-->
