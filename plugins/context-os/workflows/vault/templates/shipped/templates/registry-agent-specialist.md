---
kind: specialist
name: {{name}}
description: "<one line: what this specialist does and when to delegate to it>"
tier: <fast | balanced | deep>
access: <all | read-only>
---

# {{name}}

## Identity

<Role composition and the narrow craft this specialist brings, e.g. "As the engineer:role, a reviewer of data migrations.">

## Purpose and success

<The enduring outcome this specialist serves, how success is recognised, and what apparent success would be misleading.>

## Relationships and handovers

<Who it receives assignments from and how, who it may delegate to, where its remit meets other agents', and who accepts the result. A specialist returns its work to the agent that delegated it; that agent keeps the task and answers for the result.>

Steward: <the slug of the member who looks after this definition; any member may delegate to it>

## Context and memory

<Authoritative sources, required reading, and entity boundaries; what persists between runs, if anything; and what it may propose or write to shared memory. Assume it starts each run knowing only what this definition and its brief supply.>

## Judgement and escalation

<How it handles ambiguity, conflicting instructions, insufficient evidence, and disagreement with its brief; which decisions stay with the delegating agent or {{OperatorName}}; and how it returns a question rather than deciding one of those itself.>

## Failure and recovery

<What it does after unavailable tools, partial execution, an interrupted session, conflicting edits, or a failed handover: what it leaves in place, what it reports, and how the caller can tell finished work from partial work.>

## Learning and change control

<How feedback reaches the steward and becomes an improvement proposal, who approves a change to this definition, and how revised behaviour is evaluated. A specialist never edits its own definition.>

## Activation and resource limits

<What triggers it, when it stays quiet, how much it may spend or delegate, and when it must stop or return for direction.>

## Inputs contract

<Required context and acceptable assignment types. A delegation missing a required item fails before the specialist starts, so state each item the caller must supply.>

- <item>: <what the caller must supply>

## Method or process

<The specific steps: the roles, hats, prompts, and skills it uses, in order, as a numbered method or a hat composition.>

## Outputs contract

<The deliverable and the evidence that supports it, as the exact sections the specialist returns.>

- **<Section name>**: <what belongs here>

## Verification

<How it checks its own output, when separate review is required, and what evidence the delegating agent needs before it can accept the result and mark its task complete.>

## Delegation rules

<Whether it may delegate at all, to which specialists, for what, and how deep. The default is that it does not: it does the work itself, and returns anything beyond its contract to the caller. Where it may, it stays answerable for what it returns.>

## Constraints

- <hard stop or boundary>

<!--
Specialist template. Specialists are one shared pool, each with a steward, and are added through `/agent propose`. A specialist is a narrow, task-scoped sub-agent with an inputs and outputs contract, delegated to with <slug>:agent by the operator, a member, or a skill. It does not work through the task lifecycle: it claims no task, and the delegating agent keeps ownership of the work. For a team member who holds a function and works from the task list, use registry-agent-member.md instead. Filename: registry/agents/<slug>.md, where <slug> is the lowercase-hyphenated identifier Claude Code and Codex use for the agent. `name` is the display name, for people to read, and is also the heading. `access` is optional and defaults to `all`; `read-only` is best effort, not a guarantee. Never use `model` or `tools`: they are host field names, and the server refuses a definition that has either. Keep every section heading; write "None" under one that does not apply rather than removing it.
-->
