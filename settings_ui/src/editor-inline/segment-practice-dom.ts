import {
  markerProjections,
  visibleRangeProjection,
} from "./graph-overlay-geometry.js";
import { PLOT, plotGeometryForSvg, plotWidth } from "./plot.js";
import { selectionForVisualizer } from "./selection-controller.js";
import {
  deriveActiveSuffix,
  emptySegmentPracticeState,
  segmentControlAvailability,
  type SegmentPracticeState,
} from "./segment-practice-state.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTimeViewport } from "./visualizer-state.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const SEGMENT_MARKER_ROW_HEIGHT = 18;

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
  const row = visualizer.querySelector<SVGGElement>(".aqe-segment-marker-row");
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!row || !svg) return;
  const state = segmentPracticeStateForVisualizer(visualizer);
  const shouldShow = !!state.baseRegion && (state.editing || state.practiceState !== "stopped");
  row.style.display = shouldShow ? "" : "none";
  row.setAttribute("aria-hidden", shouldShow ? "false" : "true");
  row.replaceChildren();
  if (!shouldShow || !state.baseRegion) return;
  const viewport = readVisualizerTimeViewport(visualizer);
  const plot = plotGeometryForSvg(svg);
  appendTrack(row, plot);
  appendBoundaryMarkers(row, state.baseRegion, viewport, plot);
  for (const marker of markerProjections(state.markersMs, viewport, plot)) {
    if (!marker.visible) continue;
    appendMarker(row, marker.x, plot);
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
  row: SVGGElement,
  baseRegion: { endMs: number; startMs: number },
  viewport: ReturnType<typeof readVisualizerTimeViewport>,
  plot: ReturnType<typeof plotGeometryForSvg>,
): void {
  const [start, end] = markerProjections([baseRegion.startMs, baseRegion.endMs], viewport, plot);
  if (start?.visible) appendMarker(row, start.x, plot, "aqe-segment-boundary-marker aqe-segment-boundary-marker-start");
  if (end?.visible) appendMarker(row, end.x, plot, "aqe-segment-boundary-marker aqe-segment-boundary-marker-end");
}

function appendTrack(row: SVGGElement, plot: ReturnType<typeof plotGeometryForSvg>): void {
  const track = document.createElementNS(SVG_NS, "rect");
  const y = plot.top - SEGMENT_MARKER_ROW_HEIGHT;
  track.classList.add("aqe-segment-marker-track");
  track.setAttribute("x", plot.left.toFixed(2));
  track.setAttribute("y", y.toFixed(2));
  track.setAttribute("width", plotWidth(plot).toFixed(2));
  track.setAttribute("height", String(SEGMENT_MARKER_ROW_HEIGHT));
  row.appendChild(track);
}

function appendMarker(
  row: SVGGElement,
  x: number,
  plot: ReturnType<typeof plotGeometryForSvg>,
  className = "aqe-segment-marker",
): void {
  const y = plot.top - SEGMENT_MARKER_ROW_HEIGHT;
  if (className.includes("aqe-segment-boundary-marker")) {
    const marker = document.createElementNS(SVG_NS, "rect");
    marker.setAttribute("x", (x - 3.5).toFixed(2));
    marker.setAttribute("y", y.toFixed(2));
    marker.setAttribute("width", "7");
    marker.setAttribute("height", String(SEGMENT_MARKER_ROW_HEIGHT));
    marker.setAttribute("rx", "3.5");
    marker.setAttribute("class", className);
    row.appendChild(marker);
    return;
  }
  const marker = document.createElementNS(SVG_NS, "line");
  marker.setAttribute("x1", x.toFixed(2));
  marker.setAttribute("x2", x.toFixed(2));
  marker.setAttribute("y1", y.toFixed(2));
  marker.setAttribute("y2", plot.top.toFixed(2));
  marker.setAttribute("class", className);
  row.appendChild(marker);
}
