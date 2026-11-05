# Vault package: install, register, and run

`/vault init`, `/vault update`, and `/vault health` do their deterministic work through the vault package, `contextos-vault`, which this plugin ships as plain files in `workflows/vault/` (the plugin root is two levels above this file). Its `scaffold` workflow creates every file a vault needs that it does not yet have, and the team; its `update` workflow brings an existing vault back in step with the plugin; its `health` workflow checks the knowledge quality of the wiki and insight notes, reading only. They run as saved shared jobs under ContextOS Web's command line, `contextos-web`, with no tokens spent on the work itself.

This is the one sanctioned case of a session running ContextOS Web: the skill must know when the step has finished, and whether it succeeded, before it carries on. Never run any other `contextos-web` command from these skills on your own account: the one exception is `/vault update`'s [releases and jobs](update.md#step-7-releases-and-jobs) step, which runs `workflows install`, `libraries install`, `packages install`, and `workflows releases` only as the operator confirms them. Never start or stop its server, and never reproduce a workflow's work with the ContextOS MCP tools or the host's own file tools if the command cannot run.

Run each step below in order, every time, before the first run in a session. Every step is safe to repeat.

---

## Step 1: find the command line

Run `contextos-web --version`. If the command is not found, tell the operator that ContextOS Web is required for this step and is not installed or not on the `PATH`, and stop.

Every command below uses the operator's default `web.toml` (`contextos-web config` writes it). Its first `[[mcp_server]]` must be the ContextOS MCP server, named `contextos`, configured with the vault being worked on. If a command reports `workflow/config-invalid`, `validation/server-not-configured`, or `workflow/vault-unavailable`, tell the operator what it says and stop: the fix is in their configuration, not here.

## Step 2: install the plugin's release

1. Read the package's version from the `version` line of `<plugin root>/workflows/vault/manifest.toml`.
2. Run `contextos-web packages list --shared`. If it has a line `contextos-vault <version>` for that version, the release is installed; go to Step 3.
3. Otherwise run `contextos-web packages install --shared "<plugin root>/workflows/vault"`. It reads the folder, checks every file against the manifest's digest, and copies the release into the host's package store; it never changes the folder. Older releases stay only while a job or lock keeps them, and the install reports any it removed. Report `Installed contextos-vault <version>.`. A refusal (a digest mismatch, a link in the folder) means the plugin's files are damaged: tell the operator to reinstall the plugin, and stop.

## Step 3: register the jobs

Run `contextos-web jobs list --shared --format json` and find the jobs whose `package` is `contextos-vault` with `job` equal to `workflow`: `scaffold`, `update`, and `health`. Each names the exact release it runs in its `version`, never the newest installed, so `<version>` below is the plugin's release from Step 2. For the one the command about to run needs:

1. **Missing:** create it, passing the TOML on standard input, with `<vault>` the chosen vault's name, `<now>` the current local time as an RFC 3339 date-time with its offset (for example `2026-10-22T09:30:00+11:00`), and `<today>` the current local date (for example `2026-10-22`):
   ```bash
   contextos-web jobs create --shared --file - contextos-vault <workflow> <workflow> --format json
   ```
   ```toml
   name = "Vault <workflow>"
   version = "<version>"  # the exact release this job runs
   timeout_secs = 600
   ready = true

   [inputs]
   vault = "<vault>"
   created_at = "<now>"   # for scaffold; for update the key is updated_at; for health it is today = "<today>"
   ```
   **Present:** read it with `contextos-web jobs show --shared contextos-vault <workflow> <workflow> --format json` for its `content` and `hash`. If its `version` line names another release (the plugin was upgraded since the job was made), set it to `<version>`, changing nothing else, and apply it with `contextos-web jobs replace --shared --file - --expected-hash <hash> contextos-vault <workflow> <workflow> --format json`, piping the new TOML. The changed file returns the job to `draft`; carry on with item 3.
2. **`state` is `registered` or `enabled`:** go to Step 4.
3. **`state` is `draft` or `validated`** (a job just created, or just moved to the plugin's release): run `contextos-web jobs validate --shared contextos-vault <workflow> <workflow>`, then `contextos-web jobs dry-run --shared contextos-vault <workflow> <workflow> --scenario current --format json`. The dry run replays the package's `current` scenario, writes nothing, and registers the job when its `registration.registered` is true. When it is false with the reason `version_changed`, the job was validated for another release than the dry run ran, such as one installed between the two commands: run both commands once more. Report any other reason and stop. If validation fails because the job's own `vault` no longer exists, replace the job file with the chosen vault: `contextos-web jobs show --shared contextos-vault <workflow> <workflow> --format json` for its `hash`, then `jobs replace --shared --file - --expected-hash <hash> ...` with the same TOML. Report any other failure's `code` and `message`, and stop.
4. **`suspended` or `retired`:** tell the operator its state and stop; resuming or reactivating it is their decision, through ContextOS Web.

## Step 4: run

```bash
contextos-web jobs run --shared contextos-vault <workflow> <workflow> --format json --input vault=<vault> --input 'created_at="<now>"' [--input name=<value> ...]
```

Pass `<now>` afresh on every run (`updated_at` for update, and `today` as `<today>` for health). A `string` or `vault` input is plain text; every other kind is JSON, so a date-time is a quoted JSON string, and arrays and objects are JSON too (in PowerShell, wrap each `--input` argument in single quotes as shown). The overrides never change the saved job.

The command prints one JSON summary and returns only when the run has ended. Read it, never the log:

| `outcome` (exit status) | What it means | What to do |
| --- | --- | --- |
| `succeeded` (0) | The workflow finished | Read `outputs` |
| `degraded` (0) | It finished, with warnings | Read `outputs` and report `warnings` |
| `failed` (1) | It stopped part way | Report `code` and `message`. Every workflow is safe to run again: scaffold never replaces a file, update records each file as it goes, and health only reads |
| `refused` (3) | The script never started; nothing changed | Report `code` and `message`. `workflow/job-not-runnable` or `workflow/package-unavailable`: repeat Steps 2 and 3 once, then run again |
| (75) | Another run of the same job is in progress | Wait for it, then run again; never run both |
| (124) | It timed out | Run again: it carries on where the last run stopped |
| (130) | It was cancelled | Tell the operator; calls already made were not undone |

Every write goes through ContextOS MCP, so the server keeps the indexes, the operation log, and Git current; there is nothing to rebuild or commit afterwards. The run is recorded in ContextOS Web's run history (`run.record` in the summary), where the operator can see it later.
