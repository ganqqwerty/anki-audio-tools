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
