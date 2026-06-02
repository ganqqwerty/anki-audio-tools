# Segmented Playback Button Placement Design

## Purpose

This document updates the segmented playback UI placement from `2026-06-01-segmented-playback-design.md`.

The original design placed segment practice controls inside the Play split menu. That made the workflow hard to discover while practicing on the graph and mixed a graph-specific practice mode into playback/repeat settings. Segment practice should instead start from the selected graph region and show its controls only after the learner intentionally enters the mode.

## Approved UX

Segment practice is entered from the floating graph selection toolbar.

When a committed graph selection exists, the selection toolbar shows a text button:

`Practice segments`

The button appears next to the selected-region Play action and before destructive region actions. Text is preferred over an icon because segment practice is not a standard icon concept.

Suggested order:

`Play` | `Practice segments` | `Delete region` | `Delete rest` | `Clear selection`

Clicking `Practice segments` activates segment mode for the current selection:

- the marker row appears under the graph selection,
- a compact practice rail appears near or under the graph,
- the learner can add/remove markers in the marker row,
- the Play split menu returns to only ordinary Play, repeat, and repeat-pause settings.

Segment controls remain hidden until `Practice segments` is clicked.

## Practice Rail

The active segment-mode rail should be compact and graph-local. It should not be a large popover and should not occupy the main top toolbar.

Controls:

- `Edit markers`
- `Previous`
- `Practice` / `Pause`
- `Next`
- `Clear markers`
- `Exit`

The rail may sit below the graph or below the selected region overlay, whichever fits the current visualizer layout without covering the pitch/intensity plot or selection resize handles.

## State Behavior

Clicking `Practice segments` captures the current committed graph selection as the segment `baseRegion`.

Exiting segment mode clears temporary segment UI. Existing v1 behavior can continue clearing markers when the user changes selection or the source file changes. No segment state is persisted.

Normal Play remains mutually exclusive with segment practice. Clicking ordinary Play while segment practice is playing pauses practice instead of starting competing playback.

## Implementation Direction

Remove segment controls from `PlayPracticeOptions.svelte` / `PlaySplitButton.svelte`.

Move the entry point to the selection toolbar:

- add a text action in `SelectionToolbar.svelte` or its state wiring,
- invoke the existing segment controller to enter segment mode,
- keep the marker row rendering in `GraphVisualizer.svelte`,
- add a new graph-local rail component for active segment-mode controls.

The rail should reuse the current segment controller functions:

- start or toggle editing,
- start or pause practice,
- move previous/next,
- clear markers,
- exit segment mode.

The placement change should not alter the pure state model, viewport-aware marker geometry, playback request shape, or Python backend behavior.

## Testing

Update frontend integration and e2e tests to assert the new placement:

- segment controls are not shown in the Play split menu,
- `Practice segments` appears in the selection toolbar only when a committed graph selection exists,
- clicking `Practice segments` shows the marker row and practice rail,
- practice rail controls drive the existing segmented playback flow,
- exiting segment mode hides the rail and marker row,
- full e2e still covers marker placement, practice start, next/previous navigation, zoomed marker placement, and normal Play pausing practice.

## Out Of Scope

- Adding a top-toolbar segment button.
- Showing segment practice controls automatically for every selection.
- Persisting marker state.
- Changing segmented playback audio behavior.
- Reworking repeat settings.
