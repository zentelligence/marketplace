#!/usr/bin/env python3
"""
vault_scaffold.py: ContextOS directory scaffolding script.

Creates the complete vault directory skeleton from the schema specification,
then seeds it with plugin-provided files (registry, templates, utility scripts,
design documents). Idempotent: existing directories and files are never overwritten.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_scaffold.py --vault-root PATH
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_scaffold.py --vault-root PATH --entity-slug mycompany --entity-name "My Company"
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_scaffold.py --vault-root PATH --dry-run

CLI flags:
    --vault-root PATH    Absolute path to the vault root. Required.
    --entity-slug SLUG   Slug for a business entity (e.g. 'zentelligence'). Optional.
    --entity-name NAME   Display name for the business entity. Optional.
    --dry-run            Print planned actions without writing files.
    --json               Emit results as JSON.

"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Stub file content definitions
# ---------------------------------------------------------------------------


def _stubs(vault_root: Path, entity_slug: str, entity_name: str) -> dict[str, str]:
    """Return a mapping of vault-relative path -> stub content for every scaffolded file."""
    today = datetime.now().strftime("%Y-%m-%d")

    return {
        # --- memory ---
        "memory/index.md": _dedent("""
            # Memory

            | Folder | Purpose | Entry point |
            | --- | --- | --- |
            | `decisions/` | One file per vault decision, indexed live via `decisions.base`. | [decisions/](decisions/index.md) |
            | `designs/` | Design artefacts and roadmaps. | [designs/](designs/index.md) |
            | `entities/` | Business entities and state. | [entities/](entities/index.md) |
            | `identity/` | Who the operator is. | [identity/](identity/index.md) |
            | `insights/` | Atomic claims and relations. | [insights/](insights/index.md) |
            | `log/` | Append-only operation log. | [log/](log/index.md) |
            | `operating/` | How the vault operates. | [operating/](operating/index.md) |
            | `questions/` | One file per open question, indexed live via `questions.base`. | [questions/](questions/index.md) |
            | `raw/` | Processed source extracts (immutable). | [raw/](raw/index.md) |
            | `research/` | AI-discovered sources (immutable). | [research/](research/index.md) |
            | `sessions/` | Per-session captures (append-only). | [sessions/](sessions/index.md) |
            | `wiki/` | Compiled topical knowledge. Citations required. | [wiki/](wiki/index.md) |

            ## Retrieval discipline

            Start at this file, descend to the relevant subfolder's `index.md`, then open 1 to 3 articles.
            Do not scan the full tree. Use `vault query` before navigating manually.
        """),
        "memory/glossary.md": _dedent("""
            # Glossary

            Common terms, nicknames, and abbreviations used in this vault.

            | Term | Meaning |
            | --- | --- |
            |  |  |
        """),
        # --- memory/designs ---
        "memory/designs/index.md": _dedent("""
            # Designs

            Design artefacts, roadmaps, and architectural decisions.

            | File | Purpose |
            | --- | --- |
            |  |  |
        """),
        # --- memory/identity ---
        "memory/identity/index.md": _dedent("""
            # Identity

            | File | Purpose |
            | --- | --- |
            | [identity.md](identity.md) | Core identity: name, location, values, interests. |
            | [who-am-i.md](who-am-i.md) | Compact self-description for Claude Settings. |
            | [voice-profile.md](voice-profile.md) | Messaging themes, on-brand examples, and discrimination rule. |
        """),
        "memory/identity/identity.md": _dedent("""
            # Identity

            ## Values

            ## Interests
        """),
        "memory/identity/who-am-i.md": _dedent("""
            # Who Am I

            ## What I do

            ## Current goals

            ## Core values

            ## Friction points

            ## Communication style

            ## Voice profile

            ## Anti-patterns
        """),
        "memory/identity/voice-profile.md": _dedent("""
            # Voice Profile

            ## Core messaging themes

            | Theme | Insight carried |
            | --- | --- |
            |  |  |

            ## On-brand examples

            ## Off-brand (actively avoid)

            ## The discrimination rule
        """),
        # --- memory/insights ---
        "memory/insights/index.md": _dedent("""
            # Insight Graph

            Atomic claims and relations. One file per insight. Zettelkasten-style semantic layer
            parallel to the wiki.

            | File | Title | Status |
            | --- | --- | --- |
        """),
        # --- memory/log ---
        "memory/log/index.md": _dedent("""
            # Log

            Append-only operation log. One file per day, created on the first operation of that day.

            | Folder | Contents |
            | --- | --- |
            | `YYYY/MM/` | Date-based log files: `YYYY-MM-DD.md` |

            Format: `HH:MM | <origin> | <operation> | <summary> | files: <list>`
        """),
        # --- memory/operating ---
        "memory/operating/index.md": _dedent("""
            # Operating

            | File | Purpose |
            | --- | --- |
            | [vault-conduct.md](vault-conduct.md) | Rules for writing and editing vault files. Load before writing. |
            | [vault-operations.md](vault-operations.md) | Log format and script reference. |
            | [vault-decisions.md](vault-decisions.md) | Decision-recording process. Decisions themselves live in `memory/decisions/`. |
            | [open-questions.md](open-questions.md) | Question-recording process. Questions themselves live in `memory/questions/`. |
            | [current-priorities.md](current-priorities.md) | Planning horizons and current priorities. |
            | [autonomy-policy.md](autonomy-policy.md) | What the agent may and may not do without sign-off. |
            | [anti-patterns.md](anti-patterns.md) | Execution, content, and conversational patterns to avoid. |
            | [global-instructions.md](global-instructions.md) | Comprehensive, self-contained Cowork paste block. |
        """),
        "memory/operating/current-priorities.md": _dedent("""
            # Current Priorities

            _Run `vault init` to populate this file with your planning horizons and priorities._
        """),
        "memory/operating/autonomy-policy.md": _dedent("""
            # Autonomy Policy

            _Run `vault init` to populate this file with your autonomy and control settings._
        """),
        "memory/operating/anti-patterns.md": _dedent("""
            # Anti-Patterns

            Patterns, framings, and outputs the agent must avoid. Both for the agent's own
            conduct and for any advice offered to the operator. Refined over time.

            ## Language and tone

            ## Structure

            ## Reasoning

            ## Advice

            ## Content generation
        """),
        "memory/operating/global-instructions.md": _dedent(f"""
            # Global Instructions

            Paste the block below into Cowork Settings, Edit Global Instructions on each device.

            `vault init` will generate this block with your actual vault path after the build-out.

            ---

            Generated: {today}
        """),
        # --- memory/entities ---
        "memory/entities/index.md": _dedent("""
            # Entities

            | Slug | Name | Description |
            | --- | --- | --- |
            | [personal](personal.md) | Personal | Personal entity |
        """),
        "memory/entities/personal.md": _dedent("""
            # Personal

            _Run `vault init` to populate this file._
        """),
        # --- memory/raw ---
        "memory/raw/index.md": _dedent("""
            # Raw

            Processed source extracts. Immutable after writing. Organised by year and month.

            | Folder | Contents |
            | --- | --- |
            | `YYYY/MM/` | Date-based extracts: `YYYY-MM-DD-<slug>.md` |
        """),
        # --- memory/research ---
        "memory/research/index.md": _dedent("""
            # Research

            AI-discovered sources. Immutable after writing. Organised by year and month.

            | Folder | Contents |
            | --- | --- |
            | `YYYY/MM/` | Date-based research files: `YYYY-MM-DD-<slug>.md` |
        """),
        # --- memory/sessions ---
        "memory/sessions/index.md": _dedent("""
            # Sessions

            Per-session captures. Append-only. Organised by year and month.

            | Folder | Contents |
            | --- | --- |
            | `YYYY/MM/` | Date-based captures: `YYYY-MM-DD-HHMM-<slug>.md` |
        """),
        # --- memory/wiki ---
        "memory/wiki/index.md": _dedent("""
            # Wiki

            Compiled topical knowledge. Multi-level: `memory/wiki/<domain>/<topic>/` minimum.
            Every level requires an `index.md`.

            | Domain | Entry point |
            | --- | --- |

            ## Conventions

            - Citations required. Every article has a `**Source:**` line.
            - `## Key Takeaways` required on every article. Bullets, scannable.
            - `## Open Questions` for gaps or unresolved contradictions.
            - Never invent claims. Flag unknowns explicitly.
        """),
        # --- notes ---
        "notes/index.md": _dedent("""
            # Notes

            Scratch notes. Obsidian-facing. Not authoritative. Do not cite in wiki articles.
        """),
        # --- inbox / processed / outbox (shared, vault-root; not per-entity) ---
        "inbox/index.md": _dedent("""
            # Inbox

            Drop zone for files to process, across all entities. Ephemeral: never cite
            content here directly, process it to memory/raw/ first.
        """),
        "processed/index.md": _dedent("""
            # Processed

            Files moved here after ingestion, across all entities.
        """),
        "outbox/index.md": _dedent("""
            # Outbox

            Outputs and artefacts ready for distribution or review, across all entities.
        """),
        # --- personal ---
        "personal/index.md": _dedent("""
            # Personal

            | Folder | Purpose |
            | --- | --- |
            | [projects/](projects/index.md) | Personal projects. |

            Inbox, processed, and outbox are shared across all entities: see
            `inbox/`, `processed/`, and `outbox/` at the vault root.
        """),
        "personal/projects/index.md": _dedent("""
            # Personal Projects

            | Slug | Name | Status | Description |
            | --- | --- | --- | --- |
        """),
        # --- registry ---
        "registry/index.md": _dedent("""
            # Registry

            Operator-curated reusable prompts, roles, hats, agents, and skills.

            | Folder | Purpose |
            | --- | --- |
            | [prompts/](prompts/index.md) | Saved prompt templates. |
            | [roles/](roles/index.md) | Cognitive-posture definitions. Selected per session. |
            | [hats/](hats/index.md) | Task-phase lenses. Activated per task, released when done. |
            | [agents/](agents/index.md) | Operator agent definitions. Delegated to as sub-agents. |
            | [skills/](skills/index.md) | Custom skill files. |
        """),
        "registry/prompts/index.md": _dedent("""
            # Prompts: Index

            Prompt library. Reusable assets organised by task category.

            | Path | Purpose |
            | --- | --- |
            | [framework.md](framework.md) | KERNEL+V principles and the standard XML prompt structure |
            | [general/](general/index.md) | Blank scaffold and uncategorised prompts |
            | [writing/](writing/index.md) | Emails, reports, documentation |
            | [analysis/](analysis/index.md) | Data interpretation, problem solving |
            | [planning/](planning/index.md) | Project scoping, task breakdown |
            | [learning/](learning/index.md) | Explaining concepts, skill development |
            | [deciding/](deciding/index.md) | Weighing options, identifying risks |

            Run `prompt draft <description>` to have Claude build a new prompt from a
            plain-language description, grounded in vault context. Run `prompt create
            <slug> in <category>` to author one directly, `prompt <slug>` to retrieve
            a saved one, or `prompt list` to browse.
        """),
        "registry/roles/index.md": _dedent("""
            # Roles: Index

            Cognitive-posture definitions. Selected by the operator per prompt. Not activated automatically.

            | Role | File | Cognitive signature |
            | --- | --- | --- |

            ## Usage

            In a prompt template, the Role goes in the Task field alongside the Hat:

            ```
            Task: As <Role>:role, wearing the <Hat>:hat, <specific task>.
            ```

            See [../prompts/framework.md](../prompts/framework.md) for the prompt structure.
            Run `role create <slug>` to define a new role.
        """),
        "registry/hats/index.md": _dedent("""
            # Hats: Index

            Task-phase lenses. Activated by the operator per task. Not auto-activated.

            | Hat | File | Purpose |
            | --- | --- | --- |

            ## Usage

            In a prompt template, the Hat goes in the Task field alongside the Role:

            ```
            Task: As <Role>:role, wearing the <Hat>:hat, <specific task>.
            ```

            See [../prompts/framework.md](../prompts/framework.md) for the prompt structure.
            Run `hat create <slug>` to define a new hat.
        """),
        "registry/agents/index.md": _dedent("""
            # Agents: Index

            Operator agent definitions. Delegated to as sub-agents via `<slug>:agent` in a
            task field. Not auto-activated.

            | Agent | Slug | Purpose |
            | --- | --- | --- |

            ## Usage

            In a prompt template, the Agent goes in the Task field:

            ```
            Task: Delegate <specific task> to <slug>:agent.
            ```

            See [../prompts/framework.md](../prompts/framework.md) for the prompt structure.
            Run `agent create <slug>` to define a new agent.
        """),
        "registry/skills/index.md": _dedent("""
            # Skills: Index

            Custom skill files extending the vault's capabilities. Selected per session, not auto-activated.

            | File | Skill | Purpose |
            | --- | --- | --- |

            Hats (task-phase lenses) live in [../hats/](../hats/index.md), not here.
        """),
        # --- standards ---
        "standards/index.md": _dedent("""
            # Standards

            Writing and engineering standards applied across vault work.

            | File | Purpose |
            | --- | --- |
        """),
        # --- templates ---
        "templates/index.md": _dedent("""
            # Templates

            Reusable file templates. Obsidian Templater-compatible.

            | File | Purpose |
            | --- | --- |
            | [daily-journal.md](daily-journal.md) | Daily note template. Use with Obsidian Templater. |
            | [unique-note.md](unique-note.md) | Unique note template. Use with Obsidian Templater. |
        """),
    }


def _entity_stubs(entity_slug: str, entity_name: str) -> dict[str, str]:
    """Return stub files for a named business entity."""
    return {
        f"{entity_slug}/index.md": _dedent(f"""
            # {entity_name}

            | Folder | Purpose |
            | --- | --- |
            | [projects/](projects/index.md) | Projects and initiatives. |

            Inbox, processed, and outbox are shared across all entities: see
            `inbox/`, `processed/`, and `outbox/` at the vault root.
        """),
        f"{entity_slug}/projects/index.md": _dedent(f"""
            # {entity_name} Projects

            | Slug | Name | Status | Description |
            | --- | --- | --- | --- |
        """),
        f"memory/entities/{entity_slug}.md": _dedent(f"""
            # {entity_name}

            _Run `vault init` to populate this file._
        """),
    }


def _dedent(text: str) -> str:
    """Strip leading blank line and common indent from a triple-quoted string."""
    lines = text.split("\n")
    # Remove leading blank line.
    if lines and not lines[0].strip():
        lines = lines[1:]
    # Remove trailing blank line.
    if lines and not lines[-1].strip():
        lines = lines[:-1]
    # Find minimum indent.
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        return "\n".join(lines)
    min_indent = min(len(ln) - len(ln.lstrip()) for ln in non_empty)
    return "\n".join(ln[min_indent:] for ln in lines) + "\n"


# ---------------------------------------------------------------------------
# Plugin files to seed into the vault
# ---------------------------------------------------------------------------

# Each entry is (plugin-relative source dir, vault-relative destination dir).
# Files are copied recursively and idempotently (skip if already present).
# Paths are relative to the plugin root (parent of this script's directory).
PLUGIN_COPY_DIRS = [
    ("scripts/utility", "scripts/utility"),
    ("scaffold/registry", "registry"),
    ("scaffold/templates", "templates"),
    ("scaffold/memory/designs", "memory/designs"),
    ("scaffold/memory/decisions", "memory/decisions"),
    ("scaffold/memory/questions", "memory/questions"),
]

# Individual plugin-provided files copied outside of PLUGIN_COPY_DIRS: either loose
# files at a scaffold/memory/ level that has no dedicated directory mapping
# (decisions.base, questions.base), or files inside memory/operating/ whose siblings
# are stub-generated by _stubs() rather than copied, so the directory as a whole is
# not eligible for PLUGIN_COPY_DIRS without clobbering those dynamic stubs.
PLUGIN_COPY_FILES = [
    ("scaffold/memory/operating/vault-decisions.md", "memory/operating/vault-decisions.md"),
    ("scaffold/memory/decisions.base", "memory/decisions.base"),
    ("scaffold/memory/operating/open-questions.md", "memory/operating/open-questions.md"),
    ("scaffold/memory/questions.base", "memory/questions.base"),
]


def _copy_plugin_dirs(
    plugin_root: Path,
    vault_root: Path,
    dry_run: bool,
    files_created: list,
    files_skipped: list,
) -> None:
    """Recursively copy plugin-provided seed files to the vault, idempotently."""
    for src_rel, dst_rel in PLUGIN_COPY_DIRS:
        src_dir = plugin_root / src_rel
        dst_dir = vault_root / dst_rel
        if not src_dir.exists():
            continue
        for src in sorted(src_dir.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(src_dir)
            dst = dst_dir / rel
            vault_rel = dst.relative_to(vault_root).as_posix()
            if dst.exists():
                files_skipped.append(vault_rel)
            else:
                if not dry_run:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
                files_created.append(vault_rel)


def _copy_plugin_files(
    plugin_root: Path,
    vault_root: Path,
    dry_run: bool,
    files_created: list,
    files_skipped: list,
) -> None:
    """Copy individually plugin-provided seed files to the vault, idempotently."""
    for src_rel, dst_rel in PLUGIN_COPY_FILES:
        src = plugin_root / src_rel
        if not src.exists():
            continue
        dst = vault_root / dst_rel
        if dst.exists():
            files_skipped.append(dst_rel)
        else:
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            files_created.append(dst_rel)


# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------

DIRECTORIES = [
    "inbox",
    "memory/decisions",
    "memory/designs",
    "memory/entities",
    "memory/identity",
    "memory/insights",
    "memory/log",
    "memory/operating",
    "memory/questions",
    "memory/raw",
    "memory/research",
    "memory/sessions",
    "memory/wiki",
    "notes",
    "outbox",
    "personal/projects",
    "processed",
    "registry/agents",
    "registry/hats",
    "registry/prompts",
    "registry/roles",
    "registry/skills",
    "scripts/utility",
    "standards",
    "templates",
]

ENTITY_DIRECTORIES = [
    "{slug}/projects",
    "memory/entities/{slug}",
]


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------


def scaffold(
    vault_root: Path,
    entity_slug: str = "",
    entity_name: str = "",
    dry_run: bool = False,
) -> dict:
    """Create vault directory structure and stub files.

    Idempotent: existing directories and files are never overwritten.

    Returns a dict with keys: directories_created, files_created, files_skipped.
    """
    dirs_created: list[str] = []
    files_created: list[str] = []
    files_skipped: list[str] = []

    # Step 1: Create directories.
    all_dirs = list(DIRECTORIES)
    if entity_slug:
        all_dirs += [d.format(slug=entity_slug) for d in ENTITY_DIRECTORIES]

    for rel_dir in all_dirs:
        abs_dir = vault_root / rel_dir
        if not abs_dir.exists():
            if not dry_run:
                abs_dir.mkdir(parents=True, exist_ok=True)
            dirs_created.append(rel_dir)

    # Step 2: Copy plugin-provided seed files before creating stubs, so plugin
    # content takes precedence over stub fallbacks for overlapping paths.
    plugin_root = Path(__file__).parent.parent
    _copy_plugin_dirs(
        plugin_root=plugin_root,
        vault_root=vault_root,
        dry_run=dry_run,
        files_created=files_created,
        files_skipped=files_skipped,
    )
    _copy_plugin_files(
        plugin_root=plugin_root,
        vault_root=vault_root,
        dry_run=dry_run,
        files_created=files_created,
        files_skipped=files_skipped,
    )

    # Step 3: Create stub files for anything not yet present.
    stubs = _stubs(vault_root, entity_slug, entity_name)
    if entity_slug and entity_name:
        stubs.update(_entity_stubs(entity_slug, entity_name))

    for rel_path, content in stubs.items():
        abs_path = vault_root / rel_path
        if abs_path.exists():
            files_skipped.append(rel_path)
        else:
            if not dry_run:
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_text(content, encoding="utf-8")
            files_created.append(rel_path)

    return {
        "directories_created": dirs_created,
        "files_created": files_created,
        "files_skipped": files_skipped,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ContextOS directory scaffolding script."
    )
    parser.add_argument("--vault-root", required=True, help="Vault root directory.")
    parser.add_argument(
        "--entity-slug", default="", help="Entity slug (e.g. 'zentelligence')."
    )
    parser.add_argument("--entity-name", default="", help="Entity display name.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print planned actions without writing."
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help="Emit results as JSON."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vault_root = Path(args.vault_root).expanduser().resolve()
    if not vault_root.exists():
        if not args.dry_run:
            vault_root.mkdir(parents=True, exist_ok=True)

    result = scaffold(
        vault_root=vault_root,
        entity_slug=args.entity_slug,
        entity_name=args.entity_name,
        dry_run=args.dry_run,
    )

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        prefix = "[dry-run] " if args.dry_run else ""
        for d in result["directories_created"]:
            print(f"{prefix}created dir:  {d}/")
        for f in result["files_created"]:
            print(f"{prefix}created file: {f}")
        for f in result["files_skipped"]:
            print(f"skipped (exists): {f}")
        print(
            f"\n{prefix}Done. "
            f"{len(result['directories_created'])} directories, "
            f"{len(result['files_created'])} files created, "
            f"{len(result['files_skipped'])} skipped."
        )


if __name__ == "__main__":
    main()
