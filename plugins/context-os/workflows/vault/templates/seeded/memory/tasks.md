---
base: '[[memory/tasks.base|Tasks]]'
key_prefix: A
key_format: '{key_prefix}-{key_id}'
last_create: {{created_at}}
last_update: {{created_at}}
key_prefixes:
  A: 0
  D: 0
  Q: 0
template: '[[templates/task|Task]]'
series_templates:
  D: '[[templates/task-decision|Decision task]]'
  Q: '[[templates/task-question|Question task]]'
fixed_fields: [task_type]
link_fields:
  depends_on: {inverse: blocks}
  blocks: {inverse: depends_on}
  related: {inverse: related}
  parent: {single: true}
---

![[memory/tasks.base|Tasks]]
