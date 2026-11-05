# Skill: app list

Summarises every app under `registry/apps/`, read from each app's `manifest.toml` and checked against ContextOS Web's discovery rules. Read-only: never writes, rescans, or edits anything.

---

## Step 1: discover

1. Call `mcp__contextos__fs_search_files` on `<vault>://registry/apps` with the pattern `*/manifest.toml`. If `registry/apps/` does not exist, say so, suggest `/vault update` to add it, and stop.
2. Read every manifest in one `mcp__contextos__fs_read_multiple_files` call.
3. For each manifest with an `entry`, check `<vault>://registry/apps/<folder>/<entry>` exists with `mcp__contextos__fs_get_file_info`.

---

## Step 2: check

Apply the router's [What ContextOS Web checks](SKILL.md#what-contextos-web-checks) rules to each manifest, and record each breach against its folder. Derive for each valid app:

- **Slug**: `slug`, else the folder name. Flag a slug that differs from the folder name, because the app will not open.
- **Opens**: in place, inside the ContextOS Web shell, for `js`; in a new tab for `spa`; and for `htmx`, listed but not served by the ContextOS Web versions this skill was written against.

If this session's shell can reach the operator's host (see the router's [The operator's host](SKILL.md#the-operators-host)), also fetch `http://<bind>/<vault>/apps/` and note which apps ContextOS Web lists now. Do not rescan: that changes the host's cache, and listing is read-only. If an app is not listed, the cache may be older than the manifest, or discovery refused it; say which you cannot tell apart without a rescan.

---

## Step 3: report

Present the valid apps as a table: **Name**, **Slug**, **Kind**, **Opens**, **Entry**, **MCP servers**, and, when the host was read, **Listed by host**. List each manifest that breaches a rule separately, with every breach, so a broken manifest is not mistaken for a working app. If there are no apps, say so and mention `/app create`.

Say what the report rests on: the manifests read through ContextOS MCP and, if it was read, the host's current apps list at the address used. Whether each `mcp_servers` name is configured, and whether an app renders and works, are not checked by listing.

---

## Invariants

- Read-only. Never writes, rescans, or edits anything.
- Report what the files and the host show; never guess a field that is missing.
