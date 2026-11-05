---
name: dispatch
description: "Works the vault's task list: finds actionable action tasks assigned to agent team members in `memory/tasks.base`, claims each through ContextOS MCP, and starts the host sub-agent named by the task's assignee to work it, at most three at a time, repeating until nothing actionable remains. Fires on `/dispatch`, `/dispatch SLUG` to work only one member's tasks, and requests to process, work through, or dispatch the task list or a member's assigned tasks, including the prompt of a scheduled task such as 'dispatch ellis' tasks'. Does not fire for creating, editing, or reporting on tasks without working them (owned by the vault skill), for `SLUG:agent` delegation of a task given inline (owned by the agent skill), or for ContextOS Web jobs and workflows, which run with no agent session."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "[member-slug] [limit N]"
arguments: ["member"]
---

# Skill: dispatch

Works the vault's task list on behalf of its agent team members. This session is the dispatcher only: it chooses, claims, and hands out tasks, and each task is worked by a sub-agent that is the member the task is assigned to. The dispatcher never works a task itself.

It is built to run unattended as a scheduled task (see [Running on a schedule](#running-on-a-schedule)), so it never waits on the operator mid-run: anything that needs a person is reported at the end.

---

## ContextOS MCP

Follow steps 1, 2, and 4 of the vault router's [Before any command](../vault/SKILL.md#before-any-command) section, and step 3 for `AGENTS.md` and `vault-conduct.md`. When several vaults are configured, none was named, and no one is present to answer, report that and stop rather than choosing one. If the server is unavailable, report it and stop; never fall back to the host's own file tools. The [mcp-tools](../mcp-tools/SKILL.md) skill's notes guide covers `base_query`, claiming a record, and recording an event.

The session's working folder may be a member's workspace, `.contextos/workspaces/<slug>/` (see below). It is not vault content and changes nothing here: read and write the vault only through ContextOS MCP.

---

## Inputs

| Input | Source | Default |
| --- | --- | --- |
| Member slug | `/dispatch <slug>` | Every agent member |
| Concurrency limit | `limit <n>` in the invocation | 3 |
| `.contextos/team.toml` | Vault | Required |
| `memory/tasks.base` and `memory/tasks/` | Vault | Required |
| `memory/events.base` and `registry/events/session.run-*.md` | Vault, shipped by the scaffold | Required: the run id comes from them |

---

## Flow

### Step 1: the team

1. Read `<vault>://.contextos/team.toml`. Each `[[member]]` has a `slug`, a `name`, and a `type`. The agent members are those with `type = "agent"`, the chief of staff is the agent member with `chief_of_staff = true`, and the operator is the member with `type = "human"`. Note all three slugs.
2. If a member slug was given and it is not an agent member, say so, list the agent members, and stop.
3. Read `<vault>://.contextos/tasks.toml` if it exists: it holds this vault's own task states and priorities, which the operator may have customised. This skill needs the action states `next`, `doing`, `waiting`, and `review`; if the action type lacks any of them, report which and stop.
4. Record the start of the run and take its id from the server. Call `base_record_create` on `<vault>://memory/events.base` with `prefix: S`, `kind: session.run-started`, `members` (the slugs of the agent members this run will work for), and `scope` (the member slug given, or `team`). Supply no `severity`, `at`, `run_id`, `filename`, or any other field. The call returns a `key` such as `S-001`: that key is the run id, and a claim this run makes is `claimed_by: <worker>/<run id>`. Never make a run id from the clock or any other source, because two runs started in the same second would share it.
5. If the call fails for any reason, stop. Claim nothing, work nothing, and report the error code and remediation; with no run id there is no record of the run to tie a claim to. If it fails because the vault has no `memory/events.base` or no `session.run-started` definition (`events/unknown-kind`), tell the operator to run `/vault update`.
6. Start an empty list of tasks handled in this run. A task in it is never dispatched again in this run, whatever its state.

### Step 2: find actionable tasks

1. Query `<vault>://memory/tasks.base` with `base_query` for records with `task_type` `action`, assigned to the member slug (or to any agent member), whose `state` is either:
   - `next`; or
   - `doing` with a `claimed_until` that has passed, which is a run that ended without finishing.
2. Drop any task that:
   - is in this run's handled list;
   - has a `start_after` later than today;
   - holds a `claimed_until` still in the future;
   - is blocked: a task in its `depends_on` is still open. Look the dependencies up with `base_query` `ids`. A state is closed when its stage in `.contextos/tasks.toml`, under the dependency's own `task_type` or else the shared `[[stage]]` list, sets `closes` to `completed` or `cancelled`; every other state is open. Without that file, `done`, `adopted`, `answered`, and `dropped` are closed.
3. Order what remains by `priority`, most urgent first in the order of `.contextos/tasks.toml`'s `[[priority]]` list (without it, `high`, then `normal`, then `low`), then by the earliest of `finish_by` and `due` (none last), then by id.
4. If nothing remains, go to Step 5.

Decisions and questions are not dispatched: an agent records its recommendation or answer and leaves them open for a person, so they would be dispatched again on every run.

### Step 3: claim

Take tasks from the top of the order until this round holds the concurrency limit, with at most one task per worker: a member works its tasks one after another, never two at once, so a task whose worker already has one this round waits for a later round. For each:

1. Fetch it with `base_query` `ids` and confirm it is still actionable as in Step 2.
2. Choose its worker from `attempts` (empty counts as 0), counting this claim as one more:
   - the first or second attempt: the assignee;
   - the third attempt: the chief of staff, as an escalation. If the assignee is the chief of staff, or the team has none, treat it as a fourth attempt;
   - a fourth or later attempt: nobody. Do not claim it. Add a dated note under `## Outcome` saying it was attempted three times without finishing, set `state: waiting`, `waiting_on` to the operator's slug, and `updated` to today with `frontmatter_update` and the fetched `content_hash`, add it to the handled list, and take the next task.
3. Claim it with `frontmatter_update`, passing the fetched `content_hash` as `expected_hash`, setting `state: doing`, `claimed_by: <worker>/<run id>`, `claimed_until` to two hours from now in ISO 8601 UTC, `attempts` to its new count, and `updated` to today.
4. On `io/conflict`, another session claimed it first: leave it, add it to the handled list, and take the next task.
5. Add each claimed task to the handled list.

`attempts` is what stops a task circling: a task that keeps returning to `next`, whose claims keep lapsing, or that agents keep passing between them reaches the chief of staff on its third claim and the operator on its fourth. Never reset it; only the operator clears it.

### Step 4: hand out

1. Start one sub-agent per claimed task, all in the same turn so they run together, using the host's own agent named by the worker's slug: the assignee, or the chief of staff for an escalation. ContextOS projects every valid definition in `registry/agents/` into the host under its slug.
2. If the host has no agent by the worker's slug, its definition did not project. Do not substitute a general-purpose agent. Release the claim with `frontmatter_update` (`state: next`, `claimed_by` and `claimed_until` empty, `attempts` back to its count before this claim) and report the member under Step 5 as needing `doctor` to explain why it is not projected.
3. Give each sub-agent this brief, filled in:

   > You are working task `<id>` in the `<vault>` vault, `<vault>://<task path>`, which this run has claimed for you as `<claimed_by>` until `<claimed_until>`. Load the `mcp-tools` skill if it is not already loaded. Before anything else, call `agent_state_change` with your slug, `state: working`, and the task id as `reason`. Read the task, the vault's `AGENTS.md`, and `memory/operating/vault-conduct.md` through ContextOS MCP, and do the work its Context, Tasks, and Verify sections describe, within your definition's Remit, Authority, and Boundaries. Read and write the vault only through ContextOS MCP. Your working folder is not the vault: never cite or link anything in it, and if a file you need to keep ends up there, file it into the vault with `note_create` and `content_from` rather than retyping it. Finish in exactly one of these ways, each time setting `updated` to today and clearing `claimed_by` and `claimed_until`:
   > - **Finished:** record what was done, links to every note written, and what was and was not verified under `## Outcome`, then set `state: review`. Never set `done` yourself.
   > - **Need an answer:** add your dated question under `## Questions`, then set `state: waiting` and `waiting_on` to the slug of who must answer.
   > - **Cannot proceed:** explain why under `## Outcome`, then set `state: waiting` and `waiting_on` to the operator's slug.
   >
   > Once the task is left, call `agent_state_change` again: `idle` if you left it in `review`, or `awaiting-input` if you left it `waiting`. If the claim would lapse before you finish, extend `claimed_until` with `frontmatter_update` and the task's current `content_hash`. Reply with one line: the task id, the state you left it in, and the notes you wrote.

   For an escalation, add to the brief:

   > This task has had two attempts by `<assignee>` without finishing; its `## Outcome` and `## Questions` say what happened. As chief of staff, do not hand it back to `<assignee>` or pass it to another member. Either finish it yourself into `review`; or split it into smaller tasks with `base_record_create`, each with `parent` set to this task, record the split under `## Outcome`, and set this task to `review`; or, if only the operator can unblock it, leave it `waiting` on the operator.

4. When the sub-agents return, fetch each task with `base_query` `ids`. If one is still `doing` under this run's claim, the sub-agent stopped without finishing: add a dated note under `## Outcome` saying the run ended without a result, set `state: waiting` with `waiting_on` set to the operator's slug, and clear the claim. Never mark a task finished on the sub-agent's word alone. Then read `.contextos/team.toml` again: a worker from this round still in state `working` stopped without updating it, so call `agent_state_change` for it with `idle` and the reason `run <run id> ended its task`.
5. Return to Step 2. Stop after ten rounds even if tasks remain, and say so in the report; the next scheduled run carries on.

### Step 5: report and record the finish

1. Report, grouped by member: each task dispatched and the state it was left in, each task skipped and why (claimed elsewhere, blocked, not yet due), each member that could not be started, each task escalated to the chief of staff or handed to the operator after three attempts, and anything waiting on the operator.
2. Record the end of the run with `base_record_create` on `<vault>://memory/events.base`: `kind: session.run-finished`, `run_id` set to the key from Step 1, `members` as in Step 1, and the counts `dispatched` (tasks handed out), `review` (left in `review`), and `waiting` (left in `waiting`). Set `severity` to:
   - `info` when nothing is left waiting on a person;
   - `warning` when a task is left waiting on a person, a member could not be started, or the ten-round limit stopped the run with work remaining;
   - `error` when the run aborted before it could finish its rounds.

   Add a short `content` summarising the run if it helps a reader. Where the host reported a sub-agent's usage when it returned, such as tokens, tool uses, and duration, list it there per task; record nothing the host did not report. If this call fails, say so in the report; the work already done stands.

   `session.run-started` and `session.run-finished` are the run's record. Do not also append a summary line with `vault_log_append`: the server already logs each mutation, and the finish event carries the same facts.
3. A run that aborts records `session.run-finished` with `severity: error` if it still can. A run that crashes records nothing, and a reader sees its start with no finish.

What this run did to each task, such as a claim, a move into `review`, or a member's state change, fires server events by itself, tied to this run by the run id in `claimed_by`. Never record those yourself, and never decide what to work from events: Step 2 reads the task records only.

---

## Running on a schedule

Each agent member has a workspace, `.contextos/workspaces/<slug>/`, which the scaffold creates with the member. It exists to be a scheduled session's working folder: Git ignores `.contextos/`, and search and `index.md` maintenance skip it, so anything a host writes there by default stays out of the vault. If a member's workspace is missing, create it with `fs_create_directory`.

When the operator asks to schedule dispatching, tell them to set it up in their agent app; never write a host's scheduled-task files. In Claude Code Desktop:

1. Open **Scheduled**, then **New task**, and turn on **Only on this computer**.
2. Set the instructions to `/dispatch <slug>` for one member, or `/dispatch` for the whole team.
3. Set the local folder to `<vault folder>/.contextos/workspaces/<slug>/`, using the chief of staff's workspace for the whole team. On macOS, press Cmd+Shift+. in the folder picker to show the `.contextos` folder.
4. Choose a schedule, and click **Run now** once. Answer each permission prompt with "always allow", including the `mcp__contextos__*` tools, so later runs do not stall waiting for approval.

A run catches up once after the computer sleeps through a scheduled time, so it may start hours late. That is safe: what is actionable comes from the tasks' own state, never the clock time of the run.

---

## Invariants

- The dispatcher never works a task; only the worker's own agent does: the assignee, or the chief of staff on an escalation.
- A member works one task at a time, and every agent records its own working state with `agent_state_change`.
- Every claim adds one to `attempts`; the third goes to the chief of staff and a fourth to the operator.
- The run id is the `key` the server returned for `session.run-started`, never the clock. Nothing is claimed or worked without one.
- Every task is claimed with a conflict-checked write before its sub-agent starts, and a refused claim is never retried by another route.
- What to work is read from the task records. Events record what happened and never decide what to do.
- An agent finishes into `review` or `waiting`, never `done`.
- Never write a host's agent, skill, or scheduled-task files.
