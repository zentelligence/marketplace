// Checks the knowledge quality of a vault's wiki articles (memory/wiki/) and insight notes (memory/insights/), and
// reports what it finds for /vault health to hand to the librarian. It only reads: a run changes nothing, so it is
// safe to repeat and to schedule. Vault health (configuration, indexes, Git, stores, records, and the team) is the
// server's doctor's, and is not repeated here.
//
// Per note: a lowercase-hyphenated path, frontmatter, sources in the frontmatter (never a **Source:** line in the
// body) that resolve, an allowed status (and confidence, for an insight), no unfilled {{placeholder}}, no empty
// heading, an ## Open Questions section that holds only links to tasks (memory/tasks/) or vault decisions
// (memory/decisions/), and the age checks: a wiki article not updated for `stale_days`, and an insight still proposed
// `proposed_days` after it was created. Across the notes, from the server's link graph: every link that resolves to
// no file or several, and every note with no links in or out.
//
// The report lists every finding, sorted by path, until it nears the 64 KiB an output may hold; `total_findings` and
// `counts` always cover them all, and `truncated` says when the list stops short.

import "modules/helpers" as helpers;

// A function sees none of the script's own variables or constants, so the values the functions use are written out
// in them: the server is "contextos", a search returns at most 100000 paths, and a detail is clipped to 200
// characters.
const MAX_SEARCH = 100000;
const GRAPH_PAGE = 1000;
const REPORT_BUDGET = 60000;

// `value` as a whole number, whichever numeric form the input arrived in.
fn as_int(value) {
    if type_of(value) == "f64" { value.to_int() } else { value }
}

// The day number of a YYYY-MM-DD date (or the date part of a date-time), or () when it is not one.
fn day_of(value) {
    if type_of(value) != "string" || value.len() < 10 { return (); }
    if value.sub_string(4, 1) != "-" || value.sub_string(7, 1) != "-" { return (); }
    let y = 0;
    let m = 0;
    let d = 0;
    try {
        y = parse_int(value.sub_string(0, 4));
        m = parse_int(value.sub_string(5, 2));
        d = parse_int(value.sub_string(8, 2));
    } catch (err) {
        return ();
    }
    if m < 1 || m > 12 || d < 1 || d > 31 { return (); }
    let yy = if m <= 2 { y - 1 } else { y };
    let era = (if yy >= 0 { yy } else { yy - 399 }) / 400;
    let yoe = yy - era * 400;
    let doy = (153 * ((m + 9) % 12) + 2) / 5 + d - 1;
    era * 146097 + yoe * 365 + yoe / 4 - yoe / 100 + doy - 719468
}

fn clipped(text) {
    let copy = text;
    copy.trim();
    if copy.len() > 200 { copy.sub_string(0, 200) + "..." } else { copy }
}

fn finding(check, path, detail) {
    #{ check: check, path: path, detail: clipped(detail) }
}

// Whether every segment of `path` is lowercase letters, digits, and hyphens, starting with a letter or a digit, and
// the last ends in .md.
fn well_named(path) {
    if !path.ends_with(".md") { return false; }
    let stem = path.sub_string(0, path.len() - 3);
    for segment in stem.split("/") {
        if segment == "" { return false; }
        let first = true;
        for c in segment.chars() {
            let ok = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || (c == '-' && !first);
            if !ok { return false; }
            first = false;
        }
    }
    true
}

// The level of a Markdown heading line (1 to 6), or 0 when the line is not one.
fn heading_level(line) {
    let level = 0;
    for c in line.chars() {
        if c == '#' { level += 1; } else { break; }
    }
    if level == 0 || level > 6 || line.len() <= level || line.sub_string(level, 1) != " " { 0 } else { level }
}

// The notes under `dir` (vault-relative), sorted, leaving out the index.md files the server keeps. A folder the vault
// does not have holds none.
fn notes_under(vault, dir) {
    let result = ();
    try {
        result = call_mcp("contextos", "fs_search_files", #{ path: vault + "://" + dir, pattern: "**/*.md", max_results: 100000 });
    } catch (err) {
        if helpers::is_not_found(err) { return #{ paths: [], capped: false }; }
        throw err;
    }
    let paths = [];
    for rel in result.paths {
        let name = rel.split("/").pop();
        if name != "index.md" { paths.push(dir + "/" + rel); }
    }
    paths.sort();
    #{ paths: paths, capped: result.paths.len() >= 100000 }
}

// The findings in one note's body: the lines after its frontmatter, with every link expanded to a vault path.
fn body_findings(path, lines) {
    let found = [];
    let fenced = false;
    let in_questions = false;
    let questions_level = 0;
    for i in 0..lines.len() {
        let line = lines[i];
        let trimmed = line;
        trimmed.trim();
        if trimmed.starts_with("```") || trimmed.starts_with("~~~") { fenced = !fenced; continue; }
        if fenced { continue; }
        let level = heading_level(trimmed);
        if level > 0 {
            if in_questions && level <= questions_level { in_questions = false; }
            let next = i + 1;
            while next < lines.len() {
                let probe = lines[next];
                probe.trim();
                if probe != "" { break; }
                next += 1;
            }
            let empty = next >= lines.len();
            if !empty {
                let following = lines[next];
                following.trim();
                let next_level = heading_level(following);
                empty = next_level > 0 && next_level <= level;
            }
            if empty { found.push(finding("empty-heading", path, trimmed)); }
            if trimmed.to_lower() == "## open questions" { in_questions = true; questions_level = level; }
            continue;
        }
        if trimmed.to_lower().starts_with("**source:**") {
            found.push(finding("source-in-body", path, "line " + (i + 1) + ": move it to the frontmatter's sources"));
        }
        let at = trimmed.index_of("{{");
        if at >= 0 && trimmed.len() > at + 2 {
            let c = trimmed.sub_string(at + 2, 1).to_lower();
            if c >= "a" && c <= "z" && trimmed.index_of("}}", at) > at {
                found.push(finding("placeholder", path, trimmed));
            }
        }
        if in_questions && trimmed != "" && !trimmed.starts_with("<!--")
            && !trimmed.contains("/memory/tasks/") && !trimmed.contains("/memory/decisions/") {
            found.push(finding("open-question-unlinked", path, trimmed));
        }
    }
    found
}

let vault = inputs.vault;
let today = day_of(inputs.today);
let stale_days = if "stale_days" in inputs { as_int(inputs.stale_days) } else { 90 };
let proposed_days = if "proposed_days" in inputs { as_int(inputs.proposed_days) } else { 30 };
let wiki_statuses = ["active", "archived", "draft"];
let insight_statuses = ["proposed", "adopted", "dismissed"];
let confidences = ["low", "medium", "high"];

let findings = [];
let wiki = notes_under(vault, "memory/wiki");
let insights = notes_under(vault, "memory/insights");
for set in [["memory/wiki", wiki], ["memory/insights", insights]] {
    if set[1].capped {
        findings.push(finding("search-capped", set[0], "more than " + MAX_SEARCH + " notes; only the first were checked"));
    }
}

let notes = [];
for path in wiki.paths { notes.push(#{ path: path, insight: false }); }
for path in insights.paths { notes.push(#{ path: path, insight: true }); }

for note in notes {
    let path = note.path;
    if !well_named(path.sub_string(path.index_of("/") + 1)) {
        findings.push(finding("file-name", path, "use lowercase letters, digits, and hyphens"));
    }

    let fm = ();
    let body_start = 1;
    try {
        let read = call_mcp("contextos", "frontmatter_read", #{ path: vault + "://" + path, expand_links: true });
        fm = read.frontmatter;
        body_start = read.body_start_line;
    } catch (err) {
        findings.push(finding("frontmatter-unreadable", path, err.to_string()));
    }

    if fm != () && fm.len() == 0 {
        findings.push(finding("frontmatter-missing", path, "every note has frontmatter"));
    } else if fm != () {
        let sources = if "sources" in fm { fm.sources } else { () };
        if type_of(sources) == "string" { sources = [sources]; }
        if type_of(sources) != "array" || sources.len() == 0 {
            findings.push(finding("sources-missing", path, "list the note's sources in the frontmatter's sources"));
        } else {
            for source in sources {
                // A link value was expanded, and the link graph reports one that does not resolve; a plain path is
                // checked here.
                if type_of(source) != "string" || source.contains("[[") || source.contains("](") { continue; }
                let target = source;
                target.trim();
                if target.starts_with("/") { target = target.sub_string(1); }
                if target == "" || helpers::info_of(vault, target) == () {
                    findings.push(finding("source-unresolved", path, source));
                }
            }
        }

        let status = if "status" in fm { fm.status } else { () };
        let allowed = if note.insight { insight_statuses } else { wiki_statuses };
        if type_of(status) != "string" || !allowed.contains(status) {
            findings.push(finding("status-invalid", path, "status " + (if status == () { "missing" } else { status.to_string() })
                + "; allowed: " + allowed.reduce(|sum, s| if sum == "" { s } else { sum + ", " + s }, "")));
        }
        if note.insight && "confidence" in fm && fm.confidence != () {
            if type_of(fm.confidence) != "string" || !confidences.contains(fm.confidence) {
                findings.push(finding("confidence-invalid", path, "confidence " + fm.confidence.to_string() + "; allowed: low, medium, high"));
            }
        }

        if today != () {
            if !note.insight {
                let updated = if "updated" in fm { day_of(fm.updated) } else { () };
                if updated == () {
                    findings.push(finding("date-invalid", path, "updated is missing or not a YYYY-MM-DD date"));
                } else if today - updated >= stale_days {
                    findings.push(finding("stale", path, "updated " + fm.updated.to_string() + ", " + (today - updated) + " days ago"));
                }
            } else if status == "proposed" {
                let created = if "created" in fm { day_of(fm.created) } else { () };
                if created == () {
                    findings.push(finding("date-invalid", path, "created is missing or not a YYYY-MM-DD date"));
                } else if today - created >= proposed_days {
                    findings.push(finding("proposed-stale", path, "proposed since " + fm.created.to_string() + ", " + (today - created) + " days ago"));
                }
            }
        }
    }

    try {
        let read = call_mcp("contextos", "fs_attach_file", #{ path: vault + "://" + path, expand_links: true });
        let lines = read.content.split("\n");
        let start = if body_start > 0 { body_start - 1 } else { 0 };
        let body = if start < lines.len() { lines.extract(start) } else { [] };
        findings += body_findings(path, body);
    } catch (err) {
        findings.push(finding("unreadable", path, err.to_string()));
    }
}

// --- the link graph ------------------------------------------------------------------------------------------------
for set in [["memory/wiki", wiki], ["memory/insights", insights]] {
    if set[1].paths.len() == 0 { continue; }
    let offset = 0;
    loop {
        let page = call_mcp("contextos", "query_graph", #{ operation: "unresolved", vault: vault + "://.", path: vault + "://" + set[0],
            offset: offset, limit: GRAPH_PAGE });
        for link in page.links {
            if link.kind == "unreadable" {
                findings.push(finding("links-unreadable", link.source, link.text));
            } else {
                findings.push(finding("link-unresolved", link.source, "line " + link.line + ": " + link.text + " (" + link.kind + ")"));
            }
        }
        offset += page.links.len();
        if page.links.len() == 0 || offset >= page.total { break; }
    }
}
if notes.len() > 0 {
    let orphans = call_mcp("contextos", "query_graph", #{ operation: "orphans", vault: vault + "://." });
    for node in orphans.nodes {
        let p = node.path;
        if (p.starts_with("memory/wiki/") || p.starts_with("memory/insights/")) && !p.ends_with("/index.md") {
            findings.push(finding("orphan", p, "no links in or out"));
        }
    }
}

// --- the report ----------------------------------------------------------------------------------------------------
findings.sort(|a, b| if a.path < b.path { -1 } else if a.path > b.path { 1 } else if a.check < b.check { -1 }
    else if a.check > b.check { 1 } else { 0 });
let tally = #{};
for f in findings { tally[f.check] = if f.check in tally { tally[f.check] + 1 } else { 1 }; }
let checks = tally.keys();
checks.sort();
let counts = [];
for check in checks { counts.push(#{ check: check, count: tally[check] }); }

let listed = [];
let size = 0;
for f in findings {
    size += f.check.len() + f.path.len() + f.detail.len() + 40;
    if size > REPORT_BUDGET { break; }
    listed.push(f);
}

set_output("report", #{
    wiki_notes: wiki.paths.len(),
    insight_notes: insights.paths.len(),
    total_findings: findings.len(),
    truncated: listed.len() < findings.len(),
    counts: counts,
    findings: listed,
});
