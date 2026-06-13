# Chorusing Auto-Advance Split Menu Design

## Context

GitHub issue #19 asks for Chorusing to become a split-button surface with:

- a separate "Pause between repeats" quick setting, default `0`
- an off-by-default auto-advance checkbox
- a repeat count input shown for auto-advance, default `3`
- support for manual longer/shorter suffix navigation while auto-advance is active

Chorusing is an editor-only, non-mutating practice mode. It currently forces repeat playback for the active suffix, restores the field's ordinary repeat setting when practice pauses, and uses the same marker movement path for toolbar navigation and marker edits. Selected-region repeat loops are already browser-audio-only when they need reliable loop control, so auto-advance can stay in the TypeScript editor runtime.

## Decision

Use a dedicated `ChorusingSplitButton.svelte` instead of extending the generic processing `SplitButton` menu.

The dedicated component keeps Chorusing's controls close to the existing Play split-button pattern. It avoids adding checkbox and repeat-count-only behavior to the generic audio-processing menu, which already handles many generated-file operation variants. The Chorusing panel remains a grouped toolbar panel: the primary Chorusing action becomes a split button, while Longer suffix and Shorter suffix remain plain toolbar buttons.

## Settings And State

Add persisted Settings defaults:

- `chorusing_pause_seconds`: number, default `0`, clamped to the same `0..10` second range as Play repeat pause
- `chorusing_auto_advance_by_default`: boolean, default `false`
- `chorusing_auto_advance_repeats`: integer, default `3`, clamped to `1..20`

These defaults flow through the config schema, generated contracts, Python default config, settings initial state, editor runtime config, and frontend split-button state. Field-local quick settings initialize from these defaults and do not update persisted Settings unless the user clicks the save-default control.

Extend `FieldSplitButtonState` with Chorusing defaults, current values, and a `chorusingEdited` flag:

- default/current pause seconds
- default/current auto-advance enabled
- default/current auto-advance repeat count
- `chorusingEdited`, set when any Chorusing quick setting changes for a field and cleared when the current field promotes Chorusing defaults

## UI Behavior

`ChorusingSplitButton.svelte` renders inside the existing Chorusing toolbar panel.

Primary button:

- uses the existing `aqe:chorusing-practice` command and current enabled/disabled behavior
- toggles start/pause exactly as today
- keeps the current active/pause icon state from `syncChorusingToolbarButtons`

Menu:

- uses the existing split popover styling and tooltip conventions
- contains an auto-advance toggle
- contains a repeat-count `UnitNumberInput`, enabled only when auto-advance is on
- contains a separate pause-between-repeats `UnitNumberInput`, slider, and presets matching Play's repeat pause control where practical
- contains a save-default button
- contains a run button that starts/toggles Chorusing practice

The menu needs no Python command payload. It mutates field-local frontend state and writes the active Chorusing pause seconds to the visualizer before playback starts.

## Playback Flow

Chorusing playback remains frontend-owned.

When practice starts:

1. Ensure the Chorusing base and active suffix as today.
2. Store the current ordinary repeat state.
3. Force repeat on for the active suffix.
4. Apply the Chorusing pause seconds to `data-repeat-pause-seconds`.
5. Reset the auto-advance repeat counter for the active suffix.
6. Start browser playback for the active suffix.

When a loop boundary is reached during Chorusing:

- if auto-advance is off, keep current loop behavior
- if auto-advance is on, increment the completed-repeat count
- once the count reaches the configured repeat count, move to the next longer suffix by calling the existing Chorusing movement path
- if there is no next longer suffix, pause Chorusing and restore the field's ordinary repeat state

Manual Longer suffix and Shorter suffix clicks remain allowed while auto-advance is active. They reuse the existing movement path, restart playback for the selected suffix, and reset the auto-advance repeat counter for that suffix.

Marker insertion/removal during practice keeps its current behavior. If the active suffix changes as a consequence, the repeat counter resets before the restarted playback pass.

## Error Handling

Invalid or missing quick-setting values are clamped in the frontend state layer. Python config loading and schema validation also clamp or reject persisted values using existing config conventions.

If Chorusing cannot start because there is no graph track, no markers, or no active suffix, it keeps today's disabled/rejected behavior. Auto-advance does not add a new failure state.

If browser audio is unavailable for the selected suffix loop, keep the existing selected-repeat browser-audio warning path rather than falling back to native playback for auto-advance.

## Tests

Frontend unit and integration tests:

- Chorusing split menu renders in the Chorusing panel and keeps Longer/Shorter suffix buttons intact.
- Defaults initialize field-local Chorusing values.
- Field-local Chorusing quick settings are isolated between fields.
- Save-default sends the new Chorusing default values and updates unedited fields.
- Auto-advance increments completed suffix repeats and moves to the next longer suffix after the configured repeat count.
- Manual Longer/Shorter clicks during auto-advance reset the repeat counter and continue from the clicked suffix.
- Auto-advance pauses at the longest suffix when no longer suffix remains.

E2E tests:

- A real editor graph starts Chorusing with auto-advance enabled and advances from the shortest suffix to longer suffixes after the configured repeat count.
- Manual longer/shorter clicks during auto-advance remain responsive and do not leave stale playback selection or repeat state.

Verification commands:

- `python3 scripts/dev.py contracts-generate`
- `python3 scripts/dev.py config-schema`
- focused Svelte tests for Chorusing and split-button state
- `python3 scripts/dev.py test-e2e -- e2e/test_editor_chorusing_playback_workflow.py` if the runner supports forwarding a focused path, otherwise the repository's nearest focused e2e invocation
- `python3 scripts/dev.py check` before considering the feature complete
