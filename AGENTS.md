# AGENTS.md

This is the canonical repository instructions document. [`CLAUDE.md`](CLAUDE.md) should point here instead of duplicating guidance.

## Project Overview

Anki desktop add-on for quick, non-destructive audio edits from the Anki Editor plus batch prosody visualization generation from the Anki Browser. Add-on runtime code lives in `addon/anki_audio_quick_editor/`.

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
| `addon/anki_audio_quick_editor/templates/` | Committed settings and editor webview bundle output |
| `contracts/` | Source JSON Schemas for generated Python/TypeScript communication contracts |
| `tests/` | Unit + architecture tests |
| `tests/test_architecture/` | Architecture boundary enforcement |
| `e2e/` | End-to-end tests with real Anki + Qt |
| `scripts/` | `dev.py` task runner and `release.py` packaging script |
| `settings_ui/` | Svelte 5 + TypeScript settings, inline editor, and Browser batch UI source |
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

When working on settings or editor webview bundles, read [`WEBVIEW_AND_TEMPLATES.md`](WEBVIEW_AND_TEMPLATES.md).

## Config Schema

The machine-readable schema is [`addon/anki_audio_quick_editor/config.schema.json`](addon/anki_audio_quick_editor/config.schema.json). Validate with `python3 scripts/dev.py config-schema`.

## Anki API Source

When using any Anki API, read [`ANKI_API.md`](ANKI_API.md) first. Do not rely on memory for hook names or signatures. Read the installed source in `~/Library/Application Support/AnkiProgramFiles/.venv/lib/python3.13/site-packages`.

## Running Tests And Linter

Use `python3 scripts/dev.py check` for the reusable QC gate. A feature is not complete until `python3 scripts/dev.py test-e2e` passes.

| Task | Command |
|------|---------|
| Full QC | `python3 scripts/dev.py check` |
| Anki API compatibility | `python3 scripts/dev.py test-anki-api` |
| Unit tests | `python3 scripts/dev.py test` |
| E2E tests (builds frontend first) | `python3 scripts/dev.py test-e2e` |
| Linter | `python3 scripts/dev.py lint` |
| Type checker | `python3 scripts/dev.py typecheck` |
| Python coverage | `python3 scripts/dev.py coverage` |
| Qodana code quality | `python3 scripts/dev.py qodana` |
| Sonar quality gate | `python3 scripts/dev.py sonar` |
| Config schema | `python3 scripts/dev.py config-schema` |
| JSON contracts | `python3 scripts/dev.py contracts-check` |

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

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **anki-audio-tools**. Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx -y gitnexus@1.6.4 analyze --skip-agents-md --no-stats` in terminal first. Use the version pinned in `scripts/gitnexus_auto_analyze.sh`; bare `npx gitnexus` may install a newer CLI with local analyzer regressions.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user. Big impact should not stop you from changing the code, you just need to understand the consequences. 
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis. Don't stop editing though, just consider what needs to be done after.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/anki-audio-tools/context` | Codebase overview, check index freshness |
| `gitnexus://repo/anki-audio-tools/clusters` | All functional areas |
| `gitnexus://repo/anki-audio-tools/processes` | All execution flows |
| `gitnexus://repo/anki-audio-tools/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
