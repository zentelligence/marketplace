# Vault Operations

Log format and operation index for ContextOS.

---

## Log format

Every vault operation appends to `memory/log/YYYY/MM/YYYY-MM-DD.md`. The date is carried by the file path and the daily stub header alone; entries do not repeat it.

**Format:**
```
HH:MM | <origin> | <operation> | <summary> | files: <comma-separated list>
```

See `vault-conduct.md`'s Log format section for what `<origin>` (`manual`, `agent`, or an MCP tool name) means.

**`vault` Operations:**

| Operation | Triggered by |
| --- | --- |
| `init` | `/vault init [quick]` |
| `ingest` | `/vault ingest [files]` |
| `research` | `/vault research <topic>` |
| `capture` | `/vault capture` |
| `consolidate` | `/vault consolidate` |
| `lint` | `/vault lint` |
| `distil` | `/vault distil transcript [files]` |
| `query` | `/vault query <question>` |
| `log` | `/vault log <entry>` |
| `update` | `/vault update` |

---

## Daily log stub

When the first operation of a day runs, create `memory/log/YYYY/MM/YYYY-MM-DD.md` with:

```markdown
# Log: YYYY-MM-DD

```

Then append the first entry on the next line.

---

## Script references

| Script | Purpose | CLI |
| --- | --- | --- |
| `scripts/vault_query.py` | Vault retrieval | `python scripts/vault_query.py --vault-root . --input-json '...'` |
| `scripts/vault_scaffold.py` | Directory scaffolding | `python scripts/vault_scaffold.py --vault-root .` |
| `scripts/copy_markdown_to_raw.py` | Copy source to raw | `python scripts/copy_markdown_to_raw.py --vault-root . --source path/to/file.md` |
| `scripts/update_wiki_index.py` | Update wiki indexes | `python scripts/update_wiki_index.py --vault-root . --touched path/to/article.md` |
| `scripts/write_session_capture.py` | Write session capture | `python scripts/write_session_capture.py --vault-root . --slug my-session --outcome "..."` |
| `scripts/vault_lint.py` | Audit wiki quality | `python scripts/vault_lint.py --vault-root . [--json]` |
| `scripts/vault_update.py` | Sync vault against installed plugin version | `python scripts/vault_update.py --vault-root . [--dry-run] [--json]` |
