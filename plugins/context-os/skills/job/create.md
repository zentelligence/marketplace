# Skill: job create

Authors one saved job for an existing workflow, then takes it through static validation and a dry run to `registered`, reporting the state ContextOS Web records after each step. Enabling it is left to the operator. Each step is distinct: never fold validation into the dry run, or the dry run into activation.

The V-sequence is lighter here than for a workflow, because a job configures logic that already exists: `analyst:role` defines the configuration, `engineer:role` writes it, `auditor:role` validates and dry-runs it, and `analyst:role` accepts it against the operator's purpose.

---

## Step 1: the workflow

Ask which workflow the job runs, or infer it from the operator's description and confirm.

- **Workflow in the vault**: confirm `<vault>://registry/workflows/<package>/<workflow>/workflow.toml` exists and that `<package>/workflows.toml` lists the workflow, and read the `workflow.toml` with `mcp__contextos__fs_attach_file` for its inputs, timeout, and the `[mcp_servers]` and `[mcp_tools]` lists. Check it has at least one scenario under `tests/` (`mcp__contextos__fs_search_files`, pattern `tests/*.toml`): without one, no job of it can be registered.
- **Shared workflow**: confirm the package is installed with `contextos-web packages list --shared`, and read its workflow's inputs and `[mcp_tools]` with `contextos-web packages inspect --shared <package> <version>`.

If the workflow does not exist, or needs changing to do what the operator wants, hand over to `/workflow create` or `/workflow update` first.

---

## Step 2: interview

As `analyst:role` wearing `definer:hat`, ask in turn and wait for each answer. "Not sure yet" is recorded as open.

**Q1 (purpose):** "What is this job for: which run of the workflow, on what, for whom?" Store as `purpose_narrative`; it is the acceptance test in Step 8.

**Q2 (inputs):** For each input the workflow declares, ask for its value in plain terms, and say which are required. Never invent a value. A `vault` input of a shared workflow names a vault exactly as `vault_info` lists it.

**Q3 (owner):** Propose the owner as the router's [Owners](SKILL.md#owners) section describes: the team's technologist by default, or any other member of `.contextos/team.toml` the operator chooses. Skip this for a shared job, which has no owner of its own; instead say whether `web.toml` has an `[owner]` (ask the operator if you cannot read it).

**Q4 (cadence):** "When should this run once it is enabled?" Translate the answer into a five-field cron expression in the operator's local time zone (`vault_info`'s `time_zone`) and confirm both forms: "That is `<cron>`, which is `<plain local time>` where you are, daylight saving included." This is a recommendation for the operator to set in Step 7. It is never written into the job file. "By hand only" is a valid answer.

**Q5 (run settings):** Always ask for `timeout_secs`: how many whole seconds a run may take before it is stopped, greater than zero. Every job states its own, vault or shared, and never takes its workflow's, so there is no default to offer; propose a figure from the workflow's own timeout or the work it does, and let the operator choose. Ask for `log_level` (`debug`, `info`, `warn`, or `error`; otherwise the workflow's, else the host's) and `entity` (a configured entity slug from `.contextos/entities.toml`, or `vault`; otherwise the workflow's, else `vault`) only if the operator wants them. Skip `entity` for a shared job, which has none.

**Q6 (release):** Settle `version`, which every job states and which is never a range: the exact release of the workflow's package the job runs. Choose it from `contextos-web workflows releases <vault> <package> <workflow> --format json` (`--shared <package> <workflow>` for a shared package): offer a release whose `kind` is `current` or `future` and whose `condition` is `whole`, normally the one the operator just installed (`workflows install` reports it as `release.version`), quote its `summary`, and confirm its `version`. A job runs exactly that release and never the newest, so a later release needs a job that names it.

---

## Step 3: confirm and author

Summarise the job (workflow, slug, name, inputs, owner, run settings, and recommended schedule) and ask the operator to confirm. Then, as `engineer:role` wearing `solver:hat`, write the job file. Its slug is its file name; use lowercase letters, digits, and hyphens.

Vault job, written with `mcp__contextos__fs_write_file` to `<vault>://registry/workflows/<package>/<workflow>/jobs/<job>.toml` (or stored with `contextos-web jobs create <vault> <package> <workflow> <job> --file - --format json`, which reports the outcomes and refusals described below for a shared job, including `workflow/job-key-taken` for a key that is the `predecessor` of a job not retired):

```toml
name = "Nightly notes copy"   # required, not blank
owner = "<member slug>"       # required for the job to run: a member of .contextos/team.toml
timeout_secs = 120            # required: whole seconds, greater than zero
version = "1.2.0"             # required: the exact installed release of the workflow's package the job runs, never a range
entity = "<entity slug>"      # optional: a configured entity or "vault"; else the workflow's, else "vault"
log_level = "warn"            # optional
ready = true                  # authoring is finished, so ContextOS Web may validate it

[inputs]
since = "2026-01-01"
```

Shared job, stored with `contextos-web jobs create` in the next block, never by writing the host's data folder with this session's own file tools:

```toml
name = "Copy meeting notes"
version = "1.2.0"             # required: the exact installed release the job runs, never a range
timeout_secs = 120            # required: whole seconds, greater than zero
log_level = "warn"            # optional
ready = true

[inputs]
source_vault = "client-a"
destination_vault = "client-b"
```

Store a shared job by piping the TOML to the command, so it never touches a file the session wrote:

```bash
contextos-web jobs create --shared <package> <workflow> <job> --file - --format json
```

Read the JSON result: `outcome` is `created` or `unchanged` (the same bytes were already there), `hash` is the content hash, and `warnings` may carry `workflow/package-unavailable`, which means the package or workflow is not installed yet, so the job cannot validate until it is; tell the operator. A refusal is `{"error":{"code","message"}}` with exit status 1. `workflow/job-exists` (a different file is already there) and `workflow/job-state-remains` (stored state is left for that key) are stop-and-ask: tell the operator, and never overwrite, delete, or work round them. `workflow/job-file-invalid` carries the validation code in `cause` (fix the TOML as Step 4's table says); `workflow/job-key-mismatch` means a `slug` in the TOML differs from the job; `workflow/job-key-taken` means another file already has that key.

No other key is accepted: never a `schedule`, and never `entry`, `mcp_servers`, or `mcp_tools`, which belong to the workflow. Values follow each input's kind: text for `string` and `vault`, and TOML numbers, booleans, arrays, and tables for the rest. Never write a secret.

The job is now a `draft`. `ready = true` is not a state change and is not part of the job's version: it only lets ContextOS Web validate the job on its own.

---

## Step 4: static validation

As `auditor:role` wearing `critic:hat`, run:

```bash
contextos-web jobs validate <vault> <package> <workflow> <job>
contextos-web jobs validate --shared <package> <workflow> <job>
```

Validation compiles the script without running it and calls no tool. A pass prints `Validation passed for ... It is validated.` A failure exits unsuccessfully with `workflow/validation-failed` and lists every failure with its code and file:

| Code | Usual fix |
| --- | --- |
| `validation/artefact-missing`, `validation/artefact-invalid` | A file is missing, or a manifest has an unknown key or a bad value. A job file with no `timeout_secs` (or a zero, negative, fractional, or text one) fails as `validation/artefact-invalid`, naming the key. Fix the job file here; a workflow manifest goes to `/workflow update` |
| `validation/script-syntax` | The entry script does not compile: `/workflow update` |
| `validation/input-invalid` | Correct the input values against the workflow's declared inputs |
| `validation/server-not-configured`, `validation/tool-not-found` | The host's `web.toml` lacks a server, or a server lacks a tool. The operator fixes the host, then validate again |
| `validation/owner-unresolved` | The job names no owner, or one who is not in `.contextos/team.toml` (matched exactly, so `Vela` is not `vela`). Choose an owner who is |
| `validation/entity-unresolved` | The `entity` is neither `vault` nor a slug in `.contextos/entities.toml`. Correct it, or remove the key |

While the team is empty, has no chief of staff, or several, or does not parse, ContextOS Web reports the owner check as unverifiable and `workflow/team-invalid` blocks live runs: tell the operator to correct `.contextos/team.toml`, then validate again. A check that could not be made (a server that could not be reached, or an unusable team) is reported as unverifiable: the job does not pass, nothing is stored, and its state is unchanged. Fix with `engineer:role` wearing `refiner:hat` and validate again until it passes.

For a vault job, read `<vault>://.contextos/jobs.toml` with `mcp__contextos__fs_attach_file` and report the job's recorded `lifecycle` (`validated`) and `validation`. For a shared job, report the state the command printed.

---

## Step 5: dry run

Run:

```bash
contextos-web jobs dry-run <vault> <package> <workflow> <job> --format json [--scenario <name>]
contextos-web jobs dry-run --shared <package> <workflow> <job> --format json [--scenario <name>]
```

The dry run executes the script against a scenario's mocked results; no call reaches a server for real, though each call's arguments are checked against the tool's live schema. It completes when the script succeeds, or succeeds with warnings, and has used every call the scenario declares. `--scenario` is required when the workflow has more than one. A dry run that completes for the validated version registers the job. It leaves a run record marked `dry_run: true`.

A dry run that fails, or that ran a version changed since validation, registers nothing: fix the cause and return to Step 4. A failure in the workflow's script or scenarios goes to `/workflow update`.

Report the job's registration from the summary's `registration` field: `{"registered": true, "reason": null}`, or `{"registered": false, "reason": ...}` with the reason (`dry_run_not_completed`, `scenario_calls_unused`, `not_validated`, `version_changed`, `inputs_overridden`, or `state_unavailable`). For a vault job, read `<vault>://.contextos/jobs.toml` with `mcp__contextos__fs_attach_file` to confirm the recorded state (`registered`, with `dry_run_at`).

`--input name=value` overrides on `jobs dry-run` and `jobs run` are for ad hoc runs only: a run with overrides never registers a job and never settles its first-run trial, so never use one to register a job.

Never run the job live to stand in for a dry run.

---

## Step 6: register in the index

Leave `<vault>://registry/workflows/index.md` alone: the ContextOS MCP server maintains it, and `/job list` reads the job files themselves. Call `mcp__contextos__vault_log_append` with `entry: "job create | Registered job: <package>/<workflow>/<job> (owner: <owner>)"` and `files` listing the job file.

---

## Step 7: operator activation

Enabling a job is the operator's act. Give the operator, without running them:

- The schedule command, with the cron expression confirmed in Step 2: `contextos-web jobs schedule <vault> <package> <workflow> <job> "<cron>"` (or `jobs schedule --shared <package> <workflow> <job> "<cron>"`), or the job's page at `/<vault>/workflows/<package>/<workflow>/jobs/<job>` (or `/shared/workflows/<package>/<workflow>/jobs/<job>`), which offers the same.
- What enabling means: the job runs on that schedule in their local time, its first live run is on probation and a failure suspends it, a failed run is never retried, and any later change to the job's files makes a new version that ContextOS Web validates before it runs again.
- That the job can also be run by hand from its page while `registered`, without a schedule.

---

## Step 8: accept

As `analyst:role`, check the registered job against `purpose_narrative` with the evidence from Steps 4 and 5, and report to the operator:

- The job file path, workflow, owner, and inputs.
- Exactly what was validated and how: each command, its result, and the host and `web.toml` it ran against.
- The state ContextOS Web recorded after each step.
- What was not proved: a dry run uses mocked results, so the first live run is the first contact with the real tools.
- The recommended schedule and the command or page to enable it.

---

## Invariants

- Never write before the Step 3 confirmation, and never invent an input value, an owner, or a timeout.
- Every job states its own `timeout_secs`.
- Never write a `schedule` into a job file, and never run `jobs schedule` or any other operator command.
- Validation and the dry run are distinct steps, each followed by a report of the recorded state.
- A vault job's owner is always a member of `.contextos/team.toml`.
