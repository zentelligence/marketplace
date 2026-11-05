---
type: event-kind
kind: job.failed
label: Job failed
description: A saved job's run failed, including a run that crashed before it could record anything.
severities: [error]
default_severity: error
fields:
  required: [package, workflow, job, run, code]
  optional: []
subject: required
---

# Event kind: Job failed

## When to record

The ContextOS Web scheduler records this when a job's run ends in failure, so a job that crashes before it can record anything of its own is still shown. Record it once per failed run, with the run record as the subject. A job does not record it for itself.

## Severities

- **error**: the run did not complete. This is the only severity the kind allows.

## Fields

- `package`: the name of the package the job's workflow belongs to, which together with the workflow and job identifies the job.
- `workflow`: the slug of the workflow the job belongs to, within the package.
- `job`: the slug of the job.
- `run`: the run's id, for example `R-12`.
- `code`: the stable error code the run ended with.
