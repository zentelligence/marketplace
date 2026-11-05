---
type: task
title: "{{Action-verb-first title}}"
task_type: action
state: next
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
attempts:
tags: []
aliases: []
---

# {{Action-verb-first title}}

## Context

[What the task is for, why it matters, and what done looks like.]

## Tasks

[The steps, in order.]

## Verify

[How the outcome will be checked before the task moves on.]

## Questions

[Questions the assignee could not answer alone, each dated and attributed, with its answer written beneath it. Empty while there are none.]

## Outcome

[What was done, links to every note written, and what was and was not verified. Recorded before the task moves to review or done.]

<!--
Create with the contextos MCP base_record_create tool against memory/tasks.base, which assigns
`id` (A- action, D- decision, Q- question, from task_type) and stamps `base`; never set either
by hand. One note per task under memory/tasks/, nested in subfolders as the operator prefers.

`state` is the only lifecycle field, and each `task_type` has its own states. Below is the starting
set; .contextos/tasks.toml holds the vault's own, which the operator may customise. An action is open
in backlog (not yet actionable), next (actionable), doing (being worked), waiting (started, then
held until whoever or whatever `waiting_on` names responds), or review (finished by an agent,
awaiting a person's check), and closed in done or dropped. A decision is open while proposed, and
closed when adopted or dropped. A question is open until it is answered or dropped. A new action
starts in next, a decision in proposed, and a question in open. There is no `status` field. A
review date, when one is wanted, is `scheduled`, set by whoever raises or edits the task.

Who may change state: the operator or assignee moves between backlog and next; the assignee
starts work (an agent session by claiming the task); an agent finishes into review, and a person
(or an agent given review authority) moves review to done or back to doing; a human assignee may
move doing to done; the operator, or an agent given cancel authority, drops a task; only the
operator reopens a closed task. Workflows only create tasks. An agent may research a decision or
a question and record its recommendation or answer under Outcome, leaving the task open; only the
operator or a human assignee adopts, answers, or drops one.

A task is blocked when a task in `depends_on` is still open. That is worked out, never stored as
a state, and a blocked task is not started. A team member who cannot work at all records that in
their own working state, not in a task.

`assignee` is a team member's slug, never a display name. `entity` is one of the vault's
entities. `waiting_on` names a team member's slug, or an external party in plain words. An agent
that needs an answer writes it under Questions, sets `state: waiting` and `waiting_on` to who must
answer; the answerer writes the answer and moves the task back to next.

`claimed_by` (`<slug>/<run-id>`) and `claimed_until` (ISO 8601 UTC) are set by an agent session
when it starts the task and cleared when the task leaves doing. `attempts` counts those claims: a
dispatching session adds one each time it claims the task, hands the third attempt to the chief of
staff, and leaves a fourth waiting on the operator. Only the operator clears it. `origin` is set only by a raiser
that may run again (a workflow, recurrence) so a rerun finds the task it already raised.
`recurrence` is `every <n> <unit>`; when a recurring task is done its next instance is created for
it. `on_completion` is an instruction to whoever closes the task, not a trigger. `depends_on`,
`blocks`, `related`, and `parent` are links to other tasks; `depends_on` and `blocks` mirror each
other. Entering done, adopted, or answered sets `completed`; entering dropped sets `cancelled`.
-->
