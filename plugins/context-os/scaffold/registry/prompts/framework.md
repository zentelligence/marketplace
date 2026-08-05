# Prompt Framework

## Principles

The principles that every well-formed prompt should satisfy:
**K**ey context, kept simple
**E**xplicit outcome, state the role and objective clearly
**R**epeatable structure with role and references, reusable and refinable across sessions
**N**arrow scope, but with nuance, clear task with important subtleties
**E**xplicit constraints, rules, boundaries, and format limits
**L**ogical structure, organise the prompt into clear sections
**V**erification loop, how the AI checks its output before returning

If a prompt violates principles, tighten it before sending. The structure below is the tool that makes principles easy to apply.

## Structure

```
Mandatory **first** step is to confirm global instructions were executed fully. 

<context>
What situation the model is in. Project, stakes, prior steps, relevant memory to load.
</context>

<tasks>
As {{Role}}:role wearing the {{Hat}}:hat, the single objective.
</tasks>

<inputs>
Data provided: files, pasted text, prior outputs, links.
</inputs>

<constraints>
Rules and limits. Hard stops. Things that must not happen.
</constraints>

<outputs>
Structure of the response: format, length, required sections.
</outputs>

<verify>
How to assess correctness. The test the response must pass.
</verify>
```

## Alignment with prompt structure

| Section | Aligned principles | Purpose |
| ------- | ------------------ | ------- |
| **Context** | K (key context), N (narrow scope with nuance) | Essential background without overloading; sets the situation clearly |
| **Task** | E (explicit outcome), R (role specification) | Defines what the AI must do and, where needed, the role it occupies |
| **Inputs** | R (repeatable structure), N (nuance) | References, examples, or data the AI needs to complete the task |
| **Constraints** | E (explicit constraints) | Rules, boundaries, and format requirements; applied to the whole response |
| **Output** | L (logical structure) | The contract: desired format, structure, and specifics |
| **Verify** | V (verification loop) | How the AI checks its work before finalising |

Together the principles ensure prompts are clear, intentional, repeatable, and verifiable, producing efficient, high-quality outputs.

## Why this shape

- **Context** before task prevents the model from guessing what situation it's in.
- **Task** with explicit Role and Hat removes ambiguity about posture and mode.
- **Inputs** are named, not assumed. If Claude needs a file, it's listed.
- **Constraints** are upfront, not scattered. They apply to the whole response.
- **Output** shape is a contract. No surprise formats.
- **Verify** is the feedback loop. Without it, the prompt is a wish.

## Role and hat composition

Roles and hats compose inside the task field:

```
Task: Act as the copywriter:role wearing the planner:hat, provide a clear schedule of social media content with topics and accompanying imagery guidance per platform and per day for the coming calendar month following the defined social media content guidelines.
```

See [../roles/index.md](registry/roles/index.md), [../hats/index.md](registry/hats/index.md), and [../skills/index.md](registry/skills/index.md) for the full sets.

## Related

- Blank prompt scaffold [general/standard](general/standard.md)
