---
type: event
kind: "{{kind}}"
severity: "{{info | warning | error}}"
at: "{{RFC 3339 time in UTC}}"
entity: "{{entity}}"
subject: "{{link to the note the event is about}}"
subject_id: "{{key of the subject, when it is a record}}"
subject_path: "{{path of the subject when the event happened}}"
subject_base: "{{base the subject is a record of}}"
actor: "{{assignee/run id}}"
---

# {{What happened}}
