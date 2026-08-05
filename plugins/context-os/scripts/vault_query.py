#!/usr/bin/env python3
"""
vault_query.py: ContextOS retrieval script v1.0.

Traverses memory/wiki/ index hierarchy, performs a YAML-based full-vault scan
for cross-domain article discovery, scans memory/entities/ for entity summary
files, scans each entity's projects/ directory for active content, and scans
memory/insights/ directly. inbox/, processed/, and outbox/ are vault-root
folders shared across all entities, ephemeral, and excluded from every scan.
Returns a structured JSON payload for LLM synthesis.

Usage:
    echo '{"domains":[],"topics":[],"keywords":["your topic"]}' | python $CLAUDE_PLUGIN_ROOT/scripts/vault_query.py
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_query.py --vault-root /path/to/vault --input-json '{"domains":[],"topics":[],"keywords":["topic"]}'
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_query.py --max-candidates 15 --include-dismissed

Input JSON fields:
    domains:   list of wiki domain folder names (empty = all domains)
    topics:    list of topic folder names or substrings (empty = all topics)
    keywords:  list of free terms matched against titles, index entries, abstracts

CLI flags:
    --vault-root PATH       Absolute path to vault root (default: cwd)
    --input-json JSON       JSON input string; reads from stdin if omitted
    --max-candidates INT    Maximum candidates returned (default: 10, 0 = empty lists)
    --include-dismissed     Include insight notes with status: dismissed in results
    --include-archived      Include wiki articles with status: archived in results

"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Allow running from any directory: add scripts/ to path.
sys.path.insert(0, str(Path(__file__).parent))
from vault_utils import (  # noqa: E402
    INDEX_FILENAME,
    _parse_frontmatter,
    _parse_inline_list,
    cache_evict,
    cache_get,
    cache_set,
    open_cache,
    read_file,
)

# Force UTF-8 stdout on Windows to handle non-ASCII characters in vault content.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

W_EXACT_TITLE = 1.0
W_SUBSTR_TITLE = 0.7
W_TOPIC_PATH = 0.6
W_KEYWORD_INDEX = 0.5
W_KEYWORD_ABSTRACT = 0.4

MAX_CANDIDATES = 10
MAX_DEPTH = 10
ABSTRACT_MAX_LINES = 8


# ---------------------------------------------------------------------------
# Frontmatter value normalisation
# ---------------------------------------------------------------------------


def _as_text(value: object, default: str = "") -> str:
    """Render YAML scalar/list values as text for scoring and JSON output."""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return " ".join(_as_text(v) for v in value if v is not None)
    return str(value)


def _as_list(value: object) -> list[str]:
    """Render YAML scalar/list values as a list of strings."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [_as_text(v) for v in value if v is not None and _as_text(v) != ""]
    return [str(value)]


# ---------------------------------------------------------------------------
# Markdown table parser
# ---------------------------------------------------------------------------


def parse_table_rows(text: str) -> list[dict]:
    """Parse all markdown tables in text. Returns list of {header: cell} dicts."""
    rows: list[dict] = []
    headers: list[str] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            headers = None
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]

        # Separator row (---|---| etc.)
        if all(re.match(r"^[-: ]+$", c) for c in cells if c):
            continue

        if headers is None:
            headers = cells
        else:
            row = {
                headers[i]: (cells[i] if i < len(cells) else "")
                for i in range(len(headers))
            }
            rows.append(row)

    return rows


def extract_md_link(cell: str) -> tuple[str, str] | None:
    """Return (display_text, href) from first markdown link in cell, or None."""
    m = re.search(r"\[([^\]]*)\]\(([^)]*)\)", cell)
    return (m.group(1), m.group(2)) if m else None


# ---------------------------------------------------------------------------
# Index parsing
# ---------------------------------------------------------------------------


def parse_index(conn: object, index_path: Path) -> list[dict]:
    """Parse an index.md file.

    Returns list of entries with keys: title, description, href, is_folder, abs_path.
    """
    text = read_file(conn, index_path)
    if not text:
        return []

    index_dir = index_path.parent
    rows = parse_table_rows(text)
    entries: list[dict] = []

    for row in rows:
        link_col: str | None = None
        link: tuple[str, str] | None = None

        for col, cell in row.items():
            result = extract_md_link(cell)
            if result:
                link_col = col
                link = result
                break

        if not link:
            continue

        display, href = link
        title = display.rstrip("/")
        if title.lower().endswith(".md"):
            title = title[:-3]

        # Description: concatenate non-link cells, strip internal links.
        desc_parts = []
        for col, cell in row.items():
            if col == link_col or not cell or cell == "✓":
                continue
            clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cell).strip()
            if clean:
                desc_parts.append(clean)
        description = " | ".join(desc_parts)

        # Detect folder vs article.
        href_clean = href.rstrip("/")
        is_folder = (
            href_clean.endswith(INDEX_FILENAME) or "." not in Path(href_clean).name
        )

        # Resolve absolute path.
        if is_folder:
            if href_clean.endswith(INDEX_FILENAME):
                abs_path = (index_dir / href_clean).resolve()
            else:
                abs_path = (index_dir / href_clean / INDEX_FILENAME).resolve()
        else:
            abs_path = (index_dir / href_clean).resolve()

        entries.append(
            {
                "title": title,
                "description": description,
                "href": href,
                "is_folder": is_folder,
                "abs_path": str(abs_path),
            }
        )

    return entries


# ---------------------------------------------------------------------------
# Abstract extraction
# ---------------------------------------------------------------------------


def extract_abstract(conn: object, article_path: Path) -> str:
    """Extract abstract: ## Key Takeaways bullets, or first content paragraph."""
    text = read_file(conn, article_path)
    if not text:
        return ""

    kt = re.search(r"##\s+Key Takeaways\s*\n((?:[-*]\s+[^\n]+\n?)+)", text)
    if kt:
        lines = kt.group(1).strip().splitlines()
        return "\n".join(lines[:ABSTRACT_MAX_LINES])

    # Skip frontmatter block before scanning for first paragraph.
    all_lines = text.splitlines()
    body_start = 0
    if all_lines and all_lines[0].strip() == "---":
        for i in range(1, len(all_lines)):
            if all_lines[i].strip() == "---":
                body_start = i + 1
                break

    para: list[str] = []
    for line in all_lines[body_start:]:
        stripped = line.strip()
        if not stripped:
            if para:
                break
            continue
        if stripped.startswith("#") or stripped.startswith("**Source:"):
            continue
        para.append(stripped)
        if len(para) >= 4:
            break

    return " ".join(para)


# ---------------------------------------------------------------------------
# insights helpers
# ---------------------------------------------------------------------------


def _insight_abstract(content: str) -> str:
    """Return the body text of an insight note (after frontmatter), up to 4 lines."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        body_lines = lines
    else:
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
        body_lines = lines[end_idx + 1 :] if end_idx is not None else lines
    non_blank = [ln for ln in body_lines if ln.strip()]
    return "\n".join(non_blank[:4])


def score_insight(
    fm: dict,
    abstract: str,
    keywords: list[str],
    domains: list[str],
) -> float:
    """Score an insight note for query relevance."""
    title = _as_text(fm.get("title", ""))
    domain_list = _as_list(fm.get("domain", []))
    tags = _as_list(fm.get("tags", []))

    title_lower = title.lower()
    domain_text = " ".join(domain_list).lower()
    tags_text = " ".join(tags).lower()
    abstract_lower = abstract.lower()

    all_terms = keywords + domains
    if not all_terms:
        return 0.1

    score = 0.0
    for term in all_terms:
        t = term.lower()
        if t in title_lower:
            score += W_EXACT_TITLE if t == title_lower else W_SUBSTR_TITLE
        if t in domain_text or t in tags_text:
            score += W_KEYWORD_INDEX
        if t in abstract_lower:
            score += W_KEYWORD_ABSTRACT

    return min(score / max(len(all_terms), 1), 1.0)


# ---------------------------------------------------------------------------
# Wiki index traversal
# ---------------------------------------------------------------------------


def score_article(
    title: str,
    description: str,
    path_str: str,
    fm: dict,
    abstract: str,
    keywords: list[str],
    topics: list[str],
    domains: list[str],
) -> float:
    """Compute a composite relevance score for a wiki article candidate."""
    title_lower = title.lower()
    desc_lower = description.lower()
    path_lower = path_str.lower()
    abstract_lower = abstract.lower()

    fm_domains = _as_list(fm.get("domain", fm.get("domains", [])))
    fm_topics = _as_list(fm.get("topic", fm.get("topics", [])))
    fm_domain_text = " ".join(fm_domains).lower()
    fm_topic_text = " ".join(fm_topics).lower()

    score = 0.0

    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower == title_lower:
            score += W_EXACT_TITLE
        elif kw_lower in title_lower:
            score += W_SUBSTR_TITLE
        if kw_lower in path_lower:
            score += W_TOPIC_PATH
        if (
            kw_lower in desc_lower
            or kw_lower in fm_domain_text
            or kw_lower in fm_topic_text
        ):
            score += W_KEYWORD_INDEX
        if kw_lower in abstract_lower:
            score += W_KEYWORD_ABSTRACT

    for d in domains:
        d_lower = d.lower()
        if d_lower in fm_domain_text or d_lower in path_lower:
            score += W_KEYWORD_INDEX

    for t in topics:
        t_lower = t.lower()
        if t_lower in fm_topic_text or t_lower in path_lower:
            score += W_TOPIC_PATH
        if t_lower in title_lower:
            score += W_SUBSTR_TITLE

    denom = max(len(keywords) + len(domains) + len(topics), 1)
    return min(score / denom, 1.0)


def traverse_wiki(
    conn: object,
    vault_root: Path,
    keywords: list[str],
    topics: list[str],
    domains: list[str],
    max_candidates: int,
) -> list[dict]:
    """Traverse memory/wiki/ index hierarchy and return scored article candidates."""
    wiki_root = vault_root / "memory" / "wiki"
    master_index = wiki_root / INDEX_FILENAME

    if not master_index.exists():
        return []

    candidates: dict[str, dict] = {}
    missing_indexes: list[str] = []

    def _traverse(index_path: Path, depth: int) -> None:
        if depth > MAX_DEPTH:
            return
        entries = parse_index(conn, index_path)
        for entry in entries:
            abs_path = Path(entry["abs_path"])
            if entry["is_folder"]:
                if abs_path.exists():
                    _traverse(abs_path, depth + 1)
                else:
                    missing_indexes.append(abs_path.relative_to(vault_root).as_posix())
            else:
                # It's an article.
                fm = _parse_frontmatter(read_file(conn, abs_path))
                abstract = extract_abstract(conn, abs_path)
                rel_path = abs_path.relative_to(vault_root).as_posix()
                sc = score_article(
                    entry["title"],
                    entry["description"],
                    rel_path,
                    fm,
                    abstract,
                    keywords,
                    topics,
                    domains,
                )
                if (
                    rel_path not in candidates
                    or candidates[rel_path]["relevance_score"] < sc
                ):
                    candidates[rel_path] = {
                        "path": rel_path,
                        "title": entry["title"],
                        "abstract": abstract,
                        "status": _as_text(fm.get("status", "active")),
                        "sources": _as_list(fm.get("sources", fm.get("source", []))),
                        "domains": _as_list(fm.get("domain", fm.get("domains", []))),
                        "last_modified": _mtime(abs_path),
                        "relevance_score": sc,
                    }

    _traverse(master_index, 0)

    results = sorted(
        candidates.values(), key=lambda x: x["relevance_score"], reverse=True
    )
    return results[:max_candidates] if max_candidates > 0 else []


# ---------------------------------------------------------------------------
# YAML-based full-vault scan for cross-domain discovery
# ---------------------------------------------------------------------------


def scan_articles_by_yaml(
    conn: object,
    vault_root: Path,
    keywords: list[str],
    topics: list[str],
    domains: list[str],
    max_candidates: int,
    include_archived: bool,
    existing: dict[str, dict],
) -> dict[str, dict]:
    """Scan all *.md files under memory/wiki/ via YAML frontmatter.

    Articles tagged with multiple domains in their YAML frontmatter are surfaced
    regardless of which directory they live in (cross-domain discovery).
    Merges into existing candidate dict; higher score wins on collision.
    """
    wiki_root = vault_root / "memory" / "wiki"
    if not wiki_root.exists():
        return existing

    for md_path in wiki_root.rglob("*.md"):
        if md_path.name == INDEX_FILENAME:
            continue
        fm = _parse_frontmatter(read_file(conn, md_path))
        status = _as_text(fm.get("status", "active"))
        if status == "archived" and not include_archived:
            continue
        abstract = extract_abstract(conn, md_path)
        rel_path = md_path.relative_to(vault_root).as_posix()
        title = _as_text(fm.get("title", md_path.stem.replace("-", " ").title()))
        sc = score_article(
            rel_path, "", rel_path, fm, abstract, keywords, topics, domains
        )
        if sc > 0:
            if rel_path not in existing or existing[rel_path]["relevance_score"] < sc:
                existing[rel_path] = {
                    "path": rel_path,
                    "title": title,
                    "abstract": abstract,
                    "status": status,
                    "sources": _as_list(fm.get("sources", fm.get("source", []))),
                    "domains": _as_list(fm.get("domain", fm.get("domains", []))),
                    "last_modified": _mtime(md_path),
                    "relevance_score": sc,
                }

    return existing


# ---------------------------------------------------------------------------
# Entities scan
# ---------------------------------------------------------------------------


def scan_entities(
    conn: object,
    vault_root: Path,
    keywords: list[str],
    topics: list[str],
    domains: list[str],
    max_candidates: int,
) -> list[dict]:
    """Scan memory/entities/ recursively for entity, project, and client files."""
    entities_root = vault_root / "memory" / "entities"
    if not entities_root.exists():
        return []

    candidates: list[dict] = []

    for md_path in entities_root.rglob("*.md"):
        if md_path.name == INDEX_FILENAME:
            continue
        fm = _parse_frontmatter(read_file(conn, md_path))
        abstract = extract_abstract(conn, md_path)
        rel_path = md_path.relative_to(vault_root).as_posix()
        title = _as_text(fm.get("title", md_path.stem.replace("-", " ").title()))
        sc = score_article(title, "", rel_path, fm, abstract, keywords, topics, domains)
        if sc > 0:
            candidates.append(
                {
                    "path": rel_path,
                    "title": title,
                    "abstract": abstract,
                    "last_modified": _mtime(md_path),
                    "relevance_score": sc,
                }
            )

    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates[:max_candidates] if max_candidates > 0 else []


# ---------------------------------------------------------------------------
# Entity working directory scan
# ---------------------------------------------------------------------------

EXCLUDED_ENTITY_DIRS = {"inbox", "processed", "outbox"}


def _entity_slugs_from_index(conn: object, vault_root: Path) -> list[str]:
    """Return entity slugs parsed from memory/entities/index.md."""
    index_path = vault_root / "memory" / "entities" / INDEX_FILENAME
    if not index_path.exists():
        return []
    entries = parse_index(conn, index_path)
    slugs = []
    for entry in entries:
        stem = Path(entry["href"]).stem
        if stem and stem != "index":
            slugs.append(stem)
    return slugs


def scan_entity_dirs(
    conn: object,
    vault_root: Path,
    keywords: list[str],
    topics: list[str],
    domains: list[str],
    max_candidates: int,
) -> list[dict]:
    """Scan each entity's working directory for queryable content.

    Discovers entity slugs from memory/entities/index.md, then scans each
    {slug}/ for markdown files (in practice, {slug}/projects/). inbox/,
    processed/, and outbox/ are vault-root folders shared across all entities,
    not per-entity subdirectories, so they are never encountered here; the
    exclusion below is defensive, for a legacy vault with pre-migration
    per-entity subfolders of the same name. personal/ is always included.
    """
    slugs = _entity_slugs_from_index(conn, vault_root)
    if "personal" not in slugs:
        slugs.append("personal")

    candidates: list[dict] = []

    for slug in slugs:
        entity_dir = vault_root / slug
        if not entity_dir.exists():
            continue
        for md_path in entity_dir.rglob("*.md"):
            if md_path.name == INDEX_FILENAME:
                continue
            rel_to_entity = md_path.relative_to(entity_dir)
            if rel_to_entity.parts and rel_to_entity.parts[0] in EXCLUDED_ENTITY_DIRS:
                continue
            fm = _parse_frontmatter(read_file(conn, md_path))
            abstract = extract_abstract(conn, md_path)
            rel_path = md_path.relative_to(vault_root).as_posix()
            title = _as_text(fm.get("title", md_path.stem.replace("-", " ").title()))
            sc = score_article(
                title, "", rel_path, fm, abstract, keywords, topics, domains
            )
            if sc > 0:
                candidates.append(
                    {
                        "path": rel_path,
                        "title": title,
                        "abstract": abstract,
                        "last_modified": _mtime(md_path),
                        "relevance_score": sc,
                    }
                )

    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates[:max_candidates] if max_candidates > 0 else []


# ---------------------------------------------------------------------------
# insights scan
# ---------------------------------------------------------------------------


def scan_insights(
    conn: object,
    vault_root: Path,
    keywords: list[str],
    domains: list[str],
    max_candidates: int,
    include_dismissed: bool,
) -> list[dict]:
    """Scan memory/insights/ directly for atomic insight notes."""
    ig_root = vault_root / "memory" / "insights"
    if not ig_root.exists():
        return []

    candidates: list[dict] = []

    for md_path in ig_root.rglob("*.md"):
        if md_path.name == INDEX_FILENAME:
            continue
        content = read_file(conn, md_path)
        fm = _parse_frontmatter(content)
        status = _as_text(fm.get("status", "proposed"))
        if status == "dismissed" and not include_dismissed:
            continue
        abstract = _insight_abstract(content)
        sc = score_insight(fm, abstract, keywords, domains)
        if sc > 0:
            candidates.append(
                {
                    "path": md_path.relative_to(vault_root).as_posix(),
                    "title": _as_text(fm.get("title", md_path.stem)),
                    "abstract": abstract,
                    "status": status,
                    "confidence": _as_text(fm.get("confidence", "")),
                    "domain": _as_list(fm.get("domain", [])),
                    "last_modified": _mtime(md_path),
                    "relevance_score": sc,
                }
            )

    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates[:max_candidates] if max_candidates > 0 else []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mtime(path: Path) -> str:
    """Return ISO-8601 mtime string for path, or empty string on error."""
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Main query flow
# ---------------------------------------------------------------------------


def run_query(
    vault_root: Path,
    query: dict,
    max_candidates: int = MAX_CANDIDATES,
    include_dismissed: bool = False,
    include_archived: bool = False,
) -> dict:
    """Run the full vault query and return a structured result payload.

    Args:
        vault_root: Absolute path to the vault root directory.
        query: Dict with optional keys: domains, topics, keywords.
        max_candidates: Maximum candidates per result list.
        include_dismissed: Include insight notes with status 'dismissed'.
        include_archived: Include wiki articles with status 'archived'.

    Returns:
        Dict with keys: candidate_articles, candidate_entities, candidate_insights,
        missing_indexes, query_echo.
    """
    domains: list[str] = query.get("domains", []) or []
    topics: list[str] = query.get("topics", []) or []
    keywords: list[str] = query.get("keywords", []) or []

    vault_root = vault_root.resolve()
    conn = open_cache()

    # Pass 1: index traversal.
    candidates = traverse_wiki(
        conn, vault_root, keywords, topics, domains, max_candidates
    )
    candidates_map = {c["path"]: c for c in candidates}

    # Pass 2: YAML-based full-vault scan for cross-domain enrichment.
    candidates_map = scan_articles_by_yaml(
        conn,
        vault_root,
        keywords,
        topics,
        domains,
        max_candidates,
        include_archived,
        candidates_map,
    )

    # Filter archived unless requested.
    if not include_archived:
        candidates_map = {
            k: v for k, v in candidates_map.items() if v.get("status") != "archived"
        }

    candidate_articles = sorted(
        candidates_map.values(), key=lambda x: x["relevance_score"], reverse=True
    )
    if max_candidates > 0:
        candidate_articles = candidate_articles[:max_candidates]

    # Pass 3: entities scan (memory/entities/ summaries + top-level entity dirs).
    entity_summary = scan_entities(
        conn,
        vault_root,
        keywords,
        topics,
        domains,
        max_candidates,
    )
    entity_dirs = scan_entity_dirs(
        conn,
        vault_root,
        keywords,
        topics,
        domains,
        max_candidates,
    )
    # Merge by path; higher score wins.
    entity_map: dict[str, dict] = {e["path"]: e for e in entity_summary}
    for item in entity_dirs:
        if (
            item["path"] not in entity_map
            or item["relevance_score"] > entity_map[item["path"]]["relevance_score"]
        ):
            entity_map[item["path"]] = item
    candidate_entities = sorted(
        entity_map.values(), key=lambda x: x["relevance_score"], reverse=True
    )
    if max_candidates > 0:
        candidate_entities = candidate_entities[:max_candidates]

    # Pass 4: insights scan.
    candidate_insights = scan_insights(
        conn,
        vault_root,
        keywords,
        domains,
        max_candidates,
        include_dismissed,
    )

    return {
        "candidate_articles": candidate_articles,
        "candidate_entities": candidate_entities,
        "candidate_insights": candidate_insights,
        "missing_indexes": [],
        "query_echo": {
            "domains": domains,
            "topics": topics,
            "keywords": keywords,
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ContextOS retrieval script.")
    parser.add_argument("--vault-root", default=".", help="Vault root directory.")
    parser.add_argument(
        "--input-json", help="JSON query string; reads from stdin if omitted."
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=MAX_CANDIDATES,
        help="Maximum candidates returned per list (0 = empty).",
    )
    parser.add_argument(
        "--include-dismissed",
        action="store_true",
        help="Include insight notes with status: dismissed.",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include wiki articles with status: archived.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    raw = args.input_json or sys.stdin.read()
    try:
        query = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON input: {exc}"}))
        sys.exit(1)

    vault_root = Path(args.vault_root).expanduser().resolve()
    if not vault_root.exists():
        print(json.dumps({"error": f"Vault root does not exist: {vault_root}"}))
        sys.exit(1)

    result = run_query(
        vault_root=vault_root,
        query=query,
        max_candidates=args.max_candidates,
        include_dismissed=args.include_dismissed,
        include_archived=args.include_archived,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
