---
name: app
description: "Routes an operator command about ContextOS Web apps (`registry/apps/`) to its matching sub-skill: list (summarise the vault's apps from their manifest.toml, checked against ContextOS Web's discovery rules), create (guided interview and V-sequence build of a new app, verified on the operator's ContextOS Web host), update (review and revise apps after ContextOS Web or an app's needs change). Fires on explicit `/app COMMAND` invocations and on conversational requests to list, build, or refresh vault apps, e.g. 'what apps are registered', 'build me an app that does X', 'check the apps against the latest contextos-web'. Does not fire for workflows or jobs that run with no screen (owned by the sibling workflow and job skills), for `SLUG:role`, `SLUG:hat`, or `SLUG:agent` (owned by those skills), for `/vault COMMAND` or vault-content requests, or for a web page or tool that will not be registered under `registry/apps/` and served by ContextOS Web."
license: Apache-2.0
user-invocable: true
disable-model-invocation: false
argument-hint: "<list|create [description]|update [slug]>"
arguments: ["command"]
---

# App: Router Skill

Routes app commands to the sub-skill that carries them out. Load this file first, then load only the sub-skill the command needs.

An app is an interactive web tool in a vault's `registry/apps/<slug>/`, discovered and served by ContextOS Web at `/<vault>/apps/<slug>/`. Its JavaScript calls MCP tools through ContextOS Web's proxy. This skill scopes, builds, verifies, lists, and maintains apps; it does not run or configure the ContextOS Web server.

---

## Before any command

1. **ContextOS MCP.** This skill reads and writes the vault only through ContextOS MCP. Follow steps 1, 2, and 4 of the vault router's [Before any command](../vault/SKILL.md#before-any-command) section: confirm the server with `mcp__contextos__vault_info` and choose the vault. If the server is unavailable, report it and stop; never fall back to the host's own file tools for vault files. Paths below are within the chosen vault (`<vault>://...`).
2. **The V-sequence set.** `create` and `update` compose the shipped roles and hats. Check them as the workflow router's [Before any command](../workflow/SKILL.md#before-any-command) step 2 describes, and tell the operator to run `/vault update` if any is missing.

---

## What ContextOS Web checks

ContextOS Web registers an app only when its `manifest.toml` passes discovery. Every sub-skill checks the same rules:

- The keys are only `name`, `slug`, `kind`, `entry`, and `mcp_servers`; any other key rejects the manifest.
- `name` is present and not blank. `kind` is `js`, `spa`, or `htmx`. `entry` is present, relative to the app's folder, and the file exists.
- `slug`, when present, is lowercase letters, digits, and hyphens. Leave it out: ContextOS Web serves an app's files from the folder its slug names, so a slug that differs from the folder name is listed but does not open.
- Every `mcp_servers` name is a `[[mcp_server]]` configured in the host's `web.toml`. ContextOS MCP cannot read `web.toml`; the host's discovery checks it.
- `js` and `spa` apps are served. `htmx` apps are listed but reported as not yet supported by the ContextOS Web versions this skill was written against; check the operator's host rather than assuming either way.

A manifest that fails is left out of the apps list, and the reason goes to the ContextOS Web log. Discovery is cached per vault; `POST /<vault>/apps/rescan` (the Rescan control on the apps page) refreshes it.

---

## The operator's host

Verification that needs ContextOS Web itself (rescan, the apps list, serving an app, and its static assets) uses HTTP on the host's bind address: `[server] bind` in `web.toml`, by default `127.0.0.1:7332`, loopback only. Use it from this session's shell when the shell is on that host (for example `curl -s http://127.0.0.1:7332/<vault>/apps/`). If it cannot be reached, give the operator the exact request or page to open and ask what they see. Always say which host and address a check ran against, and never report a check as passed that was not run.

---

## Available commands

| Command | Sub-skill | Purpose |
| --- | --- | --- |
| `list` | [list.md](list.md) | Summarise the vault's apps and check their manifests |
| `create [description]` | [create.md](create.md) | Interview, V-sequence build, and host verification of a new app |
| `update [slug]` | [update.md](update.md) | Review and revise apps after ContextOS Web or their needs change |

---

## Routing

Take the command from the declared `command` argument, or from the operator's own words when the skill fired conversationally.

- No command, or `list`: load [list.md](list.md).
- `create`, optionally with a description: load [create.md](create.md), passing the description as the answer to its first question.
- `update`, optionally with a slug: load [update.md](update.md), scoped to that app if given.
- Work that runs with no screen and no person watching: hand over to the [workflow](../workflow/SKILL.md) skill.
- Anything else: ask one short clarifying question.

---

## Invariants

- Vault files are read and written only through ContextOS MCP.
- `list` is read-only. Only `create` and `update` write into `registry/apps/`, and only after the operator confirms.
- Never invent content. An interview answer left open is recorded as open.
- Never claim an app renders or works without a check that showed it, and always say what was checked, where, and what was not.
- Never put a secret, credential, or token in an app's files: they are vault content.
