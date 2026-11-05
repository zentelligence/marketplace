---
type: event-kind
kind: job.retired
label: Job retired
description: A saved job was retired because its successor was enabled, so it will not run again.
severities: [info]
default_severity: info
fields:
  required: [package, workflow, job, replaced_by, retired_at]
  optional: []
subject: required
---

# Event kind: Job retired

## When to record

The ContextOS Web scheduler records this when enabling a job's successor retires the job. Record it once per retirement, with the retired job's file as the subject. No task is raised, since the retirement follows a person's own act.

## Severities

- **info**: the job was replaced as intended. This is the only severity the kind allows.

## Fields

- `package`: the name of the package the job's workflow belongs to, which together with the workflow and job identifies the job.
- `workflow`: the slug of the workflow the job belongs to, within the package.
- `job`: the slug of the retired job.
- `replaced_by`: the key of the successor whose enabling retired the job.
- `retired_at`: when the retirement took effect, as an RFC 3339 time in UTC.
