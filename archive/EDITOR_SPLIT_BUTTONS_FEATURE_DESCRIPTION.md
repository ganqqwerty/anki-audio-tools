# Editor Split Buttons Feature Description

## Summary

The inline editor toolbar now supports split-button controls for common audio edits. The main segment runs the audio action, while the attached segment opens a floating popover that changes the parameter used by that action for the currently selected field.

The popover is centered below the trigger, closes on outside click or Escape, and keeps its state local to the active field. Settings provide the default values used when a field is first edited, but changes made from a split popover do not write back to settings.

## User-Facing Behavior

- Trim left and trim right use a millisecond slider from 50 ms to 10 s.
- Volume actions use a decibel slider.
- Speed actions use a multiplier/step slider within configured speed bounds.
- Shorten Pauses exposes Gentle, Normal, and Aggressive levels.
- Denoise is a primary button; the split menu selects Standard or RNNoise.
- Repeated clicks reuse the selected local value for that field.
- Other fields keep independent local values.
- Global settings control defaults only.

## Denoise Parameters

The current denoise implementations expose algorithm choice, not per-click strength:

- Standard uses the existing DeepFilterNet path and honors the existing global post-filter setting.
- RNNoise uses the existing RNNoise command path and does not expose a strength parameter.

## Commit Map

- `5a1cdbf` - Documents the phased rollout plan and required architecture boundaries.
- `0b7d0dd` - Adds typed editor command payload parsing for local trim overrides.
- `78854f3` - Injects split-button defaults into the editor webview runtime.
- `0b3ee3e` - Adds trim split buttons and floating millisecond controls.
- `5e0444e` - Routes parameterized payload commands through the editor processing path.
- `bf9bdbd` - Adds real-binary e2e coverage for trim split-button behavior.
- `8851936` - Adds volume and speed split buttons with local sliders.
- `3cd5787` - Adds pause aggressiveness and denoise algorithm split controls, settings defaults, schema/contracts, docs, and broader tests.

