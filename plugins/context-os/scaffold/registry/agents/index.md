# Agents: Index

Operator agent definitions. Delegated to as sub-agents via `<slug>:agent` in a task field. Not auto-activated.

An agent is a complete delegate: it composes a role (identity) with hats or a numbered method, declares what inputs it needs and what shape it returns, and runs as a sub-agent with its own model and tool scope. Unlike roles and hats, which change how the current session thinks, an agent does the work elsewhere and returns a result.

| Agent | Slug | Purpose |
| --- | --- | --- |

## Usage

In a prompt template, the Agent goes in the Task field:

```
Task: Delegate <specific task> to <slug>:agent.
```

The calling context supplies context, task, and the inputs the agent's definition requires. See [../prompts/framework.md](../prompts/framework.md) for the prompt structure.

## Adding an agent

Run `agent create <slug>` to open a guided interview that writes a new agent definition and its harness shim.

Each agent must include: identity (role composition), method (hat composition or numbered steps), an inputs contract, an outputs contract, and constraints.

## Relationship to roles and hats

| Concept | Scope | Defines |
| --- | --- | --- |
| Role | Session | Identity: who Claude is being |
| Hat | Task | Method: how Claude is thinking right now |
| Agent | Delegation | Delegate: who does the work elsewhere, and what comes back |

## Shims

Every definition here is mirrored by a generated harness shim in `.claude/agents/` so the runtime can spawn it. Shims are build artefacts: never edit them. Edit the definition here and the shim is regenerated on the next invocation.
