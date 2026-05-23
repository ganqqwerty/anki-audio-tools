# Max File Lines Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce a 500-line hard maximum and 400-line warning threshold for hand-maintained Python, TypeScript, Svelte, and JavaScript files, then refactor current oversized files so the gate passes without permanent allowlists.

**Architecture:** Keep public compatibility facades where other modules already import broad modules, then move behavior into high-cohesion modules with explicit side-effect boundaries. Core audio modules stay import-safe and Anki-free; UI adapter modules own Anki, Qt, web eval, media writes, and background scheduling. Test files are split by behavior slice so failures point at the same responsibility as the production module.

**Tech Stack:** Python 3.13, Anki add-on runtime, pytest, import-linter, existing architecture tests, `scripts/dev.py`, Svelte 5, TypeScript, ESLint 9, Vitest.

---

## Current Findings

Measured on 2026-05-18. Hand-maintained files above 500 lines block the final hard gate:

| File | Lines | Reason it grew |
| --- | ---: | --- |
| `tests/test_audio_processor.py` | 1859 | Tests all audio discovery, command building, external execution, pause pipeline, RNNoise, playback, and fixtures in one file. |
| `addon/anki_audio_quick_editor/editor_integration.py` | 1667 | Combines hook registration, bridge dispatch, session state, render replacement, region delete, playback, prosody analysis, web eval, and settings/file actions. |
| `tests/test_editor_integration.py` | 1436 | Mirrors the monolithic editor module and also contains file reveal tests. |
| `addon/anki_audio_quick_editor/audio_processor.py` | 1272 | Combines executable discovery, command construction, subprocess execution, render orchestration, manifests, filenames, support incidents, and playback segment rendering. |
| `settings_ui/tests/editor-inline.integration.test.ts` | 1241 | Covers many editor-inline workflows in one integration suite. |
| `scripts/dev.py` | 923 | Contains environment discovery, subprocess runner, every command implementation, command registry, and CLI parsing. |
| `e2e/test_editor_processing_workflow.py` | 908 | Multiple editor processing scenarios and helpers in one workflow file. |
| `settings_ui/src/editor-inline/actions.ts` | 799 | Public action facade also owns status controls, command dispatch, selection adapters, graph requests, playback, audio clock wrappers, and bridge helpers. |
| `e2e/test_editor_region_loop_workflow.py` | 794 | Region selection, looping, replacement, and helper logic share one file. |
| `e2e/test_editor_graph_workflow.py` | 672 | Graph rendering scenarios and shared setup live together. |
| `e2e/test_editor_deep_filter_workflow.py` | 543 | DeepFilter success/failure flows and fixtures share one file. |
| `tests/test_settings_commands.py` | 519 | Settings command, diagnostics, report, and log behavior share one file. |
| `addon/anki_audio_quick_editor/browser_integration.py` | 511 | Hook registration, Qt dialog, background runner, note mutation, progress, and reporting share one module. |

One file currently sits in the warning band:

| File | Lines |
| --- | ---: |
| `tests/conftest.py` | 488 |

Generated files are explicitly excluded from line-length enforcement. Current generated examples include `addon/anki_audio_quick_editor/contracts_generated.py` at 559 lines and `settings_ui/src/lib/generated/contracts.ts`.


- `audio_processor.py` has MEDIUM upstream file impact with direct production importers: `prosody_praat.py`, `prosody_fallback.py`, `editor_integration.py`, `diagnostics.py`, and `batch_operations.py`. Keep `audio_processor.py` as a facade during the split.
- `editor_integration.py` and `browser_integration.py` have LOW file-level impact because `__init__.py` is the direct production importer. Internal symbol movement is still risky because tests and e2e cover many callback flows.

## Design Rules

- Single responsibility: one file owns one reason to change.
- High cohesion: command builders stay together; external process execution stays together; editor playback stays separate from graph analysis.
- Low coupling: keep public facades for compatibility, but new leaf modules do not import facade modules.
- Dependency direction: UI adapter modules may import core modules; import-safe core modules never import UI adapter modules.
- Side-effect isolation: subprocess, media writes, note updates, web eval, threading, and Anki imports remain visible in module contracts.
- Debugging: preserve command names, run IDs, support incident records, and log context while moving code.
- Enforcement: final gates have no permanent allowlists for hand-maintained source. Generated files are ignored by a centralized generated-file predicate, not by broad ad hoc directory skips.

## Target File-Line Policy

Python:

- Add a canonical `max-file-lines` checker under `scripts/dev_tasks/file_lines.py`.
- Count physical lines, including comments and blank lines.
- Scan `.py` files under `addon/anki_audio_quick_editor`, `tests`, `e2e`, and `scripts`.
- Ignore cache/runtime/build artifacts: `__pycache__`, `.pytest_cache`, `vendor`, `templates`, `aqe_artifacts`, `.mypy_cache`, and generated frontend output.
- Ignore generated Python outputs through a named predicate, including `addon/anki_audio_quick_editor/contracts_generated.py` and any future generated contract package files.
- Print `WARNING` for files with 401-500 lines.
- Return nonzero for files with more than 500 lines.
- Add `python3 scripts/dev.py file-lines` and include it in `python3 scripts/dev.py check`.
- Add `tests/test_architecture/test_rule22_python_file_lengths.py` as the hard pytest guard.

Frontend:

- Add ESLint `max-lines` as a warning at 400 lines for hand-maintained `src/**/*.ts`, `src/**/*.svelte`, and `tests/**/*.ts`.
- Keep generated frontend files ignored, including `src/lib/generated/**` and committed webview bundle output under the add-on templates directory.
- Add a second ESLint hard-cap config or script that runs the same `max-lines` rule as an error at 500 lines for hand-maintained files.
- Include the hard-cap script in `settings_ui/package.json` `validate`.
- Update `settings_ui/tests/frontend-architecture.test.ts` to remove the temporary `actions.ts` 800-line allowance and align the production frontend hard limit with 500.

## Target Module Contracts

Audio core:

| Module | Responsibility | Allowed dependencies | Side effects |
| --- | --- | --- | --- |
| `audio_processor.py` | Backward-compatible facade reexporting public audio APIs. | New audio modules only. | None directly. |
| `audio_tools.py` | Locate ffmpeg, ffprobe, DeepFilter, and RNNoise bundle paths. | `errors` | Filesystem path lookup only. |
| `audio_commands.py` | Build ffmpeg, DeepFilter, RNNoise, region-delete, playback, and encode command arrays plus filter strings. | `audio_pipeline`, `audio_state` | None. |
| `audio_external.py` | Run external commands and normalize external error messages. | `errors`, `support` | `SUBPROCESS_RUN` |
| `audio_artifacts.py` | Create pause pipeline run directories, source/artifact records, checksums, and manifest payloads. | `audio_pipeline` | `TEMP_FILESYSTEM_CLEANUP` only where directory creation requires it. |
| `audio_rendering.py` | Orchestrate standard render, region delete render, playback segment render, and filename/temp path helpers. | `audio_commands`, `audio_external`, `audio_tools`, `audio_state`, `errors` | Temp files and subprocess through `audio_external`. |
| `audio_noise_reduction.py` | Orchestrate standard DeepFilter denoise and RNNoise denoise. | `audio_commands`, `audio_external`, `audio_tools`, `audio_state`, `errors`, `support` | Temp files and subprocess through `audio_external`. |
| `audio_pause_pipeline.py` | Orchestrate DeepFilter pause speedup pipeline and manifest retention. | `audio_artifacts`, `audio_commands`, `audio_external`, `audio_pipeline`, `audio_tools`, `audio_state`, `errors`, `support` | Temp files and subprocess through `audio_external`. |

Editor UI adapter:

| Module | Responsibility | Allowed dependencies | Side effects |
| --- | --- | --- | --- |
| `editor_integration.py` | Register Anki editor hooks and delegate callbacks. | Editor submodules, `editor_ui` | `GUI_HOOK_REGISTRATION` |
| `editor_session.py` | `UndoEntry`, `UndoHistory`, `RegionDeleteRequest`, `EditorSession`, and session reset primitives. | `audio_state`, `prosody_types` | None. |
| `editor_media.py` | Resolve current audio fields, sound refs, media paths, and media reset decisions. | `sound_refs`, `errors` | None directly. |
| `editor_frontend.py` | Web eval helpers, busy/status updates, graph redraw scheduling expressions. | `contracts_generated`, `editor_session` | `WEB_EVAL` |
| `editor_bridge.py` | Decode bridge payloads and route commands to focused handlers. | `editor_actions`, editor submodules | Web callback interaction only through `editor_frontend`. |
| `editor_processing.py` | Standard processing, DeepFilter denoise, RNNoise, history restoration after render. | `audio_processor`, `editor_media`, `editor_frontend`, `sound_refs`, `support`, `errors` | `MEDIA_WRITE`, `THREAD_SPAWN`, `BACKGROUND_TASK_DISPATCH` |
| `editor_region_delete.py` | Region delete request parsing, async region deletion, and replacement. | `audio_processor`, `editor_media`, `editor_frontend`, `sound_refs`, `errors` | `MEDIA_WRITE`, `THREAD_SPAWN`, `TEMP_FILESYSTEM_CLEANUP` |
| `editor_playback.py` | Native/html playback state, playback segment rendering, and playback cleanup. | `audio_processor`, `editor_frontend`, `editor_media`, `prosody_types` | `THREAD_SPAWN`, `WEB_EVAL`, `TEMP_FILESYSTEM_CLEANUP` |
| `editor_analysis.py` | Prosody analysis requests, stale-result checks, cache use, and graph completion/failure. | `prosody_cache`, `prosody_types`, `editor_frontend`, `editor_media` | `BACKGROUND_TASK_DISPATCH`, `WEB_EVAL` |
| `editor_settings_actions.py` | Open settings, refresh editor after save, reveal current audio file. | `file_reveal`, `editor_frontend`, `editor_media` | Settings callback and file reveal side effects. |

Browser UI adapter:

| Module | Responsibility | Allowed dependencies | Side effects |
| --- | --- | --- | --- |
| `browser_integration.py` | Register browser hooks and open the batch dialog. | `browser_dialog`, `browser_runner` | `GUI_HOOK_REGISTRATION` |
| `browser_dialog.py` | Qt dialog layout, progress display, log copy, cancel/close behavior. | `audio_operations`, `audio_state`, `browser_runner` types | Qt only. |
| `browser_runner.py` | Background batch scheduling, note processing, note mutation, media writes, and undo merge. | `batch_operations`, `audio_state`, `browser_report` | `MEDIA_WRITE`, `NOTE_UPDATE`, `UNDO_MERGE`, `BACKGROUND_TASK_DISPATCH` |
| `browser_report.py` | `BatchRunReport`, result line formatting, and summary text. | `batch_operations` types | None. |

Frontend editor-inline:

| Module | Responsibility | Allowed dependencies |
| --- | --- | --- |
| `actions.ts` | Compatibility facade that reexports public actions. |
| `control-actions.ts` | Busy state, global status, visualizer status, command button labels. |
| `command-actions.ts` | `send`, command payload focus, processing messages. |
| `selection-actions.ts` | Selection controller and gesture adapters. |
| `graph-actions.ts` | Graph request, default graph queue, renderer callbacks, reset after edit. |
| `playback-actions.ts` | Playback request construction, engine choice, html/native playback command flow. |
| `audio-clock-actions.ts` | Thin wrappers around `audio-clock.ts` only if compatibility requires them. |
| `editor-runtime-deps.ts` | Shared dependency builders for controller modules, avoiding cycles between action modules. |

Generated contracts:

- Keep `addon/anki_audio_quick_editor/contracts_generated.py` as generator-owned output.
- Do not refactor generated output to satisfy human maintainability rules.
- Make line enforcement, architecture file-size rules, and ESLint max-lines ignore generated files through explicit generated-file checks.
- Keep `python3 scripts/dev.py contracts-check` as the source of truth for generated contract correctness.

Dev runner:

- Keep `scripts/dev.py` as the CLI facade.
- Move reusable process execution to `scripts/dev_tasks/process.py`.
- Move Python/Anki environment discovery to `scripts/dev_tasks/python_env.py`.
- Move command implementations to cohesive modules: `quality.py`, `tests.py`, `frontend.py`, `contracts.py`, `coverage.py`, `release.py`, and `file_lines.py`.
- Keep command names and help output stable.

## Data Flow After Refactor

Editor processing:

1. Svelte UI calls `send()` or playback/graph action.
2. `editor_bridge.py` decodes the payload into `EditorCommandPayload`.
3. Command-specific editor module validates session and source media.
4. Audio core facade delegates to focused renderer modules.
5. Renderer returns `AudioProcessingResult` or raises `AudioProcessingError`.
6. Editor module writes media, records undo/session state, and updates frontend status.
7. Support incidents keep the same command, stderr/stdout, manifest, and log context.

Pause pipeline:

1. `audio_pause_pipeline.py` creates a run directory through `audio_artifacts.py`.
2. `audio_tools.py` resolves required executables.
3. `audio_commands.py` builds every command deterministically.
4. `audio_external.py` runs commands and normalizes failures.
5. `audio_pipeline.py` parses intervals and builds the pure timeline/filter plan.
6. `audio_artifacts.py` writes final manifest records.

Browser batch:

1. `browser_integration.py` creates `BatchRunRequest` through the dialog.
2. `browser_runner.py` owns background scheduling and note iteration.
3. `batch_operations.py` remains the import-safe operation engine.
4. `browser_report.py` formats progress and final summary.
5. `browser_dialog.py` only displays progress and receives completion.

## Test Failure Discipline During Refactoring

Some tests will fail while responsibilities move between modules. Every failure must be diagnosed before changing code or changing the test. Do not treat failures as mechanical import churn until the cause is understood.

Maintain a running failure log at `docs/superpowers/plans/2026-05-18-max-file-lines-test-failure-log.md`. Create it when the refactor starts and append an entry for each failing test that is not an obvious typo fixed immediately in the same edit. The log is especially important for tests that fail because they depended on private implementation details, fixture leakage, file layout, timing assumptions, generated artifact freshness, or other bad reasons.

Each log entry must include:

- failing command and test id
- observed failure message
- why the test failed
- classification: behavior regression, public contract break, brittle internal-detail dependency, bad fixture/setup coupling, generated artifact freshness, environment/tooling issue, or unclear
- decision: fix production code, preserve compatibility facade, rewrite test around public behavior, delete duplicate coverage, or investigate further
- follow-up owner/task when the failure reveals design debt outside the current slice

When a test is classified as a brittle internal-detail dependency, rewrite it to assert observable behavior or a documented module contract before proceeding. Do not carry brittle tests forward just because they are easy to update.

## Implementation Tasks

### Task 1: Add File-Line Enforcement Skeleton

**Files:**

- Create: `scripts/dev_tasks/__init__.py`
- Create: `scripts/dev_tasks/file_lines.py`
- Create: `docs/superpowers/plans/2026-05-18-max-file-lines-test-failure-log.md`
- Modify: `scripts/dev.py`
- Modify: `settings_ui/eslint.config.js`
- Create: `settings_ui/eslint.max-lines.config.js`
- Modify: `settings_ui/package.json`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`

- [ ] Add the Python scanner with constants `WARN_LIMIT = 400` and `ERROR_LIMIT = 500`.
- [ ] Create the test failure log with the entry template from the plan.
- [ ] Add `cmd_file_lines()` to `scripts/dev.py`, but do not wire it into `check` until all current hard failures are split.
- [ ] Add ESLint warning config for `max-lines` at 400.
- [ ] Add hard-cap ESLint config for `max-lines` at 500.
- [ ] Run `python3 scripts/dev.py file-lines`; expected result is failure listing the current hand-maintained hard offenders and no generated files.
- [ ] Run `cd settings_ui && npm run lint`; expected result includes `max-lines` warnings for oversized frontend files.
- [ ] Run `cd settings_ui && npm run lint:max-lines`; expected result is failure for frontend files above 500.

### Task 2: Lock Down Generated File Ignores

**Files:**

- Modify: `scripts/dev_tasks/file_lines.py`
- Modify: `settings_ui/eslint.config.js`
- Modify: `settings_ui/eslint.max-lines.config.js`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`
- Modify: `TESTING.md`

- [ ] Add tests for generated Python ignore matching, including `addon/anki_audio_quick_editor/contracts_generated.py`.
- [ ] Add tests for generated frontend ignore matching, including `settings_ui/src/lib/generated/contracts.ts`.
- [ ] Keep generated file ignores explicit and narrow: generated contract output, generated frontend contract output, committed template bundle output, and runtime artifact directories.
- [ ] Run `python3 scripts/dev.py file-lines`; expected result excludes `contracts_generated.py`.
- [ ] Run `cd settings_ui && npm run lint:max-lines`; expected result excludes `src/lib/generated/contracts.ts`.
- [ ] Run `python3 scripts/dev.py contracts-check`; expected result still verifies generated contract staleness.

### Task 3: Split `audio_processor.py`

**Files:**

- Modify: `addon/anki_audio_quick_editor/audio_processor.py`
- Create: `addon/anki_audio_quick_editor/audio_tools.py`
- Create: `addon/anki_audio_quick_editor/audio_commands.py`
- Create: `addon/anki_audio_quick_editor/audio_external.py`
- Create: `addon/anki_audio_quick_editor/audio_artifacts.py`
- Create: `addon/anki_audio_quick_editor/audio_rendering.py`
- Create: `addon/anki_audio_quick_editor/audio_noise_reduction.py`
- Create: `addon/anki_audio_quick_editor/audio_pause_pipeline.py`
- Modify: `tests/test_architecture/contracts.py`
- Modify: `pyproject.toml`

- [ ] Move path discovery functions to `audio_tools.py`.
- [ ] Move command/filter builders to `audio_commands.py`.
- [ ] Move subprocess execution and external error rendering to `audio_external.py`.
- [ ] Move manifest/run-directory/checksum helpers to `audio_artifacts.py`.
- [ ] Move standard render, region delete render, playback render, filename, and temp path helpers to `audio_rendering.py`.
- [ ] Move DeepFilter and RNNoise denoise orchestration to `audio_noise_reduction.py`.
- [ ] Move pause speedup orchestration to `audio_pause_pipeline.py`.
- [ ] Keep `audio_processor.py` as a facade exporting the same public names.
- [ ] Update architecture contracts and import-linter source module lists.
- [ ] Run `python3 scripts/dev.py test tests/test_audio_processor.py`.
- [ ] Run `python3 scripts/dev.py architecture-report`.
- [ ] Run `python3 scripts/dev.py file-lines`; expected result still fails on other oversized files, but not `audio_processor.py`.

### Task 4: Split Audio Processor Tests

**Files:**

- Modify/delete: `tests/test_audio_processor.py`
- Create: `tests/audio_fixtures.py`
- Create: `tests/test_audio_tools.py`
- Create: `tests/test_audio_commands.py`
- Create: `tests/test_audio_rendering.py`
- Create: `tests/test_audio_noise_reduction.py`
- Create: `tests/test_audio_pause_pipeline.py`
- Create: `tests/test_audio_playback_rendering.py`

- [ ] Move generated WAV/PCM fixture helpers into `tests/audio_fixtures.py`.
- [ ] Move executable discovery tests to `tests/test_audio_tools.py`.
- [ ] Move filter and command construction tests to `tests/test_audio_commands.py`.
- [ ] Move standard render, region delete, filename, and temp path tests to `tests/test_audio_rendering.py`.
- [ ] Move DeepFilter/RNNoise denoise tests to `tests/test_audio_noise_reduction.py`.
- [ ] Move pause speedup and manifest tests to `tests/test_audio_pause_pipeline.py`.
- [ ] Move playback segment tests to `tests/test_audio_playback_rendering.py`.
- [ ] Run `python3 scripts/dev.py test tests/test_audio_tools.py tests/test_audio_commands.py tests/test_audio_rendering.py tests/test_audio_noise_reduction.py tests/test_audio_pause_pipeline.py tests/test_audio_playback_rendering.py`.

### Task 5: Split `editor_integration.py`

**Files:**

- Modify: `addon/anki_audio_quick_editor/editor_integration.py`
- Create: `addon/anki_audio_quick_editor/editor_session.py`
- Create: `addon/anki_audio_quick_editor/editor_media.py`
- Create: `addon/anki_audio_quick_editor/editor_frontend.py`
- Create: `addon/anki_audio_quick_editor/editor_bridge.py`
- Create: `addon/anki_audio_quick_editor/editor_processing.py`
- Create: `addon/anki_audio_quick_editor/editor_region_delete.py`
- Create: `addon/anki_audio_quick_editor/editor_playback.py`
- Create: `addon/anki_audio_quick_editor/editor_analysis.py`
- Create: `addon/anki_audio_quick_editor/editor_settings_actions.py`
- Modify: `tests/test_architecture/contracts.py`
- Modify: `pyproject.toml`

- [ ] Move session dataclasses and undo history into `editor_session.py`.
- [ ] Move current field/source/media resolution helpers into `editor_media.py`.
- [ ] Move web eval, busy state, visualizer status, and graph redraw eval helpers into `editor_frontend.py`.
- [ ] Move bridge payload decode and command routing into `editor_bridge.py`.
- [ ] Move render/replace and special transform flows into `editor_processing.py`.
- [ ] Move selection deletion flow into `editor_region_delete.py`.
- [ ] Move native/html playback flow into `editor_playback.py`.
- [ ] Move prosody graph analysis flow into `editor_analysis.py`.
- [ ] Move settings open, settings refresh, and reveal-current-file actions into `editor_settings_actions.py`.
- [ ] Keep `register_editor_hooks()` and Anki hook callbacks in `editor_integration.py`.
- [ ] Update broad exception allowlist entries to point to moved functions with the same reasons.
- [ ] Run `python3 scripts/dev.py test tests/test_editor_integration.py`.
- [ ] Run `python3 scripts/dev.py test-e2e` after the editor split completes because callbacks cross Python, webview, and Anki boundaries.

### Task 6: Split Editor Integration Tests

**Files:**

- Modify/delete: `tests/test_editor_integration.py`
- Create: `tests/test_editor_session.py`
- Create: `tests/test_editor_bridge.py`
- Create: `tests/test_editor_processing.py`
- Create: `tests/test_editor_region_delete.py`
- Create: `tests/test_editor_playback.py`
- Create: `tests/test_editor_analysis.py`
- Create: `tests/test_editor_settings_actions.py`
- Create: `tests/test_file_reveal.py`

- [ ] Move undo/session/reset tests to `tests/test_editor_session.py`.
- [ ] Move bridge command and pending payload tests to `tests/test_editor_bridge.py`.
- [ ] Move render replacement and denoise tests to `tests/test_editor_processing.py`.
- [ ] Move region delete parser/replacement tests to `tests/test_editor_region_delete.py`.
- [ ] Move playback and cursor tests to `tests/test_editor_playback.py`.
- [ ] Move graph analysis and stale completion tests to `tests/test_editor_analysis.py`.
- [ ] Move settings and current audio file actions to `tests/test_editor_settings_actions.py`.
- [ ] Move reveal-file tests to `tests/test_file_reveal.py`.
- [ ] Run the new test files directly, then run `python3 scripts/dev.py test`.

### Task 7: Split `browser_integration.py`

**Files:**

- Modify: `addon/anki_audio_quick_editor/browser_integration.py`
- Create: `addon/anki_audio_quick_editor/browser_dialog.py`
- Create: `addon/anki_audio_quick_editor/browser_runner.py`
- Create: `addon/anki_audio_quick_editor/browser_report.py`
- Modify: `tests/test_browser_integration.py`
- Create: `tests/test_browser_runner.py`
- Create: `tests/test_browser_report.py`
- Modify: `tests/test_architecture/contracts.py`
- Modify: `pyproject.toml`

- [ ] Move `BatchRunReport` and result formatting to `browser_report.py`.
- [ ] Move `BatchOperationsDialog` to `browser_dialog.py`.
- [ ] Move background scheduling, note iteration, result application, and collection publishing to `browser_runner.py`.
- [ ] Keep hook registration and dialog opening in `browser_integration.py`.
- [ ] Split tests to match the new modules.
- [ ] Run `python3 scripts/dev.py test tests/test_browser_integration.py tests/test_browser_runner.py tests/test_browser_report.py`.

### Task 8: Split Frontend `actions.ts`

**Files:**

- Modify: `settings_ui/src/editor-inline/actions.ts`
- Create: `settings_ui/src/editor-inline/control-actions.ts`
- Create: `settings_ui/src/editor-inline/command-actions.ts`
- Create: `settings_ui/src/editor-inline/selection-actions.ts`
- Create: `settings_ui/src/editor-inline/graph-actions.ts`
- Create: `settings_ui/src/editor-inline/playback-actions.ts`
- Create: `settings_ui/src/editor-inline/audio-clock-actions.ts`
- Create: `settings_ui/src/editor-inline/editor-runtime-deps.ts`
- Modify: direct imports in `settings_ui/src/editor-inline/*.ts` and `.svelte` files where leaf imports improve clarity.
- Modify: `settings_ui/tests/editor-inline.actions.test.ts`
- Modify: `settings_ui/tests/editor-inline.edges.test.ts`

- [ ] Move status and busy-control logic to `control-actions.ts`.
- [ ] Move command dispatch to `command-actions.ts`.
- [ ] Move selection controller and gesture adapters to `selection-actions.ts`.
- [ ] Move graph request/render/reset/default queue logic to `graph-actions.ts`.
- [ ] Move playback engine/request/progress command logic to `playback-actions.ts`.
- [ ] Move compatibility audio-clock wrappers to `audio-clock-actions.ts` if direct users still need them.
- [ ] Keep `actions.ts` as a compatibility reexport facade under 250 lines.
- [ ] Update tests to import leaf modules for behavior-focused tests and facade imports only for window contract compatibility.
- [ ] Run `cd settings_ui && npm run validate`.

### Task 9: Split Frontend Integration Tests

**Files:**

- Modify/delete: `settings_ui/tests/editor-inline.integration.test.ts`
- Create: `settings_ui/tests/editor-inline.integration.graph.test.ts`
- Create: `settings_ui/tests/editor-inline.integration.playback.test.ts`
- Create: `settings_ui/tests/editor-inline.integration.selection.test.ts`
- Create: `settings_ui/tests/editor-inline.integration.commands.test.ts`
- Create: `settings_ui/tests/editor-inline.integration.helpers.ts`

- [ ] Move shared DOM setup, fake bridge, and visualizer helpers to `editor-inline.integration.helpers.ts`.
- [ ] Move graph scenarios to `editor-inline.integration.graph.test.ts`.
- [ ] Move playback scenarios to `editor-inline.integration.playback.test.ts`.
- [ ] Move selection/region scenarios to `editor-inline.integration.selection.test.ts`.
- [ ] Move command dispatch scenarios to `editor-inline.integration.commands.test.ts`.
- [ ] Run `cd settings_ui && npm run test -- --run editor-inline.integration`.
- [ ] Run `cd settings_ui && npm run lint:max-lines`.

### Task 10: Split `scripts/dev.py`

**Files:**

- Modify: `scripts/dev.py`
- Create: `scripts/dev_tasks/process.py`
- Create: `scripts/dev_tasks/python_env.py`
- Create: `scripts/dev_tasks/quality.py`
- Create: `scripts/dev_tasks/tests.py`
- Create: `scripts/dev_tasks/frontend.py`
- Create: `scripts/dev_tasks/contracts.py`
- Create: `scripts/dev_tasks/coverage.py`
- Create: `scripts/dev_tasks/release.py`
- Modify: tests that invoke or inspect `scripts/dev.py`

- [ ] Move `_run`, `_run_capture`, idle handling, and duration formatting to `process.py`.
- [ ] Move Anki Python discovery and setup helpers to `python_env.py`.
- [ ] Move lint, typecheck, architecture, complexity, deadcode, security, deps, and file-lines commands to `quality.py`.
- [ ] Move unit, Anki API, e2e, and pytest import probing to `tests.py`.
- [ ] Move frontend build/test commands to `frontend.py`.
- [ ] Move contract generation/check commands to `contracts.py`.
- [ ] Move coverage, Sonar, and mutmut helpers to `coverage.py`.
- [ ] Move release and info helpers to `release.py`.
- [ ] Keep `COMMANDS`, `cmd_help()`, and `main()` in `scripts/dev.py`.
- [ ] Run `python3 scripts/dev.py help`, `python3 scripts/dev.py info`, and `python3 scripts/dev.py check`.

### Task 11: Split Oversized Python and E2E Tests

**Files:**

- Modify/delete: `tests/test_settings_commands.py`
- Create: `tests/test_settings_commands_save.py`
- Create: `tests/test_settings_commands_diagnostics.py`
- Create: `tests/test_settings_commands_support_report.py`
- Create: `tests/test_settings_commands_logs.py`
- Modify/delete: `e2e/test_editor_processing_workflow.py`
- Modify/delete: `e2e/test_editor_region_loop_workflow.py`
- Modify/delete: `e2e/test_editor_graph_workflow.py`
- Modify/delete: `e2e/test_editor_deep_filter_workflow.py`
- Create shared e2e helper modules only when they reduce repeated setup and stay below 500 lines.

- [ ] Split settings command tests by command family.
- [ ] Split editor processing e2e scenarios by operation family.
- [ ] Split region loop e2e scenarios into selection, loop playback, and replacement files.
- [ ] Split graph e2e scenarios into initial render, redraw, and stale/failure files.
- [ ] Split DeepFilter e2e scenarios into success and failure files.
- [ ] Run `python3 scripts/dev.py test tests/test_settings_commands_save.py tests/test_settings_commands_diagnostics.py tests/test_settings_commands_support_report.py tests/test_settings_commands_logs.py`.
- [ ] Run `python3 scripts/dev.py test-e2e`.

### Task 12: Turn On Final Enforcement

**Files:**

- Modify: `scripts/dev.py`
- Modify: `settings_ui/package.json`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`
- Create: `tests/test_architecture/test_rule22_python_file_lengths.py`
- Modify: `TESTING.md`
- Modify: `DEVELOPMENT.md`
- Modify: `AGENTS.md` only if workflow guidance needs a new command reference.

- [ ] Add `file-lines` to `cmd_check()` after contracts and before lint.
- [ ] Add the pytest architecture rule for the Python hard cap.
- [ ] Add frontend `lint:max-lines` to `settings_ui` `validate`.
- [ ] Remove temporary frontend line-limit allowlist entries.
- [ ] Run `python3 scripts/dev.py file-lines`; expected result is pass with warnings only for 401-500 line files.
- [ ] Run `cd settings_ui && npm run lint:max-lines`; expected result is pass.
- [ ] Run `python3 scripts/dev.py check`.
- [ ] Run `python3 scripts/dev.py test-e2e`.

## Refactor Order

1. Enforcement skeleton in non-blocking mode.
2. Generated file ignore policy verification.
3. Audio production split, then audio tests.
4. Editor production split, then editor tests.
5. Browser production split and tests.
6. Frontend action split and frontend integration test split.
7. Dev runner split.
8. Remaining oversized unit/e2e test splits.
9. Enable final hard gates in `check` and `validate`.

This order keeps the riskiest public API, `audio_processor.py`, behind a facade before editor and browser code move. It also keeps tests close to the production responsibility they validate, which improves debugging when a split changes behavior.

## Verification Matrix

Run these after the matching task and again before completion:

| Scope | Command |
| --- | --- |
| Python line policy | `python3 scripts/dev.py file-lines` |
| Frontend line policy | `cd settings_ui && npm run lint:max-lines` |
| Architecture contracts | `python3 scripts/dev.py architecture-report` |
| Import-linter | `python3 scripts/dev.py arch` |
| Unit and architecture tests | `python3 scripts/dev.py test` |
| Frontend validation | `python3 scripts/dev.py test-svelte` |
| Full reusable gate | `python3 scripts/dev.py check` |
| Anki/webview e2e | `python3 scripts/dev.py test-e2e` |

## Risks and Controls

- Moving `audio_processor.py` can break five direct production importers. Keep a facade and migrate tests first by behavior slice.
- Moving editor functions can break stale async callback checks. Preserve session identity checks and keep completion handlers close to the flow they complete.
- Moving frontend actions can create circular imports. Leaf modules must import shared dependency builders from `editor-runtime-deps.ts`, never from `actions.ts`.
- Generated contracts should not be edited by hand or split for file size. The line tools must ignore them, and `contracts-check` must verify staleness.
- Hard file-line gates should be enabled only after every current >500 offender is split, otherwise `check` and frontend `validate` become unusable mid-refactor.

## Done Criteria

- No `.py`, `.ts`, `.svelte`, or `.js` hand-maintained source file is over 500 physical lines.
- Files from 401 to 500 lines emit warnings but do not fail. We consider them suspicious and usually decompose them as well.
- Test failures encountered during refactoring are classified in the failure log before fixes are made.
- `python3 scripts/dev.py check` includes Python file-line enforcement and passes.
- `settings_ui` `validate` includes ESLint hard max-lines enforcement and passes.
- Generated files are ignored by line-length tools and still verified by their existing staleness checks.
- Existing public imports from `audio_processor`, `editor_integration`, and `browser_integration` continue to work.
- Architecture contracts and import-linter reflect every new module.
- `python3 scripts/dev.py test-e2e` passes before the work is considered complete.
