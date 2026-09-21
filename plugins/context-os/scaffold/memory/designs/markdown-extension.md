# Markdown Extensions

This document defines a consistent vocabulary for triple-colon Markdown fences used across coding projects. It can be used in parallel with the `obsidian-markdown` skill if available. To install that skill add the `kepano/obsidian-skills` marketplace then add '+' `obsidian-skills`.

```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```

Triple-colon fences are not part of core Markdown. They are an extension supported by tools such as `markdown-it-container`, MyST Markdown, Docusaurus, VitePress, and other documentation systems. Exact rendering depends on the Markdown processor.

The purpose of this convention is to keep fenced containers semantic, portable, and easy to lint, transform, or render later.

---

## Core Rule

Use fences to describe the **meaning** of a block, not its visual appearance.

Prefer:

```markdown
:::warning
This migration may break consumers relying on the old field name.
:::
```

Avoid:

```markdown
:::red-box
This migration may break consumers relying on the old field name.
:::
```

The renderer can decide whether `warning` becomes amber, red, an icon, a collapsible block, or a PDF callout.

---

## Naming Convention

Use lowercase names.

Use singular nouns by default:

```text
note
warning
decision
risk
example
card
```

Use plural names only where the fence naturally contains a collection:

```text
cards
columns
```

Use attributes for layout, variants, or configuration:

```markdown
:::grid{cols=3 gap="md"}
...
:::
```

```markdown
:::note{title="Why this matters"}
...
:::
```

```markdown
:::cards{variant="compact"}
...
:::
```

Avoid encoding configuration in the fence name:

```markdown
<!-- Avoid -->
:::grid-3-columns
...
:::
```

Prefer:

```markdown
:::grid{cols=3}
...
:::
```

---

## Recommended Base Vocabulary

### 1. Admonition Fences

Use these for callouts, notices, warnings, and reader guidance.

| Fence | Use |
| --- | --- |
| `:::note` | Neutral supporting context |
| `:::info` | Useful information, explanation, or system state |
| `:::tip` | Practical suggestion or shortcut |
| `:::hint` | Nudge without giving the full answer |
| `:::important` | High-priority point that must not be missed |
| `:::warning` | Risk, caveat, or likely failure mode |
| `:::caution` | Softer warning; proceed carefully |
| `:::danger` | High-impact risk or serious consequence |
| `:::error` | Invalid, broken, failed, or impossible state |
| `:::success` | Completed, passed, or resolved state |

Example:

```markdown
:::warning
Run this migration only after confirming all downstream consumers have been updated.
:::
```

---

### 2. Reasoning and Workflow Fences

Use these for structured thinking, decision-making, and project notes.

| Fence | Use |
| --- | --- |
| `:::summary` | Compressed overview |
| `:::context` | Background needed to understand the section |
| `:::analysis` | Reasoned breakdown |
| `:::insight` | Non-obvious interpretation |
| `:::recommendation` | Suggested action or preferred path |
| `:::decision` | Chosen option and rationale |
| `:::rationale` | Reason behind a choice |
| `:::assumption` | Explicit assumption being made |
| `:::constraint` | Hard rule, limit, or boundary |
| `:::risk` | Identified risk |
| `:::mitigation` | How the risk is reduced |
| `:::tradeoff` | Tension between competing options |
| `:::question` | Open question |
| `:::todo` | Action item |
| `:::next` | Immediate next step |

Example:

```markdown
:::decision
Use `.gitattributes` as the repo-level source of truth for line endings.
:::

:::rationale
Global Git settings protect one developer machine. A repo-level rule protects every contributor and CI environment.
:::
```

---

### 3. Layout Fences

Use these only when the renderer supports layout-aware containers.

| Fence | Use |
| --- | --- |
| `:::stack` | Vertical layout |
| `:::row` | Horizontal layout |
| `:::columns` | Multi-column prose or content |
| `:::grid` | Grid layout |
| `:::cards` | Collection of card items |
| `:::card` | Individual card |
| `:::panel` | Bordered or contained block |
| `:::section` | Major page or document section |
| `:::hero` | Top visual or introductory block |
| `:::banner` | Top visual or introductory block (alias for `:::hero`; preferred in site content) |
| `:::cta` | Call to action. Use `variant` for primary/secondary styling, `display="inline"` for inline context |
| `:::aside` | Secondary note or related material |
| `:::sidebar` | Supporting side panel or navigation |
| `:::footer` | Footer content |

Examples:

```markdown
:::stack
Content arranged vertically.
:::
```

```markdown
:::grid{cols=3 gap="md"}

:::card{title="Build"}
Compile and package the application.
:::

:::card{title="Test"}
Run unit and integration tests.
:::

:::card{title="Deploy"}
Release to the target environment.
:::

:::
```

---

### 4. Technical Documentation Fences

Use these for technical, operations, and implementation documentation.

| Fence | Use |
| --- | --- |
| `:::definition` | Formal definition |
| `:::example` | Example |
| `:::counterexample` | Non-example or what not to do |
| `:::principle` | Guiding design or operating principle |
| `:::pattern` | Recommended reusable structure |
| `:::antipattern` | Known bad pattern |
| `:::procedure` | Step-by-step process |
| `:::checklist` | Verification checklist |
| `:::reference` | Stable reference material |
| `:::implementation` | Build or implementation notes |
| `:::api` | API-specific block |
| `:::schema` | Data model or schema block |
| `:::migration` | Migration-specific instruction |
| `:::test` | Test case, test plan, or validation block |

Example:

```markdown
:::principle
Prefer explicit configuration over hidden defaults.
:::

:::example
Set line-ending behaviour in `.gitattributes` rather than relying only on each developer's global Git settings.
:::
```

---

### 5. Status Fences

Use these for reports, reviews, trackers, and CI-style documents.

| Fence | Use |
| --- | --- |
| `:::draft` | Work in progress |
| `:::pending` | Not yet done |
| `:::partial` | Partly complete |
| `:::blocked` | Cannot proceed |
| `:::pass` | Passed a check |
| `:::fail` | Failed a check |
| `:::unknown` | Unknown or unresolved |
| `:::deprecated` | Retained but discouraged |
| `:::experimental` | Not stable or exploratory |
| `:::stable` | Safe or default path |

Example:

```markdown
:::blocked
Deployment cannot proceed until the production secret has been rotated.
:::
```

---

### 6. AI Workflow Fences

Use these for AI-assisted development, prompt libraries, agent workflows, source extraction, and synthesis documents.

| Fence | Use |
| --- | --- |
| `:::input` | Raw input |
| `:::output` | Generated output |
| `:::prompt` | Prompt block |
| `:::response` | AI response |
| `:::critique` | Review of output |
| `:::revision` | Revised output |
| `:::instruction` | Operating instruction |
| `:::memory` | Durable reusable context |
| `:::source` | Source excerpt or reference |
| `:::extraction` | Extracted content |
| `:::synthesis` | Combined interpretation |
| `:::validation` | Check or verification |

Example:

```markdown
:::prompt
Act as a reviewer. Check this migration plan for hidden operational risks.
:::

:::validation
Confirm that every migration has a rollback path, an owner, and a verification step.
:::
```

---

## Minimal Starter Set

For most projects, start with this smaller set.

```text
note
info
tip
important
warning
danger
error
success
summary
context
recommendation
decision
assumption
constraint
risk
tradeoff
question
todo
next
example
counterexample
principle
pattern
antipattern
procedure
checklist
pass
fail
blocked
draft
stable
experimental
stack
grid
cards
card
panel
section
cta
```

Do not add new fence types casually. Add a new fence only when it carries a distinct semantic meaning that cannot be handled by an existing fence plus attributes.

---

## Attribute Convention

Use brace-style attributes where supported:

```markdown
:::note{title="Important context"}
...
:::
```

Recommended common attributes:

| Attribute | Use |
| --- | --- |
| `title` | Human-readable title |
| `id` | Stable block identifier |
| `variant` | Visual or behavioural variant |
| `cols` | Number of grid or column items |
| `gap` | Layout gap size |
| `collapse` | Whether block should be collapsible |
| `open` | Whether collapsible block starts open |
| `level` | Severity, depth, or hierarchy where needed |
| `display` | `block` (default) or `inline` — controls whether the fence renders as a block or span-level element. Primarily used with `:::cta` |

Examples:

```markdown
:::warning{title="Breaking change"}
This API response removes the legacy `name` field.
:::
```

```markdown
:::grid{cols=2 gap="lg"}
...
:::
```

```markdown
:::details{title="Advanced notes" open=false}
Additional implementation detail.
:::
```

```markdown
:::cta{variant="primary"}
[Book a conversation](https://my.cal.au/booking/example)
:::

:::cta{variant="secondary"}
[Learn more](/about/detail)
:::
```

```markdown
:::cta{variant="primary" display="inline"}
[Register now](/offer/register)
:::
```

---

## Practical Rules

1. Prefer semantic names over presentation names.
2. Keep the vocabulary small.
3. Use attributes for configuration.
4. Use layout fences only where the renderer supports them.
5. Avoid duplicate meanings, such as both `alert` and `warning`, unless your renderer already requires them.
6. Do not use fences where a normal Markdown heading, list, table, or code block would be clearer.
7. Keep nested fences shallow. Deep nesting becomes hard to read and easy to break.
8. Use one fence for one purpose. Do not overload `:::note` to mean warning, decision, and example.

---

## Example Project Section

```markdown
# Deployment Plan

:::summary
Deploy the service using the existing release pipeline after the database migration has been verified in staging.
:::

:::assumption
The staging dataset is representative enough to expose migration timing and constraint failures.
:::

:::risk
The migration may lock high-write tables for longer than the deployment window allows.
:::

:::mitigation
Run the migration during low-traffic hours and verify lock duration in staging first.
:::

:::decision
Proceed with a two-step migration: add nullable column first, backfill second, enforce constraints last.
:::

:::next
Prepare the staging migration runbook and capture timing metrics.
:::
```

---

## PDF Render Fences

These fences are processed before markdown parsing. They have no effect in Obsidian or other renderers, which will ignore them gracefully.

| Fence           | Effect in PDF                                  | Obsidian behaviour                 |
| --------------- | ---------------------------------------------- | ---------------------------------- |
| `:::page-break` | Inserts a CSS `page-break-before: always` div. | Ignored (renders nothing visible). |

**Usage:**

```markdown
:::page-break
:::
```

The closing `:::` is optional but recommended for readability. A bare `:::page-break` with no closing line is also accepted by the renderer.

**When to use:** between major sections in a long document where you want a section to always start at the top of a new page, regardless of how content reflows.

---

## Suggested Renderer Mapping

A renderer may map fences like this:

| Semantic Fence | Possible Visual Treatment |
| --- | --- |
| `note`, `info` | Neutral callout |
| `tip`, `success`, `pass` | Positive callout |
| `warning`, `caution` | Amber callout |
| `danger`, `error`, `fail` | Red callout |
| `decision`, `recommendation` | Strong bordered decision block |
| `risk`, `tradeoff`, `assumption` | Analysis callout |
| `stack`, `grid`, `cards` | Layout containers |
| `draft`, `experimental`, `deprecated` | Status labels or banners |

The document author should not rely on a particular colour or icon. The fence should remain meaningful even when rendered as plain text.
