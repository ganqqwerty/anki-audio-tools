# AGENTS.md

This is the canonical repository instructions document. [`CLAUDE.md`](CLAUDE.md) should point here instead of duplicating guidance.

## Project Overview

Anki desktop add-on for quick, non-destructive audio edits from the Anki Editor. Add-on runtime code lives in `addon/anki_audio_quick_editor/`.

## Workflow Helpers

| Workflow | Claude Code | Codex |
|----------|-------------|-------|
| Documentation maintenance | `/doc-maintain` | `$doc-maintain` |
| Full QC suite | `/test` | `$test` |
| Dependency changes | `/add-dep` | `$add-dep` |

## Documentation Maintenance

After major refactors, package renames, config schema changes, hook changes, or architecture updates, run `/doc-maintain` in Claude Code or use the `$doc-maintain` Codex skill.

## Layout

| Directory | Contents |
|-----------|----------|
| `addon/anki_audio_quick_editor/` | Audio Quick Editor runtime package |
| `addon/anki_audio_quick_editor/settings/` | Settings dialog Python shell + bridge backend |
| `addon/anki_audio_quick_editor/templates/` | Committed webview bundle output |
| `tests/` | Unit + architecture tests |
| `tests/test_architecture/` | Architecture boundary enforcement |
| `e2e/` | End-to-end tests with real Anki + Qt |
| `scripts/` | `dev.py` task runner and `release.py` packaging script |
| `settings_ui/` | Svelte 5 + TypeScript settings UI source |
| `.claude/commands/` | Claude Code workflow commands |
| `.codex/skills/` | Repo-local Codex skills mirroring shared workflows |

## Key Facts

- Anki desktop add-ons are Python, not Java.
- Anki on this machine is version 25.09 and uses Python 3.13.5.
- Add-ons directory: `~/Library/Application Support/Anki2/addons21/`
- The local development add-on ID is `1000000002`.
- MVP audio processing requires system `ffmpeg` and `ffprobe`.
- There is no Python build step. Anki loads `__init__.py` directly.

## Development Setup & Dependencies

Read [`DEVELOPMENT.md`](DEVELOPMENT.md) before changing dependencies or troubleshooting the two-Python setup. Use `/add-dep` or `$add-dep` when adding or updating dependencies.

## Templates & WebView

When working on the settings webview bundle, read [`WEBVIEW_AND_TEMPLATES.md`](WEBVIEW_AND_TEMPLATES.md).

## Config Schema

The machine-readable schema is [`addon/anki_audio_quick_editor/config.schema.json`](addon/anki_audio_quick_editor/config.schema.json). Validate with `python3 scripts/dev.py config-schema`.

## Anki API Source

When using any Anki API, read [`ANKI_API.md`](ANKI_API.md) first. Do not rely on memory for hook names or signatures. Read the installed source in `~/Library/Application Support/AnkiProgramFiles/.venv/lib/python3.13/site-packages`.

## Running Tests And Linter

Use `python3 scripts/dev.py check` for the reusable QC gate. A feature is not complete until `python3 scripts/dev.py test-e2e` passes.

| Task | Command |
|------|---------|
| Full QC | `python3 scripts/dev.py check` |
| Unit tests | `python3 scripts/dev.py test` |
| E2E tests | `python3 scripts/dev.py test-e2e` |
| Linter | `python3 scripts/dev.py lint` |
| Type checker | `python3 scripts/dev.py typecheck` |
| Config schema | `python3 scripts/dev.py config-schema` |

## Planning Features

Plans should specify tests before implementation. Prefer a test-first approach when practical.

## Building A Release

```bash
python3 scripts/release.py
```

This builds `dist/anki-audio-quick-editor-<version>.ankiaddon`.

## Debugging

Read [`DEBUGGING.md`](DEBUGGING.md) for the full guide. Short version:

| Method | When to use |
|--------|-------------|
| Anki error popup | Startup/load crash with traceback |
| `showInfo("...")` | Quick value check |
| `print(...)` | Terminal output while launching Anki from a shell |
| VS Code + debugpy | Breakpoints and step-through debugging |

## Logging

Use the unified package logger. File logging is initialized from the add-on bootstrap after the main window is ready.

## Code Style

- Use types wherever possible.
- Keep functions self-documenting.
- Prefer extracting named helpers over explanatory inline comments.
- Add docstrings for public APIs.
- Prefer pure functions for logic that does not need Anki objects.
- Keep user preferences configuration-driven, not hardcoded.

## GitNexus — Optional Code Intelligence

If GitNexus is available for this repo, use it to inspect unfamiliar code, assess blast radius before large changes, and verify changed execution flows before finishing a refactor.

## Commit Messages

- Write a short imperative subject line.
- Keep the subject focused and specific.
- Use the body when you need to explain why the change matters.
- Explain the behavior or system impact, not just the touched files.
