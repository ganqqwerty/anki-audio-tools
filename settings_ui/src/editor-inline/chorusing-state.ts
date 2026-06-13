import type { PlaybackRegion } from "./playback-model.js";

export type ChorusingStatus = "paused" | "playing" | "stopped";
export type ChorusingMarkerDirection = "next" | "previous";

export interface ChorusingState {
  activeMarkerIndex: number | null;
  baseRegion: PlaybackRegion | null;
  markersMs: number[];
  ordinaryRepeatEnabled: boolean | null;
  practiceState: ChorusingStatus;
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
    activeMarkerIndex: null,
    baseRegion: null,
    markersMs: [],
    ordinaryRepeatEnabled: null,
    practiceState: "stopped",
    repeatPassesCompleted: 0,
    sourceFilename: "",
  };
}

export function defaultChorusingMarkers(baseRegion: PlaybackRegion | null): number[] {
  if (!baseRegion) return [];
  const lengthMs = Math.max(0, baseRegion.endMs - baseRegion.startMs);
  return normalizeChorusingMarkers([
    baseRegion.startMs,
    baseRegion.startMs + lengthMs / 3,
    baseRegion.startMs + (lengthMs * 2) / 3,
  ], baseRegion);
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
): PlaybackRegion | null {
  if (!baseRegion || activeMarkerIndex === null) return null;
  const marker = markersMs[activeMarkerIndex];
  if (typeof marker !== "number" || !Number.isFinite(marker)) return null;
  const startMs = Math.max(baseRegion.startMs, Math.min(Math.round(marker), baseRegion.endMs));
  if (startMs >= baseRegion.endMs) return null;
  return {
    endMs: baseRegion.endMs,
    mode: "selection",
    startMs,
  };
}

export function markerNavigationAvailability(
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
): ChorusingNavigationAvailability {
  if (!markersMs.length || activeMarkerIndex === null) {
    return {
      canNext: false,
      canPrevious: false,
    };
  }
  const active = normalizeActiveMarkerIndex(markersMs, activeMarkerIndex);
  return {
    canNext: active > 0,
    canPrevious: active < markersMs.length - 1,
  };
}

export function chorusingControlAvailability(state: ChorusingState): ChorusingControlAvailability {
  const hasBaseRegion = state.baseRegion !== null;
  const hasMarkers = state.markersMs.length > 0;
  const navigation = markerNavigationAvailability(state.markersMs, state.activeMarkerIndex);
  return {
    canNext: navigation.canNext,
    canPrevious: navigation.canPrevious,
    canPractice: hasBaseRegion && hasMarkers,
  };
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
