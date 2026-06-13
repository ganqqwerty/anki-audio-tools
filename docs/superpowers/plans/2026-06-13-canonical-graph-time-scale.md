# Canonical Graph Time Scale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the editor graph open and zoom by canonical rendered-pixel time density instead of stretching every clip to the full viewport.

**Architecture:** The existing `TimeViewport` remains the single coordinate system for drawing, hit testing, selection overlays, chorusing markers, playback follow, and scrolling. The viewport invariant changes so `endMs` may exceed real audio `durationMs`, while Fit remains an explicit `0..durationMs` overview. Canonical and maximum zoom-out spans are derived from rendered plot width.

**Tech Stack:** Svelte 5 inline editor UI, TypeScript viewport/rendering helpers, Vitest/jsdom frontend tests, Python e2e tests through `scripts/dev.py`.

---

## File Structure

- Modify `settings_ui/src/editor-inline/time-viewport.ts`
  - Own canonical density constants, viewport normalization, zoom-span clamping, panning, and scrollability predicates.
- Modify `settings_ui/src/editor-inline/visualizer-state.ts`
  - Reset a visualizer viewport to canonical scale using a supplied plot width.
- Modify `settings_ui/src/editor-inline/visualizer-renderer.ts`
  - Measure/sync the rendered plot width before initial viewport reset.
- Modify `settings_ui/src/editor-inline/zoom-actions.ts`
  - Apply rendered-width max zoom-out limits for buttons, wheel zoom, keyboard zoom, and selection zoom.
- Modify `settings_ui/src/editor-inline/TimeViewportScroller.svelte`
  - Hide or show the scrollbar based on scrollable audio range, not on whether the viewport contains all audio.
- Modify `settings_ui/tests/editor-inline.time-viewport.test.ts`
  - Enforce the new viewport invariant and density math.
- Modify `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`
  - Assert initial graph render uses canonical scale.
- Modify `settings_ui/tests/editor-inline.viewport.integration.test.ts`
  - Assert zoom controls and scrollbar behavior under canonical initial scale.
- Modify `settings_ui/tests/editor-inline.plot.test.ts`
  - Assert axis and hit-testing work when the visible viewport extends past audio duration.
- Modify `e2e/test_editor_graph_zoom_workflow.py`
  - Add end-to-end coverage for short and long clips opening at canonical scale.

## Task 1: Viewport Math Invariant

**Files:**
- Modify: `settings_ui/tests/editor-inline.time-viewport.test.ts`
- Modify: `settings_ui/src/editor-inline/time-viewport.ts`

- [ ] **Step 1: Replace the viewport unit tests with canonical-scale expectations**

Replace `settings_ui/tests/editor-inline.time-viewport.test.ts` with:

```typescript
import { describe, expect, it } from "vitest";

import {
  CANONICAL_TIME_MS_PER_PIXEL,
  MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL,
  canonicalTimeViewport,
  fullTimeViewport,
  hasScrollableTimeRange,
  isFullTimeViewport,
  maxZoomedOutViewportSpan,
  msVisibleInViewport,
  normalizeTimeViewport,
  panTimeViewport,
  timeViewportSpan,
  zoomTimeViewport,
  zoomTimeViewportAroundRatio,
  zoomTimeViewportToRange,
} from "../src/editor-inline/time-viewport.js";

describe("editor inline time viewport", () => {
  it("keeps full fit as an explicit duration-clamped viewport", () => {
    expect(fullTimeViewport(2000)).toEqual({ startMs: 0, endMs: 2000, durationMs: 2000 });
    expect(fullTimeViewport(Number.NaN)).toEqual({ startMs: 0, endMs: 0, durationMs: 0 });
  });

  it("builds canonical viewports from rendered plot width", () => {
    expect(CANONICAL_TIME_MS_PER_PIXEL).toBe(3.125);
    expect(MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL).toBe(25);
    expect(canonicalTimeViewport(500, 600)).toEqual({ startMs: 0, endMs: 1875, durationMs: 500 });
    expect(canonicalTimeViewport(4000, 600)).toEqual({ startMs: 0, endMs: 1875, durationMs: 4000 });
    expect(maxZoomedOutViewportSpan(600)).toBe(15000);
  });

  it("normalizes visible timeline windows without clamping end to duration", () => {
    expect(normalizeTimeViewport(-500, 5000, 2000)).toEqual({ startMs: 0, endMs: 5500, durationMs: 2000 });
    expect(normalizeTimeViewport(900, 100, 1000)).toEqual({ startMs: 100, endMs: 900, durationMs: 1000 });
    expect(normalizeTimeViewport(0, 0, 1000)).toEqual({ startMs: 0, endMs: 250, durationMs: 1000 });
    expect(normalizeTimeViewport(0, 0, 100)).toEqual({ startMs: 0, endMs: 250, durationMs: 100 });
    expect(normalizeTimeViewport(0, 0, 0)).toEqual({ startMs: 0, endMs: 0, durationMs: 0 });
  });

  it("zooms horizontally around an anchor and respects a supplied max span", () => {
    const viewport = fullTimeViewport(4000);

    expect(zoomTimeViewport(viewport, 1000, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewport(viewport, 3000, 2)).toEqual({ startMs: 1500, endMs: 3500, durationMs: 4000 });
    expect(zoomTimeViewport({ startMs: 0, endMs: 500, durationMs: 500 }, 250, 0.1, { maxSpanMs: 1000 })).toEqual({
      startMs: 0,
      endMs: 1000,
      durationMs: 500,
    });
  });

  it("zooms around a pointer ratio and clamps at clip edges when span is narrower than audio", () => {
    const viewport = fullTimeViewport(4000);

    expect(zoomTimeViewportAroundRatio(viewport, 0.25, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewportAroundRatio({ startMs: 0, endMs: 1000, durationMs: 4000 }, 0, 2)).toEqual({
      startMs: 0,
      endMs: 500,
      durationMs: 4000,
    });
  });

  it("pans only when the visible span is narrower than the audio duration", () => {
    const viewport = { startMs: 1000, endMs: 2000, durationMs: 4000 };

    expect(panTimeViewport(viewport, 500)).toEqual({ startMs: 1500, endMs: 2500, durationMs: 4000 });
    expect(panTimeViewport(viewport, -5000)).toEqual({ startMs: 0, endMs: 1000, durationMs: 4000 });
    expect(panTimeViewport(viewport, 5000)).toEqual({ startMs: 3000, endMs: 4000, durationMs: 4000 });
    expect(panTimeViewport({ startMs: 0, endMs: 1875, durationMs: 500 }, 500)).toEqual({
      startMs: 0,
      endMs: 1875,
      durationMs: 500,
    });
  });

  it("zooms to a selected range with padding while respecting min and max spans", () => {
    expect(zoomTimeViewportToRange(1000, 1400, 4000)).toEqual({ startMs: 960, endMs: 1440, durationMs: 4000 });
    expect(zoomTimeViewportToRange(1000, 1050, 4000)).toEqual({ startMs: 900, endMs: 1150, durationMs: 4000 });
    expect(zoomTimeViewportToRange(0, 4000, 4000, { maxSpanMs: 1000 })).toEqual({
      startMs: 1500,
      endMs: 2500,
      durationMs: 4000,
    });
  });

  it("reports full coverage, scrollability, span, and visibility", () => {
    const full = fullTimeViewport(1200);
    const canonicalShort = { startMs: 0, endMs: 1875, durationMs: 500 };
    const zoomed = { startMs: 200, endMs: 800, durationMs: 1200 };

    expect(isFullTimeViewport(full)).toBe(true);
    expect(isFullTimeViewport(canonicalShort)).toBe(true);
    expect(isFullTimeViewport(zoomed)).toBe(false);
    expect(hasScrollableTimeRange(full)).toBe(false);
    expect(hasScrollableTimeRange(canonicalShort)).toBe(false);
    expect(hasScrollableTimeRange(zoomed)).toBe(true);
    expect(timeViewportSpan(zoomed)).toBe(600);
    expect(msVisibleInViewport(200, zoomed)).toBe(true);
    expect(msVisibleInViewport(800, zoomed)).toBe(true);
    expect(msVisibleInViewport(801, zoomed)).toBe(false);
  });
});
```

- [ ] **Step 2: Run the viewport tests and confirm they fail**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.time-viewport.test.ts
```

Expected: FAIL on missing exports such as `canonicalTimeViewport` and on old duration-clamped normalization.

- [ ] **Step 3: Replace the viewport helper implementation**

Replace `settings_ui/src/editor-inline/time-viewport.ts` with:

```typescript
export interface TimeViewport {
  durationMs: number;
  endMs: number;
  startMs: number;
}

export interface TimeViewportClampOptions {
  maxSpanMs?: number;
}

export const MIN_TIME_VIEWPORT_MS = 250;
export const TIME_VIEWPORT_ZOOM_FACTOR = 1.25;
export const TIME_VIEWPORT_SELECTION_PADDING_RATIO = 0.1;
export const CANONICAL_TIME_MS_PER_PIXEL = 3.125;
export const MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL = 25;

export function fullTimeViewport(durationMs: number): TimeViewport {
  const duration = normalizedDuration(durationMs);
  return {
    durationMs: duration,
    endMs: duration,
    startMs: 0,
  };
}

export function canonicalTimeViewport(durationMs: number, plotWidthPx: number): TimeViewport {
  const duration = normalizedDuration(durationMs);
  if (duration <= 0) return fullTimeViewport(0);
  return normalizeTimeViewport(0, canonicalViewportSpan(plotWidthPx), duration);
}

export function canonicalViewportSpan(plotWidthPx: number): number {
  return roundedMs(sanitizedPlotWidthPx(plotWidthPx) * CANONICAL_TIME_MS_PER_PIXEL);
}

export function maxZoomedOutViewportSpan(plotWidthPx: number): number {
  return roundedMs(sanitizedPlotWidthPx(plotWidthPx) * MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL);
}

export function normalizeTimeViewport(
  startMs: number,
  endMs: number,
  durationMs: number,
  options: TimeViewportClampOptions = {},
): TimeViewport {
  const duration = normalizedDuration(durationMs);
  if (duration <= 0) return fullTimeViewport(0);
  const rawStart = finiteMs(startMs);
  const rawEnd = finiteMs(endMs);
  const low = Math.min(rawStart, rawEnd);
  const high = Math.max(rawStart, rawEnd);
  const minSpan = minimumViewportSpan(duration);
  const requestedSpan = clampedViewportSpan(high - low, minSpan, options.maxSpanMs);
  const center = Number.isFinite((rawStart + rawEnd) / 2) ? (rawStart + rawEnd) / 2 : duration / 2;
  const start = normalizedViewportStart(center, requestedSpan, duration);
  return {
    durationMs: duration,
    endMs: roundedMs(start + requestedSpan),
    startMs: roundedMs(start),
  };
}

export function timeViewportSpan(viewport: TimeViewport): number {
  return Math.max(0, viewport.endMs - viewport.startMs);
}

export function isFullTimeViewport(viewport: TimeViewport): boolean {
  return viewport.startMs <= 0 && viewport.endMs >= viewport.durationMs;
}

export function hasScrollableTimeRange(viewport: TimeViewport): boolean {
  return viewport.durationMs > 0 && timeViewportSpan(viewport) < viewport.durationMs;
}

export function msVisibleInViewport(ms: number, viewport: TimeViewport): boolean {
  const value = finiteMs(ms);
  return value >= viewport.startMs && value <= viewport.endMs;
}

export function msForViewportRatio(viewport: TimeViewport, ratio: number): number {
  const clampedRatio = Math.max(0, Math.min(1, Number(ratio) || 0));
  return viewport.startMs + clampedRatio * timeViewportSpan(viewport);
}

export function ratioForMsInViewport(ms: number, viewport: TimeViewport): number {
  const span = timeViewportSpan(viewport);
  if (span <= 0) return 0;
  return (finiteMs(ms) - viewport.startMs) / span;
}

export function zoomTimeViewport(
  viewport: TimeViewport,
  anchorMs: number,
  zoomFactor: number,
  options: TimeViewportClampOptions = {},
): TimeViewport {
  const factor = Number(zoomFactor) || 1;
  if (factor <= 0 || factor === 1) {
    return normalizeTimeViewport(viewport.startMs, viewport.endMs, viewport.durationMs, options);
  }
  const span = timeViewportSpan(viewport);
  if (span <= 0) return fullTimeViewport(viewport.durationMs);
  const minSpan = minimumViewportSpan(viewport.durationMs);
  const nextSpan = clampedViewportSpan(span / factor, minSpan, options.maxSpanMs);
  const anchor = Math.max(viewport.startMs, Math.min(finiteMs(anchorMs), viewport.endMs));
  const anchorRatio = (anchor - viewport.startMs) / span;
  const start = anchor - nextSpan * anchorRatio;
  return normalizeTimeViewport(start, start + nextSpan, viewport.durationMs, options);
}

export function zoomTimeViewportAroundRatio(
  viewport: TimeViewport,
  ratio: number,
  zoomFactor: number,
  options: TimeViewportClampOptions = {},
): TimeViewport {
  return zoomTimeViewport(viewport, msForViewportRatio(viewport, ratio), zoomFactor, options);
}

export function panTimeViewport(viewport: TimeViewport, deltaMs: number): TimeViewport {
  const span = timeViewportSpan(viewport);
  if (span <= 0) return fullTimeViewport(viewport.durationMs);
  if (span >= viewport.durationMs) return normalizeTimeViewport(0, span, viewport.durationMs);
  const delta = finiteMs(deltaMs);
  const start = Math.max(0, Math.min(viewport.startMs + delta, viewport.durationMs - span));
  return normalizeTimeViewport(start, start + span, viewport.durationMs);
}

export function zoomTimeViewportToRange(
  startMs: number,
  endMs: number,
  durationMs: number,
  options: TimeViewportClampOptions = {},
): TimeViewport {
  const duration = normalizedDuration(durationMs);
  const start = Math.max(0, Math.min(finiteMs(startMs), duration));
  const end = Math.max(0, Math.min(finiteMs(endMs), duration));
  const low = Math.min(start, end);
  const high = Math.max(start, end);
  const rangeSpan = Math.max(0, high - low);
  const padding = rangeSpan * TIME_VIEWPORT_SELECTION_PADDING_RATIO;
  const minSpan = minimumViewportSpan(duration);
  const desiredSpan = clampedViewportSpan(rangeSpan + padding * 2, minSpan, options.maxSpanMs);
  const center = low + rangeSpan / 2;
  return normalizeTimeViewport(center - desiredSpan / 2, center + desiredSpan / 2, duration, options);
}

function minimumViewportSpan(durationMs: number): number {
  if (durationMs <= 0) return 0;
  return MIN_TIME_VIEWPORT_MS;
}

function clampedViewportSpan(requestedSpanMs: number, minSpanMs: number, maxSpanMs?: number): number {
  const requested = Math.max(0, finiteMs(requestedSpanMs));
  const minimum = Math.max(0, finiteMs(minSpanMs));
  const maximum = Number.isFinite(maxSpanMs) && Number(maxSpanMs) > 0
    ? Math.max(minimum, Number(maxSpanMs))
    : Number.POSITIVE_INFINITY;
  return Math.max(minimum, Math.min(maximum, requested));
}

function normalizedViewportStart(centerMs: number, spanMs: number, durationMs: number): number {
  if (spanMs >= durationMs) return 0;
  return Math.max(0, Math.min(centerMs - spanMs / 2, durationMs - spanMs));
}

function sanitizedPlotWidthPx(value: number): number {
  const width = finiteMs(value);
  return width > 0 ? width : 600;
}

function normalizedDuration(durationMs: number): number {
  return Math.max(0, finiteMs(durationMs));
}

function finiteMs(value: number): number {
  return Number.isFinite(value) ? value : 0;
}

function roundedMs(value: number): number {
  return Math.round(value);
}
```

- [ ] **Step 4: Run the viewport tests and confirm they pass**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.time-viewport.test.ts
```

Expected: PASS for all tests in `editor-inline.time-viewport.test.ts`.

- [ ] **Step 5: Commit the viewport invariant**

Run:

```bash
git add settings_ui/src/editor-inline/time-viewport.ts settings_ui/tests/editor-inline.time-viewport.test.ts
git commit -m "Make graph time viewport span beyond audio" -m "The graph needs a stable horizontal time scale so short clips are not stretched and long clips are not compressed by default. Allowing the visible viewport to extend beyond the real audio duration gives the renderer one honest timeline for canonical pitch inspection." -m "This introduces pixel-density viewport helpers and tests the new invariant that endMs may exceed durationMs while panning remains clamped to real audio. Full check and e2e routines were not run for this focused viewport commit."
```

## Task 2: Plot And Renderer Canonical Reset

**Files:**
- Modify: `settings_ui/tests/editor-inline.plot.test.ts`
- Modify: `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`
- Modify: `settings_ui/src/editor-inline/visualizer-state.ts`
- Modify: `settings_ui/src/editor-inline/visualizer-renderer.ts`

- [ ] **Step 1: Add plot tests for viewport ranges beyond duration**

Append this test to `settings_ui/tests/editor-inline.plot.test.ts` inside the existing `describe` block:

```typescript
  it("uses visible viewport time beyond duration for axis labels and hit testing", () => {
    document.body.innerHTML = `
      <div class="aqe-visualizer">
        <svg>
          <g class="aqe-x-axis"></g>
        </svg>
      </div>
    `;
    const visualizer = document.querySelector<HTMLElement>(".aqe-visualizer")!;
    const viewport = { startMs: 0, endMs: 1875, durationMs: 500 };

    drawXAxis(visualizer, 500, viewport);

    expect(Array.from(visualizer.querySelectorAll(".aqe-x-label")).map((node) => node.textContent)).toEqual([
      "0 ms",
      "938 ms",
      "1875 ms",
    ]);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.getBoundingClientRect = () => ({
      bottom: 150,
      height: 150,
      left: 10,
      right: 630,
      top: 0,
      width: 620,
      x: 10,
      y: 0,
      toJSON: () => ({}),
    });

    const bounds = graphPixelBounds(svg);
    expect(cursorMsFromEvent({ clientX: bounds.left + 160 }, svg, 500, viewport)).toBe(500);
  });
```

- [ ] **Step 2: Add renderer tests for canonical initial scale**

Update the imports in `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`:

```typescript
import { PLOT, xForMs } from "../src/editor-inline/plot.js";
import { readVisualizerTimeViewport } from "../src/editor-inline/visualizer-state.js";
```

Add this test inside the existing `describe` block:

```typescript
  it("resets new graph tracks to canonical rendered-pixel scale", () => {
    const shortTrack: NormalizedProsodyTrack = {
      ...voicedTrack,
      durationMs: 500,
      points: [
        [0, 120, 0.1, true],
        [250, 180, 0.8, true],
        [500, 220, 0.6, true],
      ],
    };
    const visualizer = mountVisualizer(shortTrack);
    const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg")!;
    setSvgBounds(svg, 620);

    renderVisualizerTrack(visualizer, shortTrack);

    expect(readVisualizerTimeViewport(visualizer)).toEqual({ startMs: 0, endMs: 1875, durationMs: 500 });
    const pitchPath = visualizer.querySelector<SVGPathElement>(".aqe-pitch-path")?.getAttribute("d") || "";
    expect(pitchPath).toContain("L 170.00 80.80");
    expect(pitchPath).not.toContain("L 610.00 80.80");
  });
```

Replace the existing test named `resets zoom to fit when a graph is redrawn for a new track` with:

```typescript
  it("resets zoom to canonical scale when a graph is redrawn for a new track", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);

    window.__aqeSetVisualizer?.(0, { ...track, durationMs: 2000, sourceFilename: "next.mp3" }, 0);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(1875);
  });
```

- [ ] **Step 3: Run plot and renderer tests and confirm they fail**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.plot.test.ts editor-inline.visualizer-renderer.test.ts editor-inline.viewport.integration.test.ts
```

Expected: FAIL because graph render still calls `fullTimeViewport(durationMs)`.

- [ ] **Step 4: Update visualizer state reset to accept canonical plot width**

In `settings_ui/src/editor-inline/visualizer-state.ts`, change the viewport import to:

```typescript
import {
  canonicalTimeViewport,
  fullTimeViewport,
  normalizeTimeViewport,
  type TimeViewport,
} from "./time-viewport.js";
```

Replace `resetVisualizerTimeViewport` with:

```typescript
export function resetVisualizerTimeViewport(
  visualizer: VisualizerElement,
  durationMs = readVisualizerDurationMs(visualizer),
  plotWidthPx?: number,
): void {
  writeVisualizerTimeViewport(visualizer, canonicalTimeViewport(durationMs, Number(plotWidthPx) || 0));
}
```

Keep `readVisualizerTimeViewport()` and `writeVisualizerTimeViewport()` using `normalizeTimeViewport(...)` so persisted `endMs > durationMs` remains valid.

- [ ] **Step 5: Reset new tracks after measuring the synced plot width**

In `settings_ui/src/editor-inline/visualizer-renderer.ts`, add `plotWidth` to the `plot.ts` import list:

```typescript
  plotGeometryForSvg,
  plotWidth,
  svgViewBoxScale,
```

Replace this part of `renderVisualizerTrack()`:

```typescript
  visualizer.__aqeTrack = track;
  resetVisualizerTimeViewport(visualizer, track.durationMs || 0);
  renderProsodyTracks(visualizer);
```

with:

```typescript
  visualizer.__aqeTrack = track;
  const plot = syncVisualizerViewBox(visualizer);
  resetVisualizerTimeViewport(visualizer, track.durationMs || 0, plotWidth(plot));
  renderProsodyTracks(visualizer);
```

Leave `renderGraphRequested()` as `resetVisualizerTimeViewport(visualizer, 0)` because duration `0` must remain `0..0`.

- [ ] **Step 6: Run plot and renderer tests and confirm they pass**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.plot.test.ts editor-inline.visualizer-renderer.test.ts
```

Expected: PASS for both files.

- [ ] **Step 7: Commit canonical graph reset**

Run:

```bash
git add settings_ui/src/editor-inline/visualizer-state.ts settings_ui/src/editor-inline/visualizer-renderer.ts settings_ui/tests/editor-inline.plot.test.ts settings_ui/tests/editor-inline.visualizer-renderer.test.ts
git commit -m "Open graph tracks at canonical time scale" -m "Initial graph render should preserve pitch-shape readability instead of stretching every clip to the full plot width. Measuring the plot before reset lets short and long clips open at the same ms-per-pixel density." -m "Renderer tests now prove short clips can open with endMs beyond durationMs and that graph redraws reset to canonical scale. Full check and e2e routines were not run for this focused renderer commit."
```

## Task 3: Interactive Zoom And Scrolling Limits

**Files:**
- Modify: `settings_ui/tests/editor-inline.viewport.integration.test.ts`
- Modify: `settings_ui/src/editor-inline/zoom-actions.ts`
- Modify: `settings_ui/src/editor-inline/TimeViewportScroller.svelte`

- [ ] **Step 1: Update viewport integration tests for canonical scale**

In `settings_ui/tests/editor-inline.viewport.integration.test.ts`, replace the first test body named `zooms, fits, and zooms to selection from graph controls` with:

```typescript
  it("zooms, fits, and zooms to selection from graph controls", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    let state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBeGreaterThan(track.durationMs);

    window.__aqeSetCursorForTest?.(0, track.durationMs / 2, false);
    for (let index = 0; index < 4; index += 1) {
      document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')?.click();
    }
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    expect(state?.viewportEndMs).toBeLessThan(track.durationMs);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-fit-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);

    dragGraphSelection(svg, 0.25, 0.5);
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-selection-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeLessThanOrEqual(state?.selectionStartMs ?? 0);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(state?.selectionEndMs ?? 0);
    expect((state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0)).toBeLessThan(track.durationMs);
  });
```

Replace the test body named `uses graph wheel and keyboard gestures for horizontal zoom only` with:

```typescript
  it("uses graph wheel and keyboard gestures for horizontal zoom only", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const plot = document.querySelector<HTMLElement>('[data-testid="aqe-visualizer-plot-0"]')!;
    setGraphBounds(svg);

    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      ctrlKey: true,
      deltaY: -100,
    }));
    let state = window.__aqeGraphStateForTest?.(0);
    let span = (state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0);
    expect(span).toBeLessThan(1875);
    expect(span).toBeGreaterThan(track.durationMs);

    for (let index = 0; index < 4; index += 1) {
      plot.dispatchEvent(new WheelEvent("wheel", {
        bubbles: true,
        clientX: graphClientX(svg, 0.5),
        ctrlKey: true,
        deltaY: -100,
      }));
    }
    state = window.__aqeGraphStateForTest?.(0);
    const beforeShiftPanStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaX: 100,
      shiftKey: true,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(beforeShiftPanStart);

    const beforePanStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaX: -100,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeLessThan(beforePanStart);

    const beforeVerticalStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaY: 100,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(beforeVerticalStart);

    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    visualizer.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "0" }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);
  });
```

Replace the test body named `scrolls the visible time viewport with a horizontal scrollbar` with:

```typescript
  it("scrolls the visible time viewport with a horizontal scrollbar only when audio is scrollable", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const scrollbar = document.querySelector<HTMLElement>('[data-testid="aqe-time-scrollbar-0"]')!;
    const scrollport = document.querySelector<HTMLDivElement>('[data-testid="aqe-time-scrollbar-scroll-0"]')!;
    Object.defineProperty(scrollport, "clientWidth", { configurable: true, value: 200 });

    expect(scrollbar.hidden).toBe(true);

    for (let index = 0; index < 4; index += 1) {
      document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')?.click();
    }
    await Promise.resolve();
    await Promise.resolve();
    expect(scrollbar.hidden).toBe(false);
    const beforeScroll = window.__aqeGraphStateForTest?.(0);
    expect(scrollport.querySelector<HTMLElement>(".aqe-time-scrollbar-spacer")?.style.width).not.toBe("100%");

    scrollport.scrollLeft = 50;
    scrollport.dispatchEvent(new Event("scroll"));

    const afterScroll = window.__aqeGraphStateForTest?.(0);
    expect(afterScroll?.viewportStartMs).toBeGreaterThan(beforeScroll?.viewportStartMs ?? 0);
    expect(afterScroll?.viewportEndMs).toBe(track.durationMs);
  });
```

- [ ] **Step 2: Run viewport integration tests and confirm they fail**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.viewport.integration.test.ts
```

Expected: FAIL because zoom-out has no rendered-width max and the scroller still depends on `isFullTimeViewport`.

- [ ] **Step 3: Add rendered-width zoom limits**

In `settings_ui/src/editor-inline/zoom-actions.ts`, change the `time-viewport.js` import to include the new helpers:

```typescript
  hasScrollableTimeRange,
  maxZoomedOutViewportSpan,
```

Change the `plot.js` import to:

```typescript
import { graphPixelBounds, plotWidth } from "./plot.js";
```

Add this helper after `fieldOrd()`:

```typescript
function maxZoomOutSpanForVisualizer(visualizer: VisualizerElement): number {
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!svg) return maxZoomedOutViewportSpan(plotWidth());
  return maxZoomedOutViewportSpan(graphPixelBounds(svg).width);
}
```

Change `zoomInForVisualizer()` to:

```typescript
export function zoomInForVisualizer(visualizer: VisualizerElement): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  const anchorMs = readVisualizerCursorMs(visualizer);
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewport(viewport, anchorMs, TIME_VIEWPORT_ZOOM_FACTOR, {
      maxSpanMs: maxZoomOutSpanForVisualizer(visualizer),
    }),
  );
}
```

Change `zoomOutForVisualizer()` to:

```typescript
export function zoomOutForVisualizer(visualizer: VisualizerElement): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  const anchorMs = readVisualizerCursorMs(visualizer);
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewport(viewport, anchorMs, 1 / TIME_VIEWPORT_ZOOM_FACTOR, {
      maxSpanMs: maxZoomOutSpanForVisualizer(visualizer),
    }),
  );
}
```

Change `zoomSelectionForVisualizer()` to:

```typescript
export function zoomSelectionForVisualizer(visualizer: VisualizerElement): boolean {
  const selection = selectionForVisualizer(visualizer);
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  if (!selection || selection.mode !== "selection") return false;
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewportToRange(selection.startMs, selection.endMs, durationMs, {
      maxSpanMs: maxZoomOutSpanForVisualizer(visualizer),
    }),
  );
  return true;
}
```

In `handleVisualizerWheelZoom()`, change the wheel zoom apply call to:

```typescript
    applyVisualizerTimeViewport(
      visualizer,
      zoomTimeViewportAroundRatio(viewport, ratio, factor, {
        maxSpanMs: maxZoomOutSpanForVisualizer(visualizer),
      }),
    );
```

In `handleVisualizerWheelZoom()` and `handleVisualizerZoomKeyDown()`, replace checks that use `!isFullTimeViewport(viewport)` for panning with `hasScrollableTimeRange(viewport)`.

- [ ] **Step 4: Update the scroller to use scrollable audio range**

In `settings_ui/src/editor-inline/TimeViewportScroller.svelte`, replace the import of `isFullTimeViewport` with `hasScrollableTimeRange`:

```typescript
  import {
    hasScrollableTimeRange,
    panTimeViewport,
    timeViewportSpan,
  } from "./time-viewport.js";
```

In `syncFromVisualizer()`, replace:

```typescript
    hidden = isFullTimeViewport(viewport) || span <= 0;
```

with:

```typescript
    hidden = !hasScrollableTimeRange(viewport) || span <= 0;
```

In `handleScroll()`, replace:

```typescript
    if (isFullTimeViewport(viewport) || span <= 0) return;
```

with:

```typescript
    if (!hasScrollableTimeRange(viewport) || span <= 0) return;
```

- [ ] **Step 5: Run viewport integration tests and confirm they pass**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.viewport.integration.test.ts
```

Expected: PASS for `editor-inline.viewport.integration.test.ts`.

- [ ] **Step 6: Commit zoom and scroller behavior**

Run:

```bash
git add settings_ui/src/editor-inline/zoom-actions.ts settings_ui/src/editor-inline/TimeViewportScroller.svelte settings_ui/tests/editor-inline.viewport.integration.test.ts
git commit -m "Constrain graph zoom by rendered time density" -m "Zooming out needs a larger overview than the old duration clamp, but it still needs a meaningful ceiling so pitch detail is not lost without limit. Using rendered plot width keeps browser and edit-window graph scale consistent." -m "The scroller now appears only when real audio can be panned, so empty post-audio timeline space for short clips does not create fake scrolling. Full check and e2e routines were not run for this focused zoom commit."
```

## Task 4: E2E Coverage For Initial Scale

**Files:**
- Modify: `e2e/test_editor_graph_zoom_workflow.py`

- [ ] **Step 1: Allow zoom e2e helper to generate different durations**

Change `_open_zoom_graph_editor()` in `e2e/test_editor_graph_zoom_workflow.py` to:

```python
def _open_zoom_graph_editor(anki_mw, ffmpeg_config, filename: str, duration_s: float = 4.0):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / filename
    generate_tone(ffmpeg_config, source, duration_s=duration_s)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    editor, parent = _open_editor(anki_mw, note)
    wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
    track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
    return media_dir, source, editor, parent, track
```

- [ ] **Step 2: Add short-clip initial canonical scale e2e test**

Add this test after `_open_zoom_graph_editor()`:

```python
def test_editor_graph_short_clip_initial_viewport_uses_canonical_pixel_scale(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_short_canonical.wav",
        duration_s=0.5,
    )
    try:
        state = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const state = window.__aqeGraphStateForTest?.(0);
              const bounds = window.__aqeGraphPixelBoundsForTest?.(0);
              if (!state || !bounds) return null;
              const span = state.viewportEndMs - state.viewportStartMs;
              return {
                ...state,
                audioWidthPx: span > 0 ? bounds.width * state.durationMs / span : 0,
              };
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] > value["durationMs"]
            and abs(value["audioWidthPx"] - 160) <= 12,
            timeout=5.0,
        )

        assert state["durationMs"] <= 700
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 3: Add long-clip initial canonical scale e2e test**

Add this test after the short-clip e2e test:

```python
def test_editor_graph_long_clip_initial_viewport_is_not_full_fit(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_long_canonical.wav",
        duration_s=4.0,
    )
    try:
        state = wait_for_js_condition(
            editor.web,
            _graph_zoom_state_js(),
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] < value["durationMs"],
            timeout=5.0,
        )

        assert state["viewportEndMs"] > 1000
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 4: Run targeted e2e zoom tests**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_graph_zoom_workflow.py
```

Expected: PASS for `e2e/test_editor_graph_zoom_workflow.py`.

- [ ] **Step 5: Commit e2e coverage**

Run:

```bash
git add e2e/test_editor_graph_zoom_workflow.py
git commit -m "Verify canonical graph zoom in editor e2e" -m "Short and long clips need real editor coverage because graph width, WebView layout, and generated audio duration all affect the visible time scale. The e2e tests prove initial render no longer relies on full-fit stretching." -m "The focused graph zoom e2e file was run through scripts/dev.py. Full check was not run for this targeted e2e commit."
```

## Task 5: Full Frontend Validation And Focused Regression Sweep

**Files:**
- No source file edits expected unless a verification failure reveals a defect in the files touched above.

- [ ] **Step 1: Run focused frontend tests for touched graph areas**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.time-viewport.test.ts editor-inline.plot.test.ts editor-inline.visualizer-renderer.test.ts editor-inline.viewport.integration.test.ts editor-inline.graph-overlay-geometry.test.ts editor-inline.playback-zoom.integration.test.ts
```

Expected: PASS for all listed Vitest files.

- [ ] **Step 2: Run full frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: PASS. This builds generated webview bundles, runs lint autofix, then validates with Svelte check, ESLint, TypeScript, and Vitest coverage.

- [ ] **Step 3: Run focused e2e tests for graph, selection, chorusing, and playback-follow regressions**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_graph_zoom_workflow.py e2e/test_editor_chorusing_playback_workflow.py e2e/test_editor_cursor_selection_playback_workflow.py e2e/test_editor_voice_recording_comparison_workflow.py
```

Expected: PASS for all four e2e files.

- [ ] **Step 4: Run the repository quality gate if time allows**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS. If this is not run, the final implementation summary and final commit message must explicitly say full check was not run.

- [ ] **Step 5: Commit any verification-driven fixes**

If verification required fixes, commit them with:

```bash
git add settings_ui/src/editor-inline/time-viewport.ts settings_ui/src/editor-inline/visualizer-state.ts settings_ui/src/editor-inline/visualizer-renderer.ts settings_ui/src/editor-inline/zoom-actions.ts settings_ui/src/editor-inline/TimeViewportScroller.svelte settings_ui/tests/editor-inline.time-viewport.test.ts settings_ui/tests/editor-inline.plot.test.ts settings_ui/tests/editor-inline.visualizer-renderer.test.ts settings_ui/tests/editor-inline.viewport.integration.test.ts e2e/test_editor_graph_zoom_workflow.py
git commit -m "Stabilize canonical graph zoom behavior" -m "Verification exposed interaction edges around canonical viewports, so this commit keeps the visible timeline, overlays, scroller, and playback behavior consistent under the new span-beyond-duration invariant." -m "Record which focused frontend, e2e, and full-check commands were run in this body before committing."
```

If there are no verification-driven fixes, do not create an empty commit.

## Self-Review Notes

- Spec coverage: Task 1 covers canonical density constants, `endMs > durationMs`, minimum span, max zoom-out span, panning, and Fit separation. Task 2 covers initial canonical render and plot behavior. Task 3 covers interactive zoom and scroller behavior. Task 4 covers user-visible initial behavior in real WebView e2e. Task 5 covers regression verification.
- Type consistency: The plan defines `TimeViewportClampOptions`, `canonicalTimeViewport`, `canonicalViewportSpan`, `maxZoomedOutViewportSpan`, and `hasScrollableTimeRange` before they are consumed by renderer, zoom actions, and scroller code.
- Scope: The plan does not change vertical pitch scaling, add reset controls, persist zoom state, or modify standalone generated graph media.
