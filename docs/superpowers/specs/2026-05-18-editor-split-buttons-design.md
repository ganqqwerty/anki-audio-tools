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
- E2E tests that settings defaults are selected by default in the editor.
- E2E tests that changing a split-menu value does not change settings.
- E2E tests that changing a split-menu value affects only the current field.
- E2E tests that repeated main-button clicks reuse the selected local value.
- E2E tests for denoise primary-button algorithm selection if practical without running expensive denoise binaries; otherwise cover command dispatch at the bridge layer and keep binary behavior in existing processing tests.

## Risks

- The editor command bridge currently sends plain strings, so payload support must be added without breaking existing command handlers.
- Floating popovers inside Anki WebEngine need careful outside-click and focus handling to avoid stuck menus.
- Settings schema and generated TypeScript/Python contracts must stay synchronized.
- E2E denoise tests may be slow or platform-dependent; prefer testing algorithm selection separately from full denoise rendering.
