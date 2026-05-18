# Max File Lines Refactor Test Failure Log

## Entry Template

- Failing command and test id:
- Observed failure message:
- Why the test failed:
- Classification:
- Decision:
- Follow-up owner/task:

## 2026-05-18 - File-line scanner red test

- Failing command and test id: `python3 scripts/dev.py test tests/test_dev_tasks_file_lines.py` during collection of `tests/test_dev_tasks_file_lines.py`
- Observed failure message: `ModuleNotFoundError: No module named 'scripts.dev_tasks'`
- Why the test failed: The test was written first for the new `scripts.dev_tasks.file_lines` module before the implementation existed.
- Classification: behavior regression
- Decision: fix production code by adding the development task package and file-line scanner.
- Follow-up owner/task: Task 1, add the scanner and `file-lines` dev command.

## 2026-05-18 - Direct dev runner import path

- Failing command and test id: `python3 scripts/dev.py file-lines`
- Observed failure message: `ModuleNotFoundError: No module named 'scripts'`
- Why the test failed: Running `scripts/dev.py` directly puts `scripts/` on `sys.path`, not the repository root, so `from scripts.dev_tasks...` only worked under pytest imports.
- Classification: environment/tooling issue
- Decision: fix production code by ensuring the repository root is importable before importing the dev task package.
- Follow-up owner/task: Task 1, verify `python3 scripts/dev.py file-lines` works as the CLI entrypoint.

## 2026-05-18 - Audio split compatibility errors

- Failing command and test id: `pytest tests/test_audio_processor.py tests/test_architecture/test_rule15_all_modules_have_contracts.py tests/test_architecture/test_rule17_contract_driven_addon_dependency_policy.py tests/test_architecture/test_rule18_contract_driven_side_effect_policy.py tests/test_architecture/test_rule21_broad_exception_allowlist.py -vv`
- Observed failure message: 14 failures, including `TypeError: AudioProcessingResult() takes no arguments`, `NameError: name 'select_deep_filter_output' is not defined`, and a facade monkeypatch assertion for `temp_playback_path`.
- Why the test failed: The mechanical split dropped the `@dataclass` decorator from `AudioProcessingResult`, did not import the DeepFilter output selector into the pause-pipeline module, and left one old-module monkeypatch route unsynchronized.
- Classification: public contract break
- Decision: preserve compatibility facade and fix production split wiring.
- Follow-up owner/task: Task 3, rerun focused audio and architecture tests.

## 2026-05-18 - Browser split report contract errors

- Failing command and test id: `pytest tests/test_browser_integration.py tests/test_architecture/test_rule15_all_modules_have_contracts.py tests/test_architecture/test_rule17_contract_driven_addon_dependency_policy.py tests/test_architecture/test_rule18_contract_driven_side_effect_policy.py -vv`
- Observed failure message: `TypeError: BatchRunReport() takes no arguments` and architecture contract drift for `browser_dialog` and `browser_report`.
- Why the test failed: The mechanical move dropped the `@dataclass` decorator from `BatchRunReport`, and newly created production modules were not yet declared in executable architecture contracts.
- Classification: public contract break
- Decision: preserve the public report constructor and add contracts for the new browser modules.
- Follow-up owner/task: Task 7, rerun focused browser and architecture tests.

## 2026-05-18 - Broad check after initial splits

- Failing command and test id: `python3 scripts/dev.py check`
- Observed failure message: `lint`, `typecheck`, and `test` failed. Python unit tests reported three architecture-test failures; typecheck reported untyped compatibility facade wrappers in `audio_processor.py`; lint reported import ordering and unused facade re-exports.
- Why the test failed: The split left `audio_processor.py` as a monkeypatch-compatible forwarding facade without explicit wrapper signatures or an export list, and three architecture tests still inspected the old `browser_integration.py` ownership for dialog registry code that now lives in `browser_dialog.py`.
- Classification: refactor fallout / brittle internal-detail dependency
- Decision: keep the compatibility facade, add explicit exported names and typed forwarding signatures, and update architecture tests to assert the new browser module responsibilities.
- Follow-up owner/task: Rerun lint, typecheck, failed architecture tests, then the full `python3 scripts/dev.py check` gate before continuing refactors.

## 2026-05-18 - Audio facade type-hint contract drift

- Failing command and test id: `python3 scripts/dev.py test tests/test_architecture/test_rule13_batch_operation_boundaries.py::test_browser_integration_avoids_editor_actions_module tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py::test_browser_operation_selector_is_driven_by_shared_registry tests/test_architecture/test_rule19_shared_operation_contracts.py::test_browser_batch_adapter_uses_shared_registry_and_executor`
- Observed failure message: `audio_processor: unexpected addon deps ['audio_state']` from the contract-driven addon dependency policy and architecture report tests.
- Why the test failed: Typed compatibility wrappers now import `AudioEditState` and `AudioProcessingConfig` from `audio_state`, but the executable architecture contract for the facade had not been updated.
- Classification: architecture contract drift
- Decision: allow `audio_processor` to depend on `audio_state`, matching its typed facade API.
- Follow-up owner/task: Rerun Python tests and full QC check.

## 2026-05-18 - editor_session architecture manifest drift

- Failing command and test id: `python3 scripts/dev.py test tests/test_editor_integration.py`; `tests/test_architecture/test_rule5_all_modules_classified.py::TestAllModulesClassified::test_completeness`, `tests/test_architecture/test_rule15_all_modules_have_contracts.py::test_all_production_modules_have_contracts`
- Observed failure message: `Unclassified modules found ... ['editor_session']` / `Module contract manifest drift detected. Missing: ['editor_session']`
- Why the test failed: extracting `editor_session.py` introduced a production module without adding the matching architecture contract.
- Classification: public contract break.
- Decision: fix architecture contract metadata by classifying `editor_session` as import-safe core and adding it as an allowed dependency of `editor_integration`.
- Follow-up owner/task: current refactor; repeat this update for each new editor module as it is introduced.

## 2026-05-18 - editor_session import-linter manifest drift

- Failing command and test id: `python3 scripts/dev.py test tests/test_editor_integration.py`; `tests/test_architecture/test_rule2_runtime_import_safety.py::test_import_linter_import_safe_contract_tracks_module_contracts`
- Observed failure message: import-safe source modules in `pyproject.toml` were missing `anki_audio_quick_editor.editor_session`.
- Why the test failed: the architecture contract was updated, but the corresponding import-linter contract source list had not been updated.
- Classification: public contract break.
- Decision: fix tooling metadata by adding `editor_session` to the import-safe source modules list.
- Follow-up owner/task: current refactor; keep architecture contracts and import-linter manifests synchronized for every import-safe extracted module.

## 2026-05-18 - playback broad-exception allowlist relocation

- Failing command and test id: `python3 scripts/dev.py test`; `tests/test_architecture/test_rule21_broad_exception_allowlist.py::test_broad_exception_handlers_are_allowlisted_with_reasons`
- Observed failure message: `editor_playback.start_playback_from_cursor._run`, `editor_playback.stop_audio_playback`, and `editor_playback.toggle_native_pause_resume` were unallowlisted, while their old `editor_integration` entries no longer had handlers.
- Why the test failed: playback broad exception boundaries moved into `editor_playback.py`, but the allowlist still referenced the old module.
- Classification: public contract break.
- Decision: fix architecture metadata by moving the three allowlist entries to `editor_playback` with the same reasons.
- Follow-up owner/task: current refactor; update allowlists whenever background or Anki boundary handlers move.

## 2026-05-18 - region-delete persistence allowlist relocation

- Failing command and test id: `python3 scripts/dev.py test`; `tests/test_architecture/test_rule14_batch_adapter_and_persistence_boundaries.py::test_direct_media_and_note_persistence_are_isolated_to_ui_adapters`
- Observed failure message: `editor_region_delete.py:188: saved_name = editor.mw.col.media.write_data(...)`
- Why the test failed: direct media persistence moved from `editor_integration.py` into the new UI adapter `editor_region_delete.py`, but the persistence boundary allowlist still named only the previous adapter files.
- Classification: public contract break.
- Decision: add `editor_region_delete.py` to the explicit UI-adapter persistence allowlist.
- Follow-up owner/task: current refactor; include every extracted media-writing UI adapter in the boundary test allowlist.

## 2026-05-18 - editor_processing import-linter manifest drift

- Failing command and test id: `python3 scripts/dev.py test`; `tests/test_architecture/test_rule2_runtime_import_safety.py::test_import_linter_import_safe_contract_tracks_module_contracts`
- Observed failure message: import-safe source modules in `pyproject.toml` unexpectedly included `anki_audio_quick_editor.editor_processing`.
- Why the test failed: `editor_processing.py` is a UI adapter with media writes and thread/web side effects, but I added it to the import-safe source module list while updating module metadata.
- Classification: public contract break.
- Decision: remove `editor_processing` from the import-safe import-linter source list and keep it only in executable architecture contracts as a UI adapter.
- Follow-up owner/task: current refactor; only add extracted modules to the import-safe linter list when their module contract is `IMPORT_SAFE_CORE`.

## 2026-05-18 - editor_frontend background dispatch contract drift

- Failing command and test id: `python3 scripts/dev.py test`; `tests/test_architecture/test_rule20_contract_report_is_clean.py::test_architecture_report_is_clean`, `tests/test_architecture/test_rule18_contract_driven_side_effect_policy.py::test_contract_driven_side_effect_policy`
- Observed failure message: `editor_frontend: unexpected side effects ['background_task_dispatch']`
- Why the test failed: moving graph redraw scheduling into `editor_frontend.py` moved the `QTimer.singleShot` background scheduling boundary, but the new module contract only allowed Anki imports and web eval.
- Classification: public contract break / architecture contract drift
- Decision: update the `editor_frontend` contract to include `BACKGROUND_TASK_DISPATCH`.
- Follow-up owner/task: current refactor; account for Qt timer scheduling whenever moving graph redraw helpers.

## 2026-05-18 - file-line architecture guard fixture setup

- Failing command and test id: `python3 scripts/dev.py test tests/test_architecture/test_rule22_python_file_lengths.py`; `tests/test_architecture/test_rule22_python_file_lengths.py::test_hand_maintained_python_files_stay_under_hard_limit`
- Observed failure message: `fixture 'repo_root' not found`
- Why the test failed: the new architecture guard assumed a shared `repo_root` fixture that does not exist in this test suite.
- Classification: bad fixture/setup coupling
- Decision: make the guard self-contained by deriving the repository root from the test file path.
- Follow-up owner/task: current refactor; prefer local path derivation for architecture tests unless a fixture already exists.
