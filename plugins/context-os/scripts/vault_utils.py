#!/usr/bin/env python3
"""
vault_utils.py: Shared utilities for ContextOS tooling.

Provides the SQLite file cache and YAML frontmatter parser used by
vault_query.py, update_wiki_index.py, and vault_lint.py.

Cache location: $TMPDIR/context_os_cache.db
  Key:  absolute file path (TEXT)
  Data: file mtime (REAL) + full UTF-8 content (TEXT)
  Invalidation: mtime-based per entry; survives process restarts until
                the OS clears the temp directory (typically on reboot).

"""

from __future__ import annotations

import re
import sqlite3
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INDEX_FILENAME = "index.md"
CACHE_DB_NAME = "context_os_cache.db"

# ---------------------------------------------------------------------------
# SQLite cache: keyed by absolute path, invalidated on mtime change
# ---------------------------------------------------------------------------

_CACHE_TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS file_cache (
        path    TEXT PRIMARY KEY,
        mtime   REAL,
        content TEXT
    )
"""


def open_cache() -> sqlite3.Connection:
    """Open (or create) the shared vault SQLite cache and return the connection.

    The cache file is stored in the system temp directory so it persists
    across process runs without requiring a project-specific location.
    """
    cache_path = Path(tempfile.gettempdir()) / CACHE_DB_NAME
    conn = sqlite3.connect(str(cache_path))
    conn.execute(_CACHE_TABLE_DDL)
    conn.commit()
    return conn


def cache_get(conn: sqlite3.Connection, path: Path) -> str | None:
    """Return cached content for path if the cached mtime matches the current mtime.

    Returns None on a cache miss (path absent or mtime mismatch).
    A return value of None always means the caller should read the file and
    call cache_set; it does NOT mean the file is missing.
    """
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    row = conn.execute(
        "SELECT mtime, content FROM file_cache WHERE path = ?",
        (str(path),),
    ).fetchone()
    if row and abs(row[0] - mtime) < 0.001:
        return row[1]
    return None


def cache_set(conn: sqlite3.Connection, path: Path, content: str) -> None:
    """Write content for path into the cache, keyed by the file's current mtime.

    Uses INSERT OR REPLACE so that stale entries are atomically superseded.
    If the file's mtime cannot be read (e.g., just deleted), mtime is stored
    as 0.0; the entry will be superseded on the next read.
    """
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    conn.execute(
        "INSERT OR REPLACE INTO file_cache (path, mtime, content) VALUES (?, ?, ?)",
        (str(path), mtime, content),
    )
    conn.commit()


def cache_evict(conn: sqlite3.Connection, path: Path) -> None:
    """Remove a path's entry from the cache.

    Used when a file is deleted so that the cache does not serve stale content
    to subsequent callers. Safe to call when the path is not cached.
    """
    conn.execute("DELETE FROM file_cache WHERE path = ?", (str(path),))
    conn.commit()


def read_file(conn: sqlite3.Connection, path: Path) -> str:
    """Return the UTF-8 content of path, using the cache when valid.

    On a cache miss the file is read from disk and the result is stored.
    Returns an empty string if the file cannot be read (missing or permission
    error); this is stored in the cache so repeated misses skip the OS call.
    """
    cached = cache_get(conn, path)
    if cached is not None:
        return cached
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    cache_set(conn, path, text)
    return text


# ---------------------------------------------------------------------------
# YAML frontmatter parser
# ---------------------------------------------------------------------------

def _parse_inline_list(val: str) -> list[str]:
    """Parse an inline YAML array string '[item1, item2]' into a Python list.

    Used by _parse_frontmatter for fields written in inline-array notation.
    Returns an empty list for '[]'.
    """
    inner = val.strip()[1:-1]  # strip leading [ and trailing ]
    if not inner.strip():
        return []
    return [item.strip() for item in inner.split(",") if item.strip()]


def _parse_frontmatter(content: str) -> dict:
    """Minimal YAML frontmatter parser for wiki articles and insight notes.

    Handles:
    - Scalar values:      key: value
    - Inline arrays:      key: [item1, item2]
    - Multi-line arrays:  key:\\n  - item1\\n  - item2

    Returns an empty dict when no valid frontmatter block is found.
    """
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}

    result: dict = {}
    current_key: str | None = None

    for line in lines[1:end_idx]:
        if not line.strip():
            continue

        # Multi-line list item: indented dash
        if re.match(r"^\s{2,}-\s", line):
            item = re.sub(r"^\s+-\s*", "", line).strip()
            if current_key is not None:
                if not isinstance(result.get(current_key), list):
                    result[current_key] = []
                result[current_key].append(item)
            continue

        m = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s*(.*)", line)
        if m:
            current_key = m.group(1).strip()
            val = m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                result[current_key] = _parse_inline_list(val)
            else:
                result[current_key] = val if val else []

    return result


# ---------------------------------------------------------------------------
# Slugify helper
# ---------------------------------------------------------------------------

def slugify(value: str) -> str:
    """Convert a string to a lowercase-hyphenated slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"
