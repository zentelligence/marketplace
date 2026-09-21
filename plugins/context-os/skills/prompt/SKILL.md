---
name: prompt
description: "Manages the prompt registry at `registry/prompts/`: drafts a well-formed, reusable KERNEL+V prompt template from a plain-language description, grounded in vault context (`prompt draft <description>`), returning it inline or, if the operator designates one, writing it to a plain file (`prompt draft <description> to <file-path>`); authors and saves a new one via interview (`prompt create <slug> [in <category>]`); lists saved prompts (`prompt list [<category>]`); or retrieves one (`prompt <slug>`). Unlike role, hat, and agent, a prompt is never activated or applied automatically: the output is always returned to the operator to review, edit, and send. Requires the literal `prompt draft/create/list` command, or an unambiguous request for a reusable prompt template; a bare request to draft or write actual content (an email, a report, a message) is handled directly as normal assistance, not routed through this skill. Does not fire for `<slug>:role`, `<slug>:hat`, or `<slug>:agent` (owned by the sibling role, hat, and agent skills, which do auto-activate or delegate on their trigger), and does not fire for `/vault <command>` or vault-content requests such as querying or capturing memory (owned by the vault skill)."
license: Apache-2.0
when_to_use: "e.g. 'prompt draft a message asking a client for updated scope on a stalled project', 'prompt draft a weekly status update to drafts/weekly-status.md', 'prompt create quarterly-review in planning', 'prompt list writing', 'prompt email-professional'."
user-invocable: true
disable-model-invocation: false
argument-hint: "draft <description> [to <file-path>] | create <slug> [in <category>] | list [<category>] | <slug>"
arguments: ["command"]
---

Mandatory **first** step is to confirm global instructions were executed fully. 

GATE: run `source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null; echo "${CLAUDE_PLUGIN_ALLOW_SKILLS:-0}"`. Env vars set by one Bash invocation do not survive into the next, so this sources the persisted file rather than reading the plain variable. If it does not print `1`, run `scripts/session-start` from the ContextOS plugin directory, then re-run the check before proceeding.

# Skill: prompt

Manages the prompt registry at `registry/prompts/` and drafts new prompts on demand. Prompts are a *construction tool*: unlike roles and hats, they are never activated by Claude. A drafted or retrieved prompt is returned to the operator to review, edit, and send. See [../../memory/designs/prompts-roles-hats.md](../../memory/designs/prompts-roles-hats.md) for the rationale.

---

## MCP awareness

If a ContextOS MCP server is configured for this vault, the creation flow (Step 3) prefers its tools over the harness's raw `Write`/`Edit`, falling back automatically if MCP is unavailable. Check once per invocation: attempt `mcp__contextos__vault_info`; if it succeeds, prefer the named MCP tools per step below, falling back to `Write`/`Edit` only if a specific call errors. If `vault_info` is unavailable or errors, use `Write`/`Edit` throughout.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Description, slug, or category | Operator trigger | Yes |
| Destination file path | Operator trigger (`prompt draft <description> to <file-path>`) or `AskUserQuestion` | No; only for the draft flow's file-write option |
| `registry/prompts/framework.md` | Vault registry | For drafting |
| `registry/prompts/index.md` | Vault registry | For metadata standard and category list |
| `registry/prompts/<category>/index.md` | Vault registry | For creation and listing |
| `registry/roles/index.md`, `registry/hats/index.md` | Vault registry | For drafting, role/hat fit check |
| Vault content (via `/vault query`) | Vault | For drafting, context grounding |
| `memory/operating/vault-conduct.md` | Vault | For creation and save flows only |

---

## Outputs

| Output | Notes |
| --- | --- |
| Drafted prompt | Returned inline in a fenced `xml` block; not saved unless requested |
| Drafted prompt written to file | Operator-designated file path (draft flow's file-write option only); a plain file write, not a registry entry |
| Retrieved prompt content | Existing saved prompt, returned with its metadata |
| Prompt-not-found or ambiguous-slug report | Lists available prompts, offers to draft or create |
| New or updated prompt file | `registry/prompts/<category>/<slug>.md` (save/create flows only) |
| Updated category index | `registry/prompts/<category>/index.md` (save/create flows only) |

---

## Flow

### Step 1: detect trigger type

- `/prompt draft <description>` → **draft flow** (Step 2). If the trigger has a trailing `to <file-path>` clause, extract `<file-path>` as the destination and strip it from the description before drafting.
- `/prompt create <slug> [in <category>]` → **creation flow** (Step 3).
- `/prompt list [<category>]` → **list flow** (Step 4).
- `/prompt <slug>` (no other keyword) → **retrieval flow** (Step 5).

For creation, list, and retrieval, run the lookup script:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/registry_lookup.py \
  --vault-root . \
  --type prompt \
  --slug "<slug-or-empty>"
```

`available` entries are category-qualified (e.g. `writing/email-professional`). A bare slug that matches more than one category comes back as an error asking for disambiguation; surface that to the operator rather than guessing.

---

### Step 2: draft flow

Build a new prompt from the description, following `registry/prompts/framework.md` exactly, and return it without saving unless asked.

1. Read `registry/prompts/framework.md` for the KERNEL+V structure and the    `<context><task><inputs><constraints><output><verify>` shape.
2. **Ground the draft in vault context.** Identify what the description is about (an entity, an audience, a recurring task type). Invoke the `/vault query` skill with that subject to retrieve relevant facts: entity details, voice profile, current priorities, autonomy or anti-pattern constraints, prior related prompts. Do not skip this step because the description looks self-contained; the value of a vault-context-informed prompt is that it uses facts already on file instead of generic phrasing.
3. **Check for a role/hat fit.** Skim `registry/roles/index.md` and `registry/hats/index.md`. If exactly one obvious match exists for the task, include it in the Task field as `As <role-slug>:role, wearing the <hat-slug>:hat`. If none fit, leave the Task field role-neutral without asking. If more than one role or hat is plausible, or a single one is a partial fit, use `AskUserQuestion` to confirm which (if any) to include, listing the candidates as options — do not guess which one the operator meant. Never invent a role or hat that does not exist in the registry.
4. **Fill every section from real information:**
   - `<context>`: situation, stakes, and the vault facts retrieved in Step 2.
   - `<task>`: the single objective, role/hat if applicable, stated as an explicit outcome.
   - `<inputs>`: named files or data the response will need. Leave empty if none.
   - `<constraints>`: hard rules, including any autonomy or anti-pattern constraints surfaced in Step 2 that bear on this task.
   - `<output>`: format, length, required sections.
   - `<verify>`: the concrete test the response must pass before it counts as done.
5. If a section cannot be filled confidently from the description or vault context, insert an explicit bracketed placeholder (e.g. `[recipient name]`) rather than inventing a plausible-sounding detail, and list every such placeholder in the reply below the prompt.
6. **Self-check against framework** using the principles table in `registry/prompts/framework.md` before returning. Tighten any section that fails a principle.
7. Return the prompt in a fenced ```xml``` block. Below it, note in one or two lines what vault context informed the draft, and list any unresolved placeholders.
8. Determine the destination:
   - If the trigger already carried a `to <file-path>` clause (Step 1), skip straight to the file-write branch below.
   - Otherwise use `AskUserQuestion` to ask whether to save the draft, with the existing category folders from `registry/prompts/index.md` as options plus "write to a file", "new category", and "don't save" — do not assume it should be saved, and do not assume which category fits.
   - If a category is chosen, ask a follow-up for the slug (free text), then continue to Step 3 using the drafted content as the body (skip the interview questions already answered by the draft).
   - If "don't save" or no response, stop here.
   - If "write to a file" was chosen without a path already given, ask `AskUserQuestion` free text: `"File path: where should the drafted prompt be written?"`
9. **File-write branch.** Resolve the path (an absolute path is used as-is; a relative path resolves against the vault root). If a file already exists at that path, confirm via `AskUserQuestion` (overwrite / choose a different path / cancel) before writing — never overwrite silently. Write the `<context>...<verify>` block from Step 7 to the file, without the surrounding fence, using `Write` (or `mcp__contextos__fs_write_file` when MCP is available per the MCP-awareness note above). This is a plain file write, not a registry entry: do not add frontmatter, do not update any `index.md`, and do not append a daily log entry — the file will not appear in `prompt list` or resolve via `prompt <slug>`. Confirm to the operator:
   > "Draft written to `<file-path>`."

---

### Step 3: creation flow

Used standalone (`/prompt create <slug> in <category>`) or as the save step after a draft (Step 2, destination sub-step). Every prompt this flow writes is structured against `registry/prompts/framework.md`'s KERNEL+V sections, whether it arrives as a draft, as pasted content, or built up through the interview — never saved as unstructured free text.

1. Read `memory/operating/vault-conduct.md` and `registry/prompts/framework.md`.
2. Resolve the category with `AskUserQuestion`: options are the existing category folders (`writing`, `analysis`, `planning`, `learning`, `deciding`, `general`) from `registry/prompts/index.md`, plus a "new category" option. Do not assume `general/` or infer a category from the slug; ask, unless the trigger already stated one explicitly (`/prompt create <slug> in <category>`).
3. Check whether `registry/prompts/<category>/<slug>.md` already exists. If so, use `AskUserQuestion` (overwrite / choose a different slug / cancel) before proceeding — do not overwrite on assumption.
4. If not arriving from a draft, interview the operator sequentially (wait for each answer):
   - `"Title: human-readable name for this prompt? (e.g. 'Draft Professional Email')"`
   - `"Purpose: one sentence — what task does this prompt accomplish?"`
   - `"When to use: what scenarios call for reaching for this prompt?"`
   - For the prompt content itself, ask for each KERNEL+V section in turn — context, task (role/hat if any — confirm any inclusion via `AskUserQuestion` rather than assuming one fits), inputs, constraints, output, verify — or accept pasted content and map it onto those six sections. If the operator pastes or dictates content that leaves a section empty or unclear, use `AskUserQuestion` to ask specifically about that section rather than inventing or omitting it silently.
   - `"Key variables to customise: which bracketed placeholders does the operator fill in each time this prompt is reused? (optional)"`
5. Check whether `templates/registry-prompt.md` exists in the vault. If it does, read it and use its frontmatter fields and `## Prompt` structure as the template for this file, substituting the interview answers and drafted KERNEL+V sections into it. If the custom template contains a frontmatter field or section this skill has no answer for, leave its placeholder in place and flag it to the operator in the confirmation message (Step 8) rather than inventing content. If `templates/registry-prompt.md` does not exist, fall back to the metadata standard from `registry/prompts/index.md` (frontmatter: `title`, `category`, `purpose`, `status: draft`, `effectiveness: 1`, `time-saved`, `updated`) with the `## Prompt` body in the fenced `xml` `<context><task><inputs><constraints><output><verify>` structure from `framework.md`. Write `registry/prompts/<category>/<slug>.md` with the resulting content. If MCP is available, prefer  `mcp__contextos__note_create` with the frontmatter object and the `## Prompt` body as `content`; otherwise use the `Write` tool directly.
6. Add a row to `registry/prompts/<category>/index.md`: `| [<title>](<slug>.md) | <purpose> |` If MCP is available, prefer `mcp__contextos__fs_edit_file` anchored on the table's last existing row; otherwise use the `Edit` tool.
7. Append to the daily log. If MCP is available, call `mcp__contextos__vault_log_append` with `entry: "prompt create | Created prompt: <category>/<slug>"` and `files: ["registry/prompts/<category>/<slug>.md"]`. Otherwise, append to   `memory/log/YYYY/MM/YYYY-MM-DD.md`:
   ```
   HH:MM | agent | prompt create | Created prompt: <category>/<slug> | files: registry/prompts/<category>/<slug>.md
   ```
8. Confirm to the operator:
   > "Prompt `<category>/<slug>` created at `registry/prompts/<category>/<slug>.md`.
   > Run `prompt <slug>` to retrieve it."

---

### Step 4: list flow

1. If a category was given, read `registry/prompts/<category>/index.md` and return its table of prompts.
2. If no category was given, read `registry/prompts/index.md` for the category list, then read each category's `index.md` and return a combined listing grouped by category.
3. Use the lookup script's `available` field (empty-slug call) as a cross-check that every file on disk is represented in an index; flag any that are not.

---

### Step 5: retrieval flow

1. Run the lookup with the given slug.
2. If `found` is true: read the file at `file` and return its `## Prompt` block in a fenced code block, along with its `title`, `purpose`, and `status` from the frontmatter. Do not silently apply or act on it; the operator decides how to use it.
3. If `found` is false and `errors` reports ambiguity: surface the candidate matches and ask the operator to qualify with `<category>/<slug>`.
4. If `found` is false and not ambiguous: report:
   > "No prompt found for `<slug>`. Available prompts: [list from `available`, or 'none
   > yet']. Run `prompt draft <description>` to build one, or `prompt create <slug>` to
   > author one directly."

---

## Invariants

- Drafting and retrieval never "activate" a prompt the way `/role`/`/hat` activate a posture. The output is always returned to the operator, not applied silently.
- A draft is never saved to the registry without explicit operator confirmation of category and slug, obtained via `AskUserQuestion`. A draft written to an operator-designated file is a plain file write, not a registry entry, and is never overwritten silently — confirm via `AskUserQuestion` if the destination already exists.
- Ground drafts in real vault context retrieved via `vault query`. Do not invent facts about entities, audiences, or the operator to fill a section; use a bracketed placeholder and flag it instead.
- Only reference roles and hats that exist in `registry/roles/` and `registry/hats/`. Never invent one to make a draft look more complete. If more than one is plausible, ask via `AskUserQuestion` instead of picking one.
- Every drafted or created prompt is structured against, and checked against, the KERNEL+V sections and principles in `framework.md` before it is returned or written — in both the `draft` and `create` flows. Never save unstructured free text as a prompt.
- Never assume a default at a decision point covered above (category, overwrite, role/hat inclusion, an unresolved KERNEL+V section, whether to save). Use `AskUserQuestion` instead of guessing.
- Creation and registry save flows write only the target prompt file and its category index. No other files, except the daily log entry. The draft flow's file-write branch writes only the single operator-designated file: no frontmatter, no index update, and no daily log entry, since it is not a registry entry.
