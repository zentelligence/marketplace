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
| `health` | `/vault health` |
| `distil` | `/vault distil transcript [files]` |
| `query` | `/vault query <question>` |
| `log` | `/vault log <entry>` |
| `update` | `/vault update` |

---

## Daily log stub

The first operation of a day creates `memory/log/YYYY/MM/YYYY-MM-DD.md` with:

```markdown
# Log: YYYY-MM-DD

```

Then append the first entry on the next line.

---

## Workflow references

The deterministic steps run as the `contextos-vault` package's workflows, as saved shared jobs under ContextOS Web, with no tokens spent on the work itself. They are not copied into the vault.

| Workflow | Purpose | Used by |
| --- | --- | --- |
| `contextos-vault` `scaffold` workflow | Directory scaffolding and the team, run by ContextOS Web | `/vault init` |
| `contextos-vault` `update` workflow | Sync the vault against the installed plugin version, run by ContextOS Web | `/vault update` |
| `contextos-vault` `health` workflow | Check wiki and insight quality, reading only, run by ContextOS Web | `/vault health` |
