# Skill: job update

Reviews existing jobs and revises and revalidates the ones that need it: after their workflow changed, after the team changed, after ContextOS Web changed, when a job is suspended or failing, or when the operator's needs moved. It takes changed jobs back through static validation and a dry run to `registered`, exactly as [create.md](create.md) Steps 4 and 5 do, and leaves every operator act to the operator.

---

## Step 1: what prompted this

Ask: "What prompted this review: a workflow change, a team change, a ContextOS Web upgrade, a suspended or failing job, a change in what a job should do, or a general health check?" Store as `change_narrative`. Confirm any claimed ContextOS Web change with `contextos-web --version` and the relevant `--help`, or the operator's release notes, before acting on it.

---

## Step 2: scope and evidence

If the router passed `<package>/<workflow>/<job>`, review that job; otherwise run [list.md](list.md) Steps 1 to 3 and review every job. For each job in scope, gather:

- Its job file, its workflow's manifest, and its recorded state in `.contextos/jobs.toml` (`lifecycle`, `schedule`, `suspension`, `first_run`, `validation`, `dry_run_at`).
- For a suspended or failing job, its recent run records: `mcp__contextos__fs_search_files` on `<vault>://memory/jobs/<package>/<workflow>/<job>` (pattern `**/R-*.md`), then `mcp__contextos__fs_attach_file` on the newest few for `status`, `error`, and the call table.
- Its owner's entry in `.contextos/team.toml`.

---

## Step 3: review

As `auditor:role` wearing `critic:hat`, produce findings, each with its evidence:

- The owner is missing, or is no longer in `team.toml`. Propose a new owner as the router's [Owners](SKILL.md#owners) section describes; never guess one.
- An input value no longer satisfies the workflow's declared inputs, or a newly required input has no value.
- A key ContextOS Web refuses, including any `schedule`.
- A suspended job: name its recorded code and reason, and whether the cause lies in the job (fix here), the workflow (`/workflow update`), or the host, such as a server or tool missing from `web.toml` (the operator's fix). The code decides the fix: `workflow/owner-unresolved` needs a new owner from `team.toml`, then a resume; `workflow/validation-failed` needs the job's files corrected for the version, then a resume; `workflow/probation-failed` names the run that failed the trial (`run`) and the code it failed with (`failure`), so read that run's record, correct the cause, and resume; `workflow/operator-suspended` is the operator's own hold, and needs no fix; `workflow/package-unavailable` (a shared job) needs its package installed again.
- A job file with no `timeout_secs`, which an upgrade suspends as `workflow/validation-failed` when it is enabled: add the key, whole seconds greater than zero, then validate.
- Tasks ContextOS Web raised for the job (`origin` beginning `contextos-web:`) are the work items for these findings: say which are open, and leave closing them to their owner once the cause is fixed.
- A recorded validation failure that is stale because its cause outside the job's files (a server, a team member) has since been fixed: it needs validating again on demand.
- A job whose files changed since its last validation, which ContextOS Web has returned or will return to `draft`.
- A job on a release that is no longer current (`previous` or retired, from `workflows releases`), or an `enabled` or `suspended` job with a newer `future` release to move to. Such a job never changes `version` in place: it moves through a successor (Step 4).

Present the findings per job and let the operator choose which to act on.

---

## Step 4: revise

For each confirmed finding, as `engineer:role` wearing `refiner:hat`, edit the job file with `mcp__contextos__fs_edit_file`. A shared job is revised through the command line and never with this session's own file tools: read it with `contextos-web jobs show --shared <package> <workflow> <job> --format json`, which gives `content` and `hash`, edit the content, keeping its `slug` line when it has one (a file stored under another name is tracked by that `slug`, and `replace` refuses content that drops it with `workflow/job-key-mismatch`), and apply it with `contextos-web jobs replace --shared <package> <workflow> <job> --file - --expected-hash <hash> --format json`, piping the new TOML. `workflow/job-changed` means the file changed since it was read: run `show` again, reapply the edit to the current content, and replace again. Never add a `schedule`. Tell the operator that any edit to a job file is a new version: a `draft`, `validated`, or `registered` job returns to `draft`, and an `enabled` job is validated again by ContextOS Web and suspended if that fails.

### Moving a job to another release

A job in `draft`, `validated`, or `registered` changes `version` in place with `jobs replace`. An `enabled`, `suspended`, or `retired` job moves only through a successor: a new job whose file is the old one with `version` replaced and `predecessor` added. With the operator's confirmation, run `contextos-web jobs successor <vault> <package> <workflow> <job> <new-job> [--to future|previous|<version>] --format json` (or `--shared <package> <workflow> ...`); `--to` defaults to the newest `future` release. `--all` in place of `<job> <new-job>` makes one for every `enabled` or `suspended` job on the current release, named `<job>-v<major>-<minor>-<patch>`, and writes nothing when any job is refused, reporting every refusal. `--all --to previous` prepares a return of the whole workflow to its previous release.

- Read each successor's `interface_changes`: when the two releases' inputs or outputs differ, tell the operator which inputs each successor must take up, and edit them with `jobs replace` while the successor is a `draft` (its inputs are checked against its release at validation, not when it is made). When they are equal the successor carries over unchanged; when the report says unknown, compare the releases' `workflow.toml` files before validating.
- A predecessor and its successors are a chain with one job in use. A live run by hand of a job with a standing successor, or of a successor whose predecessor is `enabled` or `suspended`, is refused with `workflow/job-not-runnable`, so try a successor with dry runs.
- A successor that was ever enabled stands for good: its predecessor can never return or have another successor, and its key stays taken.
- A job on `current` returns to `previous` the same way: `jobs successor --all --to previous` (or one job with `--to previous`), then validate, dry-run, and enable each; enabling the first swaps `current` and `previous`. When the report says `previous` is not recorded, the command refuses with `workflow/transition-refused`.
- Refusals (`workflow/transition-refused`, `workflow/job-key-taken`, `workflow/package-unavailable`, and the rest) are listed in the router's [Releases and successors](SKILL.md#releases-and-successors) section. A predecessor retired without ever being enabled cannot be a predecessor: change its `version` in place or make the successor of the job before it. Never edit `version` or `predecessor` in the file of an `enabled`, `suspended`, or `retired` job by hand; restore the recorded value, then make a successor.
- Validate and dry-run the successor (Step 5), then hand it to the operator to schedule. Enabling it retires its predecessor, takes the predecessor's schedule when none is given, and may move the workflow's current and previous releases; `jobs schedule` reports both. It is refused with `workflow/job-busy` while a run holds the predecessor's claim, so the operator repeats it once that run has ended. The scheduler records an info `job.retired` event for the predecessor and raises no task.

---

## Step 5: revalidate

For each job revised, and each job whose workflow changed, run [create.md](create.md) Step 4 (static validation) and then Step 5 (dry run), as distinct steps, and report the recorded state after each.

What happens next depends on the state:

- A `registered` job is ready for the operator to schedule again, if it had been enabled before.
- An `enabled` job validated for its new version stays `enabled`, and its next live run is on probation.
- A `suspended` job stays suspended. Resuming is the operator's act: give them `contextos-web jobs resume <vault> <package> <workflow> <job>` (or `--shared ...`), which validates the current version before resuming, or the Resume action on the job's page.
- A `retired` job cannot be validated. Re-activating it as a `draft` is the operator's act (`contextos-web jobs reactivate ...`).

---

## Step 6: log and report

Call `mcp__contextos__vault_log_append` once with `entry: "job update | Reviewed N, revised M | prompted by: <short change_narrative>"` and `files` listing every vault file changed. Report per job: what changed, each command run with its result and the host it ran on, the recorded state before and after, what was not proved, and any operator act now needed, with its exact command.

---

## Invariants

- Never revise without the operator confirming the finding, and never guess an owner or an input value.
- Never schedule, clear a schedule, suspend, resume, retire, re-activate, or delete a job.
- Never start a live run in place of a dry run.
