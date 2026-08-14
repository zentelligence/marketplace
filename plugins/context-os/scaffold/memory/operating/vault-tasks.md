# Vault Tasks

Central authoritative task register. 

## Fields

Description - Clear, simple, verb-oriented task statement

### Status

Multi-value field comprising icon demarcation and related values.

| Emoji | Meaning | Use |
| --- | --- | --- |
| ➕ | Created | Identified / added (YYYY-MM-DD) |
| ✅ | Completed | Closed - done (YYYY-MM-DD) |
| ❌ | Cancelled | Closed - not doing (YYYY-MM-DD) |
| 🛫 | Start-after | Soft activation (YYYY-MM-DD) |
| 🛬 | Finish-by | Soft deadline (YYYY-MM-DD) |
| ⏳ | Scheduled | Hard activation (YYYY-MM-DD) |
| 📅 | Due | Hard deadline (YYYY-MM-DD) |
| 🔁 | Recurring | Recurring pattern |
| ⛔ | Depends-on | Unable to start |
| 🚧 | Blocks | Prevents starting |

### Priority

Use sparingly. Reserve high priorities for genuine compliance or time-bound items.

| Icon | Priority |
| --- | --- |
| 🔺 | Highest, compliance, financial risk, overdue |
| ⏫ | High, critical, important, urgent |
| 🔼 | Medium, important, not urgent |
| (none) | Normal |
| 🔽 | Low, background, maintenance |

### Tags

| Tag | Meaning | Use |
| --- | --- | --- |
| `#next` | Clear, single step, can be done now | Default action type |
| `#waiting` | Handed off; blocked by external party | Include who/what you're waiting on in the text |
| `#errand` | Physical, batchable by location | Group on errand day |
| `#maybe` | Real but not this horizon | Review at meso boundary |

Plus, `#{{entity}}` associations, and `#vault` for vault maintenance tasks sourced from session capture.

### Notes

| Icon/Key | Meaning | Use |
| --- | --- | --- |
| ⛔ | Depends-on | Unable to start |
| 🚧 | Blocks | Prevents starting |
| 🏁 | On-completion | Post-completion handling |
| 🆔 | Related | Related actions, decisions, and projects |

