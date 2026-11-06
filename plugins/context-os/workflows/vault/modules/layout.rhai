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
// The decisions the plugin itself makes about how a vault works. Each body is templates/decisions/<slug>.md, and each
// is raised through the register, so the vault's own counter gives it its id; nothing ships a fixed id. A decision is
// raised once and then belongs to the vault: correct one by adding another that supersedes it, and never edit its title,
// which is how a vault that already holds it is recognised. This list's order is the order decisions are raised in, and
// so the order of their ids in every vault; the slugs carry no order. Only ever append, keeping dates ascending.
export const DECISIONS = [
    #{ slug: "one-register",
        title: "Vault decisions and questions share one register, and it covers only the vault itself",
        description: "Decisions and questions about the vault's own design and operation live together in memory/decisions/; the operator's decisions and questions about their own work are tasks.",
        date: "2026-10-08",
        applies_to: ["memory/decisions/", "memory/decisions.base", "memory/operating/vault-decisions.md",
            "templates/registry-vault-decision.md", "templates/registry-vault-question.md", "memory/tasks/"] },
];

export const TEAM = "general";
// Each member function's area of speciality in team.toml, one or two words. The operator and the chief of staff both
// hold "owner".
export const DOMAINS = #{ "chief-of-staff": "owner", librarian: "knowledge", technologist: "technology",
    support: "support", communications: "communications", assurance: "assurance" };
