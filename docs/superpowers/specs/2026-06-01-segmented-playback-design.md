# Segmented Playback Design

## Goal

Add a graph-based practice mode for shadowing phrase endings and progressively expanding toward the full phrase.

The learner selects a phrase region on the graph, places temporary segment start markers under that region, then uses Practice playback to loop suffixes:

1. shortest suffix first,
2. repeat the current suffix until the learner advances,
3. move left marker by marker until the selected playback region covers the whole phrase.

This feature is a practice aid only. It must not modify media, note fields, config, or persisted metadata.

## Current Context

The inline editor already has the important primitives:

- Graph selection creates a committed playback region.
- Graph zoom uses a per-visualizer time viewport and maps graph pointer positions through the current visible viewport.
- Selected-region playback uses existing Play behavior, repeat, repeat pause, progress clocks, and Python playback requests.
- Region state is stored per visualizer and is already scoped by field.
- The Play split menu owns repeat-related controls.
- Python playback already accepts ordinary selected-region requests through `cursorMs`, `endMs`, `regionMode: "selection"`, and `loop`.

The new feature should reuse these primitives instead of adding a separate media pipeline.

## Chosen UX

Segmented playback is graph-only. A graph and committed phrase selection are required.

Basic flow:

1. The learner selects the whole phrase range on the graph.
2. The learner opens the Play split menu and enables segment editing.
3. A thin marker row appears under the graph for the selected phrase range.
4. Left-clicking the marker row adds a temporary segment start marker.
5. Left-clicking an existing marker removes it.
6. The learner starts `Practice` from the Play split menu.
7. Practice starts at the rightmost marker and loops the suffix from that marker to the original phrase end.
8. `Next` moves one marker left, making the suffix longer.
9. `Previous` moves one marker right, making the suffix shorter.

The active suffix is shown by moving the normal visible graph selection to the current marker-to-phrase-end range. This is intentional: the learner sees the same selected region UI that ordinary selected playback already uses.

Practice does not auto-advance. The current suffix loops until the learner presses `Next`, `Previous`, pauses practice, clears markers, or exits the mode.

## Considered Alternatives

### Marker Row Plus Existing Selection Driver

Chosen. Segment markers are edited in a dedicated row, and Practice drives the existing selection and playback machinery.

This keeps the mental model small: segment practice is automated selected-region playback.

### Separate Segment Highlight

Rejected for v1. It would avoid mutating the visible selection during practice, but it creates a second region concept on the graph and makes playback state harder to read.

### Saved Selection Presets

Rejected for v1. It is more general, but it turns a focused practice workflow into region management.

## State Model

Segment state is temporary editor-session state, scoped by field and current source filename.

It contains:

- `baseRegion`: the original phrase selection captured when segment editing or practice starts.
- `markers`: sorted start times inside `baseRegion`.
- `activeMarkerIndex`: the marker currently driving practice, counted in sorted marker order.
- `editing`: whether the marker row is accepting left-click marker edits.
- `practiceState`: stopped, playing, or paused.

The active suffix is derived:

- `startMs = markers[activeMarkerIndex]`
- `endMs = baseRegion.endMs`

`baseRegion` must remain stable while practice moves the visible selection to each derived suffix. Selection changes initiated by the practice controller do not replace `baseRegion`; they are just the current suffix projection.

If the learner manually changes or clears the graph selection after placing markers, the segment state resets and the old markers disappear. The implementation must not remap old markers into the new selection and must not keep markers that now lie outside the new selection. The learner can then start a fresh segment setup from the new selection.

Markers are cleared when:

- the source filename changes,
- the graph is reset or redrawn for another source,
- the editor closes,
- the user clears markers,
- the active field changes in a way that invalidates the visualizer state.

Markers are not persisted to note data, config, local storage, or media files in v1.

## Controls

Controls live in the Play split menu, not as a new toolbar button.

The segment section contains:

- `Edit segments`: toggles marker-row editing for the current graph selection.
- `Practice` / `Pause practice`: starts or pauses suffix practice.
- `Previous`: moves toward shorter suffixes.
- `Next`: moves toward longer suffixes.
- `Clear markers`: removes markers for the active field/source.

The marker row lives under the graph and is the direct editing surface:

- It aligns horizontally with the graph plot area.
- It uses the current graph time viewport for click-to-time conversion and marker positioning.
- It shows marker ticks at their time positions.
- It shades the active suffix from the active marker to `baseRegion.endMs`.
- Markers cannot be placed outside `baseRegion`.
- Markers outside the current zoom viewport remain in state but are not shown until panning or zooming brings them back into view.
- If `baseRegion` extends beyond the current zoom viewport, the row clips the visible phrase/active-suffix shading to the viewport while preserving the full stored `baseRegion`.
- A click close to an existing marker removes that marker; otherwise the click adds one.

Practice requires at least one marker and a valid `baseRegion`. With no valid phrase selection or no markers, Practice remains disabled or reports a concise status.

## Playback Behavior

Practice playback is mutually exclusive with normal Play playback.

Starting Practice while normal Play playback is active stops normal playback first, then starts the practice suffix. Clicking normal Play while Practice is active pauses practice and must not start a second playback in the same action.

Practice behavior:

- Starting Practice chooses the rightmost marker by default.
- It sets the visible selection to `[marker, baseRegion.endMs]`.
- It may pan or zoom the graph viewport only through the existing viewport helpers. It must not replace `baseRegion` when the viewport changes.
- It starts selected-region playback with repeat enabled for the practice loop.
- It reuses the existing repeat pause setting from the Play menu.
- It does not add a separate segment pause setting.
- `Pause practice` pauses the current practice loop.
- `Next` moves one marker left, updates the visible selection, and continues or starts looping that suffix.
- `Previous` moves one marker right, updates the visible selection, and continues or starts looping that suffix.
- Reaching the leftmost marker does not auto-stop; `Next` is disabled or no-ops there.
- Reaching the rightmost marker disables or no-ops `Previous`.

Completion never auto-advances. Natural audio boundaries loop the active suffix through the existing repeat behavior.

## Architecture

Keep the feature in the inline-editor frontend unless implementation uncovers a pre-existing bridge defect.

Expected modules:

- `segment-practice-state.ts`: pure helpers for marker normalization, add/remove hit testing, active marker traversal, base-region validation, and derived suffix regions.
- `segment-practice-controller.ts`: coordinates marker-row gestures, Play menu commands, selection updates, mutual exclusion with normal playback, and practice state transitions.
- `EditorControls.svelte` or a small child component: renders the marker row under the visualizer and wires pointer events.
- `PlaySplitButton.svelte` and split menu state modules: add the segment controls to the existing Play menu.
- `time-viewport.ts`, `plot.ts`, `visualizer-renderer.ts`, or related state helpers: reuse viewport-aware millisecond/pixel conversion, publish marker-row geometry, and apply active suffix classes without shifting the graph layout.
- `test-contract.ts`: expose marker state, base region, active suffix, and practice state for e2e assertions.

Existing playback modules continue to own actual playback requests, progress clocks, repeat wrapping, pause/resume, and native/html routing. Practice should update the normal selection before invoking existing playback actions.

Python should continue receiving ordinary selected-region playback requests. No new audio operation, media render command, or persistent schema is needed for v1.

## Data Flow

When editing starts:

1. Read the current committed graph selection.
2. Capture it as `baseRegion`.
3. Show the marker row aligned to the graph plot.
4. Initialize or retain markers only if they are valid for the same field/source/base region.

When the marker row is clicked:

1. Convert the click position to milliseconds.
2. Use the current visualizer time viewport for the conversion.
3. Clamp to `baseRegion`.
4. Reject or no-op if the click maps outside the visible portion of `baseRegion`.
5. Remove a nearby marker or add a new marker.
6. Sort and deduplicate markers.
7. Redraw the row and update menu button availability.

When the graph viewport changes through zoom, pan, fit, zoom-to-selection, or playback-follow behavior:

1. Keep `baseRegion`, markers, and `activeMarkerIndex` unchanged.
2. Recompute marker row positions from marker times using the new viewport.
3. Hide marker ticks and suffix shading portions that fall outside the visible viewport.
4. Keep practice running unless the underlying field/source/selection state became invalid.

When Practice starts:

1. Stop any normal playback.
2. Choose the rightmost marker.
3. Derive the suffix region.
4. Set the normal visible selection to that suffix.
5. Start existing selected-region repeat playback.

When Next or Previous runs:

1. Move the active marker index if possible.
2. Derive the new suffix.
3. Set the normal visible selection to that suffix.
4. If the new suffix is partly or fully outside the current viewport, bring it into view using existing viewport behavior rather than changing stored marker times.
5. Restart or continue selected-region repeat playback for the new bounds.

When the committed graph selection changes manually:

1. If the change did not come from the practice controller, stop practice state.
2. Clear markers and `activeMarkerIndex` for that field/source.
3. Treat the new selection as eligible for a fresh `baseRegion` only when the learner re-enters segment editing or starts a new setup.

When normal Play is requested during Practice:

1. Pause practice state.
2. Leave the visible suffix selection in place.
3. Do not start a separate normal playback from the same click.

The marker row must never use full-duration ratios when the graph is zoomed. Time-to-x and x-to-time calculations should go through the same viewport-aware helpers used by selection, cursor, and zoom behavior.

## Error Handling

All segment commands should re-read current visualizer state before acting.

Reject or no-op with a concise status when:

- no graph is active,
- no committed phrase selection exists,
- the selection is too short,
- the source filename changed,
- markers are missing,
- markers are outside the captured base region,
- the editor is busy,
- playback state is stale or belongs to another field.

Stale practice state must not trigger playback against a new audio file. Clearing stale markers is safer than trying to remap them.

## Testing

Use focused pure tests for state math and e2e tests for graph interaction and playback behavior.

### Unit Tests

Add tests for:

- marker add/remove hit testing,
- marker sorting and deduplication,
- marker clamping inside `baseRegion`,
- rejecting markers outside `baseRegion`,
- viewport-aware click-to-marker conversion,
- viewport-aware marker-to-x positioning,
- hiding markers outside the current viewport without deleting them,
- deriving suffix region from active marker to `baseRegion.endMs`,
- choosing the rightmost marker as the initial practice marker,
- Next moving left toward longer suffixes,
- Previous moving right toward shorter suffixes,
- retaining `baseRegion` while active suffix selection changes.

### Frontend Interaction Tests

Add Svelte or DOM-level tests where practical for:

- Play menu segment controls appearing only when graph selection prerequisites are met,
- marker row visibility while editing,
- marker tick rendering,
- active suffix shading,
- disabled states for Practice, Next, Previous, and Clear markers.

### E2E Tests

Add e2e coverage for:

- selecting a phrase, enabling segment editing, and placing markers with left click in the marker row,
- zooming into the phrase and placing markers at the correct zoomed time positions,
- panning or zooming after placing markers without losing marker state,
- clipping marker ticks and active suffix shading when part of `baseRegion` is outside the viewport,
- clicking an existing marker removes it,
- Practice starts from the rightmost marker,
- Practice sets the visible selection to marker-to-phrase-end,
- Practice or Next/Previous brings the active suffix into view when needed without changing marker times,
- practice playback loops using the existing repeat pause setting,
- Next moves one marker left and expands the selected playback region,
- Previous moves one marker right and shrinks the selected playback region,
- Practice does not auto-advance after playback boundary loops,
- starting Practice stops active normal Play playback,
- starting normal Play pauses active Practice playback,
- manually changing the phrase selection after placing markers clears those markers instead of remapping them,
- markers are scoped by field in multi-audio notes,
- markers clear when the source audio changes or graph resets.

## Out Of Scope

- Automatic audio segmentation suggestions.
- Text-aware word alignment.
- Persisting markers across editor sessions.
- General chunk playback from marker to marker.
- Auto-advance after N loops.
- A separate toolbar button for segmented playback.
- Python backend audio processing changes.
