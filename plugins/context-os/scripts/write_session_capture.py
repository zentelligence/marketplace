#!/usr/bin/env python3
"""
write_session_capture.py: Write a consistently structured ContextOS session capture.

Creates a session capture file at memory/sessions/YYYY/MM/YYYY-MM-DD-HHMM-<slug>.md.
The file records decisions, outcomes, open threads, and proposed memory updates from
the session. Proposes updates only; never applies them directly.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/write_session_capture.py --vault-root PATH --slug my-session --outcome "..."

CLI flags:
    --vault-root PATH         Vault root directory.
    --slug SLUG               Session slug. Required.
    --session-type TYPE       Session type (e.g. 'planning', 'research', 'build'). Optional.
    --primary-role ROLE       Primary AI role used in the session. Optional.
    --primary-hats LIST       Comma-separated hats (e.g. 'analyst,engineer'). Optional.
    --entities-touched LIST   Comma-separated entity slugs touched. Optional.
    --projects-touched LIST   Comma-separated project slugs touched. Optional.
    --outcome TEXT            Outcome paragraph. Required.
    --decision TEXT           Decision bullet. Repeatable.
    --open-thread TEXT        Open thread bullet. Repeatable.
    --memory-update TEXT      Proposed memory update bullet. Repeatable.
    --coding-lesson-file PATH Optional coding lesson file path.
    --timestamp STAMP         Optional timestamp in YYYY-MM-DD-HHMM form. Defaults to now.

"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


def slugify(value: str) -> str:
    """Convert a string to a lowercase-hyphenated slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "session"


def yaml_list(value: str) -> str:
    """Convert a comma-separated string to a YAML inline list."""
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        return "[]"
    return "[" + ", ".join(f'"{item}"' for item in items) + "]"


def bullet_lines(items: list[str], empty: str) -> str:
    """Format a list of items as markdown bullet lines."""
    clean = [item.strip() for item in items if item.strip()]
    if not clean:
        return f"- {empty}\n"
    return "".join(f"- {item}\n" for item in clean)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a session capture file in memory/sessions/."
    )
    parser.add_argument("--vault-root", default=".", help="Vault root directory.")
    parser.add_argument("--slug", required=True, help="Session slug.")
    parser.add_argument("--session-type", default="", help="Session type.")
    parser.add_argument("--primary-role", default="", help="Primary AI role.")
    parser.add_argument("--primary-hats", default="", help="Comma-separated hats.")
    parser.add_argument(
        "--entities-touched", default="", help="Comma-separated entity slugs."
    )
    parser.add_argument(
        "--projects-touched", default="", help="Comma-separated project slugs."
    )
    parser.add_argument("--outcome", required=True, help="Outcome paragraph.")
    parser.add_argument(
        "--decision", action="append", default=[], help="Decision bullet. Repeatable."
    )
    parser.add_argument(
        "--open-thread",
        action="append",
        default=[],
        help="Open thread bullet. Repeatable.",
    )
    parser.add_argument(
        "--memory-update",
        action="append",
        default=[],
        help="Proposed memory update bullet. Repeatable.",
    )
    parser.add_argument(
        "--coding-lesson-file", help="Optional coding lesson file path."
    )
    parser.add_argument(
        "--timestamp",
        help="Timestamp in YYYY-MM-DD-HHMM form. Defaults to local now.",
    )
    return parser.parse_args()


def render_datetime(value: str | None) -> tuple[datetime, str, str, str, str]:
    """Parse timestamp or use now. Returns (dt, year, month, date, stamp)."""
    if value:
        dt = datetime.strptime(value, "%Y-%m-%d-%H%M")
    else:
        dt = datetime.now().astimezone()
    return (
        dt,
        dt.strftime("%Y"),
        dt.strftime("%m"),
        dt.strftime("%Y-%m-%d"),
        dt.strftime("%Y-%m-%d-%H%M"),
    )


def main() -> None:
    args = parse_args()
    _, year, month, _, stamp = render_datetime(args.timestamp)

    vault_root = Path(args.vault_root).expanduser().resolve()
    session_dir = vault_root / "memory" / "sessions" / year / month
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / f"{stamp}-{slugify(args.slug)}.md"

    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing session capture: {path}")

    lesson_section = ""
    if args.coding_lesson_file:
        lesson_section = f"\n## Coding lesson\n\n- {args.coding_lesson_file.strip()}\n"

    content = f"""---
session_type: "{args.session_type.strip()}"
primary_role: "{args.primary_role.strip()}"
primary_hats: {yaml_list(args.primary_hats)}
entities_touched: {yaml_list(args.entities_touched)}
projects_touched: {yaml_list(args.projects_touched)}
created: {stamp}
---

## Outcome

{args.outcome.strip()}

## Decisions

{bullet_lines(args.decision, "None recorded.")}
## Open threads

{bullet_lines(args.open_thread, "None recorded.")}
## Memory updates proposed

{bullet_lines(args.memory_update, "None proposed.")}{lesson_section}"""

    path.write_text(content, encoding="utf-8")
    print(path.relative_to(vault_root).as_posix())


if __name__ == "__main__":
    main()
