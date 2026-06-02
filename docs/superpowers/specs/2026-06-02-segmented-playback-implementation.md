# Segmented Playback Implementation

## Purpose

This document describes the implemented segmented playback feature derived from `2026-06-01-segmented-playback-design.md`.

Segmented playback is implemented as an inline-editor frontend feature. It reuses graph selection, graph zoom viewport math, existing selected-region playback requests, repeat behavior, and the editor test contract. It does not add Python playback commands, media processing, persisted marker storage, note metadata, config fields, or local-storage state.

## User-Facing Behavior

The learner selects a phrase on the graph, opens the Play split menu, enables `Edit segments`, and clicks the marker row below the graph to place temporary start markers. `Practice` starts from the rightmost marker and loops the suffix from that marker to the original phrase end. `Next` moves left toward longer suffixes, and `Previous` moves right toward shorter suffixes.

The visible graph selection is reused as the active suffix display. This keeps practice behavior aligned with ordinary selected-region playback: practice simply updates the selected region to the current suffix and starts a looped selected-region playback request.

Markers are temporary per-visualizer state. They clear when the user clears them, when the user changes the graph selection, or when the visualizer source identity changes.

## Module Map

### Pure Segment State

`settings_ui/src/editor-inline/segment-practice-state.ts`

This file contains data-only segment behavior:

- `SegmentPracticeState` stores `baseRegion`, `markersMs`, `activeMarkerIndex`, `editing`, `practiceState`, `ordinaryRepeatEnabled`, and `sourceFilename`.
- `normalizeSegmentMarkers` clamps, rounds, sorts, and deduplicates markers inside the captured base region.
- `toggleSegmentMarker` removes a nearby marker within the hit tolerance or adds a new marker.
- `chooseInitialActiveMarkerIndex` chooses the rightmost marker.
- `moveActiveMarkerIndex` implements `Next` and `Previous`.
- `deriveActiveSuffix` converts the active marker and base region into a normal selected playback region.
- `segmentControlAvailability` derives disabled/enabled control state.

It has no DOM, playback, Svelte, or Anki dependencies.

### Zoom-Aware Overlay Geometry

`settings_ui/src/editor-inline/graph-overlay-geometry.ts`

This file keeps marker row math viewport-aware:

- `markerClickFromEvent` converts a pointer click to milliseconds through `cursorMsFromEvent` and the current `TimeViewport`.
- `markerProjections` converts marker times to graph x positions through `xForMs`.
- `visibleRangeProjection` clips base-region and active-suffix shading to the current viewport.

The marker row never uses full-duration ratios directly. Zoomed placement and rendering use the same viewport model as graph cursor and selection behavior.

### DOM State And Marker Row Rendering

`settings_ui/src/editor-inline/segment-practice-dom.ts`

This file bridges temporary segment state to the visualizer DOM:

- stores state on `VisualizerElement.__aqeSegmentPracticeState`,
- mirrors state to `data-segment-*` attributes for Svelte reactivity and tests,
- builds `SegmentPracticeControlsState` snapshots for the Play menu and test contract,
- renders marker ticks, base-region shading, and active-suffix shading into `.aqe-segment-marker-row`,
- positions the marker row against `graphPixelBounds`, `plotGeometryForSvg`, and `svgViewBoxScale`.

Off-viewport markers stay in state but are not rendered until the viewport brings them back into view.

### Controller

`settings_ui/src/editor-inline/segment-practice-controller.ts`

The controller owns orchestration:

- installs per-visualizer handlers through `installSegmentPracticeHandlers`,
- starts/stops marker editing from the current committed graph selection,
- handles marker row pointer clicks,
- starts, pauses, clears, and navigates practice,
- updates the normal graph selection to the active suffix,
- pauses practice when normal Play is requested,
- restores the learner's ordinary repeat setting when practice exits.

Practice playback is sent as an ordinary selected-region `PlaybackRequest` with `regionMode: "selection"` and `loop: true`. HTML playback goes through `startEditorHtmlPlayback`; native playback goes through `sendPlaybackRequest`.

### Selection Mutation Origin

`settings_ui/src/editor-inline/selection-events.ts`

Practice needs to update the visible graph selection without erasing its captured `baseRegion`. The implementation adds a narrow selection-origin event:

- `actions.ts` selection wrappers accept `origin?: "user" | "segment-practice" | "system"`.
- User-origin selection changes clear segment practice state.
- Segment-practice selection changes update the visible suffix and notify listeners without clearing markers.
- System-origin selection changes are used by graph initialization, redraw, and reset paths.

This avoids a broader event bus and keeps invalidation localized to the segment controller.

### Graph And Play Menu Integration

`settings_ui/src/editor-inline/GraphVisualizer.svelte`

The visualizer installs segment handlers on mount and renders a button-based marker row under the SVG plot. The row is hidden unless editing or practice is active.

`settings_ui/src/editor-inline/viewport-actions.ts`

Viewport redraw dispatches `aqe-viewport-rendered`, which tells the marker row to recompute positions after zoom, pan, fit, or playback-follow redraws.

`settings_ui/src/editor-inline/PlayPracticeOptions.svelte`

The Play split menu segment section renders:

- `Edit segments`,
- `Practice` / `Pause practice`,
- `Previous`,
- `Next`,
- `Clear markers`.

The component observes visualizer `data-segment-*`, selection, and source attributes with a `MutationObserver` and re-reads control state from the controller.

`settings_ui/src/editor-inline/PlaySplitButton.svelte`

The implementation adds `PlayPracticeOptions` to the existing Play popover. The earlier refactor plan suggested extracting repeat controls first, but v1 kept repeat controls in place and added only the practice child component to keep the change smaller.

`settings_ui/src/editor-inline/command-actions.ts`

Normal `aqe:play` first calls `pauseSegmentPracticeForNormalPlay`. If practice is currently playing, the normal Play click pauses practice and returns without starting a competing playback request from the same click.

## Data Flow

### Editing

1. `Edit segments` reads the committed graph selection through `selectionForVisualizer`.
2. The selection is captured as `baseRegion`.
3. The marker row becomes visible.
4. Marker clicks are converted through the current graph viewport.
5. The controller toggles markers through pure state helpers.
6. DOM state and menu availability are refreshed.

### Practice

1. `Practice` verifies that a base region and at least one marker exist.
2. The rightmost marker is chosen when no active marker is set.
3. The active suffix is derived as `[marker, baseRegion.endMs]`.
4. The normal graph selection is set to the suffix with `origin: "segment-practice"`.
5. Repeat is temporarily forced on for the practice loop.
6. The existing playback layer receives a normal selected-region start request.

### Navigation

`Next` moves the active marker index left toward longer suffixes. `Previous` moves it right toward shorter suffixes. Navigation updates the visible selection and, if practice is playing, starts playback again for the new suffix bounds.

### Invalidation

User-origin selection changes clear markers and practice state. Source filename changes clear stale segment state. Clearing practice while playback is active stops local progress state and sends the existing stop command path.

## Test Contract

`settings_ui/src/editor-inline/test-contract.ts` extends `GraphStateForTest` with segment fields:

- base region start/end,
- marker times,
- active marker index,
- active suffix start/end,
- editing and practice state,
- marker row visible x positions,
- active suffix visible x range,
- control availability flags.

These fields are intentionally test-facing snapshots, not a public runtime API.

## Tests

Implemented test coverage:

- `settings_ui/tests/editor-inline.segment-practice-state.test.ts`
  - marker normalization,
  - hit-test add/remove behavior,
  - rightmost initial marker selection,
  - `Next` and `Previous` traversal,
  - active suffix derivation,
  - control availability.

- `settings_ui/tests/editor-inline.graph-overlay-geometry.test.ts`
  - marker clicks use the current zoom viewport,
  - marker projections use the current zoom viewport,
  - visible ranges clip to the viewport.

- `settings_ui/tests/editor-inline.segment-practice.integration.test.ts`
  - Play menu controls and marker editing,
  - zoomed marker placement,
  - practice start from the rightmost marker,
  - `Next` expansion,
  - normal Play pausing active practice.

- `e2e/test_editor_segmented_playback_workflow.py`
  - full editor workflow for marker placement,
  - practice looping suffix bounds,
  - navigation to a longer suffix,
  - normal Play pausing practice,
  - zoomed marker placement.

## Verification

The implementation was verified with:

```bash
npm test -- editor-inline.segment-practice-state.test.ts editor-inline.graph-overlay-geometry.test.ts editor-inline.segment-practice.integration.test.ts --run
python3 scripts/dev.py test-svelte
python3 scripts/dev.py test-e2e e2e/test_editor_segmented_playback_workflow.py
python3 scripts/dev.py test-e2e
python3 scripts/dev.py check
```

## Current V1 Boundaries

The implementation intentionally stays frontend-only and session-only. It does not persist markers, auto-detect segments, add text alignment, add a segment-specific pause setting, or introduce a new backend audio operation.

The marker row recomputes on viewport redraws and clips to the visible viewport. Practice navigation updates the active selection and playback bounds; it does not add a new viewport-follow policy beyond the existing graph viewport behavior.
