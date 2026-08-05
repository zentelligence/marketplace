# Roles: Index

Cognitive-posture definitions. Selected by the operator per prompt. Not activated automatically.

Roles shape **how Claude reasons** and **what Claude prioritises** for the duration of a session. Each file defines what that role means in the operator's context specifically. When the operator writes `architect:role`, Claude draws on a rich, operator-specific definition rather than a generic interpretation of the title.

| Role | File | Cognitive signature |
| --- | --- | --- |

## Usage

In a prompt template, the Role goes in the Task field alongside the Hat:

```
Task: As <Role>:role, wearing the <Hat>:hat, <specific task>.
```

See [../prompts/framework.md](../prompts/framework.md) for the full prompt structure.

## Adding a role

Run `role create <slug>` to open a guided interview that writes a new role definition.

Each role must include: cognitive posture, priorities, characteristic questions, and avoids.

## Relationship to hats

| Concept | Scope | Defines |
| --- | --- | --- |
| Role | Session | Identity: who Claude is being |
| Hat | Task | Method: how Claude is thinking right now |

See [../hats/index.md](../hats/index.md) for the hat registry.
