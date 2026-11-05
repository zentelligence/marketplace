# Skill: workflow update

Reviews existing workflows and revises the ones that no longer fit: ContextOS Web changed (a manifest key, a host function, a tool's contract), a server or tool a workflow calls changed, or the operator's needs moved. A bounded review-and-revise cycle, not a full rebuild: it asks what changed and whether to act, not what the workflow is for.

---

## Step 1: what prompted this

Ask: "What prompted this review: a ContextOS Web upgrade, a change to a tool or server a workflow uses, a failing job, a change in what a workflow should do, or a general health check?" Store as `change_narrative`.

A change to a workflow's declared outputs (`[[output]]` or `outputs`) is a contract change for whoever reads the run summary's `outputs`, so name it when you review the workflow.

Verify any claimed ContextOS Web change before acting on it: run `contextos-web --version` and the relevant command's `--help` (for example `contextos-web workflows run --help`) through the [contextos-web command line](SKILL.md#the-contextos-web-command-line), or ask the operator for the release notes. Never act on a change you cannot confirm.

---

## Step 2: scope

If the router passed a workflow slug or package name, review that one. Otherwise run [list.md](list.md) Steps 1 to 4 and review every workflow, package source, and installed package. Report manifests that already breach the discovery rules separately: they need fixing whatever prompted the review.

For a failing job, read its recent run records with `mcp__contextos__fs_search_files` on `<vault>://memory/jobs/<package>/<workflow>/<job>` (pattern `**/R-*.md`) and `mcp__contextos__frontmatter_read` on the newest, and use each record's `status`, `error`, and call table as evidence.

---

## Step 3: review

As `auditor:role` wearing `critic:hat`, check each workflow in scope against `change_narrative` and against [create.md](create.md)'s reference sections (manifest, script interface, scenarios, and package format). Each finding names a concrete failure. Typical findings:

- A manifest key ContextOS Web no longer accepts, or a new one the change requires.
- A `call_mcp` whose arguments or result handling no longer match the tool's current schema; read the schema from the server, not from memory.
- A server or tool in `[mcp_servers]` or `[mcp_tools]` the script no longer calls, or a call those lists do not permit.
- A scenario that no longer reflects the calls the script makes or the results the tools now return.
- A recoverable failure left uncaught, or a catch that hides a failure that should fail the run.
- Messages at `info` and above that carry vault content.

Present the findings per workflow and let the operator choose which to act on.

---

## Step 4: revise

For each confirmed finding, as `engineer:role` wearing `refiner:hat`, apply the fix following [create.md](create.md)'s Step 6 rules. Files of a package in the vault change through `mcp__contextos__fs_edit_file`. A shared package is never edited in place in the store: change its source in `<vault>://registry/workflows/<package>/`, raise its `version` (a fix is a patch release, a new input or effect a minor one, a removed input or effect a major one), and rebuild its digest and bundle as [create.md](create.md)'s [Digest, bundle, and install](create.md#digest-bundle-and-install) describes.

Tell the operator plainly: a job runs the exact release its `version` names and never the newest, so a change to a package's source changes no job until a new release is installed (`contextos-web workflows install` for a vault package, a new bundle for a shared one) and the job's `version` is moved to that release with `/job update`. Moving it is a new version of the job: a `draft`, `validated`, or `registered` job returns to `draft` and must be validated and dry-run again, and an `enabled` job keeps its schedule while ContextOS Web validates the new version, and is suspended if that validation, or the first live run of the new version, fails. A job left on the older release is unaffected.

---

## Step 5: re-verify

As `auditor:role`, run every scenario of each changed workflow again as [create.md](create.md) Step 7 describes (installing a new package release first, with the operator's confirmation). A fix that introduces a new problem is a new finding: return to Step 4. Then offer `/job update` for the affected jobs, which revalidates and dry-runs them.

---

## Step 6: log and report

Call `mcp__contextos__vault_log_append` once with `entry: "workflow update | Reviewed N, revised M | prompted by: <short change_narrative>"` and `files` listing every vault file changed. Report each revision, the commands that verified it and their results, what was not verified, the jobs whose versions changed, and any finding left open.

---

## Invariants

- Never act on a ContextOS Web change you cannot confirm, and never revise without the operator confirming the finding.
- Never fix a broken manifest by guessing what was meant; report it and ask.
- Never change a job's lifecycle state; revalidation belongs to `/job update`, and enabling to the operator.
