import type { PlaybackRegion } from "./playback-state.js";
import {
  PLOT,
  drawLabels,
  drawPitch,
  drawXAxis,
  formatTime,
  pathForIntensity,
  xForMs,
} from "./plot.js";
import type { NormalizedProsodyTrack, VisualizerElement } from "./types.js";

export function renderGraphRequested(visualizer: VisualizerElement): void {
  visualizer.hidden = false;
  visualizer.dataset.graphActive = "true";
  visualizer.dataset.graphBusy = "true";
  visualizer.dataset.hasTrack = "false";
  visualizer.dataset.durationMs = "0";
  visualizer.dataset.sourceFilename = "";
  visualizer.dataset.anchorMs = "0";
  visualizer.dataset.cursorMs = "0";
  visualizer.dataset.progressMs = "0";
  visualizer.dataset.resumeRequiresRestart = "false";
  visualizer.dataset.playbackEngine = "";
  visualizer.dataset.playbackStartMs = "0";
  visualizer.dataset.playbackEndMs = "0";
  visualizer.dataset.playbackRegionMode = "full";
  resetVisualizerPlot(visualizer);
}

export function renderVisualizerTrack(visualizer: VisualizerElement, track: NormalizedProsodyTrack): void {
  visualizer.hidden = false;
  visualizer.dataset.graphActive = "true";
  visualizer.dataset.graphBusy = "false";
  visualizer.dataset.hasTrack = "true";
  visualizer.dataset.durationMs = String(track.durationMs || 0);
  visualizer.dataset.analyzerName = track.analyzerName || "";
  visualizer.dataset.sourceFilename = track.sourceFilename || "";
  const intensity = visualizer.querySelector<SVGPathElement>(".aqe-intensity");
  if (intensity) intensity.setAttribute("d", pathForIntensity(track.points, track.durationMs));
  drawPitch(visualizer, track);
  drawLabels(visualizer, track);
  drawXAxis(visualizer, track.durationMs || 0);
}

export function renderVisualizerStatus(visualizer: VisualizerElement, message: string, kind = "info"): void {
  const status = visualizer.querySelector<HTMLElement>(".aqe-visualizer-status");
  const spinner = visualizer.querySelector<HTMLElement>(".aqe-spinner");
  const processing = kind === "processing";
  visualizer.dataset.graphBusy = processing ? "true" : "false";
  if (spinner) spinner.hidden = !processing;
  if (!status) return;
  status.textContent = message || "";
  status.dataset.kind = kind || "info";
}

export function renderSelection(
  visualizer: VisualizerElement,
  selection: PlaybackRegion | null,
  draftSelection: PlaybackRegion | null,
): void {
  const band = visualizer.querySelector<SVGRectElement>(".aqe-selection");
  const startEdge = visualizer.querySelector<SVGLineElement>(".aqe-selection-start");
  const endEdge = visualizer.querySelector<SVGLineElement>(".aqe-selection-end");
  const activeSelection = draftSelection ?? selection;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!band || !startEdge || !endEdge || !activeSelection || !durationMs) {
    band?.setAttribute("width", "0");
    band?.setAttribute("visibility", "hidden");
    band?.classList.remove("aqe-selection-draft");
    startEdge?.setAttribute("visibility", "hidden");
    endEdge?.setAttribute("visibility", "hidden");
    return;
  }
  const startX = xForMs(activeSelection.startMs, durationMs);
  const endX = xForMs(activeSelection.endMs, durationMs);
  band.setAttribute("visibility", "visible");
  band.classList.toggle("aqe-selection-draft", draftSelection !== null);
  band.setAttribute("x", startX.toFixed(2));
  band.setAttribute("y", String(PLOT.top));
  band.setAttribute("width", Math.max(0, endX - startX).toFixed(2));
  band.setAttribute("height", String(PLOT.height - PLOT.top - PLOT.bottom));
  startEdge.setAttribute("visibility", "visible");
  endEdge.setAttribute("visibility", "visible");
  for (const [edge, x] of [[startEdge, startX], [endEdge, endX]] as const) {
    edge.setAttribute("x1", x.toFixed(2));
    edge.setAttribute("x2", x.toFixed(2));
    edge.setAttribute("y1", String(PLOT.top));
    edge.setAttribute("y2", String(PLOT.height - PLOT.bottom));
  }
}

export function renderCursor(visualizer: VisualizerElement, ms: number, durationMs: number): void {
  const x = xForMs(ms, durationMs);
  const cursor = visualizer.querySelector<SVGLineElement>(".aqe-cursor");
  if (cursor) {
    cursor.setAttribute("x1", x.toFixed(2));
    cursor.setAttribute("x2", x.toFixed(2));
  }
  const label = visualizer.querySelector<HTMLElement>(".aqe-cursor-label");
  if (label) label.textContent = formatTime(ms, durationMs);
}

export function resetVisualizerPlot(visualizer: VisualizerElement): void {
  visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.setAttribute("d", "");
  clearText(visualizer, ".aqe-pitch");
  clearText(visualizer, ".aqe-labels");
  clearText(visualizer, ".aqe-x-axis");
}

export function resetCursorProjection(visualizer: VisualizerElement): void {
  const cursor = visualizer.querySelector<SVGLineElement>(".aqe-cursor");
  if (cursor) {
    cursor.setAttribute("x1", String(PLOT.left));
    cursor.setAttribute("x2", String(PLOT.left));
  }
  const label = visualizer.querySelector<HTMLElement>(".aqe-cursor-label");
  if (label) label.textContent = "0 ms";
}

export function graphLogContext(
  ord: number,
  track: NormalizedProsodyTrack,
): { analyzerName: string; durationMs: number; ord: number; points: number; sourceFilename: string } {
  return {
    analyzerName: track.analyzerName,
    durationMs: track.durationMs,
    ord,
    points: track.points.length,
    sourceFilename: track.sourceFilename,
  };
}

function clearText(root: VisualizerElement, selector: string): void {
  const node = root.querySelector<HTMLElement | SVGElement>(selector);
  if (node) node.textContent = "";
}
