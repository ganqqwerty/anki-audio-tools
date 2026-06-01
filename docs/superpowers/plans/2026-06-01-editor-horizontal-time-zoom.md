# Editor Horizontal Time Zoom Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add horizontal time zoom to the inline editor audio graph while keeping pitch and intensity Y scaling unchanged.

**Architecture:** Introduce a frontend-only time viewport stored on each `.aqe-visualizer` dataset. Plot helpers, pointer hit-testing, selection rendering, cursor projection, and playback progress read that viewport for X-axis mapping only; pitch/intensity Y calculations keep using the existing full-track global ranges. Zoom controls and wheel/key gestures live in editor-inline Svelte/TypeScript and do not touch Python bridge contracts or audio processing.

**Tech Stack:** Svelte 5, TypeScript, SVG, Vitest/jsdom, Anki WebView e2e tests, existing `scripts/dev.py` build and quality runners.

---

## Current Context

CodeGraph is not initialized in this worktree, so structural exploration was done with JetBrains MCP plus direct file reads. Before implementation, initialize CodeGraph if the user approves it and re-check the touched symbols with `codegraph_context`.

The current editor graph maps the full clip duration directly to X coordinates:

- `settings_ui/src/editor-inline/plot.ts` owns `xForMs()`, `cursorMsFromEvent()`, path generation, and x-axis drawing.
- `settings_ui/src/editor-inline/visualizer-renderer.ts` owns pitch/intensity drawing, cursor projection, selection geometry, and selection toolbar coordinates.
- `settings_ui/src/editor-inline/selection-gestures.ts` owns pointer-to-ms conversion for cursor drag, Shift-selection, and resize handles.
- `settings_ui/src/editor-inline/playback-controller.ts` paints progress during playback.
- `settings_ui/src/editor-inline/EditorControls.svelte` renders the SVG graph and overlay DOM.
- `settings_ui/src/editor-inline/test-contract.ts` exposes graph state to frontend and e2e tests.

The feature is horizontal-only. Do not add Y zoom, Y pan, per-window pitch rescaling, or intensity rescaling.

## File Structure

- Create `settings_ui/src/editor-inline/time-viewport.ts`: pure viewport math, normalization, zoom, pan, fit, selection zoom, visibility checks.
- Create `settings_ui/src/editor-inline/viewport-actions.ts`: DOM-facing viewport application and redraw orchestration for a visualizer.
- Create `settings_ui/src/editor-inline/ZoomControls.svelte`: compact graph-local zoom controls with tooltips.
- Modify `settings_ui/src/editor-inline/plot.ts`: add optional viewport-aware X mapping and hit-testing while preserving default full-duration behavior.
- Modify `settings_ui/src/editor-inline/visualizer-state.ts`: read/write viewport dataset values.
- Modify `settings_ui/src/editor-inline/visualizer-renderer.ts`: draw graph, selection, cursor, and playback cursor using the active time viewport.
- Modify `settings_ui/src/editor-inline/selection-gestures.ts`: use viewport-aware pointer-to-ms conversion.
- Modify `settings_ui/src/editor-inline/playback-controller.ts`: keep the playback cursor visible by panning horizontally during playback.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte`: mount zoom controls and add graph clip paths.
- Modify `settings_ui/src/editor-inline/styles/visualizer.css`: layout and button styling for graph zoom controls.
- Modify `settings_ui/src/lib/icon-types.ts` and `settings_ui/src/lib/CommandIcon.svelte`: add lucide icons for zoom controls.
- Modify `settings_ui/src/editor-inline/types.ts`, `globals.d.ts`, and `test-contract.ts`: expose viewport fields and test helpers.
- Add `settings_ui/tests/editor-inline.time-viewport.test.ts`.
- Modify existing focused frontend tests for plot, visualizer rendering, selection gestures, and integration.
- Add `e2e/test_editor_graph_zoom_workflow.py`.

## Task 1: Pure Time Viewport Model

**Files:**
- Create: `settings_ui/src/editor-inline/time-viewport.ts`
- Test: `settings_ui/tests/editor-inline.time-viewport.test.ts`

- [ ] **Step 1: Write failing viewport math tests**

Create `settings_ui/tests/editor-inline.time-viewport.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import {
  fullTimeViewport,
  isFullTimeViewport,
  msVisibleInViewport,
  normalizeTimeViewport,
  panTimeViewport,
  timeViewportSpan,
  zoomTimeViewport,
  zoomTimeViewportAroundRatio,
  zoomTimeViewportToRange,
} from "../src/editor-inline/time-viewport.js";

describe("editor inline time viewport", () => {
  it("normalizes invalid and oversized ranges to the full duration", () => {
    expect(fullTimeViewport(2000)).toEqual({ startMs: 0, endMs: 2000, durationMs: 2000 });
    expect(normalizeTimeViewport(-500, 5000, 2000)).toEqual({ startMs: 0, endMs: 2000, durationMs: 2000 });
    expect(normalizeTimeViewport(900, 100, 1000)).toEqual({ startMs: 100, endMs: 900, durationMs: 1000 });
    expect(normalizeTimeViewport(0, 0, 1000)).toEqual({ startMs: 0, endMs: 250, durationMs: 1000 });
  });

  it("zooms horizontally around an anchor without changing duration", () => {
    const viewport = fullTimeViewport(4000);
    expect(zoomTimeViewport(viewport, 1000, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewport(viewport, 3000, 2)).toEqual({ startMs: 1500, endMs: 3500, durationMs: 4000 });
  });

  it("zooms around a pointer ratio and clamps at clip edges", () => {
    const viewport = fullTimeViewport(4000);
    expect(zoomTimeViewportAroundRatio(viewport, 0.25, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewportAroundRatio({ startMs: 0, endMs: 1000, durationMs: 4000 }, 0, 2)).toEqual({
      startMs: 0,
      endMs: 500,
      durationMs: 4000,
    });
  });

  it("pans by milliseconds and clamps to the full duration", () => {
    const viewport = { startMs: 1000, endMs: 2000, durationMs: 4000 };
    expect(panTimeViewport(viewport, 500)).toEqual({ startMs: 1500, endMs: 2500, durationMs: 4000 });
    expect(panTimeViewport(viewport, -5000)).toEqual({ startMs: 0, endMs: 1000, durationMs: 4000 });
    expect(panTimeViewport(viewport, 5000)).toEqual({ startMs: 3000, endMs: 4000, durationMs: 4000 });
  });

  it("zooms to a selected range with padding while respecting the minimum window", () => {
    expect(zoomTimeViewportToRange(1000, 1400, 4000)).toEqual({ startMs: 960, endMs: 1440, durationMs: 4000 });
    expect(zoomTimeViewportToRange(1000, 1050, 4000)).toEqual({ startMs: 900, endMs: 1150, durationMs: 4000 });
  });

  it("reports full state, span, and visibility", () => {
    const full = fullTimeViewport(1200);
    const zoomed = { startMs: 200, endMs: 800, durationMs: 1200 };
    expect(isFullTimeViewport(full)).toBe(true);
    expect(isFullTimeViewport(zoomed)).toBe(false);
    expect(timeViewportSpan(zoomed)).toBe(600);
    expect(msVisibleInViewport(200, zoomed)).toBe(true);
    expect(msVisibleInViewport(800, zoomed)).toBe(true);
    expect(msVisibleInViewport(801, zoomed)).toBe(false);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.time-viewport.test.ts
```

Expected: FAIL because `settings_ui/src/editor-inline/time-viewport.ts` does not exist.

- [ ] **Step 3: Add the pure viewport model**

Create `settings_ui/src/editor-inline/time-viewport.ts`:

```ts
export interface TimeViewport {
  durationMs: number;
  endMs: number;
  startMs: number;
}

export const MIN_TIME_VIEWPORT_MS = 250;
export const TIME_VIEWPORT_ZOOM_FACTOR = 2;
export const TIME_VIEWPORT_SELECTION_PADDING_RATIO = 0.1;

export function fullTimeViewport(durationMs: number): TimeViewport {
  const duration = normalizedDuration(durationMs);
  return {
    durationMs: duration,
    endMs: duration,
    startMs: 0,
  };
}

export function normalizeTimeViewport(startMs: number, endMs: number, durationMs: number): TimeViewport {
  const duration = normalizedDuration(durationMs);
  if (duration <= 0) return fullTimeViewport(0);
  const rawStart = finiteMs(startMs);
  const rawEnd = finiteMs(endMs);
  const low = Math.min(rawStart, rawEnd);
  const high = Math.max(rawStart, rawEnd);
  const minSpan = minimumViewportSpan(duration);
  const requestedSpan = Math.max(minSpan, Math.min(duration, high - low));
  const center = Number.isFinite((rawStart + rawEnd) / 2) ? (rawStart + rawEnd) / 2 : duration / 2;
  let start = Math.max(0, Math.min(center - requestedSpan / 2, duration - requestedSpan));
  let end = start + requestedSpan;
  if (low <= 0 && high >= duration) {
    start = 0;
    end = duration;
  }
  return {
    durationMs: duration,
    endMs: roundedMs(end),
    startMs: roundedMs(start),
  };
}

export function timeViewportSpan(viewport: TimeViewport): number {
  return Math.max(0, viewport.endMs - viewport.startMs);
}

export function isFullTimeViewport(viewport: TimeViewport): boolean {
  return viewport.startMs <= 0 && viewport.endMs >= viewport.durationMs;
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

export function zoomTimeViewport(viewport: TimeViewport, anchorMs: number, zoomFactor: number): TimeViewport {
  const factor = Number(zoomFactor) || 1;
  if (factor <= 0 || factor === 1) return normalizeTimeViewport(viewport.startMs, viewport.endMs, viewport.durationMs);
  const span = timeViewportSpan(viewport);
  if (span <= 0) return fullTimeViewport(viewport.durationMs);
  const nextSpan = Math.max(minimumViewportSpan(viewport.durationMs), Math.min(viewport.durationMs, span / factor));
  const anchor = Math.max(viewport.startMs, Math.min(finiteMs(anchorMs), viewport.endMs));
  const anchorRatio = (anchor - viewport.startMs) / span;
  const start = anchor - nextSpan * anchorRatio;
  return normalizeTimeViewport(start, start + nextSpan, viewport.durationMs);
}

export function zoomTimeViewportAroundRatio(viewport: TimeViewport, ratio: number, zoomFactor: number): TimeViewport {
  return zoomTimeViewport(viewport, msForViewportRatio(viewport, ratio), zoomFactor);
}

export function panTimeViewport(viewport: TimeViewport, deltaMs: number): TimeViewport {
  const span = timeViewportSpan(viewport);
  if (span <= 0 || span >= viewport.durationMs) return fullTimeViewport(viewport.durationMs);
  const delta = finiteMs(deltaMs);
  const start = Math.max(0, Math.min(viewport.startMs + delta, viewport.durationMs - span));
  return normalizeTimeViewport(start, start + span, viewport.durationMs);
}

export function zoomTimeViewportToRange(startMs: number, endMs: number, durationMs: number): TimeViewport {
  const duration = normalizedDuration(durationMs);
  const start = Math.max(0, Math.min(finiteMs(startMs), duration));
  const end = Math.max(0, Math.min(finiteMs(endMs), duration));
  const low = Math.min(start, end);
  const high = Math.max(start, end);
  const rangeSpan = Math.max(0, high - low);
  const padding = rangeSpan * TIME_VIEWPORT_SELECTION_PADDING_RATIO;
  const minSpan = minimumViewportSpan(duration);
  const desiredSpan = Math.max(minSpan, rangeSpan + padding * 2);
  const center = low + rangeSpan / 2;
  return normalizeTimeViewport(center - desiredSpan / 2, center + desiredSpan / 2, duration);
}

function minimumViewportSpan(durationMs: number): number {
  if (durationMs <= 0) return 0;
  return Math.min(durationMs, MIN_TIME_VIEWPORT_MS);
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

- [ ] **Step 4: Run the viewport tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.time-viewport.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add settings_ui/src/editor-inline/time-viewport.ts settings_ui/tests/editor-inline.time-viewport.test.ts
git commit -m "feat: model editor time viewport math" -m "The zoom feature needs a small pure model before touching graph rendering. This keeps horizontal viewport behavior testable without Anki or DOM state and fixes the minimum span, clamping, and selection-zoom rules that later UI code depends on. Full check and e2e were not run for this focused commit."
```

## Task 2: Viewport-Aware Plot Mapping

**Files:**
- Modify: `settings_ui/src/editor-inline/plot.ts`
- Modify: `settings_ui/tests/editor-inline.plot.test.ts`
- Modify: `settings_ui/tests/editor-inline.edges.test.ts`

- [ ] **Step 1: Add failing plot tests for viewport X mapping**

Append these cases inside the existing `describe("editor inline plot helpers", () => { ... })` block in `settings_ui/tests/editor-inline.plot.test.ts`:

```ts
  it("maps time into the visible viewport when provided", () => {
    const viewport = { startMs: 1000, endMs: 3000, durationMs: 4000 };

    expect(xForMs(1000, 4000, viewport)).toBe(PLOT.left);
    expect(xForMs(2000, 4000, viewport)).toBeCloseTo(PLOT.left + (PLOT.width - PLOT.left - PLOT.right) / 2);
    expect(xForMs(3000, 4000, viewport)).toBe(PLOT.width - PLOT.right);
  });

  it("uses visible viewport bounds for pointer hit testing", () => {
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

    const viewport = { startMs: 1000, endMs: 3000, durationMs: 4000 };
    const bounds = graphPixelBounds(svg);

    expect(cursorMsFromEvent({ clientX: bounds.left }, svg, 4000, viewport)).toBe(1000);
    expect(cursorMsFromEvent({ clientX: bounds.left + bounds.width / 2 }, svg, 4000, viewport)).toBe(2000);
    expect(cursorMsFromEvent({ clientX: bounds.left + bounds.width }, svg, 4000, viewport)).toBe(3000);
  });

  it("draws visible x-axis labels from the viewport without changing default full-axis labels", () => {
    document.body.innerHTML = `
      <div class="aqe-visualizer">
        <svg>
          <g class="aqe-x-axis"></g>
        </svg>
      </div>
    `;
    const visualizer = document.querySelector<HTMLElement>(".aqe-visualizer")!;

    drawXAxis(visualizer, 4000, { startMs: 1000, endMs: 3000, durationMs: 4000 });

    expect(Array.from(visualizer.querySelectorAll(".aqe-x-label")).map((node) => node.textContent)).toEqual([
      "1.00s",
      "2.00s",
      "3.00s",
    ]);
  });
```

In `settings_ui/tests/editor-inline.edges.test.ts`, add this test in the existing plot edge describe block:

```ts
  it("clamps viewport hit testing to the visible time range", () => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.getBoundingClientRect = () => ({
      bottom: 150,
      height: 150,
      left: 0,
      right: 620,
      top: 0,
      width: 620,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    const viewport = { startMs: 250, endMs: 750, durationMs: 1000 };

    expect(cursorMsFromEvent({ clientX: -100 }, svg, 1000, viewport)).toBe(250);
    expect(cursorMsFromEvent({ clientX: 9999 }, svg, 1000, viewport)).toBe(750);
  });
```

- [ ] **Step 2: Run focused plot tests to verify failure**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.plot.test.ts editor-inline.edges.test.ts
```

Expected: FAIL because `xForMs()`, `cursorMsFromEvent()`, and `drawXAxis()` do not accept viewport arguments.

- [ ] **Step 3: Update plot helpers for optional time viewports**

Modify `settings_ui/src/editor-inline/plot.ts`:

```ts
import type { TimeViewport } from "./time-viewport.js";
import { fullTimeViewport, msForViewportRatio, ratioForMsInViewport } from "./time-viewport.js";
```

Replace `xForMs()`:

```ts
export function xForMs(ms: number, durationMs: number, viewport?: TimeViewport | null): number {
  const activeViewport = viewport ?? fullTimeViewport(durationMs);
  const ratio = ratioForMsInViewport(ms, activeViewport);
  return PLOT.left + Math.max(0, Math.min(1, ratio)) * plotWidth();
}
```

Update signatures and internal calls:

```ts
export function pathForIntensity(
  points: readonly ProsodyPoint[],
  durationMs: number,
  viewport?: TimeViewport | null,
): string {
  if (!points.length || !durationMs) return "";
  const base = PLOT.height - PLOT.bottom;
  const first = points[0];
  if (!first) return "";
  const head = `M ${xForMs(first[0], durationMs, viewport).toFixed(2)} ${base.toFixed(2)}`;
  const body = points.map((point) => {
    const x = xForMs(point[0], durationMs, viewport).toFixed(2);
    const intensity = Math.max(0, Math.min(1, point[2] ?? 0));
    const y = (base - intensity * plotHeight()).toFixed(2);
    return `L ${x} ${y}`;
  }).join(" ");
  const last = points.at(-1) ?? first;
  const tail = `L ${xForMs(last[0], durationMs, viewport).toFixed(2)} ${base.toFixed(2)} Z`;
  return `${head} ${body} ${tail}`;
}

export function pitchSegments(
  points: readonly ProsodyPoint[],
  durationMs: number,
  minHz: number | null,
  maxHz: number | null,
  viewport?: TimeViewport | null,
): number[][][] {
  const segments: number[][][] = [];
  let current: number[][] = [];
  for (const point of points) {
    const pitchHz = point[1];
    const voiced = point[3] === true && pitchHz !== null && pitchHz !== undefined;
    if (!voiced) {
      if (current.length) segments.push(current);
      current = [];
      continue;
    }
    current.push([xForMs(point[0], durationMs, viewport), yForPitch(pitchHz, minHz, maxHz)]);
  }
  if (current.length) segments.push(current);
  return segments;
}
```

Extend `PitchDrawOptions` and `drawPitchPaths()`:

```ts
interface PitchDrawOptions {
  durationMs?: number;
  groupSelector: string;
  pathClass: string;
  pitchMaxHz?: number | null;
  pitchMinHz?: number | null;
  viewport?: TimeViewport | null;
}
```

Inside `drawPitchPaths()` call:

```ts
  for (const segment of pitchSegments(track.points, durationMs, minHz, maxHz, options.viewport)) {
```

Update public draw helpers:

```ts
export function drawPitch(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: Pick<PitchDrawOptions, "durationMs" | "pitchMaxHz" | "pitchMinHz" | "viewport"> = {},
): void {
  drawPitchPaths(visualizer, track, {
    ...options,
    groupSelector: ".aqe-pitch",
    pathClass: "aqe-pitch-path",
  });
}

export function drawLearnerPitch(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: Pick<PitchDrawOptions, "durationMs" | "pitchMaxHz" | "pitchMinHz" | "viewport">,
): void {
  drawPitchPaths(visualizer, track, {
    ...options,
    groupSelector: ".aqe-learner-pitch",
    pathClass: "aqe-learner-pitch-path",
  });
}
```

Replace `drawXAxis()` and `cursorMsFromEvent()`:

```ts
export function drawXAxis(visualizer: VisualizerElement, durationMs: number, viewport?: TimeViewport | null): void {
  const group = visualizer.querySelector<SVGGElement>(".aqe-x-axis");
  if (!group) return;
  group.textContent = "";
  const activeViewport = viewport ?? fullTimeViewport(durationMs);
  const midpoint = activeViewport.startMs + (activeViewport.endMs - activeViewport.startMs) / 2;
  const ticks = [activeViewport.startMs, midpoint, activeViewport.endMs]
    .filter((value, index, values) => index === 0 || Math.round(value) !== Math.round(values[index - 1] ?? -1));
  for (const tick of ticks) {
    const x = xForMs(tick, durationMs, activeViewport);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("class", "aqe-x-tick");
    line.setAttribute("x1", x.toFixed(2));
    line.setAttribute("x2", x.toFixed(2));
    line.setAttribute("y1", String(PLOT.height - PLOT.bottom));
    line.setAttribute("y2", String(PLOT.height - PLOT.bottom + 4));
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("class", "aqe-x-label");
    text.setAttribute("x", x.toFixed(2));
    text.setAttribute("y", String(PLOT.height - 8));
    text.textContent = formatTime(tick, durationMs);
    group.append(line, text);
  }
}

export function cursorMsFromEvent(
  event: Pick<PointerEvent, "clientX">,
  svg: SVGSVGElement,
  durationMs: number,
  viewport?: TimeViewport | null,
): number {
  const bounds = graphPixelBounds(svg);
  const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
  return msForViewportRatio(viewport ?? fullTimeViewport(durationMs), ratio);
}
```

- [ ] **Step 4: Run focused plot tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.plot.test.ts editor-inline.edges.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add settings_ui/src/editor-inline/plot.ts settings_ui/tests/editor-inline.plot.test.ts settings_ui/tests/editor-inline.edges.test.ts
git commit -m "feat: map editor graph x coordinates through a time viewport" -m "Horizontal zoom should only change the visible time slice, so the plot layer now accepts an optional viewport for X coordinates and pointer hit-testing while preserving full-duration defaults for existing callers. Full check and e2e were not run for this focused commit."
```

## Task 3: Visualizer Viewport State And Redraw

**Files:**
- Modify: `settings_ui/src/editor-inline/visualizer-state.ts`
- Modify: `settings_ui/src/editor-inline/visualizer-renderer.ts`
- Create: `settings_ui/src/editor-inline/viewport-actions.ts`
- Modify: `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`

- [ ] **Step 1: Add failing renderer tests**

Append tests to `settings_ui/tests/editor-inline.visualizer-renderer.test.ts`:

```ts
import { fullTimeViewport } from "../src/editor-inline/time-viewport.js";
import { applyVisualizerTimeViewport } from "../src/editor-inline/viewport-actions.js";
import { renderSelection, renderVisualizerTrack } from "../src/editor-inline/visualizer-renderer.js";
```

Add cases inside the existing `describe` block:

```ts
  it("redraws graph x positions through the visualizer viewport without changing pitch y scale", () => {
    const visualizer = mountVisualizer(voicedTrack);
    document.body.innerHTML = `
      <div class="aqe-visualizer" data-duration-ms="${voicedTrack.durationMs}" data-target-duration-ms="${voicedTrack.durationMs}">
        <svg class="aqe-visualizer-svg">
          <path class="aqe-intensity"></path>
          <g class="aqe-pitch"></g>
          <g class="aqe-learner-pitch"></g>
          <g class="aqe-labels"></g>
          <g class="aqe-x-axis"></g>
        </svg>
        <div class="aqe-visualizer-plot"></div>
        <div class="aqe-css-cursor">
          <div class="aqe-css-cursor-line"></div>
          <div class="aqe-css-cursor-flag">
            <div class="aqe-css-cursor-flag-box">
              <span class="aqe-css-cursor-flag-current">0 ms</span>
              <span class="aqe-css-cursor-flag-pitch"> / -- Hz</span>
            </div>
          </div>
        </div>
        <span class="aqe-cursor-label"></span>
      </div>
    `;
    const mounted = document.querySelector<VisualizerElement>(".aqe-visualizer")!;

    renderVisualizerTrack(mounted, voicedTrack);
    const fullPath = mounted.querySelector<SVGPathElement>(".aqe-pitch-path")?.getAttribute("d") || "";
    applyVisualizerTimeViewport(mounted, { startMs: 250, endMs: 750, durationMs: 1000 });
    const zoomedPath = mounted.querySelector<SVGPathElement>(".aqe-pitch-path")?.getAttribute("d") || "";

    expect(fullPath).not.toBe(zoomedPath);
    expect(zoomedPath).toContain("10.00");
    expect(zoomedPath).toContain("116.00");
  });

  it("clips selection rendering to the visible viewport while preserving selected milliseconds", () => {
    const visualizer = mountVisualizer(voicedTrack);
    visualizer.dataset.targetDurationMs = "1000";
    visualizer.dataset.viewportStartMs = "250";
    visualizer.dataset.viewportEndMs = "750";
    const selection = { startMs: 100, endMs: 500, mode: "selection" as const };

    renderSelection(visualizer, selection, null);

    const band = visualizer.querySelector<SVGRectElement>(".aqe-selection")!;
    expect(band.getAttribute("visibility")).toBe("visible");
    expect(band.getAttribute("x")).toBe(PLOT.left.toFixed(2));
    expect(Number(band.getAttribute("width"))).toBeGreaterThan(0);
  });

  it("hides the visible cursor when the cursor is outside the zoomed viewport", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const cssCursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor")!;
    visualizer.dataset.viewportStartMs = "250";
    visualizer.dataset.viewportEndMs = "750";

    renderCursor(visualizer, 900, voicedTrack.durationMs);

    expect(cssCursor.style.display).toBe("none");
  });
```

- [ ] **Step 2: Run renderer tests to verify failure**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.visualizer-renderer.test.ts
```

Expected: FAIL because viewport dataset helpers and redraw orchestration do not exist.

- [ ] **Step 3: Add visualizer dataset helpers**

Modify `settings_ui/src/editor-inline/visualizer-state.ts`:

```ts
import { fullTimeViewport, normalizeTimeViewport, type TimeViewport } from "./time-viewport.js";
```

Add:

```ts
export function readVisualizerTimeViewport(visualizer: VisualizerElement): TimeViewport {
  const durationMs = readVisualizerDurationMs(visualizer);
  const startMs = Number(visualizer.dataset.viewportStartMs || "0") || 0;
  const endMs = Number(visualizer.dataset.viewportEndMs || String(durationMs)) || durationMs;
  return normalizeTimeViewport(startMs, endMs, durationMs);
}

export function resetVisualizerTimeViewport(visualizer: VisualizerElement, durationMs = readVisualizerDurationMs(visualizer)): void {
  writeVisualizerTimeViewport(visualizer, fullTimeViewport(durationMs));
}

export function writeVisualizerTimeViewport(visualizer: VisualizerElement, viewport: TimeViewport): void {
  const normalized = normalizeTimeViewport(viewport.startMs, viewport.endMs, viewport.durationMs);
  visualizer.dataset.viewportStartMs = String(Math.round(normalized.startMs));
  visualizer.dataset.viewportEndMs = String(Math.round(normalized.endMs));
}
```

- [ ] **Step 4: Update renderer to use the active viewport**

Modify imports in `settings_ui/src/editor-inline/visualizer-renderer.ts`:

```ts
import { draftSelectionRegion, selectionRegion } from "./selection-state.js";
import { msVisibleInViewport } from "./time-viewport.js";
import {
  readVisualizerSelectionState,
  readVisualizerTargetDurationMs,
  readVisualizerTimeViewport,
  resetVisualizerTimeViewport,
} from "./visualizer-state.js";
```

In `renderGraphRequested()`, after duration fields are set:

```ts
  resetVisualizerTimeViewport(visualizer, 0);
```

In `renderVisualizerTrack()` after `visualizer.__aqeTrack = track;`:

```ts
  resetVisualizerTimeViewport(visualizer, track.durationMs || 0);
```

Export `renderProsodyTracks()` so viewport actions can reuse it:

```ts
export function renderProsodyTracks(visualizer: VisualizerElement): void {
  const target = visualizer.__aqeTrack;
  if (!target) return;
  const learner = visualizer.__aqeLearnerTrack;
  const durationMs = Math.max(target.durationMs || 0, learner?.durationMs || 0);
  const viewport = readVisualizerTimeViewport(visualizer);
  const pitchRange = combinedPitchRange(target, learner);
  visualizer.dataset.durationMs = String(durationMs);
  visualizer.dataset.targetDurationMs = String(target.durationMs || 0);
  visualizer.dataset.learnerDurationMs = String(learner?.durationMs || 0);
  const intensity = visualizer.querySelector<SVGPathElement>(".aqe-intensity");
  if (intensity) intensity.setAttribute("d", pathForIntensity(target.points, durationMs, viewport));
  drawPitch(visualizer, target, {
    durationMs,
    pitchMaxHz: pitchRange.maxHz,
    pitchMinHz: pitchRange.minHz,
    viewport,
  });
  if (learner) {
    drawLearnerPitch(visualizer, learner, {
      durationMs,
      pitchMaxHz: pitchRange.maxHz,
      pitchMinHz: pitchRange.minHz,
      viewport,
    });
  } else {
    clearLearnerVisualizerTrack(visualizer);
  }
  drawLabels(visualizer, target, {
    pitchMaxHz: pitchRange.maxHz,
    pitchMinHz: pitchRange.minHz,
  });
  drawXAxis(visualizer, durationMs, viewport);
}
```

In `renderSelection()`, replace `startX` and `endX` calculation with viewport clipping:

```ts
  const viewport = readVisualizerTimeViewport(visualizer);
  const visibleStartMs = Math.max(activeSelection.startMs, viewport.startMs);
  const visibleEndMs = Math.min(activeSelection.endMs, viewport.endMs);
  if (visibleEndMs < visibleStartMs) {
    band.setAttribute("width", "0");
    band.setAttribute("visibility", "hidden");
    startEdge?.setAttribute("visibility", "hidden");
    endEdge?.setAttribute("visibility", "hidden");
    startHandle?.setAttribute("visibility", "hidden");
    endHandle?.setAttribute("visibility", "hidden");
    startGrip?.setAttribute("visibility", "hidden");
    endGrip?.setAttribute("visibility", "hidden");
    clearSelectionOverlayGeometry(visualizer);
    return;
  }
  const startX = xForMs(visibleStartMs, durationMs, viewport);
  const endX = xForMs(visibleEndMs, durationMs, viewport);
```

In `renderCursorProjection()`, pass the viewport:

```ts
  const viewport = readVisualizerTimeViewport(visualizer);
  const x = xForMs(ms, durationMs, viewport);
```

In `renderCssCursorGeometry()`, hide when offscreen:

```ts
function renderCssCursorGeometry(visualizer: VisualizerElement, nodes: CursorRenderCache, cursorX: number, ms?: number): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  const cursor = nodes.cssCursor;
  if (!cursor) return;
  if (typeof ms === "number" && !msVisibleInViewport(ms, viewport)) {
    cursor.style.display = "none";
    cursor.style.transition = "none";
    return;
  }
  const scale = cssScaleFor(visualizer);
  cursor.style.display = "block";
  cursor.style.transition = "none";
  cursor.style.transform = `translate3d(${cssXForViewBoxX(visualizer, cursorX).toFixed(2)}px, 0, 0)`;
```

Update the call in `renderCursorProjection()`:

```ts
    renderCssCursorGeometry(visualizer, nodes, x, ms);
```

Add a redraw helper:

```ts
export function renderCurrentSelectionFromState(visualizer: VisualizerElement): void {
  const selectionState = readVisualizerSelectionState(visualizer);
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  renderSelection(
    visualizer,
    selectionRegion(selectionState, durationMs),
    draftSelectionRegion(selectionState, durationMs),
  );
}
```

- [ ] **Step 5: Add viewport redraw orchestration**

Create `settings_ui/src/editor-inline/viewport-actions.ts`:

```ts
import { renderCursor, renderCurrentSelectionFromState, renderProsodyTracks } from "./visualizer-renderer.js";
import {
  readVisualizerCursorMs,
  readVisualizerDurationMs,
  readVisualizerTimeViewport,
  writeVisualizerTimeViewport,
} from "./visualizer-state.js";
import {
  msVisibleInViewport,
  panTimeViewport,
  timeViewportSpan,
  type TimeViewport,
} from "./time-viewport.js";
import type { VisualizerElement } from "./types.js";

const PLAYBACK_FOLLOW_MARGIN_RATIO = 0.12;

export function applyVisualizerTimeViewport(visualizer: VisualizerElement, viewport: TimeViewport): void {
  writeVisualizerTimeViewport(visualizer, viewport);
  redrawVisualizerForCurrentViewport(visualizer);
}

export function redrawVisualizerForCurrentViewport(visualizer: VisualizerElement): void {
  if (visualizer.dataset.hasTrack === "true") {
    renderProsodyTracks(visualizer);
  }
  renderCurrentSelectionFromState(visualizer);
  renderCursor(
    visualizer,
    readVisualizerCursorMs(visualizer),
    readVisualizerDurationMs(visualizer),
  );
}

export function ensurePlaybackCursorVisible(visualizer: VisualizerElement, cursorMs: number): boolean {
  const viewport = readVisualizerTimeViewport(visualizer);
  if (viewport.durationMs <= 0 || timeViewportSpan(viewport) >= viewport.durationMs) return false;
  if (msVisibleInViewport(cursorMs, viewport)) {
    const span = timeViewportSpan(viewport);
    const marginMs = span * PLAYBACK_FOLLOW_MARGIN_RATIO;
    if (cursorMs >= viewport.startMs + marginMs && cursorMs <= viewport.endMs - marginMs) {
      return false;
    }
  }
  const span = timeViewportSpan(viewport);
  const targetStart = cursorMs - span * PLAYBACK_FOLLOW_MARGIN_RATIO;
  applyVisualizerTimeViewport(visualizer, panTimeViewport(viewport, targetStart - viewport.startMs));
  return true;
}
```

- [ ] **Step 6: Run renderer tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.visualizer-renderer.test.ts
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add settings_ui/src/editor-inline/visualizer-state.ts settings_ui/src/editor-inline/visualizer-renderer.ts settings_ui/src/editor-inline/viewport-actions.ts settings_ui/tests/editor-inline.visualizer-renderer.test.ts
git commit -m "feat: render editor graph through visualizer time viewport" -m "The graph now stores a per-field visible time window and redraws pitch, intensity, selection, and cursor X geometry from that window while keeping pitch and intensity Y scaling tied to the full track. Full check and e2e were not run for this focused commit."
```

## Task 4: Viewport-Aware Selection And Cursor Gestures

**Files:**
- Modify: `settings_ui/src/editor-inline/selection-gestures.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/globals.d.ts`
- Modify: `settings_ui/tests/editor-inline.selection-creation.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.selection-resize.integration.test.ts`

- [ ] **Step 1: Add failing integration coverage for zoomed hit-testing**

In `settings_ui/tests/editor-inline.selection-creation.integration.test.ts`, add:

```ts
  it("creates selections using visible viewport coordinates when zoomed", async () => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.25, 0.75);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(250);
    expect(state?.viewportEndMs).toBe(750);
    expect(state?.selectionStartMs).toBe(375);
    expect(state?.selectionEndMs).toBe(625);
  });
```

In `settings_ui/tests/editor-inline.selection-resize.integration.test.ts`, add:

```ts
  it("resizes selection handles using visible viewport coordinates when zoomed", async () => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.25, 0.75);
    dragSelectionHandle(svg, "end", 1);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.selectionStartMs).toBe(375);
    expect(state?.selectionEndMs).toBe(750);
  });
```

- [ ] **Step 2: Run selection tests to verify failure**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection-creation.integration.test.ts editor-inline.selection-resize.integration.test.ts
```

Expected: FAIL because `__aqeSetTimeViewportForTest` is missing and pointer hit-testing still uses full duration.

- [ ] **Step 3: Use viewport-aware hit-testing in selection gestures**

Modify imports in `settings_ui/src/editor-inline/selection-gestures.ts`:

```ts
  readVisualizerTimeViewport,
```

from `./visualizer-state.js`.

Update every `cursorMsFromEvent(..., svg, durationMs)` call in this file to pass the visualizer viewport:

```ts
cursorMsFromEvent(event, svg, durationMs, readVisualizerTimeViewport(visualizer))
```

Apply that pattern in:

- `startCursorDrag()`
- `clickExpandedSelection()` caller values
- `startSelectionGesture()`
- `startSelectionResizeGesture()`
- `scrubMsFromEvent()`

- [ ] **Step 4: Expose viewport state to tests**

Modify `settings_ui/src/editor-inline/types.ts` and extend `GraphStateForTest`:

```ts
  viewportEndMs: number;
  viewportStartMs: number;
```

Modify `settings_ui/src/editor-inline/test-contract.ts` imports:

```ts
import { applyVisualizerTimeViewport } from "./viewport-actions.js";
```

Add `"__aqeSetTimeViewportForTest"` to `EDITOR_TEST_WINDOW_CONTRACT_NAMES`.

In `installEditorTestWindowContract()`:

```ts
  window.__aqeSetTimeViewportForTest = setTimeViewportForTest;
```

Add the helper:

```ts
export function setTimeViewportForTest(ord: number, startMs: number, endMs: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  applyVisualizerTimeViewport(visualizer, {
    durationMs: readVisualizerTargetDurationMs(visualizer),
    endMs,
    startMs,
  });
  return true;
}
```

In `graphStateForTest()` return object:

```ts
    viewportEndMs: Number(visualizer.dataset.viewportEndMs || visualizer.dataset.durationMs || "0"),
    viewportStartMs: Number(visualizer.dataset.viewportStartMs || "0"),
```

Modify `settings_ui/src/editor-inline/globals.d.ts`:

```ts
    __aqeSetTimeViewportForTest?: ((ord: number, startMs: number, endMs: number) => boolean) | undefined;
```

- [ ] **Step 5: Run selection tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection-creation.integration.test.ts editor-inline.selection-resize.integration.test.ts
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

```bash
git add settings_ui/src/editor-inline/selection-gestures.ts settings_ui/src/editor-inline/test-contract.ts settings_ui/src/editor-inline/types.ts settings_ui/src/editor-inline/globals.d.ts settings_ui/tests/editor-inline.selection-creation.integration.test.ts settings_ui/tests/editor-inline.selection-resize.integration.test.ts
git commit -m "feat: make editor selection gestures respect time zoom" -m "Cursor scrubbing and selection editing must operate in real milliseconds even when the graph only shows a time slice. The gesture layer now converts pointer positions through the active viewport and exposes viewport state for focused tests. Full check and e2e were not run for this focused commit."
```

## Task 5: Zoom Controls, Icons, And Wheel/Keyboard Gestures

**Files:**
- Create: `settings_ui/src/editor-inline/ZoomControls.svelte`
- Create: `settings_ui/src/editor-inline/zoom-actions.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/styles/visualizer.css`
- Modify: `settings_ui/src/lib/icon-types.ts`
- Modify: `settings_ui/src/lib/CommandIcon.svelte`
- Modify: `settings_ui/tests/editor-inline.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.window-contract.test.ts`

- [ ] **Step 1: Add failing integration tests for controls and gestures**

In `settings_ui/tests/editor-inline.integration.test.ts`, add:

```ts
  it("zooms, pans, fits, and zooms to selection from graph controls", async () => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')?.click();
    let state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    expect(state?.viewportEndMs).toBeLessThan(track.durationMs);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-fit-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);

    dragGraphSelection(svg, 0.25, 0.5);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-selection-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeLessThanOrEqual(state?.selectionStartMs ?? 0);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(state?.selectionEndMs ?? 0);
    expect((state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0)).toBeLessThan(track.durationMs);
  });

  it("uses graph wheel and keyboard gestures for horizontal zoom only", async () => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    svg.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      ctrlKey: true,
      deltaY: -100,
    }));
    let state = window.__aqeGraphStateForTest?.(0);
    expect((state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0)).toBeLessThan(track.durationMs);

    const beforePanStart = state?.viewportStartMs ?? 0;
    svg.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaX: 100,
      shiftKey: true,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThanOrEqual(beforePanStart);

    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    visualizer.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "0" }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);
  });
```

- [ ] **Step 2: Run integration tests to verify failure**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.integration.test.ts
```

Expected: FAIL because zoom controls, icons, and handlers are missing.

- [ ] **Step 3: Add zoom icons**

Modify `settings_ui/src/lib/icon-types.ts`:

```ts
  | "maximize-2"
  | "scan-search"
  | "zoom-in"
  | "zoom-out"
```

Modify `settings_ui/src/lib/CommandIcon.svelte` imports:

```ts
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import ScanSearch from "@lucide/svelte/icons/scan-search";
  import ZoomIn from "@lucide/svelte/icons/zoom-in";
  import ZoomOut from "@lucide/svelte/icons/zoom-out";
```

Add branches before the custom icons:

```svelte
  {:else if icon === "maximize-2"}
    <Maximize2 {size} {strokeWidth} />
  {:else if icon === "scan-search"}
    <ScanSearch {size} {strokeWidth} />
  {:else if icon === "zoom-in"}
    <ZoomIn {size} {strokeWidth} />
  {:else if icon === "zoom-out"}
    <ZoomOut {size} {strokeWidth} />
```

- [ ] **Step 4: Add zoom action functions**

Create `settings_ui/src/editor-inline/zoom-actions.ts`:

```ts
import { t } from "../lib/i18n.js";
import { graphPixelBounds } from "./plot.js";
import { selectionForVisualizer } from "./selection-controller.js";
import {
  fullTimeViewport,
  isFullTimeViewport,
  panTimeViewport,
  TIME_VIEWPORT_ZOOM_FACTOR,
  timeViewportSpan,
  zoomTimeViewport,
  zoomTimeViewportAroundRatio,
  zoomTimeViewportToRange,
} from "./time-viewport.js";
import type { VisualizerElement } from "./types.js";
import { applyVisualizerTimeViewport } from "./viewport-actions.js";
import {
  readVisualizerCursorMs,
  readVisualizerTargetDurationMs,
  readVisualizerTimeViewport,
} from "./visualizer-state.js";

const WHEEL_PAN_RATIO = 0.0015;
const KEYBOARD_PAN_RATIO = 0.2;

export function zoomInForVisualizer(visualizer: VisualizerElement): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewport(viewport, readVisualizerCursorMs(visualizer), TIME_VIEWPORT_ZOOM_FACTOR),
  );
}

export function zoomOutForVisualizer(visualizer: VisualizerElement): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewport(viewport, readVisualizerCursorMs(visualizer), 1 / TIME_VIEWPORT_ZOOM_FACTOR),
  );
}

export function fitTimeViewportForVisualizer(visualizer: VisualizerElement): void {
  applyVisualizerTimeViewport(visualizer, fullTimeViewport(readVisualizerTargetDurationMs(visualizer)));
}

export function zoomSelectionForVisualizer(visualizer: VisualizerElement): boolean {
  const selection = selectionForVisualizer(visualizer);
  if (!selection || selection.startMs === 0 && selection.endMs === readVisualizerTargetDurationMs(visualizer)) {
    return false;
  }
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewportToRange(selection.startMs, selection.endMs, readVisualizerTargetDurationMs(visualizer)),
  );
  return true;
}

export function handleVisualizerWheelZoom(event: WheelEvent, visualizer: VisualizerElement): void {
  if (visualizer.dataset.hasTrack !== "true") return;
  if (!event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey) return;
  const viewport = readVisualizerTimeViewport(visualizer);
  if (event.ctrlKey || event.metaKey || event.altKey) {
    event.preventDefault();
    const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
    const bounds = svg ? graphPixelBounds(svg) : null;
    const ratio = bounds ? Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)) : 0.5;
    applyVisualizerTimeViewport(
      visualizer,
      zoomTimeViewportAroundRatio(viewport, ratio, event.deltaY < 0 ? TIME_VIEWPORT_ZOOM_FACTOR : 1 / TIME_VIEWPORT_ZOOM_FACTOR),
    );
    return;
  }
  if (event.shiftKey && !isFullTimeViewport(viewport)) {
    event.preventDefault();
    const delta = (event.deltaX || event.deltaY) * timeViewportSpan(viewport) * WHEEL_PAN_RATIO;
    applyVisualizerTimeViewport(visualizer, panTimeViewport(viewport, delta));
  }
}

export function handleVisualizerZoomKeyDown(event: KeyboardEvent, visualizer: VisualizerElement): boolean {
  if (event.defaultPrevented || visualizer.dataset.hasTrack !== "true") return false;
  if (event.key === "+" || event.key === "=") {
    event.preventDefault();
    zoomInForVisualizer(visualizer);
    return true;
  }
  if (event.key === "-") {
    event.preventDefault();
    zoomOutForVisualizer(visualizer);
    return true;
  }
  if (event.key === "0") {
    event.preventDefault();
    fitTimeViewportForVisualizer(visualizer);
    return true;
  }
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    const viewport = readVisualizerTimeViewport(visualizer);
    if (isFullTimeViewport(viewport)) return false;
    event.preventDefault();
    const direction = event.key === "ArrowLeft" ? -1 : 1;
    applyVisualizerTimeViewport(visualizer, panTimeViewport(viewport, direction * timeViewportSpan(viewport) * KEYBOARD_PAN_RATIO));
    return true;
  }
  return false;
}
```

- [ ] **Step 5: Add Svelte zoom controls**

Create `settings_ui/src/editor-inline/ZoomControls.svelte`:

```svelte
<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { visualizerForOrd } from "./dom-selectors.js";
  import type { FieldTarget } from "./types.js";
  import {
    fitTimeViewportForVisualizer,
    zoomInForVisualizer,
    zoomOutForVisualizer,
    zoomSelectionForVisualizer,
  } from "./zoom-actions.js";

  const { target }: { target: FieldTarget } = $props();
  let hasTrack = $state(false);
  let hasSelection = $state(false);
  let observer: MutationObserver | null = null;

  function sync(): void {
    const visualizer = visualizerForOrd(target.ord);
    hasTrack = visualizer?.dataset.hasTrack === "true";
    hasSelection = visualizer?.dataset.selectionActive === "true"
      && visualizer.dataset.selectionStartMs !== "0"
      && visualizer.dataset.selectionEndMs !== visualizer.dataset.targetDurationMs;
  }

  function withVisualizer(action: (visualizer: NonNullable<ReturnType<typeof visualizerForOrd>>) => void): void {
    const visualizer = visualizerForOrd(target.ord);
    if (!visualizer) return;
    action(visualizer);
    sync();
  }

  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    sync();
    if (!visualizer) return;
    observer = new MutationObserver(sync);
    observer.observe(visualizer, {
      attributeFilter: [
        "data-has-track",
        "data-selection-active",
        "data-selection-start-ms",
        "data-selection-end-ms",
        "data-target-duration-ms",
        "data-viewport-start-ms",
        "data-viewport-end-ms",
      ],
    });
  });

  onDestroy(() => {
    observer?.disconnect();
    observer = null;
  });
</script>

<div class="aqe-zoom-controls" data-testid={`aqe-zoom-controls-${target.ord}`} hidden={!hasTrack}>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button"
        data-testid={`aqe-zoom-out-${target.ord}`}
        data-aqe-tooltip-content={t("editor.zoom.out")}
        aria-label={t("editor.zoom.out")}
        onclick={() => withVisualizer(zoomOutForVisualizer)}
      >
        <EditorCommandIcon icon="zoom-out" />
        <span class="aqe-button-label">{t("editor.zoom.out")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button"
        data-testid={`aqe-zoom-in-${target.ord}`}
        data-aqe-tooltip-content={t("editor.zoom.in")}
        aria-label={t("editor.zoom.in")}
        onclick={() => withVisualizer(zoomInForVisualizer)}
      >
        <EditorCommandIcon icon="zoom-in" />
        <span class="aqe-button-label">{t("editor.zoom.in")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button"
        data-testid={`aqe-zoom-selection-${target.ord}`}
        data-aqe-tooltip-content={t("editor.zoom.selection")}
        aria-label={t("editor.zoom.selection")}
        disabled={!hasSelection}
        onclick={() => withVisualizer((visualizer) => { zoomSelectionForVisualizer(visualizer); })}
      >
        <EditorCommandIcon icon="scan-search" />
        <span class="aqe-button-label">{t("editor.zoom.selection")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button"
        data-testid={`aqe-zoom-fit-${target.ord}`}
        data-aqe-tooltip-content={t("editor.zoom.fit")}
        aria-label={t("editor.zoom.fit")}
        onclick={() => withVisualizer(fitTimeViewportForVisualizer)}
      >
        <EditorCommandIcon icon="maximize-2" />
        <span class="aqe-button-label">{t("editor.zoom.fit")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
</div>
```

Add English messages in `addon/anki_audio_quick_editor/locales/en.json` and mirror the same keys into every locale file with English fallback text:

```json
  "editor.zoom.fit": "Fit whole clip",
  "editor.zoom.in": "Zoom in",
  "editor.zoom.out": "Zoom out",
  "editor.zoom.selection": "Zoom to selection"
```

- [ ] **Step 6: Wire controls and gestures into EditorControls**

Modify `settings_ui/src/editor-inline/EditorControls.svelte` imports:

```ts
  import ZoomControls from "./ZoomControls.svelte";
```

Add to existing actions import or a separate import:

```ts
  import {
    handleVisualizerWheelZoom,
    handleVisualizerZoomKeyDown,
  } from "./zoom-actions.js";
```

Add viewport dataset attributes to `.aqe-visualizer`:

```svelte
      data-viewport-start-ms="0"
      data-viewport-end-ms="0"
```

Update `onkeydown`:

```svelte
      onkeydown={(event) => {
        if (handleVisualizerZoomKeyDown(event, event.currentTarget as HTMLElement as never)) return;
        handleVisualizerKeyDown(event, target.ord);
      }}
```

Use a local helper to avoid the cast:

```ts
  function handleGraphKeyDown(event: KeyboardEvent): void {
    const visualizer = visualizerForOrd(target.ord);
    if (visualizer && handleVisualizerZoomKeyDown(event, visualizer)) return;
    handleVisualizerKeyDown(event, target.ord);
  }
```

Then:

```svelte
      onkeydown={handleGraphKeyDown}
```

Place zoom controls before `.aqe-visualizer-plot`:

```svelte
      <ZoomControls {target} />
```

Add `onwheel` to the SVG:

```svelte
          onwheel={(event) => {
            const visualizer = visualizerForOrd(target.ord);
            if (visualizer) handleVisualizerWheelZoom(event, visualizer);
          }}
```

Add clip path and graph layer clip attributes inside the SVG:

```svelte
      <defs>
        <clipPath id={`aqe-plot-clip-${target.ord}`}>
          <rect
            x={PLOT.left}
            y={PLOT.top}
            width={PLOT.width - PLOT.left - PLOT.right}
            height={PLOT.height - PLOT.top - PLOT.bottom}
          ></rect>
        </clipPath>
      </defs>
      <path class="aqe-intensity" data-testid={`aqe-intensity-${target.ord}`} clip-path={`url(#aqe-plot-clip-${target.ord})`} d=""></path>
      <g class="aqe-pitch" data-testid={`aqe-pitch-${target.ord}`} clip-path={`url(#aqe-plot-clip-${target.ord})`}></g>
      <g class="aqe-learner-pitch" data-testid={`aqe-learner-pitch-${target.ord}`} clip-path={`url(#aqe-plot-clip-${target.ord})`}></g>
```

- [ ] **Step 7: Style zoom controls**

Modify `settings_ui/src/editor-inline/styles/visualizer.css`:

```css
.aqe-zoom-controls {
  align-items: center;
  display: flex;
  gap: 4px;
  justify-content: flex-end;
  margin-top: 8px;
  width: 100%;
}

.aqe-zoom-controls[hidden] {
  display: none;
}

.aqe-zoom-button {
  height: 26px;
  min-height: 26px;
  min-width: 26px;
  padding: 0;
  width: 26px;
}
```

- [ ] **Step 8: Run focused frontend tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.integration.test.ts editor-inline.window-contract.test.ts
```

Expected: PASS.

- [ ] **Step 9: Commit Task 5**

```bash
git add settings_ui/src/editor-inline/ZoomControls.svelte settings_ui/src/editor-inline/zoom-actions.ts settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/styles/visualizer.css settings_ui/src/lib/icon-types.ts settings_ui/src/lib/CommandIcon.svelte addon/anki_audio_quick_editor/locales/en.json addon/anki_audio_quick_editor/locales/de.json addon/anki_audio_quick_editor/locales/ja.json addon/anki_audio_quick_editor/locales/ru.json addon/anki_audio_quick_editor/locales/vi.json addon/anki_audio_quick_editor/locales/zh_CN.json addon/anki_audio_quick_editor/locales/zh_TW.json settings_ui/tests/editor-inline.integration.test.ts settings_ui/tests/editor-inline.window-contract.test.ts
git commit -m "feat: add horizontal zoom controls to editor graph" -m "Users need the same practical time navigation expected from audio editors without changing pitch scale. The graph now exposes zoom in, zoom out, fit, zoom-to-selection, and modified wheel or keyboard gestures entirely in the editor frontend. Full check and e2e were not run for this focused commit."
```

## Task 6: Playback Follow In Zoomed Viewports

**Files:**
- Modify: `settings_ui/src/editor-inline/playback-controller.ts`
- Modify: `settings_ui/tests/editor-inline.playback.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.actions.progress.test.ts`

- [ ] **Step 1: Add failing playback follow tests**

In `settings_ui/tests/editor-inline.playback.integration.test.ts`, add:

```ts
  it("pans the zoomed viewport as playback progress approaches the visible edge", async () => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    window.__aqeInstallAudioPlaybackTestDriverForTest?.(0);
    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;

    startManualProgressClock(visualizer as never, 450);
    vi.advanceTimersByTime(120);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    expect(state?.cursorMs).toBeGreaterThanOrEqual(450);
  });
```

If the test file does not already use fake timers, add:

```ts
import { afterEach, beforeEach, vi } from "vitest";
```

and inside the describe:

```ts
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });
```

- [ ] **Step 2: Run playback tests to verify failure**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.playback.integration.test.ts editor-inline.actions.progress.test.ts
```

Expected: FAIL because playback progress paints do not pan the viewport.

- [ ] **Step 3: Pan viewport during playback progress**

Modify `settings_ui/src/editor-inline/playback-controller.ts` imports:

```ts
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
```

In `paintProgressFromClock()`, before `renderPlaybackCursor(...)`:

```ts
    ensurePlaybackCursorVisible(visualizer, nextMs);
```

In `startProgressClock()`, after `deps.setCursor(...)`:

```ts
    ensurePlaybackCursorVisible(visualizer, clampedStartMs);
```

This keeps cursor projection and graph paths in sync because `ensurePlaybackCursorVisible()` calls `applyVisualizerTimeViewport()` only when panning is needed.

- [ ] **Step 4: Run playback tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.playback.integration.test.ts editor-inline.actions.progress.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit Task 6**

```bash
git add settings_ui/src/editor-inline/playback-controller.ts settings_ui/tests/editor-inline.playback.integration.test.ts settings_ui/tests/editor-inline.actions.progress.test.ts
git commit -m "feat: keep editor playback cursor visible while zoomed" -m "Playback in a zoomed audio editor should follow the moving time cursor instead of letting it disappear offscreen. Progress painting now pans the horizontal viewport as needed without changing playback regions or Y scaling. Full check and e2e were not run for this focused commit."
```

## Task 7: Reset Rules And New Note Behavior

**Files:**
- Modify: `settings_ui/src/editor-inline/graph-actions.ts`
- Modify: `settings_ui/src/editor-inline/visualizer-renderer.ts`
- Modify: `settings_ui/tests/editor-inline.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.runtime.integration.test.ts`

- [ ] **Step 1: Add failing reset behavior tests**

In `settings_ui/tests/editor-inline.integration.test.ts`, add:

```ts
  it("resets zoom to fit when a graph is redrawn for a new track", async () => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);

    window.__aqeSetVisualizer?.(0, { ...track, durationMs: 2000, sourceFilename: "next.mp3" }, 0);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(2000);
  });
```

In `settings_ui/tests/editor-inline.runtime.integration.test.ts`, add:

```ts
  it("clears viewport state when preparing for a new note", async () => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);

    window.__aqePrepareForNewNote?.();

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(0);
  });
```

- [ ] **Step 2: Run reset tests to verify failure if reset is incomplete**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.integration.test.ts editor-inline.runtime.integration.test.ts
```

Expected: FAIL if viewport reset has not been wired through every graph reset path.

- [ ] **Step 3: Reset viewport in graph lifecycle**

In `settings_ui/src/editor-inline/graph-actions.ts`, import:

```ts
  resetVisualizerTimeViewport,
```

from `./visualizer-state.js`.

In `prepareForNewNote()`, after `visualizer.dataset.durationMs = "0";`:

```ts
    resetVisualizerTimeViewport(visualizer, 0);
```

Confirm `renderGraphRequested()` and `renderVisualizerTrack()` already reset in `visualizer-renderer.ts` from Task 3. If not, add those calls there now:

```ts
  resetVisualizerTimeViewport(visualizer, 0);
```

for graph requested state, and:

```ts
  resetVisualizerTimeViewport(visualizer, track.durationMs || 0);
```

for rendered track state.

- [ ] **Step 4: Run reset tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.integration.test.ts editor-inline.runtime.integration.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit Task 7**

```bash
git add settings_ui/src/editor-inline/graph-actions.ts settings_ui/src/editor-inline/visualizer-renderer.ts settings_ui/tests/editor-inline.integration.test.ts settings_ui/tests/editor-inline.runtime.integration.test.ts
git commit -m "fix: reset editor graph zoom with graph lifecycle" -m "Viewport state belongs to the current rendered media, so new notes and graph redraws must not inherit stale zoom windows from earlier audio. Resetting the viewport with graph lifecycle state keeps selection, cursor, and playback coordinates tied to the active clip. Full check and e2e were not run for this focused commit."
```

## Task 8: Real Anki E2E Coverage

**Files:**
- Create: `e2e/test_editor_graph_zoom_workflow.py`
- Modify: `e2e/editor_graph_helpers.py`

- [ ] **Step 1: Add e2e helper for zoom state**

Modify `e2e/editor_graph_helpers.py` and add:

```python
def _graph_zoom_state_js(ord: int = 0) -> str:
    return f"""
    (() => {{
      const state = window.__aqeGraphStateForTest?.({ord});
      if (!state) return null;
      return {{
        cursorMs: state.cursorMs,
        durationMs: state.durationMs,
        selectionEndMs: state.selectionEndMs,
        selectionStartMs: state.selectionStartMs,
        viewportEndMs: state.viewportEndMs,
        viewportStartMs: state.viewportStartMs,
        xAxisLabels: state.xAxisLabels,
      }};
    }})()
    """
```

- [ ] **Step 2: Add e2e test for graph zoom workflow**

Create `e2e/test_editor_graph_zoom_workflow.py`:

```python
"""E2E tests for inline editor graph horizontal zoom."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_zoom_state_js,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import (
    generate_tone,
    wait_for_js_condition,
    wait_for_selector,
)


def test_editor_graph_horizontal_zoom_controls_preserve_time_selection(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_zoom_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=4.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        zoomed = wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-zoom-in-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] > 0
            and value["viewportEndMs"] < value["durationMs"],
            timeout=5.0,
        )
        assert zoomed["viewportEndMs"] - zoomed["viewportStartMs"] < zoomed["durationMs"]

        selected_zoom = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
              if (!svg) return null;
              const rect = svg.getBoundingClientRect();
              const left = rect.left + 44;
              const width = 566;
              const EventCtor = window.PointerEvent || window.MouseEvent;
              svg.dispatchEvent(new EventCtor('pointerdown', { bubbles: true, clientX: left + width * 0.25, clientY: rect.top + 20, shiftKey: true }));
              window.dispatchEvent(new EventCtor('pointermove', { bubbles: true, clientX: left + width * 0.75, clientY: rect.top + 20, shiftKey: true }));
              window.dispatchEvent(new EventCtor('pointerup', { bubbles: true, clientX: left + width * 0.75, clientY: rect.top + 20, shiftKey: true }));
              document.querySelector('[data-testid="aqe-zoom-selection-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["selectionActive"] is True
            and value["viewportStartMs"] <= value["selectionStartMs"]
            and value["viewportEndMs"] >= value["selectionEndMs"],
            timeout=5.0,
        )
        assert selected_zoom["selectionEndMs"] > selected_zoom["selectionStartMs"]

        fit = wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-zoom-fit-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] == value["durationMs"],
            timeout=5.0,
        )
        assert fit["viewportStartMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 3: Run the new e2e test**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_graph_zoom_workflow.py
```

Expected: PASS. If `scripts/dev.py test-e2e` does not accept a file argument in this repository, run the full e2e command in Step 5 instead and record that focused file selection is unsupported.

- [ ] **Step 4: Run frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: PASS.

- [ ] **Step 5: Commit Task 8**

```bash
git add e2e/test_editor_graph_zoom_workflow.py e2e/editor_graph_helpers.py
git commit -m "test: cover editor graph horizontal zoom in Anki" -m "The zoom feature affects real WebView pointer geometry, so unit tests are not enough. This e2e workflow proves zoom controls, selection mapping, and fit reset work against the Anki editor runtime. Full check and e2e were not run for this focused commit unless recorded in the terminal output."
```

## Task 9: Final Verification And Documentation Check

**Files:**
- Modify: `WEBVIEW_AND_TEMPLATES.md` only if implementation introduces a new generated-bundle caveat.
- Modify: `README.md` only if the visible feature list should explicitly mention graph zoom.

- [ ] **Step 1: Run full reusable quality gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 2: Run full e2e suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 3: Inspect docs impact**

Run:

```bash
rg -n "prosody visualization|draggable playback start cursor|graph|zoom" README.md WEBVIEW_AND_TEMPLATES.md EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md TESTING.md
```

Expected: the current docs either remain accurate or clearly need a small README/TESTING mention. Do not edit generated bundles in `addon/anki_audio_quick_editor/templates/`.

- [ ] **Step 4: Commit docs if needed**

If docs were edited:

```bash
git add README.md TESTING.md WEBVIEW_AND_TEMPLATES.md
git commit -m "docs: describe editor graph horizontal zoom behavior" -m "The editor graph now supports horizontal time navigation, so user-facing and testing docs should mention that zoom changes the visible time window without changing audio processing or pitch scaling. Full check and e2e status is recorded in the implementation thread."
```

If no docs were edited, record that no docs commit is needed because the existing docs already describe the graph at the right level of detail.

- [ ] **Step 5: Final implementation commit if verification fixes were needed**

If Step 1 or Step 2 required small fixes, commit those fixes with a message that names the failure and the impact:

```bash
git add settings_ui/src/editor-inline settings_ui/tests e2e
git commit -m "fix: stabilize editor graph zoom verification" -m "The full quality gate exposed issues in the zoom integration that focused tests missed. This commit keeps viewport state, graph rendering, and real WebView behavior aligned before the branch is handed off. Full check and e2e status is recorded in the implementation thread."
```

## Self-Review Notes

- Scope coverage: the plan covers horizontal zoom controls, wheel/key gestures, viewport math, graph redraw, selection and cursor hit-testing, playback follow, reset behavior, frontend tests, and real Anki e2e coverage.
- Y scale invariant: every task keeps pitch and intensity Y calculations tied to the existing full-track pitch range and intensity normalization.
- Contract boundary: no Python bridge payloads, generated contracts, audio processing, or config schema changes are required.
- Test coverage: pure math, plot helpers, renderer, selection gestures, controls, playback follow, lifecycle reset, and real WebView behavior are covered before full `check` and `test-e2e`.
