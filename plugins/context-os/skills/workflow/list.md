# Skill: workflow list

Summarises the vault's workflows, the bundles being prepared beside them, and the shared packages installed on the host. Read-only: never writes, validates, or runs anything.

---

## Step 1: find the vault's workflows

1. Call `mcp__contextos__fs_search_files` on `<vault>://registry/workflows` with the pattern `*/workflows.toml`. If `registry/workflows/` does not exist, say so, suggest `/vault update` to add it, and go to Step 4.
2. Read every `workflows.toml` found, and the `<package>/<workflow>/workflow.toml` of every workflow each lists, in one `mcp__contextos__fs_read_multiple_files` call.
3. Call `mcp__contextos__fs_search_files` on the same folder with `*/*/jobs/*.toml` and with `*/*/tests/*.toml`, to count each workflow's jobs and dry-run scenarios.
4. For each workflow, check its `entry` file exists with `mcp__contextos__fs_get_file_info` on `<vault>://registry/workflows/<package>/<workflow>/<entry>`.

A folder under `registry/workflows/` with no `workflows.toml` is not a package; mention it only if it holds other files. A `workflow.toml` in a folder its package's `workflows.toml` does not list is not registered; report it.

---

## Step 2: check each file

Apply the rules ContextOS Web's discovery applies, and record each breach against the package or workflow:

- `workflows.toml` has only `workflows` (the names of the package's workflows, each lowercase letters, digits, and hyphens, none twice), `modules`, `templates`, and `libraries`. A listed workflow without a `<workflow>/workflow.toml` is a missing artefact.
- `workflow.toml` has only `name`, `entry`, `timeout_secs`, `entity`, `mcp_servers`, `mcp_tools`, `input`, `output`, `required_tool_contracts`, and `log_level`. `entity`, when present, is `vault` or a slug in `.contextos/entities.toml`; its jobs belong to it unless they declare their own, and a `timeout_secs` here applies only to one-off runs, since every job states its own. Any other key makes the file invalid.
- `name` and `entry` are present, and `name` is not blank. `mcp_servers` is a table with `allow` and `deny` lists, and `mcp_tools` holds `allow` and `deny` lists of `{ server, tool }`. A server on both server lists, a pair on both tool lists, or a tool allow on a denied server contradicts itself.
- The entry file exists, and so does every module and template `workflows.toml` declares.
- No `[[input]]` has `kind = "vault"`, at any depth: a workflow run from the vault has its own vault as its scope.
- `log_level`, when present, is `debug`, `info`, `warn`, or `error`.

Whether each server an `allow` list names is configured in the host's `web.toml` cannot be read through ContextOS MCP. Say so, and point to `/job` validation or a dry run, which check it.

---

## Step 3: package folders ready to bundle

A package folder that also holds a `manifest.toml` is being prepared as a shared bundle. Read it with `mcp__contextos__fs_attach_file`: it describes the release only (`name`, `version`, `digest`, and `[[files]]`). Note its name and version, and whether that version is installed (Step 4).

---

## Step 4: installed packages

If the [contextos-web command line](SKILL.md#the-contextos-web-command-line) is available, run `contextos-web packages list --shared` and report each package name and installed version. Otherwise say the host's package store was not read, and give the command.

---

## Step 5: report

Present the vault's workflows as a table: **Package**, **Name**, **Workflow**, **Entry**, **MCP servers**, **Inputs** (name and kind, marking optional ones), **Jobs**, **Scenarios**. Flag a workflow with no scenario: none of its jobs can be registered until it has one.

List any workflow that breaches Step 2 separately, with each breach, so a broken file is not mistaken for a working one.

Then list the bundles being prepared from Step 3, with whether each version is installed, and the installed packages from Step 4. Whether a source's files still match its recorded `digest` is not checked by listing; only rebuilding the digest shows it.

If there are no workflows and no installed packages, say so and mention `/workflow create`.

State what this listing checked (the files' shape, read through ContextOS MCP) and what it did not (that servers are configured, that scripts compile, or that any job is registered). For a job's lifecycle state, point to `/job list`.

---

## Invariants

- Read-only. Never writes, edits, validates, or runs anything.
- Report what the files say; never guess a field that is missing.
