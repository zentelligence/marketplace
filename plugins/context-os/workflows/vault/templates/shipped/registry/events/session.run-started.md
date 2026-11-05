---
type: event-kind
kind: session.run-started
label: Session run started
description: A scheduled agent session began working the task list.
severities: [info]
default_severity: info
fields:
  required: [members, scope]
  optional: []
subject: none
id_field: run_id
---

# Event kind: Session run started

## When to record

A scheduled session, such as the `dispatch` skill, records this before it claims any task. The server assigns the next key from the `S` series and returns it as `key`; that key is the run's id, and the session uses it in every claim (`claimed_by: <assignee>/<run id>`) and in `session.run-finished`. A session that cannot record its start claims nothing. Never supply `run_id`, and never make a run id from the clock.

## Severities

- **info**: the run started. This is the only severity the kind allows.

## Fields

- `members`: the slugs of the members the run works for.
- `scope`: one member's slug, or `team` for the whole team.
- `run_id`: assigned by the server, never supplied.
