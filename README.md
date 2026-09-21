# Zentelligence Marketplace

Public distribution point for Zentelligence's agentic AI plugins, with separate marketplace catalogues for Anthropic and OpenAI pointing to shared plugin packages.

---

## Plugins

| Plugin | Description | Ecosystem |
| ------ | ----------- | --------- |
| [context-os](plugins/context-os/) | A structured personal knowledge vault. Human-accessible via Obsidian; AI-operated via plugin. | Claude; ChatGPT and Codex marketplace discovery verified |

---

## Installing a Claude plugin

Add this marketplace, then install a plugin from it:

```shell
/plugin marketplace add zentelligence/marketplace
/plugin install context-os@zentelligence-plugins
```

---

## Installing in ChatGPT desktop or Codex

Add the GitHub marketplace from the plugin directory, or register it through the Codex CLI:

```shell
codex plugin marketplace add zentelligence/marketplace
```

Restart ChatGPT desktop, open the plugin directory, select Zentelligence Plugins, and install ContextOS.

If the marketplace was added before a catalogue fix was published, refresh its GitHub snapshot after the fix reaches the tracked branch:

```shell
codex plugin marketplace upgrade zentelligence-plugins
codex plugin list -m zentelligence-plugins
```

Restart ChatGPT desktop after refreshing. Editing a separate development checkout does not update the registered GitHub snapshot.

### Catalogue compatibility

OpenAI reads `.agents/plugins/marketplace.json`; Claude reads `.claude-plugin/marketplace.json`. Both point to the same `plugins/context-os` directory. The OpenAI entry uses an explicit local source object, installation and authentication policies, and a category. Source paths resolve from the repository root and must begin with `./`.

The missing `./` prefix in the former OpenAI entry caused ContextOS to be skipped while the marketplace itself remained registered. A before-and-after check with the installed Codex CLI reproduced the empty listing and confirmed that correcting this prefix alone restored discovery. The existing Claude-format plugin manifest was sufficient for that check.

Discovery verification does not establish complete runtime compatibility. ContextOS still contains Claude-specific bootstrap instructions and shell scripts; its vault workflows require separate testing in the intended OpenAI execution environment.

See [OpenAI plugin packaging and marketplace metadata](https://developers.openai.com/plugins/build/plugins).

## Structure

```
marketplace/
├── .claude-plugin/
│   └── marketplace.json   Claude-facing catalogue metadata
├── .agents/plugins/
│   └── marketplace.json   Codex-facing catalogue metadata
└── plugins/
    └── <plugin-name>/     One directory per distributed plugin
```

Each plugin directory is a self-contained, cleaned distribution build of its source repository; development artefacts (tests, dev docs, local tooling) are not included.
