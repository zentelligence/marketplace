---
name: agent
description: "Loads an agent definition from `registry/agents/` and delegates a task to it as a validated sub-agent with contracted inputs and outputs, authors a new specialist or team member, or proposes a specialist for approval. Fires only on the explicit inline trigger `SLUG:agent` in a task field, used by the operator or a calling skill (e.g. 'Delegate the review of the draft article to demo-critic:agent.'), or the explicit commands `agent create SLUG` / `/agent create SLUG` and `agent propose SLUG` / `/agent propose SLUG`. Does not fire for `SLUG:role` or `SLUG:hat` (owned by the role and hat skills), for `prompt draft/create/list` (owned by the prompt skill), or for `/vault COMMAND` and vault-content requests (owned by the vault skill). Does not auto-delegate from task keywords or complexity alone without the literal `:agent` suffix naming a registry slug, and never spawns with an incomplete inputs contract."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "create <slug> | propose <slug>"
arguments: ["command"]
---

# Skill: agent

Loads an agent definition from `registry/agents/` and delegates a task to it as a sub-agent. Activated when the operator (or a calling skill) uses `<slug>:agent` in a task field. Also handles `/agent create <slug>` to author a specialist or a team member, and `/agent propose <slug>` for a member to propose a specialist.

The definition at `registry/agents/<slug>.md` is the single source of truth. This skill reads it through ContextOS MCP each time it delegates and starts a general-purpose sub-agent with it. Separately, the ContextOS server projects every agent definition into Claude Code's and Codex's own agent folders whenever it is written, so the hosts can delegate to it natively. That projection is derived data the server owns: never write, edit, or delete anything in a host's agent or skill folders, only the definition in the vault.

A definition projects only when `tier` is `fast`, `balanced`, or `deep`, the optional `access` is `all` (the default) or `read-only`, `description` is non-empty, and the body is non-empty. A definition with a `model` or `tools` field is refused: those are host field names, so use `tier` and `access`. The slug is the file name, in lowercase letters, digits, and single hyphens. Anything else is accepted by the vault but reported as a `projection/invalid-definition` warning naming the field and left unprojected.

`access: read-only` is a best-effort restriction, not a guarantee: MCP tools do not declare whether they change state, so the server classifies only ContextOS's own tools, a read-only Claude Code agent is given an allowlist of read and search tools plus ContextOS's non-mutating tools and no third-party MCP tools, and Codex can only switch off its shell, apps, and plugins, so MCP tools stay available to the agent there. `access` is interim and is expected to grow into a list of allowed tools with `*` wildcards.

---

## ContextOS MCP

This skill reads and writes the vault only through ContextOS MCP. Before the first lookup, follow steps 1 and 4 of the vault router's [Before any command](../vault/SKILL.md#before-any-command) section: confirm the server with `mcp__contextos__vault_info`, which also gives the vault order. A lookup searches every vault in that order and takes the first definition found, as [Resolving a registry slug](../vault/SKILL.md#resolving-a-registry-slug) sets out; only creation asks the operator to choose a vault (step 2). If the server is unavailable, report it and stop; never fall back to the host's own file tools. Paths below are addressed as `<vault>://...`.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| Agent slug | Inline `<slug>:agent` or `/agent create <slug>` | Yes |
| `registry/agents/<slug>.md` | Vault registry | For activation |
| `registry/agents/` | Vault registry | For available-agents listing: the `.md` files in the folder, never its server-managed `index.md` |
| Context, task, and inputs | Caller (operator or calling skill) | For activation |
| `memory/operating/vault-conduct.md` | Vault | For the creation flows only |
| `.contextos/team.toml` | Vault | For member creation and the proposal flow |

---

## Outputs

| Output | Notes |
| --- | --- |
| Sub-agent result in the definition's outputs contract | Returned to the caller verbatim |
| Agent-not-found report | Lists available agents and offers creation |
| Missing-inputs report | Lists inputs-contract items the delegation did not supply |
| New agent file | `registry/agents/<slug>.md` (creation flows only) |
| Team entry and workspace | `.contextos/team.toml` and `.contextos/workspaces/<slug>/` (member creation only) |
| Proposal task | An action task for the chief of staff, in `memory/tasks.base` (proposal flow only) |

---

## Flow

### Step 1: extract slug

Extract the agent slug from the trigger. Normalise to lowercase-hyphenated form.

Detect the trigger type:

- `<slug>:agent` in a task field → **activation flow** (Steps 2-4).
- `/agent create <slug>` as a standalone command → **creation flow** (Step 5), which sends a team member to **member creation** (Step 6).
- `/agent propose <slug>` as a standalone command → **proposal flow** (Step 7).

Resolve the slug through ContextOS MCP in configured vault order, as [Resolving a registry slug](../vault/SKILL.md#resolving-a-registry-slug) sets out: in each vault from `vault_info`, `<vault>://registry/agents/<slug>.md`, first found wins. An agent is always a single file; a folder of that name is not an agent, because the server would not project it. The full `<vault>://` path found is the definition's `file` (`found` is true). If no vault has it, `found` is false: `available` is the agent slugs across all vaults, each once, with the vault that would supply it. Never prefer the active vault over this order, and never use the host's own file tools.

### Step 2: activation - agent not found

If `found` is false:

1. Report to the caller:
   > "No agent definition found for `<slug>`. Available agents: [list from `available`, each slug once with the vault that supplies it, or 'none yet'].
   > Run `/agent create <slug>` to define a new one, or continue without delegating."
2. Ask whether to proceed without delegating, use the closest available agent, or create a new one. Do not spawn anything.

### Step 3: activation - validate the delegation

If `found` is true:

1. Read the agent definition at `file` with `mcp__contextos__fs_read_text_file`.
2. Collect from the caller: **context** (the situation), **task** (the delegated objective), and **inputs** (files, text, prior outputs).
3. Validate the delegation against the definition. Check the task is an assignment type its `## Inputs contract` accepts and within `## Activation and resource limits`, and the supplied inputs against the items `## Inputs contract` requires. If the task is out of scope, report that and do not spawn. If any required item is missing, **fail fast** before spawning:
   > "Delegation to `<slug>:agent` is missing required inputs: [each missing item, named
   > as the contract names it]. Supply them and re-delegate."
4. Do not substitute guesses for missing inputs. Do not spawn with a partial contract.

### Step 4: activation - compose and spawn

Compose a KERNEL+V prompt for the sub-agent:

| Section | Source |
| --- | --- |
| `<context>` | From the caller: the situation the delegation sits in |
| `<tasks>` | The delegated task, framed by the definition's `## Identity`, `## Purpose and success`, and `## Method or process` |
| `<inputs>` | From the caller, validated against `## Inputs contract` in Step 3 |
| `<constraints>` | The definition's `## Constraints`, `## Delegation rules`, and `## Activation and resource limits`, verbatim |
| `<outputs>` | The definition's `## Outputs contract`, verbatim |
| `<verify>` | The definition's `## Verification`, verbatim, plus every contracted section present and every constraint respected |

Spawn the sub-agent:

1. Spawn a general-purpose sub-agent with the definition body prepended as its framing.
2. Map the definition's `tier` to the host's own model where the host lets you choose one (`fast` is the host's smallest and quickest, `balanced` its general-purpose model, `deep` its most capable), and treat `access: read-only` as a constraint to honour yourself when you spawn: instruct the sub-agent to read and search only and never to change a vault or file. If the host cannot honour the tier, use its default and say so in the result.
3. Pass the composed KERNEL+V prompt as the sub-agent's task. Refer to vault files in it as `<vault>://<path>` so the sub-agent reads them through ContextOS MCP.
4. Tell the sub-agent that it claims no task and changes no task's state: the caller keeps the task, and the sub-agent returns its work to the caller.
5. If the host cannot start a sub-agent from this session, report that to the caller and stop. Never do the specialist's work in its name; the caller decides what happens next.
6. Record the delegation with `mcp__contextos__base_record_create` on `<vault>://memory/events.base`, in the vault that holds the definition: `kind: agent.delegated`, `agent` set to the slug, `caller` set to the slug of the member who delegated, the name of the skill that did, or `operator`, and `subject` linking the task by its key when there is one (`[[a-071|A-071]]`). These events are the usage record the periodic review of specialists reads. If the call fails, say so in the result; the delegation stands.

Return the sub-agent's output to the caller **in the definition's outputs contract**, with the evidence `## Verification` calls for. If the sub-agent returns output that violates the contract, reshape it into the contracted sections; never silently pass through a malformed result. If it stopped early, or returned a question under `## Judgement and escalation`, say so at the top of the result: never reshape partial work to look finished. The caller accepts or returns the result and answers for it.

### Step 5: creation flow

When the operator requests `/agent create <slug>`:

1. Choose the vault to write to (step 2 of the vault router's Before any command; the operator's choice, never assumed), then read that vault's `memory/operating/vault-conduct.md`.
2. Resolve `<slug>` across all vaults in `vault_info` order as in Step 1. If it exists in the chosen vault, confirm before overwriting. If an earlier vault than the chosen one already defines it, warn the operator that the earlier vault's definition wins every lookup and every host projection, so the new one would be shadowed, and ask whether to continue, choose another slug, or choose another vault.
3. Establish the kind.
   - If the command names an approved proposal (`/agent create <slug> from <task id>`), read that task. Continue only if the operator's approval is recorded on it; otherwise report that and stop. Write the definition its body holds with item 7, without interviewing or changing it, and continue from item 8.
   - Otherwise ask: `"Kind: is this a team member, who holds a function and works from the task list, or a specialist, who does one narrow job when delegated to? Choose one: member | specialist."` For a member, go to Step 6.
   - Only the operator creates without a proposal. If a member reached this flow, send it to Step 7 instead.
4. Check the specialist is needed, using the [simpler-first and overlap checks](#simpler-first-and-overlap-checks). Tell the operator what they show, and let them decide whether to continue.
5. Interview the operator sequentially (wait for each answer). These sections define the job, so each needs the operator's own answer:
   - `"Display name: full display name for this agent? (e.g. 'Demo Critic', 'Summariser')"`
   - `"Description: one line: what this agent does and when to delegate to it."`
   - `"Tier: how capable a model does this agent need? Choose one: fast | balanced | deep. (The server maps it to each host's model.)"`
   - `"Access: what may this agent do? Choose one: all | read-only. (Default all. Read-only is best effort, not a guarantee.)"`
   - `"Identity: which role does this agent reason as, and what narrow craft does it bring? (e.g. 'as the engineer:role, a reviewer of data migrations')"`
   - `"Purpose and success: what outcome does it serve, how will you recognise success, and what would look like success but not be?"`
   - `"Inputs contract: what kinds of assignment does it accept, and what must the caller supply for it to run? Name each item."`
   - `"Method or process: which roles, hats, prompts, or skills does it use, and in what order?"`
   - `"Outputs contract: the exact shape the agent returns, and the evidence behind it. Name each required section."`
   - `"Verification: how does it check its own output, when does its work need separate review, and what evidence lets the caller accept it?"`
   - `"Constraints: hard stops and boundaries. What must this agent never do?"`
   - `"Steward: which member looks after this definition? Any member may delegate to it."`
6. Draft the operating sections from the answers, starting from the defaults below and adjusting each to the agent's job. Add the steward to `## Relationships and handovers` as a `Steward: <member slug>` line. Show the operator all seven together, say that these are proposed defaults, and ask what to change. Write nothing until they confirm.

   | Section | Default |
   | --- | --- |
   | `## Relationships and handovers` | Takes assignments through `<slug>:agent` from the operator, a member, or a skill. Returns its work to the agent that delegated it, which keeps the task, accepts the result, and answers for it. |
   | `## Context and memory` | Knows only this definition and its brief. Treats the sources the brief names as authoritative, keeps nothing between runs, and writes to shared memory only what its outputs contract names. |
   | `## Judgement and escalation` | Faced with ambiguity, conflicting instructions, or insufficient evidence, it states the question in its output and stops rather than deciding. Anything beyond its brief stays with the caller or the operator. |
   | `## Failure and recovery` | If a tool is unavailable, an edit conflicts, or it is interrupted, it stops, reports what was finished, what was not, and what was left in place, and never presents partial work as finished. |
   | `## Learning and change control` | Feedback goes to the steward, who proposes any change. The operator approves changes to this definition, and the agent never edits it. |
   | `## Activation and resource limits` | Runs only when delegated to with `<slug>:agent`, never on its own initiative. Stops and returns for direction when a job needs more than its brief allows. |
   | `## Delegation rules` | Does not delegate. It does the work itself and returns anything beyond its contract to the caller. |

7. Read `templates/registry-agent-specialist.md`. If it does not exist, tell the operator to run `/vault update` and stop. Replace each section's placeholder text with its answer or confirmed draft, matching by section heading, and replace `{{name}}` with the display name. Leave out the closing `<!-- -->` note. If the operator's template has a section with neither an answer nor a draft here, leave its placeholder in place and flag it in the confirmation (item 11) rather than inventing content. Write `registry/agents/<slug>.md` with `mcp__contextos__note_create`, passing `frontmatter: {kind: "specialist", name: "<Display Name>", description: "<one line>", tier: "<tier>", access: "<access>"}` and `content` set to everything from the template's first heading onward.
8. Leave `registry/agents/index.md` alone: the ContextOS MCP server lists the new file in it, with its frontmatter `description` as the summary.
9. Add a log summary: call `mcp__contextos__vault_log_append` with `entry: "agent create | Created agent definition: <slug>"` and `files: ["registry/agents/<slug>.md"]`.
10. Check the write result. A `projection/` warning means the write succeeded but the agent could not be projected into Claude Code or Codex; tell the operator what it says and point them at `doctor` (see the mcp-tools skill's maintenance topic). A `projection/invalid-definition` warning naming `model` or `tools` means the definition used a host field name: fix it to `tier` and `access` with `fs_edit_file` or `frontmatter_update`. Never retry the write or write a host folder yourself.
11. Confirm to the operator:
   > "Agent `<slug>` created at `registry/agents/<slug>.md`. Use `<slug>:agent` in any future task to delegate to it. The ContextOS server also projects it into Claude Code and Codex automatically, so both hosts can delegate to it by name. `access: read-only` is best effort, not a guarantee: a read-only Claude Code agent gets no third-party MCP tools, but Codex can only switch off its shell, apps, and plugins, so there MCP tools stay available and the agent is instructed to stay read-only."

### Step 6: member creation

A new member is the operator's decision, so this step runs only for the operator, in a session they are present in.

1. Read `<vault>://.contextos/team.toml` and keep its hash. The operator is the member with `type = "human"`, and the team is the chief of staff's `team`. `<slug>` must be the member's name in lowercase-hyphenated form, must not be the operator's, and must not already be in `team.toml`. If any of these fails, say which and ask again.
2. Read the `## Remit` of every existing member. If the proposed work belongs to a function that already exists, say so and ask whether to widen that member instead.
3. Interview the operator sequentially (wait for each answer):
   - `"Name: what is this member called?"`
   - `"Function: the position they hold, in lowercase-hyphenated form. (e.g. 'finance')"`
   - `"Domain: their area of speciality, in one or two words."`
   - `"Description: one line: what can you entrust to this member, as outcomes rather than tools?"`
   - `"Tier: how capable a model does this member need? Choose one: fast | balanced | deep."`
   - `"Review authority: may this member accept work into done? Choose one: none | function | team. (Default none, so a person accepts it.)"`
   - `"Identity: what function do they hold, and what can you rely on them for?"`
   - `"Soul: what do they care about, and what will they not compromise?"`
   - `"Persona: how do they come across, and how do they push back?"`
   - `"Stewardship scope: what should they keep watch over without being asked?"`
   - `"Assigned task scope: what kinds of work can they be given, and what result should you expect?"`
   - `"Hands off: what do they not own, and who does?"`
   - `"Authority: what may they do unprompted, what may they delegate, and what needs your approval?"`
   - `"Boundaries: what must they never do, whatever a task says?"`
4. Draft the remaining sections from the answers, taking structure and each section's purpose from `templates/registry-agent-member.md`, and using the `kind: member` definitions in `registry/agents/` as examples of content only, since one may predate the current template: `## Intake and context formation`, `## Judgement and approach selection`, `## Outcomes, deliverables, and accountability`, `## Standards of care and acceptance`, and `## Collaboration, delegation, and retained responsibility`. Show the operator all five, say that they are proposed, and ask what to change. Write nothing until they confirm.
5. Read `templates/registry-agent-member.md`. If it does not exist, tell the operator to run `/vault update` and stop. Replace each section's placeholder text with its answer or confirmed draft, matching by section heading, and keep the fixed bullets under `## Ways of working`. Replace `{{name}}` with the name and `{{OperatorName}}` with the operator's name, and leave out the closing `<!-- -->` note. Write `registry/agents/<slug>.md` with `mcp__contextos__note_create`, passing `frontmatter: {kind: "member", name: "<name>", function: "<function>", description: "<one line>", tier: "<tier>", review_authority: "<authority>", effects: []}` and `content` set to everything from the first heading onward.
6. Create the member's workspace with `mcp__contextos__fs_create_directory` at `<vault>://.contextos/workspaces/<slug>`.
7. Append this entry to `.contextos/team.toml` with `mcp__contextos__fs_write_file` and the hash from item 1, never setting `chief_of_staff`:
   ```toml
   [[member]]
   slug = "<slug>"
   name = "<name>"
   type = "agent"
   team = "<team>"
   domain = "<domain>"
   ```
8. Add a log summary with `mcp__contextos__vault_log_append`: `entry: "agent create | Created team member: <slug>"` and `files: ["registry/agents/<slug>.md", ".contextos/team.toml"]`. Check the write result as Step 5's item 10 says.
9. Tell the operator the member exists, and that work reaches them only once the chief of staff knows to route it. Offer to add the function to the chief of staff's `Hands off` list, and change that definition only if they agree.

### Step 7: proposal flow

A member proposes a specialist here; it never writes one. Work from what the member already knows, and never ask the operator: this flow may run with nobody present.

1. Confirm the need has earned a specialist: at least two earlier instances of the same narrow job, each citable as a task or note, with stable inputs and outputs. If not, report that a brief given inline suits it for now, and stop.
2. Run the [simpler-first and overlap checks](#simpler-first-and-overlap-checks). If something simpler fits, report which and stop. If an existing specialist overlaps, propose a change to it instead: name it and the change, and go to item 4 with that as the draft.
3. Draft the whole definition, following `templates/registry-agent-specialist.md`, with frontmatter and every section filled. The Step 5 defaults are the starting point for the operating sections. The proposing member is the steward unless another member fits better.
4. Find the chief of staff, the member of `.contextos/team.toml` with `chief_of_staff = true`, and raise an action task for them with `mcp__contextos__base_record_create` against `<vault>://memory/tasks.base`, `prefix: A`, following `templates/task.md`, titled `Specialist proposal: <slug>`. Its body holds the evidence from item 1, why nothing simpler or existing serves, and the draft.

The chief of staff weighs the proposal and leaves the task `waiting` on the operator with a recommendation. Once the operator's approval is recorded on it, the chief of staff raises a task for the librarian to run `/agent create <slug> from <task id>`.

### Simpler-first and overlap checks

Check in this order, and stop at the first match:

| If the need is | Use instead |
| --- | --- |
| A job done once, or rarely | A brief given inline |
| Deterministic, repeatable work | A workflow (`workflow` skill) |
| A way of thinking or working | A role or hat |
| Reusable wording | A prompt |

Only a need for isolated context and a checkable contract calls for a specialist. Then read the `description` of every `kind: specialist` definition in `registry/agents/`. If one covers the job or most of it, extending it is the default. If the vault holds more than twelve specialists, say so: that is a prompt to review the pool, not a limit.

## Invariants

- Activate only on explicit `<slug>:agent` trigger. Never auto-delegate from task keywords.
- The registry definition is the single source of truth, read fresh on every activation.
- Never spawn with an incomplete inputs contract. Fail fast and name what is missing.
- Return output only in the definition's outputs contract, and never present partial work as finished.
- A specialist claims no task and changes no task's state. The caller keeps the task and answers for the result.
- Never invent agent content. If a slug is not found, report it and ask. A drafted section reaches a definition only after the operator has seen and confirmed it.
- Creating a specialist writes only `registry/agents/<slug>.md`, and creating a member also writes only its `.contextos/team.toml` entry and workspace. Never an `index.md`, and never a host's agent or skill folder.
- Only the operator creates a member. A member proposes a specialist and never writes one; the librarian writes it only from a proposal the operator has approved.
- Specialists are one shared pool. A steward looks after a definition; it does not own who may use it.
