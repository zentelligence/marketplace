---
name: <Title> Agent
description: <one line: what this agent does and when to delegate to it>
model: <sonnet | opus | haiku | inherit>
tools: <read-only | read-write | all | an explicit list of tool names>
---

# Agent: <Title>

## Identity

<Role composition, e.g. "As the engineer:role.">

## Method

<Hat composition or a numbered method.>

## Inputs contract

- <item>: <what the caller must supply>
- <item>: <what the caller must supply>

## Outputs contract

- **<Section name>**: <what belongs here>
- **<Section name>**: <what belongs here>

## Constraints

- <hard stop or boundary>
- <hard stop or boundary>

<!--
Filename: registry/agents/<slug>.md. All four frontmatter fields and all five sections are required; a shim at .claude/agents/<slug>.md is generated from this file by scripts/agent_shim.py and must never be hand-edited. Normally authored via `agent create <slug>`, which also adds a row to registry/agents/index.md and regenerates the shim.
-->
