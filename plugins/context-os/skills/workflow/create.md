# Skill: workflow create

Scopes, builds, and proves one new workflow: a workflow in a package under `registry/workflows/<package>/`, run from the vault or built into a shared package whose releases are installed into the host's package store. A V-sequence leads the build: a role per stage, descending from purpose to design and build, then ascending through verification to acceptance. Within each stage, work through the definer, planner, solver, critic, refiner, and synthesiser hats as the stage needs.

A workflow is finished here when a dry run of it completes and the operator accepts it. Saved jobs come after, with `/job create`.

---

## Step 1: interview

Ask each question in turn, in plain language, and wait for the answer. Introduce ContextOS terms only as labels for what the operator already said, and confirm them. "Not sure yet" is a valid answer: record it as open.

If the router passed a description, it answers Q1; continue from Q2.

**Q1 (purpose):** "What should this do when it runs, with nobody watching? Walk me through what it reads, what it decides, and what is different once it has finished." Store as `purpose_narrative`. It is the acceptance test in Step 8.

**Q2 (reach):** "Is this for this vault only, or should the same logic run for other vaults, across several vaults at once, or be shared with other ContextOS hosts?" Using the router's [comparison](SKILL.md#workflow-router-skill), propose a package run from the vault or a shared package and say why in one sentence. Store the confirmed choice as `kind` (`vault` or `shared`).

**Q3 (inputs):** "What should change from one run to the next: a date, a folder, a vault, a threshold? Which of those must always be given, and which are optional?" Store as `inputs_narrative`. A workflow run from the vault cannot take a vault as an input; a shared one names each vault it touches as a `vault` input.

**Q4 (steps and tools):** "Take me through the steps in order: what is read first, what is decided or transformed, and what is written or changed. For each, which tool or service does it?" Store as `steps_narrative`. Every step must reduce to MCP tool calls plus the script's own logic; flag anything that cannot as open now.

**Q5 (servers):** Name the MCP servers the steps need, as they are named in the host's `web.toml` (`[[mcp_server]] name`). If the operator does not know, ask them to check `web.toml` or the ContextOS Web settings page, and record it as open until the dry run confirms it. Store as `servers`.

**Q6 (failure and repeat):** "If a run fails halfway, what should happen to what it already changed? Is it safe to run again from the start?" Tell the operator once: ContextOS Web never retries a failed run, never undoes calls already made, and never runs two runs of one job at once. Store as `failure_narrative`.

**Q7 (time budget):** "How long should a normal run take at most?" Store as `timeout_secs`; open means the host default of 300 seconds. It limits a one-off run of the workflow only: every saved job states its own `timeout_secs` and never takes the workflow's.

**Q8 (constraints):** "Anything this must never do, or must always do?" Store as `constraints_narrative`.

---

## Step 2: confirm before building

Summarise the answers in one short paragraph with the resolved `kind`, inputs, servers, and timeout, and ask the operator to confirm. Nothing is written before this.

---

## Step 3: V1, strategist (why)

As `strategist:role`: state what the workflow is for in one sentence, test that a standing, deterministic workflow is the right form (rather than a one-off task, a note, or a manual step), check nothing in `registry/workflows/` or the installed packages already does it (`/workflow list`), and settle the scope with the operator. If the vision drifts from what the operator said, go back to Step 1.

---

## Step 4: V2, analyst (what)

As `analyst:role`: turn the vision and answers into numbered requirements, each with how it will be checked. Include the inputs with their kinds and whether each is required, the servers (and for a shared package, the exact `(server, tool)` effects), the timeout, the failure and repeat behaviour, and every constraint. Name the dry-run scenarios that will prove the workflow: at least the normal path, and each failure the design must handle. Check every requirement traces to the interview and every answer has a requirement.

---

## Step 5: V3, architect (how)

As `architect:role`, produce and confirm with the operator:

- **Layout.** A package folder `registry/workflows/<package>/` with a `workflows.toml` listing the workflow, a folder `<package>/<workflow>/` holding its `workflow.toml`, the entry script (for example `main.rhai`), and `tests/<scenario>.toml` for each scenario. Keep the workflow's folder name equal to its name in `workflows.toml`; it is the workflow's slug. A package may hold several workflows, which share its `modules/` and `templates/`. For a shared package the same folder is built into a bundle (see [Shared packages](#shared-packages)).
- **The files**, drafted in full (see [Package files](#package-files) and [Workflow manifest](#workflow-manifest)).
- **The script outline**: each `call_mcp` in order, what its result feeds, the control flow between calls, and which failures are caught (recoverable: log, `flag_degraded`, continue) and which propagate (fail the run).
- **Repeat safety**: how a rerun after a partial failure behaves. If a step is not safe to repeat, say so in the design as a known limitation.
- **Each scenario**: the calls in order, with the mocked result or error of each.
- **Tool contracts**: read each tool's schema from the server where you can (for ContextOS MCP tools, the catalogue this session has) and design arguments and result handling against it, not against memory.

Check that a different engineer could build it unambiguously and that every requirement has a design decision.

---

## Step 6: V4, engineer (build)

As `engineer:role`, write exactly the confirmed design, following [The Rhai script](#the-rhai-script) and [Dry-run scenarios](#dry-run-scenarios).

- Write every file with `mcp__contextos__fs_write_file`: every file of a package at `<vault>://registry/workflows/<package>/...`. Never write vault files with this session's own file tools.

Before handing off, check: every `call_mcp` is permitted by the workflow's `[mcp_servers]` and `[mcp_tools]` lists (the same four lists wherever it runs) and nothing allowed goes unused; recoverable and fail-fast handling match the design; no secret, credential, or token appears anywhere; log messages at `info` and above carry no vault content.

---

## Step 7: V5, auditor (verify)

As `auditor:role`, prove the build against the design and requirements using the [contextos-web command line](SKILL.md#the-contextos-web-command-line):

1. **Run from the vault.** A job runs a release, not source, so when a job is to name this workflow, install the source first with the operator's confirmation: `contextos-web workflows install <vault> <package> --format json` (and `contextos-web libraries install <vault> <library> --format json` to install a library on its own), and read the result as [the command line](SKILL.md#the-contextos-web-command-line) describes. Then run `contextos-web workflows run <vault> <package> <workflow> --release <version> --dry-run --format json --scenario <name>` for each scenario, with the `release.version` the install reported (a new release is `future`, and a run with no `--release` takes `current`), with `--input name=value` for each input the scenario's path needs. A dry run whose `outcome` is `succeeded` or `degraded` ran its script to the end, and its arguments passed each tool's live schema; read `outputs` for what the script declared. A `failed` or `refused` outcome names its cause in `code` and `message`: `workflow/workflow-not-found` means the manifest did not register (an unknown key, an unconfigured server, a missing entry), `workflow/scenario-unavailable`, `workflow/scenario-ambiguous`, and `workflow/scenario-invalid` mean the scenario could not be found, chosen, or read, `workflow/input-invalid` means an input is wrong, `workflow/output-invalid` means the script set an output badly or left a required one unset, and `workflow/script-error` means the script itself failed.
2. **Shared package.** Build and install it as [Shared packages](#shared-packages) describes, with the operator confirming the install, then run `contextos-web workflows run --shared <package> <workflow> --dry-run --format json --release <version> --scenario <name>` for each scenario.
3. Check every requirement one by one against the design and the dry-run results.

Fix defects as `engineer:role` wearing `refiner:hat` and run the dry runs again. Record exactly what was validated: each command, its result, the host and `web.toml` it ran against, and what was not validated (a dry run proves the script's logic and call shapes against mocked results; it does not prove the live tools return what the scenario assumed).

---

## Step 8: V6, analyst (validate)

As `analyst:role`, check the finished workflow against `purpose_narrative` in the operator's own terms, using the dry-run evidence, and get explicit sign-off. A gap goes back to the stage it traces to: a missed requirement to Step 4, a design gap to Step 5, a build defect to Step 6.

---

## Step 9: register and hand off

1. Leave `registry/workflows/index.md` alone: the ContextOS MCP server lists the new folder in it, and `/workflow list` reads the manifests themselves.
2. Call `mcp__contextos__vault_log_append` with `entry: "workflow create | Created workflow: <slug>"` (or `"Built package <name> <version>"`) and `files` listing every vault file written.
3. Tell the operator what was built, what was validated and where, and that it runs only through a saved job: offer `/job create` for it. A workflow in the vault is discovered by ContextOS Web on its next pass; nothing needs restarting.

---

## Package files

`registry/workflows/<package>/workflows.toml`. ContextOS Web rejects any key not shown.

```toml
workflows = ["copy-notes"]            # required: the names of the package's workflows, each the name of its folder
modules = ["modules/helpers.rhai"]    # optional: .rhai files, relative to the package, every workflow may import
templates = ["templates"]             # optional: files and folders, relative to the package, every workflow may read

[[libraries]]                         # optional: a library the package's files import from
name = "crm"
requirement = "^1.2"                  # a semver requirement; a bare 1.2.0 means ^1.2.0
```

Modules, templates, and libraries are declared once, here. A workflow lists none of them, so an import name or a template path means one file whichever workflow uses it.

## Workflow manifest

`registry/workflows/<package>/<workflow>/workflow.toml`. ContextOS Web rejects any key not shown, and a workflow whose manifest fails is not registered, so none of its jobs are either.

```toml
name = "Copy meeting notes"   # required, not blank
entry = "main.rhai"           # required; relative to the workflow's folder, and must exist
timeout_secs = 120            # optional; limits a one-off run only (default 300), as every job states its own
entity = "personal"           # optional: a configured entity or "vault"; its jobs belong to it unless they declare their own
log_level = "info"            # optional: debug, info, warn, or error

[mcp_servers]                 # optional: leave it out and every server configured in web.toml may be called
allow = ["contextos"]         # each must be a [[mcp_server]] name in web.toml
deny = []                     # optional

[mcp_tools]                   # optional
allow = []                    # { server = "crm", tool = "list_contacts" }: restricts only the servers it names
deny = []                     # { server = "contextos", tool = "fs_delete_file" }

[[input]]
name = "since"
kind = "date"
required = false              # inputs are required unless this says false; no default is ever applied
```

A workflow's slug is the name of its folder. A call to server S, tool T is permitted when S is not denied, S is allowed or no server allow list exists, (S, T) is not denied, and the tool allow list names no tool on S or names (S, T): a deny always wins, and nothing declared permits every call. A server on both server lists, a pair on both tool lists, or a tool allow on a denied server is refused as `validation/artefact-invalid`. Input kinds are `string`, `number`, `bool`, `null`, `date` (`YYYY-MM-DD`), `time` (`HH:MM:SS`), `datetime` (RFC 3339), `timestamp` (whole seconds), `array` (with `items = { kind = "..." }`), and `object` (with `properties`, a list of named fields). A workflow run from the vault cannot declare `kind = "vault"`, at any depth.

---

## The Rhai script

The script's whole interface with the world:

| Name | What it does |
| --- | --- |
| `call_mcp(server, tool, args)` | Calls one tool and returns its clean JSON result as a map. `args` is a map literal, for example `#{ path: "work://memory/x.md" }`. A failure throws an error whose text begins `workflow/<kind>:` |
| `inputs` | The run's input values, read-only. An optional input that was not supplied is absent: test it with `"since" in inputs` |
| `log_debug`, `log_info`, `log_warn`, `log_error` | Write one message to the host log at that level, when the minimum level allows. `log_warn` and `log_error` also mark the run degraded, whatever the level |
| `flag_degraded(reason)` | Marks the run degraded without logging: for a retry, a delay, or any problem the script recovered from |
| `set_output(name, value)` | Sets one output the workflow declares (`[[output]]` in its `workflow.toml`), validated against its declared kind and at most 64 KiB. A refusal throws `workflow/output-invalid` naming the output, never the value. A required output left unset fails the run. This is how a caller receives results, in the summary's `outputs` |
| `workflow_file(path)` | Reads one file the package declares in `templates` and returns `#{ content, content_hash }`, the whole text and the SHA-256 of its bytes. Never writes: deploy a template by passing its `content` to `call_mcp` |
| `workflow_files()`, `workflow_files(prefix)` | Lists every declared file, or every declared file at or beneath `prefix`, as a sorted array of paths |

Nothing else is registered: no other file access, and no network, process, or clock access. `print` and `debug` write to the host log at `info` and `debug` and never to standard output, so use `set_output` for anything a caller needs.

- **Reach.** A workflow run from the vault may make the calls its `[mcp_servers]` and `[mcp_tools]` lists permit, and on the primary server may name only its own vault: address files as `<vault>://<path>` with this vault's configured name. A shared workflow is held to the same four lists, and may name only the vaults its `vault` inputs supply, for example `inputs.source_vault + "://notes/"`. Anything else fails with `workflow/effect-denied` or `workflow/vault-out-of-scope` before it is sent.
- **Results.** A whole file read through `fs_attach_file` or `fs_read_text_file` arrives as `#{ content, content_hash }`; a byte part (`offset` or `length`) carries no `content_hash`, so a script that needs a hash reads the whole file with `fs_attach_file`. Read a whole file with `fs_attach_file`: `fs_read_text_file` returns only a preview of a file at or above the server's inline threshold (5 KB by default), marked `truncated`, so a script that parses it, JSON say, fails on the cut text. Check a file's existence or hash with `fs_get_file_info`, never a folder listing, which leaves out the paths a vault hides, such as `.contextos/`. A result that is not readable JSON fails with `workflow/result-unreadable`.
- **Workflow files.** `templates` lists files and folders relative to the package root. A folder admits every file beneath it. Paths use `/`, are relative, and have no empty, `.`, or `..` segment, no trailing `/`, no backslash or colon, no segment ending in a dot or a space, and no Windows device name such as `CON` or `aux.md`. In a vault, a link in the workflow's folder is followed within the vault and refused beyond it. A workflow reads the release its run resolved, so editing a template in the vault's source takes effect only once a new release is installed. Compare a shipped file's `content_hash` with a vault file's to decide whether an update is needed. A file is at most 1 MiB and a listing at most 1000 files. Refusals throw `workflow/file-path-invalid`, `workflow/file-undeclared`, `workflow/file-not-found`, `workflow/file-not-text`, `workflow/file-too-large`, or `workflow/file-unreadable`.
- **Errors.** Catch a recoverable failure with `try { ... } catch (err) { log_warn(...); flag_degraded(...); }`. An uncaught error fails the run, and the run's record keeps its message. A run that completes but logged a warning or error, or flagged a reason, ends `degraded`.
- **Time.** The run is stopped at its timeout, between steps or while a call waits; a call in flight may or may not have taken effect.
- **Messages.** Each is cut at 2 KiB. Keep vault content and input values out of messages at `info` and above.

---

## Dry-run scenarios

A scenario lists, in order, every call a dry run expects and the result each returns. A workflow keeps them at `registry/workflows/<package>/<workflow>/tests/<name>.toml`.

```toml
[[call]]
server = "contextos"
tool = "fs_read_text_file"
kind = "valid"                  # checked against the tool's output schema, when it has one
response = { content = "# Notes", content_hash = "sha256:..." }

[[call]]
server = "contextos"
tool = "fs_write_file"
kind = "error"                  # the call fails with this message
error = "io/conflict: the file changed"
```

`workflow_file` and `workflow_files` are reads, not calls: a dry run reads the real files and a scenario does not list them, so a scaffold's dry run lists only its writes.

`kind = "invalid"` returns `response` unchecked, to exercise the script's handling of malformed data. Each call has `response` or `error`, never both, and a scenario has at least one call. A dry run fails if the script calls anything other than the next declared call, makes more calls than declared, or leaves any declared call unused. With one scenario, `--scenario` may be left out; with several it is required; with none, the workflow's jobs cannot be registered.

---

## Shared packages

A package's source lives in the vault at `registry/workflows/<package>/` and is authored and edited through ContextOS MCP. To share it, a release is built from it as a `.tar.gz` bundle and installed into the host's package store with `contextos-web packages install --shared`. The store keeps the releases its jobs and locks use and removes the rest after each change, so an older release stays only while something keeps it; the same name and version cannot be installed twice.

```text
registry/workflows/<package>/
├── manifest.toml                 The release only: name, version, digest, [[files]]. Made when the bundle is built
├── workflows.toml                The workflows by name, and the modules, templates, and libraries they share
├── <workflow>/workflow.toml      One folder per workflow: its declaration
├── <workflow>/<entry>.rhai       That workflow's entry script and any files of its own
├── <workflow>/tests/<name>.toml  That workflow's dry-run scenarios
├── modules/                      Modules every workflow of the package may import, as `workflows.toml` declares
└── templates/                    Files the scripts read, as `workflows.toml` declares
```

ContextOS MCP may keep an `index.md` in each folder; it is not part of the package and is left out of the bundle.

### Release manifest

```toml
name = "meeting-notes"                 # lowercase letters, digits, and hyphens
version = "1.0.0"                      # an exact semver release; a pre-release version is refused
digest = "sha256:<64 lowercase hex>"   # computed over every other file, see below

[[files]]                              # every file of the package but this one, each once, with its SHA-256
path = "workflows.toml"
hash = "<64 lowercase hex>"
```

`manifest.toml` holds these keys and no others. Everything else is declared in the package file and the workflow files, and a `workflow.toml` follows [the workflow manifest](#workflow-manifest) above, for example:

```toml
# copy-notes/workflow.toml
name = "Copy notes"
entry = "copy-notes.rhai"              # relative to this folder
log_level = "info"                     # optional

[mcp_servers]
allow = ["contextos"]

[mcp_tools]
allow = [{ server = "contextos", tool = "fs_read_text_file" }]

[[input]]
name = "source_vault"
kind = "vault"

[[output]]
name = "copied"
kind = "number"

[[required_tool_contracts]]
mcp_server_name = "contextos"
tool = "fs_read_text_file"
contract_version = "1"
```

- **Workflows.** A workflow is a folder named in `workflows.toml` whose `workflow.toml` the manifest lists under `[[files]]`; its slug is the folder's name. A listed workflow without its `workflow.toml` is a missing artefact, and a `workflow.toml` in a folder `workflows.toml` does not list is refused. A package that lists a `library.toml` instead of a `workflows.toml` is a library and holds no workflow. Only a library exports modules. A library's `library.toml` has `modules`, `exports` (a non-empty subset of the modules), `libraries`, and `mcp_tools`, which declares the tools its functions call, each exactly or as `{ server = "...", tool = "*" }` for every tool on a server. A literal `call_mcp` must be declared, a computed tool name is accepted only under a `*` for its server, and a `*` is accepted by a workflow only when its lists permit every tool on that server. A `*` is never valid in a workflow's own `[mcp_tools]` lists, and a `*` beside exact entries for the same server in one `library.toml` is refused as redundant. A package version steps by what its declarations change: a workflow removed, an input removed or made required, or an output removed is major; a workflow added, a new optional input, a new output, or an entry added to or removed from any of the four lists is minor.
- **Where it runs.** A workflow with a `vault` input is shared and installs only into the host's store. A vault's own store refuses any workflow that declares one.
- **`[mcp_servers]` and `[mcp_tools]`** are the calls a workflow may make: nothing declared permits every call, a deny always wins, and the rule is the one set out above. Allow only the `(server, tool)` pairs the script calls. Validation of a shared job checks each server an allow list names is configured and offers each tool the tool allow names.
- **`required_tool_contracts`** records the tool contracts the workflow was written against; ContextOS Web carries it for the operator and does not compare versions.
- **`outputs`** documents what the workflow produces; ContextOS Web does not yet check a run's result against it.
- **`templates`** in `workflows.toml` declares the bundled files and folders the package's scripts may read with `workflow_file` and `workflow_files`. Install refuses a bundle that lacks a declared path, and any bundle holding a link.
- No file names a vault, path, or person: bindings are supplied when a job or run names its inputs.

### Digest, bundle, and install

The shell only reads the vault here; nothing it runs writes there. Take the vault's absolute `path` from `vault_info`, and run these from the package folder, `<vault path>/registry/workflows/<package>`, on the ContextOS Web host (Linux or macOS):

```bash
out=$(mktemp -d)
find . -type f ! -name index.md ! -name '.*' | sed 's|^\./||' | tr '/' '\001' | LC_ALL=C sort | tr '\001' '/' > "$out/files"
grep -vx manifest.toml "$out/files" \
  | while IFS= read -r f; do printf '%s\0' "$f"; cat -- "$f"; printf '\0'; done | shasum -a 256
```

The file list is every file of the package, in path order, without the `index.md` files and hidden files. The digest covers every listed file except `manifest.toml`, each as its relative path, a NUL byte, its content, and a NUL byte (`sha256sum` gives the same value where `shasum` is not installed). Check the list names exactly the package's files, and that no template is called `index.md`.

Write `sha256:` and that value into the manifest's `digest` with `mcp__contextos__fs_edit_file`; the manifest is not part of the digest, so this does not change it. The manifest also lists every one of those files under `[[files]]`, each with the SHA-256 of its bytes, which the same folder prints:

```bash
grep -vx manifest.toml "$out/files" | while IFS= read -r f; do printf '\n[[files]]\npath = "%s"\nhash = "%s"\n' "$f" "$(shasum -a 256 -- "$f" | cut -d' ' -f1)"; done
```

Append that output to the end of the manifest. The install refuses a file the manifest does not list, and a listed file it does not hold. Then, still from the package folder, bundle the same list into the temporary folder, with member paths relative to the package (no leading `./`, which the installer rejects):

```bash
tar -czf "$out/<name>-<version>.tar.gz" -T "$out/files"
```

With the operator's confirmation, run `contextos-web packages install --shared "$out/<name>-<version>.tar.gz"`, then `contextos-web packages inspect --shared <name> <version>` to confirm what was installed. If the install reports a digest mismatch, list the bundle with `tar -tzf` and confirm it holds exactly the reviewed files before using the computed digest it reports. A release has no pre-release version and the same name and version cannot be installed twice, so each development install takes the next patch version; dry-run each with `--release <version>`, and the store removes a superseded one on its own once nothing keeps it; ask the operator before removing one sooner with `packages remove --shared`. If the shell is not on the host or cannot read the vault path, give the operator these commands to run.

---

## Invariants

- Never write before Step 2's confirmation, and never resolve an open answer by guessing.
- Never widen `[mcp_servers]` or `[mcp_tools]` beyond what the steps need and the operator confirmed.
- A workflow is proved by dry runs that complete, never by inspection or by a live run in its place.
- Never put a secret in any file, and never put vault content in log messages at `info` and above.
- A failed critic check goes back to the stage that owns the gap.
