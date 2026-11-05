---
name: job
description: "Routes an operator command about ContextOS Web saved jobs to its sub-skill: list (summarise the jobs under `registry/workflows/*/*/jobs/` and the shared jobs on the host, with their lifecycle state), create (author a job for an existing workflow, then take it through static validation and a dry run to registration, ready for the operator to enable), update (review and revise jobs after their workflow, team, or ContextOS Web changes, and revalidate them). Fires on explicit `/job COMMAND` invocations and on conversational requests about saved jobs, e.g. 'what jobs does this vault have', 'set up a nightly job for the notes workflow', 'revalidate the jobs after that workflow change'. Does not fire for writing or changing a workflow's script or manifest, or a shared package (owned by the sibling workflow skill), for interactive apps (owned by the app skill), for `SLUG:role`, `SLUG:hat`, or `SLUG:agent`, or for `/vault COMMAND` and vault-content requests."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "<list|create [description]|update [workflow/job]>"
arguments: ["command"]
---

# Job: Router Skill

Routes job commands to the sub-skill that carries them out. Load this file first, then load only the sub-skill the command needs.

A job is a saved configuration of one workflow: the values of its inputs, its owner, and its run settings. ContextOS Web validates, schedules, and runs it with no agent session involved. This skill authors jobs and takes them to `registered`; the operator enables them. Workflows themselves belong to the [workflow](../workflow/SKILL.md) skill.

| | Vault job | Shared job |
| --- | --- | --- |
| File | `<vault>://registry/workflows/<package>/<workflow>/jobs/<job>.toml` | `workflows/<package>/<workflow>/jobs/<job>.toml` in the host's ContextOS data folder, authored only with `contextos-web jobs create`, `show`, `replace`, and `list` with `--shared` |
| Workflow | The workflow whose folder the job file sits in | A workflow from an installed package |
| State | `.contextos/jobs.toml` in the vault, readable through ContextOS MCP | The host's `state/shared-jobs.toml`, reported by the command line and the job's page |
| Owner | Required: a member of the vault's team | None of its own; `web.toml`'s `[owner]`, when set, owns every shared job |
| Timeout | `timeout_secs` required: whole seconds, greater than zero, never taken from the workflow | `timeout_secs` required, the same |
| Entity | Optional `entity`: a configured entity or `vault`; else its workflow's; else `vault` | None |
| Runs and records | `memory/jobs/<package>/<workflow>/<job>/...` in the vault | `runs/<package>/<workflow>/<job>/...` on the host |

The host's data folder is `~/.local/share/contextos` on Linux, `~/Library/Application Support/contextos` on macOS, and `%LOCALAPPDATA%\contextos\data` on Windows, beside the `packages/` folder that holds installed packages. It is named here for orientation only: never create, edit, or list a shared job's file in it with this session's own file tools. Every shared job file is created, read, replaced, and listed with `contextos-web jobs create|show|replace|list --shared ... --format json`, which reads and checks the TOML exactly as ContextOS Web does, stores the bytes unaltered, never overwrites on create, and takes the host's state lock. These commands need no `web.toml` and no running server. Each prints one JSON document with `--format json`, including a refusal as `{"error":{"code":...,"message":...}}` on standard output with exit status 1 and nothing on standard error; a usage error exits with status 2.

A vault job can be authored either by writing its file through ContextOS MCP or with the same four commands, `contextos-web jobs create|show|replace|list <vault> <package> <workflow> [<job>]`, which check the TOML exactly as ContextOS Web does and, for `create`, never overwrite. `jobs list <vault>` reports each job's release, whether that release is `current`, `previous`, `future`, or retired, its predecessor, and its successor. Prefer the commands when the job file is to be replaced against a known hash (`show` gives `content` and `hash`; `replace` takes `--expected-hash`).

---

## Releases and successors

A job names one release of its workflow in `version`, and a job that is `enabled`, `suspended`, or `retired` never changes it. It changes release only through a successor: a new job of the same workflow, copied from its predecessor with `version` replaced and `predecessor` added, which starts as a `draft` and, when the operator enables it, takes the predecessor's schedule and retires the predecessor. A job that was never enabled (`draft`, `validated`, or `registered`) changes `version` in place with `jobs replace`.

- `contextos-web jobs successor <vault> <package> <workflow> <job> <new-job> [--to future|previous|<version>] --format json` (`--shared <package> ...` for a shared job). `--to` defaults to `future`, the newest `future` release; `previous` makes a return successor; an exact version names that release.
- `contextos-web jobs successor <vault> <package> <workflow> --all [--to ...]` makes one for every job `enabled` or `suspended` on the `current` release. `--all --to previous` prepares a return of the whole workflow to its `previous` release, which is then validated, dry-run, and enabled like any successor.
- Enabling a successor (the operator's `jobs schedule`) says which predecessor it retired and how `current` and `previous` moved. Never give a successor a schedule of your own choosing; the operator may omit one to take the predecessor's.

Never edit `version` or `predecessor` in the file of an `enabled`, `suspended`, or `retired` job by hand. An `enabled` job so edited is validated at once and suspended with `workflow/validation-failed`; a `suspended` one fails validation on resume and stays suspended, and resuming is refused until the file is restored; a `retired` one is refused re-activation with `workflow/transition-refused` until it is restored. Restore the recorded value, then make a successor.

Refusals to meet and what to say:

| Code | Meaning and next step |
| --- | --- |
| `workflow/transition-refused` | A transition or successor the rules forbid; the message names the reason. Common ones: the predecessor already has a standing successor (not retired, or ever enabled), so neither another successor nor a re-activation is allowed; the predecessor was retired without ever being enabled, so it cannot be a predecessor (make the successor of the job before it, or change `version` in place); `--to previous` when no `previous` release is recorded |
| `workflow/job-key-taken` | The new key is tracked under another file or is the `predecessor` of a job not retired. Choose another key |
| `workflow/job-exists`, `workflow/job-state-remains`, `workflow/job-key-invalid` | The key is already a file, has stored state with no file, or is not a usable key. Stop and ask; never overwrite or delete to work round it |
| `workflow/package-unavailable` | The release is not installed in the store (or `future` was asked for and none is recorded). Install it with `workflows install` and confirm with `workflows releases`, or choose an installed release. For an enabled job whose unedited release has since gone, tell the operator and stop |
| `workflow/job-not-runnable` | A live run by hand of a job with a standing successor, or of a successor whose predecessor is `enabled` or `suspended`. Dry-run the successor instead |
| `workflow/job-busy` | A run holds the predecessor's claim. The operator repeats the enabling once it has ended |

Report each refusal with its code and message verbatim and change nothing to get round it.

---

## Lifecycle

| State | Runs on its schedule | Run by hand | Who moves it here |
| --- | --- | --- | --- |
| `draft` | no | no | Any new job, or any change to its workflow manifest, entry script, or job file |
| `validated` | no | no | Static validation passing (`contextos-web jobs validate`) |
| `registered` | no | yes | A dry run completing for the validated version (`contextos-web jobs dry-run`) |
| `enabled` | yes | yes | The operator, by setting a schedule |
| `suspended` | no | yes | The operator, or ContextOS Web when a new version fails validation, its first live run fails, its owner is no longer in the team, or the validation rules tighten and it no longer passes |
| `retired` | no | no | The operator |

This skill takes a job through `draft`, `validated`, and `registered`, one distinct step at a time, and reports the state ContextOS Web records after each. Setting a schedule, clearing it, suspending, resuming, retiring, re-activating, and deleting are the operator's acts: this skill gives the operator the exact command or page, and never runs it. A job file never carries a `schedule`; like any other unknown key, ContextOS Web refuses it as `validation/artefact-invalid`.

A schedule is a five-field cron expression read in the operator's local time zone (the zone `vault_info` reports as `time_zone`), daylight saving included, so `0 7 * * *` runs at 07:00 local time all year.

---

## Before any command

1. **ContextOS MCP.** Follow steps 1, 2, and 4 of the vault router's [Before any command](../vault/SKILL.md#before-any-command) section: confirm the server with `mcp__contextos__vault_info` and choose the vault. If the server is unavailable, report it and stop; never fall back to the host's own file tools for vault files. Paths below are within the chosen vault (`<vault>://...`).
2. **The V-sequence set.** `create` and `update` compose the shipped roles and hats. Check them as the workflow router's [Before any command](../workflow/SKILL.md#before-any-command) step 2 describes, and tell the operator to run `/vault update` if any is missing.
3. **The command line.** Validation and dry runs use the `contextos-web` command line exactly as the workflow router's [The contextos-web command line](../workflow/SKILL.md#the-contextos-web-command-line) section describes. The commands this skill runs are `contextos-web jobs validate` and `contextos-web jobs dry-run`, with `<vault> <workflow> <job>` for a vault job or `--shared <package> <workflow> <job>` for a shared one. Give both `--format json` and read the run summary as the workflow router describes. A live `contextos-web jobs run` is only for an ad hoc run the operator explicitly asks for, and only for a job that is `registered`, `enabled`, or `suspended`.

---

## Owners

Every vault job names an `owner` who is a member of the vault's team. ContextOS Web refuses a job whose owner is not in `.contextos/team.toml` with `validation/owner-unresolved`, matching the slug exactly (`Vela` is not `vela`). The owner is accountable for the job, and failures are raised for them as tasks.

The team needs at least one member, and exactly one with `chief_of_staff = true`: an empty team, or one with no chief of staff or several, is `workflow/team-invalid` (rule `team-empty`, `no-chief-of-staff`, or `several-chiefs-of-staff`), and ContextOS Web pauses every scheduled job in the vault until it is corrected. When an owner leaves the team, ContextOS Web suspends the job's schedule with `workflow/owner-unresolved`, refuses a live run of it, and raises a task for the chief of staff; resuming it needs a new owner first. A job's failures reach the task list by themselves, as tasks whose `origin` begins `contextos-web:`: a failed validation of a ready draft, every suspension the system makes, and a failed scheduled run of an enabled job whose script started (a run that ended before its script did, such as one whose entry script could not be read, raises nothing, and a run record says which with `script_started`). This skill never raises those tasks, and a task with that origin is not to be created, edited, or closed by it; the owner closes them once the cause is fixed. A run the command line refuses because the job is suspended says why: its text and its JSON summary carry the suspension (`code`, `by`, `at`, `run`, `reason`, and `failure`, with what was never recorded left out) beside the refusal's `message`.

To propose the owner:

1. Find the team's technologist: search `<vault>://registry/agents` with `mcp__contextos__fs_search_files` (pattern `*.md`), and read each definition's frontmatter with `mcp__contextos__frontmatter_read`. The technologist is the definition with `kind: member` and `function: technologist`; its `name` is the member's slug. Never assume a slug.
2. Read `<vault>://.contextos/team.toml` with `mcp__contextos__fs_attach_file` and confirm a `[[member]]` entry has that `slug`.
3. Offer the technologist as the default and let the operator choose any other member listed in `team.toml` instead. If there are several technologists, ask which.
4. If no technologist is defined, ask the operator to choose a member from `team.toml`. If `team.toml` is missing or lists nobody, a vault job cannot be owned yet: tell the operator to run `/vault init`, which sets up the team, and stop.

---

## Available commands

| Command | Sub-skill | Purpose |
| --- | --- | --- |
| `list` | [list.md](list.md) | Summarise jobs, their owners, and their recorded lifecycle state |
| `create [description]` | [create.md](create.md) | Author a job, validate it, and dry-run it to registration |
| `update [workflow/job]` | [update.md](update.md) | Review, revise, and revalidate existing jobs |

---

## Routing

Take the command from the declared `command` argument, or from the operator's own words when the skill fired conversationally.

- No command, or `list`, or a question about which jobs exist or what state they are in: load [list.md](list.md).
- `create`, optionally with a description: load [create.md](create.md), passing the description as the answer to its first question.
- `update`, optionally with `<package>/<workflow>/<job>`: load [update.md](update.md), scoped to that job if given.
- A request to schedule, enable, suspend, resume, retire, re-activate, or delete a job: these are the operator's acts. Give the exact command from [create.md](create.md)'s [Operator activation](create.md#step-7-operator-activation) step, or the job's page, and do not run it.
- A request to move jobs to a newer release, or back to the previous one: load [update.md](update.md) at its [Moving a job to another release](update.md#moving-a-job-to-another-release) section.
- A request to change what a workflow does: hand over to the [workflow](../workflow/SKILL.md) skill.
- Anything else: ask one short clarifying question.

---

## Invariants

- Vault files, including `.contextos/jobs.toml` and `.contextos/team.toml`, are read and written only through ContextOS MCP, and this skill never writes either of those two.
- Never write a `schedule` into a job file, and never schedule, enable, suspend, resume, retire, re-activate, or delete a job.
- Every vault job names an owner who is in `.contextos/team.toml`, and states its own `timeout_secs`.
- Never raise, edit, or close a task whose `origin` begins `contextos-web:`.
- Never start a live run as a substitute for a dry run, and never report a state ContextOS Web has not recorded.
- Never put a secret, credential, or token in a job file.
