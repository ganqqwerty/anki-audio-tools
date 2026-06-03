import {
  markerProjections,
  visibleRangeProjection,
} from "./graph-overlay-geometry.js";
import { PLOT, plotGeometryForSvg, plotWidth } from "./plot.js";
import {
  deriveActiveSuffix,
  emptyBackChainingState,
  backChainingControlAvailability,
  type BackChainingState,
} from "./back-chaining-state.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTimeViewport } from "./visualizer-state.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const BACK_CHAINING_MARKER_ROW_HEIGHT = 18;

export interface BackChainingControlsState {
  activeMarkerIndex: number | null;
  activeSuffixEndMs: number | null;
  activeSuffixStartMs: number | null;
  baseEndMs: number | null;
  baseStartMs: number | null;
  canNext: boolean;
  canPrevious: boolean;
  canPractice: boolean;
  markersMs: number[];
  practiceState: "paused" | "playing" | "stopped";
  visibleActiveRange: { endX: number; startX: number } | null;
  visibleMarkers: Array<{ ms: number; x: number }>;
}

export function backChainingStateForVisualizer(visualizer: VisualizerElement): BackChainingState {
  return visualizer.__aqeBackChainingState ?? emptyBackChainingState();
}

export function writeBackChainingState(visualizer: VisualizerElement, state: BackChainingState): void {
  visualizer.__aqeBackChainingState = state;
  visualizer.dataset.backChainingState = state.practiceState;
  visualizer.dataset.backChainingBaseStartMs = state.baseRegion ? String(Math.round(state.baseRegion.startMs)) : "";
  visualizer.dataset.backChainingBaseEndMs = state.baseRegion ? String(Math.round(state.baseRegion.endMs)) : "";
  visualizer.dataset.backChainingMarkersMs = state.markersMs.join(",");
  visualizer.dataset.backChainingActiveMarkerIndex = state.activeMarkerIndex === null ? "" : String(state.activeMarkerIndex);
  renderBackChainingMarkerRow(visualizer);
}

export function backChainingControlsForVisualizer(visualizer: VisualizerElement | null): BackChainingControlsState {
  if (!visualizer) return controlsSnapshot(emptyBackChainingState(), null);
  return controlsSnapshot(backChainingStateForVisualizer(visualizer), visualizer);
}

export function renderBackChainingMarkerRow(visualizer: VisualizerElement): void {
  const row = visualizer.querySelector<SVGGElement>(".aqe-back-chaining-marker-row");
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!row || !svg) return;
  const state = backChainingStateForVisualizer(visualizer);
  const shouldShow = !!state.baseRegion;
  row.style.display = shouldShow ? "" : "none";
  row.setAttribute("aria-hidden", shouldShow ? "false" : "true");
  row.replaceChildren();
  if (!shouldShow || !state.baseRegion) return;
  const viewport = readVisualizerTimeViewport(visualizer);
  const plot = plotGeometryForSvg(svg);
  appendTrack(row, plot);
  appendEndBoundaryMarker(row, state.baseRegion, viewport, plot);
  for (const marker of markerProjections(state.markersMs, viewport, plot)) {
    if (!marker.visible) continue;
    appendMarker(row, marker.x, plot);
  }
}

function controlsSnapshot(
  state: BackChainingState,
  visualizer: VisualizerElement | null,
): BackChainingControlsState {
  const availability = backChainingControlAvailability(state);
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
    canNext: availability.canNext,
    canPrevious: availability.canPrevious,
    canPractice: availability.canPractice,
    markersMs: state.markersMs,
    practiceState: state.practiceState,
    visibleActiveRange: visibleActiveRange
      ? { endX: visibleActiveRange.endX, startX: visibleActiveRange.startX }
      : null,
    visibleMarkers,
  };
}

function appendEndBoundaryMarker(
  row: SVGGElement,
  baseRegion: { endMs: number; startMs: number },
  viewport: ReturnType<typeof readVisualizerTimeViewport>,
  plot: ReturnType<typeof plotGeometryForSvg>,
): void {
  const [end] = markerProjections([baseRegion.endMs], viewport, plot);
  if (end?.visible) appendMarker(row, end.x, plot, "aqe-back-chaining-boundary-marker aqe-back-chaining-boundary-marker-end");
}

function appendTrack(row: SVGGElement, plot: ReturnType<typeof plotGeometryForSvg>): void {
  const track = document.createElementNS(SVG_NS, "rect");
  const y = plot.top - BACK_CHAINING_MARKER_ROW_HEIGHT;
  track.classList.add("aqe-back-chaining-marker-track");
  track.setAttribute("x", plot.left.toFixed(2));
  track.setAttribute("y", y.toFixed(2));
  track.setAttribute("width", plotWidth(plot).toFixed(2));
  track.setAttribute("height", String(BACK_CHAINING_MARKER_ROW_HEIGHT));
  row.appendChild(track);
}

function appendMarker(
  row: SVGGElement,
  x: number,
  plot: ReturnType<typeof plotGeometryForSvg>,
  className = "aqe-back-chaining-marker",
): void {
  const y = plot.top - BACK_CHAINING_MARKER_ROW_HEIGHT;
  if (className.includes("aqe-back-chaining-boundary-marker")) {
    const marker = document.createElementNS(SVG_NS, "rect");
    marker.setAttribute("x", (x - 3.5).toFixed(2));
    marker.setAttribute("y", y.toFixed(2));
    marker.setAttribute("width", "7");
    marker.setAttribute("height", String(BACK_CHAINING_MARKER_ROW_HEIGHT));
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
