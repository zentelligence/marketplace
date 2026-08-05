#!/usr/bin/env python3
"""
update_wiki_index.py: ContextOS wiki index updater and cache pre-warmer.

Called by vault-ingest after adding, updating, or removing wiki articles.
Maintains index.md files at the topic and domain levels, and pre-warms the
vault-query SQLite cache so the next vault-query invocation is fast.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/update_wiki_index.py --vault-root PATH --touched FILE [FILE ...]
    python $CLAUDE_PLUGIN_ROOT/scripts/update_wiki_index.py --vault-root PATH --removed FILE [FILE ...]
    python $CLAUDE_PLUGIN_ROOT/scripts/update_wiki_index.py --vault-root PATH --touched FILE --dry-run
    python $CLAUDE_PLUGIN_ROOT/scripts/update_wiki_index.py --vault-root PATH --touched FILE --json

Flags:
    --vault-root PATH   Absolute path to vault root.
    --touched FILE ...  Vault-relative paths of added or updated wiki articles.
    --removed FILE ...  Vault-relative paths of deleted wiki articles.
    --dry-run           Print planned changes without writing files or warming cache.
    --json              Emit results as a JSON object.

"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add scripts/ to path so vault_utils can be imported from any working directory.
sys.path.insert(0, str(Path(__file__).parent))
from vault_utils import (  # noqa: E402
    INDEX_FILENAME,
    _parse_frontmatter,
    cache_evict,
    cache_set,
    open_cache,
    read_file,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DESCRIPTION_MAX_LEN: int = 120
STUB_DESCRIPTION: str = "(description pending; update manually)"

# Header keywords identifying the article listing table in a topic index.
ARTICLE_TABLE_HEADERS: tuple = ("file", "article")

# Header keywords identifying the topic/folder listing table in domain indexes.
FOLDER_TABLE_HEADERS: tuple = ("folder", "topic", "sub-domain", "subdomain")


# ---------------------------------------------------------------------------
# Description extraction
# ---------------------------------------------------------------------------


def extract_description(content: str) -> str:
    """Extract a one-line description from article content.

    Preference order:
    1. First bullet in ## Key Takeaways.
    2. First non-blank, non-heading body sentence.
    3. Empty string when no suitable text is found.
    """
    in_kt = False
    body_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r"^##\s+Key Takeaways", stripped, re.IGNORECASE):
            in_kt = True
            continue
        if in_kt:
            if stripped.startswith("##"):
                in_kt = False
                continue
            if re.match(r"^[-*]\s+", stripped):
                text = re.sub(r"^[-*]\s+", "", stripped).strip()
                return _truncate(text)
            continue
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith("**Source:")
            and not stripped.startswith("---")
        ):
            body_lines.append(stripped)

    if body_lines:
        first = body_lines[0]
        sentence_end = first.find(". ")
        text = first[: sentence_end + 1] if sentence_end != -1 else first
        return _truncate(text)

    return ""


def _truncate(text: str) -> str:
    """Truncate text to DESCRIPTION_MAX_LEN, appending ellipsis if truncated."""
    if len(text) <= DESCRIPTION_MAX_LEN:
        return text
    return text[: DESCRIPTION_MAX_LEN - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Markdown table helpers
# ---------------------------------------------------------------------------


def _split_table_row(line: str) -> list[str]:
    """Split a markdown table row into stripped cell strings."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    return [c.strip() for c in stripped.strip("|").split("|")]


def _is_separator_row(line: str) -> bool:
    """Return True if line is a markdown table separator (|---|---|)."""
    cells = _split_table_row(line)
    return bool(cells) and all(re.match(r"^[-: ]+$", c) for c in cells if c)


def _extract_href_from_cell(cell: str) -> str | None:
    """Extract the href from the first markdown link in a table cell."""
    m = re.search(r"\[([^\]]*)\]\(([^)]*)\)", cell)
    return m.group(2) if m else None


def _normalise_href(href: str) -> str:
    """Strip a leading './' prefix and lowercase for comparison."""
    return href.lstrip("./").lower()


def _folder_row_exists(content: str, folder_name: str) -> bool:
    """Return True if content already contains a table row for folder_name."""
    pattern = re.compile(r"\[" + re.escape(folder_name) + r"[/]?\]", re.IGNORECASE)
    return bool(pattern.search(content))


# ---------------------------------------------------------------------------
# IndexTable: manage a single index.md's article or folder table
# ---------------------------------------------------------------------------


class IndexTable:
    """Read, modify, and serialise a markdown table within an index.md file."""

    def __init__(
        self,
        content: str,
        header_keywords: tuple = ARTICLE_TABLE_HEADERS,
    ) -> None:
        self._original_content = content
        self._header_keywords = header_keywords
        self._lines = content.splitlines(keepends=True)
        self._changed = False
        self._table_start: int | None = None
        self._table_end: int | None = None
        self._col_count: int = 2
        self._headers: list[str] = []
        self._rows: list[dict] = []
        self._locate_table()

    @property
    def changed(self) -> bool:
        return self._changed

    def add_or_update(self, filename: str, title: str, description: str) -> None:
        """Add a new article row or update an existing row."""
        if self._table_start is None:
            self._append_new_table(filename, title, description)
            return

        norm = _normalise_href(filename)
        for row in self._rows:
            if _normalise_href(row["href"]) == norm:
                row["cells"] = self._build_cells(filename, title, description)
                self._changed = True
                return

        self._rows.append(
            {"href": filename, "cells": self._build_cells(filename, title, description)}
        )
        self._rows.sort(key=lambda r: _normalise_href(r["href"]))
        self._changed = True

    def remove(self, filename: str) -> None:
        """Remove the row for filename. Safe to call when the row is absent."""
        if self._table_start is None:
            return
        norm = _normalise_href(filename)
        before = len(self._rows)
        self._rows = [r for r in self._rows if _normalise_href(r["href"]) != norm]
        if len(self._rows) != before:
            self._changed = True

    def serialise(self) -> str:
        """Render the (possibly modified) content back to markdown."""
        if not self._changed or self._table_start is None:
            return self._original_content

        header_line = self._lines[self._table_start]
        sep_line = self._lines[self._table_start + 1]
        new_table_lines = [header_line, sep_line]
        for row in self._rows:
            new_table_lines.append("| " + " | ".join(row["cells"]) + " |\n")

        result_lines = (
            list(self._lines[: self._table_start])
            + new_table_lines
            + list(self._lines[self._table_end :])
        )
        return "".join(result_lines)

    def _build_cells(self, filename: str, title: str, description: str) -> list[str]:
        if self._col_count == 3:
            return [f"[{filename}]({filename})", title, description]
        return [f"[{filename}]({filename})", description]

    def _locate_table(self) -> None:
        i = 0
        while i < len(self._lines):
            line = self._lines[i].rstrip("\n\r")
            if not line.strip().startswith("|"):
                i += 1
                continue
            header_cells = _split_table_row(line)
            if not header_cells:
                i += 1
                continue
            first_header = header_cells[0].lower()
            if not any(kw in first_header for kw in self._header_keywords):
                i += 1
                continue
            if i + 1 >= len(self._lines):
                i += 1
                continue
            sep = self._lines[i + 1].rstrip("\n\r")
            if not _is_separator_row(sep):
                i += 1
                continue
            self._table_start = i
            self._headers = header_cells
            self._col_count = len(header_cells)
            j = i + 2
            while j < len(self._lines):
                data_line = self._lines[j].rstrip("\n\r")
                if not data_line.strip().startswith("|"):
                    break
                cells = _split_table_row(data_line)
                href = _extract_href_from_cell(cells[0]) if cells else None
                if href:
                    self._rows.append({"href": href, "cells": cells})
                j += 1
            self._table_end = j
            return

    def _append_new_table(self, filename: str, title: str, description: str) -> None:
        cells = self._build_cells(filename, title, description)
        if self._col_count == 3:
            header = "| File | Title | Description |"
            sep = "| --- | --- | --- |"
        else:
            header = "| File | Description |"
            sep = "| --- | --- |"
        row = "| " + " | ".join(cells) + " |"
        addition = f"\n## Articles\n\n{header}\n{sep}\n{row}\n"
        self._original_content = self._original_content.rstrip("\n") + addition
        self._lines = self._original_content.splitlines(keepends=True)
        self._changed = True
        self._locate_table()


# ---------------------------------------------------------------------------
# IndexChain: manage index.md files affected by an article change
# ---------------------------------------------------------------------------


def _stub_topic_index(topic_name: str) -> str:
    """Generate a minimal topic index.md for a newly created topic folder."""
    title = topic_name.replace("-", " ").title()
    return (
        f"# {title}\n"
        "\n"
        "_Index auto-generated by vault-ingest. Add description here._\n"
        "\n"
        "## Articles\n"
        "\n"
        "| File | Description |\n"
        "| --- | --- |\n"
    )


def _append_folder_stub(content: str, folder_name: str) -> str:
    """Append a stub row for folder_name to the folder table in content."""
    lines = content.splitlines(keepends=True)
    table_start = None
    col_count = 2

    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if not stripped.strip().startswith("|"):
            continue
        cells = _split_table_row(stripped)
        if not cells:
            continue
        first = cells[0].lower()
        if any(kw in first for kw in FOLDER_TABLE_HEADERS):
            if i + 1 < len(lines) and _is_separator_row(lines[i + 1].rstrip("\n\r")):
                table_start = i
                col_count = len(cells)
                break

    index_href = f"{folder_name}/{INDEX_FILENAME}"
    stub_cells = [f"[{folder_name}/]({index_href})"] + [STUB_DESCRIPTION] * (
        col_count - 1
    )
    stub_line = "| " + " | ".join(stub_cells) + " |\n"

    if table_start is None:
        addition = (
            f"\n## Topics\n\n| Folder | Description |\n| --- | --- |\n{stub_line}"
        )
        return content.rstrip("\n") + addition

    j = table_start + 2
    insert_idx = None
    while j < len(lines):
        row_line = lines[j].rstrip("\n\r")
        if not row_line.strip().startswith("|"):
            insert_idx = j
            break
        row_cells = _split_table_row(row_line)
        href = _extract_href_from_cell(row_cells[0]) if row_cells else None
        if href and _normalise_href(href) > _normalise_href(folder_name + "/"):
            insert_idx = j
            break
        j += 1

    if insert_idx is None:
        insert_idx = j

    lines.insert(insert_idx, stub_line)
    return "".join(lines)


class IndexChain:
    """Identify and update all index.md files affected by a wiki article change."""

    def __init__(self, article_path: Path, wiki_root: Path) -> None:
        self._article_path = article_path.resolve()
        self._wiki_root = wiki_root.resolve()

        rel = self._article_path.relative_to(self._wiki_root)
        parts = rel.parts

        self._domain = parts[0] if len(parts) > 1 else ""

        self.topic_index: Path = self._article_path.parent / INDEX_FILENAME
        self.domain_index: Path = (
            self._wiki_root / self._domain / INDEX_FILENAME if self._domain else Path()
        )

        self._topic_op: str | None = None
        self._topic_title: str = ""
        self._topic_description: str = ""
        self._domain_stub_needed: bool = False

    def update_article(self, title: str, description: str) -> None:
        """Stage an add-or-update operation for this article in the topic index."""
        self._topic_op = "add_or_update"
        self._topic_title = title
        self._topic_description = description
        self._domain_stub_needed = not self.topic_index.exists()

    def remove_article(self) -> None:
        """Stage a remove operation for this article from the topic index."""
        self._topic_op = "remove"

    def write_all(
        self,
        conn: object,
        dry_run: bool = False,
    ) -> list[str]:
        """Apply staged operations and return absolute paths of files written."""
        written: list[str] = []

        if self._topic_op is None:
            return written

        # Topic index.
        if self.topic_index.exists():
            content = self.topic_index.read_text(encoding="utf-8")
        else:
            content = _stub_topic_index(self.topic_index.parent.name)

        table = IndexTable(content)

        if self._topic_op == "add_or_update":
            table.add_or_update(
                self._article_path.name,
                self._topic_title,
                self._topic_description,
            )
        elif self._topic_op == "remove":
            table.remove(self._article_path.name)

        if table.changed or not self.topic_index.exists():
            written.append(str(self.topic_index))
            if not dry_run:
                self.topic_index.parent.mkdir(parents=True, exist_ok=True)
                new_content = table.serialise()
                self.topic_index.write_text(new_content, encoding="utf-8")
                cache_set(conn, self.topic_index, new_content)

        # Domain index: stub row for new topic.
        if (
            self._domain_stub_needed
            and self._topic_op == "add_or_update"
            and self.domain_index != Path()
            and self.domain_index.exists()
        ):
            domain_content = self.domain_index.read_text(encoding="utf-8")
            topic_folder = self.topic_index.parent.name
            if not _folder_row_exists(domain_content, topic_folder):
                new_domain_content = _append_folder_stub(domain_content, topic_folder)
                written.append(str(self.domain_index))
                if not dry_run:
                    self.domain_index.write_text(new_domain_content, encoding="utf-8")
                    cache_set(conn, self.domain_index, new_domain_content)

        return written


# ---------------------------------------------------------------------------
# Cache warmer
# ---------------------------------------------------------------------------


class CacheWarmer:
    """Pre-warm and evict entries in the vault-query SQLite cache."""

    def __init__(self, conn: object) -> None:
        self._conn = conn

    def warm(self, paths: list[Path], dry_run: bool = False) -> None:
        """Read each path from disk and write its content into the cache."""
        if dry_run:
            return
        for path in paths:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                cache_set(self._conn, path, content)
            except OSError:
                pass

    def evict(self, paths: list[Path], dry_run: bool = False) -> None:
        """Remove each path's cache entry."""
        if dry_run:
            return
        for path in paths:
            cache_evict(self._conn, path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Update wiki index.md files and pre-warm the vault-query cache."
    )
    parser.add_argument(
        "--vault-root", default=os.getcwd(), help="Vault root directory."
    )
    parser.add_argument(
        "--touched",
        nargs="+",
        default=[],
        metavar="FILE",
        help="Vault-relative paths of added or updated wiki articles.",
    )
    parser.add_argument(
        "--removed",
        nargs="+",
        default=[],
        metavar="FILE",
        help="Vault-relative paths of deleted wiki articles.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without modifying files.",
    )
    parser.add_argument(
        "--json", action="store_true", dest="output_json", help="Emit results as JSON."
    )
    args = parser.parse_args(argv)

    vault_root = Path(args.vault_root).resolve()
    wiki_root = vault_root / "memory" / "wiki"
    conn = open_cache()
    warmer = CacheWarmer(conn)

    all_written: list[str] = []
    article_paths_touched: list[Path] = []
    article_paths_removed: list[Path] = []

    # Process touched (added/updated) articles.
    for rel in args.touched:
        article_path = (vault_root / rel).resolve()
        if not article_path.exists():
            if not args.output_json:
                print(
                    f"[warn] touched file not found, skipping: {rel}", file=sys.stderr
                )
            continue

        content = article_path.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(content)
        title = fm.get("title", "") or article_path.stem.replace("-", " ").title()
        description = extract_description(content)

        chain = IndexChain(article_path, wiki_root)
        chain.update_article(title, description)
        written = chain.write_all(conn, dry_run=args.dry_run)
        all_written.extend(written)
        article_paths_touched.append(article_path)

    # Process removed articles.
    for rel in args.removed:
        article_path = (vault_root / rel).resolve()
        chain = IndexChain(article_path, wiki_root)
        chain.remove_article()
        written = chain.write_all(conn, dry_run=args.dry_run)
        all_written.extend(written)
        article_paths_removed.append(article_path)

    # Pre-warm cache for touched articles and written indexes.
    warm_paths = article_paths_touched + [Path(p) for p in all_written]
    warmer.warm(warm_paths, dry_run=args.dry_run)
    warmer.evict(article_paths_removed, dry_run=args.dry_run)

    result = {
        "indexes_written": all_written,
        "articles_touched": [
            p.relative_to(vault_root).as_posix() for p in article_paths_touched
        ],
        "articles_removed": [
            p.relative_to(vault_root).as_posix() for p in article_paths_removed
        ],
        "dry_run": args.dry_run,
    }

    if args.output_json:
        print(json.dumps(result, indent=2))
    else:
        prefix = "[dry-run] " if args.dry_run else ""
        for path in all_written:
            print(f"{prefix}wrote: {path}")
        print(
            f"\n{prefix}{len(all_written)} index file(s) updated, "
            f"{len(article_paths_touched)} article(s) touched, "
            f"{len(article_paths_removed)} article(s) removed."
        )


if __name__ == "__main__":
    main()
