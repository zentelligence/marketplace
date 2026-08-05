---
name: hat
description: "Load a task-phase hat definition from the vault registry and activate it for the current task."
---

# Skill: hat

Loads a hat definition from `registry/hats/` and activates its thinking mode, method, and output format. Activated when the operator uses `<slug>:hat` anywhere in their prompt. Also handles `hat create <slug>` to author new hat definitions.

---

## Triggers

```
<slug>:hat
hat create <slug>
```

Appears inline in the task field of a KERNEL+V prompt. Examples:

- `"As architect:role, wearing the critic:hat, evaluate the proposed schema."`
- `"Wearing the solver:hat, propose three solutions."`
- `"hat create refiner"`

---

## Tools required

`Read`, `Write`, `Edit`, `Bash`

`Write` and `Edit` are used only during hat creation. Normal activation uses only `Read` and `Bash`, subject to further restriction by the hat definition's `tools` field.

---

## MCP awareness

If a ContextOS MCP server is configured for this vault, the creation flow (Step 4) prefers its tools over the harness's raw `Write`/`Edit`, falling back automatically if MCP is unavailable. Check once per invocation: attempt `mcp__contextos__vault_info`; if it succeeds, prefer the named MCP tools per step below, falling back to `Write`/`Edit` only if a specific call errors. If `vault_info` is unavailable or errors, use `Write`/`Edit` throughout.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Hat slug | Inline `<slug>:hat` or `hat create <slug>` | Yes |
| `registry/hats/<slug>.md` | Vault registry | For activation |
| `registry/hats/index.md` | Vault registry | For available-hats listing |
| `memory/operating/vault-conduct.md` | Vault | For creation flow only |

---

## Outputs

| Output | Notes |
| --- | --- |
| Task response in hat's output format | Produced using hat's method and constraints |
| Hat-not-found report | Lists available hats and offers creation |
| New hat file | `registry/hats/<slug>.md` (creation flow only) |

---

## Flow

### Step 1: extract slug

Extract the hat slug from the trigger. Normalise to lowercase-hyphenated form.

Detect the trigger type:

- `<slug>:hat` in a larger prompt → **activation flow** (Steps 2-3).
- `hat create <slug>` as a standalone command → **creation flow** (Step 4).

Run the lookup for either trigger:

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/registry_lookup.py \
  --vault-root . \
  --type hat \
  --slug "<slug>"
```

### Step 2: activation - hat found

If `found` is true:

1. Read the hat definition at `file`.
2. Apply tool constraints from the `## Tools permitted` section. These are hard behavioural constraints for the duration of this task. See [Tool scoping](#tool-scoping) below.
3. Activate `## Cognitive Posture`. Follow `## Method` as a procedure. Produce output shaped by `## Output Format`. Respect `## Constraints` unconditionally.
4. Do not narrate or quote the hat definition back to the operator. Apply it directly.
5. Hat activation is **task-scoped only**: it applies for the current task and is released when the task response is complete.
6. When a role is also active (from `<slug>:role`), the role defines identity and the hat defines method. They compose: reason as the role would, using the hat's procedure.

### Step 3: activation - hat not found

If `found` is false:

1. Report to the operator:
   > "No hat definition found for `<slug>`. Available hats: [list from `available`, or 'none yet'].
   > Run `hat create <slug>` to define a new one, or continue without a hat."
2. Ask whether to proceed without a hat, use the closest available one, or create a new one.

### Step 4: creation flow

When the operator requests `hat create <slug>`:

1. Read `memory/operating/vault-conduct.md`.
2. Check whether `registry/hats/<slug>.md` already exists. If so, confirm before overwriting.
3. Interview the operator sequentially (wait for each answer):
   - `"Display name: full display name for this hat? (e.g. 'Critic', 'Refiner', 'Solver')"`
   - `"Description: one sentence on what this hat does."`
   - `"Cognitive posture: how does this hat approach a task? 2-3 sentences."`
   - `"Tools permitted: what may this hat use? Choose one: read-only (Read and non-destructive Bash) | read+write (add Write and Edit) | all | none."`
   - `"Method: numbered procedure this hat follows step by step."`
   - `"Output format: what sections must every response in this hat include?"`
   - `"Constraints: what must this hat never do? (e.g. 'Do not propose solutions.', 'Do not soften findings.')"`
4. Check whether `templates/registry-hat.md` exists in the vault. If it does, read it and use its content as the template, substituting the interview answers from Step 3 into its placeholders by matching section headings. If the custom template contains a section this skill has no interview answer for, leave its placeholder in place and flag it to the operator in the confirmation message (Step 7) rather than inventing content. If `templates/registry-hat.md` does not exist, use the fallback template below verbatim. Write `registry/hats/<slug>.md` with the resulting content. If MCP is available, prefer `mcp__contextos__note_create` with `frontmatter: {name: "<Display Name> Hat", description: "<one-line description>"}` and `content` set to everything from `# Hat: <Display Name>` onward; otherwise use the `Write` tool directly.
5. Add a row to `registry/hats/index.md`: `| [<Display Name>](<slug>.md) | <slug> | <one-line description> |` If MCP is available, prefer `mcp__contextos__fs_edit_file` anchored on the table's last existing row; otherwise use the `Edit` tool.
6. Append to the daily log. If MCP is available, call `mcp__contextos__vault_log_append` with `entry: "hat create | Created hat definition: <slug>"` and `files: ["registry/hats/<slug>.md"]`. Otherwise, append to `memory/log/YYYY/MM/YYYY-MM-DD.md`:
   ```
   HH:MM | agent | hat create | Created hat definition: <slug> | files: registry/hats/<slug>.md
   ```
7. Confirm to the operator:
   > "Hat `<slug>` created at `registry/hats/<slug>.md`. Use `<slug>:hat` in any future prompt to activate it."

---

## Hat file template (fallback)

Used only when `templates/registry-hat.md` is not present in the vault.

```markdown
---
name: <Display Name> Hat
description: <one-line description>
---

# Hat: <Display Name>

## Cognitive Posture

<How this hat approaches a task. 2-3 sentences.>

## Tools permitted

<read-only | read+write | all | none>

## Method

1. <step>
2. <step>
3. <step>

## Output format

- **<Section name>**: <what belongs here>
- **<Section name>**: <what belongs here>

## Constraints

- <hard constraint>
- <hard constraint>
```

---

## Tool scoping

Tool restrictions in a hat file are hard behavioural constraints. When a hat declares its permitted tools:

| Hat declares | Permitted in this task |
| --- | --- |
| `read-only` | `Read`, non-destructive `Bash` (ls, cat, grep, find). No `Write`, `Edit`, or state-modifying commands. |
| `read+write` | `Read`, `Write`, `Edit`, `Bash` (all). |
| `all` | All tools unrestricted. |
| `none` | Operate from current context only. No tool calls. |

If the operator's task requires a tool the active hat does not permit, surface the conflict:
> "The active hat (`<slug>`) restricts this to [read-only / read+write / none]. This task
> requires [the restricted tool]. Switch hat, or complete the observation phase first?"

Do not silently bypass the hat's tool restriction.

---

## Invariants

- Activate only on explicit `<slug>:hat` trigger. Never auto-activate from task keywords.
- Hat activation is task-scoped. Release after the task response is complete.
- Tool restrictions from the hat file are binding for the duration of that task.
- When role and hat are both active: role shapes identity, hat shapes method. They compose.
- Never invent hat content. If a slug is not found, report it and ask.
- Creation writes only `registry/hats/<slug>.md` and updates `registry/hats/index.md`. No other files.
