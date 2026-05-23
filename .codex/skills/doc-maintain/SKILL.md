---
name: doc-maintain
description: Audit and update repository documentation after major refactors, schema changes, hook changes, or migration work. Use when AGENTS.md, ARCHITECTURE.md, TESTING.md, CONFIG_SCHEMA.md, WEBVIEW_AND_TEMPLATES.md, or DEVELOPMENT.md may be stale.
metadata:
  short-description: Audit and sync repo docs
---

# Doc Maintain

Use this skill after major refactors, module renames, config schema changes, hook changes, layer architecture changes, or migration work.

## Ground Truth To Collect

- `addon/anki_short_story/*.py` and `addon/anki_short_story/settings/*.py`
- `tests/*.py`
- `tests/test_architecture/*.py`
- `settings_ui/tests/**/*.ts`
- Top-level keys and nested structure of `addon/anki_short_story/config.json`
- Import-linter contract names from `pyproject.toml`
- Layer sets from `tests/test_architecture/conftest.py`

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
- Story generator architecture, entry points, and dialog class names
- Shared Bits UI tooltip guidance for live settings/editor UI, including the rule to avoid native `title`/SVG `<title>` tooltips

### `DEVELOPMENT.md`

- Two-Python paths
- `DEV_DEPS` sync between `scripts/dev.py` and `pyproject.toml`
- Vendored package list
- Svelte dependency names

## Workflow

1. Inventory the codebase to gather the current truth.
2. Diff docs against the current code and config.
3. Make targeted updates instead of broad rewrites.
4. Verify tool config sync:
   - `vulture_whitelist.py` covers hook callbacks and fixtures flagged by vulture
   - `pyproject.toml [tool.bandit] skips` still matches assertion patterns in code
   - `scripts/dev.py` `DEV_DEPS` matches `[dependency-groups] dev` in `pyproject.toml`
5. Grep for stale patterns before finishing.

## Known Stale Patterns

- `bridge_handler`
- `prompt_tab_ui`
- `prompt_tab_bundle`
- Deleted tab module names: `ai_tab`, `fields_tab`, `params_tab`, `tweaks_tab`, `tts_tab`, `fields_autodetect`, `autodetect_dialog`
- `"period"` as a config key
- Old contract names: `pure-and-bridge-no-upper-layers`, `bridge-py-no-sibling-tabs`
- `setModal(True)` or claims that the dialog is modal
- Large duplicated guidance blocks in `CLAUDE.md` instead of a pointer to `AGENTS.md`

## Reporting

Summarize:

- which docs changed
- what stale facts were corrected
- whether any doc sections still need human confirmation
