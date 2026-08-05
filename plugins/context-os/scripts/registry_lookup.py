#!/usr/bin/env python3
"""
registry_lookup.py: Locate role, hat, prompt, or agent definition files in the vault registry.

Resolves a slug to a definition file path, reporting whether it exists and
listing all available definitions of the same type.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/registry_lookup.py --vault-root . --type role   --slug architect
    python $CLAUDE_PLUGIN_ROOT/scripts/registry_lookup.py --vault-root . --type hat    --slug critic
    python $CLAUDE_PLUGIN_ROOT/scripts/registry_lookup.py --vault-root . --type prompt --slug email-professional
    python $CLAUDE_PLUGIN_ROOT/scripts/registry_lookup.py --vault-root . --type agent  --slug demo-critic

CLI flags:
    --vault-root PATH   Vault root directory (default: cwd).
    --type TYPE         Definition type: "role", "hat", "prompt", or "agent".
    --slug SLUG         Slug to look up (lowercased, alphanumeric and hyphens).
                        For type "prompt", may be bare ("email-professional") or
                        category-qualified ("writing/email-professional").

Output JSON fields:
    found:      True when a matching definition file exists.
    slug:       Normalised slug that was queried.
    type:       "role", "hat", "prompt", or "agent".
    file:       Vault-relative path to the definition file, or null if not found.
    available:  Sorted list of slugs currently defined for this type. Prompt
                slugs are category-qualified (e.g. "writing/email-professional").
    errors:     Blocking errors. Non-empty means do not proceed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REGISTRY_DIRS: dict[str, str] = {
    "role": "registry/roles",
    "hat": "registry/hats",
    "prompt": "registry/prompts",
    "agent": "registry/agents",
}

# Files that document the prompt registry itself rather than defining a usable prompt.
PROMPT_NON_ENTRIES: set[str] = {"index", "framework"}


def normalise_slug(raw: str) -> str:
    """Lowercase and strip characters that cannot appear in a filename slug."""
    slug = raw.strip().lower()
    slug = re.sub(r"[^a-z0-9-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def normalise_prompt_slug(raw: str) -> str:
    """Normalise a prompt slug, preserving an optional '<category>/<name>' shape."""
    parts = [normalise_slug(part) for part in raw.strip().split("/")]
    return "/".join(part for part in parts if part)


def _available(registry_dir: Path) -> list[str]:
    """List all defined slugs in a registry directory."""
    slugs: list[str] = []
    for path in sorted(registry_dir.iterdir()):
        if path.is_file() and path.suffix == ".md" and path.stem != "index":
            slugs.append(path.stem)
        elif path.is_dir() and (path / "SKILL.md").exists():
            slugs.append(path.name)
    return slugs


def _available_prompts(registry_dir: Path) -> list[str]:
    """List all defined prompt slugs, category-qualified, across the prompt registry."""
    slugs: list[str] = []
    for path in sorted(registry_dir.rglob("*.md")):
        if path.stem in PROMPT_NON_ENTRIES:
            continue
        slugs.append(path.relative_to(registry_dir).with_suffix("").as_posix())
    return slugs


def _lookup_prompt(vault_root: Path, registry_dir: Path, slug: str) -> dict:
    """Resolve a prompt slug. Accepts bare ("standard") or category-qualified
    ("general/standard") slugs. A bare slug matching more than one category is
    reported as ambiguous rather than guessed."""
    available = _available_prompts(registry_dir)

    if "/" in slug:
        candidate = registry_dir / f"{slug}.md"
        matches = [slug] if candidate.exists() else []
    else:
        matches = [s for s in available if s == slug or s.endswith(f"/{slug}")]

    if len(matches) == 1:
        found_path = registry_dir / f"{matches[0]}.md"
        return {
            "found": True,
            "slug": matches[0],
            "type": "prompt",
            "file": found_path.relative_to(vault_root).as_posix(),
            "available": available,
            "errors": [],
        }

    errors = []
    if len(matches) > 1:
        errors.append(
            f"Slug {slug!r} is ambiguous across categories: {matches}. "
            "Qualify it as '<category>/<slug>'."
        )

    return {
        "found": False,
        "slug": slug,
        "type": "prompt",
        "file": None,
        "available": available,
        "errors": errors,
    }


def lookup(vault_root: Path, kind: str, slug: str) -> dict:
    """Resolve a registry definition by type and slug.

    Returns a result dict with keys: found, slug, type, file, available, errors.
    """
    if kind not in REGISTRY_DIRS:
        return {
            "found": False,
            "slug": slug,
            "type": kind,
            "file": None,
            "available": [],
            "errors": [
                f"Unknown type {kind!r}. Must be 'role', 'hat', 'prompt', or 'agent'."
            ],
        }

    vault_root = vault_root.resolve()
    registry_dir = vault_root / REGISTRY_DIRS[kind]

    if not registry_dir.exists():
        return {
            "found": False,
            "slug": slug,
            "type": kind,
            "file": None,
            "available": [],
            "errors": [
                f"Registry directory '{REGISTRY_DIRS[kind]}' not found. "
                "Run 'vault init' to scaffold the vault."
            ],
        }

    if kind == "prompt":
        return _lookup_prompt(vault_root, registry_dir, slug)

    # Flat file takes precedence over directory-based definition.
    flat = registry_dir / f"{slug}.md"
    nested = registry_dir / slug / "SKILL.md"

    found_path: Path | None = None
    if flat.exists():
        found_path = flat
    elif nested.exists():
        found_path = nested

    available = _available(registry_dir)

    if found_path:
        return {
            "found": True,
            "slug": slug,
            "type": kind,
            "file": found_path.relative_to(vault_root).as_posix(),
            "available": available,
            "errors": [],
        }

    return {
        "found": False,
        "slug": slug,
        "type": kind,
        "file": None,
        "available": available,
        "errors": [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Look up role, hat, prompt, or agent definitions in the vault registry."
    )
    parser.add_argument("--vault-root", default=".", help="Vault root directory.")
    parser.add_argument(
        "--type",
        required=True,
        choices=["role", "hat", "prompt", "agent"],
        help="Definition type: 'role', 'hat', 'prompt', or 'agent'.",
    )
    parser.add_argument("--slug", required=True, help="Slug to look up.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vault_root = Path(args.vault_root).expanduser().resolve()
    slug = (
        normalise_prompt_slug(args.slug)
        if args.type == "prompt"
        else normalise_slug(args.slug)
    )
    result = lookup(vault_root, args.type, slug)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
