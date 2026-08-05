#!/usr/bin/env python3
"""
vault_lint.py: ContextOS wiki and insights quality auditor.

Scans memory/wiki/ and memory/insights/ for structural and quality issues.
Produces a structured report. No files are modified during the lint pass.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_lint.py --vault-root PATH
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_lint.py --vault-root PATH --json
    python $CLAUDE_PLUGIN_ROOT/scripts/vault_lint.py --vault-root PATH --stale-days 90

CLI flags:
    --vault-root PATH     Vault root directory.
    --stale-days INT      Days after which an article is flagged as stale (default: 90).
    --json                Emit results as JSON instead of human-readable text.

"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add scripts/ to path for vault_utils import.
sys.path.insert(0, str(Path(__file__).parent))
from vault_utils import (  # noqa: E402
    INDEX_FILENAME,
    _parse_frontmatter,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_STALE_DAYS = 90
REQUIRED_SECTIONS = {"## Key Takeaways"}
SOURCE_RE = re.compile(r"\*\*Source:\*\*", re.IGNORECASE)
UNRESOLVED_PLACEHOLDER_RE = re.compile(r"\{\{[A-Za-z][^}]*\}\}")
EMPTY_HEADING_RE = re.compile(r"^(#{1,6} .+)\n(\n#{1,6} |\Z)", re.MULTILINE)
LOWERCASE_HYPHEN_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*\.[a-z]+$")
VALID_STATUSES = {"active", "archived", "draft"}
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# insights (memory/insights/): a flat Zettelkasten-style layer parallel
# to the wiki. Status/confidence enums match what vault_query.py actually reads
# (status defaults to "proposed" and treats "dismissed" specially), not the
# active/archived/draft enum used by wiki articles.
INSIGHT_SUBDIR = "memory/insights"
INSIGHT_VALID_STATUSES = {"proposed", "adopted", "dismissed"}
INSIGHT_VALID_CONFIDENCE = {"low", "medium", "high"}
INSIGHT_STALE_PROPOSED_DAYS = 30
RELATIONS_SECTION_RE = re.compile(
    r"^## Relations\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)


# ---------------------------------------------------------------------------
# Issue types
# ---------------------------------------------------------------------------


class Issue:
    """Represents a single lint finding."""

    def __init__(self, category: str, path: str, detail: str) -> None:
        self.category = category
        self.path = path
        self.detail = detail

    def to_dict(self) -> dict:
        return {"category": self.category, "path": self.path, "detail": self.detail}

    def __str__(self) -> str:
        return f"  [{self.category}] {self.path}: {self.detail}"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_filename(path: Path, vault_root: Path) -> list[Issue]:
    """Flag files whose names are not lowercase-hyphenated."""
    issues = []
    name = path.name
    if not LOWERCASE_HYPHEN_RE.match(name) and name != INDEX_FILENAME:
        rel = path.relative_to(vault_root).as_posix()
        issues.append(
            Issue("structural", rel, f"Filename '{name}' is not lowercase-hyphenated.")
        )
    return issues


def check_frontmatter(path: Path, vault_root: Path, content: str) -> list[Issue]:
    """Check YAML frontmatter presence and status field validity."""
    issues = []
    rel = path.relative_to(vault_root).as_posix()
    fm = _parse_frontmatter(content)

    if not fm:
        issues.append(Issue("quality", rel, "Missing YAML frontmatter."))
        return issues

    status = fm.get("status", "")
    if isinstance(status, str) and status and status not in VALID_STATUSES:
        issues.append(
            Issue(
                "quality",
                rel,
                f"Unknown status value: '{status}'. Expected one of: {', '.join(sorted(VALID_STATUSES))}.",
            )
        )

    return issues


def check_required_sections(path: Path, vault_root: Path, content: str) -> list[Issue]:
    """Check that required sections are present."""
    issues = []
    rel = path.relative_to(vault_root).as_posix()
    content_lower = content.lower()

    if "## key takeaways" not in content_lower:
        issues.append(Issue("quality", rel, "Missing '## Key Takeaways' section."))

    if not SOURCE_RE.search(content):
        issues.append(Issue("citation", rel, "Missing '**Source:**' line."))

    return issues


def check_unresolved_placeholders(
    path: Path, vault_root: Path, content: str
) -> list[Issue]:
    """Flag any remaining {{...}} placeholder strings."""
    issues = []
    rel = path.relative_to(vault_root).as_posix()
    matches = UNRESOLVED_PLACEHOLDER_RE.findall(content)
    if matches:
        unique = sorted(set(matches))
        issues.append(
            Issue("quality", rel, f"Unresolved placeholder(s): {', '.join(unique)}")
        )
    return issues


def check_source_paths(path: Path, vault_root: Path, content: str) -> list[Issue]:
    """Check that Source: lines reference files that actually exist.

    Tries the href both as a path relative to the article directory and as a
    vault-root-relative path, so that both `../../raw/...` and `memory/raw/...`
    style links are accepted.
    """
    issues = []
    rel = path.relative_to(vault_root).as_posix()
    article_dir = path.parent

    # Match both the display text and href: [display](href)
    for m in re.finditer(
        r"\*\*Source:\*\*[^\n]*\[([^\]]*)\]\(([^)]+)\)", content, re.IGNORECASE
    ):
        display = m.group(1).strip()
        href = m.group(2).strip()
        if href.startswith("http"):
            continue  # External URLs are not validated.
        # Try 1: resolve href relative to article directory.
        if (article_dir / href).resolve().exists():
            continue
        # Try 2: display text as vault-root-relative (convention: display shows vault path).
        if (
            display
            and not display.startswith("../")
            and (vault_root / display).resolve().exists()
        ):
            continue
        # Try 3: href as vault-root-relative when it does not traverse above vault root.
        if not href.startswith("../") and (vault_root / href).resolve().exists():
            continue
        issues.append(Issue("citation", rel, f"Source path does not exist: {href}"))

    return issues


def check_open_questions(path: Path, vault_root: Path, content: str) -> list[str]:
    """Return any open-questions summaries for flagging (not errors)."""
    flags = []
    if "## open questions" in content.lower():
        flags.append(path.relative_to(vault_root).as_posix())
    return flags


def check_staleness(path: Path, vault_root: Path, stale_days: int) -> list[dict]:
    """Flag articles whose mtime is older than stale_days."""
    stale = []
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        cutoff = datetime.now() - timedelta(days=stale_days)
        if mtime < cutoff:
            stale.append(
                {
                    "path": path.relative_to(vault_root).as_posix(),
                    "last_updated": mtime.strftime("%Y-%m-%d"),
                }
            )
    except OSError:
        pass
    return stale


def check_index_references(
    index_path: Path,
    vault_root: Path,
    content: str,
) -> tuple[list[Issue], list[Issue]]:
    """Check that every link in an index.md points to an existing file.

    Returns (broken_links, orphaned_articles) where orphaned_articles is
    populated with articles in the same directory that are not in the index.
    """
    broken: list[Issue] = []
    index_dir = index_path.parent
    rel_index = index_path.relative_to(vault_root).as_posix()

    # Collect all hrefs from markdown links in the index.
    referenced_files: set[Path] = set()
    for m in re.finditer(r"\[([^\]]*)\]\(([^)]*)\)", content):
        href = m.group(2).strip()
        if href.startswith("http") or href.startswith("#"):
            continue
        resolved = (index_dir / href).resolve()
        referenced_files.add(resolved)
        if not resolved.exists():
            broken.append(
                Issue("structural", rel_index, f"Link target does not exist: {href}")
            )

    # Orphaned articles: .md files in the directory not in the index.
    orphaned: list[Issue] = []
    for md_path in index_dir.glob("*.md"):
        if md_path.name == INDEX_FILENAME:
            continue
        # Compare resolved forms; referenced_files holds resolved hrefs.
        if md_path.resolve() not in referenced_files:
            orphaned.append(
                Issue(
                    "structural",
                    md_path.relative_to(vault_root).as_posix(),
                    "Article not referenced in its parent index.md.",
                )
            )

    return broken, orphaned


# ---------------------------------------------------------------------------
# insights checks (memory/insights/)
# ---------------------------------------------------------------------------


def check_insight_frontmatter(
    path: Path, vault_root: Path, content: str
) -> list[Issue]:
    """Check insight-note frontmatter: presence, status enum, confidence enum."""
    issues = []
    rel = path.relative_to(vault_root).as_posix()
    fm = _parse_frontmatter(content)

    if not fm:
        issues.append(Issue("quality", rel, "Missing YAML frontmatter."))
        return issues

    status = fm.get("status", "")
    if isinstance(status, str) and status and status not in INSIGHT_VALID_STATUSES:
        issues.append(
            Issue(
                "quality",
                rel,
                f"Unknown status value: '{status}'. Expected one of: {', '.join(sorted(INSIGHT_VALID_STATUSES))}.",
            )
        )

    confidence = fm.get("confidence", "")
    if (
        isinstance(confidence, str)
        and confidence
        and confidence not in INSIGHT_VALID_CONFIDENCE
    ):
        issues.append(
            Issue(
                "quality",
                rel,
                f"Unknown confidence value: '{confidence}'. Expected one of: {', '.join(sorted(INSIGHT_VALID_CONFIDENCE))}.",
            )
        )

    return issues


def check_insight_relation_links(
    path: Path, vault_root: Path, content: str
) -> list[Issue]:
    """Check that links in an insight note's '## Relations' section resolve to real files."""
    issues = []
    rel = path.relative_to(vault_root).as_posix()
    note_dir = path.parent

    match = RELATIONS_SECTION_RE.search(content)
    if not match:
        return issues

    for _text, href in MD_LINK_RE.findall(match.group(1)):
        href_clean = href.split("#")[0].strip()
        if not href_clean or href_clean.startswith("http"):
            continue
        if (note_dir / href_clean).resolve().exists():
            continue
        if (
            not href_clean.startswith("../")
            and (vault_root / href_clean).resolve().exists()
        ):
            continue
        issues.append(
            Issue(
                "structural", rel, f"Relation link target does not exist: {href_clean}"
            )
        )

    return issues


def check_insight_stale_proposed(
    path: Path, vault_root: Path, content: str
) -> dict | None:
    """Flag a `status: proposed` insight note whose `created` date is stale.

    Proposed insights are meant to be adopted or dismissed, not left in limbo;
    this is a distinct concept from general article staleness (check_staleness),
    which just tracks last-edited time regardless of lifecycle status.
    """
    fm = _parse_frontmatter(content)
    if fm.get("status", "") != "proposed":
        return None

    created_str = fm.get("created", "")
    if not isinstance(created_str, str) or not created_str.strip():
        return None

    try:
        created = datetime.strptime(created_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

    cutoff = (datetime.now() - timedelta(days=INSIGHT_STALE_PROPOSED_DAYS)).date()
    if created > cutoff:
        return None

    return {
        "path": path.relative_to(vault_root).as_posix(),
        "created": created_str.strip(),
        "age_days": (datetime.now().date() - created).days,
    }


# ---------------------------------------------------------------------------
# Main lint runner
# ---------------------------------------------------------------------------


def run_lint(vault_root: Path, stale_days: int = DEFAULT_STALE_DAYS) -> dict:
    """Run all lint checks on the vault wiki and insights, and return a structured report."""
    vault_root = vault_root.resolve()
    wiki_root = vault_root / "memory" / "wiki"
    insight_root = vault_root / "memory" / "insights"

    structural_issues: list[dict] = []
    quality_issues: list[dict] = []
    citation_issues: list[dict] = []
    open_questions_flagged: list[str] = []
    stale_articles: list[dict] = []
    stale_proposed_insights: list[dict] = []

    article_count = 0
    index_count = 0
    insight_count = 0

    if not wiki_root.exists():
        quality_issues.append(
            {
                "category": "structural",
                "path": "memory/wiki/",
                "detail": "Wiki root does not exist.",
            }
        )
    else:
        # Scan all markdown files.
        for md_path in wiki_root.rglob("*.md"):
            try:
                content = md_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                structural_issues.append(
                    {
                        "category": "structural",
                        "path": md_path.relative_to(vault_root).as_posix(),
                        "detail": "Could not read file.",
                    }
                )
                continue

            is_index = md_path.name == INDEX_FILENAME

            if is_index:
                index_count += 1
                broken, orphaned = check_index_references(md_path, vault_root, content)
                for iss in broken:
                    structural_issues.append(iss.to_dict())
                for iss in orphaned:
                    structural_issues.append(iss.to_dict())
            else:
                article_count += 1

                # Filename check.
                for iss in check_filename(md_path, vault_root):
                    structural_issues.append(iss.to_dict())

                # Frontmatter check.
                for iss in check_frontmatter(md_path, vault_root, content):
                    quality_issues.append(iss.to_dict())

                # Required sections.
                for iss in check_required_sections(md_path, vault_root, content):
                    if iss.category == "citation":
                        citation_issues.append(iss.to_dict())
                    else:
                        quality_issues.append(iss.to_dict())

                # Unresolved placeholders.
                for iss in check_unresolved_placeholders(md_path, vault_root, content):
                    quality_issues.append(iss.to_dict())

                # Source path integrity.
                for iss in check_source_paths(md_path, vault_root, content):
                    citation_issues.append(iss.to_dict())

                # Open questions.
                open_questions_flagged.extend(
                    check_open_questions(md_path, vault_root, content)
                )

                # Staleness.
                stale_articles.extend(check_staleness(md_path, vault_root, stale_days))

    if insight_root.exists():
        # Scan memory/insights/: a flat layer, same index.md convention as the wiki.
        for md_path in insight_root.rglob("*.md"):
            try:
                content = md_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                structural_issues.append(
                    {
                        "category": "structural",
                        "path": md_path.relative_to(vault_root).as_posix(),
                        "detail": "Could not read file.",
                    }
                )
                continue

            if md_path.name == INDEX_FILENAME:
                index_count += 1
                broken, orphaned = check_index_references(md_path, vault_root, content)
                for iss in broken:
                    structural_issues.append(iss.to_dict())
                for iss in orphaned:
                    structural_issues.append(iss.to_dict())
            else:
                insight_count += 1

                for iss in check_filename(md_path, vault_root):
                    structural_issues.append(iss.to_dict())

                for iss in check_insight_frontmatter(md_path, vault_root, content):
                    quality_issues.append(iss.to_dict())

                for iss in check_unresolved_placeholders(md_path, vault_root, content):
                    quality_issues.append(iss.to_dict())

                for iss in check_insight_relation_links(md_path, vault_root, content):
                    structural_issues.append(iss.to_dict())

                stale_entry = check_insight_stale_proposed(md_path, vault_root, content)
                if stale_entry is not None:
                    stale_proposed_insights.append(stale_entry)

    total_issues = len(structural_issues) + len(quality_issues) + len(citation_issues)

    # Count articles that have no issues.
    articles_with_issues: set[str] = set()
    for iss in structural_issues + quality_issues + citation_issues:
        articles_with_issues.add(iss["path"])
    clean_articles = (article_count + insight_count) - len(articles_with_issues)

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "structural_issues": structural_issues,
        "quality_issues": quality_issues,
        "citation_issues": citation_issues,
        "open_questions_flagged": open_questions_flagged,
        "stale_articles": stale_articles,
        "stale_proposed_insights": stale_proposed_insights,
        "summary": {
            "total_articles": article_count,
            "total_index_files": index_count,
            "total_insight_notes": insight_count,
            "total_issues": total_issues,
            "clean_articles": max(clean_articles, 0),
        },
    }


# ---------------------------------------------------------------------------
# Report formatter
# ---------------------------------------------------------------------------


def format_report(report: dict) -> str:
    """Format a lint report as human-readable markdown."""
    lines = [
        f"## Lint Report: {report['date']}",
        "",
    ]

    def _section(title: str, issues: list[dict]) -> None:
        lines.append(f"### {title}")
        if issues:
            for iss in issues:
                lines.append(f"- {iss['path']}: {iss['detail']}")
        else:
            lines.append("- (none)")
        lines.append("")

    _section("Structural issues", report["structural_issues"])
    _section("Quality issues", report["quality_issues"])
    _section("Citation issues", report["citation_issues"])

    lines.append("### Open questions flagged")
    if report["open_questions_flagged"]:
        for path in report["open_questions_flagged"]:
            lines.append(f"- {path}")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("### Potentially stale (>{} days)".format(DEFAULT_STALE_DAYS))
    if report["stale_articles"]:
        for item in report["stale_articles"]:
            lines.append(f"- {item['path']}: last updated {item['last_updated']}")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append(
        "### Stale proposed insights (>{} days)".format(INSIGHT_STALE_PROPOSED_DAYS)
    )
    if report["stale_proposed_insights"]:
        for item in report["stale_proposed_insights"]:
            lines.append(
                f"- {item['path']}: proposed {item['created']} ({item['age_days']} days ago)"
            )
    else:
        lines.append("- (none)")
    lines.append("")

    s = report["summary"]
    lines.append("### Summary")
    lines.append(f"Total articles: {s['total_articles']}")
    lines.append(f"Total insight notes: {s['total_insight_notes']}")
    lines.append(f"Total issues: {s['total_issues']}")
    lines.append(f"Clean articles: {s['clean_articles']}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ContextOS wiki quality auditor.")
    parser.add_argument("--vault-root", default=".", help="Vault root directory.")
    parser.add_argument(
        "--stale-days",
        type=int,
        default=DEFAULT_STALE_DAYS,
        help="Days after which articles are flagged as stale.",
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help="Emit results as JSON."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vault_root = Path(args.vault_root).expanduser().resolve()

    if not vault_root.exists():
        print(json.dumps({"error": f"Vault root does not exist: {vault_root}"}))
        sys.exit(1)

    report = run_lint(vault_root=vault_root, stale_days=args.stale_days)

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))


if __name__ == "__main__":
    main()
