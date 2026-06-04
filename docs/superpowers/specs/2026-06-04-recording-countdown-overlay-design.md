# Recording Countdown Overlay Design

## Goal

Resolve GitHub issue #17 by making voice recording start immediately by default and showing a large, clear countdown over the graph only when the user configures a positive countdown.

## Scope

In scope:

- Change the default `voice_recording_countdown_seconds` value from `3` to `0`.
- Preserve the existing `0..10` numeric setting instead of adding a second enable flag.
- Treat `0` as no countdown: recording dispatch starts immediately with no countdown status or overlay.
- Render a graph-centered countdown overlay for positive countdown values.
- Keep the normal status row behavior for recording, stopping, analyzing, ready, and failed states.
- Update config defaults, frontend defaults, fixtures, and focused tests.

Out of scope:

- Changing the recorder backend or Python recording lifecycle.
- Making the Record / Play yours panel visible by default.
- Adding new countdown durations beyond the existing `0..10` range.
- Changing graph analysis, learner pitch overlay, playback, or generated media behavior.

## Approved UX

The existing countdown seconds setting remains the single control. A value of `0` means "off." This is the new default in the committed config and all fallback defaults.

When the value is `0`, pressing Record clears any previous learner overlay, resets the recording cursor, and sends the existing `aqe:record-voice` payload immediately. The frontend does not enter `countdown` status, so the user does not see a transient `0` countdown.

When the value is greater than `0`, the existing timer flow remains: the frontend owns the countdown before it sends `aqe:record-voice` to Python. During that countdown, the graph surface shows a centered overlay with a large number. The regular status row still exposes the localized countdown message, and the overlay should have an accessible label derived from the same message.

## Architecture

`settings_ui/src/editor-inline/recording-actions.ts` remains the owner of recording countdown state. It should:

- branch immediately for `countdownSeconds <= 0`,
- set countdown state only for positive countdown values,
- render or clear the countdown overlay when learner recording state changes,
- clear the overlay when recording resets or leaves countdown state.

`settings_ui/src/editor-inline/GraphVisualizer.svelte` should provide a stable overlay host inside `.aqe-visualizer-plot` so the overlay can cover the graph without mutating the SVG.

`settings_ui/src/editor-inline/styles/visualizer.css` should style the overlay as non-interactive, centered, readable in light and dark Anki themes, and contained within the plot area. It must not block pointer events for graph selection, zoom, or back-chaining marker controls.

The persisted setting remains schema-first through `voice_recording_countdown_seconds`. No contract shape changes are required unless generated files drift from the existing schema.

## Data Flow

Settings defaults flow into the editor through `window.__AQE_EDITOR_CONFIG__.splitButtonDefaults.voiceRecordingCountdownSeconds`.

Field-local quick settings continue to come from `getSplitButtonState(ord)`. Users can still choose `0`, `3`, or `5` from the Record split menu, use the slider, and promote that field-local value as the default.

The countdown overlay is purely frontend state. Python still receives the same `aqe:record-voice` command payload only after any positive countdown completes.

## Testing

Focused frontend tests should cover:

- default split-button countdown is `0`,
- `0` dispatches `aqe:record-voice` immediately without setting countdown status,
- positive countdown values render a countdown overlay on the visualizer plot,
- leaving countdown state clears the overlay.

Config and settings tests should update expectations from `3` to `0` for default config, settings initial state, and fixtures.

E2E coverage should include at least one existing voice-recording workflow using `voice_recording_countdown_seconds=0` so recording remains immediate and deterministic. A positive-countdown visual e2e test is optional unless the frontend integration test cannot exercise the overlay reliably.

Verification target:

- `python3 scripts/dev.py test-svelte`
- focused Python config/settings/editor UI tests touched by the default change
- `python3 scripts/dev.py check`
- `python3 scripts/dev.py test-e2e`
