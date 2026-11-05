---
base: '[[memory/events.base|Events]]'
last_create: {{created_at}}
last_update: {{created_at}}
key_prefixes:
  S: 0
key_format: '{key_prefix}-{key_id}'
template: '[[templates/event|Event]]'
fixed_fields: [type]
event_kinds: registry/events
series_kinds:
  S: session.run-started
---

![[memory/events.base|Events]]
