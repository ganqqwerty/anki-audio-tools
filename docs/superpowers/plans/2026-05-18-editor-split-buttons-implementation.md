# Editor Split Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build inline editor split buttons with per-field local parameters for trim, volume, speed, Shorten Pauses, and denoise while keeping global settings unchanged.

**Architecture:** Frontend owns local per-field UI state and floating popovers. Import-safe Python modules decode command payloads and apply pure state transitions. `editor_integration.py` remains the Anki adapter that coordinates rendering, media writes, field replacement, and status updates.

**Tech Stack:** Python 3.13, Anki 25.09 APIs, Svelte 5, TypeScript, Vitest, pytest, Qt/WebEngine e2e, ffmpeg/ffprobe, bundled DeepFilterNet and RNNoise.

---

## File Structure

- Modify `addon/anki_audio_quick_editor/config.json`: add default denoise algorithm and Shorten Pauses aggressiveness if needed.
- Modify `addon/anki_audio_quick_editor/config.schema.json`: validate new settings.
- Modify `contracts/communication.schema.json`: only if editor command payloads become an owned generated contract.
- Regenerate `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts` after schema changes.
- Modify `addon/anki_audio_quick_editor/audio_state.py`: add typed split-button defaults, override validation, and pure state transitions.
- Modify `addon/anki_audio_quick_editor/editor_actions.py`: decode/normalize payload commands and apply overrides without Anki imports.
- Modify `addon/anki_audio_quick_editor/editor_ui.py`: inject split-button defaults into `window.__AQE_EDITOR_CONFIG__`.
- Modify `addon/anki_audio_quick_editor/editor_integration.py`: route payload commands through normalized action data and keep render/media side effects here.
- Modify `settings_ui/src/editor-inline/types.ts`: add split-button runtime config and payload types.
- Modify `settings_ui/src/editor-inline/bridge.ts`: send JSON payloads while keeping plain string commands available.
- Modify `settings_ui/src/editor-inline/actions.ts`: dispatch commands with local overrides and close popovers on command dispatch.
- Modify `settings_ui/src/editor-inline/commands.ts`: declare split-capable command metadata.
- Create `settings_ui/src/editor-inline/split-button-state.ts`: per-field local state, formatting, clamping, and payload construction.
- Create `settings_ui/src/editor-inline/SplitButton.svelte`: reusable split-button UI and floating popover behavior.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte`: replace eligible command buttons with split buttons.
- Modify `settings_ui/src/editor-inline/styles.css`: split-button and popover styles.
- Modify `settings_ui/src/settings/GeneralSettingsPanel.svelte`: expose new defaults where needed.
- Modify `addon/anki_audio_quick_editor/templates/editor/editor_bundle.{js,css}` and settings bundles through `python3 scripts/dev.py build`.
- Add/update `tests/test_editor_actions.py`, `tests/test_audio_state.py`, `tests/test_editor_ui.py`, `tests/test_editor_integration.py`.
- Add/update `settings_ui/tests/editor-inline.actions.test.ts`, `settings_ui/tests/editor-inline.integration.test.ts`, and create `settings_ui/tests/split-button-state.test.ts`.
- Add/update architecture tests under `tests/test_architecture/`.
- Add/update e2e tests in `e2e/test_editor_processing_workflow.py`, plus denoise/pause-specific files when needed.

## Task 1: Payload Decode And Trim Overrides

**Files:**
- Modify: `addon/anki_audio_quick_editor/audio_state.py`
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Test: `tests/test_editor_actions.py`
- Test: `tests/test_audio_state.py`

- [ ] **Step 1: Write failing Python tests**

Add tests proving:

```python
def test_decode_processing_command_accepts_json_payload() -> None:
    assert decoded.field_ord == 0
    assert decoded.overrides.trim_step_ms == 200


def test_apply_processing_command_uses_trim_override_without_mutating_config() -> None:
    state = AudioEditState("clip.mp3")
    assert apply_processing_command(decoded, state, config) == AudioEditState("clip.mp3", left_trim_ms=200)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_editor_actions.py::test_decode_processing_command_accepts_json_payload tests/test_editor_actions.py::test_apply_processing_command_uses_trim_override_without_mutating_config -q
```

Expected: fail because the decoder/override types do not exist.

- [ ] **Step 3: Implement minimal import-safe payload support**

Add frozen dataclasses for normalized command payloads and override values in `editor_actions.py` or an import-safe helper. Keep string commands compatible by normalizing plain strings into the same structure.

Implementation requirements:

- Clamp trim override to `50..10000`.
- Preserve `operation_for_command(command: str)`.
- Keep `audio_operations.py` free of `aqe:` strings beyond existing adapter mapping.

- [ ] **Step 4: Run focused tests and architecture tests**

Run:

```bash
python3 -m pytest tests/test_editor_actions.py tests/test_audio_state.py tests/test_architecture/test_rule13_batch_operation_boundaries.py tests/test_architecture/test_rule19_shared_operation_contracts.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_state.py addon/anki_audio_quick_editor/editor_actions.py tests/test_editor_actions.py tests/test_audio_state.py
git commit -m "Add editor command payload trim overrides"
```

## Task 2: Editor Runtime Defaults

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_ui.py`
- Test: `tests/test_editor_ui.py`

- [ ] **Step 1: Write failing tests**

Add a test that `injection_script(...)` embeds split-button defaults:

```python
assert '"splitButtonDefaults"' in script
assert '"volumeStepDb": 2.5' in script
assert '"speedStep": 0.1' in script
```

- [ ] **Step 2: Run test and verify RED**

Run:

```bash
python3 -m pytest tests/test_editor_ui.py::test_injection_script_embeds_split_button_defaults -q
```

Expected: fail because defaults are not injected.

- [ ] **Step 3: Implement defaults injection**

Extend `editor_ui.injection_script(...)` signature or config construction so editor integration can pass:

```json
{
  "splitButtonDefaults": {
    "volumeStepDb": 3.0,
    "speedStep": 0.05,
    "pauseAggressiveness": "normal",
    "denoiseAlgorithm": "standard"
  }
}
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_editor_ui.py tests/test_editor_integration.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_ui.py addon/anki_audio_quick_editor/editor_integration.py tests/test_editor_ui.py tests/test_editor_integration.py
git commit -m "Inject split button defaults into editor runtime"
```

## Task 3: Frontend Split Button State And Trim UI

**Files:**
- Create: `settings_ui/src/editor-inline/split-button-state.ts`
- Create: `settings_ui/src/editor-inline/SplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/bridge.ts`
- Modify: `settings_ui/src/editor-inline/actions.ts`
- Modify: `settings_ui/src/editor-inline/commands.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/styles.css`
- Test: `settings_ui/tests/split-button-state.test.ts`
- Test: `settings_ui/tests/editor-inline.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.actions.test.ts`

- [ ] **Step 1: Write failing frontend tests**

Add Vitest coverage proving:

```ts
expect(formatTrimMs(200)).toBe("200 ms");
expect(formatTrimMs(1000)).toBe("1 s");
expect(clampTrimStepMs(10)).toBe(50);
expect(clampTrimStepMs(20000)).toBe(10000);
```


- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd settings_ui
npm run test -- split-button-state.test.ts editor-inline.integration.test.ts editor-inline.actions.test.ts
```

Expected: fail because split-button helpers/components do not exist.

- [ ] **Step 3: Implement frontend trim split button**

Implement:

- `split-button-state.ts` with trim formatting, clamping, per-field defaults, and payload building.
- `SplitButton.svelte` with primary button, attached arrow, floating popover, outside click close, Escape close, and centered-under-trigger positioning with viewport clamping.
- Trim left/right sliders with range `50..10000`, preset buttons `100`, `200`, `500`, `1000`.
- `bridge.ts` JSON payload send helper.
- `actions.ts` dispatch path that closes open popovers on command dispatch.

- [ ] **Step 4: Run frontend focused tests**

Run:

```bash
cd settings_ui
npm run test -- split-button-state.test.ts editor-inline.integration.test.ts editor-inline.actions.test.ts
```

Expected: pass.

- [ ] **Step 5: Run frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: pass and update committed editor bundle if source changed.

- [ ] **Step 6: Commit**

```bash
git add settings_ui/src/editor-inline settings_ui/tests addon/anki_audio_quick_editor/templates/editor
git commit -m "Add trim split buttons to editor toolbar"
```

## Task 4: Python Editor Integration With Payload Commands

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_integration.py`
- Test: `tests/test_editor_integration.py`
- Test: `tests/test_architecture/test_rule3_editor_bridge_contract.py`

- [ ] **Step 1: Write failing integration tests**

Add tests proving `_handle_bridge_command` accepts a JSON payload, focuses the requested field, applies the normalized command, and keeps existing plain string commands working.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_editor_integration.py::test_bridge_accepts_processing_json_payload tests/test_editor_integration.py::test_bridge_keeps_plain_processing_commands -q
```

Expected: fail before payload routing is wired.

- [ ] **Step 3: Implement editor adapter routing**

In `editor_integration.py`, normalize incoming command text through the import-safe decoder. Use `fieldOrd` from payload to focus the right field before rendering. Keep non-processing commands and special denoise commands compatible.

- [ ] **Step 4: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_editor_integration.py tests/test_architecture/test_rule3_editor_bridge_contract.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_integration.py tests/test_editor_integration.py tests/test_architecture/test_rule3_editor_bridge_contract.py
git commit -m "Route editor processing payload commands"
```

## Task 5: Trim E2E With Real Binaries And Multi-Field Isolation

**Files:**
- Modify: `e2e/test_editor_processing_workflow.py`

- [ ] **Step 1: Write failing E2E tests**

Add tests:

- configured trim default appears in the trim split popover.
- field 0 and field 1 can hold different trim values and only active field media changes.
- Automatically Show Graph still draws startup graphs on a multi-field note.

- [ ] **Step 2: Run selected E2E tests and verify RED**

Run:

```bash
python3 scripts/dev.py test-e2e -- -k "trim_split or automatically_show_graph"
```

Expected: fail until frontend/backend wiring is complete.

- [ ] **Step 3: Fix only the behavior covered by the tests**

Adjust selectors, data-testid attributes, field focusing, and payload routing until the selected e2e tests pass with real ffmpeg/ffprobe.

- [ ] **Step 4: Run selected E2E tests**

Run:

```bash
python3 scripts/dev.py test-e2e -- -k "trim_split or automatically_show_graph"
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add e2e/test_editor_processing_workflow.py settings_ui/src/editor-inline addon/anki_audio_quick_editor/templates/editor addon/anki_audio_quick_editor
git commit -m "Cover trim split buttons with e2e tests"
```

## Task 6: Volume Split Buttons

**Files:**
- Modify: `addon/anki_audio_quick_editor/audio_state.py`
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `settings_ui/src/editor-inline/split-button-state.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/SplitButton.svelte`
- Modify tests for Python, frontend, and e2e.

- [ ] **Step 1: Write failing tests for volume override sign, clamping, frontend dB display, and e2e real-binary output change**
- [ ] **Step 2: Verify RED with focused pytest, Vitest, and selected e2e**
- [ ] **Step 3: Implement volume override and UI**
- [ ] **Step 4: Verify GREEN with focused pytest, Vitest, and selected e2e**
- [ ] **Step 5: Commit with message `Add volume split buttons`**

## Task 7: Speed Split Buttons

**Files:** same shared frontend/backend paths as Task 6.

- [ ] **Step 1: Write failing tests for speed override validation, min/max clamping, frontend display, repeated clicks, and real-binary duration change**
- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement speed split buttons**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit with message `Add speed split buttons`**

## Task 8: Shorten Pauses Aggressiveness

**Files:**
- Modify config/schema/contracts/settings UI as needed.
- Modify `audio_state.py`, `audio_pipeline.py` or import-safe helper, `audio_processor.py` only for effective config acceptance.
- Modify frontend split-button state and UI.
- Add unit, integration, frontend, and e2e tests.

- [ ] **Step 1: Write failing tests for `gentle|normal|aggressive` config validation and mapping**
- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement settings, mapping, frontend slider, and command overrides**
- [ ] **Step 4: Run generated contract checks, focused tests, and real-binary e2e for Normal plus one non-Normal level**
- [ ] **Step 5: Commit with message `Add pause aggressiveness split button`**

## Task 9: Denoise Algorithm Split Button

**Files:**
- Modify config/schema/contracts/settings UI as needed.
- Modify frontend denoise menu.
- Modify `editor_actions.py`/`editor_integration.py` dispatch mapping for selected algorithm.
- Add tests.

- [ ] **Step 1: Write failing tests for default algorithm, local algorithm selection, frontend menu, Python dispatch, and e2e real-binary Standard/RNNoise success path where feasible**
- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement denoise primary button plus floating algorithm menu**
- [ ] **Step 4: Verify GREEN with focused tests and real-binary e2e**
- [ ] **Step 5: Commit with message `Add denoise algorithm split button`**

## Task 10: Final Architecture, Bundle, And Quality Gate

**Files:**
- Modify architecture tests if not already complete.
- Regenerate bundles/contracts.

- [ ] **Step 1: Run architecture tests**

```bash
python3 scripts/dev.py arch
python3 -m pytest tests/test_architecture -q
```

- [ ] **Step 2: Run full QC**

```bash
python3 scripts/dev.py check
```

- [ ] **Step 3: Run full e2e**

```bash
python3 scripts/dev.py test-e2e
```


```bash
```

- [ ] **Step 5: Commit final fixes**

```bash
git add .
git commit -m "Complete editor split button controls"
```

## Self-Review

- Spec coverage: the plan includes UI behavior, local per-field state, payload dispatch, settings defaults, all feature phases, architecture tests, integration tests, multi-field e2e, Automatically Show Graph e2e, real-binary success paths, and exceptional mock allowances.
- Placeholder scan: no task depends on an undefined later type for the first executable slice. Later feature phases intentionally reference the shared primitives created in Tasks 1-5.
