import {
  PLOT,
  cursorMsFromEvent,
  type PlotGeometry,
  xForMs,
} from "./plot.js";
import {
  msVisibleInViewport,
  type TimeViewport,
} from "./time-viewport.js";

export interface TimeRange {
  endMs: number;
  startMs: number;
}

export interface MarkerClickProjection {
  insideVisibleBaseRegion: boolean;
  ms: number;
}

export interface MarkerProjection {
  ms: number;
  visible: boolean;
  x: number;
}

export interface VisibleRangeProjection {
  endMs: number;
  endX: number;
  startMs: number;
  startX: number;
}

export function markerClickFromEvent(
  event: Pick<PointerEvent, "clientX">,
  svg: SVGSVGElement,
  viewport: TimeViewport,
  baseRegion: TimeRange,
): MarkerClickProjection {
  const ms = Math.round(cursorMsFromEvent(event, svg, viewport.durationMs, viewport));
  const visibleBaseStart = Math.max(baseRegion.startMs, viewport.startMs);
  const visibleBaseEnd = Math.min(baseRegion.endMs, viewport.endMs);
  return {
    insideVisibleBaseRegion: ms >= visibleBaseStart && ms <= visibleBaseEnd,
    ms,
  };
}

export function markerProjections(
  markersMs: readonly number[],
  viewport: TimeViewport,
  plot: PlotGeometry = PLOT,
): MarkerProjection[] {
  return markersMs.map((ms) => ({
    ms,
    visible: msVisibleInViewport(ms, viewport),
    x: xForMs(ms, viewport.durationMs, viewport, plot),
  }));
}

export function visibleRangeProjection(
  range: TimeRange,
  viewport: TimeViewport,
  plot: PlotGeometry = PLOT,
): VisibleRangeProjection | null {
  const startMs = Math.max(range.startMs, viewport.startMs);
  const endMs = Math.min(range.endMs, viewport.endMs);
  if (endMs < startMs) return null;
  return {
    endMs,
    endX: xForMs(endMs, viewport.durationMs, viewport, plot),
    startMs,
    startX: xForMs(startMs, viewport.durationMs, viewport, plot),
  };
}
