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
import { graphPixelBounds } from "./plot.js";
import {
  readVisualizerCursorMs,
  readVisualizerTargetDurationMs,
  readVisualizerTimeViewport,
} from "./visualizer-state.js";

const WHEEL_PAN_RATIO = 0.0015;
const WHEEL_ZOOM_SENSITIVITY = 0.0015;
const WHEEL_ZOOM_MAX_ABS_DELTA = 300;
const KEYBOARD_PAN_RATIO = 0.2;

export function zoomInForVisualizer(visualizer: VisualizerElement): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  const anchorMs = readVisualizerCursorMs(visualizer);
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewport(viewport, anchorMs, TIME_VIEWPORT_ZOOM_FACTOR),
  );
}

export function zoomOutForVisualizer(visualizer: VisualizerElement): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  const anchorMs = readVisualizerCursorMs(visualizer);
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewport(viewport, anchorMs, 1 / TIME_VIEWPORT_ZOOM_FACTOR),
  );
}

export function fitTimeViewportForVisualizer(visualizer: VisualizerElement): void {
  applyVisualizerTimeViewport(
    visualizer,
    fullTimeViewport(readVisualizerTargetDurationMs(visualizer)),
  );
}

export function zoomSelectionForVisualizer(visualizer: VisualizerElement): boolean {
  const selection = selectionForVisualizer(visualizer);
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  if (!selection || selection.mode !== "selection") return false;
  applyVisualizerTimeViewport(
    visualizer,
    zoomTimeViewportToRange(selection.startMs, selection.endMs, durationMs),
  );
  return true;
}

export function handleVisualizerWheelZoom(event: WheelEvent, visualizer: VisualizerElement): boolean {
  if (visualizer.dataset.hasTrack !== "true") return false;
  const viewport = readVisualizerTimeViewport(visualizer);
  if (event.ctrlKey || event.metaKey || event.altKey) {
    event.preventDefault();
    const target = event.currentTarget instanceof SVGSVGElement
      ? event.currentTarget
      : visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
    const bounds = target ? graphPixelBounds(target) : null;
    const ratio = bounds ? Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)) : 0.5;
    const factor = wheelZoomFactor(event.deltaY);
    applyVisualizerTimeViewport(visualizer, zoomTimeViewportAroundRatio(viewport, ratio, factor));
    return true;
  }
  const horizontalDelta = Number(event.deltaX) || 0;
  const verticalDelta = Number(event.deltaY) || 0;
  const shouldPan = !isFullTimeViewport(viewport)
    && (event.shiftKey || Math.abs(horizontalDelta) > Math.abs(verticalDelta));
  if (!shouldPan) return false;
  const panDelta = event.shiftKey ? (horizontalDelta || verticalDelta) : horizontalDelta;
  if (!panDelta) return false;
  event.preventDefault();
  const delta = panDelta * timeViewportSpan(viewport) * WHEEL_PAN_RATIO;
  applyVisualizerTimeViewport(visualizer, panTimeViewport(viewport, delta));
  return true;
}

function wheelZoomFactor(deltaY: number): number {
  const delta = Math.max(-WHEEL_ZOOM_MAX_ABS_DELTA, Math.min(WHEEL_ZOOM_MAX_ABS_DELTA, Number(deltaY) || 0));
  return Math.exp(-delta * WHEEL_ZOOM_SENSITIVITY);
}

export function handleVisualizerZoomKeyDown(event: KeyboardEvent, visualizer: VisualizerElement): boolean {
  if (event.defaultPrevented || visualizer.dataset.hasTrack !== "true") return false;
  const viewport = readVisualizerTimeViewport(visualizer);
  if (event.key === "+" || event.key === "=") {
    event.preventDefault();
    zoomInForVisualizer(visualizer);
    return true;
  }
  if (event.key === "-" || event.key === "_") {
    event.preventDefault();
    zoomOutForVisualizer(visualizer);
    return true;
  }
  if (event.key === "0") {
    event.preventDefault();
    fitTimeViewportForVisualizer(visualizer);
    return true;
  }
  if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && !isFullTimeViewport(viewport)) {
    event.preventDefault();
    const direction = event.key === "ArrowLeft" ? -1 : 1;
    const delta = direction * timeViewportSpan(viewport) * KEYBOARD_PAN_RATIO;
    applyVisualizerTimeViewport(visualizer, panTimeViewport(viewport, delta));
    return true;
  }
  return false;
}
