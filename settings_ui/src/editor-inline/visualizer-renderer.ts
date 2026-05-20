import type { PlaybackRegion } from "./playback-state.js";
import {
  PLOT,
  drawLabels,
  drawPitch,
  drawXAxis,
  formatPitchHz,
  formatTime,
  pathForIntensity,
  pitchHzAtMs,
  xForMs,
} from "./plot.js";
import type { NormalizedProsodyTrack, VisualizerElement } from "./types.js";

const CURSOR_FLAG_WIDTH = 82;
const CURSOR_FLAG_HALF_WIDTH = CURSOR_FLAG_WIDTH / 2;
const CURSOR_FLAG_Y = PLOT.top + 4;
const CURSOR_FLAG_NOTCH_MAX_OFFSET = CURSOR_FLAG_HALF_WIDTH - 5;

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
  delete visualizer.__aqeTrack;
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
  visualizer.__aqeTrack = track;
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
  const startHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-start");
  const endHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-end");
  const startGrip = visualizer.querySelector<SVGGElement>(".aqe-selection-resize-grip-start");
  const endGrip = visualizer.querySelector<SVGGElement>(".aqe-selection-resize-grip-end");
  const activeSelection = draftSelection ?? selection;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!band || !startEdge || !endEdge || !activeSelection || !durationMs) {
    band?.setAttribute("width", "0");
    band?.setAttribute("visibility", "hidden");
    band?.classList.remove("aqe-selection-draft");
    startEdge?.setAttribute("visibility", "hidden");
    endEdge?.setAttribute("visibility", "hidden");
    startHandle?.setAttribute("visibility", "hidden");
    endHandle?.setAttribute("visibility", "hidden");
    startGrip?.setAttribute("visibility", "hidden");
    endGrip?.setAttribute("visibility", "hidden");
    return;
  }
  const startX = xForMs(activeSelection.startMs, durationMs);
  const endX = xForMs(activeSelection.endMs, durationMs);
  const plotTop = PLOT.top;
  const plotBottom = PLOT.height - PLOT.bottom;
  const plotHeight = plotBottom - plotTop;
  const handleHeight = plotHeight * 0.8;
  const handleY = plotTop + (plotHeight - handleHeight) / 2;
  const handleCenterY = handleY + handleHeight / 2;
  band.setAttribute("visibility", "visible");
  band.classList.toggle("aqe-selection-draft", draftSelection !== null);
  band.setAttribute("x", startX.toFixed(2));
  band.setAttribute("y", String(plotTop));
  band.setAttribute("width", Math.max(0, endX - startX).toFixed(2));
  band.setAttribute("height", String(plotHeight));
  startEdge.setAttribute("visibility", "visible");
  endEdge.setAttribute("visibility", "visible");
  for (const [edge, x] of [[startEdge, startX], [endEdge, endX]] as const) {
    edge.setAttribute("x1", x.toFixed(2));
    edge.setAttribute("x2", x.toFixed(2));
    edge.setAttribute("y1", String(plotTop));
    edge.setAttribute("y2", String(plotBottom));
  }
  const showHandles = selection !== null && draftSelection === null;
  for (const [handle, grip, x] of [[startHandle, startGrip, startX], [endHandle, endGrip, endX]] as const) {
    handle?.setAttribute("visibility", showHandles ? "visible" : "hidden");
    handle?.setAttribute("x", (x - 5).toFixed(2));
    handle?.setAttribute("y", handleY.toFixed(2));
    handle?.setAttribute("width", "10");
    handle?.setAttribute("height", handleHeight.toFixed(2));
    grip?.setAttribute("visibility", showHandles ? "visible" : "hidden");
    grip?.setAttribute("transform", `translate(${x.toFixed(2)} ${handleCenterY.toFixed(2)})`);
  }
}

export function renderCursor(visualizer: VisualizerElement, ms: number, durationMs: number): void {
  const x = xForMs(ms, durationMs);
  const cursor = visualizer.querySelector<SVGLineElement>(".aqe-cursor");
  if (cursor) {
    cursor.setAttribute("x1", x.toFixed(2));
    cursor.setAttribute("x2", x.toFixed(2));
  }
  const currentText = formatTime(ms, durationMs);
  const pitchText = formatPitchHz(visualizer.__aqeTrack ? pitchHzAtMs(visualizer.__aqeTrack.points, ms) : null);
  const label = visualizer.querySelector<HTMLElement>(".aqe-cursor-label");
  if (label) label.textContent = `${currentText} / ${pitchText}`;
  const flag = visualizer.querySelector<SVGGElement>(".aqe-cursor-flag");
  if (!flag) return;
  if (durationMs <= 0) {
    flag.setAttribute("visibility", "hidden");
    return;
  }
  const flagX = clampedCursorFlagX(x);
  flag.setAttribute("visibility", "visible");
  flag.setAttribute("transform", `translate(${flagX.toFixed(2)} ${CURSOR_FLAG_Y})`);
  flag.querySelector<SVGTextElement>(".aqe-cursor-flag-current")!.textContent = currentText;
  flag.querySelector<SVGTextElement>(".aqe-cursor-flag-pitch")!.textContent = ` / ${pitchText}`;
  flag.querySelector<SVGPathElement>(".aqe-cursor-flag-notch")?.setAttribute(
    "transform",
    `translate(${cursorFlagNotchOffset(x, flagX).toFixed(2)} 0)`,
  );
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
  if (label) label.textContent = "0 ms / -- Hz";
  const flag = visualizer.querySelector<SVGGElement>(".aqe-cursor-flag");
  if (flag) {
    flag.setAttribute("visibility", "hidden");
    flag.setAttribute("transform", `translate(${PLOT.left + CURSOR_FLAG_HALF_WIDTH} ${CURSOR_FLAG_Y})`);
    flag.querySelector<SVGTextElement>(".aqe-cursor-flag-current")!.textContent = "0 ms";
    flag.querySelector<SVGTextElement>(".aqe-cursor-flag-pitch")!.textContent = " / -- Hz";
    flag.querySelector<SVGPathElement>(".aqe-cursor-flag-notch")?.removeAttribute("transform");
  }
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

function clampedCursorFlagX(cursorX: number): number {
  const minX = PLOT.left + CURSOR_FLAG_HALF_WIDTH;
  const maxX = PLOT.width - PLOT.right - CURSOR_FLAG_HALF_WIDTH;
  return Math.max(minX, Math.min(cursorX, maxX));
}

function cursorFlagNotchOffset(cursorX: number, flagX: number): number {
  return Math.max(-CURSOR_FLAG_NOTCH_MAX_OFFSET, Math.min(cursorX - flagX, CURSOR_FLAG_NOTCH_MAX_OFFSET));
}
