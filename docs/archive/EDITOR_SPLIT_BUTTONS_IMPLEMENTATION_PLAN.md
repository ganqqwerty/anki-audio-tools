# Editor Split Buttons Implementation Plan

## Goal

Build inline editor split buttons with per-field local parameters for trim, volume, speed, Shorten Pauses, and denoise while keeping global settings unchanged.

## Architecture Boundaries

- `settings_ui/src/editor-inline/` owns split-button rendering, floating popovers, local per-field state, formatting, and JSON command payload creation.
- `settings_ui/src/settings/` owns persisted settings controls and must not import editor-local split state.
- `editor_ui.py` remains import-safe HTML/config injection and only serializes defaults into `window.__AQE_EDITOR_CONFIG__`.
- `editor_actions.py` remains import-safe command decoding, override validation, command-to-operation mapping, and pure state transition glue.
- `editor_integration.py` remains the Anki adapter for rendering, media writes, field replacement, and status updates.
- `audio_state.py` owns typed processing defaults and `AudioEditState` transitions.
- `audio_operations.py` remains the shared operation registry and is kept free of editor-only `aqe:` bridge concerns.

The implementation includes an architecture test guarding the settings/editor boundary so persisted settings state and field-local split state do not import each other.

## Phase 1: Command Payloads And Trim Overrides

Commit: `0b7d0dd Add editor command override payload parsing for trims`

- Add normalized editor command payload decoding.
- Keep plain string commands compatible.
- Prove trim overrides apply locally without mutating `AudioProcessingConfig`.

Tests:

- `tests/test_editor_actions.py`
- `tests/test_audio_state.py`

## Phase 2: Editor Runtime Defaults

Commit: `78854f3 Expose split button defaults to the editor webview`

- Inject `splitButtonDefaults` into the editor webview runtime.
- Include trim, volume, speed, pause aggressiveness, and denoise algorithm defaults.
- Preserve import-safe behavior in `editor_ui.py`.

Tests:

- `tests/test_editor_ui.py`
- `tests/test_editor_integration.py`

## Phase 3: Trim Split Buttons

Commit: `0b3ee3e Add trim split buttons with field-local millisecond controls`

- Add reusable split-button UI with primary and attached option segments.
- Add floating popover positioning under the trigger.
- Add outside-click and Escape close behavior.
- Add per-field local state and payload building.

Tests:

- `settings_ui/tests/split-button-state.test.ts`
- `settings_ui/tests/editor-inline.integration.test.ts`

## Phase 4: Processing Payload Routing

Commit: `5e0444e Route parameterized editor commands through processing payloads`

- Route JSON payload commands through the same processing flow as string commands.
- Preserve command history and field targeting.
- Ensure local overrides reach both state transitions and rendering.

Tests:

- `tests/test_editor_actions.py`
- `tests/test_editor_integration.py`

## Phase 5: Trim E2E Coverage

Commit: `bf9bdbd Cover trim split button behavior in end-to-end tests`

- Add real-binary e2e coverage for field-local trim values.
- Cover repeated main-button clicks using the selected local value.
- Cover multi-field isolation and settings defaults.

Tests:

- `e2e/test_editor_processing_workflow.py`

## Phase 6: Volume And Speed Split Buttons

Commit: `8851936 Add volume and speed split buttons with local sliders`

- Add decibel sliders for volume actions.
- Add speed sliders for slower/faster actions.
- Keep local field values independent from persisted settings.

Tests:

- `settings_ui/tests/split-button-state.test.ts`
- `settings_ui/tests/editor-inline.integration.test.ts`
- `e2e/test_editor_processing_workflow.py`

## Phase 7: Shorten Pauses And Denoise

Commit: `3cd5787 Add pause aggressiveness and denoise algorithm split controls`

- Add Gentle, Normal, and Aggressive Shorten Pauses levels.
- Map pause aggressiveness to deterministic render settings for a single command.
- Convert denoise from a dropdown menu to a button with algorithm split menu.
- Add settings defaults for pause aggressiveness and denoise algorithm.
- Update config version, JSON schema, generated contracts, docs, and templates.

Tests:

- `tests/test_editor_actions.py`
- `settings_ui/tests/app.test.ts`
- `settings_ui/tests/split-button-state.test.ts`
- `settings_ui/tests/editor-inline.integration.test.ts`
- `settings_ui/tests/frontend-architecture.test.ts`
- `e2e/test_editor_processing_workflow.py`
- `e2e/test_editor_deep_filter_workflow.py`
- `python3 scripts/dev.py test-e2e`
- `python3 scripts/dev.py check`

## Verification

The completed implementation passed:

- `python3 scripts/dev.py test-e2e`
- `python3 scripts/dev.py check`

