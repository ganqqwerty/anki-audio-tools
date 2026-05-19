# Editor Region Resize Handles Design

## Goal

Make selected audio regions in the inline editor resizable after creation. Users currently hold Shift and drag across the graph to create or replace a region. The new behavior should let them refine a committed region by dragging visible edge handles.

## Current Context

The inline editor frontend already has a narrow selected-region flow:

- `settings_ui/src/editor-inline/selection-state.ts` normalizes and validates selection ranges.
- `settings_ui/src/editor-inline/selection-gestures.ts` handles Shift-drag selection creation and normal cursor scrubbing.
- `settings_ui/src/editor-inline/selection-controller.ts` writes selection and draft state to visualizer dataset fields, then redraws.
- `settings_ui/src/editor-inline/visualizer-renderer.ts` renders the selected band and edge lines.
- Delete-region and selected playback behavior already consume the committed `selectionStartMs` and `selectionEndMs` values from visualizer state.

No Python bridge or backend contract change is required for resizing itself. The resize feature changes frontend interaction and state transitions; existing Python actions should receive the resized region through the current visualizer state.

## Chosen UX

Use visible edge handles.

When a committed selection exists, the graph shows two small handles aligned with the selection start and end. Dragging a handle with normal, unmodified pointer input resizes that edge. Shift is not required because the handle itself is the mode signal.

Existing graph interactions remain unchanged:

- Shift-drag on graph space creates or replaces the selected region.
- A short Shift-click clears the selected region.
- Normal drag on graph space scrubs the cursor.
- Normal drag on a handle resizes the selected region.

The handles are shown only for committed selections. Draft selections created during Shift-drag do not show resize handles until committed.

## Considered Alternatives

Visible edge handles were chosen because they are discoverable and precise.

Rejected alternatives:

- Shift-drag nearest edge: visually cleaner, but harder to discover and easier to trigger unexpectedly.
- Handles plus dragging the selected band to move the whole region: useful, but it adds conflict risk with normal cursor scrubbing. Moving the whole region is out of scope for this pass.

## Resize Behavior

Dragging the left handle changes only the selection start. Dragging the right handle changes only the selection end.

During drag:

- The resize is represented as draft selection state.
- The existing selection remains the stable committed value until release.
- The graph redraws continuously so the user sees the proposed resized region.
- Escape, pointer cancel, lost pointer capture, or window blur cancels the draft and preserves the original committed selection.

On release:

- The draft range is committed.
- The result is clamped to the audio duration.
- The existing minimum selection duration of 50 ms is preserved.
- Handles do not swap roles. If the dragged edge crosses the opposite edge, it clamps at the minimum duration boundary instead of inverting the selection.
- Playback region dataset fields are updated to the committed resized selection.

## Playback Behavior

Resize must treat selected playback as live state, not just static selection data.

If playback is stopped:

- Resizing commits the new region and keeps playback stopped.
- The play button remains `Play`.
- The playback region start/end update to the resized selection.
- The cursor/progress indicator moves to the resized selection start after commit, matching current selection-commit behavior.

If selected playback is playing:

- Pointer-down on a handle temporarily interrupts visual/audio progress while the user drags.
- The progress indicator freezes during the resize gesture.
- On release, playback restarts from the resized selection start.
- The play button remains `Pause`.
- `playbackStartMs`, `playbackEndMs`, audio clock position, and progress indicator reflect the resized region.
- If the resized end is earlier than the pre-resize progress, playback still restarts from the resized selection start instead of completing immediately.

If selected playback is paused:

- Resizing keeps playback paused.
- The play button remains `Play`.
- The committed resized region becomes the active playback region.
- `resumeRequiresRestart` is set so the next Play starts from the resized selection start rather than stale paused progress.

If repeat is enabled:

- Loop boundaries follow the resized selection after commit.
- A forced or natural boundary wrap should use the updated start and end values.

## Architecture

Keep the feature within the existing inline-editor frontend boundary.

Expected module responsibilities:

- `EditorControls.svelte`: renders SVG handle elements with stable test IDs and attaches handle pointerdown events.
- `visualizer-renderer.ts`: positions, shows, and hides handles alongside existing selection band and edge rendering.
- `selection-state.ts`: owns pure resize range math, including clamping, minimum duration enforcement, and preserving the opposite edge.
- `selection-controller.ts`: exposes draft/commit helpers for resized selection state using the existing dataset fields.
- `selection-gestures.ts`: owns the new resize gesture lifecycle and playback interruption/restart rules.
- `actions.ts`: wires the new gesture through existing dependency factories without taking on resize logic.
- `styles.css`: gives handles a clear pointer target and resize cursor without obscuring the graph.

No backend modules should be modified for resize behavior unless implementation discovers a pre-existing bridge defect. The existing region delete request should already read the updated selection values.

## Accessibility And Input

The handles should be large enough to drag reliably in the Anki webview. They should use cursor feedback such as `ew-resize` and remain visible in light and dark modes through `currentColor`.

Keyboard resizing is out of scope for this pass. The feature should not regress existing keyboard behavior such as Escape canceling a selection gesture or Backspace deleting a selected region.

## Testing

Use test-first implementation where practical. The e2e suite is the primary protection because the risky behavior spans pointer events, SVG rendering, audio-clock progress, and play button state.

### Pure Unit Tests

Add tests for resize math:

- Resize start preserves end.
- Resize end preserves start.
- Start and end clamp to audio duration.
- Dragged edge cannot cross the opposite edge.
- Minimum 50 ms duration is enforced.
- Invalid or zero-duration audio produces no committed selection.

### E2E Gesture Tests

Add a focused resize gesture suite:

- Handles appear only after a committed selection exists.
- Handles hide when the selection is cleared.
- Left handle drag changes only `selectionStartMs`.
- Right handle drag changes only `selectionEndMs`.
- Handle drag without Shift resizes.
- Graph body drag without Shift still scrubs the cursor.
- Shift-drag graph body still creates or replaces a selection.
- Pointer cancel or Escape during handle drag restores the original committed selection.

### E2E Playback Tests

Add playback-specific resize coverage:

- Stopped playback plus right-edge resize updates `selectionEndMs`, `playbackEndMs`, and keeps play button as `Play`.
- Stopped playback plus left-edge resize updates `selectionStartMs`, `playbackStartMs`, moves cursor/progress to the new start, and keeps play button as `Play`.
- Playing selected region plus handle pointer-down freezes progress while dragging.
- Playing selected region plus release restarts playback from the resized selection start and keeps play button as `Pause`.
- Paused selected region plus resize keeps state paused, keeps play button as `Play`, sets `resumeRequiresRestart=true`, and next Play starts from resized selection start.
- Repeat enabled plus resized end uses the new end boundary when wrapping.
- Resizing the end earlier than current progress restarts from the resized selection start on release.

### E2E Backend Consumer Tests

Protect consumers of the resized range:

- Delete-region after resize removes the resized range, not the original range.
- Existing graph-default behavior still supports selection creation and resize.
- Multiple audio fields keep resize state scoped per field.
- Starting playback in another field still stops playback in the previous field after resizing.

## Risks

The highest risk is playback state drift: resize changes the selected region while the audio clock, cursor, play button, and repeat loop all have cached state. The design avoids ambiguous mid-play mutations by freezing progress during drag and restarting from the committed resized start on release.

The second risk is gesture conflict. Restricting resize to explicit handle elements keeps normal graph scrubbing and Shift-drag creation stable.

## Out Of Scope

- Moving the entire selected region by dragging the band.
- Keyboard-based resize nudging.
- Persisting selections between notes or sessions.
- Backend contract changes for resize-specific commands.
