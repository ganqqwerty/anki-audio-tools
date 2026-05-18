# Editor Split Buttons Design

## Goal

Add split-button parameter controls to the inline editor toolbar so users can tune common audio actions per field without changing global settings. The main button performs the action. A small attached arrow opens a floating popover that changes how the main button behaves for the active field.

## Scope

In scope:

- Trim left and trim right amount.
- Volume adjustment amount.
- Slower and faster speed multiplier or step.
- Shorten Pauses aggressiveness.
- Denoise algorithm choice.
- Settings defaults for every split-button value.
- E2E tests for settings defaults, local overrides, repeated clicks, and field isolation.

Out of scope for this pass:

- Persisting per-field split-button overrides across editor sessions.
- Adding new denoise algorithm strength parameters beyond the algorithms already supported.
- Reworking the full editor toolbar layout beyond the split-button controls.

## UX

Each eligible command becomes a split button:

- The primary segment keeps the existing icon and label and runs the action.
- The attached secondary segment opens a floating popover.
- The popover top edge sits just below the split button.
- The horizontal center of the popover aligns with the horizontal center of the trigger.
- The popover clamps to the visible editor/webview bounds when the centered position would overflow.
- Only one popover can be open at a time.
- The popover closes on outside click, Escape, opening another popover, or dispatching a command.

The main button always uses the current local value for that field. For example, if field 0 trim-left is set to 200 ms, clicking Trim Left three times adds 200 ms each time. Field 1 still uses its own local value.

## Controls

Trim left and trim right:

- Slider range: 50 ms to 10 s.
- Display formatted values as milliseconds below 1000 ms and seconds at or above 1000 ms.
- Include small preset buttons such as 100 ms, 200 ms, 500 ms, and 1 s for fast selection.
- Default value comes from settings.

Volume up and volume down:

- Slider controls the dB amount applied per click.
- Range comes from the configured volume bounds where practical, with the value interpreted as a positive step for Volume Up and negative step for Volume Down.
- Default value comes from settings.

Slower and faster:

- Slider controls the speed delta or target multiplier used by the main command.
- Values are constrained by configured min and max speed.
- Default value comes from settings.

Shorten Pauses:

- Slider exposes a simple user-facing aggressiveness level: Gentle, Normal, Aggressive.
- Internally, each level maps to the pause-detection and target-gap settings used for one render.
- Normal maps to the current configured settings.
- Gentle should preserve more pause length than Normal.
- Aggressive should compress more pause length than Normal.

Denoise:

- Denoise becomes a primary button plus attached algorithm menu.
- Primary button runs the selected local algorithm.
- The split menu selects Standard or RNNoise.
- Standard remains DeepFilterNet-based. The existing implementation exposes the DeepFilterNet post-filter as a global setting, not as a per-click strength parameter.
- RNNoise remains command-only in the current wrapper and does not expose a strength parameter.

## State Model

The editor frontend owns local split-button state per field ordinal. Initial values come from `window.__AQE_EDITOR_CONFIG__`, which must include the relevant audio-processing defaults from Python.

Local state rules:

- A newly mounted field initializes from settings.
- Editing a popover value updates only that field's local split-button state.
- Local changes do not call the settings bridge and do not mutate persisted settings.
- Repeated main-button clicks reuse the local value.
- Other fields keep independent local values.
- Reloading/recreating editor controls may reinitialize from settings; persistence across editor sessions is out of scope.

## Command Flow

The frontend should send processing commands with an optional override payload rather than only the command string. The existing string command path should keep working for compatibility and tests.

Expected shape:

```json
{
  "command": "aqe:trim-left",
  "fieldOrd": 0,
  "overrides": {
    "trimStepMs": 200
  }
}
```

Python decodes the payload, validates it, builds a one-command effective configuration or direct operation parameter, and applies it only to that command. Invalid or missing overrides fall back to configured defaults where that is safer than failing the command.

## Settings

Settings must expose defaults for:

- Trim step.
- Volume step.
- Speed step or multiplier behavior.
- Shorten Pauses default aggressiveness.
- Denoise default algorithm.

Existing settings should be reused where they already represent the same concept. New schema fields should be added only for values that do not exist yet, such as default pause aggressiveness and default denoise algorithm.

## Audio Behavior

Trim, volume, and speed should remain non-destructive and continue to generate a new media file per action.

Shorten Pauses should keep using the existing DeepFilterNet plus silence-detect pipeline. Aggressiveness maps should be deterministic and covered by unit tests. A proposed first mapping:

- Gentle: higher pause threshold and longer target gap than Normal.
- Normal: configured `internal_pause_silence_threshold_db`, `internal_pause_threshold_ms`, and `internal_pause_target_gap_ms`.
- Aggressive: lower pause threshold and shorter target gap than Normal.

The exact numeric mapping should be chosen during implementation against the current pipeline constraints and validated with focused unit tests.

## Testing

Use a test-first implementation. Required coverage:

- Unit tests for command payload decoding and fallback behavior.
- Unit tests for applying trim, speed, volume, and pause-aggressiveness overrides.
- Frontend tests for split-button local state initialization, popover close behavior, and per-field isolation.
- Integration tests for risky bridge and render boundaries, especially payload decoding, settings default propagation, session state isolation, and command fallback behavior.
- E2E tests that settings defaults are selected by default in the editor.
- E2E tests that changing a split-menu value does not change settings.
- E2E tests that changing a split-menu value affects only the current field.
- E2E tests that repeated main-button clicks reuse the selected local value.
- E2E tests for multi-field notes where each field keeps independent split-button values and generated media updates only the active field.
- E2E tests for the Automatically Show Graph setting to prove graph startup still works with split-button controls and multi-field initialization.
- E2E tests should use real processing binaries for normal success paths, including ffmpeg/ffprobe and the bundled denoise binaries where the feature under test depends on them.
- Exceptional-scenario E2E tests may use mocks only when the mock demonstrates the exceptional behavior directly, such as a renderer raising an error, a missing binary, or a failed external command.
- E2E tests for denoise primary-button algorithm selection should use real binaries for success-path coverage where practical. If full denoise rendering is too slow for every local override case, keep one real-binary success path and cover the remaining algorithm dispatch matrix with focused integration tests.

## Implementation Phases

Each phase should be completed test-first and should leave the full relevant quality gate green before moving on. Shared infrastructure may be introduced in the earliest phase that needs it, but each feature phase must include its settings, unit/integration tests, frontend tests, E2E coverage, and generated bundle updates.

### Phase 1: Shared Split-Button Infrastructure

Settings:

- Extend editor runtime config so the inline editor receives all split-button defaults from Python.
- Add any schema fields needed by later phases, with generated TypeScript/Python contracts kept in sync.

Implementation:

- Add the split-button component shape, floating popover positioning, outside-click close, Escape close, and single-open-popover behavior.
- Add local per-field split-button state initialized from settings.
- Add payload-capable command dispatch while preserving the existing plain string command path.
- Add Python payload decoding and validation scaffolding without changing audio behavior yet.

Tests:

- Frontend tests for popover positioning contract, close behavior, and one-open-popover behavior.
- Frontend tests for per-field local state initialization and isolation.
- Python unit tests for command payload decoding, validation, fallback, and compatibility with plain string commands.
- Integration tests from frontend command payload shape through Python command handling using non-rendering or minimal render boundaries.
- E2E smoke test that the editor toolbar still mounts for single-field and multi-field notes.
- E2E test that the Automatically Show Graph setting still renders startup graphs with split-button controls present.

### Phase 2: Trim Left And Trim Right

Settings:

- Reuse the trim-step default setting for the initial split-button value unless a new default is needed.
- Keep the slider range fixed at 50 ms to 10 s.

Implementation:

- Add trim left and trim right split buttons.
- Apply local `trimStepMs` overrides per command.
- Ensure repeated clicks accumulate the selected trim amount.

Tests:

- Unit tests for trim override validation and accumulation.
- Frontend tests for trim slider formatting, presets, and local state.
- Integration tests proving trim payloads update only the effective command value, not persisted settings.
- E2E tests with real ffmpeg/ffprobe for configured default selection, changing trim amount locally, repeated trim clicks, and output-duration change.
- Multi-field E2E tests proving field 0 and field 1 can use different trim amounts and only the active field media reference changes.

### Phase 3: Volume

Settings:

- Reuse volume step and configured min/max volume settings for defaults and slider bounds.

Implementation:

- Add volume up and volume down split buttons.
- Interpret the selected dB amount as positive for Volume Up and negative for Volume Down.
- Clamp effective volume to configured min/max bounds.

Tests:

- Unit tests for volume override validation, sign handling, and clamping.
- Frontend tests for dB slider display and per-field local state.
- Integration tests proving volume payloads do not mutate settings.
- E2E tests with real ffmpeg/ffprobe for default dB selection, local override, repeated clicks, and multi-field isolation.

### Phase 4: Speed Slower And Faster

Settings:

- Reuse speed step and configured min/max speed settings for defaults and slider bounds.

Implementation:

- Add slower and faster split buttons.
- Apply the selected speed delta or multiplier consistently with the existing slower/faster behavior.
- Clamp effective speed to configured min/max bounds.

Tests:

- Unit tests for speed override validation and min/max clamping.
- Frontend tests for speed slider display and local state.
- Integration tests for payload handling and settings isolation.
- E2E tests with real ffmpeg/ffprobe for default speed selection, local override, output-duration change, repeated clicks, and multi-field isolation.

### Phase 5: Shorten Pauses Aggressiveness

Settings:

- Add a default Shorten Pauses aggressiveness setting with values Gentle, Normal, and Aggressive.
- Normal maps to the current configured pause settings.

Implementation:

- Add the Shorten Pauses split button with a three-stop aggressiveness slider.
- Map Gentle, Normal, and Aggressive to deterministic per-render pause settings.
- Keep the existing DeepFilterNet plus silence-detect pipeline.

Tests:

- Unit tests for aggressiveness mapping and validation.
- Integration tests proving the effective pause settings reach the render pipeline without changing persisted settings.
- Frontend tests for labeled slider stops and default selection.
- E2E tests with real binaries for Normal success path and at least one non-Normal aggressiveness success path.
- Multi-field E2E tests proving different fields can keep different aggressiveness values.
- Exceptional-scenario E2E tests may mock renderer failure or missing binary behavior to verify error display and cleanup.

### Phase 6: Denoise Algorithm Split Button

Settings:

- Add a default denoise algorithm setting with Standard and RNNoise options.
- Keep DeepFilterNet post-filter as the existing global setting.

Implementation:

- Replace the current denoise details menu with a primary Denoise button plus attached floating algorithm menu.
- Primary Denoise runs the selected local algorithm for the active field.
- Algorithm selection is local per field and does not mutate settings.

Tests:

- Unit tests for algorithm default validation and command mapping.
- Frontend tests for menu selection, local state, and popover close behavior.
- Integration tests proving selected algorithm dispatches to the correct Python renderer.
- E2E tests with real bundled binaries for Standard and RNNoise success paths where feasible.
- Multi-field E2E tests proving field-local algorithm selection.
- Exceptional-scenario E2E tests may mock renderer failures for Standard or RNNoise to verify user-visible error handling and busy-state cleanup.

### Phase 7: Cross-Feature Regression And Quality Gate

Settings:

- Verify all new settings appear in the settings dialog, persist correctly, migrate correctly, and are included in generated contracts.

Implementation:

- Rebuild committed settings and editor webview bundles.
- Review toolbar layout at narrow and normal editor widths.
- Confirm popover viewport clamping near toolbar edges.

Tests:

- Full frontend test suite.
- Full Python unit and integration suite.
- E2E multi-field regression covering at least trim, volume, speed, Shorten Pauses, denoise, and Automatically Show Graph together in one realistic editor session.
- `python3 scripts/dev.py check`.
- `python3 scripts/dev.py test-e2e`.

## Risks

- The editor command bridge currently sends plain strings, so payload support must be added without breaking existing command handlers.
- Floating popovers inside Anki WebEngine need careful outside-click and focus handling to avoid stuck menus.
- Settings schema and generated TypeScript/Python contracts must stay synchronized.
- E2E denoise tests may be slow or platform-dependent; prefer testing algorithm selection separately from full denoise rendering.
