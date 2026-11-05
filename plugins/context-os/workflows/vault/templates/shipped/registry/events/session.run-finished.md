---
type: event-kind
kind: session.run-finished
label: Session run finished
description: A scheduled agent session finished working the task list, or stopped early.
severities: [info, warning, error]
default_severity: info
fields:
  required: [run_id, members, dispatched, review, waiting]
  optional: []
subject: none
---

# Event kind: Session run finished

## When to record

A scheduled session records this once, when it ends, with the `run_id` its `session.run-started` returned and the counts for the run. A session that crashes records no finish: a started run with no finish and with its claims lapsed is how a reader sees it. The note may summarise what was done in `content`.

## Severities

- **info**: the run finished and nothing is left waiting on a person.
- **warning**: something is left waiting on a person, or the round limit stopped the run with work remaining.
- **error**: the run aborted.

## Fields

- `run_id`: the key `session.run-started` returned, for example `S-1042`.
- `members`: the slugs of the members the run worked for.
- `dispatched`: how many tasks the run handed out.
- `review`: how many of them were left in `review`.
- `waiting`: how many were left in `waiting`.
