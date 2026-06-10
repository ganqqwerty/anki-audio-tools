# Region Selection And Loop Playback Feature Plan

Implementation commit: `845517118054e89aff001fd0c2ab3e5920549211`

## Background

Audio Quick Editor already has a compact prosody graph in the Anki Editor. The graph supports a single playback cursor/progress indicator:

- Normal graph click or drag moves the cursor.
- Play starts from the cursor.
- During playback, the cursor becomes the progress indicator.
- HTML audio playback is preferred when a visualizer track is present because it can seek and report progress accurately.
- Native Anki playback remains a fallback path.

The new feature adds region selection and optional indefinite repeat. It must not make the existing click-to-position and drag-to-scrub workflow harder, because that is already part of the current editor muscle memory.

The selected interaction model is Shift-only selection:

- Normal click and normal drag keep their current meaning.
- Shift gestures are the only way to create or clear a playback region.
- There is at most one explicit selected region.
- A cleared explicit selection means the effective playback region is the whole graph.

This document is an implementation handoff. It describes the intended behavior, state model, progress indicator rules, and the tests that should be implemented before and during the feature work.

## User Goals

- Select a precise part of a short audio clip.
- Play only that selected part.
- Repeat the selected part indefinitely for listening practice.
- Keep using normal graph clicks to play from any point.
- Keep dragging the progress indicator to scrub or change the playback start.
- Configure whether repeat is checked by default.

## Non-Goals

- Multi-region selection.
- Waveform editing.
- Region trimming or destructive edits from the selected range.
- Keyboard-only region editing in the first implementation.
- Persisting a selected region across note loads.
- Native Anki indefinite loop playback if HTML audio is available.

## Terminology

- **Playhead**: the vertical cursor line when playback is stopped or paused.
- **Progress indicator**: the same vertical line while playback is playing.
- **Explicit selection**: a user-created region with `selectionStartMs < selectionEndMs`.
- **Effective playback region**: explicit selection when present, otherwise the full graph `[0, durationMs]`.
- **Repeat**: the checkbox near the player. When checked, the effective playback region repeats indefinitely.
- **Selection gesture**: Shift plus pointer interaction on the graph.
- **Scrub gesture**: normal pointer interaction that moves the playhead.

## UX Contract

### Controls

Add a checkbox near the Play button.

Recommended label:

```text
Repeat
```

Rationale: when no explicit selection exists, the effective region is the whole graph, so "Repeat selection" would be slightly misleading. A tooltip or accessible label may clarify "Repeat selected region, or the whole graph when no region is selected."

### Graph Visuals

The graph should render:

- The existing playhead/progress line.
- A translucent selected-region band when an explicit selection exists.
- Optional region edge handles or boundary lines if they fit the compact UI.
- A live provisional selection band while the user is Shift-dragging, before the left mouse button is released.

When explicit selection is cleared, do not draw a full-width highlighted band by default. A full-width highlight would look like a permanent visual state and would make it harder to tell whether the user has selected a special subsection. The effective playback region is still the whole graph.

During Shift-drag, the provisional band must update continuously from the gesture anchor to the current pointer position. The user should be able to see the exact region being selected while the drag is still in progress, not only after `pointerup`.

Recommended visual behavior:

- Before the drag threshold is crossed, keep the existing committed selection visible and do not show a tiny provisional band.
- Once the threshold is crossed, show the provisional band using the same selected-region style, or a slightly lighter variant if that is clearer.
- Normalize the preview visually while dragging, so right-to-left drags show the band between the earlier and later times.
- Clamp the preview to graph bounds while dragging.
- On `pointerup`, commit the provisional band as the explicit selection.
- On `pointercancel`, Escape, loss of capture, or editor teardown before `pointerup`, discard the provisional band and preserve the previously committed selection.
- If an old explicit selection exists, it may remain visible until the new drag crosses the threshold; after that, the provisional band should visually replace it so the user does not see two competing selected regions.
- The playhead/progress indicator should remain separate from the provisional region. Shift-drag preview should not move the playhead until the selection is committed.

### Pointer Rules

Normal pointer interaction:

- Normal click on graph: move playhead to clicked time.
- Normal drag on graph or playhead: scrub/move playhead, preserving current behavior.
- Normal click or drag never creates, changes, or clears selection.

Shift pointer interaction:

- Shift-click without meaningful drag: clear explicit selection.
- Shift-drag on graph: create a new explicit selection.
- Shift-drag shows a provisional selected region while dragging, before the button is released.
- New Shift-drag replaces any previous selection.
- Reverse Shift-drag is normalized. Earlier time becomes `selectionStartMs`; later time becomes `selectionEndMs`.
- Shift-drag beyond graph bounds is clamped to `[0, durationMs]`.
- Tiny Shift-drag below the drag threshold is treated as Shift-click and clears explicit selection.

The implementation should use both a pixel threshold and a resulting time threshold. The exact values can be tuned, but tests should avoid relying on a single magic pixel. The important rule is that accidental tiny movement during Shift-click does not create a tiny loop.

For live preview, thresholding should prevent visual flicker:

- `pointerdown` records the anchor but does not immediately draw a provisional region.
- `pointermove` starts drawing only after the gesture exceeds the selection threshold.
- Additional `pointermove` events update the same provisional band; they do not repeatedly commit selection state.
- `pointerup` below threshold clears explicit selection as Shift-click.
- `pointerup` above threshold promotes the current provisional bounds into the committed explicit selection.

## State Model

Store the following state in the visualizer/frontend playback model:

- `selectionStartMs`: start of explicit selection, or empty/null when no explicit selection exists.
- `selectionEndMs`: end of explicit selection, or empty/null when no explicit selection exists.
- `selectionActive`: whether an explicit selection exists.
- `selectionDraftActive`: whether a Shift-drag preview is currently visible.
- `selectionDraftStartMs`: start of the provisional preview, or empty/null when no preview is active.
- `selectionDraftEndMs`: end of the provisional preview, or empty/null when no preview is active.
- `repeatEnabled`: checkbox state.
- `playbackStartMs`: actual start time of the current playback pass.
- `playbackEndMs`: actual end time of the current playback pass.
- `playbackRegionMode`: `"selection"` or `"full"` for diagnostics and tests.

The existing fields still matter:

- `cursorMs`: the visual playhead/progress position.
- `anchorMs`: the restart anchor used after playback completes.
- `progressMs`: the latest displayed progress value.
- `playbackState`: `"stopped"`, `"playing"`, or `"paused"`.
- `progressClockMode`: `"audio"`, `"manual"`, or `"stopped"`.
- `playbackEngine`: `"html"` or `"native"`.

Recommended invariant:

```text
If playbackState is playing, cursorMs/progressMs represent actual playback time.
If playbackState is stopped or paused, cursorMs represents the next start point unless an explicit selection overrides it.
If an explicit selection exists and Play starts a new pass, playback starts at selectionStartMs.
```

## Playback Semantics

### Starting Playback

When the user presses Play:

1. Resolve the effective playback region.
2. If an explicit selection exists, start at `selectionStartMs`.
3. If no explicit selection exists, start at current `anchorMs` or `cursorMs`, preserving current behavior.
4. Set `playbackEndMs`:
   - Explicit selection: `selectionEndMs`.
   - No explicit selection: `durationMs`.
5. If repeat is checked:
   - Explicit selection loops from `selectionEndMs` back to `selectionStartMs`.
   - No explicit selection loops from `durationMs` back to `0`.

### One-Shot Completion

When repeat is unchecked:

- Explicit selection playback stops at `selectionEndMs`.
- Full graph playback stops at `durationMs`.
- On stop, set the playhead to the start of the just-played region:
  - Explicit selection: `selectionStartMs`.
  - No explicit selection: the original playback anchor.
- Send the backend `aqe:play-ended` signal once.

### Indefinite Repeat

When repeat is checked:

- The frontend must not send `aqe:play-ended` at loop boundaries.
- On each boundary, seek back to the start of the effective region.
- The progress indicator should jump from the end boundary back to the start boundary in graph time.
- The Play button remains `Pause`.
- Playback only ends when the user pauses, starts another operation, loads another note, or an unrecoverable playback error occurs.

### Pause And Resume

When paused:

- Freeze the progress indicator at the current actual playback time.
- Keep the current selection unchanged.
- Pressing Play resumes from the frozen progress time if it is inside the effective playback region.
- If the frozen progress time is outside a newly changed explicit selection, restart from `selectionStartMs`.

### Editing Commands And Redraws

Editing commands include destructive-output operations that generate a new audio reference, such as Volume +, Volume -, Slower, Faster, Trim, Standard denoise, Remove pauses, and RNNoise.

When the user clicks an editing command while playback is playing, repeating, or paused:

- Stop playback immediately before the command enters the processing/busy state.
- Cancel active animation frames, pause/clear the HTML audio clock as appropriate, and stop any native playback queue.
- Do not send `aqe:play-ended`; this is a user-initiated operation, not natural playback completion.
- Set the Play button back to `Play` and expose `playbackState: "stopped"` in test state.
- If the edit succeeds and the graph is redrawn for the new audio, clear the explicit selection on the new graph.
- Keep the Repeat checkbox state unchanged for that mounted control unless the control is remounted for a new note; with no explicit selection, Repeat applies to the whole graph.

When the user clicks an editing command while playback is already stopped:

- Do not start playback and do not use the selected region as an edit range.
- Existing selection may remain visible while the old graph is still shown/busy.
- If the edit succeeds and the graph is redrawn, the new graph starts with `selectionActive: false`, empty selection bounds, and `playbackRegionMode: "full"`.
- If the edit fails, leave playback stopped. The existing graph and selection may remain available so the user does not lose context after a failed operation.

### Native Fallback

HTML audio is the preferred implementation path for region playback because it can seek and loop precisely.

For the initial implementation:

- HTML playback should support selected one-shot playback and indefinite repeat.
- Native fallback may support existing full-graph playback from cursor.
- If selected playback cannot be honored natively, prefer a clear non-fatal fallback:
  - one-shot selected playback may render a bounded temporary segment with ffmpeg, or
  - show a warning and play from cursor with existing behavior.

Do not silently claim that a selected region is being repeated if native playback cannot actually enforce the selected boundaries.

## Progress Indicator And Selection Interactions

The playhead/progress indicator always shows playback time. Selection gestures define playback scope. These two concepts should not compete visually.

### Stopped State

| User action | Selection effect | Progress indicator effect |
| --- | --- | --- |
| Normal click inside no selection | No selection change | Moves to clicked time |
| Normal click inside existing selection | Existing selection remains | Moves to clicked time |
| Normal click outside existing selection | Existing selection remains | Moves to clicked time |
| Normal drag | Existing selection remains | Follows drag position |
| Shift-click anywhere | Clears explicit selection | Stays where it was |
| Shift-drag left to right | Shows live provisional band, then replaces selection on release | During drag, do not move indicator; on release move to new `selectionStartMs` |
| Shift-drag right to left | Shows live normalized provisional band, then replaces selection on release | During drag, do not move indicator; on release move to normalized `selectionStartMs` |
| Shift-drag starts inside old selection | Old selection remains until threshold, then live provisional band replaces it visually | During drag, indicator stays fixed; on release moves to new start |
| Shift-drag starts outside old selection | Old selection remains until threshold, then live provisional band replaces it visually | During drag, indicator stays fixed; on release moves to new start |
| Tiny Shift-drag | Clears explicit selection | Stays where it was |

### Playing Without Repeat

| User action | Selection effect | Progress indicator effect | Playback effect |
| --- | --- | --- | --- |
| Normal click | No selection change | Moves/seeks to clicked time | Continue from clicked time if HTML audio can seek |
| Normal drag | No selection change | Follows drag/release | Restart or seek from released time, preserving current behavior |
| Shift-click | Clears explicit selection | Keeps current progress time | Continue playing from current progress time using full-graph region |
| Shift-drag new region | Shows live provisional band, then replaces selection on release | Freeze while dragging; on release move to new start | Stop current pass once selection drag is confirmed; restart from new selection start on release |
| Shift-drag tiny movement | Clears explicit selection | Keeps current progress time | Continue full-graph playback from current progress time |
| Press Play button | Selection unchanged | Freeze at current progress | Pause |

### Playing With Repeat Enabled

| User action | Selection effect | Progress indicator effect | Playback effect |
| --- | --- | --- | --- |
| Boundary reached with explicit selection | Selection unchanged | Jump from `selectionEndMs` to `selectionStartMs` | Continue playing |
| Boundary reached with no explicit selection | No explicit selection | Jump from `durationMs` to `0` | Continue playing |
| Normal click inside active region | Selection unchanged | Seek to clicked time | Continue loop from clicked time |
| Normal click outside explicit selection | Selection unchanged | Prefer clamping to selection start or nearest boundary | Continue looping inside selection |
| Normal drag outside explicit selection | Selection unchanged | Prefer clamping to selected region on release | Continue looping inside selection |
| Shift-click | Clears explicit selection | Keep current progress time | Continue playback, now looping whole graph |
| Shift-drag new region | Shows live provisional band, then replaces selection on release | Freeze while dragging; on release move to new start | Stop current loop once selection drag is confirmed; start looping new selection on release |
| Uncheck Repeat | Selection unchanged | Continue from current time | Finish current pass and stop at region end |
| Check Repeat while one-shot playing | Selection unchanged | Continue from current time | Loop when next boundary is reached |

For normal click outside an explicit selection while repeat is enabled, clamping is recommended because the user has explicitly asked to loop that region. If implementation instead treats the click as "escape this selected loop and play from clicked point", that must be called out as a product decision and tested. The safer first behavior is to keep repeat scoped to the selected region.

### Paused State

| User action | Selection effect | Progress indicator effect | Playback effect |
| --- | --- | --- | --- |
| Normal click | No selection change | Moves to clicked time | Next Play resumes from clicked time if no explicit selection, or from selection start if selection overrides |
| Normal drag | No selection change | Follows drag | Next Play uses released time only when no explicit selection exists |
| Shift-click | Clears explicit selection | Stays where it was | Next Play uses current playhead/full graph |
| Shift-drag new region | Replaces selection | On release moves to new selection start | Next Play starts at new selection start |
| Press Play | Selection unchanged | Starts moving | Resume if current time is valid, otherwise restart from effective region start |

## Region Lengths And Boundary Rules

Test and support these ranges:

- Full graph: no explicit selection, effective `[0, durationMs]`.
- Full explicit selection: Shift-drag from `0` to `durationMs`.
- Near-start selection: e.g. `[0, 150]`.
- Near-end selection: e.g. `[durationMs - 150, durationMs]`.
- Middle selection: e.g. `[500, 1250]`.
- Very short valid selection: the smallest supported duration after thresholding.
- Too-short selection: below threshold, treated as no explicit selection.
- Reverse selection: e.g. drag from 1500 ms to 500 ms.
- Out-of-bounds left/right: clamped.
- Zero-duration or unknown-duration graph: selection disabled and safe no-op.

Use realistic audio durations in tests:

- 0 ms or invalid duration for guard tests.
- 300 ms for short clips.
- 1000 ms for common smoke tests.
- 2000 ms or longer for interaction tests where progress movement must be observable.

## Configuration

Add a setting:

```json
"repeat_playback_by_default": false
```

Behavior:

- The settings dialog exposes a checkbox.
- The inline editor runtime receives this default through `window.__AQE_EDITOR_CONFIG__`.
- Each mounted editor control initializes its Repeat checkbox from the default.
- User changes in one mounted control should apply to that control. They do not need to persist back to settings unless the user changes the setting in the settings dialog.
- Note load/remount resets the checkbox to the configured default.

Schema work:

- Bump `_config_version`.
- Add the field to `config.schema.json`.
- Add the default to `config.json`.
- Regenerate generated Python and TypeScript contracts.
- Update tests that assert config shape.
- Update `CONFIG_SCHEMA.md` when implementation lands.

## Implementation Notes

Expected frontend files:

- `settings_ui/src/editor-inline/EditorControls.svelte`
- `settings_ui/src/editor-inline/actions.ts`
- `settings_ui/src/editor-inline/plot.ts`
- `settings_ui/src/editor-inline/types.ts`
- `settings_ui/src/editor-inline/runtime.ts`
- `settings_ui/src/editor-inline/globals.d.ts`

Expected Python files:

- `addon/anki_audio_quick_editor/editor_ui.py`
- `addon/anki_audio_quick_editor/editor_integration.py`
- `addon/anki_audio_quick_editor/config.schema.json`
- `addon/anki_audio_quick_editor/config.json`
- `addon/anki_audio_quick_editor/config_migration.py`
- Generated contract files after schema updates.

Key frontend helpers to add:

- `selectionForVisualizer(visualizer)`
- `effectivePlaybackRegion(visualizer)`
- `setSelection(visualizer, startMs, endMs, options)`
- `clearSelection(visualizer, options)`
- `draftSelectionForVisualizer(visualizer)`
- `setSelectionDraft(visualizer, startMs, endMs, options)`
- `clearSelectionDraft(visualizer)`
- `commitSelectionDraft(visualizer, options)`
- `setRepeatEnabled(visualizer, enabled)`
- `clampMsToRegion(ms, region)`
- `shouldTreatSelectionGestureAsClick(startEvent, endEvent, startMs, endMs)`

Playback clock updates should compare progress against `playbackEndMs`, not always `durationMs`.

Looping should be implemented with actual audio seeking when using HTML audio:

1. Detect `nextMs >= playbackEndMs`.
2. If repeat is enabled, seek to region start and continue the clock.
3. If repeat is disabled, complete playback.

The manual clock fallback should mirror the same boundary behavior so tests can exercise logic without a real audio element.

## Test Strategy

Statement coverage is not enough for this feature. The risk is not only missing lines; it is incorrect state transitions across input gestures, playback state, region boundaries, and async audio behavior. The implementation should include a behavior matrix that is intentionally redundant across frontend unit tests, Svelte integration tests, Python bridge tests, and real Anki e2e tests.

The target is not "100 percent coverage". The target is:

- Every state transition in the tables above is tested at least once.
- Every playback boundary rule is tested in both one-shot and repeat modes.
- Every pointer gesture class is tested stopped, playing, and paused where meaningful.
- Each high-risk behavior has both a fast frontend test and a real e2e test.

## Frontend Unit Tests

Add or extend tests under `settings_ui/tests/`.

### Selection Math And Plot Helpers

Test:

- `selectionForVisualizer` returns no explicit selection by default.
- `effectivePlaybackRegion` returns `[0, durationMs]` without explicit selection.
- Explicit selection returns normalized `[start, end]`.
- Reverse drag is normalized.
- Negative starts clamp to `0`.
- Ends beyond duration clamp to `durationMs`.
- Unknown or zero duration returns no selectable region.
- Too-short selection clears explicit selection.
- Full explicit selection is valid if it exceeds threshold.
- Pixel-to-ms conversion remains correct after graph bounds scaling.

### State Serialization

Test graph state exposure includes:

- `selectionActive`.
- `selectionStartMs`.
- `selectionEndMs`.
- `selectionDraftActive`.
- `selectionDraftStartMs`.
- `selectionDraftEndMs`.
- `repeatEnabled`.
- `playbackStartMs`.
- `playbackEndMs`.
- `playbackRegionMode`.

These fields should appear in `GraphStateForTest` so e2e tests can assert exact behavior without scraping SVG geometry.

### Repeat Checkbox

Test:

- Default unchecked when config is false or omitted.
- Default checked when config is true.
- User toggling updates visualizer state.
- Busy state disables the checkbox if playback/edit buttons are disabled.
- Note reset returns checkbox to configured default.
- Remounting a field applies current editor runtime config.

### Selection Gestures

Simulate pointer events:

- Shift-click clears selection.
- Shift-click with tiny movement clears selection.
- Shift pointerdown alone does not show a provisional selection.
- Shift pointermove below threshold does not show a provisional selection.
- Shift pointermove past threshold shows a provisional selection before pointerup.
- Additional Shift pointermove updates the provisional selection bounds before pointerup.
- Shift-drag creates selection.
- Shift-drag commits the last provisional bounds on pointerup.
- Shift-drag does not mutate committed selection state until pointerup.
- Shift-drag replaces old selection.
- Old selection remains committed if a Shift-drag is canceled before pointerup.
- Provisional selection visually replaces old selection only after threshold is crossed.
- Shift-drag left-to-right sets expected bounds.
- Shift-drag right-to-left normalizes bounds.
- Shift-drag right-to-left normalizes the provisional preview before pointerup.
- Shift-drag starts inside old selection and replaces it.
- Shift-drag starts outside old selection and replaces it.
- Shift-drag clamps at graph left/right bounds.
- Shift-drag clamps the provisional preview at graph left/right bounds before pointerup.
- `pointercancel` during Shift-drag clears draft state and preserves prior committed selection.
- Losing pointer capture during Shift-drag clears draft state and does not leave stale SVG nodes.
- Normal click does not clear or change selection.
- Normal drag does not clear or change selection.
- Selection gestures call the Python cursor bridge only when implementation intentionally commits a cursor change.

### Progress Clock, One-Shot

Use mocked `requestAnimationFrame`, mocked `performance.now`, and fake audio elements.

Test:

- Explicit selection starts playback at `selectionStartMs`.
- Explicit selection sets `playbackEndMs` to `selectionEndMs`.
- One-shot explicit selection completes at `selectionEndMs`, not `durationMs`.
- On completion, cursor returns to `selectionStartMs`.
- No explicit selection preserves current full-graph behavior.
- Starting with cursor after `selectionEndMs` still starts at `selectionStartMs` when explicit selection exists.
- Starting with cursor inside selection still starts at `selectionStartMs` for a new Play press.
- Pause freezes current progress.
- Resume inside selected region resumes from frozen progress.
- Resume outside selected region restarts from selection start.

### Progress Clock, Repeat

Test:

- Explicit selection loops from end to start.
- Full graph loops from duration to `0` when no explicit selection exists.
- Loop boundary does not send `aqe:play-ended`.
- Multiple loop passes keep `playbackState` as `playing`.
- Progress after wrap is within tolerance of region start.
- Unchecking repeat during playback finishes the current pass and then stops.
- Checking repeat during one-shot playback loops at the next boundary.
- Repeat with a too-short/cleared selection loops the whole graph.
- Audio element `ended` event during repeat seeks back instead of completing, if the event fires at a loop boundary.

### Interactions During Playback

Test:

- Shift-drag while playing freezes visible progress during drag.
- Shift-drag while playing shows a live provisional band before release.
- Confirmed Shift-drag while playing stops the current pass only after the drag threshold is crossed, not on a bare Shift-pointerdown.
- Shift-drag release restarts playback from new selection start.
- Shift-click while playing clears selection and keeps current progress.
- Normal click while playing seeks without changing selection.
- Normal drag while playing preserves existing selection.
- Normal click outside selected repeat region clamps to the selected region, if that product decision is kept.
- Pause during a Shift selection gesture does not leave timers running.
- Playback error during repeat falls back or stops without leaving `playbackState` incorrectly as `playing`.
- Clicking an editing command while selected playback is running immediately stops playback before processing begins.
- Clicking an editing command while selected repeat is looping does not send `aqe:play-ended` and does not leave a repeat timer running.
- Clicking an editing command while paused stops playback instead of preserving a resumable paused loop.
- Clicking an editing command while stopped does not start playback and does not reinterpret the selected region as an edit range.
- Successful edit/redraw after any of the above clears explicit selection on the new graph and reports `playbackRegionMode: "full"`.
- Failed edit after playback was stopped leaves playback stopped and does not leave the Play button as `Pause`.

## Svelte Integration Tests

Extend `settings_ui/tests/editor-inline.integration.test.ts`.

Test through mounted controls instead of direct helper calls:

- Repeat checkbox renders next to Play.
- Repeat checkbox initial state follows `initializeEditorRuntime({ repeatPlaybackByDefault: true })`.
- Shift pointerdown alone does not render selection SVG nodes.
- Shift pointermove beyond threshold renders a provisional selection band before pointerup.
- Provisional selection band updates as the pointer moves before release.
- Graph receives selection SVG nodes only after explicit Shift-drag.
- Committed graph state remains unchanged while only a provisional selection is visible.
- Pointerup promotes the provisional band to committed `selectionActive: true`.
- Pointercancel removes the provisional band and keeps the previous committed selection.
- Selection band disappears after Shift-click.
- Existing Play button starts selected playback when selection exists.
- Existing Play button still starts from cursor when no explicit selection exists.
- Play button label remains `Pause` across loop boundaries.
- Checkbox remains stable during graph redraw.
- Selection state resets on `window.__aqePrepareForNewNote`.
- Processing command clicked during selected playback immediately changes Play back to `Play`, stops the active clock, disables controls for processing, and does not queue `aqe:play-ended`.
- Processing command clicked while stopped with a selection does not start playback, enters busy state normally, and leaves the old selection only until successful redraw.
- Successful `window.__aqeSetVisualizer` after processing clears selection nodes and exposes `selectionActive: false`.
- Failed processing status leaves playback stopped and controls recover without a stuck selected-loop playback state.

## Python Unit Tests

Add or update Python tests under `tests/`.

### Config And Contracts

Test:

- `repeat_playback_by_default` is in config schema.
- `config.json` includes the default.
- Config migration picks up the new default for old user configs.
- Current config version increments.
- Generated Python contracts include the field.
- Generated TypeScript contracts include the field.
- Settings save accepts the new field.
- Settings initial state includes the new field.

### Editor Injection

Test:

- `injection_script` embeds `repeatPlaybackByDefault` from config.
- Default false is embedded when config is missing the field.
- Audio field indices still embed correctly.
- Existing window contract is preserved.
- No raw, unescaped config JSON is interpolated unsafely.

This may require extending `injection_script` to accept a small editor runtime config object instead of only audio field indices.

### Bridge Requests

If `PlaybackRequest` crosses the Python bridge with region fields, test:

- Python tolerates old frontend requests without `endMs` and `loop`.
- Python decodes `cursorMs`, `endMs`, and `loop` defensively.
- HTML playback request with selection marks the session active without starting native playback.
- Pause request during selected HTML playback stores the current cursor.
- Play-ended is ignored at loop boundaries because frontend should not send it.
- Processing command during HTML selected playback calls the existing session stop path before rendering and does not wait for frontend loop completion.
- Processing command during native playback stops the native queue before rendering.
- Processing command while already stopped does not start playback and keeps processing behavior identical to existing edit commands.
- Successful processing/redraw asks the frontend to render fresh graph state whose selection is cleared by the frontend reset logic.

### Native Fallback Policy

If selected native playback is implemented with temporary ffmpeg segments, test:

- Segment render starts at selection start.
- Segment render duration equals selection length.
- Temporary filename includes start/end for diagnostics.
- One-shot native selected playback uses the segment.
- Repeat selected playback refuses native fallback or reports a clear warning if indefinite native repeat cannot be guaranteed.

If native selected playback is not implemented initially, test:

- HTML selected playback never invokes native fake playback.
- HTML failure falls back with a clear state and does not pretend selected repeat is active.

## End-To-End Tests

Add tests under `e2e/test_editor_playback_workflow.py` or a new focused file such as `e2e/test_editor_region_loop_workflow.py`.

Use real Anki editor runtime, generated tones, and the existing HTML audio test driver. E2E tests should assert exact graph state through `window.__aqeGraphStateForTest`.

### E2E Selection Basics

Test:

- Shift-drag creates a middle selection on a 2 second tone.
- Shift-drag displays a visible provisional band before releasing the mouse button.
- Moving farther during the same Shift-drag updates the visible provisional band before release.
- Releasing the mouse commits the last provisional region.
- Shift-drag reverse direction creates the same normalized selection.
- Reverse Shift-drag displays a normalized provisional band before release.
- Shift-click clears selection.
- New Shift-drag replaces old selection.
- Canceling a Shift-drag before release does not replace the old selection.
- Normal click after selection moves cursor but keeps selection.
- Normal drag after selection moves cursor but keeps selection.
- Shift-drag beyond graph left/right clamps to graph bounds.
- Shift-drag beyond graph bounds visibly clamps the provisional band before release.
- Tiny Shift-drag clears selection rather than creating a tiny selected region.

### E2E One-Shot Playback

Test:

- Selected playback starts at selection start.
- Selected playback stops at selection end.
- Progress indicator never goes materially past selection end.
- Completion returns cursor to selection start.
- No explicit selection preserves existing full-graph playback from cursor.
- Explicit full-region selection behaves like full graph but still reports `playbackRegionMode: "selection"`.
- Near-start selection `[0, about 250 ms]` starts at zero and stops around end.
- Near-end selection starts near end and stops at duration.
- Short valid selection plays and stops with tolerance.

### E2E Repeat Playback

Test:

- Repeat checked plus explicit middle selection loops at least three passes.
- Progress jumps from selection end back to selection start within tolerance.
- `playbackState` remains `playing` across loop boundaries.
- Backend/native fake playback is not invoked for HTML repeat.
- Play button stays `Pause` while looping.
- Clicking Play while looping pauses and freezes progress.
- Pressing Play again resumes within the selected region.
- Unchecking Repeat while looping stops at the next selected-region boundary.
- Repeat checked with no explicit selection loops from duration to zero.

### E2E Interactions During Playback

Test:

- While one-shot selected playback is running, Shift-drag a new region; playback restarts from the new region start.
- While one-shot selected playback is running, the new region is visible during the drag before playback restarts on release.
- While repeat selected playback is running, Shift-drag a new region; looping restarts in the new region.
- While repeat selected playback is running, provisional selection preview appears while progress is frozen and before the new loop starts.
- While repeat selected playback is running, Shift-click clears explicit selection; playback continues and future loops use the whole graph.
- While selected playback is paused, Shift-drag a new selection; next Play starts at the new selection start.
- While selected playback is paused, Shift-click clears selection; next Play uses current playhead/full graph.
- Normal click while selected repeat is playing seeks or clamps according to the final product rule, and selection remains unchanged.
- Normal drag while selected repeat is playing preserves selection and does not corrupt loop boundaries.

### E2E Multiple Audio Fields In One Note

Test:

- Create a note with two supported audio fields using different filenames and different durations.
- Verify one control surface and one graph state exists per audio field, with each `ord` reporting its own `sourceFilename`, `durationMs`, cursor, selection, repeat state, and audio clock source.
- Create a selection and enable Repeat in the first field; verify the second field still has no explicit selection and keeps its configured Repeat default.
- Create a different selection in the second field; verify the first field selection is preserved but not mutated by second-field gestures.
- Start repeat playback in the first field, then press Play in the second field; only one field should remain playing, the first field's timers/audio should stop, and the second field should become the active playback field.
- Start selected one-shot playback in the second field, then press Play in the first field; the second field should stop or pause according to the final single-active-playback policy, and no overlapping audio clocks should continue advancing.
- While the first field is looping, click Graph/Redraw on the second field; the first field should continue only if redraw is scoped to the second field, and the second field should not inherit the first field's selection or repeat state.
- While the first field is looping, run a processing command on the second field; playback should stop if processing globally disables controls, and both field graph states should end in a non-busy, non-playing state after the operation completes.
- With one field selected and the other unselected, normal click and normal drag in either graph should affect only that field's cursor.
- Bridge assertions should confirm `window.__aqeActiveField`, `PlaybackRequest.ord`, and backend session `field_index` always match the field whose Play button was pressed.

### E2E Browser Note Switching

Test:

- Open the Anki Browser with two notes that each contain one audio field with different source filenames; create a selected repeat loop on note A, then select note B.
- Note switching should stop note A playback, clear note A timers, and mount/render note B controls with no stale explicit selection.
- Note B graph state should report note B's `sourceFilename`, `durationMs`, `selectionActive: false`, and Repeat initialized from the configured default, not from note A's checkbox state.
- Start selected playback on note B, then switch back to note A; note B playback should stop and note A should not restore its old explicit selection unless selection persistence is intentionally added later.
- Use two notes with the same field index but different audio filenames; switching notes should update the audio clock `src`, graph labels, duration, and source filename without reusing stale HTML audio state.
- Use one note with a supported audio field and one note with no supported audio; switching to the unsupported note should remove or hide controls and stop any active loop without leaving a busy or playing graph state.
- Use one note with two audio fields and another note with one audio field; switching should dispose extra field controls from the previous note and keep `__aqeGraphStateForTest` scoped to currently mounted fields only.
- While note A is looping, trigger a browser note change quickly followed by Play on note B; stale callbacks from note A should not send `aqe:play-ended`, restart playback, or overwrite note B's cursor/session state.
- After several A/B switches, fake native playback attempts and HTML audio test driver state should show at most one active playback source, and it should belong to the currently selected note.
- Closing the Browser while a selected repeat loop is running should dispose the editor runtime, stop playback, and leave no active animation frame or audio test-driver timer.

### E2E Settings Default

Test:

- Open settings.
- Enable repeat by default.
- Save.
- Open editor with audio note.
- Graph controls mount with Repeat checked.
- Shift-drag selection and Play loops selected region without manually checking Repeat.
- Disable repeat by default.
- Save.
- Remount editor controls.
- Repeat starts unchecked.

### E2E Reset And Lifecycle

Test:

- Analyze graph, create selection, start repeat, then switch note: playback stops and new note has no stale selection.
- Create selection while playback is stopped, click an editing button such as Volume +, wait for successful redraw, and assert the new graph has `selectionActive: false`, empty selection bounds, and `playbackRegionMode: "full"`.
- Start one-shot selected playback, click an editing button such as Volume + during playback, and assert playback stops immediately, the Play button returns to `Play`, no native/HTML timer continues, and successful redraw has no selection.
- Start selected repeat playback, click an editing button such as Remove pauses during a loop, and assert no `aqe:play-ended` is sent at the processing boundary, playback does not resume after processing, and the redrawn graph has no selection.
- Pause selected playback, click an editing button, and assert the paused state is converted to stopped before processing and cannot be resumed from the old region.
- If an editing command fails after stopping playback, assert playback remains stopped, controls recover, and the Play button is not stuck as `Pause`.
- Create selection, perform an edit action that redraws graph: playback stops; selection resets on successful redraw.
- Create selection, Undo: graph redraws and selection resets.
- Start selected playback, click Graph/Redraw: playback stops and no stale timers continue.
- Missing or unsupported media error path does not leave repeat or selection UI stuck in a busy state.
- Closing editor during selected repeat cleans up playback timers and temporary state.

## Test Tolerances

Use explicit tolerances because real Qt/webview timing is noisy:

- Cursor/progress start tolerance: existing `PLAYBACK_INTERVAL_TOLERANCE_MS` or tighter where current tests already prove stable.
- Boundary stop tolerance: allow a small overshoot, but assert it is far below the next meaningful region.
- Loop wrap tolerance: after wrap, assert progress is near start and less than `selectionStartMs + tolerance`.
- No-progress-while-paused tolerance: assert frozen progress changes by less than existing pause tolerance.

Avoid tests that only check labels. For playback correctness, assert:

- `audioClockCurrentMs`.
- `progressMs`.
- `cursorMs`.
- `playbackStartMs`.
- `playbackEndMs`.
- `selectionStartMs`.
- `selectionEndMs`.
- `selectionDraftActive`.
- `selectionDraftStartMs`.
- `selectionDraftEndMs`.
- `playbackRegionMode`.
- `playbackState`.
- `progressClockMode`.

## Acceptance Criteria

The feature is complete when:

- The user can create a selected region only with Shift-drag.
- The user sees the selected region update live during Shift-drag before releasing the mouse button.
- The user can clear explicit selection with Shift-click.
- Normal graph click and drag behavior remains compatible with the current app.
- Play honors explicit selection when present.
- Repeat loops the effective playback region indefinitely until user action stops it.
- Progress indicator starts, moves, wraps, pauses, resumes, and stops at the correct times.
- Settings can make Repeat checked by default.
- Unit, integration, and e2e tests cover the behavior matrix above.
- `python3 scripts/dev.py check` passes.
- `python3 scripts/dev.py test-e2e` passes.

## Codex Implementation Plan

### Summary

- Implement v1 in the existing inline editor state machine with dataset-backed selection/repeat state and expanded `GraphStateForTest` diagnostics.
- Add live Shift-drag selection preview state so users see the provisional region before release.
- Add `repeat_playback_by_default: false`, bump config version to 8, regenerate contracts, rebuild templates, and update docs.
- HTML audio is authoritative for selected playback and repeat. Native fallback remains existing full-graph/cursor playback only.
- Use the recommended UX from this feature plan: Shift-only region editing, normal gestures preserve selection, and selected repeat clamps normal seeks to the selected region.

### Test-First Sequence

- Config/contracts: update Python and Svelte settings tests for config version 8 and `repeat_playback_by_default`; assert generated Python/TS contracts include the field.
- Frontend unit tests: cover selection normalization/clamping, live draft preview state, reverse drag, zero duration, min thresholds (`4px`, `50ms`), repeat defaults/toggling, `GraphStateForTest` fields, one-shot boundaries, repeat wrapping, pause/resume, and selected HTML failure.
- Svelte integration tests: drive actual controls for Repeat rendering, pointermove-before-pointerup provisional selection band, Shift-drag commit, Shift-click clear, normal click/drag preservation, selected Play start, loop boundary button state, edit-command stop/reset behavior, and note reset.
- Python bridge tests: tolerate optional playback request fields (`endMs`, `loop`, `regionMode`); verify HTML selected requests do not render native segments and edit commands stop active playback before rendering.
- E2E: add `e2e/test_editor_region_loop_workflow.py` for live preview-before-release, create/reverse/clear/replace selection, selected one-shot, 3-pass repeat, pause/resume, clear-while-looping, redraw/note-switch lifecycle, and settings default round trip.
- E2E: include edit-command scenarios for stopped, playing, repeating, paused, success, and failure paths.
- E2E: include multi-field same-note coverage and Browser note-switching coverage to prove playback, selection, repeat, and bridge state stay scoped to the active field and current note.

### Implementation Changes

- Extend `EditorRuntimeConfig`, `PlaybackRequest`, and `GraphStateForTest` with repeat/region fields, including draft-selection diagnostics for tests.
- Store visualizer state as `selectionActive`, `selectionStartMs`, `selectionEndMs`, `selectionDraftActive`, `selectionDraftStartMs`, `selectionDraftEndMs`, `repeatEnabled`, `playbackStartMs`, `playbackEndMs`, and `playbackRegionMode`.
- Add helpers: `selectionForVisualizer`, `effectivePlaybackRegion`, `setSelection`, `clearSelection`, `setSelectionDraft`, `clearSelectionDraft`, `commitSelectionDraft`, `setRepeatEnabled`, `clampMsToRegion`, and `shouldTreatSelectionGestureAsClick`.
- Add a Repeat checkbox after Play and an SVG selection layer with one translucent band plus boundary lines.
- Route Shift pointer events to selection preview/commit logic; normal pointer handling continues to scrub/cursor behavior.
- Update playback clocks to compare against `playbackEndMs`; one-shot sends `aqe:play-ended` once, repeat seeks back without notifying Python.
- Stop active playback synchronously before any processing command enters busy state, and clear explicit selection when a successful processing redraw installs the new graph.
- If explicit selection exists and HTML audio is unavailable/fails, stop UI playback and show a warning; do not silently queue native selected playback.

### Config, Build, Docs

- Update `config.schema.json`, `config.json`, `CURRENT_CONFIG_VERSION`, settings UI defaults, and settings save/initial-state tests.
- Change `injection_script` to emit `{ audioFieldIndices, repeatPlaybackByDefault }`, with false fallback from editor config.
- Run `python3 scripts/dev.py contracts-generate`, then `python3 scripts/dev.py build`.
- Update `CONFIG_SCHEMA.md`; use `$doc-maintain` after implementation.

### Verification

- Fast checks: targeted Python tests, targeted Vitest editor-inline tests, `contracts-check`, and `config-schema`.

### Assumptions

- No persisted selection across note loads.
- Explicit full-range Shift selection is valid and reports `playbackRegionMode: "selection"`.
- Native selected repeat is out of scope for v1.
