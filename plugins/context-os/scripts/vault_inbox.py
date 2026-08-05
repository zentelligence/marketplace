#!/usr/bin/env python3
"""
vault_inbox.py: Archive a processed inbox file to processed/ and update indexes.

Moves a file from inbox/<filename> to processed/<filename>, removes its row from
the inbox index.md (if present), and appends a row to the processed index.md.
inbox/ and processed/ are shared vault-root folders, not scoped per entity; entity
attribution for a file's content is determined separately, during ingest, not by
its location in inbox/. Idempotent on indexes; safe to re-run after a partial
failure.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_inbox.py --vault-root . --file report.md
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_inbox.py --vault-root . --file brief.md --dry-run

CLI flags:
    --vault-root PATH       Vault root directory. Required.
    --file FILENAME         Filename to archive from inbox to processed. Required.
    --dry-run               Print planned actions without moving any files.
    --json                  Emit result as JSON.

"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

INDEX_FILENAME = "index.md"


# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------

def _remove_table_row(index_path: Path, file_name: str) -> None:
    """Remove the row for file_name from the index table. No-op if absent."""
    if not index_path.exists():
        return
    lines = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
    filtered = [ln for ln in lines if f"[{file_name}]" not in ln]
    if len(filtered) != len(lines):
        index_path.write_text("".join(filtered), encoding="utf-8")


def _append_table_row(index_path: Path, file_name: str, date: str) -> None:
    """Append an archive row to the processed index, creating the table if absent."""
    content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    row = f"| [{file_name}]({file_name}) | {date} |"

    # Idempotent: skip if row already present.
    if f"[{file_name}]" in content:
        return

    if "| --- |" in content:
        # Table already exists: append row.
        content = content.rstrip("\n") + f"\n{row}\n"
    else:
        # No table yet: append header then row.
        header = "| File | Archived |\n| --- | --- |"
        content = content.rstrip("\n") + f"\n\n{header}\n{row}\n"

    index_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Core operation
# ---------------------------------------------------------------------------

def archive_file(
    vault_root: Path,
    file_name: str,
    dry_run: bool = False,
) -> dict:
    """Move a file from inbox/ to processed/ and update indexes.

    Returns a result dict with keys: moved, source, destination,
    inbox_index_updated, processed_index_updated, dry_run, errors.
    """
    inbox_path = vault_root / "inbox" / file_name
    processed_dir = vault_root / "processed"
    processed_path = processed_dir / file_name
    inbox_index = vault_root / "inbox" / INDEX_FILENAME
    processed_index = processed_dir / INDEX_FILENAME

    if not inbox_path.exists():
        return {
            "moved": False,
            "errors": [f"File not found in inbox: inbox/{file_name}"],
        }

    if processed_path.exists():
        return {
            "moved": False,
            "errors": [f"Destination already exists: processed/{file_name}"],
        }

    today = datetime.now().strftime("%Y-%m-%d")

    if not dry_run:
        processed_dir.mkdir(parents=True, exist_ok=True)
        inbox_path.rename(processed_path)
        _remove_table_row(inbox_index, file_name)
        _append_table_row(processed_index, file_name, today)

    return {
        "moved": True,
        "source": f"inbox/{file_name}",
        "destination": f"processed/{file_name}",
        "inbox_index_updated": f"inbox/{INDEX_FILENAME}",
        "processed_index_updated": f"processed/{INDEX_FILENAME}",
        "dry_run": dry_run,
        "errors": [],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive a processed inbox file to processed/ and update indexes."
    )
    parser.add_argument("--vault-root", required=True, help="Vault root directory.")
    parser.add_argument("--file", required=True, help="Filename to archive from inbox.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without moving files.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit JSON output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vault_root = Path(args.vault_root).expanduser().resolve()

    if not vault_root.exists():
        print(json.dumps({"error": f"Vault root does not exist: {vault_root}"}))
        sys.exit(1)

    result = archive_file(vault_root, args.file, dry_run=args.dry_run)

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["errors"]:
            sys.exit(1)
        return

    if result["errors"]:
        for e in result["errors"]:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if result.get("dry_run"):
        print(f"DRY RUN: {result['source']} → {result['destination']}")
    else:
        print(f"Archived: {result['source']} → {result['destination']}")


if __name__ == "__main__":
    main()
