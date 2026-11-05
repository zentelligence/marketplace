---
type: event-kind
kind: job.suspended
label: Job suspended
description: A saved job was suspended, so it will not run again until a person resumes it.
severities: [warning]
default_severity: warning
fields:
  required: [package, workflow, job, code, suspended_at]
  optional: []
subject: required
---

# Event kind: Job suspended

## When to record

The ContextOS Web scheduler records this when it suspends a job, for example after repeated failures. Record it once per suspension, with the job's file as the subject.

## Severities

- **warning**: the job has stopped running and needs a person to look at it. This is the only severity the kind allows.

## Fields

- `package`: the name of the package the job's workflow belongs to, which together with the workflow and job identifies the job.
- `workflow`: the slug of the workflow the job belongs to, within the package.
- `job`: the slug of the job.
- `code`: the stable code that explains why the job was suspended.
- `suspended_at`: when the suspension took effect, as an RFC 3339 time in UTC.
