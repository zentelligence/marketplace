---
type: task
title: "{{Decision to make, as a question or a choice}}"
task_type: decision
state: proposed
entity: "{{entity}}"
assignee: "{{team member slug}}"
priority: normal
created: <% tp.date.now("YYYY-MM-DD") %>
updated: <% tp.date.now("YYYY-MM-DD") %>
start_after:
finish_by:
scheduled:
due:
completed:
cancelled:
recurrence:
parent:
depends_on: []
blocks: []
related: []
waiting_on:
on_completion:
origin:
claimed_by:
claimed_until:
tags: []
aliases: []
---

# {{Decision to make, as a question or a choice}}

## Context

[What has to be decided, why now, the options, and what each would mean.]

## Tasks

[The steps, in order.]

## Verify

[How the outcome will be checked before the task moves on.]

## Questions

[Questions the assignee could not answer alone, each dated and attributed, with its answer written beneath it. Empty while there are none.]

## Outcome

[The recommendation or the decision taken, by whom, and why, with links to the evidence. Recorded before the decision is adopted or dropped.]

<!--
Create with the contextos MCP base_record_create tool against memory/tasks.base, which assigns `id`
(the D- series) and stamps `base`; never set either by hand. `type` and `task_type` are fixed by this
template. A decision starts in proposed. The full field reference is the closing comment of templates/task.md.
-->
