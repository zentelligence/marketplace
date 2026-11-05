// The vault's layout, shared by the scaffold and update workflows: the folders every vault has, and the team and
// domains each scaffolded member is written with. A module holds only exported constants written out in full, so
// importing it runs nothing.

// Every folder a vault has from the start. The package writes no index.md: the ContextOS MCP server creates and
// maintains each folder's, so a folder that would otherwise hold no file is created empty for it to fill.
// memory/events/ is left out: only the server writes there, and it creates the folder with the first event.
export const FOLDERS = ["inbox", "journal", "memory", "memory/decisions", "memory/designs", "memory/entities",
    "memory/identity", "memory/insights", "memory/jobs", "memory/log", "memory/operating", "memory/raw",
    "memory/research", "memory/sessions", "memory/tasks", "memory/wiki", "notes", "outbox", "personal", "processed",
    "registry", "registry/agents", "registry/apps", "registry/events", "registry/hats", "registry/instructions",
    "registry/prompts", "registry/prompts/analysis", "registry/prompts/deciding", "registry/prompts/general",
    "registry/prompts/learning", "registry/prompts/planning", "registry/prompts/writing", "registry/roles",
    "registry/scripts", "registry/skills", "registry/workflows", "standards", "templates"];
export const TEAM = "general";
// Each member function's area of speciality in team.toml, one or two words. The operator and the chief of staff both
// hold "owner".
export const DOMAINS = #{ "chief-of-staff": "owner", librarian: "knowledge", technologist: "technology",
    support: "support", communications: "communications", assurance: "assurance" };
