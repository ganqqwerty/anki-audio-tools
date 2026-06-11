---
name: doc-maintain
description: Audit and update repository documentation after major refactors, schema changes, hook changes, or migration work. Use when AGENTS.md, ARCHITECTURE.md, TESTING.md, CONFIG_SCHEMA.md, WEBVIEW_AND_TEMPLATES.md, or DEVELOPMENT.md may be stale.
metadata:
  short-description: Audit and sync repo docs
---

# Doc Maintain

Use this skill after major refactors, module renames, config schema changes, hook changes, layer architecture changes, or migration work.

## Ground Truth To Collect

- `addon/anki_audio_quick_editor/*.py`
- `addon/anki_audio_quick_editor/settings/*.py`
- `tests/*.py`
- `tests/test_architecture/**/*.py`
- `settings_ui/tests/**/*.ts`
- `settings_ui/tests/**/*.svelte`
- Top-level keys and nested structure of `addon/anki_audio_quick_editor/config.json`
- Import-linter contract names from `pyproject.toml`
- Layer sets from `tests/test_architecture/conftest.py`
- Fresh architecture archive from `python3 scripts/dev.py graphs-archive`, especially:
  - `docs/archive/architecture_diagrams/YYYY-MM-DD/index.json`
  - `architecture-layers.json`
  - `relationships.json`
  - `webview-injection.json`
  - `bridge-commands.json`

## What To Sync

### `AGENTS.md`

- Workflow helper names and dual terminology: `/doc-maintain` and `$doc-maintain`, `/test` and `$test`, `/add-dep` and `$add-dep`
- Layout table, especially `.claude/commands/` and `.codex/skills/`
- Key facts: Anki version, Python version, symlink path, add-on id
- Pointers to `DEVELOPMENT.md`, `WEBVIEW_AND_TEMPLATES.md`, `CONFIG_SCHEMA.md`, `ANKI_API.md`, and `TESTING.md`
- Testing guidance, especially the rule that a feature is not complete until `python3 scripts/dev.py test-e2e` passes

### `ARCHITECTURE.md`

- Module responsibilities
- Config structure
- Hooks registered in `__init__.py`
- Architecture graph/archive pointers and how to use them
- Import-linter contracts table
- Layer classification table
- AST rules table
- Svelte build paths
- Future enhancements list

### `TESTING.md`

- What's-tested table
- Test file list
- Architecture rules table
- Import-linter contracts table
- Svelte UI tests section

### `CONFIG_SCHEMA.md`

- Config structure must match `config.json`
- `config.get(...)` access patterns must match current usage

### `WEBVIEW_AND_TEMPLATES.md`

- Template file list
- Settings, inline editor, Browser batch, and reviewer WebView entry points
- Bridge protocols and generated bundle paths
- Shared Bits UI tooltip guidance for live settings/editor UI, including the rule to avoid native `title`/SVG `<title>` tooltips

### `DEVELOPMENT.md`

- Two-Python paths
- `DEV_DEPS` sync between `scripts/dev_tasks/setup.py` and `pyproject.toml`
- Vendored package list
- Svelte dependency names

## Workflow

1. Inventory the codebase to gather the current truth.
2. Run `python3 scripts/dev.py graphs-archive`.
   - Use the generated archive to understand module, bridge, webview, and layer relationships.
   - Treat executable contracts and tests as the source of truth when they disagree with generated archive categorization.
   - Run `python3 scripts/dev.py graphs-all` or `python3 scripts/dev.py graphs-check` when the committed human-readable diagrams in `docs/graphs/` may be stale.
3. Diff docs against the current code, tests, config, and graph archive.
4. Make targeted updates instead of broad rewrites. Prefer principle-level explanations, stable source-of-truth pointers, and WHY over duplicated module/function lists.
5. Verify tool config sync:
   - `vulture_whitelist.py` covers hook callbacks and fixtures flagged by vulture
   - `pyproject.toml [tool.bandit] skips` still matches assertion patterns in code
   - `scripts/dev_tasks/setup.py` `DEV_DEPS` matches `[dependency-groups] dev` in `pyproject.toml`
6. Grep for stale patterns before finishing.

## Known Stale Patterns

- `bridge_handler`
- `prompt_tab_ui`
- `prompt_tab_bundle`
- Deleted tab module names: `ai_tab`, `fields_tab`, `params_tab`, `tweaks_tab`, `tts_tab`, `fields_autodetect`, `autodetect_dialog`
- `"period"` as a config key
- Old contract names: `pure-and-bridge-no-upper-layers`, `bridge-py-no-sibling-tabs`
- Claims that `SettingsDialog` is modal
- Large duplicated guidance blocks in `CLAUDE.md` instead of a pointer to `AGENTS.md`

## Reporting

Summarize:

- which docs changed
- what stale facts were corrected
- whether any doc sections still need human confirmation
