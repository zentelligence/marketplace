# Standard Prompt Template

Copy and fill. See [../framework.md](framework.md) for the KERNEL+V rationale.

```xml
<context>
What situation the model is in. Project, stakes, prior steps, relevant memory to load.
</context>

<task>
As {{Role}}:role wearing the {{Hat}}:hat, the single objective.
</task>

<inputs>
- file or data
- file or data
</inputs>

<constraints>
- rule or limit
- rule or limit
</constraints>

<output>
Structure of the response: format, length, required sections.
</output>

<verify>
How to assess correctness. The test the response must pass.
</verify>
```
