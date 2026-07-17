import {
  markerProjections,
  visibleRangeProjection,
} from "./graph-overlay-geometry.js";
import { PLOT, plotGeometryForSvg, plotWidth } from "./plot.js";
import {
  emptyChorusingState,
  chorusingControlAvailability,
  markerIndexForExactStart,
  type ChorusingState,
} from "./chorusing-state";
import { readChorusingState, writeChorusingStateForOrd } from "./chorusing-state-store.js";
import { controlsForRawOrd } from "./dom-selectors.js";
import { selectionForVisualizer } from "./selection-controller.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTimeViewport } from "./visualizer-state.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const BACK_CHAINING_MARKER_ROW_HEIGHT = 18;

export interface ChorusingControlsState {
  activeMarkerIndex: number | null;
  activeSuffixEndMs: number | null;
  activeSuffixStartMs: number | null;
  baseEndMs: number | null;
  baseStartMs: number | null;
  canNext: boolean;
  canPrevious: boolean;
  canPractice: boolean;
  markersMs: number[];
  practiceState: "stopped";
  visibleActiveRange: { endX: number; startX: number } | null;
  visibleMarkers: Array<{ ms: number; x: number }>;
}

export function chorusingStateForVisualizer(visualizer: VisualizerElement): ChorusingState {
  return readChorusingState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function writeChorusingState(visualizer: VisualizerElement, state: ChorusingState): void {
  writeChorusingStateForOrd(Number(visualizer.dataset.aqeFieldOrd || "0"), state);
  visualizer.dataset.chorusingState = "stopped";
  visualizer.dataset.chorusingBaseStartMs = state.baseRegion ? String(Math.round(state.baseRegion.startMs)) : "";
  visualizer.dataset.chorusingBaseEndMs = state.baseRegion ? String(Math.round(state.baseRegion.endMs)) : "";
  visualizer.dataset.chorusingMarkersMs = state.markersMs.join(",");
  const selection = activeMarkerSelection(state, selectionForVisualizer(visualizer));
  const activeMarkerIndex = selection ? markerIndexForExactStart(state.markersMs, selection.startMs) : null;
  visualizer.dataset.chorusingActiveMarkerIndex = activeMarkerIndex === null ? "" : String(activeMarkerIndex);
  renderChorusingMarkerRow(visualizer);
}

export function chorusingControlsForVisualizer(visualizer: VisualizerElement | null): ChorusingControlsState {
  if (!visualizer) return controlsSnapshot(emptyChorusingState(), null);
  return controlsSnapshot(chorusingStateForVisualizer(visualizer), visualizer);
}

export function chorusingMarkerControlsVisible(visualizer: VisualizerElement): boolean {
  if (visualizer.dataset.selectionMarkerShiftButtonsEnabled === "true") return true;
  const rawOrd = visualizer.dataset.aqeFieldOrd;
  return !!rawOrd && !!controlsForRawOrd(rawOrd)?.querySelector(".aqe-chorusing-toolbar-panel");
}

export function renderChorusingMarkerRow(visualizer: VisualizerElement): void {
  const row = visualizer.querySelector<SVGGElement>(".aqe-chorusing-marker-row");
  const hitbox = visualizer.querySelector<HTMLElement>(".aqe-chorusing-marker-hitbox");
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!row || !svg) return;
  const state = chorusingStateForVisualizer(visualizer);
  const shouldShow = !!state.baseRegion && chorusingMarkerControlsVisible(visualizer);
  row.style.display = shouldShow ? "" : "none";
  row.setAttribute("aria-hidden", shouldShow ? "false" : "true");
  if (hitbox) hitbox.hidden = !shouldShow;
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
  state: ChorusingState,
  visualizer: VisualizerElement | null,
): ChorusingControlsState {
  const selection = activeMarkerSelection(state, selectionForVisualizer(visualizer));
  const availability = chorusingControlAvailability(state, selection);
  const viewport = visualizer ? readVisualizerTimeViewport(visualizer) : null;
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  const plot = svg ? plotGeometryForSvg(svg) : PLOT;
  const visibleMarkers = viewport
    ? markerProjections(state.markersMs, viewport, plot)
      .filter((marker) => marker.visible)
      .map(({ ms, x }) => ({ ms, x }))
    : [];
  const visibleActiveRange = selection && viewport
    ? visibleRangeProjection(selection, viewport, plot)
    : null;
  return {
    activeMarkerIndex: selection ? markerIndexForExactStart(state.markersMs, selection.startMs) : null,
    activeSuffixEndMs: selection?.endMs ?? null,
    activeSuffixStartMs: selection?.startMs ?? null,
    baseEndMs: state.baseRegion?.endMs ?? null,
    baseStartMs: state.baseRegion?.startMs ?? null,
    canNext: availability.canNext,
    canPrevious: availability.canPrevious,
    canPractice: availability.canPractice,
    markersMs: state.markersMs,
    practiceState: "stopped",
    visibleActiveRange: visibleActiveRange
      ? { endX: visibleActiveRange.endX, startX: visibleActiveRange.startX }
      : null,
    visibleMarkers,
  };
}

function activeMarkerSelection(
  state: ChorusingState,
  selection: ReturnType<typeof selectionForVisualizer>,
): ReturnType<typeof selectionForVisualizer> {
  if (!selection || !state.baseRegion) return selection;
  const coversBase = Math.round(selection.startMs) <= Math.round(state.baseRegion.startMs)
    && Math.round(selection.endMs) >= Math.round(state.baseRegion.endMs);
  return coversBase && !state.fullBaseSelectionActive ? null : selection;
}

function appendEndBoundaryMarker(
  row: SVGGElement,
  baseRegion: { endMs: number; startMs: number },
  viewport: ReturnType<typeof readVisualizerTimeViewport>,
  plot: ReturnType<typeof plotGeometryForSvg>,
): void {
  const [end] = markerProjections([baseRegion.endMs], viewport, plot);
  if (end?.visible) appendMarker(row, end.x, plot, "aqe-chorusing-boundary-marker aqe-chorusing-boundary-marker-end");
}

function appendTrack(row: SVGGElement, plot: ReturnType<typeof plotGeometryForSvg>): void {
  const track = document.createElementNS(SVG_NS, "rect");
  const y = plot.top - BACK_CHAINING_MARKER_ROW_HEIGHT;
  track.classList.add("aqe-chorusing-marker-track");
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
  className = "aqe-chorusing-marker",
): void {
  const y = plot.top - BACK_CHAINING_MARKER_ROW_HEIGHT;
  if (className.includes("aqe-chorusing-boundary-marker")) {
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
