# Zentelligence Marketplace

Public distribution point for Zentelligence's agentic AI plugins.

---

## Plugins

| Plugin | Description | Ecosystem |
| ------ | ----------- | --------- |
| [context-os](plugins/context-os/) | A structured personal knowledge vault. Human-accessible via Obsidian; AI-operated via Claude Cowork. | Claude |

---

## Installing a Claude plugin

Add this marketplace, then install a plugin from it:

```shell
/plugin marketplace add zentelligence/marketplace
/plugin install context-os@zentelligence-plugins
```

---

## Structure

```
marketplace/
├── .claude-plugin/
│   └── marketplace.json   Claude-facing catelogue metadata
├── .agents/plugins/
│   └── marketplace.json   Codex-facing catalogue metadata
└── plugins/
    └── <plugin-name>/     One directory per distributed plugin
```

Each plugin directory is a self-contained, cleaned distribution build of its source repository; development artefacts (tests, dev docs, local tooling) are not included.
