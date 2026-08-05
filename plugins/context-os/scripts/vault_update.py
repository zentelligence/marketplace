#!/usr/bin/env python3
"""
vault_update.py: Sync a vault's shipped content against the installed plugin version.

Run after upgrading the context-os plugin to bring an existing vault back in step
with it: adds any new scaffold directories, stub files, or plugin-provided seed
files introduced since the vault was created or last updated (by delegating to
`vault_scaffold.scaffold()`, which is already idempotent and additive), then
refreshes plugin-shipped "replaceable" files (registry index scaffolds, templates,
`memory/designs/`, `scripts/utility/`) that changed upstream and that the operator
has not edited locally.

A file the operator has edited locally is never silently overwritten, even if the
plugin's copy has also changed; it is reported as a conflict for manual review.
Detecting "has the operator edited this" requires a baseline, so the first run
against any given vault only records baselines (plus whatever `scaffold()` adds);
it does not overwrite anything. Subsequent runs can then tell an untouched file
(safe to refresh) from an edited one (never touched automatically).

State lives in `.contextos/state.json` at the vault root: the plugin version last
synced, the timestamp of that sync, and a SHA-256 hash of each shipped file as last
written by the plugin, keyed by vault-relative path.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_update.py --vault-root PATH
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_update.py --vault-root PATH --dry-run
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_update.py --vault-root PATH --json

CLI flags:
    --vault-root PATH   Absolute path to the vault root. Required.
    --dry-run           Report planned actions without writing files.
    --json              Emit results as JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vault_scaffold import PLUGIN_COPY_DIRS, scaffold  # noqa: E402

STATE_DIR = ".contextos"
STATE_FILE = "state.json"


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def _hash_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_state(vault_root: Path) -> dict:
    """Load `.contextos/state.json`, or a fresh default structure if absent or invalid."""
    state_path = vault_root / STATE_DIR / STATE_FILE
    if not state_path.exists():
        return {"plugin_version": None, "last_update": None, "synced_files": {}}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"plugin_version": None, "last_update": None, "synced_files": {}}
    state.setdefault("synced_files", {})
    return state


def _save_state(vault_root: Path, state: dict, dry_run: bool) -> None:
    """Write state back to `.contextos/state.json`, creating the directory if needed."""
    if dry_run:
        return
    state_dir = vault_root / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / STATE_FILE
    state_path.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _plugin_version(plugin_root: Path) -> str | None:
    """Read the installed plugin's own version from its manifest."""
    manifest = plugin_root / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


def refresh_shipped_files(
    plugin_root: Path,
    vault_root: Path,
    state: dict,
    dry_run: bool,
) -> dict:
    """Diff plugin-shipped replaceable files against the vault and apply safe updates.

    Compares each file's current hash against the last-synced hash recorded in
    `state["synced_files"]` to distinguish an operator edit from an upstream
    change. A file with no recorded baseline is only baselined this run, never
    overwritten. `state` is mutated in place.

    Returns a dict with keys: updated, unchanged, conflicts (each a list of
    vault-relative paths). Files that do not yet exist in the vault are skipped;
    `scaffold()` is responsible for adding those.
    """
    synced: dict = state["synced_files"]
    updated: list[str] = []
    unchanged: list[str] = []
    conflicts: list[str] = []

    for src_rel, dst_rel in PLUGIN_COPY_DIRS:
        src_dir = plugin_root / src_rel
        dst_dir = vault_root / dst_rel
        if not src_dir.exists():
            continue

        for src_file in sorted(src_dir.rglob("*")):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(src_dir)
            dst_file = dst_dir / rel
            if not dst_file.exists():
                continue  # scaffold() handles files that don't exist yet.

            vault_rel = dst_file.relative_to(vault_root).as_posix()
            src_hash = _hash_file(src_file)
            dst_hash = _hash_file(dst_file)
            recorded_hash = synced.get(vault_rel)

            if recorded_hash is None:
                # No baseline yet: record current state without overwriting.
                synced[vault_rel] = dst_hash
                (unchanged if dst_hash == src_hash else conflicts).append(vault_rel)
                continue

            operator_edited = dst_hash != recorded_hash
            plugin_changed = src_hash != recorded_hash

            if not operator_edited and plugin_changed:
                if not dry_run:
                    shutil.copyfile(src_file, dst_file)
                synced[vault_rel] = src_hash
                updated.append(vault_rel)
            elif operator_edited and plugin_changed and dst_hash != src_hash:
                conflicts.append(vault_rel)
            else:
                # Neither side changed, or the operator's edit already matches
                # the new plugin content.
                if dst_hash == src_hash:
                    synced[vault_rel] = src_hash
                unchanged.append(vault_rel)

    return {"updated": updated, "unchanged": unchanged, "conflicts": conflicts}


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def update(vault_root: Path, plugin_root: Path, dry_run: bool = False) -> dict:
    """Run the full update: add new scaffold content, then refresh shipped files.

    Returns a dict with keys: plugin_version, directories_created, files_added,
    files_updated, files_unchanged, conflicts.
    """
    scaffold_result = scaffold(vault_root, dry_run=dry_run)

    state = _load_state(vault_root)
    refresh_result = refresh_shipped_files(plugin_root, vault_root, state, dry_run)

    state["plugin_version"] = _plugin_version(plugin_root)
    state["last_update"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _save_state(vault_root, state, dry_run)

    return {
        "plugin_version": state["plugin_version"],
        "directories_created": scaffold_result["directories_created"],
        "files_added": scaffold_result["files_created"],
        "files_updated": refresh_result["updated"],
        "files_unchanged": refresh_result["unchanged"],
        "conflicts": refresh_result["conflicts"],
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync a vault's shipped content against the installed plugin version."
    )
    parser.add_argument("--vault-root", required=True, help="Vault root directory.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Report planned actions without writing."
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help="Emit results as JSON."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vault_root = Path(args.vault_root).expanduser().resolve()
    if not vault_root.exists():
        print(json.dumps({"errors": [f"Vault root does not exist: {vault_root}"]}))
        sys.exit(1)

    plugin_root = Path(__file__).parent.parent
    result = update(vault_root, plugin_root, dry_run=args.dry_run)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        prefix = "[dry-run] " if args.dry_run else ""
        print(f"{prefix}Plugin version: {result['plugin_version']}")
        for d in result["directories_created"]:
            print(f"{prefix}created dir:  {d}/")
        for f in result["files_added"]:
            print(f"{prefix}added file:   {f}")
        for f in result["files_updated"]:
            print(f"{prefix}updated file: {f}")
        if result["conflicts"]:
            print(f"\n{prefix}Conflicts (locally modified, not overwritten):")
            for f in result["conflicts"]:
                print(f"  {f}")
        print(
            f"\n{prefix}Done. "
            f"{len(result['directories_created'])} directories, "
            f"{len(result['files_added'])} files added, "
            f"{len(result['files_updated'])} files updated, "
            f"{len(result['conflicts'])} conflicts."
        )


if __name__ == "__main__":
    main()
