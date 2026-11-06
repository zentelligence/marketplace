// Helpers both vault package workflows use. A module holds only functions, imports, and exported constants, so
// importing it runs nothing.

// The position of the last `needle` in `text`, or -1; Rhai strings have index_of only.
fn last_index(text, needle) {
    let at = -1;
    let next = text.index_of(needle);
    while next >= 0 {
        at = next;
        next = text.index_of(needle, at + 1);
    }
    at
}

// A copy of `text` with every `placeholder` replaced by `value`.
fn replaced(text, placeholder, value) {
    let copy = text;
    copy.replace(placeholder, value);
    copy
}

// Whether `err`, from a ContextOS call, says the path does not exist.
fn is_not_found(err) {
    let text = err.to_string();
    text.contains("not-found") || text.contains("not found")
}

// `path`'s file information in `vault`, or () when it does not exist. Asked directly rather than from a folder
// listing, because a listing leaves out the paths a vault hides, such as .contextos/.
fn info_of(vault, path) {
    try {
        return call_mcp("contextos", "fs_get_file_info", #{ path: vault + "://" + path });
    } catch (err) {
        if !is_not_found(err) { throw err; }
    }
    ()
}

// Whether `path` exists in `vault`.
fn exists_in(vault, path) { info_of(vault, path) != () }

// Raises `decision`, an entry of layout::DECISIONS, in `vault`'s register, which assigns its id. Returns that id, or ""
// when the register already holds a decision of that title.
fn raise_decision(vault, decision) {
    try {
        let record = call_mcp("contextos", "base_record_create", #{
            path: vault + "://memory/decisions.base",
            prefix: "VD",
            unique_fields: ["title"],
            frontmatter: #{ title: decision.title, description: decision.description, date: decision.date,
                status: "adopted", applies_to: decision.applies_to, superseded_by: () },
            content: workflow_file("templates/decisions/" + decision.slug + ".md").content,
        });
        return record.key;
    } catch (err) {
        if !err.to_string().contains("duplicate-record") { throw err; }
    }
    ""
}
