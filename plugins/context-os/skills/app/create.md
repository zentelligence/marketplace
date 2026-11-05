# Skill: app create

Scopes, builds, and verifies one new app under `registry/apps/`, from a requirements interview to a manifest that ContextOS Web registers and an app the operator has seen working. A V-sequence leads the build: a role per stage, descending from purpose to design and build, then ascending through verification to acceptance. Within each stage, work through the definer, planner, solver, critic, refiner, and synthesiser hats as the stage needs.

---

## Step 1: interview

Ask each question in turn, in plain language, and wait for the answer. Introduce ContextOS terms only as labels for what the operator already said, and confirm them. "Not sure yet" is a valid answer: record it as open.

If the router passed a description, it answers Q1; continue from Q2.

**Q1 (purpose):** "What should this app let someone do? Walk me through it: what they see, what they click or type, and what changes because they used it." Store as `purpose_narrative`. It is the acceptance test in Step 8.

**Q2 (audience):** "Who will open it: just you, or others who use this vault?" Store as `audience`.

**Q3 (shape and placement):** "Picture it on screen. Is it a tool that belongs inside the ContextOS Web cockpit, rendering in place? Or a self-contained app with its own screens and navigation, opening in its own tab? Or does the server send back page fragments as you interact?" Map the answer to a kind and confirm it:

- `js`: renders in place inside the cockpit shell, with no router of its own.
- `spa`: its own client-side router and screens, opening in a new tab.
- `htmx`: server-returned fragments. Before building one, check the operator's host (Step 7's host checks, or the operator opening an existing `htmx` app): the ContextOS Web versions this skill was written against list an `htmx` app but do not serve it. If the host does not serve it, offer `js` or `spa` and let the operator choose.

Store the confirmed choice as `kind`.

**Q4 (tool access):** "Does it need to read or change anything in this vault, or talk to another connected tool or service? Name each." Store as `tool_access`, and resolve each to a `[[mcp_server]]` name in the host's `web.toml`. If the operator does not know the names, ask them to check `web.toml` or the ContextOS Web settings page, and keep it open until Step 7 confirms discovery accepts the manifest.

**Q5 (live updates):** "Does anything need to update on its own while it is open, without a refresh?" If yes, check what the host offers rather than assuming: ContextOS Web's documentation and its `/static/` assets for the operator's version. Polling a tool with `callTool` on an interval works on every version; any push channel must be confirmed on the operator's host before the design relies on it. Store the choice as `live_updates_strategy` (`none`, `poll`, or a confirmed host mechanism).

**Q6 (constraints):** "Anything this must never do, or must always do?" Store as `constraints_narrative`.

---

## Step 2: confirm before building

Summarise the interview in one short paragraph with the resolved `kind`, `mcp_servers`, and `live_updates_strategy`, and ask the operator to confirm. Nothing is written before this.

---

## Step 3: V1, strategist (why)

As `strategist:role`: state what the app is for in one sentence, test that an app is the right form (rather than a note, a query, or a workflow with no screen), check nothing in `registry/apps/` already does it (`/app list`), and settle the scope with the operator. If the vision drifts from what the operator said, go back to Step 1.

---

## Step 4: V2, analyst (what)

As `analyst:role`: turn the vision and answers into numbered requirements, each with how it will be checked: the functional behaviour from `purpose_narrative`, the `kind`, the `mcp_servers`, the live-update strategy, accessibility, and every constraint. Check every requirement traces to the interview and every answer has a requirement.

---

## Step 5: V3, architect (how)

As `architect:role`, design against what the operator's host actually provides. Where the host is reachable, read its shell page (`/<vault>/apps/`) and `/static/contextos-web.css` (with the files it imports) to see which scripts and classes exist, rather than relying on a remembered list. Produce and confirm with the operator:

- **Layout**: `registry/apps/<slug>/manifest.toml`, the entry file, and any assets, with the folder named as the slug.
- **The manifest**, in full: `name`, `kind`, `entry`, and `mcp_servers` (only the servers `tool_access` named). No `slug`, and no other key.
- **How it fits the shell**, which depends on `kind`:
  - `js`: the entry HTML is composed into the ContextOS Web shell page, which already loads the shell stylesheet, htmx, and `/static/contextos-web-client.js` (confirm on the host's page source). Author the entry as a content fragment, not a full page, and reuse real shell classes. Other assets are served unchanged.
  - `spa`: served as a standalone document in a new tab, never wrapped. It links `/static/contextos-web.css` itself if it wants the shell's look, and loads `/static/contextos-web-client.js` itself. An unmatched path under the app serves the entry document, so the app's router must handle it.
- **CSS**: the app shares the page with the shell (a `js` app always; a `spa` that links the shell stylesheet too). Prefix every class the app invents with its slug (`<slug>-summary`), never a bare common word.
- **Tool calls**: `window.contextosWeb.callTool(server, tool, args)` returns a Promise that resolves with the tool's unwrapped result and rejects with an `Error` carrying `code`, `remediation`, and `result` on a tool error, or `status` and `body` on a proxy failure. `await` it in `try`/`catch`; never unwrap the MCP envelope by hand. Pass `{ raw: true }` only when the full envelope is needed, and check `isError` yourself then. ContextOS Web's proxy accepts any server configured on the host, so the manifest's `mcp_servers` is the app's declaration and audit trail: the app must call only those servers.
- **Browser capabilities**: feature-detect any browser API beyond `fetch` and the DOM (for example `if ("EventSource" in window)`) and design a fallback, rather than assuming the operator's browser has it.
- **Live updates**: the confirmed `live_updates_strategy`, with its interval or mechanism.
- **No build step**: hand-authored HTML, CSS, and JavaScript, served as they are. No `package.json`, bundler, or Node tooling.

Check that a different engineer could build it unambiguously and that every requirement has a design decision.

---

## Step 6: V4, engineer (build)

As `engineer:role`, write exactly the confirmed design with `mcp__contextos__fs_write_file`. Before handing off, check:

- Every `callTool` names a server in `mcp_servers`, and nothing listed goes unused.
- Vault content and tool output reach the DOM only through `textContent` or an escaping helper, never raw `innerHTML`.
- A `js` entry is a fragment, not a duplicate page; every shell class used exists on the host; every invented class carries the slug prefix.
- Every control has discernible text and every input a label.
- No secret, credential, or token appears in any file.

---

## Step 7: V5, auditor (verify)

As `auditor:role`, verify in layers and record the result of each:

1. **Manifest, through ContextOS MCP.** Read `manifest.toml` back and check it against the router's [What ContextOS Web checks](SKILL.md#what-contextos-web-checks); confirm the entry exists with `mcp__contextos__fs_get_file_info`.
2. **Discovery and serving, on the host.** Using the router's [The operator's host](SKILL.md#the-operators-host): `POST /<vault>/apps/rescan` (it answers with a redirect to the apps page), then `GET /<vault>/apps/` and confirm the app is listed, then `GET /<vault>/apps/<slug>/` and confirm a `200` with the entry content for `js` and `spa`. An app missing from the list after a rescan failed discovery: an unknown key, an unconfigured server, a bad slug, or a missing entry; the reason is in the ContextOS Web log. For `htmx`, record what the host returns.
3. **Behaviour, in a browser.** Rendering, layout against the shell, and every `callTool` working against the real servers need a browser. If this session has a browser tool that can reach the host, use it; otherwise ask the operator to open `http://<bind>/<vault>/apps/<slug>/`, exercise each requirement, and tell you what they see. Wait for that confirmation.
4. Check every requirement from Step 4 one by one against the results.

Fix defects as `engineer:role` wearing `refiner:hat` and verify again.

---

## Step 8: V6, analyst (validate)

As `analyst:role`, check the app against `purpose_narrative` in the operator's own terms, using the evidence from Step 7, and get explicit sign-off. A gap goes back to the stage it traces to: a missed requirement to Step 4, a design gap to Step 5, a build defect to Step 6.

---

## Step 9: register and report

1. Leave `<vault>://registry/apps/index.md` alone: the ContextOS MCP server lists the new app folder in it, and `/app list` reads the manifests themselves.
2. Call `mcp__contextos__vault_log_append` with `entry: "app create | Created app: <slug>"` and `files` listing every file written.
3. Report precisely what was validated: the manifest checks (through ContextOS MCP), the discovery and serving checks (the host and address, and each response), and the behaviour checks (in which browser, by whom). Name anything not verified, and why.

---

## Invariants

- Never write before Step 2's confirmation, and never resolve an open answer by guessing.
- Never widen `mcp_servers` beyond what `tool_access` named.
- Never assume a host or browser capability or restriction that can be checked; check it, or say it was not checked.
- Never claim an app works without the Step 7 evidence.
- A failed critic check goes back to the stage that owns the gap.
