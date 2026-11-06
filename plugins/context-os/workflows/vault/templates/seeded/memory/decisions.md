---
base: '[[memory/decisions.base|Vault decisions]]'
key_prefix: VD
key_format: '{key_prefix}-{key_id}'
last_create: {{created_at}}
last_update: {{created_at}}
key_prefixes:
  VD: 0
  VQ: 0
template: '[[templates/registry-vault-decision|Vault decision]]'
series_templates:
  VQ: '[[templates/registry-vault-question|Vault question]]'
---

![[memory/decisions.base|Vault decisions]]
