# Python File Size Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove every current Python file-size warning from `python3 scripts/dev.py file-lines` through semantic decomposition, while keeping touched files below the repo's 350-line soft limit where practical.

**Architecture:** Keep existing public module facades for callers, then move cohesive responsibilities into focused modules with explicit architecture contracts. Production splits must preserve dependency direction: import-safe runtime and selection helpers stay Anki-free, while UI adapters own Anki, Qt, web eval, media writes, threads, note updates, and undo merging. Test splits should mirror behavior groups instead of arbitrary line chunks.

**Tech Stack:** Python 3.13, Anki add-on runtime, pytest, import-linter architecture contracts, Codegraph, JetBrains MCP rename/search, `scripts/dev.py`.

---

## Current Findings

Measured on 2026-05-27 with `python3 scripts/dev.py file-lines`.

There are no hard errors above 500 lines. There are 9 warnings above 400 lines:

| File | Lines | Primary responsibility problem |
| --- | ---: | --- |
| `addon/anki_audio_quick_editor/runtime_manager.py` | 489 | Platform detection, path lookup, status state, async install coordination, download/extract/promote, cleanup, and status payload formatting share one module. |
| `tests/test_release.py` | 482 | Release archive fixtures, selection tests, validation tests, runtime manifest variants, and archive naming tests share one suite. |
| `tests/test_browser_integration.py` | 466 | Browser hook/dialog tests, batch runner tests, fake collection objects, background completion tests, and result-application tests share one suite. |
| `addon/anki_audio_quick_editor/settings/commands.py` | 443 | Public bridge dispatch, settings persistence, reset/check-media UI actions, async job threading, health/support/log/runtime operations, frontend logs, and clipboard handling share one module. |
| `tests/test_editor_bridge_commands.py` | 440 | Processing payload tests, split-default tests, pending payload tests, busy-state tests, playback cancellation tests, share tests, and stop-playback tests share one suite. |
| `scripts/release_assets.py` | 436 | Public release-asset facade, lock helpers, verification/staging orchestration, fetch wrappers, path helpers, diagnostics, and CLI handlers share one script. |
| `tests/test_dev_runner.py` | 429 | CLI parsing, pytest runner behavior, frontend build commands, e2e commands, qodana, check orchestration, i18n, and parallel executor tests share one suite. |
| `scripts/release.py` | 407 | Release constants, version checks, manifest file selection, source staging, release metadata, archive writing, validation, runtime pack publishing, and CLI orchestration share one script. |
| `addon/anki_audio_quick_editor/browser_integration.py` | 401 | Browser hook registration, dialog opening, selected-note snapshotting, background scheduling, batch iteration, note mutation, progress reporting, and collection change publishing share one module. |

The soft-limit scan also shows several 351-400 line files. This plan does not expand scope to all of them, but every file touched by this work should end below 350 lines unless there is a concrete reason documented in the final change summary.

## Non-Negotiable Refactor Rules

- Do not change `WARN_LIMIT = 400` or `ERROR_LIMIT = 500`.
- Do not add permanent allowlists for hand-maintained files.
- Do not extract one small method just to drop a file below the warning threshold.
- Preserve public imports where practical by keeping facade modules.
- Update architecture contracts for every new add-on runtime module.
- Use Codegraph before moving production symbols to confirm callers and impact.
- Use JetBrains MCP rename refactoring for any symbol rename. Prefer moves without renames.
- Keep tests behavior-focused. If a test currently asserts a private helper only because the helper was in a monolith, either move the helper test with the helper or rewrite it around the new module contract.

## Target File Structure

### Runtime

| File | Responsibility |
| --- | --- |
| `addon/anki_audio_quick_editor/runtime_manager.py` | Compatibility facade and high-level public API exports only. |
| `addon/anki_audio_quick_editor/runtime_paths.py` | Runtime filesystem path derivation: manifest path, user files dir, runtime base dir, state path, managed runtime root. |
| `addon/anki_audio_quick_editor/runtime_platform.py` | Current target detection and managed executable-name mapping. |
| `addon/anki_audio_quick_editor/runtime_lookup.py` | Managed tool/model lookup, expected tool/model paths, readiness quick checks. |
| `addon/anki_audio_quick_editor/runtime_state.py` | Runtime state JSON read/write, status payload construction, last-status/thread-safe status storage. |
| `addon/anki_audio_quick_editor/runtime_install.py` | Sync/async install orchestration, download, extract, promote, cleanup, progress notification, friendly errors. |

### Settings

| File | Responsibility |
| --- | --- |
| `addon/anki_audio_quick_editor/settings/commands.py` | Public `handle_settings_command`, save/reset/check-media, frontend log, clipboard copy, and simple routing. |
| `addon/anki_audio_quick_editor/settings/async_commands.py` | Async command payload decoding, job id handling, thread lifecycle, progress/done JS callbacks, worker exception reporting. |
| `addon/anki_audio_quick_editor/settings/async_operations.py` | Health check, support report, show-log, runtime status, runtime install, config-payload normalization, add-on directory lookup. |

### Browser Batch

| File | Responsibility |
| --- | --- |
| `addon/anki_audio_quick_editor/browser_integration.py` | Hook registration, menu action wiring, selected-note validation, field-group building, dialog creation. |
| `addon/anki_audio_quick_editor/browser_batch_runner.py` | Background execution, run loop, note processing, result application, collection change publishing, progress/log reporting. |

### Release Tooling

| File | Responsibility |
| --- | --- |
| `scripts/release.py` | CLI orchestration, version checks, runtime-pack flow, and facade exports needed by existing tests/callers. |
| `scripts/release_manifest_selection.py` | `release_runtime_executables`, `release_runtime_shared_files`, `release_runtime_support_files`, `release_manifest_files`. |
| `scripts/release_archive.py` | Include/exclude decisions, source staging, release info writing, archive writing, archive validation. |
| `scripts/release_assets.py` | Public facade and CLI entrypoint for release assets. |
| `scripts/release_assets_core.py` | Lock loading, lock helper wrappers, verify/stage orchestration, checksum updates, fetch wrappers. |
| `scripts/release_assets_paths.py` | Release asset binary/source path helpers and current-target detection. |
| `scripts/release_assets_cli_handlers.py` | CLI subcommand adapters, diagnostic reporting, RNNoise build script dispatch. |

### Tests

| Current file | Split into |
| --- | --- |
| `tests/test_browser_integration.py` | `tests/test_browser_integration_hooks.py`, `tests/test_browser_batch_runner.py`, `tests/test_browser_result_application.py`, `tests/browser_batch_fixtures.py` |
| `tests/test_dev_runner.py` | `tests/test_dev_cli.py`, `tests/test_dev_pytest_runner.py`, `tests/test_dev_frontend_commands.py`, `tests/test_dev_check_runner.py`, `tests/test_dev_quality_commands.py` |
| `tests/test_editor_bridge_commands.py` | `tests/test_editor_bridge_processing_commands.py`, `tests/test_editor_bridge_split_defaults.py`, `tests/test_editor_bridge_non_processing_commands.py`, `tests/editor_bridge_command_fixtures.py` |
| `tests/test_release.py` | `tests/release_archive_fixtures.py`, `tests/test_release_archive_selection.py`, `tests/test_release_archive_validation.py`, `tests/test_release_runtime_manifest.py` |

## Implementation Tasks

### Task 1: Establish the Baseline and Impact Map

**Files:**
- Read: `scripts/dev_tasks/file_lines.py`
- Read: `tests/test_architecture/contract_ui.py`
- Read: `tests/test_architecture/contract_core.py`
- Read: `tests/test_architecture/test_rule23_refactor_module_contracts.py`

- [ ] Run `python3 scripts/dev.py file-lines`.
  Expected: 9 warnings listed in Current Findings and exit code 0.
- [ ] Run Codegraph context for each production area before moving code:
  `runtime_manager`, `settings.commands`, `browser_integration`, `release.py`, and `release_assets.py`.
- [ ] Use `mcp__idea__.search_symbol` for public symbols that tests or other modules import directly before deciding whether to keep a facade export.
- [ ] Record the baseline line counts for the 9 warning files and any new files created during the work.

### Task 2: Split `runtime_manager.py` by Runtime Responsibility

**Files:**
- Create: `addon/anki_audio_quick_editor/runtime_paths.py`
- Create: `addon/anki_audio_quick_editor/runtime_platform.py`
- Create: `addon/anki_audio_quick_editor/runtime_lookup.py`
- Create: `addon/anki_audio_quick_editor/runtime_state.py`
- Create: `addon/anki_audio_quick_editor/runtime_install.py`
- Modify: `addon/anki_audio_quick_editor/runtime_manager.py`
- Modify: `tests/test_runtime_manager.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `tests/test_architecture/test_rule23_refactor_module_contracts.py`
- Modify: `pyproject.toml`

- [ ] Move `current_platform_key` and `_TOOL_EXECUTABLES` into `runtime_platform.py`.
- [ ] Move path helpers into `runtime_paths.py`: `runtime_manifest_path`, `user_files_dir`, `runtime_base_dir`, `runtime_state_path`, `managed_runtime_root`.
- [ ] Move managed lookup helpers into `runtime_lookup.py`: `managed_tool_path`, `expected_managed_tool_path`, `managed_spleeter_model_path`, `expected_managed_spleeter_model_path`, `managed_silero_vad_model_path`, `expected_managed_silero_vad_model_path`, `managed_model_path`, `expected_managed_model_path`, `is_runtime_ready`, `_runtime_state_matches`, `_runtime_file_quick_check`.
- [ ] Move state/status helpers into `runtime_state.py`: `read_state`, `_write_ready_state`, `_status`, `_notify`, and shared last-status lock helpers needed by async installation.
- [ ] Move install orchestration into `runtime_install.py`: `runtime_status`, `ensure_runtime_async`, `ensure_runtime`, `_install_thread_main`, `_download_extract_promote`, `_download_pack`, `_cleanup_old_runtimes`, `_friendly_install_error`.
- [ ] Keep `runtime_manager.py` as a facade exporting the existing public names so existing production callers such as `audio_tools`, `diagnostics`, `settings.initial_state`, and `__init__` continue to import from `runtime_manager`.
- [ ] Update `tests/test_runtime_manager.py` to monkeypatch platform through `anki_audio_quick_editor.runtime_platform.platform`, not through the old monolithic module.
- [ ] Add explicit architecture contracts for the new runtime modules. `runtime_paths`, `runtime_platform`, `runtime_lookup`, and `runtime_state` should be `IMPORT_SAFE_CORE`; `runtime_install` should be `IMPORT_SAFE_CORE` with the same thread/temp cleanup side effects currently assigned to `runtime_manager`.
- [ ] Update the import-linter `import-safe-no-upper-layers` source/forbidden module lists in `pyproject.toml` through the existing contract-driven pattern.
- [ ] Run `python3 scripts/dev.py test tests/test_runtime_manager.py tests/test_architecture/test_rule23_refactor_module_contracts.py`.
  Expected: pass.

### Task 3: Split Settings Bridge Async Work from Public Dispatch

**Files:**
- Create: `addon/anki_audio_quick_editor/settings/async_commands.py`
- Create: `addon/anki_audio_quick_editor/settings/async_operations.py`
- Modify: `addon/anki_audio_quick_editor/settings/commands.py`
- Modify: `tests/test_settings_commands_save.py`
- Modify: `tests/test_settings_commands_diagnostics.py`
- Modify: `tests/test_settings_commands_support_report.py`
- Modify: `tests/test_settings_commands_logs.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule21_broad_exception_allowlist.py`
- Modify: `pyproject.toml`

- [ ] Move `_handle_async_cmd` and `_raw_job_id` into `settings/async_commands.py`.
- [ ] Move `_dispatch_op`, `_op_health_check`, `_op_support_report`, `_op_show_log_file`, `_op_runtime_status`, `_op_runtime_install`, `_config_payload`, `_runtime_status_for_settings`, and `_addon_dir_for_settings` into `settings/async_operations.py`.
- [ ] Keep `handle_settings_command` in `settings/commands.py` and route `"settings.async"` to `handle_async_settings_command`.
- [ ] Keep settings save/reset/check-media, frontend log handling, and support report clipboard copy in `settings/commands.py`.
- [ ] Preserve the public import path `anki_audio_quick_editor.settings.commands.handle_settings_command`.
- [ ] Update tests only where they assert moved private helpers or logger names. Tests that exercise the public bridge should continue through `handle_settings_command`.
- [ ] Add architecture contracts for `settings.async_commands` and `settings.async_operations` with `SETTINGS_BACKEND` layer and explicit side effects.
- [ ] Move the broad exception allowlist entry from `settings.commands._handle_async_cmd._run` to the new async worker symbol.
- [ ] Run `python3 scripts/dev.py test tests/test_settings_commands_save.py tests/test_settings_commands_diagnostics.py tests/test_settings_commands_support_report.py tests/test_settings_commands_logs.py tests/test_architecture/test_rule21_broad_exception_allowlist.py`.
  Expected: pass.

### Task 4: Split Browser Batch Execution from Hook/Dialog Wiring

**Files:**
- Create: `addon/anki_audio_quick_editor/browser_batch_runner.py`
- Modify: `addon/anki_audio_quick_editor/browser_integration.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py`
- Modify: `tests/test_architecture/test_rule19_shared_operation_contracts.py`
- Modify: `tests/test_architecture/test_rule23_refactor_module_contracts.py`
- Modify: `pyproject.toml`
- Create: `tests/browser_batch_fixtures.py`
- Create: `tests/test_browser_integration_hooks.py`
- Create: `tests/test_browser_batch_runner.py`
- Create: `tests/test_browser_result_application.py`
- Delete: `tests/test_browser_integration.py`

- [ ] Move `_run_batch_in_background`, `_run_batch`, `_process_note`, `_apply_result`, and `_publish_collection_changes` into `browser_batch_runner.py`.
- [ ] Keep `register_browser_hooks`, `_browser_hook_boundary`, `_on_browser_menus_did_init`, `_open_batch_dialog`, `_snapshots_for_note_ids`, `_snapshot_from_note`, and `_create_dialog` in `browser_integration.py`.
- [ ] Import runner functions from `browser_batch_runner.py` where the dialog start callback needs them.
- [ ] Add a `browser_batch_runner` architecture contract as `UI_ADAPTER` with media write, note update, undo merge, background dispatch, and Anki import side effects.
- [ ] Update batch architecture tests so persistence and shared-operation boundaries check `browser_batch_runner.py` for note mutation and media writes instead of expecting all batch side effects in `browser_integration.py`.
- [ ] Split tests by behavior: hook/menu/dialog setup, batch runner progress/cancel/failure behavior, and result application/conflict behavior.
- [ ] Keep shared fake note/collection objects in `tests/browser_batch_fixtures.py`; do not put them in global `tests/conftest.py`.
- [ ] Run `python3 scripts/dev.py test tests/test_browser_integration_hooks.py tests/test_browser_batch_runner.py tests/test_browser_result_application.py tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py tests/test_architecture/test_rule19_shared_operation_contracts.py`.
  Expected: pass.

### Task 5: Split Release Packaging from Release CLI Orchestration

**Files:**
- Create: `scripts/release_manifest_selection.py`
- Create: `scripts/release_archive.py`
- Modify: `scripts/release.py`
- Create: `tests/release_archive_fixtures.py`
- Create: `tests/test_release_archive_selection.py`
- Create: `tests/test_release_archive_validation.py`
- Create: `tests/test_release_runtime_manifest.py`
- Delete: `tests/test_release.py`

- [ ] Move `release_runtime_executables`, `release_runtime_shared_files`, `release_runtime_support_files`, and `release_manifest_files` into `scripts/release_manifest_selection.py`.
- [ ] Move `_should_include`, `_stage_source_tree`, `_latest_commit_info`, `_write_release_info`, `_stage_release_tree`, `_build_archive`, and `_validate_archive` into `scripts/release_archive.py`.
- [ ] Keep `scripts/release.py` as the CLI orchestrator and re-export moved names that existing tests or scripts access through `scripts.release`.
- [ ] Move release archive helper functions from the current test file into `tests/release_archive_fixtures.py`.
- [ ] Split tests into archive selection, archive validation, and runtime manifest suites.
- [ ] Run `python3 scripts/dev.py test tests/test_release_archive_selection.py tests/test_release_archive_validation.py tests/test_release_runtime_manifest.py`.
  Expected: pass.

### Task 6: Split Release Asset Facade, Core, Paths, and CLI Handlers

**Files:**
- Create: `scripts/release_assets_core.py`
- Create: `scripts/release_assets_paths.py`
- Create: `scripts/release_assets_cli_handlers.py`
- Modify: `scripts/release_assets.py`
- Modify: `tests/test_release_assets.py`
- Modify: `tests/test_release_assets_dpdfnet.py`
- Modify: `tests/test_release_asset_fetch.py`
- Modify: `tests/release_assets_helpers.py`

- [ ] Move `load_lock`, `lock_targets`, `lock_tools`, `lock_shared_files`, `verify_assets`, `stage_assets`, `lock_checksums`, `fetch_deepfilter`, `fetch_ffmpeg`, `fetch_sherpa_spleeter`, `fetch_spleeter_models`, `fetch_silero_vad`, and `fetch_silero_vad_model` into `scripts/release_assets_core.py`.
- [ ] Move `current_target_key`, `asset_binary_path`, `source_tool_binary_path`, and `_ffmpeg_archive_path` into `scripts/release_assets_paths.py`.
- [ ] Move `_target_selection`, `_append_diagnostic_report`, `_run_build_script`, `_cmd_verify`, `_cmd_stage`, fetch command adapters, `_cmd_lock_checksums`, `_cmd_build_rnnoise`, `_build_script_name`, and parser wiring into `scripts/release_assets_cli_handlers.py`.
- [ ] Keep `scripts/release_assets.py` as a public facade that re-exports the existing public names used by `scripts/release.py`, `scripts/release_runtime.py`, `scripts/release_validation.py`, `scripts/release_acceptance.py`, and release asset tests.
- [ ] Keep `release_assets.main(argv)` available for `tests/test_release_assets_dpdfnet.py`.
- [ ] Run `python3 scripts/dev.py test tests/test_release_assets.py tests/test_release_assets_dpdfnet.py tests/test_release_asset_fetch.py`.
  Expected: pass.

### Task 7: Split Dev Runner Tests by Command Family

**Files:**
- Create: `tests/test_dev_cli.py`
- Create: `tests/test_dev_pytest_runner.py`
- Create: `tests/test_dev_frontend_commands.py`
- Create: `tests/test_dev_check_runner.py`
- Create: `tests/test_dev_quality_commands.py`
- Delete: `tests/test_dev_runner.py`

- [ ] Move `_parse_cli_args` tests into `tests/test_dev_cli.py`.
- [ ] Move pytest argument and `_run_pytest` behavior tests into `tests/test_dev_pytest_runner.py`.
- [ ] Move build UI, Svelte, e2e, and frontend sequencing tests into `tests/test_dev_frontend_commands.py`.
- [ ] Move `check` orchestration and parallel executor tests into `tests/test_dev_check_runner.py`.
- [ ] Move qodana and i18n command tests into `tests/test_dev_quality_commands.py`.
- [ ] Run `python3 scripts/dev.py test tests/test_dev_cli.py tests/test_dev_pytest_runner.py tests/test_dev_frontend_commands.py tests/test_dev_check_runner.py tests/test_dev_quality_commands.py`.
  Expected: pass.

### Task 8: Split Editor Bridge Command Tests by Command Family

**Files:**
- Create: `tests/editor_bridge_command_fixtures.py`
- Create: `tests/test_editor_bridge_processing_commands.py`
- Create: `tests/test_editor_bridge_split_defaults.py`
- Create: `tests/test_editor_bridge_non_processing_commands.py`
- Delete: `tests/test_editor_bridge_commands.py`

- [ ] Move repeated fake editor/session setup into `tests/editor_bridge_command_fixtures.py`.
- [ ] Move processing JSON, pause overrides, plain processing, pending payload, busy-session, playback-preparation cancel, and graph-analysis cancel tests into `tests/test_editor_bridge_processing_commands.py`.
- [ ] Move split default update and pending split-default persistence tests into `tests/test_editor_bridge_split_defaults.py`.
- [ ] Move callback facade, share command, and stop-playback tests into `tests/test_editor_bridge_non_processing_commands.py`.
- [ ] Run `python3 scripts/dev.py test tests/test_editor_bridge_processing_commands.py tests/test_editor_bridge_split_defaults.py tests/test_editor_bridge_non_processing_commands.py`.
  Expected: pass.

### Task 9: Final File-Size and Architecture Verification

**Files:**
- Modify only if earlier tasks expose contract drift: `pyproject.toml`, `tests/test_architecture/*`

- [ ] Run `python3 scripts/dev.py file-lines`.
  Expected: `PASS: no hand-maintained Python files exceed 400 lines.`
- [ ] Run a soft-limit audit for touched files and confirm each production/test file touched by this plan is below 350 lines, or document the exact exception.
- [ ] Run `python3 scripts/dev.py architecture-report`.
  Expected: no contract violations.
- [ ] Run `python3 scripts/dev.py lint`.
  Expected: pass after safe autofix.
- [ ] Run `python3 scripts/dev.py typecheck`.
  Expected: pass.
- [ ] Run `python3 scripts/dev.py test`.
  Expected: pass.
- [ ] Run `python3 scripts/dev.py check`.
  Expected: pass.
- [ ] Run `python3 scripts/dev.py test-e2e`.
  Expected: pass before considering the feature complete.

## Execution Notes

- Execute production splits before test-only splits where tests directly import moved private helpers.
- Keep module moves as plain moves with the same function names unless a name becomes misleading after extraction.
- When renaming a symbol, use JetBrains MCP `rename_refactoring` rather than search-and-replace.
- After each file move, wait for Codegraph's file watcher before asking Codegraph for updated impact.
- If a test fails after a move, classify it before editing: behavior regression, facade export missing, architecture contract missing, stale monkeypatch target, or brittle private-helper assertion.
- Do not merge all fixtures into `tests/conftest.py`; localized helper modules keep test dependencies visible.
