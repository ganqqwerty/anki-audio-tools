import type { PlaybackRegion } from "./playback-model.js";

export type ChorusingMarkerDirection = "next" | "previous";

export const DEFAULT_CHORUSING_MARKER_INTERVAL_MS = 500;
export const CHORUSING_MARKER_INTERVAL_MIN_MS = 50;
export const CHORUSING_MARKER_INTERVAL_MAX_MS = 10000;

export interface ChorusingState {
  baseRegion: PlaybackRegion | null;
  fullBaseSelectionActive: boolean;
  markersMs: number[];
  repeatPassesCompleted: number;
  sourceFilename: string;
}

export interface ChorusingControlAvailability {
  canNext: boolean;
  canPrevious: boolean;
  canPractice: boolean;
}

export interface ChorusingNavigationAvailability {
  canNext: boolean;
  canPrevious: boolean;
}

export interface ToggleChorusingMarkerResult {
  markersMs: number[];
  removed: boolean;
}

export function emptyChorusingState(): ChorusingState {
  return {
    baseRegion: null,
    fullBaseSelectionActive: false,
    markersMs: [],
    repeatPassesCompleted: 0,
    sourceFilename: "",
  };
}

export function clampChorusingMarkerIntervalMs(value: unknown): number {
  if (typeof value === "boolean" || typeof value !== "number" || !Number.isFinite(value)) {
    return DEFAULT_CHORUSING_MARKER_INTERVAL_MS;
  }
  return Math.max(
    CHORUSING_MARKER_INTERVAL_MIN_MS,
    Math.min(CHORUSING_MARKER_INTERVAL_MAX_MS, Math.round(value)),
  );
}

export function defaultChorusingMarkers(
  baseRegion: PlaybackRegion | null,
  markerIntervalMs = DEFAULT_CHORUSING_MARKER_INTERVAL_MS,
): number[] {
  if (!baseRegion) return [];
  const intervalMs = clampChorusingMarkerIntervalMs(markerIntervalMs);
  const markers: number[] = [];
  for (let markerMs = baseRegion.startMs; markerMs < baseRegion.endMs; markerMs += intervalMs) {
    markers.push(markerMs);
  }
  return normalizeChorusingMarkers(markers, baseRegion);
}

export function normalizeChorusingMarkers(markersMs: readonly number[], baseRegion: PlaybackRegion | null): number[] {
  if (!baseRegion) return [];
  return Array.from(
    new Set(
      markersMs
        .map((marker) => clampMarkerMs(marker, baseRegion))
        .filter((marker) => marker >= baseRegion.startMs && marker <= baseRegion.endMs)
        .map((marker) => Math.round(marker)),
    ),
  ).sort((left, right) => left - right);
}

export function toggleChorusingMarker(
  markersMs: readonly number[],
  rawMarkerMs: number,
  baseRegion: PlaybackRegion,
  hitToleranceMs: number,
): ToggleChorusingMarkerResult {
  const normalized = normalizeChorusingMarkers(markersMs, baseRegion);
  const markerMs = clampMarkerMs(rawMarkerMs, baseRegion);
  const existingIndex = normalized.findIndex((marker) => Math.abs(marker - markerMs) <= hitToleranceMs);
  if (existingIndex >= 0) {
    return {
      markersMs: normalized.filter((_, index) => index !== existingIndex),
      removed: true,
    };
  }
  return {
    markersMs: normalizeChorusingMarkers([...normalized, markerMs], baseRegion),
    removed: false,
  };
}

export function chooseInitialActiveMarkerIndex(markersMs: readonly number[]): number | null {
  return markersMs.length ? markersMs.length - 1 : null;
}

export function activeMarkerIndexAfterMarkerToggle(
  previousMarkersMs: readonly number[],
  nextMarkersMs: readonly number[],
  activeMarkerIndex: number | null,
): number | null {
  if (!nextMarkersMs.length) return null;
  const active = normalizeActiveMarkerIndex(previousMarkersMs, activeMarkerIndex);
  const activeMarker = previousMarkersMs[active];
  if (typeof activeMarker !== "number" || !Number.isFinite(activeMarker)) {
    return chooseInitialActiveMarkerIndex(nextMarkersMs);
  }
  const exactIndex = nextMarkersMs.findIndex((marker) => marker === activeMarker);
  if (exactIndex >= 0) return exactIndex;
  const insertionPoint = nextMarkersMs.findIndex((marker) => marker > activeMarker);
  if (insertionPoint < 0) return nextMarkersMs.length - 1;
  return insertionPoint;
}

export function moveActiveMarkerIndex(
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
  direction: ChorusingMarkerDirection,
): number | null {
  if (!markersMs.length) return null;
  const active = normalizeActiveMarkerIndex(markersMs, activeMarkerIndex);
  if (direction === "next") return Math.max(0, active - 1);
  return Math.min(markersMs.length - 1, active + 1);
}

export function deriveActiveSuffix(
  baseRegion: PlaybackRegion | null,
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
  activeStartMs: number | null = null,
  activeEndMs: number | null = null,
): PlaybackRegion | null {
  if (!baseRegion) return null;
  const endMs = activeChorusingEndMs(baseRegion, activeEndMs);
  if (endMs === null) return null;
  const startMs = activeChorusingStartMs(
    baseRegion,
    markersMs,
    activeMarkerIndex,
    activeStartMs,
    endMs,
  );
  if (startMs === null || startMs >= endMs) return null;
  return {
    endMs,
    mode: "selection",
    startMs,
  };
}

export function markerIndexForExactStart(markersMs: readonly number[], startMs: number): number | null {
  const rounded = Math.round(startMs);
  const index = markersMs.findIndex((marker) => Math.round(marker) === rounded);
  return index >= 0 ? index : null;
}

export function markerNavigationAvailability(
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
  activeStartMs: number | null = null,
  activeEndMs: number | null = null,
): ChorusingNavigationAvailability {
  if (!markersMs.length) {
    return {
      canNext: false,
      canPrevious: false,
    };
  }
  const currentStart = currentChorusingStartForNavigation(markersMs, activeMarkerIndex, activeStartMs);
  if (currentStart === null) {
    return {
      canNext: false,
      canPrevious: false,
    };
  }
  return {
    canNext: markerIndexInDirection(markersMs, currentStart, activeEndMs, "next") !== null,
    canPrevious: markerIndexInDirection(markersMs, currentStart, activeEndMs, "previous") !== null,
  };
}

export function chorusingControlAvailability(
  state: ChorusingState,
  selection: PlaybackRegion | null = null,
): ChorusingControlAvailability {
  const hasBaseRegion = state.baseRegion !== null;
  const hasMarkers = state.markersMs.length > 0;
  const navigation = markerNavigationAvailability(
    state.markersMs,
    markerIndexForExactStart(state.markersMs, selection?.startMs ?? Number.NaN),
    selection?.startMs ?? null,
    selection?.endMs ?? null,
  );
  return {
    canNext: navigation.canNext,
    canPrevious: navigation.canPrevious,
    canPractice: hasBaseRegion && hasMarkers,
  };
}

export function moveActiveMarkerIndexForSuffix(
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
  direction: ChorusingMarkerDirection,
  activeStartMs: number | null = null,
  activeEndMs: number | null = null,
): number | null {
  const currentStart = currentChorusingStartForNavigation(markersMs, activeMarkerIndex, activeStartMs);
  if (currentStart === null) return moveActiveMarkerIndex(markersMs, activeMarkerIndex, direction);
  return markerIndexInDirection(markersMs, currentStart, activeEndMs, direction);
}

function normalizeActiveMarkerIndex(markersMs: readonly number[], activeMarkerIndex: number | null): number {
  if (!markersMs.length) return 0;
  if (activeMarkerIndex === null || !Number.isFinite(activeMarkerIndex)) return markersMs.length - 1;
  return Math.max(0, Math.min(Math.trunc(activeMarkerIndex), markersMs.length - 1));
}

function clampMarkerMs(markerMs: number, baseRegion: PlaybackRegion): number {
  const finite = Number.isFinite(markerMs) ? markerMs : baseRegion.startMs;
  return Math.max(baseRegion.startMs, Math.min(finite, baseRegion.endMs));
}

function activeChorusingEndMs(baseRegion: PlaybackRegion, activeEndMs: number | null): number | null {
  const rawEnd = activeEndMs ?? baseRegion.endMs;
  if (!Number.isFinite(rawEnd)) return null;
  return Math.max(baseRegion.startMs, Math.min(Math.round(rawEnd), baseRegion.endMs));
}

function activeChorusingStartMs(
  baseRegion: PlaybackRegion,
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
  activeStartMs: number | null,
  endMs: number,
): number | null {
  if (activeStartMs !== null && Number.isFinite(activeStartMs)) {
    return Math.max(baseRegion.startMs, Math.min(Math.round(activeStartMs), endMs));
  }
  if (activeMarkerIndex === null) return null;
  const marker = markersMs[activeMarkerIndex];
  if (typeof marker !== "number" || !Number.isFinite(marker)) return null;
  return Math.max(baseRegion.startMs, Math.min(Math.round(marker), endMs));
}

function currentChorusingStartForNavigation(
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
  activeStartMs: number | null,
): number | null {
  if (activeStartMs !== null && Number.isFinite(activeStartMs)) return Math.round(activeStartMs);
  if (!markersMs.length || activeMarkerIndex === null) return null;
  const active = normalizeActiveMarkerIndex(markersMs, activeMarkerIndex);
  const marker = markersMs[active];
  return typeof marker === "number" && Number.isFinite(marker) ? Math.round(marker) : null;
}

function markerIndexInDirection(
  markersMs: readonly number[],
  currentStartMs: number,
  activeEndMs: number | null,
  direction: ChorusingMarkerDirection,
): number | null {
  const roundedStart = Math.round(currentStartMs);
  const roundedEnd = activeEndMs !== null && Number.isFinite(activeEndMs)
    ? Math.round(activeEndMs)
    : null;
  if (direction === "next") {
    for (let index = markersMs.length - 1; index >= 0; index -= 1) {
      const marker = markersMs[index];
      if (typeof marker === "number" && Math.round(marker) < roundedStart) return index;
    }
    return null;
  }
  for (let index = 0; index < markersMs.length; index += 1) {
    const rawMarker = markersMs[index];
    if (typeof rawMarker !== "number") continue;
    const marker = Math.round(rawMarker);
    if (marker > roundedStart && (roundedEnd === null || marker < roundedEnd)) return index;
  }
  return null;
}
