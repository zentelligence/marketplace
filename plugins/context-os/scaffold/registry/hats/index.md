# Hats: Index

Task-phase lenses. Activated by the operator per task. Not auto-activated.

Hats narrow the **mode of thinking** for a specific task phase. Unlike roles (which define who Claude is being for a session), hats define how Claude is thinking at a specific moment. A hat is activated per task and released when that task response is complete.

| Hat | File | Purpose |
| --- | --- | --- |

## Usage

In a prompt template, the Hat goes in the Task field alongside the Role:

```
Task: As <Role>:role, wearing the <Hat>:hat, <specific task>.
```

See [../prompts/framework.md](../prompts/framework.md) for the full prompt structure.

## Adding a hat

Run `hat create <slug>` to open a guided interview that writes a new hat definition.

Each hat must include: cognitive posture, tools permitted, method (numbered steps), output format (required sections), and constraints.

## Relationship to roles

| Concept | Scope | Defines |
| --- | --- | --- |
| Role | Session | Identity: who Claude is being |
| Hat | Task | Method: how Claude is thinking right now |

They compose, not conflict. When both are active, reason as the role would, using the hat's procedure.
