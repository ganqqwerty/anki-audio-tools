# Audio Batch Operation Parameter Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show only one Browser entry point for **Run Audio Batch Operation...** and make every existing batch transform operation use the same user-adjustable parameter defaults and overrides as its matching Editor split-button operation.

**Architecture:** Keep Browser/UI wiring, batch execution, and editor bridge command decoding separated. Add a small import-safe shared parameter module that owns validation, clamping, and effective `AudioProcessingConfig` construction; then have `editor_actions.py` and `batch_operations.py` depend on that module instead of depending on each other. The Browser dialog becomes an adapter that presents Qt controls and serializes selected values into `BatchRunRequest`.


---

## Requirements

### Functional Requirements

- The Browser must expose **Run Audio Batch Operation...** through exactly one add-on-created entry point.
- The preferred retained entry point is the Browser **Cards** menu action registered from `browser_menus_did_init`.
- The explicit Browser context-menu action registered from `browser_will_show_context_menu` must be removed unless a later product decision explicitly asks for context-menu-only access.
- Existing batch operations remain:
  - `graph`
  - `remove_pauses`
  - `slower`
  - `faster`
  - `volume_down`
  - `volume_up`
- This change does not add new batch operations such as Editor-only trim or denoise. That is a separate scope because trim changes the operation registry and denoise uses a separate special-transform renderer path.
- Batch `remove_pauses` must expose the same parameter as the Editor: `pauseAggressiveness` with values `gentle`, `normal`, `aggressive`.
- Batch `slower` and `faster` must expose the same parameter as the Editor: `speedStep`, clamped to `0.01..0.25`.
- Batch `volume_down` and `volume_up` must expose the same parameter as the Editor: `volumeStepDb`, clamped to `0.5..12.0`.
- Batch `graph` has no Editor split-button parameter and should not show transform parameter controls.
- Batch dialog defaults must come from the same settings values used by the Editor:
  - `pause_aggressiveness`
  - `speed_step`
  - `volume_step_db`
- Local batch parameter choices must not mutate persisted settings.
- The batch report start line should include selected parameter values for transform operations so logs are auditable.

### Non-Functional Requirements

- `batch_operations.py` and `batch_visualization.py` must remain free of `aqe:` editor bridge strings.
- `browser_integration.py` must not import `editor_actions.py`.
- `editor_actions.py` must remain import-safe and Anki-free.
- `audio_operations.py` should remain the operation registry and pure state-transition layer, not a Qt/editor payload parser.
- New shared parameter code must be import-safe and must depend only on `audio_state.py`.
- The legacy `batch_visualization.process_note_visualization()` wrapper must continue to work without passing explicit parameters.
- Existing plain-string editor commands must keep working.
- Architecture tests are a hard requirement. The implementation is not acceptable until the affected architecture tests, the full `tests/test_architecture` suite, and the import-linter architecture gate pass.
- E2E tests are a hard requirement. The feature is not complete until `python3 scripts/dev.py test-e2e` passes.
- A focused unit-test pass alone is insufficient for completion, even if the changed behavior is covered by unit tests.

### Architectural Decisions

- Add a new module: `addon/anki_audio_quick_editor/audio_operation_params.py`.
- This module owns:
  - `AudioOperationParameters`
  - numeric clamp constants
  - raw value normalization helpers
  - `effective_config_for_operation(operation, config, parameters)`
  - pause aggressiveness mapping to effective pause thresholds
- Move the current editor-only pause aggressiveness config mapping from `editor_actions.py` into `audio_operation_params.py`.
- Keep editor bridge payload decoding in `editor_actions.py`; bridge payloads are still an editor concern.
- Store batch selections as `BatchRunRequest.parameters: AudioOperationParameters`.
- Pass `AudioProcessingConfig` into `BatchOperationsDialog` at construction time so Qt defaults match persisted settings before the user starts a run.
- Update architecture contracts to explicitly classify `audio_operation_params` as import-safe core and to allow the affected modules to import it.

### Dependency Impact

- `audio_operation_params.py`
  - Layer: `IMPORT_SAFE_CORE`
  - Allowed add-on dependencies: `audio_state`
- `editor_actions.py`
  - Add dependency: `audio_operation_params`
  - Keep dependency: `audio_operations`, `audio_state`
- `batch_operations.py`
  - Add dependency: `audio_operation_params`
  - Keep dependency: `audio_operations`, `audio_processor`, `audio_state`, diagnostics/media/prosody/sound helpers
- `browser_dialog.py`
  - Add dependency: `audio_operation_params`
  - Keep dependency: `audio_operations`, `batch_operations`, `browser_report`, `i18n`
- `browser_integration.py`
  - No new dependency required; it already imports `audio_state` and can pass `AudioProcessingConfig` to the dialog.


- `register_browser_hooks` upstream impact: LOW risk, one direct caller: `_setup_browser_integration`.
- `BatchOperationsDialog` upstream impact: LOW risk, direct import from `browser_integration.py`.
- `process_note_batch_operation` upstream impact: LOW risk, direct callers are `_process_note` and `process_note_visualization`.
- `apply_audio_operation` upstream impact: HIGH risk because editor and batch flows both depend on it. Avoid changing its public behavior unless a focused impact check is rerun and the change is necessary.

---

## File Structure

- Create `addon/anki_audio_quick_editor/audio_operation_params.py`: shared import-safe parameter model and config helpers.
- Modify `addon/anki_audio_quick_editor/editor_actions.py`: delegate override clamping and effective config construction to the shared helper.
- Modify `addon/anki_audio_quick_editor/batch_operations.py`: add parameters to `BatchRunRequest` and apply an effective config before transform rendering.
- Modify `addon/anki_audio_quick_editor/browser_dialog.py`: add operation-specific Qt controls and serialize selected values into `BatchRunRequest`.
- Modify `addon/anki_audio_quick_editor/browser_integration.py`: stop registering the context-menu action, pass config into `BatchOperationsDialog`, include parameters in batch start logs.
- Modify `tests/test_architecture/contract_audio.py`: classify the new helper and update allowed dependencies.
- Modify `tests/test_architecture/contract_editor.py`: allow `editor_actions` to import the new helper.
- Modify `tests/test_architecture/contract_ui.py`: allow `browser_dialog` to import the new helper.
- Modify `tests/test_architecture/test_rule13_batch_operation_boundaries.py`: preserve the no-`aqe:` batch-core rule and ensure parameter helper is shared.
- Modify `tests/test_architecture/test_rule19_shared_operation_contracts.py`: update contract expectations.
- Modify `tests/test_editor_actions.py`: prove editor behavior is unchanged after moving shared parameter logic.
- Modify `tests/test_batch_visualization.py`: prove batch transform parameters affect speed/volume/pause config.
- Modify `tests/test_browser_integration.py`: prove only the menu hook is registered and dialog receives config defaults.
- Add `tests/test_audio_operation_params.py`: focused import-safe tests for clamp/default/effective config logic.

---

## Implementation Plan

### Task 1: Remove The Duplicate Browser Entry Point

**Files:**
- Modify: `addon/anki_audio_quick_editor/browser_integration.py`
- Modify: `tests/test_browser_integration.py`
- Modify: `tests/test_architecture/test_rule19_shared_operation_contracts.py` only if text assertions need adjustment

- [ ] **Step 1: Run impact analysis before editing Browser hook symbols**

Run:

```text
```

Expected: LOW risk. Direct test consumers should be in `tests/test_browser_integration.py`.

- [ ] **Step 2: Write the failing hook registration test**

Update `tests/test_browser_integration.py::test_register_browser_hooks`:

```python
def test_register_browser_hooks() -> None:
    hooks = SimpleNamespace(browser_menus_did_init=MagicMock(), browser_will_show_context_menu=MagicMock())

    register_browser_hooks(hooks)

    hooks.browser_menus_did_init.append.assert_called_once()
    hooks.browser_will_show_context_menu.append.assert_not_called()
```

Remove direct imports and tests for `_on_browser_will_show_context_menu` if any are added later.

- [ ] **Step 3: Run the focused failing test**

Run:

```bash
python3 -m pytest tests/test_browser_integration.py::test_register_browser_hooks -q
```

Expected: FAIL because `register_browser_hooks()` still appends the context-menu hook.

- [ ] **Step 4: Remove the explicit context-menu registration**

In `addon/anki_audio_quick_editor/browser_integration.py`, change:

```python
def register_browser_hooks(gui_hooks: Any) -> None:
    """Register Browser menu hooks."""
    gui_hooks.browser_menus_did_init.append(
        _browser_hook_boundary("browser_menus_did_init", _on_browser_menus_did_init)
    )
```

Delete `_on_browser_will_show_context_menu()` if no tests or code import it.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_browser_integration.py tests/test_anki_api_contract_mocks.py -q
```

Expected: PASS. `test_anki_api_contract_mocks.py` may still assert Anki hook signatures globally; do not change it unless it asserts add-on registration behavior directly.

### Task 2: Add Shared Import-Safe Operation Parameters

**Files:**
- Create: `addon/anki_audio_quick_editor/audio_operation_params.py`
- Modify: `tests/test_architecture/contract_audio.py`
- Modify: `tests/test_architecture/contract_editor.py`
- Modify: `tests/test_architecture/contract_ui.py`
- Add: `tests/test_audio_operation_params.py`

- [ ] **Step 1: Write focused parameter tests**

Create `tests/test_audio_operation_params.py`:

```python
from anki_audio_quick_editor.audio_operation_params import (
    AudioOperationParameters,
    effective_config_for_operation,
    parameters_from_raw,
)
from anki_audio_quick_editor.audio_operations import OP_FASTER, OP_GRAPH, OP_REMOVE_PAUSES, OP_VOLUME_UP
from anki_audio_quick_editor.audio_state import AudioProcessingConfig


def test_parameters_from_raw_clamps_editor_matching_ranges() -> None:
    params = parameters_from_raw(
        trim_step_ms=10,
        volume_step_db=99,
        speed_step=0.001,
        pause_aggressiveness="invalid",
    )

    assert params.trim_step_ms == 50
    assert params.volume_step_db == 12.0
    assert params.speed_step == 0.01
    assert params.pause_aggressiveness is None


def test_effective_config_uses_volume_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(volume_step_db=3.0)
    params = AudioOperationParameters(volume_step_db=6.0)

    effective = effective_config_for_operation(OP_VOLUME_UP, config, params)

    assert effective.volume_step_db == 6.0
    assert config.volume_step_db == 3.0


def test_effective_config_uses_speed_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(speed_step=0.05)
    params = AudioOperationParameters(speed_step=0.1)

    effective = effective_config_for_operation(OP_FASTER, config, params)

    assert effective.speed_step == 0.1
    assert config.speed_step == 0.05


def test_effective_config_uses_pause_aggressiveness_override() -> None:
    config = AudioProcessingConfig(
        internal_pause_silence_threshold_db=-45,
        internal_pause_threshold_ms=300,
        internal_pause_target_gap_ms=100,
        pause_aggressiveness="normal",
    )
    params = AudioOperationParameters(pause_aggressiveness="aggressive")

    effective = effective_config_for_operation(OP_REMOVE_PAUSES, config, params)

    assert effective.pause_aggressiveness == "aggressive"
    assert effective.internal_pause_silence_threshold_db == -50
    assert effective.internal_pause_threshold_ms == 180
    assert effective.internal_pause_target_gap_ms == 60


def test_effective_config_ignores_parameters_for_graph() -> None:
    config = AudioProcessingConfig(speed_step=0.05, volume_step_db=3.0)
    params = AudioOperationParameters(speed_step=0.1, volume_step_db=6.0, pause_aggressiveness="aggressive")

    assert effective_config_for_operation(OP_GRAPH, config, params) == config
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_audio_operation_params.py -q
```

Expected: FAIL because `audio_operation_params.py` does not exist.

- [ ] **Step 3: Implement the shared helper**

Create `addon/anki_audio_quick_editor/audio_operation_params.py`:

```python
"""Shared import-safe parameter handling for editor and batch audio operations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .audio_state import AudioProcessingConfig

MIN_TRIM_OVERRIDE_MS = 50
MAX_TRIM_OVERRIDE_MS = 10_000
MIN_VOLUME_STEP_DB = 0.5
MAX_VOLUME_STEP_DB = 12.0
MIN_SPEED_STEP = 0.01
MAX_SPEED_STEP = 0.25
PAUSE_AGGRESSIVENESS = frozenset({"gentle", "normal", "aggressive"})


@dataclass(frozen=True)
class AudioOperationParameters:
    """Validated optional parameters shared by editor and batch operations."""

    trim_step_ms: int | None = None
    volume_step_db: float | None = None
    speed_step: float | None = None
    pause_aggressiveness: str | None = None


def parameters_from_raw(
    *,
    trim_step_ms: Any = None,
    volume_step_db: Any = None,
    speed_step: Any = None,
    pause_aggressiveness: Any = None,
) -> AudioOperationParameters:
    """Normalize raw UI values into clamped operation parameters."""
    return AudioOperationParameters(
        trim_step_ms=_clamp_trim_step_ms(_int_or_none(trim_step_ms)),
        volume_step_db=_clamp_float(
            _float_or_none(volume_step_db),
            MIN_VOLUME_STEP_DB,
            MAX_VOLUME_STEP_DB,
        ),
        speed_step=_clamp_float(
            _float_or_none(speed_step),
            MIN_SPEED_STEP,
            MAX_SPEED_STEP,
        ),
        pause_aggressiveness=_pause_aggressiveness_or_none(pause_aggressiveness),
    )


def effective_config_for_operation(
    operation: str,
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    """Return the render config after applying operation-local parameters."""
    if operation == "graph":
        return config
    effective = replace(
        config,
        volume_step_db=parameters.volume_step_db or config.volume_step_db,
        speed_step=parameters.speed_step or config.speed_step,
    )
    if operation == "remove_pauses":
        return config_for_pause_aggressiveness(
            effective,
            parameters.pause_aggressiveness or config.pause_aggressiveness,
        )
    return effective


def config_for_pause_aggressiveness(
    config: AudioProcessingConfig,
    aggressiveness: str,
) -> AudioProcessingConfig:
    """Return pause detection thresholds for one supported aggressiveness level."""
    if aggressiveness == "gentle":
        return replace(
            config,
            internal_pause_silence_threshold_db=-42,
            internal_pause_threshold_ms=450,
            internal_pause_target_gap_ms=180,
            pause_aggressiveness=aggressiveness,
        )
    if aggressiveness == "aggressive":
        return replace(
            config,
            internal_pause_silence_threshold_db=-50,
            internal_pause_threshold_ms=180,
            internal_pause_target_gap_ms=60,
            pause_aggressiveness=aggressiveness,
        )
    return replace(config, pause_aggressiveness="normal")


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _clamp_trim_step_ms(value: int | None) -> int | None:
    if value is None:
        return None
    return max(MIN_TRIM_OVERRIDE_MS, min(MAX_TRIM_OVERRIDE_MS, value))


def _clamp_float(value: float | None, minimum: float, maximum: float) -> float | None:
    if value is None:
        return None
    return max(minimum, min(maximum, value))


def _pause_aggressiveness_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value if value in PAUSE_AGGRESSIVENESS else None
```

- [ ] **Step 4: Update architecture contracts**

In `tests/test_architecture/contract_audio.py`, add:

```python
"audio_operation_params": contract(
    "audio_operation_params",
    layer=Layer.IMPORT_SAFE_CORE,
    allowed_addon_deps=("audio_state",),
),
```

Add `"audio_operation_params"` to:

```python
"batch_operations": contract(... allowed_addon_deps=(..., "audio_operation_params", ...))
```

In `tests/test_architecture/contract_editor.py`, update:

```python
"editor_actions": contract(
    "editor_actions",
    layer=Layer.IMPORT_SAFE_CORE,
    allowed_addon_deps=("audio_operation_params", "audio_operations", "audio_state"),
),
```

In `tests/test_architecture/contract_ui.py`, update:

```python
"browser_dialog": contract(
    "browser_dialog",
    layer=Layer.UI_ADAPTER,
    allowed_addon_deps=("audio_operation_params", "audio_operations", "batch_operations", "browser_report", "i18n"),
    ...
),
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_audio_operation_params.py tests/test_architecture/test_rule5_all_modules_classified.py tests/test_architecture/test_rule17_contract_driven_addon_dependency_policy.py -q
```

Expected: PASS.

### Task 3: Refactor Editor Parameter Logic To The Shared Helper

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `tests/test_editor_actions.py`

- [ ] **Step 1: Run impact analysis before editing editor action symbols**

Run:

```text
```

Expected: editor processing tests and bridge tests are direct consumers.

- [ ] **Step 2: Preserve behavior with existing tests**

Run:

```bash
python3 -m pytest tests/test_editor_actions.py tests/test_editor_bridge_commands.py -q
```

Expected before edits: PASS.

- [ ] **Step 3: Replace duplicate validation with shared helper**

In `editor_actions.py`:

- Import:

```python
from .audio_operation_params import (
    AudioOperationParameters,
    effective_config_for_operation,
    parameters_from_raw,
)
```

- Change `EditorCommandOverrides` to either subclass no class and mirror the same fields, or replace it with an alias-compatible dataclass shape. The lowest-risk path is to keep `EditorCommandOverrides` as the public editor type but build it from `parameters_from_raw()`.
- Remove editor-local constants and helpers that now live in `audio_operation_params.py`.
- Change `_overrides_from_raw()` to:

```python
def _overrides_from_raw(raw: Any) -> EditorCommandOverrides:
    if not isinstance(raw, dict):
        return EditorCommandOverrides()
    params = parameters_from_raw(
        trim_step_ms=raw.get("trimStepMs"),
        volume_step_db=raw.get("volumeStepDb"),
        speed_step=raw.get("speedStep"),
        pause_aggressiveness=raw.get("pauseAggressiveness"),
    )
    return EditorCommandOverrides(
        trim_step_ms=params.trim_step_ms,
        volume_step_db=params.volume_step_db,
        speed_step=params.speed_step,
        pause_aggressiveness=params.pause_aggressiveness,
    )
```

- Change `processing_config_for_command()` to:

```python
def processing_config_for_command(
    command: str | EditorCommandPayload,
    config: AudioProcessingConfig,
) -> AudioProcessingConfig:
    payload = decode_editor_command_payload(command)
    operation = operation_for_command(payload.command)
    if operation is None:
        return config
    return effective_config_for_operation(
        operation,
        config,
        AudioOperationParameters(
            volume_step_db=payload.overrides.volume_step_db,
            speed_step=payload.overrides.speed_step,
            pause_aggressiveness=payload.overrides.pause_aggressiveness,
        ),
    )
```

Keep trim handling in `apply_processing_command()` because trim-left/right are editor commands, not shared `audio_operations` transforms.

- [ ] **Step 4: Run editor and architecture tests**

Run:

```bash
python3 -m pytest tests/test_editor_actions.py tests/test_editor_bridge_commands.py tests/test_architecture/test_rule13_batch_operation_boundaries.py tests/test_architecture/test_rule19_shared_operation_contracts.py -q
```

Expected: PASS, with no `aqe:` strings introduced into batch core modules.

### Task 4: Add Batch Request Parameters And Effective Config Use

**Files:**
- Modify: `addon/anki_audio_quick_editor/batch_operations.py`
- Modify: `addon/anki_audio_quick_editor/batch_visualization.py` only if constructor call style needs explicit compatibility
- Modify: `tests/test_batch_visualization.py`

- [ ] **Step 1: Run impact analysis before editing batch request/executor symbols**

Run:

```text
```

Expected: LOW to MEDIUM risk. Direct consumers are browser integration, batch visualization wrapper, and batch tests.

- [ ] **Step 2: Write failing batch parameter tests**

In `tests/test_batch_visualization.py`, add tests:

```python
def test_process_note_batch_operation_uses_speed_parameter_for_transform(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    speeds: list[float] = []

    def fake_render_audio(source_path, state, _config, output_path=None, on_command=None, artifact_root=None):
        del source_path, _config, on_command, artifact_root
        assert output_path is not None
        speeds.append(state.speed)
        output_path.write_bytes(b"rendered")

    monkeypatch.setattr("anki_audio_quick_editor.batch_operations.render_audio", fake_render_audio)

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_FASTER,
            source_field="Audio",
            parameters=AudioOperationParameters(speed_step=0.2),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(speed_step=0.05),
        media_writer=lambda name, data: name,
    )

    assert result.written
    assert speeds == [1.2]
```

Add a pause config test:

```python
def test_process_note_batch_operation_uses_pause_aggressiveness_parameter(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    configs: list[AudioProcessingConfig] = []

    def fake_render_audio(source_path, state, config, output_path=None, on_command=None, artifact_root=None):
        del source_path, state, on_command, artifact_root
        assert output_path is not None
        configs.append(config)
        output_path.write_bytes(b"rendered")

    monkeypatch.setattr("anki_audio_quick_editor.batch_operations.render_audio", fake_render_audio)

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_REMOVE_PAUSES,
            source_field="Audio",
            parameters=AudioOperationParameters(pause_aggressiveness="gentle"),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(pause_aggressiveness="normal"),
        media_writer=lambda name, data: name,
    )

    assert result.written
    assert configs[0].pause_aggressiveness == "gentle"
    assert configs[0].internal_pause_threshold_ms == 450
```

Import `AudioOperationParameters` and `OP_REMOVE_PAUSES`.

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_batch_visualization.py::test_process_note_batch_operation_uses_speed_parameter_for_transform tests/test_batch_visualization.py::test_process_note_batch_operation_uses_pause_aggressiveness_parameter -q
```

Expected: FAIL because `BatchRunRequest` has no `parameters` field.

- [ ] **Step 4: Add parameters to `BatchRunRequest`**

In `batch_operations.py`:

```python
from dataclasses import dataclass, field

from .audio_operation_params import AudioOperationParameters, effective_config_for_operation
```

Change `BatchRunRequest`:

```python
@dataclass(frozen=True)
class BatchRunRequest:
    """One validated batch operation request selected by the Browser UI."""

    operation: str
    source_field: str
    target_field: str | None = None
    parameters: AudioOperationParameters = field(default_factory=AudioOperationParameters)
```

In `_process_transform_operation()`, replace:

```python
updated_state = apply_audio_operation(
    request.operation,
    AudioEditState(source_file=audio_filename),
    config,
)
```

with:

```python
effective_config = effective_config_for_operation(request.operation, config, request.parameters)
updated_state = apply_audio_operation(
    request.operation,
    AudioEditState(source_file=audio_filename),
    effective_config,
)
```

Pass `effective_config` to `render_audio()` instead of `config`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_batch_visualization.py tests/test_architecture/test_rule13_batch_operation_boundaries.py tests/test_architecture/test_rule19_shared_operation_contracts.py -q
```

Expected: PASS.

### Task 5: Add Batch Dialog Parameter Controls

**Files:**
- Modify: `addon/anki_audio_quick_editor/browser_dialog.py`
- Modify: `addon/anki_audio_quick_editor/browser_integration.py`
- Modify: `tests/test_browser_integration.py`

- [ ] **Step 1: Run impact analysis before editing dialog symbols**

Run:

```text
```

Expected: LOW risk. Browser integration is the only production constructor.

- [ ] **Step 2: Write failing config pass-through test**

In `tests/test_browser_integration.py::test_open_batch_dialog_builds_field_groups_from_selected_notes`, update the fake browser `mw` to include an addon manager:

```python
addon_manager = SimpleNamespace(
    addonFromModule=lambda _module: "anki_audio_quick_editor",
    getConfig=lambda _addon_id: {
        "speed_step": 0.1,
        "volume_step_db": 6.0,
        "pause_aggressiveness": "aggressive",
    },
)
browser = SimpleNamespace(
    selected_notes=lambda: [2, 1, 2],
    mw=SimpleNamespace(col=col, addonManager=addon_manager),
)
```

Update `create_dialog` to receive the config:

```python
def create_dialog(_browser: object, note_ids: list[int], groups: tuple[object, ...], config: AudioProcessingConfig) -> Dialog:
    dialog_calls.append((note_ids, groups, config))
    return Dialog()
```

Assert:

```python
assert dialog_calls[0][2].speed_step == 0.1
assert dialog_calls[0][2].volume_step_db == 6.0
assert dialog_calls[0][2].pause_aggressiveness == "aggressive"
```

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_browser_integration.py::test_open_batch_dialog_builds_field_groups_from_selected_notes -q
```

Expected: FAIL because `_create_dialog()` does not accept config.

- [ ] **Step 4: Pass config to the dialog**

In `_open_batch_dialog()`:

```python
config = AudioProcessingConfig.from_config(
    browser.mw.addonManager.getConfig(browser.mw.addonManager.addonFromModule(__name__)) or {}
)
dialog = _create_dialog(browser, note_ids, groups, config)
```

Change:

```python
def _create_dialog(
    browser: Any,
    note_ids: list[int],
    groups: tuple[FieldGroup, ...],
    config: AudioProcessingConfig,
) -> Any:
    return BatchOperationsDialog(browser, note_ids, groups, config, _run_batch_in_background)
```

Change `BatchOperationsDialog.__init__()` signature to accept `config: AudioProcessingConfig`.

- [ ] **Step 5: Add Qt parameter controls**

In `browser_dialog.py`, import:

```python
from .audio_operation_params import AudioOperationParameters, parameters_from_raw
from .audio_state import AudioProcessingConfig
```

Add `QDoubleSpinBox` to the local `aqt.qt` import list in `BatchOperationsDialog.__init__()`:

```python
from aqt.qt import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
)
```

Add widgets in `__init__()`:

```python
self._config = config
self._speed_label = QLabel("Speed step")
self._speed_spin = QDoubleSpinBox()
self._volume_label = QLabel("Volume step (dB)")
self._volume_spin = QDoubleSpinBox()
self._pause_label = QLabel("Shorten pauses level")
self._pause_combo = QComboBox()
```

Configure controls:

```python
self._speed_spin.setRange(0.01, 0.25)
self._speed_spin.setSingleStep(0.01)
self._speed_spin.setDecimals(2)
self._speed_spin.setValue(config.speed_step)
self._volume_spin.setRange(0.5, 12.0)
self._volume_spin.setSingleStep(0.5)
self._volume_spin.setDecimals(1)
self._volume_spin.setValue(config.volume_step_db)
for value in ("gentle", "normal", "aggressive"):
    self._pause_combo.addItem(value.capitalize(), value)
self._pause_combo.setCurrentIndex(max(0, self._pause_combo.findData(config.pause_aggressiveness)))
```

Add a parameter row below `_field_row(groups)`:

```python
layout.addLayout(self._parameter_row())
```

Add:

```python
def _parameter_row(self) -> Any:
    from aqt.qt import QHBoxLayout

    row = QHBoxLayout()
    row.addWidget(self._speed_label)
    row.addWidget(self._speed_spin)
    row.addWidget(self._volume_label)
    row.addWidget(self._volume_spin)
    row.addWidget(self._pause_label)
    row.addWidget(self._pause_combo)
    return row
```

Add:

```python
def _selected_parameters(self) -> AudioOperationParameters:
    return parameters_from_raw(
        speed_step=float(self._speed_spin.value()),
        volume_step_db=float(self._volume_spin.value()),
        pause_aggressiveness=self._pause_combo.currentData(),
    )
```

In `_start()`, pass:

```python
parameters=self._selected_parameters(),
```

to `BatchRunRequest`.

After setting `self._running = True`, call:

```python
self._sync_target_visibility()
```

so operation-specific parameter controls are disabled during the run.

In `_sync_target_visibility()`, show controls by operation:

```python
operation = str(self._operation_combo.currentData() or OP_GRAPH)
show_speed = operation in {"slower", "faster"}
show_volume = operation in {"volume_down", "volume_up"}
show_pause = operation == "remove_pauses"
self._speed_label.setVisible(show_speed)
self._speed_spin.setVisible(show_speed)
self._volume_label.setVisible(show_volume)
self._volume_spin.setVisible(show_volume)
self._pause_label.setVisible(show_pause)
self._pause_combo.setVisible(show_pause)
self._speed_spin.setEnabled(show_speed and not self._running)
self._volume_spin.setEnabled(show_volume and not self._running)
self._pause_combo.setEnabled(show_pause and not self._running)
```

- [ ] **Step 6: Use localized labels if available**

Prefer adding batch-specific locale keys only if existing settings labels are not acceptable. The first implementation can use existing message keys already loaded into `_messages`:

```python
self.tr("settings.speed_step")
self.tr("settings.volume_step_db")
self.tr("settings.pause_aggressiveness")
```

If a locale is missing any key, `format_message()` returns the key. Add missing keys to all locale JSON files only when tests expose missing display text.

- [ ] **Step 7: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_browser_integration.py tests/test_batch_visualization.py -q
```

Expected: PASS.

### Task 6: Include Parameters In Batch Logging

**Files:**
- Modify: `addon/anki_audio_quick_editor/browser_integration.py`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: other locale JSON files only if existing tests require all catalogs to have the same key set
- Modify: `tests/test_browser_integration.py`

- [ ] **Step 1: Write failing report-log test**

Add or update a `_run_batch()` test to assert the first log line includes parameter details for transforms:

```python
def test_run_batch_logs_transform_parameters(monkeypatch, tmp_path: Path) -> None:
    col = _FakeCol()
    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_integration._process_note",
        lambda *_args, **_kwargs: BatchNoteResult(
            note_id=1,
            status="skipped",
            message="source field 'Audio' has no supported sound reference",
            audio_filename=None,
        ),
    )
    logs: list[str] = []

    _run_batch(
        col,
        [1],
        BatchRunRequest(
            operation=OP_FASTER,
            source_field="Audio",
            parameters=AudioOperationParameters(speed_step=0.1),
        ),
        tmp_path,
        AudioProcessingConfig(),
        threading.Event(),
        logs.append,
        lambda *_args: None,
    )

    assert "parameters=" in logs[0]
    assert "speed_step=0.1" in logs[0]
```

- [ ] **Step 2: Run test and verify RED**

Run:

```bash
python3 -m pytest tests/test_browser_integration.py::test_run_batch_logs_transform_parameters -q
```

Expected: FAIL because the log line does not include parameters.

- [ ] **Step 3: Implement compact parameter formatting**

Add to `browser_integration.py`:

```python
def _format_parameters(request: BatchRunRequest) -> str:
    params = request.parameters
    values: list[str] = []
    if request.operation in {"slower", "faster"} and params.speed_step is not None:
        values.append(f"speed_step={params.speed_step}")
    if request.operation in {"volume_down", "volume_up"} and params.volume_step_db is not None:
        values.append(f"volume_step_db={params.volume_step_db}")
    if request.operation == "remove_pauses" and params.pause_aggressiveness is not None:
        values.append(f"pause_aggressiveness={params.pause_aggressiveness}")
    return ", ".join(values) if values else "defaults"
```

Extend the existing `batch.log.starting` values with:

```python
"parameters": _format_parameters(request),
```

Update `addon/anki_audio_quick_editor/locales/en.json`:

```json
"batch.log.starting": "Starting batch: {total} notes, operation={operation}, source={source}, target={target}, parameters={parameters}."
```

Apply the same format argument to other locale strings without changing their existing prose more than necessary:

```json
"batch.log.starting": "... parameters={parameters}."
```

- [ ] **Step 4: Run i18n and browser tests**

Run:

```bash
python3 -m pytest tests/test_browser_integration.py tests/test_i18n.py -q
```

Expected: PASS.

### Task 7: Preserve Architecture Rules And Shared Contract Tests

**Files:**
- Modify: `tests/test_architecture/test_rule13_batch_operation_boundaries.py`
- Modify: `tests/test_architecture/test_rule19_shared_operation_contracts.py`

- [ ] **Step 1: Add architecture assertions for the new helper**

In `tests/test_architecture/test_rule13_batch_operation_boundaries.py`, add:

```python
def test_batch_and_editor_share_operation_parameter_helper() -> None:
    editor_text = (ADDON_DIR / "editor_actions.py").read_text(encoding="utf-8")
    batch_text = (ADDON_DIR / "batch_operations.py").read_text(encoding="utf-8")

    assert "audio_operation_params" in editor_text
    assert "audio_operation_params" in batch_text
```

Keep:

```python
assert "aqe:" not in text, relative
```

for batch core modules.

- [ ] **Step 2: Update rule 19 expected dependency sets**

In `tests/test_architecture/test_rule19_shared_operation_contracts.py`, update:

```python
assert MODULE_CONTRACTS["browser_dialog"].allowed_addon_deps == frozenset(
    {"audio_operation_params", "audio_operations", "batch_operations", "browser_report", "i18n"}
)
```

Add an assertion:

```python
assert MODULE_CONTRACTS["audio_operation_params"].allowed_addon_deps == frozenset({"audio_state"})
```

- [ ] **Step 3: Run architecture tests**

Run:

```bash
python3 -m pytest tests/test_architecture/test_rule13_batch_operation_boundaries.py tests/test_architecture/test_rule19_shared_operation_contracts.py tests/test_architecture/test_rule5_all_modules_classified.py tests/test_architecture/test_rule17_contract_driven_addon_dependency_policy.py -q
```

Expected: PASS.

### Task 8: Verification

**Files:**
- No planned source edits unless verification exposes a defect.

- [ ] **Step 1: Run the focused Python test set**

Run:

```bash
python3 -m pytest tests/test_audio_operation_params.py tests/test_editor_actions.py tests/test_editor_bridge_commands.py tests/test_batch_visualization.py tests/test_browser_integration.py -q
```

Expected: PASS.

- [ ] **Step 2: Run the required architecture test set**

Run:

```bash
python3 -m pytest tests/test_architecture/test_rule13_batch_operation_boundaries.py tests/test_architecture/test_rule19_shared_operation_contracts.py tests/test_architecture/test_rule5_all_modules_classified.py tests/test_architecture/test_rule17_contract_driven_addon_dependency_policy.py -q
```

Expected: PASS.

- [ ] **Step 3: Run the full required architecture test suite**

Run:

```bash
python3 -m pytest tests/test_architecture -q
```

Expected: PASS.

- [ ] **Step 4: Run the required import-linter architecture gate**

Run:

```bash
python3 scripts/dev.py arch
```

Expected: PASS.

- [ ] **Step 5: Run the reusable QC gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 6: Run required e2e tests before declaring the feature complete**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.


Run:

```text
```

Expected: changed symbols are limited to Browser hook/dialog wiring, shared operation parameters, editor action delegation, batch operation request/execution, tests, and locale strings.

---

## Acceptance Criteria

- Browser no longer adds a duplicate explicit context-menu **Run Audio Batch Operation...** action.
- Batch dialog shows speed controls only for `slower`/`faster`.
- Batch dialog shows volume controls only for `volume_down`/`volume_up`.
- Batch dialog shows pause aggressiveness controls only for `remove_pauses`.
- Batch dialog shows no transform parameter controls for `graph`.
- Batch defaults match persisted settings used by Editor split buttons.
- Batch selected parameters affect the rendered output/config for speed, volume, and pause shortening.
- Editor split-button behavior remains unchanged.
- Batch core modules still contain no `aqe:` bridge strings.
- No Browser module imports `editor_actions.py`.
- Focused tests pass.
- The full `tests/test_architecture` suite passes.
- `python3 scripts/dev.py arch` passes.
- `python3 scripts/dev.py check` passes.
- `python3 scripts/dev.py test-e2e` passes.

## Deferred Scope

- Adding batch trim-left/trim-right operations.
- Adding batch denoise operations.
- Converting batch dialog to Svelte/WebView UI.
- Remembering last-used batch parameter choices independently from settings.
- Adding a separate toolbar button for batch operations.

These items should be planned separately because they expand the operation registry, change processing surfaces, or add new persistence behavior beyond parameter parity for existing batch operations.
