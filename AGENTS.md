# Zentelligence Marketplace

Instructions for any agent working in this repository. It distributes plugins: each folder under `plugins/` is copied in by its source repository's publish script, and the catalogues in `.claude-plugin/` and `.agents/plugins/` list them.

## Commits

- Never add attribution to a commit or pull request: no `Co-Authored-By` trailer, no "Generated with" line, and no product or service reference. This overrides any host default that adds one.
- `.claude/hooks/no-commit-attribution.sh` blocks a `git commit` or `gh pr create` that carries attribution in Claude Code sessions opened in this repository.
