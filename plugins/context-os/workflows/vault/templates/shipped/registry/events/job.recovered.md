---
type: event-kind
kind: job.recovered
label: Job recovered
description: A job that had failed or been suspended ran successfully again.
severities: [info]
default_severity: info
fields:
  required: [package, workflow, job, run]
  optional: []
subject: required
---

# Event kind: Job recovered

## When to record

The ContextOS Web scheduler records this for the first scheduled run that succeeds after a failure that no success has followed, or after a suspension that was resumed. Runs that ended cancelled, interrupted, skipped, or degraded in between neither recover the job nor forget the failure. Record it once, with the successful run record as the subject. An ordinary success after a success records nothing.

## Severities

- **info**: the job is healthy again. This is the only severity the kind allows.

## Fields

- `package`: the name of the package the job's workflow belongs to, which together with the workflow and job identifies the job.
- `workflow`: the slug of the workflow the job belongs to, within the package.
- `job`: the slug of the job.
- `run`: the id of the run that succeeded, for example `R-13`.
