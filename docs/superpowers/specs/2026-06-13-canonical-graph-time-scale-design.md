# Canonical Graph Time Scale Design

## Purpose

The editor graph currently opens in a full-fit viewport. That stretches short clips across the whole plot and compresses long clips into the same width. Both behaviors make pitch movement harder to read because the horizontal shape changes with clip duration instead of reflecting time consistently.

The graph should open at a canonical time density. A 500 ms word should occupy about 160 rendered plot pixels by default, so short Mandarin words can show fast pitch drops and rises without being flattened by viewport fitting. Long clips should also open at that same density instead of being squeezed into a full-audio overview.

## User Guarantee

On initial graph load, horizontal scale is based on rendered plot pixels, not on total audio duration.

- Default density: `3.125 ms/px`, equivalent to `500 ms = 160 px`.
- Maximum interactive zoom-out density: `25 ms/px`, equivalent to `500 ms = 20 px`.
- A short clip starts at time `0` on the left and leaves empty timeline space after the audio when the visible canonical span is wider than the clip.
- A long clip opens on the first canonical visible window rather than the full duration.
- The explicit Fit command still shows the whole audio as `0..durationMs`.

This separates the default tone-inspection view from the deliberate full-overview command.

## Current System Context

The inline editor viewport is represented by `TimeViewport` in `settings_ui/src/editor-inline/time-viewport.ts`. The current normalization clamps every viewport span to the real audio duration. `renderVisualizerTrack()` resets a newly rendered graph with `fullTimeViewport(durationMs)`, so every graph starts in full-fit mode.

Rendering already maps milliseconds to plot x-coordinates through the viewport in `plot.ts`. Zoom buttons, wheel zoom, keyboard zoom, panning, selection rendering, chorusing markers, playback follow, and the horizontal scroller all consume the same viewport state.

Because the coordinate system is already centralized, the preferred design changes the viewport invariant rather than adding a second rendering-only scale.

## Viewport Invariant

`TimeViewport` becomes a visible timeline window, not only a crop of real audio duration.

- `durationMs` remains the real audio duration.
- `startMs` and `endMs` describe visible time.
- `startMs` never normalizes below `0`.
- `endMs` may exceed `durationMs`.
- If the visible span is wider than the audio duration, the viewport stays left-aligned at `startMs = 0`.
- If the visible span is narrower than the audio duration, panning clamps to `0..durationMs - span`.

This invariant should be enforced in tests. In particular, `endMs > durationMs` is valid and should not be normalized away.

## Time Scale Constants

Add named constants to the viewport layer:

```typescript
export const CANONICAL_TIME_MS_PER_PIXEL = 3.125;
export const MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL = 25;
```

Derived spans use rendered plot width:

```typescript
canonicalSpanMs = plotWidthPx * CANONICAL_TIME_MS_PER_PIXEL;
maxZoomedOutSpanMs = plotWidthPx * MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL;
```

For the existing static SVG plot width of about `600 px`, the initial fallback canonical span is about `1875 ms`.

## Initial Viewport

When a graph track is rendered, reset the viewport to the canonical span:

```typescript
startMs = 0;
endMs = plotWidthPx * 3.125;
```

Use the actual rendered plot width in CSS pixels when available. If the SVG has not measured yet, fall back to the existing viewBox plot width. The resize observer may redraw the graph, but it should not silently overwrite a user-adjusted viewport after the initial track render.

Examples:

- `500 ms` clip in a `600 px` plot: viewport `0..1875`, audio occupies `160 px`.
- `700 ms` clip in a `600 px` plot: viewport `0..1875`, audio occupies `224 px`.
- `30 s` clip in a `600 px` plot: viewport `0..1875`, only the first canonical window is shown.

## Zoom And Fit Behavior

Interactive zoom uses the same viewport state and rendered plot width.

- Zoom in keeps a minimum positive span of `250 ms`; duration `0` remains `0..0`.
- Zoom out clamps at `plotWidthPx * 25 ms/px`.
- Button zoom, wheel zoom, and keyboard zoom use the same limits.
- Zoom anchoring keeps using the cursor or pointer ratio.
- Selection zoom keeps focusing the selected range plus padding and clamps to the same min/max limits.
- Fit remains `fullTimeViewport(durationMs)` and may exceed the interactive zoom-out limit for very long clips.

Fit is a deliberate exception because its command means "show the whole audio," not "return to canonical zoom."

## Panning And Scrolling

Panning is meaningful only when the visible span is narrower than real audio duration.

- If `span >= durationMs`, pan returns the left-aligned viewport.
- If `span < durationMs`, pan clamps to `0..durationMs - span`.
- The horizontal scroller remains hidden when there is no scrollable audio range.
- The horizontal scroller appears when a long clip has a viewport span narrower than the duration.

Scroller sizing should use the real audio duration for the scrollable range, while the visible span comes from the current viewport. Empty post-audio time in a short clip should not create a fake scroll range.

## Rendering And Interaction

The renderer should keep using one coordinate system.

- `plot.ts` continues to map milliseconds to x-coordinates through `TimeViewport`.
- Axis ticks use the visible viewport range, even when that range extends beyond audio duration.
- Cursor hit testing maps plot pixels back through the visible viewport, then existing cursor and selection code can clamp to real audio duration where edits require real audio time.
- Selection overlays and chorusing markers use the same viewport projections.
- Playback follow does not pan if the visible span already contains the whole audio.

This avoids the dual-timeline problem where drawing uses a synthetic scale but interactions use duration-clamped time.

## Error Handling

No user-facing error state is needed for bad geometry. The system should degrade to deterministic fallbacks.

- If plot width is missing, zero, or non-finite, use the static plot width from the SVG viewBox.
- If duration is `0`, keep viewport `0..0`.
- If a requested interactive span is below the minimum, clamp to `250 ms` for positive-duration clips.
- If a requested interactive span is above the max zoom-out span, clamp to the max zoom-out span.
- If a requested viewport has a negative start, normalize it back to `0`.
- If a requested viewport span is wider than duration, normalize it to start at `0`.
- Fit bypasses the interactive max zoom-out limit and returns `0..durationMs`.

## Testing

Viewport unit tests should cover the core invariants:

- canonical viewport for `500 ms` duration and `600 px` plot width normalizes to `0..1875 ms`;
- `endMs > durationMs` remains valid;
- `startMs` never normalizes below `0`;
- interactive zoom-out stops at `plotWidthPx * 25`;
- panning a span wider than duration remains left-aligned at `0`;
- panning a span narrower than duration clamps to `0..durationMs - span`;
- Fit returns `0..durationMs` and is not capped by the interactive zoom-out limit.

Frontend or e2e-facing tests should cover user-visible behavior:

- initial graph load for a short clip is not full-fit;
- initial graph load for a long clip shows only the canonical first window;
- Fit still returns `0..durationMs`;
- zoom out can show a span wider than a short clip duration, up to the new max;
- the scrollbar stays hidden when the visible span is wider than the clip;
- the scrollbar appears when a long clip is zoomed in enough to pan.

Existing zoom, selection, chorusing marker, and playback-follow tests should continue to assert that overlays and cursor behavior use the active viewport.

## Out Of Scope

- Changing vertical pitch scaling.
- Adding a separate Reset Zoom command.
- Changing generated standalone graph media.
- Persisting per-field zoom settings across editor sessions.
- Reworking the graph into a separate scale-plus-offset model.
