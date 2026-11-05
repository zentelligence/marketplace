---
name: workflow
description: "Routes an operator command about ContextOS Web workflows to its sub-skill: list (summarise the vault's workflow packages under `registry/workflows/` and the shared packages installed on the host), create (guided interview and V-sequence build of a workflow in a vault package or a shared package, proved with a dry run), update (review and revise workflows after ContextOS Web or a workflow's needs change). Fires on explicit `/workflow COMMAND` invocations and on conversational requests to list, build, or refresh workflows or workflow packages, e.g. 'what workflows does this vault have', 'build a workflow that files new meeting notes', 'package this workflow so other vaults can use it', 'refresh the workflows after the contextos-web upgrade'. Does not fire for saved jobs, schedules, or a job's lifecycle (owned by the sibling job skill), for interactive apps (owned by the app skill), for `SLUG:role`, `SLUG:hat`, or `SLUG:agent` (owned by those skills), or for `/vault COMMAND` and vault-content requests."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "<list|create [description]|update [slug]>"
arguments: ["command"]
---

# Workflow: Router Skill

Routes workflow commands to the sub-skill that carries them out. Load this file first, then load only the sub-skill the command needs.

A workflow is a Rhai script that ContextOS Web runs with no agent session involved: every effect it has is an MCP tool call, checked against what the workflow declares before it is sent. This skill develops workflows and proves them with dry runs. Saved jobs, their lifecycle, and their owners belong to the [job](../job/SKILL.md) skill. Workflows and jobs are a flywheel: skills develop and register them, and ContextOS Web validates, schedules, and runs them.

Every workflow lives in a package, in the vault and on the host alike. A package is a folder holding a `workflows.toml` that lists its workflows by name, and a folder for each workflow with its own `workflow.toml`:

```text
<package>/
├── workflows.toml            workflows = ["scaffold", "update"], and the modules, templates, and libraries they share
├── <workflow>/workflow.toml  one workflow: name, entry, timeout_secs, entity, [mcp_servers], [mcp_tools], [[input]], [[output]], [[required_tool_contracts]], log_level
├── <workflow>/<entry>.rhai   that workflow's scripts, and its jobs/ and tests/ folders
├── modules/                  .rhai files every workflow of the package may import
└── templates/                files every workflow of the package may read
```

A package lists exactly one of `workflows.toml` and `library.toml`, and that file says what kind of package it is. A library package holds one library: a `library.toml` and its modules, with no workflow.

| | Run from the vault | Shared package |
| --- | --- | --- |
| Source | `<vault>://registry/workflows/<package>/`, with a `workflows.toml` | The same folder, built into a `.tar.gz` bundle with a `manifest.toml` that describes the release |
| Runs from | A release of the source installed into the vault's own package store, which only ContextOS Web writes | A release installed in the ContextOS Web host's package store from the bundle |
| Reaches | Its own vault only, and the calls its `[mcp_servers]` and `[mcp_tools]` lists permit | The calls the same lists permit, and the vaults its `vault` inputs name at run time |
| Versioned | By semver release; a job names the release it runs | By semver release; several releases can be installed side by side |
| Jobs | `<package>/<workflow>/jobs/<job>.toml`, with an owner on the vault's team | Shared job files on the host, owned by `web.toml`'s `[owner]` if any |
| Choose when | The logic serves this vault, or is still being shaped | The same logic must run for several vaults, across vaults, or with no vault, or be distributed to other hosts |

Start with a vault package unless the operator names a reason for a shared one. A workflow that declares a `vault` input is shared and installs only into the host's store.

A package in the vault is written only through ContextOS MCP. ContextOS Web finds a vault package by its `workflows.toml`, and a workflow by the folder `workflows.toml` lists; a folder with a `workflow.toml` that `workflows.toml` does not list is not registered. A job is found by listing the job files in a workflow's `jobs/` folder, and its workflow is the folder it sits in.

---

## Before any command

1. **ContextOS MCP.** This skill reads and writes the vault only through ContextOS MCP. The one exception is bundling a package release, where the session's shell reads (never writes) the package's source folder from the vault's path to build the bundle outside the vault. Follow steps 1, 2, and 4 of the vault router's [Before any command](../vault/SKILL.md#before-any-command) section: confirm the server with `mcp__contextos__vault_info` and choose the vault. If the server is unavailable, report it and stop; never fall back to the host's own file tools for vault files. Paths below are within the chosen vault (`<vault>://...`).
2. **The V-sequence set.** `create` and `update` compose the shipped roles (strategist, analyst, architect, engineer, auditor) and hats (definer, planner, solver, critic, refiner, synthesiser). Check each exists with `mcp__contextos__fs_get_file_info` on `<vault>://registry/roles/<slug>.md` and `<vault>://registry/hats/<slug>.md`. If any is missing, tell the operator to run `/vault update`, which adds them, and offer to continue without the missing ones; never write them yourself. Where one is missing and the operator continues, reason as that stage would and say once that the formal definition was not used.

---

## The contextos-web command line

Development uses the `contextos-web` command line on the operator's ContextOS Web host. It reads `web.toml` from `--config <path>`, else `CONTEXTOS_WEB_CONFIG`, else `~/.config/contextos/web.toml`, and connects its own MCP sessions, so the web server need not be running.

- Run it from this session's shell only when the shell is on that host. Check first with `contextos-web --version`. If the command is missing or cannot reach the host's configuration, give the operator the exact command to run and ask them to paste its output. Never reproduce a validation or a dry run by reasoning about the files instead.
- Run every `jobs run`, `jobs dry-run`, and `workflows run` with `--format json`. Standard output is then exactly one JSON document, the run summary, and nothing else: a script's `print` and `debug` go to the host log. Read its fields (`outcome`, `code`, `message`, `exit_code`, `run.record`, `outputs`, `registration`, `warnings`, `host_warnings`) and never parse the text form. `outcome` is `succeeded`, `degraded` (succeeded with warnings), `failed`, `cancelled`, or `refused` (the script never started).
- The exit status grades the ending: 0 completed, 1 failed, 2 the command line was not understood (no summary), 3 and 75 refused so nothing ran (75 is `workflow/job-busy`), 124 timed out, 130 cancelled. A refusal made no script call and never changes a job's lifecycle: it does not settle a first-run trial, suspend the job, or leave the job any less enabled, since an outage or a missing release is no defect of the job. Its only side effects are that a vault override refusal still uses up a run number, and that a vault run refused after its record was created (an unreadable entry script, say) leaves a `failed` record. A failure, a timeout, or a cancellation may have made some calls, and a cancelled run's calls are not undone.
- Report every result verbatim enough to keep its `validation/` or `workflow/` code, and say on which host and against which `web.toml` it ran.
- Commands this skill runs during development:
  - `contextos-web workflows run <vault> <package> <workflow> --source --dry-run --format json [--scenario <name>] [--input name=value ...]`: proves a vault workflow's source in `registry/` against a scenario, installing nothing. A library it names without a requirement is read from its source in `registry/libraries/`, and one named with a requirement from the newest installed release that satisfies it; the summary's `libraries` gives each one's `origin`, `source` or `release`. `workflows install` installs the library source a source run read, so what was tested is what is installed; `--release current|future|previous|<version>` in place of `--source` proves an installed release instead (the current one when neither is given). No call reaches a server for real; arguments are still checked against each tool's live schema.
  - `contextos-web workflows run --shared <package> <workflow> --dry-run --format json [--release current|future|previous|<version>] [--scenario <name>] [--input name=value ...]`: the same for an installed package.
  - `contextos-web packages list --shared --format json` and `contextos-web packages inspect --shared <package> <version> --format json`: read the host's package store; give `<vault>` in place of `--shared` for a vault's. `list` reports each release's `condition`, `origin`, the `kind` of each workflow in it (`current`, `previous`, `future`, or `retired`), its library lock, and every reason a rule keeps it.
  - `contextos-web packages install --shared <bundle.tar.gz>` (or `<vault> <bundle.tar.gz>`) and `contextos-web packages remove --shared <package> <version>` (or `<vault> <package> <version>`): change a package store, so run each only after the operator confirms it. Both stores remove releases nothing keeps on their own afterwards, and report them; manual removal is rarely needed. `remove` is refused with `packages/in-use`, naming the jobs and releases, while a rule keeps the release. Never add `--force` without showing the operator those `reasons` first: it removes the release anyway, and the jobs it names are suspended or returned to draft by the next validation pass.
  - A store that answers `packages/ledger-unreadable` refuses installs and removals. When its ledger is missing, `contextos-web packages inspect <vault> --rebuild-ledger` (or `--shared --rebuild-ledger`) rebuilds it from the releases present; when it is unreadable, tell the operator to restore a copy.
  - `contextos-web workflows install <vault> <package> --format json` and `contextos-web libraries install <vault> <library> --format json`: make a release of the vault's source in the vault's own package store, so run each only after the operator confirms it. The source is checked as validation checks a job's code and nothing is installed when a check fails; the refusal carries the `validation/` or `packages/` code. The store works out the version, starting at 1.0.0, and content that a current or future release already holds installs nothing, so installing unchanged source again is safe. A library the package names in `workflows.toml` without a `requirement` is read from `registry/libraries/<library>/` and installed first, and the release requires `^` the version it was tested on, which is the exact release the check ran against; a stated `requirement` uses the newest installed release that satisfies it. Read `release.version`, `release.outcome`, `standing` (whether the release is `current`, `previous`, or `future` for each workflow, normally `future` for a new one), `requirements`, and `libraries` from the result. `--version <v>` restores that exact release when it was removed, damaged, or incomplete, from source unchanged since it was installed. Run `workflows releases` afterwards to confirm what the new release is.
  - `contextos-web workflows releases <vault> <package> <workflow> --format json` and `contextos-web workflows releases --shared <package> <workflow> --format json`: read-only report of one workflow's releases, newest first. Each entry in `releases` has `version`, `kind` (`current`, `previous`, `future`, or `retired`), `summary` (the words to quote to the operator, such as `Current, installed 3 November 2026`), `installed_at`, `origin` (`source` or `bundle`), `condition` (`whole`, `removed`, `incomplete`, `damaged`, or `unverifiable`) with its `problems`, `retired`, `lock` (the library releases the release runs with, `null` until a job on it has passed validation), and `jobs` (how many job files name it, by lifecycle stage).
  - `contextos-web jobs successor <vault> <package> <workflow> <job> <new-job> [--to future|previous|<version>] --format json`, or `--all` for every `enabled` or `suspended` job on the current release: moves jobs to a new release by making successors, so run it only after the operator confirms. After installing a release, offer it for the jobs on the current release, and take up the `interface_changes` it reports as the [job](../job/update.md) skill describes.
- **The development loop.** Editing source changes nothing that is running: a job runs an installed release, and a workflow release is closed once installed. So, with the operator confirming each step that changes a store or a job: (1) edit the source in `registry/`; (2) prove it with `workflows run --source --dry-run`, or install it and prove the `future` release with `--release future`; (3) make successors for the jobs that should take it (`jobs successor`, or `--all` for every job on `current`), adjust each in `draft`, validate, and dry-run; (4) the operator enables each, which moves its predecessor's schedule to it, retires the predecessor, makes `future` the `current` release, and the old `current` the `previous`; (5) if it goes wrong, `jobs successor --all --to previous`, dry-run, and enable; (6) retention clears what no rule keeps, while run records and the ledger keep the history. A library fix reaches a workflow only through a new workflow release and successors, because installing a newer library release changes no job already validated. The job and library pages show the same releases (current, previous, future, or retired, with their jobs, locks, and which jobs need a successor), so point the operator to them as well as `workflows releases`.
- A live run (`workflows run` without `--dry-run`) makes real changes. Run one only when the operator explicitly asks for an ad hoc run, never as a substitute for a dry run.
- Never run `jobs schedule`, `suspend`, `resume`, `retire`, `reactivate`, or `delete`: those are the operator's acts.

---

## Available commands

| Command | Sub-skill | Purpose |
| --- | --- | --- |
| `list` | [list.md](list.md) | Summarise vault workflows, package sources, and installed packages |
| `create [description]` | [create.md](create.md) | Interview, V-sequence build, and dry-run proof of a new workflow or package |
| `update [slug]` | [update.md](update.md) | Review and revise workflows after ContextOS Web or their needs change |

---

## Routing

Take the command from the declared `command` argument, or from the operator's own words when the skill fired conversationally.

- No command, or `list`: load [list.md](list.md).
- `create`, optionally with a description: load [create.md](create.md), passing the description as the answer to its first question.
- `update`, optionally with a workflow slug or package name: load [update.md](update.md), scoped to that one if given.
- A request about a saved job, its schedule, or its state: hand over to the [job](../job/SKILL.md) skill.
- Anything else: ask one short clarifying question.

---

## Invariants

- Vault files are read and written only through ContextOS MCP.
- `list` is read-only. Only `create` and `update` write workflow files, and only after the operator confirms the design.
- Never invent content. An interview answer left open is recorded as open, not guessed.
- Never put a secret, credential, or token in a manifest, script, or scenario.
- A workflow is proved by a dry run that completes, never by inspection alone, and never by a live run in place of one.
- Never schedule, enable, or change the lifecycle state of a job.
