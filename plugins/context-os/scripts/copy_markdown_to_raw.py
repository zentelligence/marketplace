#!/usr/bin/env python3
"""Copy a Markdown source into memory/raw/ with deterministic frontmatter.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/copy_markdown_to_raw.py --vault-root PATH --source path/to/file.md
    python $CLAUDE_PLUGIN_ROOT/scripts/copy_markdown_to_raw.py --vault-root PATH --source path/to/file.md --slug my-slug

CLI flags:
    --vault-root PATH   Vault root directory.
    --source PATH       Source Markdown file to copy.
    --slug SLUG         Output slug. Defaults to source heading or filename.
    --origin TITLE      Origin title. Defaults to first heading or filename.
    --summary TEXT      One-line summary. Defaults to a source-copy description.
    --captured DATE     Capture date in YYYY-MM-DD form. Defaults to today.
    --type TYPE         Source type: document | transcript | export | note | other. Default: document.
    --domain DOMAIN     Best-fit wiki domain. Optional.

"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<frontmatter>.*?)\n---\s*\n?", re.DOTALL)

VALID_TYPES = ("document", "transcript", "export", "note", "other")


def slugify(value: str) -> str:
    """Convert a string to a lowercase-hyphenated slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "source"


def first_heading_or_name(source_path: Path, body: str) -> str:
    """Return the first Markdown heading from body, or the filename stem."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or source_path.stem
    return source_path.stem


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """Split a Markdown file into existing frontmatter lines and body."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [], text
    existing = [
        line for line in match.group("frontmatter").splitlines() if line.strip()
    ]
    return existing, text[match.end() :]


def merge_frontmatter(required: dict[str, str], existing: list[str]) -> str:
    """Merge required frontmatter fields with any additional existing fields.

    Required fields always appear first and override existing values for the
    same key. Additional existing fields are appended verbatim.
    """
    required_keys = set(required)
    lines = ["---"]
    for key, value in required.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}: "{escaped}"')
    for line in existing:
        key = line.split(":", 1)[0].strip()
        if key and key not in required_keys:
            lines.append(line)
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a Markdown source into memory/raw/ with deterministic frontmatter."
    )
    parser.add_argument("--vault-root", default=".", help="Vault root directory.")
    parser.add_argument("--source", required=True, help="Source Markdown file path.")
    parser.add_argument(
        "--slug", help="Output slug. Defaults to source heading or filename."
    )
    parser.add_argument(
        "--origin", help="Origin title. Defaults to first heading or filename."
    )
    parser.add_argument("--summary", help="One-line summary.")
    parser.add_argument(
        "--captured", help="Capture date in YYYY-MM-DD form. Defaults to today."
    )
    parser.add_argument(
        "--type",
        dest="source_type",
        default="document",
        choices=VALID_TYPES,
        help="Source type.",
    )
    parser.add_argument("--domain", default="", help="Best-fit wiki domain.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    vault_root = Path(args.vault_root).expanduser().resolve()
    source_path = Path(args.source).expanduser().resolve()

    if not source_path.exists():
        raise SystemExit(f"Source file does not exist: {source_path}")

    text = source_path.read_text(encoding="utf-8", errors="replace")
    existing_frontmatter, body = split_frontmatter(text)

    captured = args.captured or datetime.now().astimezone().strftime("%Y-%m-%d")
    year = captured[:4]
    month = captured[5:7]
    origin = args.origin or first_heading_or_name(source_path, body)
    slug = slugify(args.slug or origin)
    summary = args.summary or f"Source copied from {source_path.name}."

    output_dir = vault_root / "memory" / "raw" / year / month
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{captured}-{slug}.md"

    if output_path.exists():
        raise SystemExit(
            f"Refusing to overwrite existing immutable raw file: {output_path}"
        )

    required = {
        "origin": origin,
        "source_path": str(source_path),
        "captured": captured,
        "summary": summary,
        "type": args.source_type,
    }
    if args.domain:
        required["domain"] = args.domain

    frontmatter = merge_frontmatter(required, existing_frontmatter)
    output_path.write_text(frontmatter + body, encoding="utf-8")
    print(output_path.relative_to(vault_root).as_posix())


if __name__ == "__main__":
    main()
