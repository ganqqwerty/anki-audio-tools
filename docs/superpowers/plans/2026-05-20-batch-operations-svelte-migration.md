# Batch Operations Svelte Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Browser batch operations Qt control surface with a Svelte-powered Anki WebView while preserving the existing batch workflow and Python executor behavior.

**Architecture:** Keep `browser_integration.py`, `batch_operations.py`, and `browser_report.py` responsible for Browser selection, background execution, collection writes, cancellation, progress, and reports. Replace only the presentation layer in `browser_dialog.py` with an `AnkiWebView` shell that mounts a new Svelte batch bundle, and add a small import-safe state/contract helper so the shell stays thin. Shared Editor/Batch behavior stays in existing Python operation modules and extracted frontend `$lib` helpers; Svelte owns form state and rendering only.

**Tech Stack:** Python 3.13, Anki 25.09 `AnkiWebView`, Svelte 5, TypeScript, Vite IIFE bundles, generated JSON communication contracts, pytest, Vitest, GitNexus, `python3 scripts/dev.py` QC commands.

---

## Requirements

### Functional Requirements

- Keep the Browser menu action **Run Audio Batch Operation...** and its selected-note behavior.
- Preserve the existing operation set:
  - `graph`
  - `remove_pauses`
  - `slower`
  - `faster`
  - `volume_down`
  - `volume_up`
- Preserve the existing batch execution path:
  - `browser_integration._open_batch_dialog()`
  - `browser_integration._run_batch_in_background()`
  - `browser_integration._run_batch()`
  - `batch_operations.process_note_batch_operation()`
- Preserve the current dialog behavior:
  - choose operation and source field before starting
  - choose target field only for `graph`
  - show speed parameter only for `slower` and `faster`
  - show volume parameter only for `volume_down` and `volume_up`
  - show pause aggressiveness only for `remove_pauses`
  - disable operation, field, and parameter controls while running
  - show progress, status text, and append-only log lines
  - Cancel requests stop after the current note
  - Copy Log copies the Python-held log text
  - Cancel button becomes Close after success or failure
- Do not add a Qt fallback or feature flag.
- Do not redesign the workflow or add new batch operations.
- Preserve test coverage: do not delete, skip, xfail, or weaken existing Python, frontend, or e2e tests to make the migration pass.
- Existing e2e tests must be adjusted only for the Svelte/WebView surface when selectors or rendered structure change. The current e2e suite has editor/settings coverage, not a dedicated Browser batch workflow test; keep that coverage intact and do not replace e2e coverage with lower-level tests.

### Non-Functional Requirements

- Read `ANKI_API.md` before changing Anki-facing code and verify the installed `aqt.webview.AnkiWebView` signatures if changing shell behavior.
- Run GitNexus impact before editing any function, class, or method.
- Run `gitnexus_detect_changes(scope="all")` before any commit.
- Keep generated bundle files ignored in git; regenerate them for local runtime and e2e verification.
- Use generated communication contracts for Python/TypeScript payloads instead of ad hoc `Any` shapes.
- Keep bridge side effects isolated to bridge modules and Python dialog shell code.
- Keep the Svelte frontends independent at the architecture-test level: `src/settings/`, `src/editor-inline/`, and `src/batch/` are sibling applications that may share code only through `src/lib/` or generated contract types, not by importing each other.
- Keep hand-maintained Svelte files below existing frontend line limits by splitting the batch UI into focused components.
- Keep Python coverage at or above the existing configured gate: `coverage.py` and `scripts/dev_tasks/coverage.py` currently fail below 80%.
- Keep frontend coverage at or above the current Vitest coverage behavior by adding new Svelte tests for the batch UI instead of excluding files from coverage.

### GitNexus Findings Already Collected

- `BatchOperationsDialog` upstream impact: LOW risk, one direct importer: `browser_integration.py`.
- `browser_integration._open_batch_dialog` upstream impact: LOW risk, one direct caller: `_on_browser_menus_did_init`.
- `browser_integration._create_dialog` upstream impact: LOW risk, one direct caller: `_open_batch_dialog`.
- `browser_integration._run_batch` upstream impact: LOW risk, direct caller is the background `task` closure.
- `browser_integration._run_batch_in_background` showed no graph callers in the current index, but tests call it directly. Re-run impact before editing because the index can lag local changes.

### Reuse And Sharing Decisions

- Reuse Python operation contracts instead of duplicating behavior:
  - `audio_operations.py` remains the shared source for operation names, labels, `BATCH_OPERATIONS`, and `requires_target_field()`.
  - `audio_operation_params.py` already shares parameter parsing, clamping, and effective `AudioProcessingConfig` construction between Editor and batch. The Svelte migration must keep using it through `BatchRunRequest.parameters` and `process_note_batch_operation()`.
  - `batch_operations.py` and `browser_report.py` remain the shared batch execution and report core; the Svelte work must not move media writes, note updates, or report formatting into TypeScript.
- Reuse frontend infrastructure already shared by settings/editor:
  - use `$lib/i18n.ts` for `configureI18n()` and `t()`;
  - use `$lib/logger.ts` via `createLogger("batch", ...)`;
  - use `$lib/bridge.ts` for the low-level `pycmd` sender;
  - use generated contract types from `$lib/types.ts`.
- Extract frontend audio-operation parameter helpers from `settings_ui/src/editor-inline/split-button-state.ts` into a new `$lib/audio-operation-parameters.ts` module. Shared helpers should include speed/volume clamp constants, pause aggressiveness values, and formatters; editor-specific per-field state stays in `split-button-state.ts`.
- Do not reuse `SplitButton.svelte` directly for the batch dialog. It is coupled to editor field ordinals and `window.__aqeSplitButtonStates`; the batch dialog should reuse the extracted pure helpers and build its own form controls.
- `CommandIcon.svelte` is reusable if the batch UI introduces icon buttons. If the batch UI needs a missing icon such as copy/close, extend `icon-types.ts` and `CommandIcon.svelte` once and keep both Editor and batch on the same icon wrapper.
- Add frontend architecture tests for this dependency model. The tests must fail if batch imports editor/settings modules, if editor imports batch/settings modules, if settings imports editor/batch modules, or if shared `$lib` modules import any feature frontend. The only allowed cross-frontend sharing path is `$lib` plus generated contracts.

---

## File Structure

- Modify `contracts/communication.schema.json`: add typed batch initial state, start request, progress, log, finish, and error payload contracts.
- Regenerate ignored files:
  - `addon/anki_audio_quick_editor/contracts_generated.py`
  - `settings_ui/src/lib/generated/contracts.ts`
- Modify `settings_ui/src/lib/types.ts`: export generated batch contract types.
- Modify `settings_ui/src/lib/i18n.ts`: add fallback batch and operation labels.
- Create `settings_ui/src/lib/audio-operation-parameters.ts`: shared frontend clamp/format helpers extracted from the editor split-button state module.
- Modify `settings_ui/src/editor-inline/split-button-state.ts`: import shared clamp/format helpers and keep only editor field state plus command payload construction locally.
- Add `settings_ui/tests/audio-operation-parameters.test.ts`.
- Create `settings_ui/src/batch/main.ts`: Svelte IIFE bundle entrypoint.
- Create `settings_ui/src/batch/BatchApp.svelte`: root state and callback registration.
- Create `settings_ui/src/batch/BatchControls.svelte`: operation, field, and parameter form controls.
- Create `settings_ui/src/batch/BatchFooter.svelte`: Start, Copy Log, Cancel, and Close buttons.
- Create `settings_ui/src/batch/batch-state.ts`: pure state helpers and payload construction.
- Create `settings_ui/src/batch/bridge.ts`: `pycmd` command sender and `window.onBatch*` callback registration.
- Add `settings_ui/tests/batch-state.test.ts`, `settings_ui/tests/batch-bridge.test.ts`, and `settings_ui/tests/batch-app.test.ts`.
- Create `settings_ui/vite.batch.config.ts` and update `settings_ui/package.json` build scripts.
- Modify `settings_ui/eslint.config.js` and `settings_ui/tests/frontend-architecture.test.ts` for the new bridge, source area, and explicit no-direct-dependencies rules between the settings, editor, and batch frontends.
- Create `addon/anki_audio_quick_editor/browser_dialog_state.py`: new import-safe state builder and `BatchStartRequest` decoder.
- Modify `addon/anki_audio_quick_editor/browser_dialog.py`: replace Qt child controls with the webview shell and bridge command handler.
- Modify `addon/anki_audio_quick_editor/browser_integration.py`: keep dialog factory compatible with the new shell and avoid executor changes unless tests require a tiny adapter adjustment.
- Add or update `tests/test_browser_dialog_state.py`, `tests/test_browser_dialog.py`, and `tests/test_browser_integration.py`.
- Modify `tests/test_architecture/contract_ui.py` and affected rule tests to include `browser_dialog_state`.
- Modify build/release/docs files:
  - `.gitignore`
  - `WEBVIEW_AND_TEMPLATES.md`
  - `scripts/release.py`
  - `scripts/release_smoke.py`
  - `tests/test_release.py`

---

## Implementation Plan

### Task 1: Add Batch Communication Contracts

**Files:**
- Modify: `contracts/communication.schema.json`
- Modify: `settings_ui/src/lib/types.ts`
- Regenerate: `addon/anki_audio_quick_editor/contracts_generated.py`
- Regenerate: `settings_ui/src/lib/generated/contracts.ts`

- [ ] **Step 1: Run impact analysis for generated-contract consumers before editing schema-adjacent code**

Run:

```text
gitnexus_impact({repo: "anki-audio-tools", target: "handle_settings_command", file_path: "addon/anki_audio_quick_editor/settings/commands.py", direction: "upstream", includeTests: true})
gitnexus_impact({repo: "anki-audio-tools", target: "BatchRunRequest", file_path: "addon/anki_audio_quick_editor/batch_operations.py", direction: "upstream", includeTests: true})
```

Expected: `handle_settings_command` impact stays limited to settings shell tests, and `BatchRunRequest` impact includes Browser/batch tests. Do not edit settings command behavior for this task.

- [ ] **Step 2: Add schema definitions**

In `contracts/communication.schema.json`, add top-level properties:

```json
"batchInitialState": { "$ref": "#/definitions/BatchInitialState" },
"batchStartRequest": { "$ref": "#/definitions/BatchStartRequest" },
"batchProgressPayload": { "$ref": "#/definitions/BatchProgressPayload" },
"batchLogPayload": { "$ref": "#/definitions/BatchLogPayload" },
"batchFinishPayload": { "$ref": "#/definitions/BatchFinishPayload" },
"batchErrorPayload": { "$ref": "#/definitions/BatchErrorPayload" }
```

Add definitions:

```json
"BatchOperationName": {
  "enum": ["graph", "remove_pauses", "slower", "faster", "volume_down", "volume_up"]
},
"BatchParameterKind": {
  "enum": ["none", "speed", "volume", "pause"]
},
"BatchPauseAggressiveness": {
  "enum": ["gentle", "normal", "aggressive"]
},
"BatchOperationParameters": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "speed_step": { "type": "number" },
    "volume_step_db": { "type": "number" },
    "pause_aggressiveness": { "$ref": "#/definitions/BatchPauseAggressiveness" }
  }
},
"BatchOperationOption": {
  "type": "object",
  "additionalProperties": false,
  "required": ["operation", "label", "requires_target_field", "parameter_kind"],
  "properties": {
    "operation": { "$ref": "#/definitions/BatchOperationName" },
    "label": { "type": "string" },
    "requires_target_field": { "type": "boolean" },
    "parameter_kind": { "$ref": "#/definitions/BatchParameterKind" }
  }
},
"BatchFieldGroup": {
  "type": "object",
  "additionalProperties": false,
  "required": ["notetype_name", "fields"],
  "properties": {
    "notetype_name": { "type": "string" },
    "fields": { "type": "array", "items": { "type": "string" } }
  }
},
"BatchDefaults": {
  "type": "object",
  "additionalProperties": false,
  "required": ["speed_step", "volume_step_db", "pause_aggressiveness"],
  "properties": {
    "speed_step": { "type": "number" },
    "volume_step_db": { "type": "number" },
    "pause_aggressiveness": { "$ref": "#/definitions/BatchPauseAggressiveness" }
  }
},
"BatchInitialState": {
  "type": "object",
  "additionalProperties": false,
  "required": ["note_count", "operations", "field_groups", "defaults", "locale", "direction", "messages"],
  "properties": {
    "note_count": { "type": "integer" },
    "operations": { "type": "array", "items": { "$ref": "#/definitions/BatchOperationOption" } },
    "field_groups": { "type": "array", "items": { "$ref": "#/definitions/BatchFieldGroup" } },
    "defaults": { "$ref": "#/definitions/BatchDefaults" },
    "locale": { "type": "string" },
    "direction": { "enum": ["ltr", "rtl"] },
    "messages": { "type": "object", "additionalProperties": { "type": "string" } }
  }
},
"BatchStartRequest": {
  "type": "object",
  "additionalProperties": false,
  "required": ["operation", "source_field", "parameters"],
  "properties": {
    "operation": { "$ref": "#/definitions/BatchOperationName" },
    "source_field": { "type": "string" },
    "target_field": { "type": ["string", "null"] },
    "parameters": { "$ref": "#/definitions/BatchOperationParameters" }
  }
},
"BatchProgressPayload": {
  "type": "object",
  "additionalProperties": false,
  "required": ["processed", "total", "current_audio", "failures", "message"],
  "properties": {
    "processed": { "type": "integer" },
    "total": { "type": "integer" },
    "current_audio": { "type": "string" },
    "failures": { "type": "integer" },
    "message": { "type": "string" }
  }
},
"BatchLogPayload": {
  "type": "object",
  "additionalProperties": false,
  "required": ["line"],
  "properties": {
    "line": { "type": "string" }
  }
},
"BatchFinishPayload": {
  "type": "object",
  "additionalProperties": false,
  "required": ["processed", "total", "written", "skipped", "failures", "canceled", "summary"],
  "properties": {
    "processed": { "type": "integer" },
    "total": { "type": "integer" },
    "written": { "type": "integer" },
    "skipped": { "type": "integer" },
    "failures": { "type": "integer" },
    "canceled": { "type": "boolean" },
    "summary": { "type": "string" }
  }
},
"BatchErrorPayload": {
  "type": "object",
  "additionalProperties": false,
  "required": ["message"],
  "properties": {
    "message": { "type": "string" }
  }
}
```

- [ ] **Step 3: Regenerate contracts**

Run:

```bash
python3 scripts/dev.py contracts-generate
```

Expected: writes `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts`.

- [ ] **Step 4: Export batch types from frontend type barrel**

Update `settings_ui/src/lib/types.ts` to export these generated names:

```ts
export type {
  BatchErrorPayload,
  BatchFieldGroup,
  BatchFinishPayload,
  BatchInitialState,
  BatchLogPayload,
  BatchOperationOption,
  BatchOperationParameters,
  BatchProgressPayload,
  BatchStartRequest,
} from "./generated/contracts.js";
export {
  BatchOperationName,
  BatchParameterKind,
  BatchPauseAggressiveness,
} from "./generated/contracts.js";
```

- [ ] **Step 5: Verify contract generation**

Run:

```bash
python3 scripts/dev.py contracts-check
```

Expected: PASS with `Generated communication contracts are up to date.`

### Task 2: Build Import-Safe Batch Dialog State Helpers

**Files:**
- Create: `addon/anki_audio_quick_editor/browser_dialog_state.py`
- Add: `tests/test_browser_dialog_state.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Modify: `tests/test_architecture/test_rule19_shared_operation_contracts.py`

- [ ] **Step 1: Run impact analysis before adding helpers consumed by the dialog**

Run:

```text
gitnexus_impact({repo: "anki-audio-tools", target: "BatchOperationsDialog", file_path: "addon/anki_audio_quick_editor/browser_dialog.py", direction: "upstream", includeTests: true})
gitnexus_impact({repo: "anki-audio-tools", target: "BatchRunRequest", file_path: "addon/anki_audio_quick_editor/batch_operations.py", direction: "upstream", includeTests: true})
```

Expected: LOW risk for the dialog wrapper and direct batch request consumers in unit tests.

- [ ] **Step 2: Write state helper tests**

Create `tests/test_browser_dialog_state.py`:

```python
from anki_audio_quick_editor.audio_operations import OP_FASTER, OP_GRAPH, OP_REMOVE_PAUSES
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import FieldGroup
from anki_audio_quick_editor.browser_dialog_state import (
    build_batch_initial_state,
    batch_finish_payload,
    batch_progress_payload,
    request_from_batch_start_payload,
)
from anki_audio_quick_editor.browser_report import BatchRunReport


def test_build_batch_initial_state_contains_operations_fields_defaults_and_i18n() -> None:
    state = build_batch_initial_state(
        note_count=3,
        groups=(FieldGroup("Basic", ("Audio", "Image")),),
        config=AudioProcessingConfig(speed_step=0.1, volume_step_db=6.0, pause_aggressiveness="aggressive"),
    )

    assert state["note_count"] == 3
    assert state["field_groups"] == [{"notetype_name": "Basic", "fields": ["Audio", "Image"]}]
    assert state["defaults"] == {
        "speed_step": 0.1,
        "volume_step_db": 6.0,
        "pause_aggressiveness": "aggressive",
    }
    graph = next(item for item in state["operations"] if item["operation"] == OP_GRAPH)
    faster = next(item for item in state["operations"] if item["operation"] == OP_FASTER)
    pause = next(item for item in state["operations"] if item["operation"] == OP_REMOVE_PAUSES)
    assert graph["requires_target_field"] is True
    assert graph["parameter_kind"] == "none"
    assert faster["parameter_kind"] == "speed"
    assert pause["parameter_kind"] == "pause"
    assert state["locale"] == "en"
    assert state["direction"] == "ltr"
    assert "batch.start" in state["messages"]


def test_request_from_batch_start_payload_builds_batch_run_request() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "faster",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {"speed_step": 0.2},
        }
    )

    assert request.operation == "faster"
    assert request.source_field == "Audio"
    assert request.target_field is None
    assert request.parameters.speed_step == 0.2


def test_request_from_batch_start_payload_rejects_missing_graph_target() -> None:
    try:
        request_from_batch_start_payload(
            {
                "operation": "graph",
                "source_field": "Audio",
                "target_field": None,
                "parameters": {},
            }
        )
    except ValueError as exc:
        assert str(exc) == "Choose a target field before starting."
    else:
        raise AssertionError("expected missing graph target to fail")


def test_progress_and_finish_payloads_match_frontend_contract() -> None:
    progress = batch_progress_payload(
        processed=1,
        total=3,
        current_audio="clip.mp3",
        failures=0,
        message="Processed 1/3 notes. Current audio: clip.mp3. Failures: 0.",
    )
    report = BatchRunReport(total=3, processed=2, written=1, skipped=1, failures=0, messages={})
    finish = batch_finish_payload(report)

    assert progress == {
        "processed": 1,
        "total": 3,
        "current_audio": "clip.mp3",
        "failures": 0,
        "message": "Processed 1/3 notes. Current audio: clip.mp3. Failures: 0.",
    }
    assert finish == {
        "processed": 2,
        "total": 3,
        "written": 1,
        "skipped": 1,
        "failures": 0,
        "canceled": False,
        "summary": report.summary,
    }
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_browser_dialog_state.py -q
```

Expected: FAIL because `browser_dialog_state.py` does not exist.

- [ ] **Step 4: Implement `browser_dialog_state.py`**

Create `addon/anki_audio_quick_editor/browser_dialog_state.py` with these public helpers:

```python
"""Import-safe state and contract helpers for the Browser batch dialog."""

from __future__ import annotations

from typing import Any

from .audio_operation_params import parameters_from_raw
from .audio_operations import (
    BATCH_OPERATIONS,
    OP_FASTER,
    OP_GRAPH,
    OP_REMOVE_PAUSES,
    OP_SLOWER,
    OP_VOLUME_DOWN,
    OP_VOLUME_UP,
    operation_label,
    requires_target_field,
)
from .audio_state import AudioProcessingConfig
from .batch_operations import BatchRunRequest, FieldGroup
from .browser_report import BatchRunReport
from .contracts_generated import BatchStartRequest
from .i18n import active_context, format_message

CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def build_batch_initial_state(
    *,
    note_count: int,
    groups: tuple[FieldGroup, ...],
    config: AudioProcessingConfig,
) -> dict[str, Any]:
    """Return JSON-serializable state consumed by the batch Svelte app."""
    i18n = active_context()
    messages = dict(i18n["messages"])
    return {
        "note_count": note_count,
        "operations": [_operation_option(operation, messages) for operation in BATCH_OPERATIONS],
        "field_groups": [
            {"notetype_name": group.notetype_name, "fields": list(group.fields)}
            for group in groups
        ],
        "defaults": {
            "speed_step": config.speed_step,
            "volume_step_db": config.volume_step_db,
            "pause_aggressiveness": config.pause_aggressiveness,
        },
        "locale": i18n["locale"],
        "direction": i18n["direction"],
        "messages": messages,
    }


def request_from_batch_start_payload(raw_payload: object) -> BatchRunRequest:
    """Decode and validate one frontend batch start request."""
    payload = BatchStartRequest.from_dict(raw_payload).to_dict()
    params = payload.get("parameters") or {}
    return BatchRunRequest(
        operation=str(payload.get("operation") or ""),
        source_field=str(payload.get("source_field") or ""),
        target_field=payload.get("target_field"),
        parameters=parameters_from_raw(
            speed_step=params.get("speed_step"),
            volume_step_db=params.get("volume_step_db"),
            pause_aggressiveness=params.get("pause_aggressiveness"),
        ),
    )


def batch_progress_payload(
    *,
    processed: int,
    total: int,
    current_audio: str,
    failures: int,
    message: str,
) -> dict[str, Any]:
    """Return the typed progress payload sent to Svelte."""
    return {
        "processed": processed,
        "total": total,
        "current_audio": current_audio,
        "failures": failures,
        "message": message,
    }


def batch_finish_payload(report: BatchRunReport) -> dict[str, Any]:
    """Return the typed final payload sent to Svelte."""
    return {
        "processed": report.processed,
        "total": report.total,
        "written": report.written,
        "skipped": report.skipped,
        "failures": report.failures,
        "canceled": report.canceled,
        "summary": report.summary,
    }


def invalid_start_message() -> str:
    """Return the stable message for invalid frontend start payloads."""
    return format_message(dict(active_context()["messages"]), "batch.failed", {"error": "Invalid batch request"})


def _operation_option(operation: str, messages: dict[str, str]) -> dict[str, Any]:
    return {
        "operation": operation,
        "label": operation_label(operation, messages),
        "requires_target_field": requires_target_field(operation),
        "parameter_kind": _parameter_kind(operation),
    }


def _parameter_kind(operation: str) -> str:
    if operation in {OP_SLOWER, OP_FASTER}:
        return "speed"
    if operation in {OP_VOLUME_DOWN, OP_VOLUME_UP}:
        return "volume"
    if operation == OP_REMOVE_PAUSES:
        return "pause"
    if operation == OP_GRAPH:
        return "none"
    return "none"
```

- [ ] **Step 5: Update architecture contracts**

In `tests/test_architecture/contract_ui.py`, add a `browser_dialog_state` contract:

```python
"browser_dialog_state": contract(
    "browser_dialog_state",
    layer=Layer.UI_ADAPTER,
    allowed_addon_deps=(
        "audio_operation_params",
        "audio_operations",
        "audio_state",
        "batch_operations",
        "browser_report",
        "contracts_generated",
        "i18n",
    ),
),
```

Update `MODULE_CONTRACTS["browser_dialog"].allowed_addon_deps` expectations in rule tests to include `browser_dialog_state`.

- [ ] **Step 6: Run focused Python tests**

Run:

```bash
python3 -m pytest tests/test_browser_dialog_state.py tests/test_architecture/test_rule19_shared_operation_contracts.py -q
```

Expected: PASS.

### Task 3: Extract Frontend Operation Parameter Helpers Shared With Editor

**Files:**
- Create: `settings_ui/src/lib/audio-operation-parameters.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state.ts`
- Add: `settings_ui/tests/audio-operation-parameters.test.ts`
- Modify: `settings_ui/tests/split-button-state.test.ts` only if imports need to move

- [ ] **Step 1: Run impact analysis before editing editor split-button state**

Run:

```text
gitnexus_impact({repo: "anki-audio-tools", target: "getSplitButtonState", file_path: "settings_ui/src/editor-inline/split-button-state.ts", direction: "upstream", includeTests: true})
gitnexus_impact({repo: "anki-audio-tools", target: "buildSplitCommandPayload", file_path: "settings_ui/src/editor-inline/split-button-state.ts", direction: "upstream", includeTests: true})
```

Expected: frontend editor split-button tests are the main consumers. This task must preserve the current public exports from `split-button-state.ts`.

- [ ] **Step 2: Write shared helper tests**

Create `settings_ui/tests/audio-operation-parameters.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import {
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatPauseAggressiveness,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
} from "../src/lib/audio-operation-parameters.js";
import { configureI18n } from "../src/lib/i18n.js";

describe("audio-operation-parameters", () => {
  it("matches editor and batch clamp ranges", () => {
    expect(clampTrimStepMs(10)).toBe(50);
    expect(clampTrimStepMs(20_000)).toBe(10_000);
    expect(clampVolumeStepDb(99)).toBe(12);
    expect(clampVolumeStepDb(0.1)).toBe(0.5);
    expect(clampSpeedStep(0.001)).toBe(0.01);
    expect(clampSpeedStep(1)).toBe(0.25);
  });

  it("formats operation parameter labels consistently", () => {
    configureI18n("en", "ltr", {});

    expect(formatTrimMs(500)).toBe("500 ms");
    expect(formatTrimMs(1500)).toBe("1.5 s");
    expect(formatVolumeDb(1.5)).toBe("1.5 dB");
    expect(formatSpeedStep(0.1, "faster")).toBe("x1.10");
    expect(formatSpeedStep(0.1, "slower")).toBe("x0.90");
    expect(formatPauseAggressiveness("aggressive")).toBe("Aggressive");
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd settings_ui
npm run test -- audio-operation-parameters.test.ts split-button-state.test.ts
```

Expected: FAIL because `src/lib/audio-operation-parameters.ts` does not exist.

- [ ] **Step 4: Create the shared frontend helper module**

Create `settings_ui/src/lib/audio-operation-parameters.ts`:

```ts
import { t } from "./i18n.js";

export type PauseAggressiveness = "gentle" | "normal" | "aggressive";

const MIN_TRIM_MS = 50;
const MAX_TRIM_MS = 10_000;
const MIN_VOLUME_STEP_DB = 0.5;
const MAX_VOLUME_STEP_DB = 12;
const MIN_SPEED_STEP = 0.01;
const MAX_SPEED_STEP = 0.25;
const MIN_REPEAT_PAUSE_SECONDS = 0;
const MAX_REPEAT_PAUSE_SECONDS = 10;

export function clampTrimStepMs(value: number): number {
  if (!Number.isFinite(value)) return 100;
  return Math.max(MIN_TRIM_MS, Math.min(MAX_TRIM_MS, Math.round(value)));
}

export function clampVolumeStepDb(value: number): number {
  if (!Number.isFinite(value)) return 3;
  return Math.max(MIN_VOLUME_STEP_DB, Math.min(MAX_VOLUME_STEP_DB, Math.round(value * 10) / 10));
}

export function clampSpeedStep(value: number): number {
  if (!Number.isFinite(value)) return 0.05;
  return Math.max(MIN_SPEED_STEP, Math.min(MAX_SPEED_STEP, Math.round(value * 100) / 100));
}

export function clampRepeatPauseSeconds(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(
    MIN_REPEAT_PAUSE_SECONDS,
    Math.min(MAX_REPEAT_PAUSE_SECONDS, Math.round(value * 10) / 10),
  );
}

export function formatTrimMs(value: number): string {
  const ms = clampTrimStepMs(value);
  if (ms < 1000) return `${ms} ms`;
  const seconds = ms / 1000;
  return `${Number.isInteger(seconds) ? seconds.toFixed(0) : seconds.toFixed(1)} s`;
}

export function formatVolumeDb(value: number): string {
  const db = clampVolumeStepDb(value);
  return `${Number.isInteger(db) ? db.toFixed(0) : db.toFixed(1)} dB`;
}

export function formatSpeedStep(value: number, operation: string): string {
  const step = clampSpeedStep(value);
  const multiplier = operation === "aqe:slower" || operation === "slower" ? 1 - step : 1 + step;
  return `x${multiplier.toFixed(2)}`;
}

export function formatRepeatPauseSeconds(value: number): string {
  const seconds = clampRepeatPauseSeconds(value);
  return `${Number.isInteger(seconds) ? seconds.toFixed(0) : seconds.toFixed(1)} s`;
}

export function formatPauseAggressiveness(value: PauseAggressiveness): string {
  if (value === "aggressive") return t("settings.pause_aggressiveness.aggressive");
  if (value === "gentle") return t("settings.pause_aggressiveness.gentle");
  return t("settings.pause_aggressiveness.normal");
}
```

- [ ] **Step 5: Rewire editor split-button state to reuse the shared helpers**

In `settings_ui/src/editor-inline/split-button-state.ts`, replace the local clamp/format constants and functions with imports and re-exports:

```ts
import {
  clampRepeatPauseSeconds,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatPauseAggressiveness,
  formatRepeatPauseSeconds,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
} from "../lib/audio-operation-parameters.js";
export {
  clampRepeatPauseSeconds,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatPauseAggressiveness,
  formatRepeatPauseSeconds,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
} from "../lib/audio-operation-parameters.js";
```

Keep `DEFAULTS`, `fieldStates()`, `getSplitButtonState()`, setters, and command payload builders in `split-button-state.ts` because those are Editor-specific.

- [ ] **Step 6: Run focused shared/editor tests**

Run:

```bash
cd settings_ui
npm run test -- audio-operation-parameters.test.ts split-button-state.test.ts
```

Expected: PASS. Existing editor tests must not be weakened or skipped.

### Task 4: Build Batch Svelte State, Bridge, And Tests

**Files:**
- Create: `settings_ui/src/batch/batch-state.ts`
- Create: `settings_ui/src/batch/bridge.ts`
- Add: `settings_ui/tests/batch-state.test.ts`
- Add: `settings_ui/tests/batch-bridge.test.ts`
- Modify: `settings_ui/eslint.config.js`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`

- [ ] **Step 1: Write batch state tests**

Create `settings_ui/tests/batch-state.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import {
  FALLBACK_BATCH_INITIAL_STATE,
  batchStartRequest,
  selectedOperation,
  shouldShowTargetField,
} from "../src/batch/batch-state.js";
import { BatchOperationName } from "../src/lib/types.js";

describe("batch-state", () => {
  it("selects the current operation and target visibility", () => {
    const graph = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Graph);
    const faster = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Faster);

    expect(graph?.requires_target_field).toBe(true);
    expect(faster?.requires_target_field).toBe(false);
    expect(shouldShowTargetField(graph)).toBe(true);
    expect(shouldShowTargetField(faster)).toBe(false);
  });

  it("builds graph start requests with target field and no parameters", () => {
    expect(
      batchStartRequest({
        operation: BatchOperationName.Graph,
        sourceField: "Audio",
        targetField: "Image",
        speedStep: 0.1,
        volumeStepDb: 6,
        pauseAggressiveness: "aggressive",
      }),
    ).toEqual({
      operation: BatchOperationName.Graph,
      source_field: "Audio",
      target_field: "Image",
      parameters: {},
    });
  });

  it("builds transform start requests with only the active parameter", () => {
    expect(
      batchStartRequest({
        operation: BatchOperationName.Faster,
        sourceField: "Audio",
        targetField: "Image",
        speedStep: 0.2,
        volumeStepDb: 6,
        pauseAggressiveness: "aggressive",
      }),
    ).toEqual({
      operation: BatchOperationName.Faster,
      source_field: "Audio",
      target_field: null,
      parameters: { speed_step: 0.2 },
    });

    expect(
      batchStartRequest({
        operation: BatchOperationName.RemovePauses,
        sourceField: "Audio",
        targetField: "Image",
        speedStep: 0.2,
        volumeStepDb: 6,
        pauseAggressiveness: "gentle",
      }),
    ).toEqual({
      operation: BatchOperationName.RemovePauses,
      source_field: "Audio",
      target_field: null,
      parameters: { pause_aggressiveness: "gentle" },
    });
  });
});
```

- [ ] **Step 2: Write bridge tests**

Create `settings_ui/tests/batch-bridge.test.ts`:

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  batchCancel,
  batchClose,
  batchCopyLog,
  batchStart,
  registerBatchCallbacks,
} from "../src/batch/bridge.js";
import { BatchOperationName } from "../src/lib/types.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;

describe("batch bridge", () => {
  beforeEach(() => {
    delete window.onBatchProgress;
    delete window.onBatchLog;
    delete window.onBatchFinish;
    delete window.onBatchError;
  });

  it("serializes batch commands through pycmd", () => {
    batchStart({ operation: BatchOperationName.Graph, source_field: "Audio", target_field: "Image", parameters: {} });
    batchCancel();
    batchCopyLog();
    batchClose();

    expect(pycmd.mock.calls.map(([command]) => command)).toEqual([
      'batch_start:{"operation":"graph","source_field":"Audio","target_field":"Image","parameters":{}}',
      "batch_cancel",
      "batch_copy_log",
      "batch_close",
    ]);
  });

  it("registers frontend callbacks", () => {
    const callbacks = {
      onProgress: vi.fn(),
      onLog: vi.fn(),
      onFinish: vi.fn(),
      onError: vi.fn(),
    };

    registerBatchCallbacks(callbacks);

    expect(window.onBatchProgress).toBe(callbacks.onProgress);
    expect(window.onBatchLog).toBe(callbacks.onLog);
    expect(window.onBatchFinish).toBe(callbacks.onFinish);
    expect(window.onBatchError).toBe(callbacks.onError);
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd settings_ui
npm run test -- batch-state.test.ts batch-bridge.test.ts
```

Expected: FAIL because batch source files do not exist.

- [ ] **Step 4: Implement `batch-state.ts`**

Create `settings_ui/src/batch/batch-state.ts`:

```ts
import {
  BatchOperationName,
  BatchParameterKind,
  BatchPauseAggressiveness,
  Direction,
} from "$lib/types.js";
import {
  clampSpeedStep,
  clampVolumeStepDb,
} from "$lib/audio-operation-parameters.js";
import type {
  BatchInitialState,
  BatchOperationOption,
  BatchStartRequest,
} from "$lib/types.js";

export interface BatchFormState {
  operation: string;
  sourceField: string;
  targetField: string;
  speedStep: number;
  volumeStepDb: number;
  pauseAggressiveness: string;
}

export const FALLBACK_BATCH_INITIAL_STATE: BatchInitialState = {
  note_count: 0,
  operations: [
    { operation: BatchOperationName.Graph, label: "Graph", requires_target_field: true, parameter_kind: BatchParameterKind.None },
    { operation: BatchOperationName.RemovePauses, label: "Shorten Pauses", requires_target_field: false, parameter_kind: BatchParameterKind.Pause },
    { operation: BatchOperationName.Slower, label: "Slower", requires_target_field: false, parameter_kind: BatchParameterKind.Speed },
    { operation: BatchOperationName.Faster, label: "Faster", requires_target_field: false, parameter_kind: BatchParameterKind.Speed },
    { operation: BatchOperationName.VolumeDown, label: "Volume -", requires_target_field: false, parameter_kind: BatchParameterKind.Volume },
    { operation: BatchOperationName.VolumeUp, label: "Volume +", requires_target_field: false, parameter_kind: BatchParameterKind.Volume },
  ],
  field_groups: [],
  defaults: {
    speed_step: 0.05,
    volume_step_db: 3,
    pause_aggressiveness: BatchPauseAggressiveness.Normal,
  },
  locale: "en",
  direction: Direction.LTR,
  messages: {},
};

export function initialBatchState(): BatchInitialState {
  return window.__AQE_BATCH_INITIAL_STATE__ ?? FALLBACK_BATCH_INITIAL_STATE;
}

export function initialFormState(state: BatchInitialState): BatchFormState {
  const firstOperation = state.operations[0]?.operation ?? BatchOperationName.Graph;
  const firstField = state.field_groups[0]?.fields[0] ?? "";
  return {
    operation: firstOperation,
    sourceField: firstField,
    targetField: firstField,
    speedStep: state.defaults.speed_step,
    volumeStepDb: state.defaults.volume_step_db,
    pauseAggressiveness: state.defaults.pause_aggressiveness,
  };
}

export function selectedOperation(
  state: BatchInitialState,
  operation: string,
): BatchOperationOption | undefined {
  return state.operations.find((item) => item.operation === operation);
}

export function shouldShowTargetField(operation: BatchOperationOption | undefined): boolean {
  return operation?.requires_target_field === true;
}

export function batchStartRequest(form: BatchFormState): BatchStartRequest {
  const request: BatchStartRequest = {
    operation: form.operation as BatchStartRequest["operation"],
    source_field: form.sourceField,
    target_field: form.operation === BatchOperationName.Graph ? form.targetField : null,
    parameters: {},
  };
  if (form.operation === BatchOperationName.Slower || form.operation === BatchOperationName.Faster) {
    request.parameters.speed_step = clampSpeedStep(form.speedStep);
  }
  if (form.operation === BatchOperationName.VolumeDown || form.operation === BatchOperationName.VolumeUp) {
    request.parameters.volume_step_db = clampVolumeStepDb(form.volumeStepDb);
  }
  if (form.operation === BatchOperationName.RemovePauses) {
    request.parameters.pause_aggressiveness = form.pauseAggressiveness as BatchPauseAggressiveness;
  }
  return request;
}
```

- [ ] **Step 5: Implement `batch/bridge.ts`**

Create `settings_ui/src/batch/bridge.ts`:

```ts
import { sendBridgeCommand } from "$lib/bridge.js";
import type {
  BatchErrorPayload,
  BatchFinishPayload,
  BatchLogPayload,
  BatchProgressPayload,
  BatchStartRequest,
} from "$lib/types.js";

export interface BatchCallbacks {
  onProgress?: (payload: BatchProgressPayload) => void;
  onLog?: (payload: BatchLogPayload) => void;
  onFinish?: (payload: BatchFinishPayload) => void;
  onError?: (payload: BatchErrorPayload) => void;
}

export function batchStart(request: BatchStartRequest): void {
  sendBridgeCommand(`batch_start:${JSON.stringify(request)}`);
}

export function batchCancel(): void {
  sendBridgeCommand("batch_cancel");
}

export function batchClose(): void {
  sendBridgeCommand("batch_close");
}

export function batchCopyLog(): void {
  sendBridgeCommand("batch_copy_log");
}

export function registerBatchCallbacks(callbacks: BatchCallbacks): void {
  if (callbacks.onProgress) window.onBatchProgress = callbacks.onProgress;
  if (callbacks.onLog) window.onBatchLog = callbacks.onLog;
  if (callbacks.onFinish) window.onBatchFinish = callbacks.onFinish;
  if (callbacks.onError) window.onBatchError = callbacks.onError;
}

declare global {
  interface Window {
    __AQE_BATCH_INITIAL_STATE__?: import("$lib/types.js").BatchInitialState;
    onBatchProgress?: (payload: BatchProgressPayload) => void;
    onBatchLog?: (payload: BatchLogPayload) => void;
    onBatchFinish?: (payload: BatchFinishPayload) => void;
    onBatchError?: (payload: BatchErrorPayload) => void;
  }
}
```

- [ ] **Step 6: Update lint and frontend architecture tests**

In `settings_ui/eslint.config.js`, update:

```js
const BRIDGE_FILES = ["**/lib/bridge.ts", "**/editor-inline/bridge.ts", "**/batch/bridge.ts"];
```

In `settings_ui/tests/frontend-architecture.test.ts`, update bridge/window side-effect allowlists so `src/batch/bridge.ts` is allowed to assign `window.onBatch*`.

In `settings_ui/tests/frontend-architecture.test.ts`, add architecture tests that enforce the dependency boundary between the three frontends:

```ts
const frontendAreas = [
  { name: "settings", prefix: "src/settings/" },
  { name: "editor", prefix: "src/editor-inline/" },
  { name: "batch", prefix: "src/batch/" },
] as const;

it("keeps settings, editor, and batch frontends independent except shared lib imports", () => {
  const offenders = frontendArchitectureFiles()
    .map((path) => ({ relPath: toRelPath(path), source: readFileSync(path, "utf-8") }))
    .flatMap(({ relPath, source }) => forbiddenFrontendImports(relPath, source));

  expect(offenders).toEqual([]);
});

it("keeps shared lib modules independent from feature frontends", () => {
  const offenders = frontendArchitectureFiles()
    .map((path) => ({ relPath: toRelPath(path), source: readFileSync(path, "utf-8") }))
    .filter(({ relPath, source }) => relPath.startsWith("src/lib/") && importsFeatureFrontend(source))
    .map(({ relPath }) => relPath);

  expect(offenders).toEqual([]);
});

it("keeps batch and editor window contracts separated", () => {
  const offenders = frontendArchitectureFiles()
    .map((path) => ({ relPath: toRelPath(path), source: withoutComments(readFileSync(path, "utf-8")) }))
    .filter(({ relPath, source }) => {
      if (relPath.startsWith("src/batch/")) return /__aqe|__AQE_EDITOR_CONFIG__/.test(source);
      if (relPath.startsWith("src/editor-inline/")) return /__AQE_BATCH_INITIAL_STATE__|onBatch/.test(source);
      return false;
    })
    .map(({ relPath }) => relPath);

  expect(offenders).toEqual([]);
});
```

Implement helper functions in that test file rather than duplicating regex logic inline:

```ts
function frontendArchitectureFiles(): string[] {
  return walk(sourceRoot)
    .filter((path) => /\.(svelte|ts)$/.test(path))
    .filter((path) => isHandMaintainedFrontendFile(toRelPath(path)));
}

function forbiddenFrontendImports(relPath: string, source: string): string[] {
  const owner = frontendAreas.find((area) => relPath.startsWith(area.prefix));
  if (!owner) return [];
  return frontendAreas
    .filter((area) => area.name !== owner.name)
    .filter((area) => importsFrontendArea(source, area.prefix))
    .map((area) => `${relPath}: imports ${area.prefix}`);
}

function importsFeatureFrontend(source: string): boolean {
  return frontendAreas.some((area) => importsFrontendArea(source, area.prefix));
}

function importsFrontendArea(source: string, prefix: string): boolean {
  const imports = Array.from(source.matchAll(/\bfrom\s+["']([^"']+)["']|import\s+["']([^"']+)["']/g), (match) => match[1] ?? match[2] ?? "");
  const areaName = prefix.slice("src/".length, -1);
  return imports.some((specifier) => {
    if (specifier.startsWith("$lib/")) return false;
    if (specifier.startsWith(`../${areaName}/`) || specifier.startsWith(`../../${areaName}/`)) return true;
    return specifier.includes(`/${areaName}/`);
  });
}
```

Keep the existing persisted settings/editor split-state separation test or replace it with the broader three-frontend dependency test above. The new assertions must cover:

- `src/batch/` cannot import `src/editor-inline/` or `src/settings/`.
- `src/editor-inline/` cannot import `src/batch/` or `src/settings/`.
- `src/settings/` cannot import `src/batch/` or `src/editor-inline/`.
- `src/lib/` cannot import any feature frontend.
- Batch source cannot reference editor-only globals such as `__aqe*` or `__AQE_EDITOR_CONFIG__`; editor source cannot reference `__AQE_BATCH_INITIAL_STATE__` or `onBatch*`.

- [ ] **Step 7: Run focused frontend state and bridge tests**

Run:

```bash
cd settings_ui
npm run test -- batch-state.test.ts batch-bridge.test.ts frontend-architecture.test.ts
```

Expected: PASS.

### Task 5: Build Batch Svelte Components

**Files:**
- Create: `settings_ui/src/batch/BatchApp.svelte`
- Create: `settings_ui/src/batch/BatchControls.svelte`
- Create: `settings_ui/src/batch/BatchFooter.svelte`
- Create: `settings_ui/src/batch/main.ts`
- Add: `settings_ui/tests/batch-app.test.ts`
- Modify: `settings_ui/src/lib/i18n.ts`

- [ ] **Step 1: Write app behavior tests**

Create `settings_ui/tests/batch-app.test.ts`:

```ts
import { fireEvent, render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";

import BatchApp from "../src/batch/BatchApp.svelte";
import {
  BatchOperationName,
  BatchParameterKind,
  BatchPauseAggressiveness,
  Direction,
} from "../src/lib/types.js";

function setInitialState(): void {
  window.__AQE_BATCH_INITIAL_STATE__ = {
    note_count: 2,
    operations: [
      { operation: BatchOperationName.Graph, label: "Graph", requires_target_field: true, parameter_kind: BatchParameterKind.None },
      { operation: BatchOperationName.RemovePauses, label: "Shorten Pauses", requires_target_field: false, parameter_kind: BatchParameterKind.Pause },
      { operation: BatchOperationName.Faster, label: "Faster", requires_target_field: false, parameter_kind: BatchParameterKind.Speed },
      { operation: BatchOperationName.VolumeUp, label: "Volume +", requires_target_field: false, parameter_kind: BatchParameterKind.Volume },
    ],
    field_groups: [{ notetype_name: "Basic", fields: ["Audio", "Image"] }],
    defaults: { speed_step: 0.1, volume_step_db: 6, pause_aggressiveness: BatchPauseAggressiveness.Aggressive },
    locale: "en",
    direction: Direction.LTR,
    messages: {},
  };
}

function pycmdMock(): ReturnType<typeof vi.fn> {
  return (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
}

describe("BatchApp", () => {
  it("renders controls and sends a graph start request", async () => {
    setInitialState();
    render(BatchApp);

    expect(screen.getByText("Choose an operation and fields for the selected notes.")).toBeInTheDocument();
    expect(screen.getByLabelText("Target field")).toBeInTheDocument();

    await fireEvent.click(screen.getByRole("button", { name: "Start" }));

    const call = pycmdMock().mock.calls.find(([command]) => String(command).startsWith("batch_start:"))?.[0] as string;
    expect(JSON.parse(call.slice("batch_start:".length))).toEqual({
      operation: BatchOperationName.Graph,
      source_field: "Audio",
      target_field: "Audio",
      parameters: {},
    });
  });

  it("shows only operation-specific parameter controls", async () => {
    setInitialState();
    render(BatchApp);

    await fireEvent.change(screen.getByLabelText("Operation"), { target: { value: BatchOperationName.Faster } });
    expect(screen.queryByLabelText("Target field")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Speed step")).toBeInTheDocument();

    await fireEvent.change(screen.getByLabelText("Operation"), { target: { value: BatchOperationName.RemovePauses } });
    expect(screen.getByLabelText("Shorten pauses level")).toBeInTheDocument();
    expect(screen.queryByLabelText("Speed step")).not.toBeInTheDocument();
  });

  it("updates progress, log, finish state, and copy log command", async () => {
    setInitialState();
    render(BatchApp);

    await fireEvent.click(screen.getByRole("button", { name: "Start" }));
    window.onBatchLog?.({ line: "Starting batch" });
    window.onBatchProgress?.({
      processed: 1,
      total: 2,
      current_audio: "clip.mp3",
      failures: 0,
      message: "Processed 1/2 notes. Current audio: clip.mp3. Failures: 0.",
    });
    window.onBatchFinish?.({
      processed: 2,
      total: 2,
      written: 1,
      skipped: 1,
      failures: 0,
      canceled: false,
      summary: "Completed: 2/2 notes processed, 1 written, 1 skipped, 0 failures.",
    });

    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "2");
    expect(screen.getByText("Starting batch")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();

    await fireEvent.click(screen.getByRole("button", { name: "Copy Log" }));
    expect(pycmdMock()).toHaveBeenCalledWith("batch_copy_log");
  });
});
```

- [ ] **Step 2: Add fallback i18n messages**

In `settings_ui/src/lib/i18n.ts`, add these fallback keys:

```ts
"batch.window_title": "Run Audio Batch Operation",
"batch.instructions": "Choose an operation and fields for the selected notes.",
"batch.operation": "Operation",
"batch.source_field": "Source field",
"batch.target_field": "Target field",
"batch.start": "Start",
"batch.copy_log": "Copy Log",
"batch.cancel": "Cancel",
"batch.close": "Close",
"batch.no_audio": "no audio",
"batch.starting": "Starting {operation} batch...",
"batch.progress": "Processed {processed}/{total} notes. Current audio: {audio}. Failures: {failures}.",
"batch.cancel_requested": "Cancel requested; stopping after the current note.",
"batch.failed": "Batch operation failed: {error}",
"operation.graph": "Graph",
"operation.remove_pauses": "Shorten Pauses",
"operation.slower": "Slower",
"operation.faster": "Faster",
"operation.volume_down": "Volume -",
"operation.volume_up": "Volume +",
```

- [ ] **Step 3: Implement Svelte components**

Create `BatchControls.svelte` with:

```svelte
<script lang="ts">
  import { t } from "$lib/i18n.js";
  import { BatchParameterKind, BatchPauseAggressiveness } from "$lib/types.js";
  import type { BatchInitialState, BatchOperationOption } from "$lib/types.js";
  import type { BatchFormState } from "./batch-state.js";

  interface Props {
    state: BatchInitialState;
    form: BatchFormState;
    selected: BatchOperationOption | undefined;
    disabled: boolean;
  }

  let { state, form = $bindable(), selected, disabled }: Props = $props();
</script>

<div class="batch-grid">
  <label>
    <span>{t("batch.operation")}</span>
    <select bind:value={form.operation} disabled={disabled}>
      {#each state.operations as operation}
        <option value={operation.operation}>{operation.label}</option>
      {/each}
    </select>
  </label>

  <label>
    <span>{t("batch.source_field")}</span>
    <select bind:value={form.sourceField} disabled={disabled}>
      {#each state.field_groups as group}
        {#each group.fields as field}
          <option value={field}>{group.notetype_name} / {field}</option>
        {/each}
      {/each}
    </select>
  </label>

  {#if selected?.requires_target_field}
    <label>
      <span>{t("batch.target_field")}</span>
      <select bind:value={form.targetField} disabled={disabled}>
        {#each state.field_groups as group}
          {#each group.fields as field}
            <option value={field}>{group.notetype_name} / {field}</option>
          {/each}
        {/each}
      </select>
    </label>
  {/if}

  {#if selected?.parameter_kind === BatchParameterKind.Speed}
    <label>
      <span>{t("settings.speed_step")}</span>
      <input bind:value={form.speedStep} disabled={disabled} max="0.25" min="0.01" step="0.01" type="number" />
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Volume}
    <label>
      <span>{t("settings.volume_step_db")}</span>
      <input bind:value={form.volumeStepDb} disabled={disabled} max="12" min="0.5" step="0.5" type="number" />
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Pause}
    <label>
      <span>{t("settings.pause_aggressiveness")}</span>
      <select bind:value={form.pauseAggressiveness} disabled={disabled}>
        <option value={BatchPauseAggressiveness.Gentle}>{t("settings.pause_aggressiveness.gentle")}</option>
        <option value={BatchPauseAggressiveness.Normal}>{t("settings.pause_aggressiveness.normal")}</option>
        <option value={BatchPauseAggressiveness.Aggressive}>{t("settings.pause_aggressiveness.aggressive")}</option>
      </select>
    </label>
  {/if}
</div>
```

Create `BatchFooter.svelte` with Start, Copy Log, and Cancel/Close buttons wired to callback props. Use plain `<button type="button">` controls and disable Start while running.

Create `BatchApp.svelte` with:

```svelte
<script lang="ts">
  import { onMount } from "svelte";
  import { sendBridgeCommand } from "$lib/bridge.js";
  import { configureI18n, t } from "$lib/i18n.js";
  import { createLogger } from "$lib/logger.js";
  import type { BatchFinishPayload, BatchProgressPayload } from "$lib/types.js";
  import BatchControls from "./BatchControls.svelte";
  import BatchFooter from "./BatchFooter.svelte";
  import { batchCancel, batchClose, batchCopyLog, batchStart, registerBatchCallbacks } from "./bridge.js";
  import { batchStartRequest, initialBatchState, initialFormState, selectedOperation } from "./batch-state.js";

  const state = initialBatchState();
  configureI18n(state.locale, state.direction, state.messages);
  const logger = createLogger("batch", (payload) => {
    sendBridgeCommand(`frontend_log:${JSON.stringify(payload)}`);
  });

  let form = $state(initialFormState(state));
  let running = $state(false);
  let finished = $state(false);
  let status = $state(t("batch.instructions"));
  let processed = $state(0);
  let total = $state(state.note_count);
  let failures = $state(0);
  let logLines = $state<string[]>([]);

  let selected = $derived(selectedOperation(state, form.operation));

  onMount(() => {
    registerBatchCallbacks({
      onProgress: (payload: BatchProgressPayload) => {
        processed = payload.processed;
        total = payload.total;
        failures = payload.failures;
        status = payload.message;
      },
      onLog: (payload) => {
        logLines = [...logLines, payload.line];
      },
      onFinish: (payload: BatchFinishPayload) => {
        running = false;
        finished = true;
        processed = payload.processed;
        total = payload.total;
        failures = payload.failures;
        status = payload.summary;
      },
      onError: (payload) => {
        running = false;
        finished = true;
        status = payload.message;
        logLines = [...logLines, payload.message];
      },
    });
    logger.info("batch UI mounted", { noteCount: state.note_count });
  });

  function start(): void {
    running = true;
    finished = false;
    logLines = [];
    batchStart(batchStartRequest(form));
  }
</script>
```

Complete the markup with a compact root layout, `BatchControls`, a native `<progress>` element with `aria-valuenow`, a read-only log `<pre>`, and `BatchFooter`.

Create `settings_ui/src/batch/main.ts`:

```ts
import { mount } from "svelte";
import BatchApp from "./BatchApp.svelte";

const app = mount(BatchApp, {
  target: document.getElementById("app")!,
});

export default app;
```

- [ ] **Step 4: Run focused app tests**

Run:

```bash
cd settings_ui
npm run test -- batch-state.test.ts batch-bridge.test.ts batch-app.test.ts
```

Expected: PASS.

### Task 6: Replace Qt Batch Dialog With WebView Shell

**Files:**
- Modify: `addon/anki_audio_quick_editor/browser_dialog.py`
- Add or modify: `tests/test_browser_dialog.py`
- Modify: `tests/test_browser_integration.py`

- [ ] **Step 1: Run impact analysis before editing the dialog class and factory**

Run:

```text
gitnexus_impact({repo: "anki-audio-tools", target: "BatchOperationsDialog", file_path: "addon/anki_audio_quick_editor/browser_dialog.py", direction: "upstream", includeTests: true})
gitnexus_impact({repo: "anki-audio-tools", target: "_create_dialog", file_path: "addon/anki_audio_quick_editor/browser_integration.py", direction: "upstream", includeTests: true})
gitnexus_impact({repo: "anki-audio-tools", target: "_run_batch_in_background", file_path: "addon/anki_audio_quick_editor/browser_integration.py", direction: "upstream", includeTests: true})
```

Expected: LOW risk. Direct Browser integration tests should be the main consumers.

- [ ] **Step 2: Write dialog shell tests**

Add `tests/test_browser_dialog.py` with fake webview and Qt classes modeled after `tests/test_settings_shell.py`. Cover:

```python
def test_render_batch_content_embeds_initial_state_and_bundle(monkeypatch, tmp_path) -> None:
    import anki_audio_quick_editor.browser_dialog as browser_dialog

    bundle_dir = tmp_path / "batch"
    bundle_dir.mkdir()
    bundle_js = bundle_dir / "batch_bundle.js"
    bundle_css = bundle_dir / "batch_bundle.css"
    bundle_js.write_text("window.__batchBundleLoaded = true;", encoding="utf-8")
    bundle_css.write_text(".batch-root { color: red; }", encoding="utf-8")
    monkeypatch.setattr(browser_dialog, "_BUNDLE_JS", bundle_js)
    monkeypatch.setattr(browser_dialog, "_BUNDLE_CSS", bundle_css)

    body, head = browser_dialog._render_batch_content({"danger": "</script>"})

    assert "<style>.batch-root { color: red; }</style>" in head
    assert "window.__AQE_BATCH_INITIAL_STATE__ = {\"danger\": \"<\\/script>\"};" in body
    assert "window.addEventListener(\"error\"" in body
    assert "frontend_log:" in body
    assert "window.__batchBundleLoaded = true;" in body
```

Also cover bridge behavior:

```python
def test_batch_dialog_bridge_start_cancel_copy_and_close(monkeypatch, request) -> None:
    dialog_module = _reload_browser_dialog_with_fake_qt(request)
    run_calls = []
    copied = []
    monkeypatch.setattr(dialog_module, "request_from_batch_start_payload", lambda _payload: "request")
    monkeypatch.setattr(dialog_module, "_clipboard_set_text", lambda text: copied.append(text))

    dialog = dialog_module.BatchOperationsDialog(
        browser=object(),
        note_ids=[1, 2],
        groups=(),
        config=AudioProcessingConfig(),
        run_batch_in_background=lambda *args: run_calls.append(args),
    )

    assert dialog._webview.bridge('batch_start:{"operation":"graph","source_field":"Audio","target_field":"Image","parameters":{}}') is True
    assert run_calls[0][2] == [1, 2]
    assert run_calls[0][3] == "request"

    dialog.append_log("line one")
    assert dialog._webview.bridge("batch_copy_log") is True
    assert copied == ["line one"]
    assert dialog._webview.bridge("batch_cancel") is True
    assert dialog.cancel_event.is_set()
    assert dialog._webview.bridge("batch_close") is True
    assert dialog._dialog.rejected is True
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_browser_dialog.py -q
```

Expected: FAIL because the current dialog is still Qt-control based and lacks webview rendering helpers.

- [ ] **Step 4: Implement the webview shell**

In `addon/anki_audio_quick_editor/browser_dialog.py`:

- Keep `BatchOperationsDialog` as the public class.
- Replace `QComboBox`, `QProgressBar`, `QPlainTextEdit`, and button members with:
  - `self._dialog = QDialog(browser)`
  - `self._webview = AnkiWebView(parent=self._dialog)`
  - `self._webview.requiresCol = False`
  - `self._log_lines: list[str] = []`
  - `self._running = False`
  - `self._finished = False`
- Add `_render_batch_content(initial_state: dict[str, Any]) -> tuple[str, str]` using the same escaping and error reporter pattern as settings.
- Set bridge command to `self._handle_bridge_command`.
- Send JS callbacks with helper methods:

```python
def _emit(self, callback: str, payload: dict[str, Any]) -> None:
    self._webview.eval(f"window.{callback}({json.dumps(payload)})")
```

- Implement public methods:

```python
def append_log(self, line: str) -> None:
    self._log_lines.append(line)
    self._emit("onBatchLog", {"line": line})


def update_progress(self, processed: int, total: int, current_audio: str, failures: int) -> None:
    audio = current_audio or self.tr("batch.no_audio")
    message = self.tr(
        "batch.progress",
        {"processed": processed, "total": total, "audio": audio, "failures": failures},
    )
    self._emit(
        "onBatchProgress",
        batch_progress_payload(
            processed=processed,
            total=total,
            current_audio=current_audio,
            failures=failures,
            message=message,
        ),
    )
```

Implement final callbacks:

```python
def finish_with_report(self, report: BatchRunReport) -> None:
    self._running = False
    self._finished = True
    self.append_log(report.summary)
    self._emit("onBatchFinish", batch_finish_payload(report))


def finish_with_error(self, message: str) -> None:
    self._running = False
    self._finished = True
    self.append_log(message)
    self._emit("onBatchError", {"message": message})
```

- Implement bridge dispatch:

```python
def _handle_bridge_command(self, cmd: str) -> bool:
    if cmd.startswith("batch_start:"):
        return self._handle_batch_start(cmd[len("batch_start:"):])
    if cmd == "batch_cancel":
        self._cancel_or_close()
        return True
    if cmd == "batch_close":
        self._dialog.reject()
        return True
    if cmd == "batch_copy_log":
        _clipboard_set_text("\n".join(self._log_lines))
        return True
    if cmd.startswith("frontend_log:"):
        _handle_frontend_log(cmd[len("frontend_log:"):])
        return True
    return False
```

For frontend logs, reuse the settings command behavior by decoding `FrontendLogPayload` and calling `record_frontend_error` for errors, or log non-errors through the package logger.

- [ ] **Step 5: Preserve start validation and runner invocation**

Implement:

```python
def _handle_batch_start(self, payload_str: str) -> bool:
    try:
        raw_payload = json.loads(payload_str)
        request = request_from_batch_start_payload(raw_payload)
    except (json.JSONDecodeError, AssertionError, TypeError) as exc:
        message = self.tr("batch.failed", {"error": "Invalid batch request"})
        self.finish_with_error(message)
        logger.warning("invalid batch start payload: %s", exc)
        return True
    except ValueError as exc:
        self.append_log(str(exc))
        return True

    self._running = True
    self._finished = False
    self._log_lines.clear()
    self._emit(
        "onBatchProgress",
        batch_progress_payload(
            processed=0,
            total=len(self.note_ids),
            current_audio="",
            failures=0,
            message=self.tr("batch.starting", {"operation": operation_label(request.operation, self._messages)}),
        ),
    )
    self._run_batch_in_background(self.browser, self, self.note_ids, request)
    return True
```

- [ ] **Step 6: Run focused Python tests**

Run:

```bash
python3 -m pytest tests/test_browser_dialog.py tests/test_browser_integration.py -q
```

Expected: PASS.

### Task 7: Wire Batch Bundle Build And Release Packaging

**Files:**
- Create: `settings_ui/vite.batch.config.ts`
- Modify: `settings_ui/package.json`
- Modify: `.gitignore`
- Modify: `scripts/release.py`
- Modify: `scripts/release_smoke.py`
- Modify: `tests/test_release.py`
- Modify: `WEBVIEW_AND_TEMPLATES.md`

- [ ] **Step 1: Run impact analysis before editing release/build functions**

Run:

```text
gitnexus_impact({repo: "anki-audio-tools", target: "cmd_build_ui", file_path: "scripts/dev.py", direction: "upstream", includeTests: true})
gitnexus_impact({repo: "anki-audio-tools", target: "_verify_bundle_fresh", file_path: "scripts/release.py", direction: "upstream", includeTests: true})
gitnexus_impact({repo: "anki-audio-tools", target: "smoke_archive", file_path: "scripts/release_smoke.py", direction: "upstream", includeTests: true})
```

Expected: build and release tests are the direct consumers.

- [ ] **Step 2: Add Vite batch config**

Create `settings_ui/vite.batch.config.ts`:

```ts
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  resolve: {
    conditions: ["browser"],
    alias: {
      $lib: "/src/lib",
    },
  },
  build: {
    outDir: "../addon/anki_audio_quick_editor/templates/batch",
    emptyOutDir: false,
    lib: {
      entry: "src/batch/main.ts",
      name: "BatchOperationsUI",
      fileName: "batch_bundle",
      formats: ["iife"],
    },
    rollupOptions: {
      output: {
        entryFileNames: "batch_bundle.js",
        assetFileNames: "batch_bundle.[ext]",
      },
    },
  },
});
```

- [ ] **Step 3: Update package scripts**

In `settings_ui/package.json`, change:

```json
"build": "npm run build:settings && npm run build:editor && npm run build:batch",
"build:batch": "vite build --config vite.batch.config.ts",
```

Add `vite.batch.config.ts` to ESLint ignored config files.

- [ ] **Step 4: Update ignored generated files**

In `.gitignore`, add:

```gitignore
/addon/anki_audio_quick_editor/templates/batch/batch_bundle.*
```

- [ ] **Step 5: Update release requirements**

In `scripts/release.py`, add:

```python
"templates/batch/batch_bundle.js",
"templates/batch/batch_bundle.css",
```

to `BASE_REQUIRED_ARCHIVE_FILES`, and add a third bundle spec to `_verify_bundle_fresh()` with sources:

```python
[
    src_dir / "batch",
    src_dir / "lib",
]
```

and bundles:

```python
[
    ADDON_DIR / "templates" / "batch" / "batch_bundle.js",
    ADDON_DIR / "templates" / "batch" / "batch_bundle.css",
]
```

In `scripts/release_smoke.py`, require:

```python
_require_nonempty(package_dir, "templates/batch/batch_bundle.js")
```

CSS is already validated by release archive requirements; add a smoke assertion for CSS too if the existing smoke style requires both files for settings/editor.

- [ ] **Step 6: Update release tests**

In `tests/test_release.py`, update `test_release_validates_required_frontend_bundles` so it removes `templates/batch/batch_bundle.css` and asserts that path appears in validation output.

- [ ] **Step 7: Update WebView docs**

In `WEBVIEW_AND_TEMPLATES.md`, update the frontend bundles section to list:

```markdown
- Browser batch operations source: `settings_ui/src/batch/` and shared `settings_ui/src/lib/`
- output: `addon/anki_audio_quick_editor/templates/batch/batch_bundle.{js,css}`
```

Remove or replace the sentence that says no Browser batch-visualization template is bundled.

- [ ] **Step 8: Run build/release focused checks**

Run:

```bash
python3 scripts/dev.py build
python3 -m pytest tests/test_release.py -q
```

Expected: PASS. The build writes ignored bundle files under `addon/anki_audio_quick_editor/templates/batch/`.

### Task 8: Full Verification, Coverage Parity, And Change Review

**Files:**
- All changed implementation, tests, docs, and generated contract files.

- [ ] **Step 1: Run frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: PASS. This command rebuilds bundles, runs ESLint autofix, then runs frontend validation. Review any formatter or lint rewrites before continuing.
This must include the frontend architecture tests proving that settings, editor, and batch remain sibling frontends with no direct imports or window-contract coupling.

- [ ] **Step 2: Run Python unit and architecture tests**

Run:

```bash
python3 scripts/dev.py test
```

Expected: PASS.

- [ ] **Step 3: Run Python coverage gate explicitly**

Run:

```bash
python3 scripts/dev.py coverage
```

Expected: PASS at the existing 80% fail-under threshold. If coverage drops, add or strengthen tests for the changed Python/Svelte boundary; do not lower `fail_under`, add blanket coverage exclusions, or remove test targets.

- [ ] **Step 4: Run Anki API compatibility**

Run:

```bash
python3 scripts/dev.py test-anki-api
```

Expected: PASS. If this fails because the Anki API mock surface is missing `AnkiWebView` or Qt exports, update `tests/conftest.py` and the contract mock tests explicitly.

- [ ] **Step 5: Run full QC**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS. This includes config/schema, contracts, architecture, lint, typecheck, file-lines, security, deadcode, deps, complexity, Qodana, Anki API, unit tests, coverage, and frontend validation.

- [ ] **Step 6: Review e2e changes for parity before running them**

Run:

```bash
git diff -- e2e/
```

Expected: e2e diffs, if any, only update selectors, waits, or WebView/Svelte rendering assumptions. There must be no deleted e2e scenarios, skipped tests, xfails, or broad test relaxations. If an e2e test is structurally coupled to Qt widgets, adjust it to target stable Svelte-visible text or `data-testid` attributes while preserving the same user workflow.

- [ ] **Step 7: Run e2e**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS. This is required by `AGENTS.md` before calling the feature complete, and it must pass with the same e2e coverage intent as before the migration.

- [ ] **Step 8: Run GitNexus changed-flow review before commit**

Run:

```text
gitnexus_detect_changes({repo: "anki-audio-tools", scope: "all"})
```

Expected: affected symbols are limited to Browser batch dialog shell/state, batch frontend, contracts, build/release plumbing, and tests/docs. Investigate unexpected editor audio-processing or settings-save flows before committing.

- [ ] **Step 9: Commit intentionally**

Review:

```bash
git status --short
git diff --stat
```

Stage only intended files. Do not stage runtime logs such as `addon/anki_audio_quick_editor/anki_audio_quick_editor_events.jsonl.1`.

Commit message:

```bash
git commit -m "Migrate batch operations dialog to Svelte"
```

Expected: commit contains source, tests, docs, schema changes, and generated contract files only if the repository normally tracks them. Ignored generated bundles stay uncommitted.

---

## Acceptance Criteria

- Browser **Run Audio Batch Operation...** opens a Svelte-backed webview dialog.
- Starting a graph operation requires a target field and appends generated visualization media exactly as before.
- Starting transform operations updates the source field exactly as before and uses selected speed, volume, or pause parameters.
- Progress, cancellation, log copying, final summary, and worker error behavior match the old Qt dialog.
- Editor and batch continue to share Python operation parameter behavior through `audio_operation_params.py`.
- Editor and batch share frontend parameter clamp/format helpers through `$lib/audio-operation-parameters.ts`; editor field-specific state remains editor-only.
- Frontend architecture tests enforce that settings, editor, and batch do not import each other or share frontend-specific window globals; shared code flows only through `$lib` and generated contracts.
- Existing unit, frontend, coverage, and e2e gates remain at least as strict as before the migration. E2E changes are selector/rendering adjustments only, not scenario removals.
- Release archive validation requires the batch bundle.
- `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e` pass.
