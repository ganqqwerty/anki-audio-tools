---
name: add-dep
description: Add or update dependencies in this repository using the correct vendoring, Python dev-dependency, or Svelte dependency workflow. Use when the user asks to introduce, upgrade, or troubleshoot a dependency.
metadata:
  short-description: Add or update repo dependencies
---

# Add Dep

Read `DEVELOPMENT.md` first, then determine which dependency category applies.

## Decision Tree

1. If code in `addon/anki_short_story/` needs it at add-on runtime, it is a **Python runtime dependency** and must be vendored into `addon/anki_short_story/vendor/`.
2. If it is a linter, test tool, type checker, or similar, it is a **Python dev dependency** and must be listed in both `scripts/dev.py` and `pyproject.toml`.
3. If it is for `settings_ui/`, it is a **Svelte dependency** and belongs in `settings_ui/package.json`.

## Python Runtime Dependency

- Install into `addon/anki_short_story/vendor/`
- Remove `.dist-info/` directories
- Verify vendored loading works with the appropriate tests
- Ensure transitive runtime dependencies are also vendored

## Python Dev Dependency

- Add the package to `DEV_DEPS` in `scripts/dev.py`
- Add the package to `[dependency-groups] dev` in `pyproject.toml`
- Run `python3 scripts/dev.py setup`
- If needed, add a matching `dev.py` command
- Verify with `python3 scripts/dev.py check`

## Svelte Dependency

- Use `npm install` or `npm install --save-dev` inside `settings_ui/`
- Rebuild the bundle if runtime code changed
- Verify with `python3 scripts/dev.py test-svelte`

## Never Do

- Never `pip install` runtime dependencies into system Python instead of vendoring them
- Never use `uv add`
- Never run dev tools directly when `scripts/dev.py` has the supported wrapper
- Never update only one of `scripts/dev.py` or `pyproject.toml` for Python dev dependencies
- Never put Python runtime dependencies in `pyproject.toml` instead of vendoring them

## Reporting

Explain:

- which dependency category you chose
- which files were updated
- which verification commands were run
- any follow-up required, such as rebuilding UI bundles or syncing transitive vendored deps
