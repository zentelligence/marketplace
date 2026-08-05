# Skill: vault lint

---

## Purpose

Audit the wiki for quality issues. Produces a report only; no edits during the lint pass. The operator reviews the report and decides what to fix, either manually or by triggering targeted updates in a follow-up session.

---

## Triggers

```
vault lint | lint | audit vault | audit wiki | vault audit | check quality
```

---

## Tools required

`Read`, `Bash`

---

## Inputs

| Input | Source | Required |
| --- | --- | --- |
| `memory/wiki/` tree | Vault | Yes |
| `memory/index.md` and all wiki `index.md` files | Vault | Yes |
| `memory/insights/` tree | Vault | If present; skipped silently if the vault has no insight graph |
| `memory/operating/vault-conduct.md` | Vault | Yes |

---

## Outputs

| Output | Notes |
| --- | --- |
| Lint report | Presented in the session. Optionally written to vault if operator requests. |

---

## Flow

### Step 1: run the lint script

Run this as the first action of a fresh session, before any `Write`/`Edit` calls touch the vault. Cowork's Linux VM accesses the vault through a FUSE mount of the host filesystem; once a prior session in the same VM has overwritten files, the FUSE daemon can keep serving stale cached content to a later read in that same VM. A fresh session starts the daemon clean, so the scan reflects what is actually on disk rather than a stale cache.

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_lint.py --vault-root . --stale-days 90
```

The script scans both `memory/wiki/` and `memory/insights/` (if the latter
exists; skipped silently otherwise).

For JSON output (useful for programmatic handling):
```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_lint.py --vault-root . --json
```

### Step 1b: supplement with MCP graph checks (optional)

If MCP is available (see the vault router's MCP awareness section), also call `mcp__contextos__query_graph` with `operation: "orphans"` and, for any suspect article the script's broken-link check flagged, `operation: "backlinks"`, to cross-check the script's index.md-based structural checks against the server's wikilink graph. Surface any discrepancy between the two rather than silently preferring one source. This supplements Step 1; it never replaces it; the script remains the authoritative source for quality, citation, and staleness checks that the MCP catalogue does not cover.

### Step 2: review and present

Read the script output. Present the structured report to the operator covering:

1. **Structural issues:** missing indexes, broken links, orphaned articles, bad filenames (wiki and insights both).
2. **Quality issues:** missing sections, unresolved placeholders, empty headings, insight notes with an invalid `status` or `confidence` value.
3. **Citation issues:** missing Source: lines, broken source paths.
4. **Open questions flagged:** articles with `## Open Questions` content needing attention.
5. **Potentially stale articles:** articles not updated in 90+ days.
6. **Stale proposed insights:** insight notes still `status: proposed` after 30+ days, flagged for a decision to adopt or dismiss.
7. **Summary:** total articles, total insight notes, total issues, clean article count.

### Step 3: offer remediation paths

For each category of issues, suggest remediation:

- **Structural issues**: offer to create missing index.md files or fix broken links.
- **Quality issues**: offer a targeted `vault consolidate` to add missing sections.
- **Citation issues**: ask the operator to supply the correct source path.
- **Open questions**: ask whether to prioritise resolution in the next session.
- **Stale articles**: ask whether to refresh via `vault research` or manual update.
- **Stale proposed insights**: ask whether to adopt (promote to a working principle), dismiss, or leave pending with a reason.

No edits are made during the lint pass itself. All remediation happens in subsequent `vault consolidate` or `vault ingest` sessions.

---

## Checks performed by vault_lint.py

### Structural
- Every `index.md` at every level exists and has content beyond a stub.
- Every file referenced in an index.md actually exists at the listed path.
- No orphaned articles (articles with no index.md entry pointing to them).
- File names are lowercase-hyphenated.

### Article quality
- Every article has `## Key Takeaways`.
- Every article has a `**Source:**` line.
- No article has unresolved `{{...}}` placeholder strings.
- No article has invalid `status` values.

### Citation integrity
- Source paths in `**Source:**` lines resolve to actual files in `memory/raw/` or `memory/research/`.

### Staleness
- Articles not updated in 90+ days are flagged.

### Open questions
- Articles with `## Open Questions` content are flagged for operator attention.

### Insight graph (`memory/insights/`, skipped if it does not exist)
- Same structural checks as the wiki: `index.md` presence and link integrity, orphaned notes, lowercase-hyphenated filenames.
- Frontmatter: `status` must be one of `proposed`, `adopted`, `dismissed`; `confidence` (if set) must be one of `low`, `medium`, `high`. This is a different enum from wiki articles' `active`/`archived`/`draft` status, since insight notes follow a propose-then-decide lifecycle rather than a publish-then-archive one.
- Links inside a note's `## Relations` section resolve to real files.
- No unresolved `{{...}}` placeholder strings.
- `status: proposed` notes with a `created` date 30+ days old are flagged as stale-proposed, separately from the wiki's 90-day staleness check.

---

## Invariants

- No vault files are modified during the lint pass.
- The lint report is generated fresh on each run; it is not cached.
