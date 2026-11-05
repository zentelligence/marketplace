---
type: decision
title: "{{Decision title}}"
description:
date: <% tp.date.now("YYYY-MM-DD") %>
status: adopted
applies_to: []
superseded_by:
---

# {{Decision title}}

## Context

[The situation or problem about the vault's own design or operation that forced a choice.]

## Options considered

[Alternatives weighed, with the trade-off that settled it.]

## Decision

[The rule now in force, stated precisely enough to apply without this entry's context.]

## Migration backlog

[Existing non-compliant content, migrated opportunistically when next touched, or "none".]

## Recorded in

[Spec or standard file updated to carry the rule, e.g. memory/operating/vault-conduct.md, a standards/ file.]

<!--
A decision about the vault itself: its design, schema, conventions, structure, or operation.
A decision about the operator's own work outside the vault is a task (`task_type: decision`) in
memory/tasks/, not a record here.

Create with the contextos MCP base_record_create tool against memory/decisions.base with
`prefix: VD`, which assigns the next `VD-` id and stamps `base`; never set either by hand. Give
the heading the id once assigned: `# VD-NNN: Decision title`.

`status` is adopted or superseded. A decision is never edited to remove or rewrite what it said:
superseding one creates a new decision, and the old one's frontmatter changes to `status:
superseded` and `superseded_by` the new id, its body untouched. `applies_to` lists the
directories, file types, or operations this decision governs. The server lists it in
memory/decisions/index.md; memory/decisions.base provides live views.
-->
