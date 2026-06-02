# Segmented Playback Refactors And Tests

## Purpose

This document describes the small refactorings and additional tests needed to implement segmented playback cleanly and simply. It complements `2026-06-01-segmented-playback-design.md`; it does not change the product behavior.

The goal is to add segment practice by reusing the existing graph selection, viewport, repeat playback, and test-contract machinery. The implementation should avoid a second playback pipeline, avoid persisted segment data, and avoid a broad rewrite of the inline editor.

## Current Shape To Preserve

- Graph selection is already a committed playback region.
- `time-viewport.ts` and `plot.ts` already provide viewport-aware time and x-coordinate mapping.
- `selection-controller.ts` owns committed and draft selection state.
- `playback-model.ts`, `playback-controller.ts`, and `playback-actions.ts` already own playback planning, repeat boundaries, repeat pause, and html/native routing.
- `PlaySplitButton.svelte` already owns repeat controls and is the natural home for practice controls.
- `test-contract.ts` already exposes graph, viewport, selection, repeat, playback, and cursor state for Vitest and e2e assertions.

Segmented playback should sit on top of these pieces. It should not add Python commands or backend schemas in v1.

## Refactorings

### 1. Extract Viewport-Aware Graph Overlay Geometry

The marker row needs the same viewport-aware conversions already used by selection and cursor behavior:

- client x to milliseconds,
- milliseconds to SVG/viewbox x,
- milliseconds to CSS px,
- clipping a time range to the current viewport,
- detecting whether a marker is visible in the current viewport.

Keep this as a small helper, either in `plot.ts` if the functions are general enough or in a new `graph-overlay-geometry.ts` if they are DOM-overlay specific. The helper should reuse `cursorMsFromEvent`, `xForMs`, `graphPixelBounds`, `svgViewBoxScale`, `readVisualizerTimeViewport`, and `msVisibleInViewport` rather than duplicating full-duration ratio math.

This refactor should be verified before adding segment UI. Existing selection, cursor, zoom, and renderer tests should continue to pass unchanged.

### 2. Add Pure Segment State Helpers

Create `segment-practice-state.ts` for data-only behavior:

- normalize, sort, clamp, and deduplicate markers,
- add or remove a marker using hit-test tolerance,
- validate `baseRegion` against duration/source identity supplied by the controller,
- choose the initial rightmost marker,
- move active marker left or right,
- derive active suffix `{ startMs, endMs, mode: "selection" }`,
- report disabled states for Practice, Next, Previous, and Clear markers.

This file should not touch DOM, Svelte state, playback, Anki, or browser globals. Keeping it pure keeps the feature understandable and gives high-confidence unit tests before UI work.

### 3. Add A Minimal Selection Mutation Origin

Practice updates the visible selection to each active suffix. Manual user selection changes should clear segment state, but practice-driven selection changes must not replace `baseRegion` or clear markers.

Add the smallest origin mechanism that supports that distinction. Preferred shape:

- extend the public selection wrapper functions in `actions.ts` with an optional source such as `{ origin?: "user" | "segment-practice" | "system" }`,
- default to `"user"` for gesture-facing calls and pass `"system"` from initialization or graph lifecycle code when needed,
- let the segment controller call selection updates with `"segment-practice"`,
- notify/reset segment state only for user-origin selection changes.

Do not introduce a general event bus unless another existing module already needs one. The segment controller can own the reset logic, and selection wrappers can call one narrow hook.

### 4. Keep Practice Playback As Selected-Region Playback

Add a small practice playback adapter in `segment-practice-controller.ts` rather than a new media pipeline.

The adapter should:

- stop or pause active normal playback through existing playback actions,
- set the visible selection to the active suffix,
- force looped playback for the practice request without saving a new repeat default,
- preserve or restore the learner's ordinary repeat setting when practice exits,
- call existing selected-region playback behavior,
- use existing repeat pause behavior,
- rely on `playbackRequestForStart`, `startEditorHtmlPlayback`, `sendPlaybackRequest`, and `playbackEngineFor` patterns instead of creating a segment-specific request type.

The only new state should be practice mode state: stopped, playing, or paused. Python should still see ordinary selected-region playback requests.

### 5. Decompose The Play Split Menu Before Adding Controls

`PlaySplitButton.svelte` currently contains the primary button, repeat controls, repeat pause controls, default-save behavior, and the menu body. Adding segmented playback directly there would make the component harder to reason about.

Before adding practice controls, extract small children:

- `PlayRepeatOptions.svelte` for repeat toggle, pause input/slider, presets, and default-save wiring,
- `PlayPracticeOptions.svelte` for Edit segments, Practice/Pause, Previous, Next, and Clear markers.

Keep ownership clear: `PlaySplitButton.svelte` owns popover open/close and primary Play dispatch; child components own their local menu controls. This keeps the menu change mechanical and reduces the chance of breaking existing repeat behavior.

### 6. Render Marker Row As A Graph Overlay Sibling

Add a small marker row component next to the graph plot content, not as a separate graph system. It should be a sibling of the existing overlay/scroller pieces inside `GraphVisualizer.svelte`, aligned by the shared plot geometry.

The row should:

- render only while segment editing or practice state is active,
- use viewport-aware geometry from the helper refactor,
- clip base-region and active-suffix shading to the visible viewport,
- hide off-viewport markers without deleting them,
- dispatch marker clicks to the segment controller,
- avoid shifting the graph layout when shown or hidden.

The component should not own marker math. It should receive already-normalized state and call controller functions.

### 7. Extend The Test Contract Intentionally

Extend `GraphStateForTest` and `test-contract.ts` only with fields needed for assertions:

- `segmentEditing`,
- `segmentPracticeState`,
- `segmentBaseStartMs`,
- `segmentBaseEndMs`,
- `segmentMarkersMs`,
- `segmentActiveMarkerIndex`,
- `segmentActiveStartMs`,
- `segmentActiveEndMs`,
- visible marker x positions,
- visible active suffix row geometry,
- disabled states for practice controls.

Add test helpers only when they remove repeated pointer math from tests, for example a marker-row click helper that accepts a viewport ratio. Do not expose implementation-only internals.

### 8. Centralize Segment Invalidation

Segment state should be cleared when source identity or visualizer lifetime changes. Put that clearing in one controller function and call it from existing lifecycle points:

- graph requested/reset,
- new track rendered,
- source filename changed,
- editor/note lifecycle reset,
- user clears markers,
- user-origin selection change.

Avoid scattering direct marker array mutation across graph, selection, and playback files.

## Recommended Implementation Order

1. Add pure segment state helpers and tests.
2. Extract viewport-aware overlay geometry and prove existing viewport/selection/cursor tests still pass.
3. Add segment controller state and test-contract fields without rendering controls yet.
4. Add marker row rendering and marker editing tests.
5. Add selection mutation origin handling and reset tests.
6. Decompose Play split menu and preserve existing repeat tests.
7. Add practice controls and selected-region playback adapter.
8. Add e2e coverage for the full graph workflow.

This order keeps each change reviewable and prevents playback work from being mixed with geometry and menu cleanup.

## Additional Tests

### Vitest Pure Unit Tests

Add `settings_ui/tests/editor-inline.segment-practice-state.test.ts`:

- markers are sorted and deduplicated,
- markers clamp inside `baseRegion`,
- markers outside `baseRegion` are rejected,
- nearby click removes a marker and distant click adds one,
- rightmost marker is chosen when practice starts,
- Next moves left toward longer suffixes,
- Previous moves right toward shorter suffixes,
- derived suffix always ends at `baseRegion.endMs`,
- invalid base region or missing markers disables Practice,
- active marker survives viewport changes because viewport is not part of pure state.

Add or extend geometry tests:

- marker row click uses the current viewport, not full duration,
- marker x positions use current viewport,
- off-viewport markers are hidden without being removed,
- active suffix shading clips to the viewport.

### Vitest Integration Tests

Add targeted tests under `settings_ui/tests/` using existing editor-inline helpers:

- Play menu shows segment controls only when graph selection prerequisites are met.
- Edit segments captures the current committed selection as `baseRegion`.
- Marker row appears when editing is enabled and disappears after clear/reset.
- Clicking the marker row adds/removes markers at correct times while zoomed.
- Panning or zooming after marker placement preserves marker times.
- Practice sets visible selection to the active suffix but preserves `baseRegion`.
- User-origin selection changes clear markers; practice-origin selection changes do not.
- Practice starts from the rightmost marker.
- Next expands the visible selection by moving one marker left.
- Previous shrinks the visible selection by moving one marker right.
- Normal Play while Practice is active pauses practice and does not start a second playback in the same click.
- Starting Practice while normal playback is active stops normal playback first.
- Practice loops even when ordinary repeat was off, and exiting practice does not save repeat as a new default.
- Repeat pause is reused; no segment-specific pause value appears in state.
- Multi-field editor state keeps markers and practice state scoped per field/source.
- Source reset or graph redraw clears stale segment state.

Existing tests to extend carefully:

- `editor-inline.play-options.integration.test.ts` for Play menu controls.
- `editor-inline.playback-zoom.integration.test.ts` for viewport follow and clipping behavior.
- `editor-inline.selection-playback.integration.test.ts` or a new adjacent file for selected-region playback reuse.
- `editor-inline.window-contract.test.ts` for new test-contract fields.
- `editor-inline.visualizer-renderer.test.ts` only if marker row geometry is rendered through shared renderer helpers.

### E2E Tests

Add a focused e2e file such as `e2e/test_editor_segmented_playback_workflow.py`.

Cover:

- select a phrase, enable segment editing, and place markers in the marker row,
- zoom into the phrase and place markers at zoomed positions,
- pan/zoom after placing markers and confirm marker state survives,
- start Practice and assert playback request uses selected-region bounds from the rightmost marker to phrase end,
- Next moves left and expands selected playback bounds,
- Previous moves right and shrinks selected playback bounds,
- repeat boundary loops the same suffix and does not auto-advance,
- normal Play pauses active Practice without starting competing playback,
- manual phrase reselection clears old markers,
- markers are scoped by field in a two-audio-field note,
- source redraw/reset clears markers.

Use existing helpers from `editor_region_loop_helpers.py`, `editor_graph_helpers.py`, and `editor_playback_helpers.py` where possible. Add segment-specific helper functions only for marker row interactions and practice-menu commands.

## Verification Commands

Run focused checks while developing:

```bash
python3 scripts/dev.py test-svelte --verbose
python3 scripts/dev.py test-e2e-parallel --verbose
```

Before calling the feature complete:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

The e2e command is required because Anki loads built webview bundles, not the TypeScript source directly.

## Non-Goals

- No Python backend changes for v1.
- No persisted marker storage.
- No new audio render operation.
- No separate playback request kind for segments.
- No automatic segmentation suggestions.
- No general event bus unless the narrow selection-origin hook proves insufficient.
- No broad rewrite of `GraphVisualizer.svelte`, playback, or selection gestures.

## Success Criteria

The implementation is clean enough when:

- segment math is testable without DOM,
- graph geometry remains viewport-aware and shared with existing graph behavior,
- practice playback appears to the rest of the system as selected-region playback,
- manual selection changes and practice-driven selection changes are distinguishable,
- Play menu growth does not make repeat behavior harder to maintain,
- stale markers cannot survive source or field changes,
- the new e2e tests prove the zoomed graph workflow and playback loop behavior.
