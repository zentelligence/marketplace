---
name: app
description: "Scaffolds a new contextos-web app under `registry/apps/<slug>/` in the vault registry: a conformant `manifest.toml` (schema per `specification/web-apps.md`) and an entry-file stub. Fires only on the explicit command `/app create <slug>` (optionally `--kind spa|htmx`). Does not fire on inline persona-style triggers (no `<slug>:app`, unlike `:role`/`:hat`/`:agent`): an app is served content, not a cognitive posture to adopt in-session. Does not fire for `/role`, `/hat`, `/agent`, `/prompt`, or `/vault` commands (owned by the sibling skills), and does not itself register the app with a running `contextos-web` process (discovery happens on that server's own next request for the vault, or via its `/apps/` page's rescan control)."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "create <slug> [--kind spa|htmx]"
arguments: ["command"]
---

# Skill: app

Scaffolds a `contextos-web` app: a `registry/apps/<slug>/manifest.toml` and its entry-file stub. Activated via `/app create <slug>` (or `/app create <slug> --kind htmx`). There is no activation flow (unlike `role`/`hat`/`agent`): an app is not adopted in-session, it is served by `contextos-web` once registered.

---

## Background: what this scaffolds

`contextos-web` (the `context-os-mcp` repository's browser-facing crate) discovers apps under `registry/apps/<slug>/` in each configured vault and serves them at `GET /<vault-name>/apps/<slug>/...`. Discovery reads only `manifest.toml`; every other file in the app's own directory (a `readme.md`, source files, the built bundle) is either served content or ignored. Full route and validation behaviour: `specification/web-routes.md` §4 and `specification/web-apps.md`.

Two app kinds exist:

- **`spa`** — fully served in v1. A static single-page-app bundle, opened in a new tab (`target = "_blank"`). An unmatched sub-path under the app's own route falls back to the bundle's own entry file, so the SPA's client-side router still works.
- **`htmx`** — accepted by the schema and listed on the vault's `/apps/` page, but not yet servable (`contextos-web` returns a distinct "not yet supported" response for it). Scaffold one now to reserve the slug and shape; it becomes servable once stage 2 lands.

---

## MCP awareness

If a ContextOS MCP server is configured for this vault, prefer its tools over the harness's raw `Write`/`Edit`, falling back automatically if MCP is unavailable. Check once per invocation: attempt `mcp__contextos__vault_info`; if it succeeds, prefer the named MCP tools per step below, falling back to `Write`/`Edit` only if a specific call errors. If `vault_info` is unavailable or errors, use `Write`/`Edit` throughout.

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| App slug | `/app create <slug>` | Yes |
| Kind | `--kind spa\|htmx` flag, or interview | No (default `spa`) |
| `registry/apps/<slug>/manifest.toml` | Vault registry | Existence check before overwrite |
| `web.toml`'s configured `[[mcp_server]]` names | Operator (this skill has no live connection to a running `contextos-web` instance) | Only if the app names `mcp_servers` |

---

## Outputs

| Output | Notes |
| --- | --- |
| `registry/apps/<slug>/manifest.toml` | The app's machine-readable manifest |
| `registry/apps/<slug>/<entry>` | A minimal entry-file stub (only written if it does not already exist) |
| Confirmation report | Names the manifest path and how the app becomes visible |

---

## Flow

### Step 1: extract slug and kind

Normalise the slug to lowercase-hyphenated form (`[a-z0-9-]+`), matching the vault's existing file-naming convention and `manifest.toml`'s own `slug` field validity rule. Reject and ask again if the operator supplies a slug outside that character class rather than silently rewriting it beyond simple case-folding and space-to-hyphen conversion.

Read `--kind` if given; default `spa`.

### Step 2: existence check

Check whether `registry/apps/<slug>/manifest.toml` already exists (`mcp__contextos__fs_get_file_info` if MCP is available, otherwise a direct file read attempt). If it exists, confirm with the operator before overwriting.

### Step 3: interview

Ask sequentially (wait for each answer), skipping a question the operator already answered via a flag:

- `"Display name: what should this app be called on the vault's apps page? (e.g. 'Task Register Dashboard')"`
- `"Entry file: what is the app's own entry file, relative to its own directory? (default: index.html)"`
- `"Target: '_blank' (opens in a new tab) or 'embed' (stage-2 inline composition)? (default: _blank for spa, embed for htmx)"`
- `"MCP servers: which configured '[[mcp_server]]' names (from this vault's web.toml) will this app call, if any? List names separated by commas, or leave blank for a purely static app."`

Do not invent a value for any of these; an unanswered optional question keeps its stated default.

### Step 4: write the manifest

Write `registry/apps/<slug>/manifest.toml` (creating the directory) with the schema below, substituting the interview answers. Field order and comments are cosmetic; the required shape is documented in full under "Manifest schema" below.

If MCP is available, prefer `mcp__contextos__fs_write_file`; otherwise use the `Write` tool directly.

### Step 5: write the entry-file stub

If `registry/apps/<slug>/<entry>` does not already exist, write a minimal stub:

- **`spa`**: the "SPA entry stub" template below, which demonstrates calling an MCP tool via the JS client.
- **`htmx`**: a bare `<div>` placeholder noting that stage-2 composition is not yet implemented; do not fabricate SSE-subscription markup that has no server-side counterpart yet.

### Step 6: confirm

Report to the operator:

> "App `<slug>` scaffolded at `registry/apps/<slug>/manifest.toml`. It becomes visible on `contextos-web`'s `GET /<vault-name>/apps/` page the next time that server discovers this vault's `registry/apps/` (its first request for this vault since startup, or the refresh control on that page for an already-running server). No `contextos-web` restart or code change is required."

If the manifest names any `mcp_servers`, add:

> "Confirm each of `<names>` is present as a `[[mcp_server]]` entry in this vault's own `contextos-web` instance's `web.toml` — this skill cannot verify that against a running server, and a name absent there will fail registration with a diagnostic naming the missing server."

---

## Manifest schema

Full authority: `specification/web-apps.md` §2. Summarised here for the interview substitution in Step 4.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | Display name shown on the vault's apps page |
| `slug` | string | no | Defaults to the containing directory's name; must be `[a-z0-9-]+` if given explicitly |
| `kind` | `"spa"` \| `"htmx"` | yes | `"htmx"` is schema-valid but not yet servable |
| `entry` | string | yes | Relative path within this app's own directory; must exist at registration time or the whole app fails to register |
| `target` | `"_blank"` \| `"embed"` | yes | `"_blank"` for a `spa` app opened in a new tab; `"embed"` names the intended `htmx` composition mode |
| `mcp_servers` | string[] | no (default empty) | Every entry must match a `[[mcp_server]]` name in the vault's `contextos-web` `web.toml`; empty is valid (a purely static app) |

An unrecognised key, an invalid `kind`/`target` value, or an `mcp_servers` entry the running server does not recognise all fail that one app's registration with a diagnostic naming the app and the violation, without affecting any other app's registration.

### Worked example: `kind = "spa"`

```toml
name    = "Task Register Dashboard"
slug    = "task-register"
kind    = "spa"
entry   = "index.html"
target  = "_blank"

mcp_servers = ["contextos"]
```

### Worked example: `kind = "htmx"` (schema-valid, not yet servable)

```toml
name    = "Live Task Widget"
slug    = "live-task-widget"
kind    = "htmx"
entry   = "widget.html"
target  = "embed"

mcp_servers = ["contextos"]
```

---

## SPA entry stub (fallback)

Used for a `kind = "spa"` app when `<entry>` does not already exist. Demonstrates the deterministic, non-model-mediated MCP call surface (`callTool`) every registered app has available with no LLM step involved — the same tool contract a direct API consumer or `contextos-mcp` client would use.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title><Display Name></title>
</head>
<body>
<h1><Display Name></h1>
<pre id="output">Loading…</pre>
<script src="/static/contextos-web-client.js"></script>
<script>
  // Replace "contextos" and "vault_info" with the server/tool this app
  // actually needs; see this manifest's own `mcp_servers` allow-list.
  window.contextosWeb
    .callTool("contextos", "vault_info", {})
    .then((result) => {
      document.getElementById("output").textContent = JSON.stringify(result, null, 2);
    })
    .catch((error) => {
      document.getElementById("output").textContent = "Error: " + error.message;
    });
</script>
</body>
</html>
```

---

## Discovering available MCP server names

There is no live "list configured servers" endpoint this skill can call. `mcp_servers` names come from the vault operator's own `contextos-web` `web.toml` (`web-architecture.md` §2, `[[mcp_server]]` entries), which this skill has no filesystem access to (it lives outside the vault, alongside the `contextos-web` binary). Ask the operator directly, or point them at their own `web.toml`, rather than guessing a name.

---

## Invariants

- Activate only on the explicit `/app create <slug>` command. Never infer app creation from task phrasing.
- Never invent a `manifest.toml` field value the operator did not supply and this document does not default; leave the interview's stated defaults in place instead.
- Writes only `registry/apps/<slug>/manifest.toml` and, when absent, its own entry-file stub. No other files, and never a `contextos-web` configuration file (`web.toml` is outside the vault and outside this skill's writable scope).
- This skill scaffolds the manifest; it does not itself register the app with any running `contextos-web` process. Say so plainly in the confirmation (Step 6) rather than implying immediate availability.
