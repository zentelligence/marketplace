// Brings an existing vault back in step with this package. Without `apply` it only reports the plan; with `apply`
// it adds what is missing, refreshes what is safe to refresh, resolves the conflicts the operator chose, applies the
// migrations the operator named, creates any agent member's missing workspace, and records all of it in
// .contextos/state.json.
//
// Each shipped file is compared three ways: the shipped ancestor its vault copy derives from (A, recorded in the
// state), the vault copy now (V), and the package's copy now (P).
// - V == P: unchanged; A becomes P.
// - A unknown and V != P: a conflict. The operator's content is never recorded as shipped.
// - V == A and P != A: untouched by the operator; refreshed to P, and A becomes P.
// - V != A and P == A: customised by the operator, and the package has not changed: left alone.
// - V != A and P != A: a conflict; A is kept, so it stays a conflict until resolved.
// Seeded files are added when missing and never refreshed. AGENTS.md, CLAUDE.md, and registry/instructions/global.md
// carry the operator's name, so they arrive only through the migrations that know it.
//
// The plugin's decisions are not files: each is raised through the register, which gives it the next id the vault's own
// counter has free, so it can never land on a record the vault already holds. One is raised at most once: the state
// records it, and a decision of that title already in the register counts as raised. They are raised in list order, and
// a failure stops the rest until the next run, so ids keep that order. Update never rewrites a record.

import "modules/helpers" as helpers;
import "modules/layout" as layout;

const PACKAGE_VERSION = "1.0.0";
const PLUGIN = "context-os";
const STATE_FILE = ".contextos/state.json";
const ORIENTATION = "registry/instructions/global.md";
const RETIRED_DIR = ".contextos/retired";
const DECISIONS_DIR = "memory/decisions";

fn name_of(path) {
    let at = helpers::last_index(path, "/");
    if at < 0 { path } else { path.sub_string(at + 1) }
}

// The bare file name of a register record named with a slug, `vd-001-some-slug.md` giving `vd-001.md`, or "" for any
// other name.
fn bare_record_name(name) {
    if !name.ends_with(".md") { return ""; }
    let parts = name.split("-");
    if parts.len() < 3 || (parts[0] != "vd" && parts[0] != "vq") || parts[1] == "" { return ""; }
    for digit in parts[1].chars() {
        if digit < '0' || digit > '9' { return ""; }
    }
    parts[0] + "-" + parts[1] + ".md"
}

fn listing(vault, dir) {
    let path = if dir == "" { vault + "://." } else { vault + "://" + dir };
    let names = #{};
    try {
        let result = call_mcp("contextos", "fs_list_directory", #{ path: path });
        for entry in result.entries { names[entry.name] = entry.kind; }
    } catch (err) {
        if !helpers::is_not_found(err) { throw err; }
    }
    names
}

// Whether the register in `folder` holds a decision titled `title`, in any file and under any id.
fn holds_decision(vault, folder, title) {
    let found = call_mcp("contextos", "base_query", #{ vault: vault + "://.", format: "json", definition: #{
        filters: "file.inFolder(\"" + folder + "\") && note.title == \"" + title + "\"",
        order: ["note.title"],
    } });
    found.matched > 0
}

fn read_text(vault, path) {
    try {
        return call_mcp("contextos", "fs_attach_file", #{ path: vault + "://" + path });
    } catch (err) {
        if !helpers::is_not_found(err) { throw err; }
    }
    ()
}

// The operator's name from a vault instructions heading, `# <name>'s ContextOS`, or "" when there is none.
fn operator_from_heading(text) {
    for line in text.split("\n") {
        let trimmed = line;
        trimmed.trim();
        if trimmed.starts_with("# ") && trimmed.ends_with("'s ContextOS") {
            let name = trimmed.sub_string(2, trimmed.len() - 2 - "'s ContextOS".len());
            name.trim();
            return name;
        }
    }
    ""
}

// Every file under `dir` in `vault`, as paths relative to the vault, leaving out the index.md files the server
// maintains.
fn files_under(vault, dir) {
    let files = [];
    let names = listing(vault, dir);
    let keys = names.keys();
    keys.sort();
    for name in keys {
        let path = dir + "/" + name;
        if names[name] == "dir" { files += files_under(vault, path); }
        else if name != "index.md" { files.push(path); }
    }
    files
}

let vault = inputs.vault;
let updated_at = inputs.updated_at;
let apply = "apply" in inputs && inputs.apply;
let errors = [];

// --- state ------------------------------------------------------------------------------------------------------
let state = #{ package_version: (), last_update: (), synced_files: #{}, migrations: [], decisions_raised: [] };
let state_hash = "";
let state_read = read_text(vault, STATE_FILE);
if state_read != () {
    try {
        let parsed = parse_json(state_read.content);
        for key in ["package_version", "last_update", "synced_files", "migrations", "decisions_raised"] {
            if key in parsed && parsed[key] != () { state[key] = parsed[key]; }
        }
        state_hash = state_read.content_hash;
    } catch (err) {
        errors.push(STATE_FILE + " is not valid JSON, so the update stopped before changing anything; correct or remove it");
        set_output("plan", #{ applied: false, files_added: [], files_refreshed: [], conflicts: [], resolved: [],
            migrations_pending: [], migrations_applied: [], team_conflicts: [], errors: errors });
        return;
    }
}
let synced = state.synced_files;
// An entry plugin 1.17.3 recorded is the bare hash of the vault's copy as last synced, which may hold the operator's
// edits, so it says nothing about what shipped: the ancestor is unknown, and a copy that differs is a conflict.
for path in synced.keys() {
    if type_of(synced[path]) != "map" { synced[path] = #{ shipped: (), plugin: PLUGIN }; }
}

// --- the package's files ------------------------------------------------------------------------------------------
let shipped = #{};
for source in workflow_files("templates/shipped") { shipped[source.sub_string("templates/shipped/".len())] = source; }
let seeded = #{};
for source in workflow_files("templates/seeded") {
    let destination = source.sub_string("templates/seeded/".len());
    if destination != "AGENTS.md" && destination != "CLAUDE.md" && destination != ORIENTATION {
        seeded[destination] = source;
    }
}

let resolutions = #{};
if "resolve" in inputs {
    for item in inputs.resolve {
        if item.choice != "keep-mine" && item.choice != "take-plugin" {
            errors.push(item.path + ": choose keep-mine or take-plugin");
        } else if !(item.path in shipped) {
            errors.push(item.path + " is not a file this package ships");
        } else {
            resolutions[item.path] = item.choice;
        }
    }
}

let files_added = [];
let files_refreshed = [];
let conflicts = [];
let resolved = [];

let folders_added = [];
for folder in layout::FOLDERS {
    if helpers::exists_in(vault, folder) { continue; }
    if apply { call_mcp("contextos", "fs_create_directory", #{ path: vault + "://" + folder }); }
    folders_added.push(folder);
}

let shipped_paths = shipped.keys();
shipped_paths.sort();
for destination in shipped_paths {
    let source = workflow_file(shipped[destination]);
    let info = helpers::info_of(vault, destination);
    if info == () {
        if apply {
            call_mcp("contextos", "fs_write_file", #{ path: vault + "://" + destination, content: source.content });
            synced[destination] = #{ shipped: source.content_hash, plugin: PLUGIN };
        }
        files_added.push(destination);
        continue;
    }
    let current = info.content_hash;
    let entry = if destination in synced { synced[destination] } else { #{ shipped: (), plugin: PLUGIN } };
    let ancestor = entry.shipped;

    if destination in resolutions {
        if resolutions[destination] == "take-plugin" && current != source.content_hash && apply {
            call_mcp("contextos", "fs_write_file",
                #{ path: vault + "://" + destination, content: source.content, expected_hash: current });
        }
        if apply { synced[destination] = #{ shipped: source.content_hash, plugin: PLUGIN }; }
        resolved.push(destination + " (" + resolutions[destination] + ")");
    } else if current == source.content_hash {
        synced[destination] = #{ shipped: source.content_hash, plugin: entry.plugin ?? PLUGIN };
    } else if ancestor == () {
        conflicts.push(destination);
    } else if current == ancestor {
        if apply {
            call_mcp("contextos", "fs_write_file",
                #{ path: vault + "://" + destination, content: source.content, expected_hash: current });
            synced[destination] = #{ shipped: source.content_hash, plugin: PLUGIN };
        }
        files_refreshed.push(destination);
    } else if source.content_hash != ancestor {
        conflicts.push(destination);
    }
}

let seeded_paths = seeded.keys();
seeded_paths.sort();
for destination in seeded_paths {
    if helpers::exists_in(vault, destination) { continue; }
    if apply {
        let content = workflow_file(seeded[destination]).content;
        content = helpers::replaced(content, "{{created_at}}", updated_at);
        call_mcp("contextos", "fs_write_file", #{ path: vault + "://" + destination, content: content });
    }
    files_added.push(destination);
}

// --- the plugin's decisions -----------------------------------------------------------------------------------------
let decisions_added = [];
let raised = state.decisions_raised;
for decision in layout::DECISIONS {
    if raised.contains(decision.slug) { continue; }
    if !holds_decision(vault, DECISIONS_DIR, decision.title) {
        if apply {
            try {
                let key = helpers::raise_decision(vault, decision);
                if key != "" { decisions_added.push(key + ": " + decision.title); }
            } catch (err) {
                errors.push(decision.slug + ": " + err.to_string());
                break;
            }
        } else {
            decisions_added.push(decision.title);
        }
    }
    raised.push(decision.slug);
}

// --- migrations ----------------------------------------------------------------------------------------------------
let pending = [];
let agents_heading = "";
let agents_read = read_text(vault, "AGENTS.md");
let claude_read = read_text(vault, "CLAUDE.md");
if agents_read != () { agents_heading = operator_from_heading(agents_read.content); }
let claude_heading = if claude_read != () { operator_from_heading(claude_read.content) } else { "" };

if claude_read != () && agents_read == () {
    pending.push(#{ id: "vault-instructions",
        description: "The vault's instructions are in CLAUDE.md; they belong in AGENTS.md, read by Claude Code and Codex alike, with CLAUDE.md as its one-line import.",
        action: "Write AGENTS.md from the shipped template, carrying the operator's name from CLAUDE.md's heading; keep the old file as CLAUDE.legacy.md to merge any customisations by hand; replace CLAUDE.md with the one-line @AGENTS.md import.",
        paths: ["CLAUDE.md"] });
}
if helpers::exists_in(vault, "memory/operating/global-instructions.md") {
    pending.push(#{ id: "global-instructions",
        description: "memory/operating/global-instructions.md is a retired instructions paste block; its general rules now live in AGENTS.md, and the orientation every session receives in registry/instructions/global.md.",
        action: "Move it to memory/operating/archive/global-instructions.md.",
        paths: ["memory/operating/global-instructions.md"] });
}
if helpers::exists_in(vault, "registry/index.md") && !helpers::exists_in(vault, ORIENTATION) {
    pending.push(#{ id: "orientation",
        description: "This vault has no " + ORIENTATION + ", the orientation the ContextOS MCP server places in every Claude Code and Codex session, so sessions outside the vault are not told how to reach it.",
        action: "Write " + ORIENTATION + " from the shipped template, carrying the operator's name from the heading of AGENTS.md (or CLAUDE.md); its operator profile sections stay marked not yet captured until /vault init fills them from the vault's own files.",
        paths: [ORIENTATION] });
}
let shims = [];
for name in listing(vault, ".claude/agents").keys() {
    if !name.ends_with(".md") { continue; }
    let read = read_text(vault, ".claude/agents/" + name);
    if read != () && read.content.contains("source sha256: ") { shims.push(".claude/agents/" + name); }
}
shims.sort();
if shims.len() > 0 {
    pending.push(#{ id: "agent-shims",
        description: "Generated agent shims in .claude/agents/; the ContextOS MCP server now projects agents into Claude Code and Codex itself.",
        action: "Move each generated shim to " + RETIRED_DIR + "/agent-shims/; hand-written files there are left alone.",
        paths: shims });
}
if helpers::exists_in(vault, "memory/index.md") && !helpers::exists_in(vault, ".contextos/team.toml") {
    pending.push(#{ id: "team",
        description: "This vault has no team declaration, so it has none of the six team members the plugin ships (chief of staff, librarian, technologist, support, communications, and assurance). Run /vault init to create the team.",
        paths: [".contextos/team.toml"] });
}

let team_file = read_text(vault, ".contextos/team.toml");
let old_scripts = helpers::info_of(vault, "scripts");
if old_scripts != () && old_scripts.kind == "dir" {
    pending.push(#{ id: "registry-scripts",
        description: "Utility scripts in a top-level scripts/ folder; they belong in registry/scripts/, beside the vault's other reusable definitions.",
        action: "Move every file in scripts/ to the same place under registry/scripts/. A file you edited replaces the plugin's untouched copy there, keeping your edits; one that differs from an edited copy there is left in scripts/ to merge by hand. What remains of scripts/ then moves to " + RETIRED_DIR + "/scripts/, or, when a file was left, each file already handled does.",
        paths: ["scripts/"] });
}
let slugged = [];
for name in listing(vault, DECISIONS_DIR).keys() {
    if bare_record_name(name) != "" { slugged.push(DECISIONS_DIR + "/" + name); }
}
slugged.sort();
if slugged.len() > 0 {
    pending.push(#{ id: "decision-filenames",
        description: "Records in " + DECISIONS_DIR + "/ whose file names carry a slug; a record's file is named for its id alone.",
        action: "Move each to its bare id, such as vd-001.md. Where a record already holds that name, an identical copy or the plugin's unedited one moves to " + RETIRED_DIR + "/decisions/; any other is left to merge by hand. Links to the old names do not follow.",
        paths: slugged });
}

let migrations_applied = [];
let requested = if "migrate" in inputs { inputs.migrate } else { [] };
let pending_by_id = #{};
for item in pending { pending_by_id[item.id] = item; }
for id in requested {
    if !(id in pending_by_id) { errors.push(id + ": not pending in this vault"); continue; }
    if !("action" in pending_by_id[id]) { errors.push(id + ": reported only; there is nothing to apply"); continue; }
    if !apply { continue; }
    let changes = [];
    try {
        if id == "vault-instructions" {
            let template = workflow_file("templates/seeded/AGENTS.md").content;
            if claude_heading != "" { template = helpers::replaced(template, "{{OperatorName}}", claude_heading); }
            call_mcp("contextos", "fs_move_file", #{ source: vault + "://CLAUDE.md", destination: vault + "://CLAUDE.legacy.md" });
            changes.push("moved CLAUDE.md to CLAUDE.legacy.md");
            call_mcp("contextos", "fs_write_file", #{ path: vault + "://AGENTS.md", content: template });
            call_mcp("contextos", "fs_write_file", #{ path: vault + "://CLAUDE.md",
                content: workflow_file("templates/seeded/CLAUDE.md").content });
            changes.push("wrote AGENTS.md from the shipped template"
                + (if claude_heading == "" { "; the operator's name was not found, so {{OperatorName}} remains" } else { "" }));
            changes.push("wrote CLAUDE.md as the @AGENTS.md import");
            agents_heading = claude_heading;
        } else if id == "global-instructions" {
            call_mcp("contextos", "fs_move_file", #{ source: vault + "://memory/operating/global-instructions.md",
                destination: vault + "://memory/operating/archive/global-instructions.md" });
            changes.push("moved memory/operating/global-instructions.md to memory/operating/archive/global-instructions.md");
        } else if id == "orientation" {
            let name = if agents_heading != "" { agents_heading } else { claude_heading };
            let template = workflow_file("templates/seeded/" + ORIENTATION).content;
            if name != "" { template = helpers::replaced(template, "{{OperatorName}}", name); }
            call_mcp("contextos", "fs_write_file", #{ path: vault + "://" + ORIENTATION, content: template });
            changes.push("wrote " + ORIENTATION + " from the shipped template"
                + (if name == "" { "; the operator's name was not found, so {{OperatorName}} remains" } else { "" }));
        } else if id == "agent-shims" {
            for path in shims {
                let destination = RETIRED_DIR + "/agent-shims/" + name_of(path);
                call_mcp("contextos", "fs_move_file", #{ source: vault + "://" + path, destination: vault + "://" + destination });
                changes.push("moved " + path + " to " + destination);
            }
        } else if id == "registry-scripts" {
            let retire = [];
            let left = [];
            for path in files_under(vault, "scripts") {
                let destination = "registry/" + path;
                let target = helpers::info_of(vault, destination);
                let source = helpers::info_of(vault, path);
                if target == () {
                    call_mcp("contextos", "fs_move_file", #{ source: vault + "://" + path, destination: vault + "://" + destination });
                    if path in synced { synced[destination] = synced[path]; }
                    changes.push("moved " + path + " to " + destination);
                } else if target.content_hash == source.content_hash {
                    if path in synced && !(destination in synced) { synced[destination] = synced[path]; }
                    retire.push(path);
                } else if destination in shipped && target.content_hash == workflow_file(shipped[destination]).content_hash {
                    call_mcp("contextos", "fs_write_file", #{ path: vault + "://" + destination,
                        content: read_text(vault, path).content, expected_hash: target.content_hash });
                    if path in synced { synced[destination] = synced[path]; } else { synced.remove(destination); }
                    changes.push("wrote " + path + " over the plugin's untouched copy at " + destination + ", keeping its edits");
                    retire.push(path);
                } else {
                    left.push(path);
                    continue;
                }
                synced.remove(path);
            }
            if left.len() == 0 {
                call_mcp("contextos", "fs_move_file", #{ source: vault + "://scripts", destination: vault + "://" + RETIRED_DIR + "/scripts" });
                changes.push("moved what remained of scripts/ to " + RETIRED_DIR + "/scripts/");
            } else {
                for path in retire {
                    call_mcp("contextos", "fs_move_file", #{ source: vault + "://" + path, destination: vault + "://" + RETIRED_DIR + "/" + path });
                    changes.push("moved " + path + " to " + RETIRED_DIR + "/" + path);
                }
                changes.push("left " + left.len() + " file(s) in scripts/ that differ from an edited copy in registry/scripts/, to merge by hand: "
                    + left.reduce(|sum, path| if sum == "" { path } else { sum + ", " + path }, ""));
            }
        } else if id == "decision-filenames" {
            let left = [];
            for path in slugged {
                let destination = DECISIONS_DIR + "/" + bare_record_name(name_of(path));
                let target = helpers::info_of(vault, destination);
                if target == () {
                    call_mcp("contextos", "fs_move_file", #{ source: vault + "://" + path, destination: vault + "://" + destination });
                    changes.push("moved " + path + " to " + destination);
                } else {
                    let current = helpers::info_of(vault, path).content_hash;
                    let unedited = path in synced && synced[path].shipped == current;
                    if current != target.content_hash && !unedited {
                        left.push(path);
                        continue;
                    }
                    let retired = RETIRED_DIR + "/decisions/" + name_of(path);
                    call_mcp("contextos", "fs_move_file", #{ source: vault + "://" + path, destination: vault + "://" + retired });
                    changes.push("moved " + path + " to " + retired + ", since " + destination + " already holds that id");
                }
                synced.remove(path);
            }
            if left.len() > 0 {
                changes.push("left " + left.len() + " file(s) that differ from the record already at their bare id, to merge by hand: "
                    + left.reduce(|sum, path| if sum == "" { path } else { sum + ", " + path }, ""));
            }
        }
    } catch (err) {
        errors.push(id + ": " + err.to_string());
        if changes.len() == 0 { continue; }
    }
    state.migrations.push(#{ id: id, applied: updated_at, package_version: PACKAGE_VERSION, changes: changes });
    migrations_applied.push(id);
}
let migrations_pending = [];
for item in pending { if !migrations_applied.contains(item.id) { migrations_pending.push(item); } }

// --- the team ------------------------------------------------------------------------------------------------------
let team_conflicts = [];
let health = call_mcp("contextos", "doctor", #{ path: vault });
for check in health.checks {
    let team = check.kind == "team_config";
    if team && check.status == "fail" { team_conflicts.push(check.message); }
}

// --- workspaces ----------------------------------------------------------------------------------------------------
// Each agent member's working folder for scheduled sessions (/dispatch), created when it is missing.
let workspaces_added = [];
if team_file != () {
    let agents = [];
    let slug = "";
    for line in (team_file.content + "\n[[member]]").split("\n") {
        let trimmed = line;
        trimmed.trim();
        if trimmed == "[[member]]" { slug = ""; continue; }
        if !trimmed.contains("=") { continue; }
        let key = trimmed.sub_string(0, trimmed.index_of("="));
        key.trim();
        let value = trimmed.sub_string(trimmed.index_of("=") + 1);
        value.trim();
        value.replace("\"", "");
        value.replace("'", "");
        if key == "slug" { slug = value; }
        if key == "type" && value == "agent" && slug != "" { agents.push(slug); }
    }
    for member in agents {
        let workspace = ".contextos/workspaces/" + member;
        if helpers::exists_in(vault, workspace) { continue; }
        if apply { call_mcp("contextos", "fs_create_directory", #{ path: vault + "://" + workspace }); }
        workspaces_added.push(workspace);
    }
}

// --- record --------------------------------------------------------------------------------------------------------
if apply {
    state.synced_files = synced;
    state.decisions_raised = raised;
    state.package_version = PACKAGE_VERSION;
    state.last_update = updated_at;
    let args = #{ path: vault + "://" + STATE_FILE, content: state.to_json() + "\n" };
    if state_hash != "" { args.expected_hash = state_hash; }
    call_mcp("contextos", "fs_write_file", args);
}

set_output("plan", #{
    applied: apply,
    folders_added: folders_added,
    files_added: files_added,
    files_refreshed: files_refreshed,
    decisions_added: decisions_added,
    conflicts: conflicts,
    resolved: resolved,
    migrations_pending: migrations_pending,
    migrations_applied: migrations_applied,
    team_conflicts: team_conflicts,
    workspaces_added: workspaces_added,
    errors: errors,
});
