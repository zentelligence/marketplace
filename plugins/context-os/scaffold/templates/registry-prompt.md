---
title: <Human-readable name>
category: <writing | analysis | planning | learning | deciding | general>
purpose: <one sentence: what task this prompt accomplishes>
status: draft
effectiveness: 1
time-saved: <estimate, e.g. "15 min">
updated: <% tp.date.now("YYYY-MM-DD") %>
---

## Prompt

```xml
<context>
What situation the model is in. Project, stakes, prior steps, relevant memory to load.
</context>

<task>
As {{Role}}:role wearing the {{Hat}}:hat, the single objective.
</task>

<inputs>
- file or data
</inputs>

<constraints>
- rule or limit
</constraints>

<output>
Structure of the response: format, length, required sections.
</output>

<verify>
How to assess correctness. The test the response must pass.
</verify>
```

<!--
Filename: registry/prompts/<category>/<slug>.md. Prompts are a construction tool: returned to the operator to review, edit, and send, never activated by Claude. See ../framework.md for the KERNEL+V rationale. Normally authored via `prompt create <slug> in <category>` or `prompt draft <description>`, which also adds a row to registry/prompts/<category>/index.md.
-->
