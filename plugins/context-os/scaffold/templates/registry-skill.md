---
name: <slug>
description: "<one line: what this skill does and when it should be used — state the trigger phrasing explicitly, since this is what gets matched against operator intent>"
---

# Skill: <Display Name>

## Purpose

<What this skill does and why it exists, in a sentence or two.>

## Triggers

```
<phrase or command that invokes this skill>
```

## Tools required

<Read, Write, Edit, Bash, etc. List only what this skill actually needs.>

## Flow

### Step 1: <name>

<Imperative steps. This is an instruction set for Claude, not documentation
for a human — write steps, not prose explaining the feature.>

## Invariants

- <hard constraint this skill must never violate>

<!--
Filename: registry/skills/<slug>.md. Custom skill extending this vault's own capabilities beyond the plugin's built-in ones; selected per session, not auto-activated, unless operator manually loads into Cowork. Task-phase lenses belong in registry/hats/ instead. Add a row to registry/skills/index.md when this file is created: 
| [<Display Name>](<slug>.md) | <slug> | <one-line purpose> |
-->
