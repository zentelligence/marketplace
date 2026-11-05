# Skill: vault health

---

## Purpose

Check the vault's health and the quality of its knowledge, and put the fixes in hand. Two sources, one report:

- **Vault health**, from the ContextOS MCP server's `doctor`: configuration, managed indexes, Git, the search stores, frontmatter that does not parse, duplicate ids, records that do not match their base, link integrity, the team, event kinds, and projection into the agent hosts.
- **Knowledge quality**, from the vault package's `health` workflow, run as a saved shared job: what `memory/operating/vault-conduct.md` asks of wiki articles and insight notes (lowercase-hyphenated names, frontmatter, sources in the frontmatter, allowed `status` and `confidence` values, no unfilled placeholders or empty headings, open questions held as links to tasks or vault decisions, and staleness), plus every link that does not resolve and every note with no links in or out, from the server's link graph.

It runs unattended, usually on a schedule, so it never stops to ask the operator. The checks write nothing. What can be fixed is fixed in the same run: `doctor_resolve` repairs what the server can, and the vault's librarian, the member whose domain is knowledge, started as a sub-agent, resolves the knowledge findings and the knowledge-related `doctor` findings, confirming each against `doctor` and the `health` job. Whatever needs a decision goes up the team, never straight to the operator: the librarian escalates to the chief of staff, who settles it or takes it to the operator.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| `doctor` report | ContextOS MCP | Yes |
| The `health` job's report | The vault package, through ContextOS Web ([package.md](package.md)) | Yes |
| `memory/operating/vault-conduct.md` | Vault | Yes |
| `.contextos/team.toml` and `registry/agents/` | Vault | To find the librarian and the chief of staff, for Steps 5 and 6 |

---

## Outputs

| Output | Notes |
| --- | --- |
| Health report | Returned at the end of the run, in the session or to the scheduler. |
| Repairs | Only through `doctor_resolve`, and never a standing change such as initialising Git. |
| Knowledge fixes | Made by the librarian sub-agent, within the bounds in Step 5. |
| Escalations | Action tasks for the chief of staff in `memory/tasks.base`, one per finding, never raised twice. |
| Log entry | One line through `vault_log_append`. |

---

## Flow

### Step 1: vault health

Call `mcp__contextos__doctor` for the vault. Keep each check's `kind`, `status`, `message`, `remediation`, and whether it is auto-fixable. See the mcp-tools skill's maintenance topic for what each check means and which ones `doctor_resolve` leaves alone (`frontmatter`, `duplicate_ids`, `record_conformance`, `link_integrity`, and `team_config` are reported, never repaired).

### Step 2: knowledge quality

Run the vault package's `health` job as [package.md](package.md) describes (Steps 1 to 4), with `<today>` the current local date as `YYYY-MM-DD`:

```bash
contextos-web jobs run --shared contextos-vault health health --format json --input vault=<vault> --input 'today="<today>"'
```

It reads `memory/wiki/` and, if it exists, `memory/insights/`, and writes nothing. Read `outputs.report`: `findings` (each a `check`, the note's `path`, and a `detail`), `counts` per check, `total_findings`, and `truncated`. When `truncated` is true the list stops short of `total_findings`, to keep the report within ContextOS Web's output limit; the rest are found again on the next run, once these are fixed. A `failed` or `refused` run is a finding in itself: report its `code` and `message`, and escalate it in Step 6.

### Step 3: assemble the report

Assemble two sections, each grouped and counted.

**Vault health** (from `doctor`): every check that did not pass, with its message and remediation, and which are auto-fixable. Say plainly when every check passed.

**Knowledge quality** (from the `health` job), by `check`:

1. **Structure:** `file-name`, `frontmatter-missing`, `frontmatter-unreadable`, `empty-heading`, and `orphan` (no links in or out).
2. **Sources:** `sources-missing`, `source-unresolved`, and `source-in-body` (a `**Source:**` line to move into the frontmatter's `sources`).
3. **Quality:** `status-invalid`, `confidence-invalid`, `date-invalid`, and `placeholder`.
4. **Links:** `link-unresolved` and `links-unreadable`.
5. **Open questions:** `open-question-unlinked`, an item under `## Open Questions` that is not a link to a question or decision task, or to a vault decision or question.
6. **Staleness:** `stale` (a wiki article not updated in 90 or more days) and `proposed-stale` (an insight proposed 30 or more days ago).
7. **Summary:** wiki articles and insight notes checked, and the findings in total.

### Step 4: vault repairs

1. If any `doctor` finding is auto-fixable, call `mcp__contextos__doctor_resolve` with `path` set to the vault and `dry_run: true`.
2. If the dry run would initialise Git, call nothing more and escalate every auto-fixable finding: initialising Git is a standing change, because it starts automatic commits on every future mutation, so it waits for the operator, and the call cannot leave it out. Otherwise call `doctor_resolve` again without `dry_run`.
3. Call `doctor` again and keep what is left.
4. The knowledge-related findings still failing (`frontmatter`, `duplicate_ids`, `record_conformance`, and `link_integrity`) go to the librarian in Step 5 with the knowledge findings. Escalate, as in Step 6, every other finding still failing: one whose remediation is the operator's (configuration, the stores, the team, event kinds, projection), the Git initialisation, and any repair that did not take.

Never repair a `doctor` finding by hand outside the librarian's bounds, and never create or edit an `index.md`: a missing or stale one is the server's to repair.

### Step 5: knowledge fixes, delegated to the librarian

Find the librarian: the agent member of `.contextos/team.toml` whose `registry/agents/<slug>.md` has `function: librarian`. If the vault has none, or the host has no agent by that slug (its definition did not project; `doctor` says why), make no knowledge fixes: escalate one finding saying the librarian could not be started and why, with the knowledge findings listed in it, and go to Step 6.

1. Group the findings into pieces of work: for example, one note needing its frontmatter and sources, a batch of broken links, a batch of open questions to raise as tasks, a batch of stale articles to review, or one stale proposed insight.
2. Start the librarian as a sub-agent now, using the host's own agent named by the librarian's slug; one sub-agent for the batch, or one per independent piece of work, started in the same turn so they run together. Never substitute a general-purpose agent. Brief it with:

   > You are resolving findings from an unattended `/vault health` run in the `<vault>` vault; nobody is waiting to answer questions. Load the `mcp-tools` skill if it is not already loaded, then call `agent_state_change` with your slug, `state: working`, and `reason: vault health`. Read the vault's `AGENTS.md` and `memory/operating/vault-conduct.md` through ContextOS MCP, and work through exactly these findings, within your definition's Remit, Authority, and Boundaries: `<findings, each with its check, note path, and detail, and each doctor finding with its kind and message>`.
   >
   > Fix a finding only when the fix does not change what the vault claims or decide anything for someone else: add frontmatter a note lacks, move a `**Source:**` line into the frontmatter's `sources`, repoint a broken link or source whose intended target is clear, correct a `status` or `confidence` value the note plainly implies, fill a placeholder from the note's own content, correct frontmatter that does not parse or a record that does not match its base, rename a file to lowercase-hyphenated form with `fs_move_file`, or confirm a stale article against its sources and update its date. For an open question held as text, raise it as a question task with `base_record_create` against `memory/tasks.base` (`prefix: Q`, following `templates/task-question.md`, assigned to the chief of staff, with `origin: vault-health:open-question:<note path>` and `unique_fields: ["origin"]`), or, when it is about the vault itself, as a vault question against `memory/decisions.base` (`prefix: VQ`); then replace the text with a link to it. Anything else you escalate instead of fixing: a source you cannot identify, a claim that needs changing, adopting or dismissing an insight, deleting a note, or anything outside your remit. Never invent a source or a claim.
   >
   > Read and write the vault only through ContextOS MCP, with `expected_hash` on every edit; never create or edit an `index.md`, and never write to `memory/raw/` or `memory/research/`. Raise no task other than an open question's. After fixing a `doctor` finding, call `doctor` and confirm it now passes. When finished, call `agent_state_change` with `state: idle`, and return, for each finding, one of: `fixed`, with what you changed and the note's path; or `escalate`, with the question or decision the chief of staff needs to settle, what you found, and what you recommend.

3. When the sub-agents return, run the `health` job and `doctor` again. A finding reported `fixed` that still appears is escalated, with the librarian's account and what still fails. Never count a finding as fixed on the sub-agent's word alone.
4. Then read `.contextos/team.toml` again: if the librarian is still `working`, it stopped without updating its state, so call `agent_state_change` for it with `idle` and the reason `vault health run ended`.

### Step 6: escalate to the chief of staff

Find the chief of staff: the member of `.contextos/team.toml` with `chief_of_staff = true`. For each finding to escalate, from Steps 2, 4, and 5, raise an action task with `mcp__contextos__base_record_create` against `<vault>://memory/tasks.base`, `prefix: A`, following `templates/task.md`, with:

- `title` naming the finding and its note, verb first, for example "Settle the source for `memory/wiki/<slug>.md`";
- `assignee` the chief of staff's slug, `state: next`, `priority: normal`;
- `origin: vault-health:<check>:<note path>`, using the `doctor` check `kind` or the `health` job's `check`, and the vault for a vault-wide finding, with `unique_fields: ["origin"]`;
- `## Context` holding what is wrong, what the librarian found and recommends, or the finding's remediation, and `## Tasks` and `## Verify` saying what settles it and how the next health run will confirm it.

The chief of staff picks these up in the next `/dispatch` run, and settles each, routes it, or leaves it waiting on the operator if only the operator can decide. A refusal with `io/duplicate-record` means an earlier run already escalated this finding: leave that task as it is and count it as already escalated. If the vault has no chief of staff (`doctor`'s `team_config` check fails), raise nothing, and put each escalation in the report instead.

### Step 7: report and log

1. Return one report: the vault health and knowledge quality findings as in Step 3; then what was repaired, what the librarian fixed (with the notes changed and the question tasks raised), what was escalated (with each task's id), and what was already escalated by an earlier run.
2. Call `mcp__contextos__vault_log_append` with `entry: "vault health | <n> vault findings, <n> knowledge findings; <n> repaired, <n> fixed by the librarian, <n> escalated, <n> already escalated"` and `files` listing the notes the librarian changed and the tasks raised.

---

## Running on a schedule

Schedule it as `/dispatch` is scheduled (see the dispatch skill's Running on a schedule section), with the instructions `/vault health` and the librarian's workspace, `.contextos/workspaces/<slug>/`, as the local folder. Run it shortly before a scheduled `/dispatch`, so the chief of staff picks up its escalations in the same cycle. Never write a host's scheduled-task files.

---

## Invariants

- The run never waits on the operator. A decision goes to the chief of staff as a task, and from there to the operator only if the chief of staff cannot settle it.
- Steps 1 to 3 write nothing. Repairs are only through `doctor_resolve`, never a standing change such as initialising Git.
- Knowledge fixes are made by the librarian sub-agent, never by this skill directly, and only those that change no claim and decide nothing.
- A finding is escalated once: `origin` with `unique_fields` keeps a later run from raising it again.
- Never create or edit an `index.md`.
- Never reproduce the `health` job's checks with the MCP tools or the host's own file tools if the command line cannot run; report it and escalate it.
- The report is generated fresh on each run; it is not cached.
