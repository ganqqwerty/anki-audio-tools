import type { PlaybackRegion } from "./playback-model.js";

export type BackChainingStatus = "paused" | "playing" | "stopped";
export type BackChainingMarkerDirection = "next" | "previous";

export interface BackChainingState {
  activeMarkerIndex: number | null;
  baseRegion: PlaybackRegion | null;
  editing: boolean;
  markersMs: number[];
  ordinaryRepeatEnabled: boolean | null;
  practiceState: BackChainingStatus;
  sourceFilename: string;
}

export interface BackChainingControlAvailability {
  canClear: boolean;
  canEdit: boolean;
  canNext: boolean;
  canPractice: boolean;
  canPrevious: boolean;
}

export interface BackChainingNavigationAvailability {
  canNext: boolean;
  canPrevious: boolean;
}

export interface ToggleBackChainingMarkerResult {
  markersMs: number[];
  removed: boolean;
}

export function emptyBackChainingState(): BackChainingState {
  return {
    activeMarkerIndex: null,
    baseRegion: null,
    editing: false,
    markersMs: [],
    ordinaryRepeatEnabled: null,
    practiceState: "stopped",
    sourceFilename: "",
  };
}

export function defaultBackChainingMarkers(baseRegion: PlaybackRegion | null): number[] {
  if (!baseRegion) return [];
  const lengthMs = Math.max(0, baseRegion.endMs - baseRegion.startMs);
  return normalizeBackChainingMarkers([
    baseRegion.startMs,
    baseRegion.startMs + lengthMs / 3,
    baseRegion.startMs + (lengthMs * 2) / 3,
  ], baseRegion);
}

export function normalizeBackChainingMarkers(markersMs: readonly number[], baseRegion: PlaybackRegion | null): number[] {
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

export function toggleBackChainingMarker(
  markersMs: readonly number[],
  rawMarkerMs: number,
  baseRegion: PlaybackRegion,
  hitToleranceMs: number,
): ToggleBackChainingMarkerResult {
  const normalized = normalizeBackChainingMarkers(markersMs, baseRegion);
  const markerMs = clampMarkerMs(rawMarkerMs, baseRegion);
  const existingIndex = normalized.findIndex((marker) => Math.abs(marker - markerMs) <= hitToleranceMs);
  if (existingIndex >= 0) {
    return {
      markersMs: normalized.filter((_, index) => index !== existingIndex),
      removed: true,
    };
  }
  return {
    markersMs: normalizeBackChainingMarkers([...normalized, markerMs], baseRegion),
    removed: false,
  };
}

export function chooseInitialActiveMarkerIndex(markersMs: readonly number[]): number | null {
  return markersMs.length ? markersMs.length - 1 : null;
}

export function moveActiveMarkerIndex(
  markersMs: readonly number[],
  activeMarkerIndex: number | null,
  direction: BackChainingMarkerDirection,
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
): BackChainingNavigationAvailability {
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

export function backChainingControlAvailability(state: BackChainingState): BackChainingControlAvailability {
  const hasBaseRegion = state.baseRegion !== null;
  const hasMarkers = state.markersMs.length > 0;
  const navigation = markerNavigationAvailability(state.markersMs, state.activeMarkerIndex);
  return {
    canClear: hasMarkers || state.editing || state.practiceState !== "stopped",
    canEdit: hasBaseRegion,
    canNext: navigation.canNext,
    canPractice: hasBaseRegion && hasMarkers,
    canPrevious: navigation.canPrevious,
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
