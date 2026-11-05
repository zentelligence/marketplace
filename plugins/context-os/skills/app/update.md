# Skill: app update

Reviews existing apps under `registry/apps/` and revises the ones that no longer fit: ContextOS Web changed (a manifest rule, a served kind, a shell class or script, the client library), a tool an app calls changed, or the operator's needs moved. A bounded review-and-revise cycle: it asks what changed and whether to act, not what each app is for.

---

## Step 1: what prompted this

Ask: "What prompted this review: a ContextOS Web upgrade, a change to a tool an app uses, an app that stopped working, a change in what an app should do, or a general health check?" Store as `change_narrative`.

Verify any claimed ContextOS Web change against the operator's host before acting on it (see the router's [The operator's host](SKILL.md#the-operators-host)): its version, its apps page, its `/static/` assets, or its release notes from the operator. Never act on a change you cannot confirm.

---

## Step 2: scope

If the router passed a slug, review that app; otherwise run [list.md](list.md) Steps 1 and 2 and review every app. Report manifests that already breach the discovery rules separately: they need fixing whatever prompted the review.

---

## Step 3: review

As `auditor:role` wearing `critic:hat`, check each app in scope against `change_narrative`, the router's [What ContextOS Web checks](SKILL.md#what-contextos-web-checks), and [create.md](create.md)'s Step 5 and Step 6 rules. Each finding names a concrete failure and how it was found. Typical findings:

- A manifest key or value discovery now refuses, or a `slug` that differs from the folder name.
- A shell class the app uses no longer exists in the host's stylesheet, or an invented class without the slug prefix.
- A `callTool` whose arguments or result handling no longer match the tool's current schema, or a call to a server not in `mcp_servers`.
- An `htmx` app on a host that now serves `htmx`, which needs only a rescan and a check, or an app that would now fit another kind better.
- A polling design the host now offers a confirmed alternative to.
- Vault content or tool output written to the DOM without escaping.

Present the findings per app and let the operator choose which to act on.

---

## Step 4: revise

For each confirmed finding, as `engineer:role` wearing `refiner:hat`, apply the fix with `mcp__contextos__fs_edit_file`, following [create.md](create.md)'s Step 5 and Step 6 rules.

---

## Step 5: re-verify

For each app changed, run [create.md](create.md) Step 7's layers again: the manifest through ContextOS MCP, discovery and serving on the host after a rescan, and behaviour in a browser. A fix that introduces a new problem is a new finding: return to Step 4.

---

## Step 6: log and report

Call `mcp__contextos__vault_log_append` once with `entry: "app update | Reviewed N apps, revised M | prompted by: <short change_narrative>"` and `files` listing every file changed. Report each revision and exactly how it was verified: what was checked through ContextOS MCP, on which host and address, and in which browser by whom, and what was not verified. List any broken manifest still unresolved.

---

## Invariants

- Never act on a ContextOS Web change you cannot confirm, and never revise without the operator confirming the finding.
- Never fix a broken manifest by guessing what was meant; report it and ask.
- The build rules of [create.md](create.md) apply to every revision.
