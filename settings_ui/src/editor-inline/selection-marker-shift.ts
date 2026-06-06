import { MIN_SELECTION_DURATION_MS, clampMs, type SelectionRange } from "./selection-state.js";

export type SelectionShiftDirection = "next" | "previous";
export type SelectionShiftEdge = "end" | "start";
export type SelectionShiftDisabledReason =
  | "crosses_other_edge"
  | "no_next"
  | "no_previous"
  | "too_short";

export interface SelectionMarkerShiftResolution {
  direction: SelectionShiftDirection;
  disabledReason: SelectionShiftDisabledReason | null;
  edge: SelectionShiftEdge;
  nextRange: SelectionRange | null;
  targetMarkerMs: number | null;
}

export function normalizeSelectionShiftMarkers(
  markersMs: readonly number[],
  durationMs: number,
): number[] {
  const duration = Math.max(0, Number(durationMs) || 0);
  return Array.from(
    new Set(
      markersMs
        .map((markerMs) => Math.round(clampMs(markerMs, duration)))
        .filter((markerMs) => Number.isFinite(markerMs)),
    ),
  ).sort((left, right) => left - right);
}

export function resolveSelectionMarkerShift(
  selection: SelectionRange,
  edge: SelectionShiftEdge,
  direction: SelectionShiftDirection,
  markersMs: readonly number[],
  durationMs: number,
  minDurationMs = MIN_SELECTION_DURATION_MS,
): SelectionMarkerShiftResolution {
  const normalized = normalizeSelectionShiftMarkers(markersMs, durationMs);
  const startMs = Math.round(clampMs(selection.startMs, durationMs));
  const endMs = Math.round(clampMs(selection.endMs, durationMs));
  const edgeMs = edge === "start" ? startMs : endMs;
  const targetMarkerMs = direction === "previous"
    ? findPreviousMarker(normalized, edgeMs)
    : findNextMarker(normalized, edgeMs);

  if (targetMarkerMs === null) {
    return {
      direction,
      disabledReason: direction === "previous" ? "no_previous" : "no_next",
      edge,
      nextRange: null,
      targetMarkerMs: null,
    };
  }

  if (edge === "start") {
    if (targetMarkerMs >= endMs) {
      return blocked(direction, edge, targetMarkerMs, "crosses_other_edge");
    }
    if (endMs - targetMarkerMs < Math.max(0, Number(minDurationMs) || 0)) {
      return blocked(direction, edge, targetMarkerMs, "too_short");
    }
    return {
      direction,
      disabledReason: null,
      edge,
      nextRange: { startMs: targetMarkerMs, endMs },
      targetMarkerMs,
    };
  }

  if (targetMarkerMs <= startMs) {
    return blocked(direction, edge, targetMarkerMs, "crosses_other_edge");
  }
  if (targetMarkerMs - startMs < Math.max(0, Number(minDurationMs) || 0)) {
    return blocked(direction, edge, targetMarkerMs, "too_short");
  }
  return {
    direction,
    disabledReason: null,
    edge,
    nextRange: { startMs, endMs: targetMarkerMs },
    targetMarkerMs,
  };
}

function blocked(
  direction: SelectionShiftDirection,
  edge: SelectionShiftEdge,
  targetMarkerMs: number,
  disabledReason: SelectionShiftDisabledReason,
): SelectionMarkerShiftResolution {
  return {
    direction,
    disabledReason,
    edge,
    nextRange: null,
    targetMarkerMs,
  };
}

function findPreviousMarker(markersMs: readonly number[], edgeMs: number): number | null {
  for (let index = markersMs.length - 1; index >= 0; index -= 1) {
    if (markersMs[index] < edgeMs) return markersMs[index];
  }
  return null;
}

function findNextMarker(markersMs: readonly number[], edgeMs: number): number | null {
  for (const markerMs of markersMs) {
    if (markerMs > edgeMs) return markerMs;
  }
  return null;
}
