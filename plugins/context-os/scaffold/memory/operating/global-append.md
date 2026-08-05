## ContextOS active

Your personal knowledge vault is running. Core skills are available.

**Operations:**

| Command | Purpose |
| --- | --- |
| `vault init` | First-run setup: scaffold directory structure and personalise your vault |
| `vault ingest` | Process files from inbox/ into memory |
| `vault research` | Web research → memory/research/ → wiki |
| `vault query` | Answer questions from vault knowledge |
| `vault capture` | End-of-session memory capture |
| `vault consolidate` | Apply approved memory updates |
| `vault lint` | Audit wiki for quality issues |

**Source processing:**

| Command | Purpose |
| --- | --- |
| `vault distil-transcript` | Extract a conversational transcript to memory/raw/ |

**Registry (inline in any prompt):**

| Command | Purpose |
| --- | --- |
| `<slug>:role` | Adopt a role's cognitive posture for the session |
| `<slug>:hat` | Activate a hat's thinking mode for the current task |
| `<slug>:agent` | Delegate the task to an operator agent, run as a sub-agent |

**Registry:**

| Command | Purpose |
| --- | --- |
| `agent create <slug>` | Define a new operator agent in registry/agents/ |
| `hat create <slug>` | Define a new operator hat in registry/hats/ |
| `prompt create <slug>` | Define a new operator prompt in registry/prompts/ |
| `role create <slug>` | Define a new operator role in registry/roles/ |

Run `vault init` if you have not yet completed first-run setup.
