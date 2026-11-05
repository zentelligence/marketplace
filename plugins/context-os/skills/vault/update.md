# Skill: vault update

---

## Purpose

Bring an existing vault back in step with the installed context-os plugin after an upgrade. Installs the plugin's release of the vault package, adds anything the vault is missing, refreshes plugin-shipped files the operator has not customised (templates, the task and decision registers' Bases, `memory/designs/`, `memory/operating/`'s shipped files, the V-sequence roles and hats, `registry/scripts/utility/`), and offers the migrations earlier plugin versions left behind. Files the operator has edited are never silently overwritten; they are reported for review instead. Missing folders are created; the package writes no `index.md`, because the server creates and maintains every folder's.

Not a first-run skill. `/vault init` scaffolds and personalises a fresh vault; `/vault update` maintains an already-personalised one across plugin upgrades.

The work runs as the vault package's `update` workflow, as a saved shared job; [package.md](package.md) covers installing, registering, and running it. Run its Steps 1 to 3 before Step 2 below. The plugin's new release is installed in its Step 2, which is how this command also brings the host's copy of the vault package up to date.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| `.contextos/state.json` | Vault (created on the first applied run if absent) | No |
| The package's shipped and seeded templates, `workflows/vault/templates/` | Installed plugin, through the installed release | Yes |

---

## Outputs

The run's `outputs.plan`:

| Field | Notes |
| --- | --- |
| `folders_added` | Folders the vault is missing, created empty for the server to index. |
| `files_added` | Files the vault is missing. Never overwrites an existing file. |
| `files_refreshed` | Shipped files unchanged by the operator since the last sync whose shipped copy has since changed. |
| `conflicts` | Shipped files changed both by the operator and in the plugin; listed, not touched. |
| `resolved` | Conflicts resolved as the operator chose. |
| `migrations_pending`, `migrations_applied` | Material from earlier plugin versions, each applied only when the operator approves it. |
| `team_conflicts` | Why `.contextos/team.toml` cannot be used by the vault's jobs, from the server's `doctor` check. |
| `errors` | Anything that could not be done. |
| `applied` | Whether the run changed the vault. |

An applied run also records in `.contextos/state.json` the vault package's version, the time, each shipped file's shipped ancestor and shipping plugin, and a receipt per applied migration.

---

## Flow

### Step 1: protective gate

This process performs bulk mutations of directories and files in a vault. Using `AskUserQuestion`, ask the operator to confirm two things before continuing: that they have a recent backup, and that they want to proceed. Stop if either is declined.

If they do not have a backup, some vaults may have a backup script in `registry/scripts/utility/` (or, in a vault not yet updated, `scripts/utility/`), such as `backup-obsidian-vault.ps1` (Windows) or `backup-obsidian-vault-macos.sh` (macOS). Simple backup options are duplicating (copy-paste) or compressing (right-click, compress) the vault folder. Re-ask once they confirm it is done, or to proceed without one. 

### Step 2: preview

Run the `update` job as a plan, which writes nothing (see [package.md](package.md), Step 4):

```bash
contextos-web jobs run --shared contextos-vault update update --format json --input vault=<vault> --input 'updated_at="<now>"'
```

If the vault has no `.contextos/state.json` yet, no shipped file has a known ancestor: each one that matches the plugin's copy is baselined on the first applied run, and each one that differs is reported as a conflict for the operator to resolve, never overwritten.

### Step 3: confirm

Summarise `outputs.plan` for the operator: files that would be added, files that would be refreshed (safe, being unmodified since the last sync), any `conflicts` (files the operator has changed where the plugin's copy differs too), and the `migrations_pending` backlog (each with its `description` and proposed `action`). Report each `team_conflicts` item too: the server's `doctor` says why `.contextos/team.toml` cannot be used by the vault's jobs, and ContextOS Web pauses the vault's scheduled jobs while it stays that way. Which member is the chief of staff is the operator's decision, so show the item and the file and let the operator correct it; never edit `team.toml` to repair it. Ask before applying if there is anything to refresh or any conflict to review; adding brand-new files needs no confirmation, since it is purely additive and identical in risk to `/vault init`'s scaffold step.

### Step 4: resolve conflicts

A conflict is reported on every run until it is resolved, so settle each one now or tell the operator it will reappear. For each conflicting file, tell the operator its path and that both they and the plugin have changed it. Offer a diff: `mcp__contextos__git_diff` if the vault is a Git repository, otherwise read the vault's copy through MCP and show the plugin's copy from `workflows/vault/templates/shipped/<path>` in the plugin. Then ask which they want:

- **Keep mine (`keep-mine`):** the vault's copy stays, and the plugin's current copy is recorded as reviewed, so the file is left alone until the plugin changes it again.
- **Take the plugin's (`take-plugin`):** the vault's copy is replaced with the plugin's.
- **Merge by hand:** edit the vault's copy through MCP to combine both, then resolve it as `keep-mine`.

The choices are applied with everything else in Step 6.

### Step 5: choose migrations

For each item in `migrations_pending`, explain its `description` and proposed `action`, and ask whether to apply it. An item with no `action` is reported only; say what handles it (`team`: run `/vault init`, which resumes without touching anything already captured and asks only for the members' names). `registry-scripts` moves the top-level `scripts/` folder into `registry/scripts/`; if its receipt lists files left in `scripts/`, show them to the operator to merge by hand.

### Step 6: apply

Run the `update` job once more, applying everything at once: the additions and refreshes, each conflict choice, and each approved migration.

```bash
contextos-web jobs run --shared contextos-vault update update --format json --input vault=<vault> --input 'updated_at="<now>"' --input apply=true \
  --input 'resolve=[{"path":"<path>","choice":"keep-mine"}]' --input 'migrate=["<id>","<id>"]'
```

Leave out `resolve` or `migrate` when there is nothing to give it. Report `outputs.plan` again: what was added, refreshed, and resolved, `migrations_applied`, and any `errors`. Each applied migration leaves a receipt in `.contextos/state.json`; report its changes and include them in the log entry below. After `vault-instructions`, point out `CLAUDE.legacy.md`: any customisations in the old instructions are to be merged into `AGENTS.md` by hand, and the legacy file deleted once done. After `orientation`, tell the operator its profile sections are marked not yet captured, and offer `/vault init`, which fills each one from the vault's identity, operating, and voice files without asking again for what they hold. Every write went through ContextOS MCP, so the indexes, the operation log, Git, and the hosts' orientation block are already current.

### Step 7: releases and jobs

Vault workflow and library source (`registry/workflows/<package>/`, `registry/libraries/<library>/`) is written by Step 6 as any shipped file is, so the operator's edits are never overwritten and a changed file in both places is a conflict. Written source runs nothing and changes no job. Skip this step when the run added, refreshed, or resolved none.

1. For each workflow or library whose source was added, refreshed, or resolved, tell the operator its source changed, and ask before installing it into the vault's package store: `contextos-web workflows install <vault> <package> --format json` or `contextos-web libraries install <vault> <library> --format json`. Source unchanged since its last install installs nothing and reports so. Read `release.version` and `standing` from the result. Never run either command without that confirmation.
2. A host workflow arrives as a bundle, installed with `contextos-web packages install --shared <bundle.tar.gz>` (the vault package itself is installed by [package.md](package.md) Step 2). Install a bundle only on the same confirmation.
3. An update never moves an existing job, and never installs, enables, or retires anything on its own. Run `contextos-web workflows releases <vault> <package> <workflow> --format json` (or `--shared`) for each workflow whose release you installed or that has a release newer than its jobs, and report per workflow: the new `future` release (its `version` and `summary`), and the jobs that could move (those `enabled` or `suspended` on the `current` release, from `jobs`).
4. Tell the operator how to move them. For one job, `contextos-web jobs successor <vault> <package> <workflow> <job> <new-job>`; for every job on `current`, `contextos-web jobs successor <vault> <package> <workflow> --all`. Each successor is a `draft` that is then validated, dry-run, and scheduled, which retires its predecessor and moves `future` to `current` and the old `current` to `previous`; the [job](../job/SKILL.md) skill carries that through. Offer to make the successors; run `jobs successor` only when the operator asks.

### Step 8: log

Call `mcp__contextos__vault_log_append` with `entry: "update | synced to plugin v<version> | <n> added, <n> updated, <n> conflicts, <n> resolved, migrations: <ids>"` and `files` set to the added, updated, resolved, and migrated paths.

---

## Invariants

- Never overwrite a file the operator has edited while the plugin's copy also differs. It stays a conflict, reported on every run, until the operator resolves it.
- Never record the operator's content as the shipped ancestor of a file.
- Never apply a migration the operator has not approved.
- Never install a release, make a successor, or move a job without the operator asking. An update reports the new `future` release and the jobs that could move, and stops there.
- Never touch content outside the plugin's shipped, replaceable set: identity, entities, priorities, registry content the operator authored themselves, folder `index.md` files, `AGENTS.md`, `CLAUDE.md`, and `registry/instructions/global.md` are operator-owned and are never part of this skill's refresh pass.
- Never reproduce the workflow's work with the MCP tools or the host's own file tools if the command line cannot run; report and stop.
- `.contextos/` holds plugin bookkeeping only. Never store vault content there, and never treat it as citable vault knowledge.
