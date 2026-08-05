
Roles, hats, and the prompt structure belong in different places for different reasons.

## The Core Distinction

Ask: **is this something Claude activates, or something you construct before Claude sees it?**

- **Prompt structure** (Context/Task/Inputs/Constraints/Output/Verify) is a _construction tool_. It shapes what you send to Claude. Claude never needs to know the framework exists, it just receives well-formed prompts as a result.
- **Roles** are _cognitive postures_ Claude adopts. They shape how Claude reasons and what it prioritises.
- **Hats** are _task-phase lenses_ within a role. They narrow the mode of thinking for a specific moment.

This distinction determines where each lives. In practice, roles and hats are both loaded by a small **router skill** (`skills/role/`, `skills/hat/`), one skill per type, not one skill per definition. The router does the mechanical work, resolving a slug to a file, listing what's available, offering creation, but the definitions themselves live as plain markdown in the registry and never auto-activate from task content. See [How they compose](#how-they-compose-in-practice) below for why this is the resolution to the tension raised in the Roles section.

## Prompts

The KERNEL+V framework provides the structure:

```
registry/
  prompts/framework.md      # Documents KERNEL+V for your reference
  prompts/{{category}}/
    index.md                # Category listing
    {{slug}}.md              # Saved prompt, e.g. pre-filled for code review tasks
  prompts/general/standard.md  # Blank KERNEL+V scaffold
```

The `prompt` skill (`skills/prompt/SKILL.md`) manages this registry: `prompt draft <description>` grounds a new prompt in vault context (via `vault-query`) and the KERNEL+V structure before returning it; `prompt create <slug>` runs an interview and saves one directly; `prompt list` and `prompt <slug>` read back what's saved. None of these flows apply a prompt on the operator's behalf, drafted or retrieved content is always handed back for the operator to review, edit, and send. That's the line that keeps prompts out of the "Claude activates this" category even though a skill now manages the registry: the skill manages storage and drafting, not execution. The framework shapes your input; it's yours, not Claude's.

---

## Roles

The original question here was whether roles should be skills at all: making a role a skill sounds like it would mean Claude auto-activates a role based on keyword detection in the task, which is the wrong inversion. You choose the role; Claude adopts it, it should never guess.

The resolution is the **router pattern**: `skills/role/SKILL.md` is one generic skill that fires only on an explicit, deterministic marker, `<slug>:role` inline in a prompt, or `role create <slug>` as a standalone command. It never fires on semantic task content. On activation it runs `scripts/registry_lookup.py --type role --slug <slug>` to resolve the slug to `registry/roles/<slug>.md` (or report it missing, list what exists, and offer to create it), reads that file, and adopts the posture. Adoption is session-scoped: it persists until a new `<slug>:role` trigger replaces it, not just for the one prompt.

Each role file defines what that role means _in your context specifically_, for example:

```markdown
# Role: Architect

## Cognitive Posture
Systems-first. Evaluates decisions for long-term structural integrity, not short-term convenience. Identifies coupling, boundary violations, and constraint mismatches before they become debt.

## Prioritises
- Interface contracts over implementation detail
- Reversibility of decisions
- Explicit trade-offs over implicit assumptions

## Characteristic questions
- What does this decision close off?
- Where is the boundary, and is it the right one?
- What fails first under load or change?

## Avoids
- Premature concreteness
- Optimising locally at the expense of system coherence
```

`role create <slug>` interviews the operator for these sections, writes the file, and adds a row to `registry/roles/index.md`. No role content is ever invented by the router; an unknown slug is reported, not guessed at.

---

## Hats

Hats are _not_ auto-activated by task match either. They are manually invoked per prompt, and like roles they are implemented as a router skill, `skills/hat/SKILL.md`, because:

- They have structured instruction sets that are too long for inline prompts.
- They can reference external assets (checklists, frameworks, output templates).
- They benefit from a declared tool-permission level, a Critic hat should observe, not write files; a Refiner should be able to.

The router fires on `<slug>:hat` inline, or `hat create <slug>` as a standalone command, resolves the slug via the same `registry_lookup.py` script against `registry/hats/`, and applies the definition's posture, method, and output format directly, without narrating or quoting the definition back to the operator. Unlike roles, hat activation is  **task-scoped**: it applies for the current task only and is released once that response is complete.

Tool scoping is declared in plain language inside the definition, not as a machine-enforced frontmatter tool list: the file states one of `read-only`, `read+write`, `all`, or `none` under `## Tools permitted`, and the router skill treats that as a hard behavioural constraint for the duration of the task, surfacing a conflict rather than silently bypassing it if the task needs a tool the active hat doesn't permit.

Example, the Critic hat, in the actual current template:

```markdown
---
name: Critic Hat
description: Applies adversarial analysis to surface weaknesses, risks, and blind spots
---

# Hat: Critic

## Cognitive Posture

Adversarial but constructive. The goal is to find what's wrong before reality does. Not contrarian for its own sake.

## Tools permitted

read-only

## Method

1. Identify stated assumptions, which are load-bearing?
2. Find the failure mode of each key decision.
3. Surface what's been optimised for at the expense of what.
4. Name the risks that haven't been acknowledged.
5. Distinguish fatal flaws from acceptable trade-offs.

## Output format

- **Assumptions**: stated and unstated
- **Failure modes**: per decision
- **Unacknowledged risks**: named directly
- **Fatal vs. acceptable issues**: distinguished explicitly
- **Open questions**: what the author should be able to answer but probably can't

## Constraints

- Do not propose solutions. That is the Solver's job.
- Do not soften findings to protect feelings.
- Do not critique style when substance is the concern.
```

`hat create <slug>` interviews the operator for each of these sections (including the tools-permitted level), writes the file, and adds a row to `registry/hats/index.md`.

---

## How They Compose in Practice

The standard prompt structure naturally slots role and hat into the Task field:

```
Context: prompt task context

Task: Act as {{role}}:role wearing the {{hat}}:hat, specific task

Inputs: paths to files and folders, any associated format information

Constraints: limits, invariants, and directives

Output: file/s and any associated formatting information

Verify: Do not return as complete or finalised unless: conditions
```

Both markers in that Task field are deterministic router triggers, not semantic cues. The `role` router resolves `{{role}}` and adopts it for the session; the `hat` router resolves `{{hat}}` and applies it for this task; both go through the same `registry_lookup.py` script, which is also what the `prompt` skill uses to resolve saved prompt slugs. That script is the single source of truth for "does this slug exist," so no router ever invents a role, hat, or prompt that isn't actually on disk, it either loads the real definition, or reports what's available and offers to create one.

When role and hat are both active: the role defines identity, the hat defines method. They compose, reason as the role would, using the hat's procedure.

---

The separation matters: roles define _who Claude is being_, hats define _how Claude is thinking_, and KERNEL+V defines _what you're asking_. Conflating any two of these produces prompts that are either underdefined or over-constrained. Making roles and hats routable, rather than either hand-pasted or auto-activated, keeps the operator in control of  *when* posture and method engage while removing the copy-paste overhead of loading them manually each time.

---

## Future direction: a `wiki` CLI

Both routers, and the `prompt` skill, currently depend on a Claude session to interpret the trigger and call `registry_lookup.py` on the operator's behalf. An open idea is a `wiki` CLI, a deterministic command-line tool parallel to `scripts/vault_router.py` and `scripts/vault_scaffold.py`, that could query, list, and manipulate registry and wiki content directly from a shell. That would let an operator look up a role, hat, or prompt, or browse the wiki, without going through Claude Cowork or any AI session at all. Not yet built; worth revisiting once the router pattern above is stable and the shape of a non-Claude-Cowork operator workflow is clearer.
