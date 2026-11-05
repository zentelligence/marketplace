# Skill: job list

Summarises the vault's saved jobs with their owners and the lifecycle state ContextOS Web records, and the host's shared jobs, listed with `contextos-web jobs list --shared`. Read-only: never writes, validates, or runs anything.

---

## Step 1: find the vault's jobs

1. Call `mcp__contextos__fs_search_files` on `<vault>://registry/workflows` with the pattern `*/*/jobs/*.toml`. If `registry/workflows/` does not exist, say so and suggest `/vault update`.
2. Read every job file found, and each parent workflow's `workflow.toml`, in one `mcp__contextos__fs_read_multiple_files` call.
3. Read `<vault>://.contextos/jobs.toml` and `<vault>://.contextos/team.toml` with `mcp__contextos__fs_attach_file`. A missing `jobs.toml` means ContextOS Web has recorded nothing yet, so every job is a `draft`.

---

## Step 2: read each job

For each job file, take:

- **Slug**: the file's `slug`, else its file name without `.toml`. Slugs are unique within a workflow, not across the vault.
- **Workflow**: the folder the job file sits in, which is the workflow's slug, and the package folder above it.
- **Name**, **Owner**, **Inputs** (names and values), **Timeout** (the job's own `timeout_secs`; there is no fallback, and a job file without one does not load), **Entity** (the job's `entity`, else its workflow's, else `vault`), and **Ready** (`ready = true` means authoring is finished and ContextOS Web validates the job automatically).
- **Recorded state**, from `jobs.toml`'s `[<package>.<workflow>.<job>]` table: `lifecycle` (absent means `draft`), `schedule`, `suspension` (`code`, `reason`, and, when they were recorded, `by`, `at`, and for a failed first run `run` and `failure`; a suspension an older release stored as free text reads as `workflow/suspended`), `first_run` (the next live run is on probation), `dry_run_at`, and `validation` (`passed`, `at`, and each failure's `code`, `artefact`, and `message`).

Flag, as ContextOS Web would refuse them:

- A key other than `name`, `slug`, `timeout_secs`, `version`, `predecessor`, `owner`, `entity`, `inputs`, `log_level`, and `ready`.
- A missing `version` (`validation/artefact-invalid`: the job does not load).
- A missing `timeout_secs` (`validation/artefact-invalid`: the job does not load).
- An `entity` that is neither `vault` nor a slug in `.contextos/entities.toml` (`validation/entity-unresolved`).
- A missing `owner`, or one with no `[[member]]` entry of that `slug` in `team.toml` (`validation/owner-unresolved`).
- An input value the workflow does not declare, or a required input with no value (`validation/input-invalid`).

The recorded state describes the version ContextOS Web last saw. If a job's files changed since, ContextOS Web returns it to `draft` on its next pass (or validates it, if it was `enabled`); say so when a file looks newer than `validation.at`.

To say whether the release a job's `version` names is current, previous, future, or retired, and whether it is whole, run `contextos-web workflows releases <vault> <package> <workflow> --format json` and match the job's `version` with an entry in `releases`; quote that entry's `summary`. If the command is unavailable, report the release as unknown rather than inferring it from the files. `contextos-web jobs list <vault> --format json` gives the same per job directly (`version`, `release_kind`, `predecessor`, `successor`). Flag an `enabled` or `suspended` job on a `previous` or retired release, or on `current` while a `future` release exists, as one that could move through `jobs successor`, and show each chain as predecessor, job, successor.

---

## Step 3: shared jobs

Shared jobs live on the host, not in the vault. List them with `contextos-web jobs list --shared --format json`, which needs no `web.toml` and no running server and takes the host's state, not this session's shell location, as its source. Each entry in `jobs` has `package`, `workflow`, `job`, `file` (set only when the file's name is not the job's key), `name`, `state` (the lifecycle state), `schedule`, `ready`, `version`, `release_kind` (`current`, `previous`, `future`, or `retired`), `predecessor`, `successor`, `hash`, `problems`, and, for a suspended job, `suspension` (`code`, `reason`, `by`, `at`, `run`, and `failure`; `by`, `at`, and `run` are left out when they were never recorded). Never infer a state; report `state` as given. Report every `problems` entry with its `code` and `message`: a file that does not load (a `validation/` code), a key two files share (`workflow/job-key-taken`), or stored state whose file is missing (`workflow/job-not-found`). If the command is not available because `contextos-web` is not installed on this host, say shared jobs were not read.

---

## Step 4: report

Present the vault's jobs grouped by workflow, as a table: **Job**, **Name**, **Owner**, **State**, **Release** (`version` and its `release_kind`), **Chain** (predecessor and successor), **Schedule**, **On trial**, **Last validation**, **Last dry run**. Under the table, list any suspended job with its code, who suspended it, the run that failed it when there is one, and its reason, any failed validation with each failure's code and message, and every flag from Step 2.

List shared jobs separately, with their package and workflow.

If there are no jobs, say so and mention `/job create`, and `/workflow create` if there is no workflow yet.

Say what the report rests on: the job files and `.contextos/jobs.toml` read through ContextOS MCP, as recorded by ContextOS Web, not a fresh validation.

---

## Invariants

- Read-only. Never writes, validates, dry-runs, or runs anything.
- Report the state ContextOS Web recorded; never infer one it did not record.
