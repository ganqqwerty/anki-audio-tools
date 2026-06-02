export interface TimeViewport {
  durationMs: number;
  endMs: number;
  startMs: number;
}

export const MIN_TIME_VIEWPORT_MS = 250;
export const TIME_VIEWPORT_ZOOM_FACTOR = 1.25;
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
