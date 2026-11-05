---
type: decision
id: VD-002
title: Vault decisions and questions share one register, and it covers only the vault itself
description: Decisions and questions about the vault's own design and operation live together in memory/decisions/; the operator's decisions and questions about their own work are tasks.
date: 2026-10-08
status: adopted
applies_to: [memory/decisions/, memory/decisions.base, memory/operating/vault-decisions.md, templates/registry-vault-decision.md, templates/registry-vault-question.md, memory/tasks/]
superseded_by:
---

# VD-002: Vault decisions and questions share one register, and it covers only the vault itself

## Context

VD-001 gave decisions and questions a register each: `memory/decisions/` with `decisions.base`, and `memory/questions/` with `questions.base`. The questions register reached beyond the vault itself, also holding gaps in vault content and questions only the operator could answer about their own affairs. Meanwhile the task register (`memory/tasks/`) gained decision and question task types, so a question or decision about the operator's own work had two possible homes.

## Options considered

- **Keep two registers.** Two folders, two bases, and two guides for records that share a scope and a lifecycle shape, and an overlap with question and decision tasks that each author has to resolve.
- **Fold vault decisions and questions into tasks.** Loses the distinction between commitments about how the vault works, which must be citable and superseded rather than closed, and the operator's day-to-day work.
- **One register for the vault itself, tasks for everything else.** Chosen: the vault's own design and operation has one place to look, and everything about the operator's work outside the vault has one place too.

## Decision

`memory/decisions/` holds every decision and every question about the vault itself: its design, schema, conventions, structure, and operation. A record's `type` is `decision` or `question`. Ids are issued by `memory/decisions.md`, the register's id sidecar: `VD-` for decisions and `VQ-` for questions, each series counted separately. `memory/decisions.base` shows adopted and superseded decisions and open and resolved questions.

Decisions and questions about how the operator runs their entities and acts outside the vault are tasks in `memory/tasks/` (`task_type: decision` or `question`). So is a gap in vault content that needs work to close, such as a source read only in part or research awaiting confirmation.

A record is never deleted or moved. A decision is superseded by a new decision, and a question is resolved in place.

## Migration backlog

A vault created before this decision keeps its `memory/questions/` folder and `questions.base`; nothing is deleted. Move each question about the vault itself into `memory/decisions/` with a `VQ-` id, `type: question`, and `created` in place of `raised`, and turn each other question into a question task. Remove the old folder and base once empty, with the operator's approval.

## Recorded in

`memory/operating/vault-decisions.md`, `memory/decisions/index.md`, `memory/decisions.base`, and the two register templates. Supersedes VD-001.
