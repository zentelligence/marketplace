#!/usr/bin/env python3
"""
agent_shim.py: Generate harness-discoverable sub-agent shims from registry agent definitions.

The operator-managed source of truth is `registry/agents/<slug>.md`. This script derives a Claude harness agent file (the "shim") at `.claude/agents/<slug>.md`
inside the vault, so the runtime can spawn the agent as a sub-agent. Shims are generated artefacts: they embed a content hash of their source definition, are
regenerated whenever the definition drifts, and must never be hand-edited. If the two disagree, the registry definition wins.

Usage:
    python $CLAUDE_PLUGIN_ROOT/scripts/agent_shim.py --vault-root . --slug demo-critic
    python $CLAUDE_PLUGIN_ROOT/scripts/agent_shim.py --vault-root . --slug demo-critic --check
    python $CLAUDE_PLUGIN_ROOT/scripts/agent_shim.py --vault-root . --all

CLI flags:
    --vault-root PATH   Vault root directory (default: cwd).
    --slug SLUG         Agent slug to (re)generate the shim for.
    --all               Process every definition in registry/agents/.
    --check             Report freshness only; never write.

Output JSON fields (per agent):
    slug:        Agent slug processed.
    type:        Always "agent".
    definition:  Vault-relative path to the registry definition.
    shim:        Vault-relative path to the shim, or null when not applicable.
    status:      "generated" | "regenerated" | "fresh" | "stale" (--check only).
    errors:      Blocking errors. Non-empty means no shim was written.

Deterministic tools mapping (definition `tools:` -> shim `tools:` frontmatter):
    read-only    -> Read, Glob, Grep
    read-write   -> Read, Glob, Grep, Write, Edit
    all          -> key omitted (all tools available)
    explicit list-> passed through verbatim
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

AGENTS_DIR = "registry/agents"
SHIM_DIR = ".claude/agents"

REQUIRED_FRONTMATTER = ("name", "description", "model", "tools")
REQUIRED_SECTIONS = (
    "Identity",
    "Method",
    "Inputs contract",
    "Outputs contract",
    "Constraints",
)
VALID_MODELS = {"sonnet", "opus", "haiku", "inherit"}

TOOL_PRESETS = {
    "read-only": "Read, Glob, Grep",
    "read-write": "Read, Glob, Grep, Write, Edit",
}

_HASH_MARKER = re.compile(r"source sha256: ([0-9a-f]{64})")


def normalise_slug(raw: str) -> str:
    """Lowercase and strip characters that cannot appear in a filename slug.

    Mirrors registry_lookup.normalise_slug so both scripts resolve identically.
    """
    slug = raw.strip().lower()
    slug = re.sub(r"[^a-z0-9-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_definition(path: Path) -> dict:
    """Parse and validate a registry agent definition.

    Returns a dict with keys: frontmatter, sections, body, errors. The body is
    everything after the closing frontmatter fence, verbatim. Non-empty errors
    means the definition does not satisfy the binding schema.
    """
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    frontmatter: dict[str, str] = {}
    body = text
    match = re.match(r"\A---\n(.*?)\n---\n?", text, flags=re.DOTALL)
    if match:
        for line in match.group(1).splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                frontmatter[key.strip()] = value.strip()
        body = text[match.end() :].lstrip("\n")
    else:
        errors.append("Definition has no frontmatter block.")

    for field in REQUIRED_FRONTMATTER:
        if not frontmatter.get(field):
            errors.append(f"Missing frontmatter field: {field!r}.")

    model = frontmatter.get("model", "")
    if model and model not in VALID_MODELS:
        errors.append(
            f"Invalid model {model!r}. Must be one of: {', '.join(sorted(VALID_MODELS))}."
        )

    sections: dict[str, str] = {}
    for heading, content in re.findall(
        r"^## (.+?)\n(.*?)(?=^## |\Z)", body, flags=re.DOTALL | re.MULTILINE
    ):
        sections[heading.strip()] = content.strip()

    for section in REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"Missing required section: '## {section}'.")

    return {
        "frontmatter": frontmatter,
        "sections": sections,
        "body": body,
        "errors": errors,
    }


def map_tools(tools_value: str) -> str | None:
    """Map a definition's tools declaration to the shim's tools frontmatter.

    Returns None when the shim should omit the tools key entirely ("all").
    Presets map deterministically; anything else is an explicit tool list and
    passes through verbatim.
    """
    value = tools_value.strip()
    if value == "all":
        return None
    return TOOL_PRESETS.get(value, value)


def build_shim(slug: str, definition_text: str, parsed: dict) -> str:
    """Render the shim file content for a parsed, valid definition."""
    frontmatter = parsed["frontmatter"]
    lines = [
        "---",
        f"name: {slug}",
        f"description: {frontmatter['description']}",
    ]
    if frontmatter["model"] != "inherit":
        lines.append(f"model: {frontmatter['model']}")
    tools = map_tools(frontmatter["tools"])
    if tools is not None:
        lines.append(f"tools: {tools}")
    lines.append("---")
    lines.append("")
    lines.append(
        f"<!-- Generated from {AGENTS_DIR}/{slug}.md "
        f"(source sha256: {_sha256(definition_text)}). "
        "Do not edit: the registry definition wins. "
        "Regenerate with scripts/agent_shim.py. -->"
    )
    lines.append("")
    lines.append(parsed["body"].rstrip("\n"))
    lines.append("")
    return "\n".join(lines)


def _shim_is_fresh(shim_path: Path, definition_text: str) -> bool:
    if not shim_path.exists():
        return False
    match = _HASH_MARKER.search(shim_path.read_text(encoding="utf-8"))
    return bool(match) and match.group(1) == _sha256(definition_text)


def generate(vault_root: Path, slug: str, check_only: bool = False) -> dict:
    """Ensure the shim for one agent exists and matches its definition.

    Writes the shim when missing or stale (unless check_only), and reports the
    resulting status. Invalid or missing definitions produce errors and no shim.
    """
    definition_path = vault_root / AGENTS_DIR / f"{slug}.md"
    result = {
        "slug": slug,
        "type": "agent",
        "definition": f"{AGENTS_DIR}/{slug}.md",
        "shim": None,
        "status": None,
        "errors": [],
    }

    if not definition_path.exists():
        result["errors"].append(
            f"No agent definition at {AGENTS_DIR}/{slug}.md. "
            "Run 'agent create <slug>' to define one."
        )
        return result

    definition_text = definition_path.read_text(encoding="utf-8")
    parsed = parse_definition(definition_path)
    if parsed["errors"]:
        result["errors"] = parsed["errors"]
        return result

    shim_path = vault_root / SHIM_DIR / f"{slug}.md"
    result["shim"] = f"{SHIM_DIR}/{slug}.md"

    if _shim_is_fresh(shim_path, definition_text):
        result["status"] = "fresh"
        return result

    if check_only:
        result["status"] = "stale"
        return result

    existed = shim_path.exists()
    shim_path.parent.mkdir(parents=True, exist_ok=True)
    shim_path.write_text(build_shim(slug, definition_text, parsed), encoding="utf-8")
    result["status"] = "regenerated" if existed else "generated"
    return result


def generate_all(vault_root: Path, check_only: bool = False) -> list[dict]:
    """Process every definition in registry/agents/, skipping index.md."""
    agents_dir = vault_root / AGENTS_DIR
    results: list[dict] = []
    if not agents_dir.exists():
        return results
    for path in sorted(agents_dir.glob("*.md")):
        if path.stem == "index":
            continue
        results.append(generate(vault_root, path.stem, check_only=check_only))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate harness sub-agent shims from registry agent definitions."
    )
    parser.add_argument("--vault-root", default=".", help="Vault root directory.")
    parser.add_argument("--slug", help="Agent slug to process.")
    parser.add_argument(
        "--all", action="store_true", help="Process every agent definition."
    )
    parser.add_argument(
        "--check", action="store_true", help="Report freshness only; never write."
    )
    args = parser.parse_args()
    if bool(args.slug) == args.all:
        parser.error("Provide exactly one of --slug or --all.")
    return args


def main() -> None:
    args = parse_args()
    vault_root = Path(args.vault_root).expanduser().resolve()

    if args.all:
        results = generate_all(vault_root, check_only=args.check)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        if any(r["errors"] for r in results):
            sys.exit(1)
    else:
        result = generate(vault_root, normalise_slug(args.slug), check_only=args.check)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["errors"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
