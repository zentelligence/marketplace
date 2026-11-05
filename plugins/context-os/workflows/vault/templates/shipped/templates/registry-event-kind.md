---
type: event-kind
kind: <dot.separated-kind-name>
label: <Display name>
description: "<one line: what happened>"
severities: [info]
default_severity: info
fields:
  required: []
  optional: []
subject: none
# id_field: <field the server fills with the next key from the kind's series in memory/events.md>
# retention_days: <days to keep this kind's info events, overriding the vault's window>
---

# Event kind: <Display name>

## When to record

<Who records this kind, and the moment they record it. A kind is recorded once per thing that happened, not once per step.>

## Severities

- **info**: <what an info event of this kind means>
- **warning**: <what a warning means, if the kind allows it>
- **error**: <what an error means, if the kind allows it>

## Fields

- `<field>`: <what it holds>

<!--
Filename: registry/events/<kind>.md, where the file's basename equals `kind`: lower-case dot-separated segments of letters, digits, and hyphens. A client records an event of this kind with base_record_create against memory/events.base, and the server validates it against this definition before writing anything.

`severities` is a non-empty subset of info, warning, and error, and `default_severity` is one of them. `fields.required` and `fields.optional` name the kind's own fields; a name may not be one the server stamps or every event carries (type, kind, severity, at, entity, subject, subject_id, subject_path, subject_base, actor) or a common note field (title, created, updated, tags, aliases, description). `subject` is `required`, `optional`, or `none`: whether the record links to the note the event is about. A recorder gives only the link, by key for a record such as a task (`[[a-071|A-071]]`); the server stamps `subject_id`, `subject_path`, and `subject_base` from the note it names.

`id_field` is optional. Name it when the event starts something others refer to: the server assigns the next key from a series declared under `key_prefixes` in memory/events.md and returns it as the call's `key`, and the caller never supplies it. `retention_days` is optional and overrides the vault's retention window for this kind's info events; warnings and errors are kept.

Never define a kind the server fires itself (task.*, member.state-changed, vault.degraded, vault.recovered): `doctor` reports it and it cannot be recorded. Changing a definition leaves records already written unchanged.
-->
