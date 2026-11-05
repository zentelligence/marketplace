---
type: event-kind
kind: agent.delegated
label: Agent delegated
description: Work was delegated to a specialist through the agent skill.
severities: [info]
default_severity: info
fields:
  required: [agent, caller]
  optional: []
subject: optional
---

# Event kind: Agent delegated

## When to record

The `agent` skill records this once per delegation, when it has started the sub-agent, with the task the work belongs to as the subject when there is one. A host calling a projected agent directly does not pass through the skill, so that delegation is not recorded: no events for a specialist means asking its steward, not that it is unused.

## Severities

- **info**: the delegation started. This is the only severity the kind allows.

## Fields

- `agent`: the slug of the agent delegated to.
- `caller`: the slug of the member who delegated, the name of the skill that did, or `operator`.
