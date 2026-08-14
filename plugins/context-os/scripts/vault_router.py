#!/usr/bin/env python3
"""
vault_router.py: Deterministic command routing and pre-flight checks for the vault skill.

Parses the operator's command string, matches it to a sub-skill, performs a pre-flight
check (vault root accessible), reports whether `vault update` is recommended (installed
plugin version versus the vault's last-synced version in `.contextos/state.json`), and
returns a structured JSON result for the AI to act on.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_router.py --vault-root . --command "ingest"
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_router.py --vault-root . --command "vault ingest ~/Downloads/notes.md"
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_router.py --vault-root . --command "query what do I know about AI tools"
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_router.py --vault-root . --command "vault research zettelkasten"
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_router.py --vault-root . --command "vault init quick"

CLI flags:
    --vault-root PATH   Vault root directory (default: cwd).
    --command TEXT      Operator command string to route. Reads from stdin if omitted.

Output JSON fields:
    skill:            Matched skill name, or null if unmatched.
    skill_file:       Relative path to sub-skill file, or null.
    args:             Parsed arguments extracted from the command (e.g. files, topic, question).
    preflight:        Pre-flight check results (vault_root_ok, synced_plugin_version,
                      current_plugin_version, update_recommended).
    errors:           List of blocking error messages. Empty on success.
    warnings:         List of non-blocking advisories (e.g. `vault update` recommended).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vault_update import _load_state, _plugin_version  # noqa: E402


# ---------------------------------------------------------------------------
# Routing table
# ---------------------------------------------------------------------------

# Each entry: (regex pattern, skill name, skill file path)
ROUTES: list[tuple[str, str, str]] = [
    (r"vault\s+init|initialise\s+vault|initialize\s+vault|init\s+vault|quick\s+init|init\s+quick|^init$",
     "init", "skills/vault/init.md"),
    (r"vault\s+ingest|process\s+inbox|^ingest\b",
     "ingest", "skills/vault/ingest.md"),
    (r"vault\s+research|research\s+topic|find\s+sources|^research$",
     "research", "skills/vault/research.md"),
    (r"vault\s+query|query\s+vault|what\s+does\s+the\s+vault\s+say|what\s+do\s+i\s+know\s+about|^query$",
     "query", "skills/vault/query.md"),
    (r"vault\s+capture|end\s+of\s+session|session\s+capture|save\s+session|^capture$",
     "capture", "skills/vault/capture.md"),
    (r"vault\s+consolidate|consolidate|apply\s+memory\s+updates|apply\s+updates|^consolidate$",
     "consolidate", "skills/vault/consolidate.md"),
    (r"vault\s+lint|audit\s+vault|vault\s+audit|check\s+quality|^lint|^health$",
     "lint", "skills/vault/lint.md"),
    (r"vault\s+distil|distil\s+transcript|process\s+transcript|import\s+transcript|^distil$|^distil-transcript$",
     "distil-transcript", "skills/vault/distil-transcript.md"),
    (r"vault\s+log\b|^log\b",
     "log", "skills/vault/log.md"),
    (r"vault\s+update|update\s+vault|sync\s+vault|apply\s+plugin\s+update|^update$",
     "update", "skills/vault/update.md"),
]

# Argument extraction: skill -> (pattern to capture arg, arg key name)
ARG_PATTERNS: dict[str, tuple[str, str]] = {
    "ingest": (
        r"(?:vault\s+ingest|process\s+inbox|ingest)\s+(.+)",
        "files",
    ),
    "research": (
        r"(?:vault\s+research|research\s+topic|find\s+sources)\s+(.+)",
        "topic",
    ),
    "query": (
        r"(?:vault\s+query|query\s+vault|what\s+does\s+the\s+vault\s+say\s+about|query"
        r"|what\s+do\s+i\s+know\s+about)\s+(.+)",
        "question",
    ),
}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _parse_init_args(command: str) -> dict[str, str]:
    """Detect a `quick` mode flag anywhere in an init command (e.g. `vault init quick`,
    `quick init`, `init quick`). Absence means the full guided build-out.
    """
    if re.search(r"\bquick\b", command, re.IGNORECASE):
        return {"mode": "quick"}
    return {}


def _parse_log_args(command: str) -> dict[str, str]:
    """Extract `entry` and, if present, `files` from a `vault log ...` command.

    `files` is recognised as a trailing `files: <comma-separated list>` clause so
    the entry text itself may contain arbitrary prose. Case-preserving throughout.
    """
    m = re.search(r"(?:vault\s+log|^log)\s+(.+)", command, re.IGNORECASE)
    if not m:
        return {}

    remainder = m.group(1).strip()
    files_match = re.search(r"\bfiles:\s*(.+)$", remainder, re.IGNORECASE)

    args: dict[str, str] = {}
    if files_match:
        args["files"] = files_match.group(1).strip()
        entry = remainder[: files_match.start()].strip().rstrip("|").strip()
    else:
        entry = remainder

    if entry:
        args["entry"] = entry
    return args


def route_command(command: str) -> dict:
    """Match a command string to a skill.

    Returns a dict with keys: skill, skill_file, args.
    skill is None when no route matches.
    """
    command_stripped = command.strip()

    for pattern, skill_name, skill_file in ROUTES:
        if re.search(pattern, command_stripped, re.IGNORECASE):
            if skill_name == "log":
                args = _parse_log_args(command_stripped)
            elif skill_name == "init":
                args = _parse_init_args(command_stripped)
            else:
                args = {}
                if skill_name in ARG_PATTERNS:
                    arg_pattern, arg_key = ARG_PATTERNS[skill_name]
                    # Case-preserving: file paths and topics/questions may be case-sensitive.
                    m = re.search(arg_pattern, command_stripped, re.IGNORECASE)
                    if m and m.group(1):
                        args[arg_key] = m.group(1).strip()
            return {
                "skill": skill_name,
                "skill_file": skill_file,
                "args": args,
            }

    return {"skill": None, "skill_file": None, "args": {}}


# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------

def preflight(vault_root: Path, plugin_root: Path | None = None) -> dict:
    """Check vault root accessibility and whether `vault update` is recommended.

    `vault_root_ok` (CLAUDE.md exists) is the only hard-blocking check; a vault
    that has never run `vault update`, or is behind the installed plugin's
    version, is advisory only, since `vault_update.py`'s scaffold step is
    additive and safe to run at any time, and skills do not depend on a
    specific plugin version to function.

    Returns a dict with keys: vault_root_ok, synced_plugin_version,
    current_plugin_version, update_recommended, errors, warnings.
    """
    claude_md = vault_root / "CLAUDE.md"

    if not claude_md.exists():
        return {
            "vault_root_ok": False,
            "synced_plugin_version": None,
            "current_plugin_version": None,
            "update_recommended": False,
            "errors": [
                f"CLAUDE.md not found at {vault_root}. Run `/vault init` to scaffold the vault."
            ],
            "warnings": [],
        }

    if plugin_root is None:
        plugin_root = Path(__file__).parent.parent

    current_plugin_version = _plugin_version(plugin_root)
    synced_plugin_version = _load_state(vault_root).get("plugin_version")

    warnings: list[str] = []
    update_recommended = False

    if synced_plugin_version is None:
        update_recommended = True
        warnings.append(
            "No .contextos/state.json found. Run `vault update` to record the "
            "installed plugin version and pick up any scaffold content added "
            "since this vault was created."
        )
    elif current_plugin_version is not None and synced_plugin_version != current_plugin_version:
        update_recommended = True
        warnings.append(
            f"Vault last synced to plugin v{synced_plugin_version}; installed "
            f"plugin is v{current_plugin_version}. Run `vault update`."
        )

    return {
        "vault_root_ok": True,
        "synced_plugin_version": synced_plugin_version,
        "current_plugin_version": current_plugin_version,
        "update_recommended": update_recommended,
        "errors": [],
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(vault_root: Path, command: str, plugin_root: Path | None = None) -> dict:
    """Run pre-flight checks and route the command. Returns combined result dict."""
    pf = preflight(vault_root, plugin_root)
    route = route_command(command)

    errors = list(pf["errors"])

    # init is expected to run on a fresh vault where CLAUDE.md doesn't exist yet.
    if route["skill"] == "init":
        errors = [e for e in errors if "CLAUDE.md not found" not in e]

    if not route["skill"]:
        errors.append(f"No matching vault command found for: {command!r}")

    return {
        "skill": route["skill"],
        "skill_file": route["skill_file"],
        "args": route["args"],
        "preflight": {
            "vault_root_ok": pf["vault_root_ok"],
            "synced_plugin_version": pf["synced_plugin_version"],
            "current_plugin_version": pf["current_plugin_version"],
            "update_recommended": pf["update_recommended"],
        },
        "errors": errors,
        "warnings": pf["warnings"],
    }


def resolve_vault_root(vault_root_str: str) -> Path:
    """Resolve vault root, converting Windows paths to Linux paths where possible."""
    windows_match = re.match(r'^([A-Za-z]):[/\\](.*)', vault_root_str)
    if windows_match:
        drive = windows_match.group(1).lower()
        rest = windows_match.group(2).replace('\\', '/')

        candidates: list[Path] = [
            Path(f'/mnt/{drive}/{rest}'),
            Path(f'/{drive}/{rest}'),
        ]

        sessions_dir = Path('/sessions')
        if sessions_dir.is_dir():
            try:
                for session in sessions_dir.iterdir():
                    mnt = session / 'mnt'
                    if mnt.is_dir():
                        candidates.append(mnt / drive / rest)
            except PermissionError:
                pass

        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        return candidates[0]

    return Path(vault_root_str).expanduser().resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vault command router and pre-flight checker.")
    parser.add_argument("--vault-root", default=".", help="Vault root directory.")
    parser.add_argument(
        "--command", default=None,
        help="Command string to route. Reads from stdin if omitted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    command = args.command or sys.stdin.read().strip()

    if not command:
        print(json.dumps({"errors": ["No command provided."]}))
        sys.exit(1)

    vault_root = resolve_vault_root(args.vault_root)
    plugin_root = Path(__file__).parent.parent
    result = run(vault_root, command, plugin_root)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
