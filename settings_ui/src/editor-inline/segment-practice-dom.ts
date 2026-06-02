import {
  markerProjections,
  visibleRangeProjection,
} from "./graph-overlay-geometry.js";
import { PLOT, graphPixelBounds, plotGeometryForSvg, svgViewBoxScale } from "./plot.js";
import { selectionForVisualizer } from "./selection-controller.js";
import {
  deriveActiveSuffix,
  emptySegmentPracticeState,
  segmentControlAvailability,
  type SegmentPracticeState,
} from "./segment-practice-state.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTimeViewport } from "./visualizer-state.js";

export interface SegmentPracticeControlsState {
  activeMarkerIndex: number | null;
  activeSuffixEndMs: number | null;
  activeSuffixStartMs: number | null;
  baseEndMs: number | null;
  baseStartMs: number | null;
  canClear: boolean;
  canEdit: boolean;
  canNext: boolean;
  canPractice: boolean;
  canPrevious: boolean;
  editing: boolean;
  markersMs: number[];
  panelOpen: boolean;
  practiceState: "paused" | "playing" | "stopped";
  visibleActiveRange: { endX: number; startX: number } | null;
  visibleMarkers: Array<{ ms: number; x: number }>;
}

export function segmentPracticeStateForVisualizer(visualizer: VisualizerElement): SegmentPracticeState {
  return visualizer.__aqeSegmentPracticeState ?? emptySegmentPracticeState();
}

export function writeSegmentPracticeState(visualizer: VisualizerElement, state: SegmentPracticeState): void {
  visualizer.__aqeSegmentPracticeState = state;
  visualizer.dataset.segmentEditing = state.editing ? "true" : "false";
  visualizer.dataset.segmentPracticeState = state.practiceState;
  visualizer.dataset.segmentBaseStartMs = state.baseRegion ? String(Math.round(state.baseRegion.startMs)) : "";
  visualizer.dataset.segmentBaseEndMs = state.baseRegion ? String(Math.round(state.baseRegion.endMs)) : "";
  visualizer.dataset.segmentMarkersMs = state.markersMs.join(",");
  visualizer.dataset.segmentActiveMarkerIndex = state.activeMarkerIndex === null ? "" : String(state.activeMarkerIndex);
  renderSegmentMarkerRow(visualizer);
}

export function segmentPracticeControlsForVisualizer(visualizer: VisualizerElement | null): SegmentPracticeControlsState {
  if (!visualizer) return controlsSnapshot(emptySegmentPracticeState(), null);
  return controlsSnapshot(segmentPracticeStateForVisualizer(visualizer), visualizer);
}

export function renderSegmentMarkerRow(visualizer: VisualizerElement): void {
  const row = visualizer.querySelector<HTMLElement>(".aqe-segment-marker-row");
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!row || !svg) return;
  const state = segmentPracticeStateForVisualizer(visualizer);
  const shouldShow = !!state.baseRegion && (state.editing || state.practiceState !== "stopped");
  row.hidden = !shouldShow;
  row.textContent = "";
  if (!shouldShow || !state.baseRegion) return;
  positionMarkerRow(row, svg);
  const viewport = readVisualizerTimeViewport(visualizer);
  const plot = plotGeometryForSvg(svg);
  const scale = svgViewBoxScale(svg);
  const base = visibleRangeProjection(state.baseRegion, viewport, plot);
  if (base) appendRange(row, "aqe-segment-base-range", (base.startX - plot.left) * scale.x, (base.endX - base.startX) * scale.x);
  appendBoundaryMarkers(row, state.baseRegion, viewport, plot, scale.x);
  const activeSuffix = deriveActiveSuffix(state.baseRegion, state.markersMs, state.activeMarkerIndex);
  const active = activeSuffix ? visibleRangeProjection(activeSuffix, viewport, plot) : null;
  if (active) {
    appendRange(row, "aqe-segment-active-range", (active.startX - plot.left) * scale.x, (active.endX - active.startX) * scale.x);
  }
  for (const marker of markerProjections(state.markersMs, viewport, plot)) {
    if (!marker.visible) continue;
    appendMarker(row, (marker.x - plot.left) * scale.x);
  }
}

function controlsSnapshot(
  state: SegmentPracticeState,
  visualizer: VisualizerElement | null,
): SegmentPracticeControlsState {
  const availability = segmentControlAvailability(state);
  const currentSelection = visualizer ? selectionForVisualizer(visualizer) : null;
  const suffix = deriveActiveSuffix(state.baseRegion, state.markersMs, state.activeMarkerIndex);
  const viewport = visualizer ? readVisualizerTimeViewport(visualizer) : null;
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  const plot = svg ? plotGeometryForSvg(svg) : PLOT;
  const visibleMarkers = viewport
    ? markerProjections(state.markersMs, viewport, plot)
      .filter((marker) => marker.visible)
      .map(({ ms, x }) => ({ ms, x }))
    : [];
  const visibleActiveRange = suffix && viewport
    ? visibleRangeProjection(suffix, viewport, plot)
    : null;
  return {
    activeMarkerIndex: state.activeMarkerIndex,
    activeSuffixEndMs: suffix?.endMs ?? null,
    activeSuffixStartMs: suffix?.startMs ?? null,
    baseEndMs: state.baseRegion?.endMs ?? null,
    baseStartMs: state.baseRegion?.startMs ?? null,
    canClear: availability.canClear,
    canEdit: availability.canEdit || currentSelection !== null,
    canNext: availability.canNext,
    canPractice: availability.canPractice,
    canPrevious: availability.canPrevious,
    editing: state.editing,
    markersMs: state.markersMs,
    panelOpen: visualizer?.dataset.segmentPanelOpen === "true",
    practiceState: state.practiceState,
    visibleActiveRange: visibleActiveRange
      ? { endX: visibleActiveRange.endX, startX: visibleActiveRange.startX }
      : null,
    visibleMarkers,
  };
}

function appendBoundaryMarkers(
  row: HTMLElement,
  baseRegion: { endMs: number; startMs: number },
  viewport: ReturnType<typeof readVisualizerTimeViewport>,
  plot: ReturnType<typeof plotGeometryForSvg>,
  scaleX: number,
): void {
  const [start, end] = markerProjections([baseRegion.startMs, baseRegion.endMs], viewport, plot);
  if (start?.visible) appendMarker(row, (start.x - plot.left) * scaleX, "aqe-segment-boundary-marker aqe-segment-boundary-marker-start");
  if (end?.visible) appendMarker(row, (end.x - plot.left) * scaleX, "aqe-segment-boundary-marker aqe-segment-boundary-marker-end");
}

function positionMarkerRow(row: HTMLElement, svg: SVGSVGElement): void {
  const bounds = graphPixelBounds(svg);
  const containerBounds = row.parentElement?.getBoundingClientRect();
  const left = containerBounds ? bounds.left - containerBounds.left : 0;
  row.style.left = `${left.toFixed(2)}px`;
  row.style.width = `${bounds.width.toFixed(2)}px`;
}

function appendRange(row: HTMLElement, className: string, leftPx: number, widthPx: number): void {
  const range = document.createElement("span");
  range.className = className;
  range.style.left = `${Math.max(0, leftPx).toFixed(2)}px`;
  range.style.width = `${Math.max(0, widthPx).toFixed(2)}px`;
  row.appendChild(range);
}

function appendMarker(row: HTMLElement, leftPx: number, className = "aqe-segment-marker"): void {
  const marker = document.createElement("span");
  marker.className = className;
  marker.style.left = `${leftPx.toFixed(2)}px`;
  row.appendChild(marker);
}
