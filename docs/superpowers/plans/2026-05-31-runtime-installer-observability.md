# Runtime Installer Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the detailed runtime installer window and step-level runtime install telemetry described in `docs/superpowers/specs/2026-05-31-runtime-installer-observability-design.md`.

**Architecture:** Keep runtime install orchestration import-safe and UI-agnostic. Add a pure progress model, a single active install session coordinator, a subprocess-only probe module, and a WebView/Svelte installer dialog as the only UI owner. Settings and startup open or attach to that dialog; runtime-dependent actions use a small guardrail helper to fail early with coded repair guidance.

**Tech Stack:** Python 3.13, Anki Qt/WebView, generated JSON contracts, Svelte 5, TypeScript, Vitest, pytest, import-linter architecture contracts, e2e Anki runtime tests.

---

## File Structure

Backend core:

- Create `addon/anki_audio_quick_editor/runtime_install_progress.py`: pure step IDs, labels, statuses, snapshots, details, and failure/warning state transitions. No Anki, Qt, subprocess, network, zip, or filesystem mutation.
- Create `addon/anki_audio_quick_editor/runtime_install_session.py`: owns the single active runtime install/verification operation, observer subscription, thread lifecycle, latest snapshot, and attach-or-start behavior. No Anki or Qt imports.
- Create `addon/anki_audio_quick_editor/runtime_preflight.py`: writable-directory and disk-space checks. No Anki or UI imports.
- Create `addon/anki_audio_quick_editor/runtime_probes.py`: dry-run command definitions and subprocess timeout/result capture. This is the only new runtime core module allowed to run subprocesses.
- Create `addon/anki_audio_quick_editor/runtime_required.py`: runtime-not-ready guardrail helper that returns a structured `AQE-RUNTIME-003` user-facing error. No UI imports.
- Modify `addon/anki_audio_quick_editor/runtime_install.py`: emit detailed step snapshots while preserving existing install safety behavior.
- Modify `addon/anki_audio_quick_editor/runtime_archive.py`: expose archive/member/extracted-file verification details without importing UI/session modules.
- Modify `addon/anki_audio_quick_editor/runtime_manager.py`: re-export new session/progress APIs needed by startup and settings.
- Modify `addon/anki_audio_quick_editor/runtime_state.py`: keep the concise `RuntimeStatus` shape, and do not embed the full step list there.
- Modify `addon/anki_audio_quick_editor/error_codes.py`: add `AQE-RUNTIME-004` through `AQE-RUNTIME-007`.
- Modify `addon/anki_audio_quick_editor/diagnostics_runtime.py` and `addon/anki_audio_quick_editor/support_reporting.py` so the latest runtime install operation appears in support context.

Backend UI and settings:

- Create `addon/anki_audio_quick_editor/runtime_installer_dialog.py`: AnkiWebView-backed dialog, subscribes to `runtime_install_session`, sends snapshots to frontend, warns on incomplete close.
- Create `addon/anki_audio_quick_editor/runtime_installer_bridge.py`: decodes installer WebView bridge commands and keeps dialog command handling out of the pure runtime modules.
- Modify `addon/anki_audio_quick_editor/settings/__init__.py`: expose an `open_runtime_installer()` method on `SettingsDialog`; settings backend must not import the dialog module directly.
- Modify `addon/anki_audio_quick_editor/settings/commands.py`: add a settings bridge command that asks the settings shell/dialog to open the runtime installer.
- Modify `addon/anki_audio_quick_editor/settings/async_operations.py`: stop using the old small progress flow from the visible Install/Repair Runtime button; keep `runtime_status` summary.
- Modify `addon/anki_audio_quick_editor/__init__.py`: startup opens the detailed installer when runtime is missing/invalid and attaches to an active session when one exists.

Contracts and frontend:

- Modify `contracts/communication.schema.json`: add runtime install snapshot, step, detail, probe result, warning, and command payload definitions.
- Regenerate `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts` with `python3 scripts/dev.py contracts-generate`.
- Modify `settings_ui/src/lib/types.ts`: export generated runtime installer types and the installer bridge payload/result aliases.
- Create `settings_ui/src/runtime-installer/main.ts`.
- Create `settings_ui/src/runtime-installer/RuntimeInstallerApp.svelte`.
- Create `settings_ui/src/runtime-installer/runtime-installer-state.ts`: step ordering, snapshot narrowing, display helpers, and close-warning state.
- Create `settings_ui/src/runtime-installer/bridge.ts`: installer-specific bridge commands and callback registration.
- Create `settings_ui/src/runtime-installer/styles.css`.
- Create `settings_ui/vite.runtime-installer.config.ts` and update `settings_ui/package.json` build scripts so `npm run build` emits `templates/runtime-installer/runtime_installer_bundle.{js,css}`.
- Modify `settings_ui/src/settings/DiagnosticsPanel.svelte` and `SettingsApp.svelte`: Install/Repair Runtime opens the detailed installer instead of running the small async install progress flow.

Tests:

- Create or modify backend tests:
  - `tests/test_runtime_install_progress.py`
  - `tests/test_runtime_install_session.py`
  - `tests/test_runtime_preflight.py`
  - `tests/test_runtime_probes.py`
  - `tests/test_runtime_required.py`
  - `tests/test_runtime_manager.py`
  - `tests/test_settings_commands_diagnostics.py`
  - `tests/test_settings_shell.py`
  - `tests/test_support_reporting.py`
- Create or modify architecture tests:
  - `tests/test_architecture/contract_core.py`
  - `tests/test_architecture/contract_ui.py`
  - `tests/test_architecture/test_rule23_refactor_module_contracts.py`
  - Create `tests/test_architecture/test_rule25_runtime_installer_boundaries.py`
  - Update `pyproject.toml` import-linter source/forbidden module lists.
- Create or modify frontend tests:
  - `settings_ui/tests/runtime-installer-state.test.ts`
  - `settings_ui/tests/runtime-installer-app.test.ts`
  - `settings_ui/tests/bridge.test.ts`
  - `settings_ui/tests/app.test.ts`
  - `settings_ui/tests/frontend-architecture.test.ts`
- Create or modify e2e tests for missing runtime startup, dismiss warning, forced failure, retry, guardrail, and successful install.

Docs:

- Modify `ARCHITECTURE.md`.
- Modify `TESTING.md`.
- Modify `WEBVIEW_AND_TEMPLATES.md` because a new WebView bundle is introduced.
- Modify `docs/errors/AQE-RUNTIME-003/index.html`.
- Add pages for `AQE-RUNTIME-004` through `AQE-RUNTIME-007`.

---

## Implementation Strategy

The implementation moves from contracts and pure state outward to side effects and UI. Do not start with the dialog. The first working slice is a runtime install snapshot that can represent every planned step without doing install work. The second slice is a session coordinator that publishes those snapshots to observers. Only after those two pieces are stable should `runtime_install.py` emit real installer events.

Runtime install operation lifecycle:

1. Caller asks `runtime_install_session` to start or attach to a runtime install operation.
2. Session creates or returns one active operation ID.
3. Session publishes the latest snapshot immediately to new observers.
4. Worker runs install or verification orchestration and publishes snapshots after every step transition.
5. Final snapshot remains available after success or failure so reopening the dialog shows useful state.
6. A new explicit repair attempt replaces the latest failed operation with a new operation ID.

Verification-only lifecycle:

1. Settings opens the installer while runtime is already ready.
2. Session starts a verification-only operation.
3. The operation emits select-package, local-state, extracted-file verification, permission check, dry-run, and ready steps.
4. It does not redownload, re-extract, force reinstall, delete runtime files, or rewrite state unless existing state is invalid.

Install lifecycle:

1. Select platform, manifest, runtime pack, and expected file list.
2. Check existing state and reusable cached archive.
3. Run preflight for writable paths and disk space.
4. Download or reuse a validated archive.
5. Verify archive size and checksum.
6. Validate zip contents before extraction.
7. Extract manifest-listed files to a temporary directory.
8. Verify extracted file size and checksum.
9. Apply and verify executable permissions.
10. Promote the verified temp runtime and write runtime state.
11. Run dry-run probes.
12. Cleanup temp files and old runtime directories.
13. Confirm managed runtime lookup resolves expected tools.

Snapshot ownership:

- `runtime_install_progress.py` owns the in-memory snapshot shape and transition helpers.
- Generated contracts own the JSON wire shape.
- `runtime_install.py` owns the moment when a step changes state.
- `runtime_install_session.py` owns fanout to observers and latest-snapshot retention.
- The dialog and Svelte app render snapshots; they do not infer install state from filesystem paths.

Failure taxonomy:

- Use `AQE-RUNTIME-003` when a user action needs runtime but runtime is not ready.
- Use `AQE-RUNTIME-004` for download and network/write failures during download.
- Use `AQE-RUNTIME-005` for archive size, archive checksum, corrupt zip, unsafe path, missing member, and unexpected member failures.
- Use `AQE-RUNTIME-006` for extraction failures, extracted file size/hash failures, promotion failures, and runtime state write failures.
- Use `AQE-RUNTIME-007` for executable permission and dry-run probe failures.
- Cleanup failures become warnings when the runtime is otherwise usable; they become errors only when they prevent readiness or leave state ambiguous.

Dialog/frontend flow:

1. Startup or Settings opens `runtime_installer_dialog.py`.
2. Dialog renders the runtime-installer WebView with the latest snapshot as initial state.
3. Dialog subscribes to `runtime_install_session` and pushes snapshots to `window.onRuntimeInstallProgress(...)`.
4. Frontend renders the fixed checklist in contract order and expands details from snapshot data.
5. Close command closes the dialog. If latest snapshot is not ready, Python shows the incomplete-install warning.
6. The Settings diagnostics panel keeps the concise runtime summary but delegates repair/install visibility to the detailed dialog.

Runtime guardrail flow:

1. Runtime-dependent entry points call `runtime_required.require_runtime_ready(...)` immediately before external-tool or managed-runtime-file work.
2. If runtime is not ready, the action returns the same structured coded repair guidance through its existing user-facing error channel.
3. The guardrail does not open UI, hide controls, disable the add-on, or start installation.

Implementation order rationale:

- Contracts and pure progress state land first so every later task has a typed, testable target.
- Session coordination lands before real install instrumentation to avoid adding a second ad hoc progress mechanism.
- Runtime orchestration and pessimistic install tests land before UI so the dialog renders real semantics rather than placeholder steps.
- Architecture tests land before final e2e so boundary mistakes are caught while the implementation is still small enough to correct.

---

## Architecture Rules To Enforce

Runtime core boundaries:

- `runtime_install_progress.py` can define data structures and pure transformations only. It cannot import `aqt`, `anki`, `subprocess`, `urllib`, `zipfile`, `shutil`, `runtime_installer_dialog`, `settings`, or any frontend/webview module.
- `runtime_install_session.py` can spawn/manage one worker thread and call runtime core orchestration. It cannot import `aqt`, `anki`, Qt, WebView shell, settings UI, or installer dialog code.
- `runtime_preflight.py` can inspect filesystem state and disk usage. It cannot import UI modules, start downloads, run subprocesses, or mutate runtime state beyond explicit preflight-created directories.
- `runtime_probes.py` can run subprocesses and return bounded probe results. It cannot download, extract, promote, write runtime state, import Anki, or display UI.
- `runtime_install.py` can orchestrate download/extract/verify/promote and emit progress snapshots. It cannot import installer dialog, settings modules, Svelte bundle paths, or WebView shell.
- `runtime_archive.py` remains archive-specific. It cannot know about operation IDs, dialogs, settings commands, or support-report UI.
- `runtime_required.py` can inspect runtime readiness and build coded user-facing errors. It cannot show UI or run installation.

UI boundaries:

- `runtime_installer_dialog.py` is the only Python module that owns the Runtime Installation WebView dialog.
- `runtime_installer_bridge.py` can decode installer WebView commands, but cannot perform archive extraction or subprocess probes.
- Settings backend modules under `addon/anki_audio_quick_editor/settings/` must not import `runtime_installer_dialog.py`; they should call a dialog/shell callback or method.
- Startup in `__init__.py` dynamically imports the installer dialog after Anki main window initialization; import-safe modules must not import it.

Frontend boundaries:

- Add `settings_ui/src/runtime-installer/` as a fourth feature frontend area.
- Runtime installer frontend modules can import `src/lib/*` and `src/runtime-installer/*`.
- Runtime installer frontend modules cannot import `src/settings/*`, `src/editor-inline/*`, or `src/batch/*`.
- Settings frontend can send the command to open the installer, but cannot import runtime-installer components directly.
- Shared `src/lib/*` modules cannot import runtime-installer, settings, editor, or batch feature modules.

---

## Spec Traceability Matrix

| Design Requirement | Planned Tasks |
| --- | --- |
| Dedicated detailed window for startup and repair | Tasks 8, 9, 10, 12 |
| Same window every time, ready verification if already ready | Tasks 4, 8, 10, 12 |
| Dismissible window with incomplete-install warning | Tasks 8, 10, 12 |
| Runtime actions fail early with coded repair guidance | Task 7 |
| Fixed checklist with 13 steps | Tasks 2, 4, 10 |
| Structured snapshots with operation ID, step IDs, details | Tasks 1, 2, 4 |
| Archive size/hash, contents, extraction, file verification | Tasks 4, 5 |
| Permission checks and dry-run probes | Tasks 5, 6 |
| Cleanup warning/error behavior | Tasks 4, 5 |
| Single active operation, attach-or-start | Task 3 |
| Support reports include latest failed operation | Task 6 |
| New runtime error codes | Task 1 |
| Architecture/import boundaries | Task 11 |
| WebView bundle docs and runtime error docs | Task 13 |
| Full check and e2e verification | Task 14 |

---

### Task 1: Contracts And Error Codes

**Files:**
- Modify: `contracts/communication.schema.json`
- Modify: `addon/anki_audio_quick_editor/error_codes.py`
- Regenerate: `addon/anki_audio_quick_editor/contracts_generated.py`
- Regenerate: `settings_ui/src/lib/generated/contracts.ts`
- Modify: `settings_ui/src/lib/types.ts`
- Test: `tests/test_error_codes.py`
- Test: `settings_ui/tests/runtime-installer-state.test.ts`

- [ ] **Step 1: Write failing contract and error-code tests**

  Add tests that assert:
  - `AQE_RUNTIME_DOWNLOAD_FAILED == "AQE-RUNTIME-004"`.
  - `AQE_RUNTIME_ARCHIVE_VERIFICATION_FAILED == "AQE-RUNTIME-005"`.
  - `AQE_RUNTIME_EXTRACTION_FAILED == "AQE-RUNTIME-006"`.
  - `AQE_RUNTIME_EXECUTABLE_CHECK_FAILED == "AQE-RUNTIME-007"`.
  - A runtime install snapshot payload with `operation_id`, `current_step_id`, `steps`, `error_code`, `failed_step_id`, and download byte fields validates through generated Python and TypeScript narrowing.
  - Generated contracts reject snapshots missing required step IDs or containing unknown step status values.

- [ ] **Step 2: Run failing checks**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_error_codes.py
  cd settings_ui && npm run test -- runtime-installer
  python3 scripts/dev.py contracts-check
  ```

  Expected: fail because codes and runtime installer contract definitions do not exist.

- [ ] **Step 3: Add schema definitions and error codes**

  Add generated contract definitions for:
  - `RuntimeInstallStepStatus`: `pending`, `running`, `passed`, `failed`, `skipped`, `warning`.
  - `RuntimeInstallStepId`: the 13 fixed step IDs.
  - `RuntimeInstallStep`.
  - `RuntimeInstallProbeResult`.
  - `RuntimeInstallSnapshot`.
  - `RuntimeInstallerInitialState`.
  - `RuntimeInstallerCommand` with `close`, `start_or_attach`, and `frontend.log` command payloads.

  Add new runtime error-code constants in `error_codes.py`.

- [ ] **Step 4: Regenerate contracts**

  Run:

  ```bash
  python3 scripts/dev.py contracts-generate
  python3 scripts/dev.py contracts-check
  ```

  Expected: generated Python and TypeScript contracts are current.

- [ ] **Step 5: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_error_codes.py
  cd settings_ui && npm run test -- runtime-installer
  ```

  Expected: focused tests pass.

- [ ] **Step 6: Commit**

  Commit only the contract/error-code changes. Include in the commit body why structured snapshots need generated contracts and how the new error codes improve failure triage.

---

### Task 2: Pure Runtime Install Progress Model

**Files:**
- Create: `addon/anki_audio_quick_editor/runtime_install_progress.py`
- Test: `tests/test_runtime_install_progress.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `tests/test_architecture/test_rule23_refactor_module_contracts.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing progress-model tests**

  Add tests for:
  - Initial snapshot contains all 13 steps in design order, all pending, with one operation ID.
  - Running a step marks exactly that step running and earlier passed steps remain passed.
  - Passing, failing, skipping, and warning a step produce JSON-safe detail dictionaries.
  - Failing a step sets `phase=error`, `failed_step_id`, `error_code`, and `error_message`.
  - Download progress details preserve URL, downloaded bytes, expected bytes, and bounded percentage.
  - Snapshot serialization round-trips through generated `RuntimeInstallSnapshot`.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_install_progress.py
  python3 scripts/dev.py test tests/test_architecture/test_rule23_refactor_module_contracts.py
  ```

  Expected: fail because the module and architecture contract entries do not exist.

- [ ] **Step 3: Implement the minimal pure model**

  Implement a small builder/state object with named methods for step transitions. Keep it deterministic and independent from runtime installation side effects.

- [ ] **Step 4: Add architecture contract entries**

  Register `runtime_install_progress` as `Layer.IMPORT_SAFE_CORE`. Its allowed addon deps are `contracts_generated` and `error_codes`. It has no side effects.

- [ ] **Step 5: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_install_progress.py tests/test_architecture/test_rule23_refactor_module_contracts.py
  python3 scripts/dev.py arch
  ```

  Expected: progress model and architecture checks pass.

- [ ] **Step 6: Commit**

  Commit the progress model and architecture contract updates.

---

### Task 3: Single Active Runtime Install Session

**Files:**
- Create: `addon/anki_audio_quick_editor/runtime_install_session.py`
- Modify: `addon/anki_audio_quick_editor/runtime_manager.py`
- Test: `tests/test_runtime_install_session.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `tests/test_architecture/test_rule23_refactor_module_contracts.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing session tests**

  Add tests for:
  - `start_or_attach()` starts one worker for the first request.
  - A second startup/settings request while the first is active attaches to the same operation ID and does not start another worker.
  - Observers receive an immediate latest snapshot when subscribing.
  - Unsubscribing stops delivery to that observer without cancelling the worker.
  - Final ready/error snapshots remain available after completion.
  - Reopening after a failed operation returns the latest failed snapshot until a new repair starts.
  - Exceptions from observer callbacks are logged and do not kill the install worker.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_install_session.py
  ```

  Expected: fail because the session coordinator does not exist.

- [ ] **Step 3: Implement attach-or-start session coordination**

  Keep thread management and observer state in this module. Do not add Anki or Qt imports. Use injected install/verify callables in tests so behavior is deterministic.

- [ ] **Step 4: Re-export session API from runtime manager**

  Expose only the small functions needed by startup/settings/dialog code. Avoid exposing mutable session internals.

- [ ] **Step 5: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_install_session.py
  python3 scripts/dev.py test tests/test_runtime_manager.py
  python3 scripts/dev.py arch
  ```

  Expected: session and existing runtime manager tests pass.

- [ ] **Step 6: Commit**

  Commit the session coordinator.

---

### Task 4: Instrument Runtime Install Orchestration

**Files:**
- Modify: `addon/anki_audio_quick_editor/runtime_install.py`
- Create: `addon/anki_audio_quick_editor/runtime_preflight.py`
- Test: `tests/test_runtime_manager.py`
- Test: `tests/test_runtime_preflight.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing orchestration tests**

  Extend runtime install tests to assert step-level snapshots for:
  - Successful install visits all 13 steps in order.
  - Already-ready runtime runs verification-only state and reports ready without forced reinstall.
  - Malformed or missing manifest fails during select-runtime-package.
  - Unsupported platform fails before download and includes platform details.
  - Preflight rejects unwritable runtime/download directories.
  - Low disk space fails preflight when free bytes are less than twice pack size.
  - Concurrent startup/settings attempts share one operation through `runtime_install_session`.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_manager.py tests/test_runtime_preflight.py tests/test_runtime_install_session.py
  ```

  Expected: fail because orchestration does not emit the new steps and preflight does not exist.

- [ ] **Step 3: Add preflight and step emission**

  Implement preflight before download. Emit snapshots for select package, local state, preflight, download, archive verification, archive contents, unarchive, extracted-file verification, permissions, promote, probes, cleanup, and ready.

- [ ] **Step 4: Preserve old concise runtime status**

  Confirm `runtime_status()` still returns the existing concise shape expected by Settings diagnostics and generated `RuntimeStatus`.

- [ ] **Step 5: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_manager.py tests/test_runtime_preflight.py tests/test_runtime_install_session.py
  python3 scripts/dev.py contracts-check
  ```

  Expected: focused runtime tests and contracts pass.

- [ ] **Step 6: Commit**

  Commit runtime orchestration instrumentation and preflight.

---

### Task 5: Archive, Extraction, Permission, Promotion, And Cleanup Failure Coverage

**Files:**
- Modify: `addon/anki_audio_quick_editor/runtime_archive.py`
- Modify: `addon/anki_audio_quick_editor/runtime_install.py`
- Test: `tests/test_runtime_manager.py`
- Test: `tests/test_runtime_archive.py`

- [ ] **Step 1: Write failing pessimistic archive/install tests**

  Add tests for:
  - Cached archive is revalidated before reuse and rejected when checksum differs from manifest.
  - Download timeout includes URL, downloaded bytes, operation ID, and download step.
  - HTTP failure includes URL and download step.
  - Interrupted partial download removes `*.download`.
  - Archive size mismatch reports expected and actual sizes.
  - Archive SHA mismatch reports expected and actual SHA.
  - Corrupt/non-zip archive maps to archive verification.
  - Unsafe path, unexpected file, and missing file map to archive contents.
  - Extraction write failure leaves no promoted partial runtime and records temp paths.
  - Extracted file size/hash mismatch maps to extracted-file verification.
  - POSIX chmod failure maps to permission step.
  - Windows permission step is skipped or limited to existence/path checks.
  - Promotion failure leaves an existing ready runtime untouched.
  - `runtime_state.json` write failure prevents ready status.
  - Cleanup failure is warning-only when runtime is usable and error when it prevents readiness.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_manager.py
  ```

  Expected: new pessimistic cases fail until archive/install mapping is implemented.

- [ ] **Step 3: Implement failure mapping and details**

  Keep checksums authoritative and size checks diagnostic. Preserve atomic promotion semantics: never remove a prior ready runtime until the new runtime is verified and ready to promote.

- [ ] **Step 4: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_manager.py
  ```

  Expected: runtime install pessimistic tests pass.

- [ ] **Step 5: Commit**

  Commit archive/install failure mapping.

---

### Task 6: Dry-Run Probes, Logging, And Support Report Context

**Files:**
- Create: `addon/anki_audio_quick_editor/runtime_probes.py`
- Modify: `addon/anki_audio_quick_editor/runtime_install.py`
- Modify: `addon/anki_audio_quick_editor/diagnostics_runtime.py`
- Modify: `addon/anki_audio_quick_editor/support_reporting.py`
- Test: `tests/test_runtime_probes.py`
- Test: `tests/test_runtime_manager.py`
- Test: `tests/test_settings_commands_support_report.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing probe and support tests**

  Add tests for:
  - Probe command selection for each supported executable that has a safe diagnostic invocation.
  - Probe success records command, exit code, stdout tail, stderr tail, and timeout false.
  - Probe timeout records timeout true and bounded output.
  - Probe non-zero exit maps to `AQE-RUNTIME-007`.
  - Missing executable maps to `AQE-RUNTIME-007`.
  - Latest failed runtime install operation appears in support report context with operation ID, failed step, code, platform, manifest, URL, and recent step history.
  - Logs/breadcrumbs flush on failed runtime install steps.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_probes.py tests/test_runtime_manager.py tests/test_settings_commands_support_report.py
  ```

  Expected: fail because probes and support context are not wired.

- [ ] **Step 3: Implement probes and support context**

  Keep subprocess calls in `runtime_probes.py`. Bound stdout/stderr tails to keep UI and reports readable. Record probe details into step detail and support context.

- [ ] **Step 4: Add architecture allowances**

  Register `runtime_probes` as import-safe core with `SideEffect.SUBPROCESS_RUN`. Add a specific architecture test that no other new runtime installer core module uses subprocess.

- [ ] **Step 5: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_probes.py tests/test_runtime_manager.py tests/test_settings_commands_support_report.py
  python3 scripts/dev.py arch
  ```

  Expected: probes, support context, and architecture pass.

- [ ] **Step 6: Commit**

  Commit probes and support-report enrichment.

---

### Task 7: Runtime-Required Guardrail

**Files:**
- Create: `addon/anki_audio_quick_editor/runtime_required.py`
- Modify runtime-dependent entry points:
  - `addon/anki_audio_quick_editor/editor_processing.py`
  - `addon/anki_audio_quick_editor/editor_analysis.py`
  - `addon/anki_audio_quick_editor/browser_batch_runner.py`
  - `addon/anki_audio_quick_editor/settings/async_operations.py`
  - `addon/anki_audio_quick_editor/reviewer_integration.py`
- Test: `tests/test_runtime_required.py`
- Test: `tests/test_editor_frontend.py`
- Test: `tests/test_browser_batch_runner.py`
- Test: `tests/test_settings_commands_diagnostics.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing guardrail tests**

  Add tests for:
  - Missing runtime returns structured `AQE-RUNTIME-003` with Settings > Diagnostics > Install/Repair Runtime guidance.
  - Invalid runtime state returns the same guardrail before subprocess invocation.
  - Editor transform path uses the guardrail instead of trying to run ffmpeg.
  - Browser batch path uses the guardrail instead of producing a subprocess/file error.
  - Settings health check reports runtime-not-ready clearly while still allowing support report/log actions.
  - Actions that do not require runtime continue to work.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_required.py tests/test_settings_commands_diagnostics.py
  ```

  Expected: fail because the guardrail helper and call sites are not implemented.

- [ ] **Step 3: Implement guardrail helper and narrow call-site checks**

  Keep the helper import-safe. Make call sites check readiness immediately before runtime-dependent work, not during module import or UI registration.

- [ ] **Step 4: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_required.py tests/test_settings_commands_diagnostics.py tests/test_browser_batch_runner.py tests/test_editor_frontend.py
  ```

  Expected: guardrail tests pass for runtime-required, settings diagnostics, browser batch, and editor frontend paths.

- [ ] **Step 5: Commit**

  Commit runtime-required guardrails.

---

### Task 8: Python Runtime Installer Dialog Shell

**Files:**
- Create: `addon/anki_audio_quick_editor/runtime_installer_dialog.py`
- Create: `addon/anki_audio_quick_editor/runtime_installer_bridge.py`
- Modify: `addon/anki_audio_quick_editor/__init__.py`
- Modify: `addon/anki_audio_quick_editor/settings/__init__.py`
- Modify: `addon/anki_audio_quick_editor/settings/commands.py`
- Test: `tests/test_runtime_installer_dialog.py`
- Test: `tests/test_settings_shell.py`
- Test: `tests/test_settings_commands_diagnostics.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing dialog and settings-shell tests**

  Add tests for:
  - Runtime installer dialog renders WebView content with `window.__AQE_RUNTIME_INSTALLER_INITIAL_STATE__`.
  - Dialog subscribes to the active runtime install session on show/open.
  - Dialog sends snapshots to `window.onRuntimeInstallProgress(...)`.
  - Closing while incomplete shows the exact incomplete-install warning and unsubscribes.
  - Closing after ready does not show the warning.
  - Settings command opens the dialog through the settings shell callback without importing the dialog in `settings/commands.py`.
  - Startup missing/invalid runtime opens the dialog automatically.
  - Startup ready runtime does not open the dialog.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_installer_dialog.py tests/test_settings_shell.py tests/test_settings_commands_diagnostics.py
  ```

  Expected: fail because the dialog and command do not exist.

- [ ] **Step 3: Implement dialog shell and bridge**

  Use `webview_shell.render_webview_content()` and the existing frontend error reporter pattern. Keep dialog code responsible for Qt/WebView lifecycle only.

- [ ] **Step 4: Replace Settings Install/Repair Runtime command path**

  Settings frontend will send a bridge command. Backend command dispatch should call a method/callback on the Settings dialog, not import the installer UI from settings backend.

- [ ] **Step 5: Update startup behavior**

  Replace the current tooltip-only startup flow for missing runtime with opening/attaching the detailed installer. Keep concise success/failure breadcrumbs.

- [ ] **Step 6: Run focused tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_installer_dialog.py tests/test_settings_shell.py tests/test_settings_commands_diagnostics.py
  python3 scripts/dev.py arch
  ```

  Expected: dialog, settings shell, and architecture tests pass.

- [ ] **Step 7: Commit**

  Commit the Python dialog shell and startup/settings integration.

---

### Task 9: Runtime Installer Frontend Bundle

**Files:**
- Create: `settings_ui/src/runtime-installer/main.ts`
- Create: `settings_ui/src/runtime-installer/RuntimeInstallerApp.svelte`
- Create: `settings_ui/src/runtime-installer/runtime-installer-state.ts`
- Create: `settings_ui/src/runtime-installer/bridge.ts`
- Create: `settings_ui/src/runtime-installer/styles.css`
- Create: `settings_ui/vite.runtime-installer.config.ts`
- Modify: `settings_ui/package.json`
- Modify: `settings_ui/src/lib/types.ts`
- Test: `settings_ui/tests/runtime-installer-state.test.ts`
- Test: `settings_ui/tests/runtime-installer-app.test.ts`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`

- [ ] **Step 1: Write failing frontend state tests**

  Add tests for:
  - All 13 fixed steps render in order from a snapshot.
  - Running, passed, failed, skipped, and warning states map to stable display labels/classes.
  - Failure state exposes code, operation ID, failed step, and repair guidance.
  - Download byte progress formats expected and actual byte values without changing the step order.
  - Missing optional details do not crash rendering.
  - Reopening after failure preserves failed step details from initial state.

- [ ] **Step 2: Write failing component tests**

  Add tests for:
  - Header shows runtime state, manifest ID, platform, operation ID.
  - Checklist rows are present with stable `data-testid` values.
  - Expanded details include URL, paths, hashes, byte counts, command, exit code, stdout/stderr tails when present.
  - Close button sends the `runtime_installer.close` bridge command.
  - No native `title` attributes are introduced.
  - Long URL/path/hash text wraps instead of overflowing its container.

- [ ] **Step 3: Run failing frontend tests**

  Run:

  ```bash
  cd settings_ui && npm run test -- runtime-installer frontend-architecture
  ```

  Expected: fail because runtime-installer frontend modules and architecture area do not exist.

- [ ] **Step 4: Implement frontend bundle**

  Build the installer as its own feature area under `src/runtime-installer/`. Use shared lib components only. Keep the UI dense, utilitarian, and checklist-focused.

- [ ] **Step 5: Add Vite build target**

  Update `npm run build` to include the runtime installer bundle and output to `addon/anki_audio_quick_editor/templates/runtime-installer/`.

- [ ] **Step 6: Run focused frontend validation**

  Run:

  ```bash
  cd settings_ui && npm run test -- runtime-installer frontend-architecture
  cd settings_ui && npm run check
  cd settings_ui && npm run typecheck
  ```

  Expected: focused frontend tests, Svelte check, and TypeScript pass.

- [ ] **Step 7: Commit**

  Commit the runtime installer frontend bundle and tests.

---

### Task 10: Settings Frontend Integration

**Files:**
- Modify: `settings_ui/src/settings/SettingsApp.svelte`
- Modify: `settings_ui/src/settings/DiagnosticsPanel.svelte`
- Modify: `settings_ui/src/lib/bridge.ts`
- Test: `settings_ui/tests/app.test.ts`
- Test: `settings_ui/tests/runtime-installer-app.test.ts`
- Test: `settings_ui/tests/bridge.test.ts`

- [ ] **Step 1: Write failing settings frontend tests**

  Add tests for:
  - Clicking Install/Repair Runtime sends a bridge command to open the detailed installer.
  - The button no longer starts `runtime_install` via the small async progress flow.
  - Diagnostics still shows concise runtime status.
  - Existing health check, support report, show log file, and check media actions still work.
  - Closing the installer during active install shows warning through backend dialog tests, not through Settings UI state.

- [ ] **Step 2: Run failing tests**

  Run:

  ```bash
  cd settings_ui && npm run test -- app bridge runtime-installer
  ```

  Expected: fail because Settings still calls `startAsyncOp("runtime_install")`.

- [ ] **Step 3: Implement settings bridge command**

  Add a typed bridge helper for opening the installer. Keep Settings UI separate from runtime-installer components.

- [ ] **Step 4: Run focused tests**

  Run:

  ```bash
  cd settings_ui && npm run test -- app bridge runtime-installer
  cd settings_ui && npm run typecheck
  ```

  Expected: settings frontend tests and typecheck pass.

- [ ] **Step 5: Commit**

  Commit settings frontend integration.

---

### Task 11: Architecture Boundary Tests

**Files:**
- Create: `tests/test_architecture/test_rule25_runtime_installer_boundaries.py`
- Modify: `tests/test_architecture/contract_core.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule23_refactor_module_contracts.py`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing architecture tests**

  Add Python architecture checks for:
  - New runtime core modules are classified and tracked by import-linter.
  - `runtime_install_progress.py` imports no Anki, Qt, subprocess, network, archive, settings, or UI modules.
  - `runtime_install_session.py` imports no Anki, Qt, settings, or dialog modules.
  - `runtime_probes.py` is the only new runtime installer core module with subprocess side effects.
  - `runtime_install.py` imports no installer dialog, settings shell/backend, or WebView shell.
  - `settings/commands.py` does not import `runtime_installer_dialog`.
  - `runtime_installer_dialog.py` is UI adapter layer and can depend on WebView shell and runtime install session.

  Add frontend architecture checks for:
  - `src/runtime-installer/*` cannot import settings, editor-inline, or batch modules.
  - Settings frontend cannot import runtime-installer components.
  - Shared `src/lib/*` cannot import runtime-installer modules.
  - Runtime installer bundle is excluded from generated-template file checks.

- [ ] **Step 2: Run failing architecture tests**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_architecture/test_rule25_runtime_installer_boundaries.py tests/test_architecture/test_rule23_refactor_module_contracts.py
  cd settings_ui && npm run test -- frontend-architecture
  python3 scripts/dev.py arch
  ```

  Expected: fail until contracts/import-linter/frontend architecture lists are updated.

- [ ] **Step 3: Update architecture contracts**

  Classify each new module with explicit allowed deps and side effects. Update `pyproject.toml` import-linter source/forbidden lists through the existing contract-driven pattern, not by manually weakening the rule.

- [ ] **Step 4: Run architecture checks**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_architecture/test_rule25_runtime_installer_boundaries.py tests/test_architecture/test_rule23_refactor_module_contracts.py
  cd settings_ui && npm run test -- frontend-architecture
  python3 scripts/dev.py arch
  ```

  Expected: architecture checks pass.

- [ ] **Step 5: Commit**

  Commit architecture boundary tests and contract updates.

---

### Task 12: E2E Runtime Installer Coverage

**Files:**
- Create: `e2e/test_runtime_installer_workflow.py`
- Modify: `e2e/conftest.py`
- Modify: `e2e/settings_dialog_helpers.py`
- Modify e2e fixtures to inject test runtime manifests and failure modes through local files.

- [ ] **Step 1: Write failing e2e tests**

  Add e2e coverage for:
  - Startup with missing runtime opens the detailed installer window.
  - Dismissing incomplete install shows the warning.
  - Settings > Diagnostics > Install/Repair Runtime opens the same detailed installer.
  - Forced checksum/archive failure shows failed step, coded message, and operation ID.
  - Forced download/archive failure leaves no promoted partial runtime and a later repair can retry.
  - Runtime-dependent editor or batch action after dismissed/failed install shows coded repair guidance instead of subprocess/file error.
  - Successful install lets a runtime-dependent action proceed past the guardrail.

- [ ] **Step 2: Run failing e2e target**

  Run the canonical e2e target:

  ```bash
  python3 scripts/dev.py test-e2e
  ```

  Expected: new e2e tests fail until the UI and backend are fully wired.

- [ ] **Step 3: Make e2e fixtures deterministic**

  Use local file URLs or fixture-controlled failure modes for runtime packs. Do not rely on remote GitHub URLs in e2e.

- [ ] **Step 4: Run e2e again**

  Run:

  ```bash
  python3 scripts/dev.py test-e2e
  ```

  Expected: e2e passes.

- [ ] **Step 5: Commit**

  Commit e2e coverage and fixture support.

---

### Task 13: Documentation And Error Help Pages

**Files:**
- Modify: `ARCHITECTURE.md`
- Modify: `TESTING.md`
- Modify: `WEBVIEW_AND_TEMPLATES.md`
- Modify: `docs/errors/AQE-RUNTIME-003/index.html`
- Create: `docs/errors/AQE-RUNTIME-004/index.html`
- Create: `docs/errors/AQE-RUNTIME-005/index.html`
- Create: `docs/errors/AQE-RUNTIME-006/index.html`
- Create: `docs/errors/AQE-RUNTIME-007/index.html`
- Modify: `docs/errors/index.html`

- [ ] **Step 1: Write docs coverage checks**

  Add or update the docs/error-code coverage test so `AQE-RUNTIME-004` through `AQE-RUNTIME-007` require help pages.

- [ ] **Step 2: Update architecture/testing/template docs**

  Document:
  - Detailed runtime installer as canonical startup/repair UI.
  - Step-level logging and operation ID in support reports.
  - New runtime-installer WebView bundle and build output.
  - Pessimistic runtime installer test coverage expectations.

- [ ] **Step 3: Update error help pages**

  Ensure each runtime code page tells users:
  - What failed.
  - The repair path: Settings > Diagnostics > Install/Repair Runtime.
  - What to include in bug reports: operation ID, failed step, platform, manifest ID, and logs/support report.

- [ ] **Step 4: Run docs-focused checks**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_error_codes.py
  python3 scripts/dev.py contracts-check
  ```

  Expected: docs/code references are consistent.

- [ ] **Step 5: Commit**

  Commit docs and help pages.

---

### Task 14: Full Verification And Cleanup

**Files:**
- All files touched by prior tasks

- [ ] **Step 1: Run backend focused suite**

  Run:

  ```bash
  python3 scripts/dev.py test tests/test_runtime_manager.py tests/test_runtime_install_progress.py tests/test_runtime_install_session.py tests/test_runtime_preflight.py tests/test_runtime_probes.py tests/test_runtime_required.py tests/test_runtime_installer_dialog.py
  ```

  Expected: all focused runtime installer backend tests pass.

- [ ] **Step 2: Run frontend validation**

  Run:

  ```bash
  python3 scripts/dev.py test-svelte
  ```

  Expected: Svelte check, ESLint, TypeScript, Vitest, coverage, and frontend bundle generation pass.

- [ ] **Step 3: Run architecture and contract gates**

  Run:

  ```bash
  python3 scripts/dev.py contracts-check
  python3 scripts/dev.py arch
  python3 scripts/dev.py test tests/test_architecture
  ```

  Expected: generated contracts are current, import-linter passes, and architecture tests pass.

- [ ] **Step 4: Run full QC**

  Run:

  ```bash
  python3 scripts/dev.py check
  ```

  Expected: full QC passes.

- [ ] **Step 5: Run canonical e2e**

  Run:

  ```bash
  python3 scripts/dev.py test-e2e
  ```

  Expected: e2e passes.

- [ ] **Step 6: Inspect generated templates and git status**

  Run:

  ```bash
  git status --short
  git diff --check
  ```

  Expected: no whitespace errors. Generated frontend templates may be ignored by git; tracked source/docs/contracts/test changes are intentional.

- [ ] **Step 7: Final implementation commit**

  Commit any final docs or cleanup left after the earlier slice commits. The commit body must explain why the final cleanup matters and mention if full check/e2e were not run.

---

## Plan Self-Review

Spec coverage:

- Startup and Settings both open the detailed installer: Tasks 8, 10, 12.
- Dismissal warning without disabling add-on or hiding UI: Tasks 8, 10, 12.
- Runtime-dependent guardrail with coded repair guidance: Task 7.
- Step-level progress model and all 13 steps: Tasks 1, 2, 4, 5, 6, 10.
- Size/checksum/archive/extract/permission/dry-run/cleanup coverage: Tasks 4, 5, 6.
- Error identifiers and support-report context: Tasks 1, 6, 13.
- Pessimistic scenarios: Tasks 3, 4, 5, 6, 7, 12.
- Architecture boundaries: Task 11, with contract updates in tasks that introduce modules.
- Documentation: Task 13.
- Full verification: Task 14.

Risk notes:

- The largest integration risk is event delivery from background runtime install sessions into an AnkiWebView dialog. Keep this behind `runtime_install_session` and dialog tests before touching frontend rendering.
- The second largest risk is accidentally letting settings backend import dialog/UI code. The plan adds explicit architecture tests before final verification.
- The third largest risk is e2e flakiness around startup timing. Fixture-controlled local runtime packs and attach-to-active-session behavior should keep tests deterministic.
