// Scaffolds a vault: creates every file the package ships or seeds that the vault does not have yet, and, when the
// operator and members are given, the team and each agent member's workspace. Strictly additive: a file that exists
// is never read for change or replaced, and a run repeated after a failure carries on where the last one stopped.
//
// Templates: templates/shipped/<path> and templates/seeded/<path> go to <path>; templates/entity/profile.md goes to
// memory/entities/<entity_slug>.md, beside an empty <entity_slug>/ folder. The difference
// between shipped and seeded matters only to the update workflow, which refreshes shipped files and never seeded ones.
// templates/members/<function>.md is read only here, to write each team member, and never reaches the vault itself.
// The plugin's decisions are raised through the register once this run has created it; a register that already exists
// is the update workflow's to bring in step.

import "modules/helpers" as helpers;
import "modules/layout" as layout;

const SERVER = "contextos";
const TEAM_FILE = ".contextos/team.toml";
const WORKSPACES = ".contextos/workspaces/";

// The lowercase-hyphenated identifier both agent hosts use for a member named `name`.
fn member_slug(name) {
    let out = "";
    let gap = false;
    for c in name.to_lower().chars() {
        if (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') {
            if gap && out != "" { out += "-"; }
            out += c;
            gap = false;
        } else {
            gap = true;
        }
    }
    out
}

// A TOML basic string holding `value`.
fn toml_string(value) {
    let out = "\"";
    for c in value.chars() {
        if c == '"' { out += "\\\""; }
        else if c == '\\' { out += "\\\\"; }
        else if c == '\n' { out += "\\n"; }
        else if c == '\r' { out += "\\r"; }
        else if c == '\t' { out += "\\t"; }
        else { out += c; }
    }
    out + "\""
}

// The template's text without its closing authoring note (a trailing <!-- ... --> block).
fn without_closing_note(text) {
    let trimmed = trim_end_copy(text);
    if trimmed.ends_with("-->") {
        let at = helpers::last_index(trimmed, "<!--");
        if at >= 0 {
            let body = trimmed.sub_string(0, at);
            return trim_end_copy(body) + "\n";
        }
    }
    text
}

fn trim_end_copy(text) {
    let copy = text;
    while copy.len() > 0 && (copy.ends_with(" ") || copy.ends_with("\n") || copy.ends_with("\r") || copy.ends_with("\t")) {
        copy = copy.sub_string(0, copy.len() - 1);
    }
    copy
}

let vault = inputs.vault;
let created_at = inputs.created_at;
let files_created = [];
let files_skipped = 0;
let errors = [];

// Every destination, with the template it comes from and whether it takes the creation placeholders.
let plan = #{};
for source in workflow_files("templates/shipped") {
    plan[source.sub_string("templates/shipped/".len())] = #{ source: source, seeded: false };
}
for source in workflow_files("templates/seeded") {
    plan[source.sub_string("templates/seeded/".len())] = #{ source: source, seeded: true };
}
let entity_slug = if "entity_slug" in inputs { inputs.entity_slug } else { "" };
let entity_name = if "entity_name" in inputs { inputs.entity_name } else { "" };
if entity_slug != "" {
    if entity_name == "" { entity_name = entity_slug; }
    plan["memory/entities/" + entity_slug + ".md"] = #{ source: "templates/entity/profile.md", seeded: true };
}

let folders_created = [];
let folders = layout::FOLDERS;
if entity_slug != "" { folders.push(entity_slug); }
folders.sort();
for folder in folders {
    if helpers::exists_in(vault, folder) { continue; }
    call_mcp(SERVER, "fs_create_directory", #{ path: vault + "://" + folder });
    folders_created.push(folder);
}

let destinations = plan.keys();
destinations.sort();
for destination in destinations {
    if helpers::exists_in(vault, destination) {
        files_skipped += 1;
        continue;
    }
    let item = plan[destination];
    let content = workflow_file(item.source).content;
    if item.seeded {
        content = helpers::replaced(content, "{{created_at}}", created_at);
        content = helpers::replaced(content, "{{entity_name}}", entity_name);
    }
    call_mcp(SERVER, "fs_write_file", #{ path: vault + "://" + destination, content: content });
    files_created.push(destination);
}

let decisions_created = [];
if files_created.contains("memory/decisions.md") {
    for decision in layout::DECISIONS {
        try {
            let key = helpers::raise_decision(vault, decision);
            if key != "" { decisions_created.push(key); }
        } catch (err) {
            errors.push(decision.slug + ": " + err.to_string());
            break;
        }
    }
}

// The team: the operator as its human member, and each member rendered from its shipped template.
let members_created = [];
let members_skipped = [];
let workspaces_created = [];
let team_added = [];
if "operator" in inputs && inputs.operator != "" {
    let operator = inputs.operator;
    let team_text = "";
    let team_hash = "";
    let existing = #{};
    try {
        let read = call_mcp(SERVER, "fs_attach_file", #{ path: vault + "://" + TEAM_FILE });
        team_text = read.content;
        team_hash = read.content_hash;
    } catch (err) {
        if !err.to_string().contains("not-found") && !err.to_string().contains("not found") { throw err; }
    }
    for line in team_text.split("\n") {
        let trimmed = line;
        trimmed.trim();
        if trimmed.starts_with("slug") && trimmed.contains("=") {
            let value = trimmed.sub_string(trimmed.index_of("=") + 1);
            value.trim();
            value.replace("\"", "");
            value.replace("'", "");
            existing[value] = true;
        }
    }

    let entries = "";
    let operator_slug = member_slug(operator);
    if operator_slug == "" {
        errors.push("operator needs a name with at least one letter or digit");
    } else if !(operator_slug in existing) {
        entries += "\n[[member]]\nslug = " + toml_string(operator_slug) + "\nname = " + toml_string(operator) + "\ntype = \"human\"\n";
        entries += "team = " + toml_string(layout::TEAM) + "\ndomain = " + toml_string(layout::DOMAINS["chief-of-staff"]) + "\n";
        existing[operator_slug] = true;
        team_added.push(operator_slug);
    }

    let members = if "members" in inputs { inputs.members } else { [] };
    for member in members {
        let slug = member_slug(member.name);
        let source = "templates/members/" + member.function + ".md";
        if slug == "" { errors.push(member.function + ": the name has no letters or digits"); continue; }
        if slug == operator_slug { errors.push(member.function + ": the name is the operator's own; choose another"); continue; }
        let template = "";
        try {
            template = workflow_file(source).content;
        } catch (err) {
            errors.push(member.function + ": no member template " + source);
            continue;
        }
        // The member's working folder for scheduled sessions: under .contextos/, so Git, search, and index.md skip it.
        let workspace = WORKSPACES + slug;
        if !helpers::exists_in(vault, workspace) {
            call_mcp(SERVER, "fs_create_directory", #{ path: vault + "://" + workspace });
            workspaces_created.push(workspace);
        }
        let destination = "registry/agents/" + slug + ".md";
        if helpers::exists_in(vault, destination) {
            members_skipped.push(destination);
        } else {
            let text = without_closing_note(template);
            text = helpers::replaced(text, "{{slug}}", slug);
            text = helpers::replaced(text, "name: \"{{name}}\"", "name: " + toml_string(member.name));
            text = helpers::replaced(text, "{{name}}", member.name);
            text = helpers::replaced(text, "{{OperatorName}}", operator);
            call_mcp(SERVER, "fs_write_file", #{ path: vault + "://" + destination, content: text });
            members_created.push(destination);
        }
        if !(slug in existing) {
            entries += "\n[[member]]\nslug = " + toml_string(slug) + "\nname = " + toml_string(member.name) + "\ntype = \"agent\"\n";
            if member.function == "chief-of-staff" { entries += "chief_of_staff = true\n"; }
            entries += "team = " + toml_string(layout::TEAM) + "\n";
            if member.function in layout::DOMAINS { entries += "domain = " + toml_string(layout::DOMAINS[member.function]) + "\n"; }
            existing[slug] = true;
            team_added.push(slug);
        }
    }

    if entries != "" {
        let current = trim_end_copy(team_text);
        let text = if current == "" { entries.sub_string(1) } else { current + "\n" + entries };
        let args = #{ path: vault + "://" + TEAM_FILE, content: text };
        if team_hash != "" { args.expected_hash = team_hash; }
        call_mcp(SERVER, "fs_write_file", args);
    }
}

set_output("result", #{
    folders_created: folders_created,
    files_created: files_created,
    files_skipped: files_skipped,
    decisions_created: decisions_created,
    members_created: members_created,
    members_skipped: members_skipped,
    workspaces_created: workspaces_created,
    team_added: team_added,
    errors: errors,
});
