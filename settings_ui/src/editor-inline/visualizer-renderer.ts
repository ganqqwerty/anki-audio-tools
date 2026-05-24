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

type CursorRenderCache = NonNullable<VisualizerElement["__aqeCursorRenderCache"]>;

const CURSOR_FLAG_WIDTH = 82;
const CURSOR_FLAG_HALF_WIDTH = CURSOR_FLAG_WIDTH / 2;
const CURSOR_FLAG_BOX_HEIGHT = 20;
const PLAYBACK_TEXT_PAINT_INTERVAL_MS = 100;

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
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
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
  const spinner = visualizer.querySelector<HTMLElement>(".aqe-spinner");
  const processing = kind === "processing";
  visualizer.dataset.graphBusy = processing ? "true" : "false";
  visualizer.dataset.statusMessage = message || "";
  if (spinner) spinner.hidden = !processing;
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
    startHandle?.classList.remove("aqe-selection-resize-dragging");
    endHandle?.classList.remove("aqe-selection-resize-dragging");
    startGrip?.setAttribute("visibility", "hidden");
    endGrip?.setAttribute("visibility", "hidden");
    startGrip?.classList.remove("aqe-selection-resize-dragging");
    endGrip?.classList.remove("aqe-selection-resize-dragging");
    clearSelectionOverlayGeometry(visualizer);
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
  const showHandles = selection !== null;
  const handlesDragging = selection !== null && draftSelection !== null;
  for (const [handle, grip, x] of [[startHandle, startGrip, startX], [endHandle, endGrip, endX]] as const) {
    handle?.setAttribute("visibility", showHandles ? "visible" : "hidden");
    handle?.classList.toggle("aqe-selection-resize-dragging", handlesDragging);
    handle?.setAttribute("x", (x - 5).toFixed(2));
    handle?.setAttribute("y", handleY.toFixed(2));
    handle?.setAttribute("width", "10");
    handle?.setAttribute("height", handleHeight.toFixed(2));
    grip?.setAttribute("visibility", showHandles ? "visible" : "hidden");
    grip?.classList.toggle("aqe-selection-resize-dragging", handlesDragging);
    grip?.setAttribute("transform", `translate(${x.toFixed(2)} ${handleCenterY.toFixed(2)})`);
  }
  setSelectionOverlayGeometry(visualizer, startX, endX, plotTop, plotBottom);
}

export function renderCursor(visualizer: VisualizerElement, ms: number, durationMs: number): void {
  renderCursorProjection(visualizer, ms, durationMs, { geometry: true, text: true });
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
}

export function renderPlaybackCursor(
  visualizer: VisualizerElement,
  ms: number,
  durationMs: number,
  nowMs: number,
): void {
  const lastTextPaintedAtMs = visualizer.__aqeCursorTextPaintedAtMs;
  const text = lastTextPaintedAtMs === undefined
    || nowMs - lastTextPaintedAtMs >= PLAYBACK_TEXT_PAINT_INTERVAL_MS;
  if (!text) return;
  renderCursorProjection(visualizer, ms, durationMs, { geometry: false, text });
  if (text) visualizer.__aqeCursorTextPaintedAtMs = nowMs;
}

export function startPlaybackCursorTransition(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
): void {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const nodes = cursorRenderCache(visualizer);
  if (!nodes.cssCursor || !durationMs || endMs <= startMs) return;
  renderCursorProjection(visualizer, startMs, durationMs, { geometry: true, text: true });
  const endX = cssXForViewBoxX(visualizer, xForMs(endMs, durationMs));
  nodes.cssCursor.style.transition = "none";
  void nodes.cssCursor.offsetWidth;
  nodes.cssCursor.style.transition = `transform ${Math.max(0, endMs - startMs).toFixed(0)}ms linear`;
  nodes.cssCursor.style.transform = `translate3d(${endX.toFixed(2)}px, 0, 0)`;
}

export function stopPlaybackCursorTransition(visualizer: VisualizerElement): void {
  const cursor = cursorRenderCache(visualizer).cssCursor;
  if (cursor) cursor.style.transition = "none";
}

function renderCursorProjection(
  visualizer: VisualizerElement,
  ms: number,
  durationMs: number,
  options: { geometry: boolean; text: boolean },
): void {
  const nodes = cursorRenderCache(visualizer);
  const x = xForMs(ms, durationMs);
  if (options.geometry) {
    renderCssCursorGeometry(visualizer, nodes, x);
  }
  if (options.text) {
    const currentText = formatTime(ms, durationMs);
    const track = visualizer.__aqeTrack;
    const pitchHz = track ? pitchHzAtMs(track.points, ms) : null;
    const pitchText = formatPitchHz(pitchHz);
    if (nodes.label) nodes.label.textContent = `${currentText} / ${pitchText}`;
    if (nodes.cssFlagCurrent) nodes.cssFlagCurrent.textContent = currentText;
    if (nodes.cssFlagPitch) nodes.cssFlagPitch.textContent = ` / ${pitchText}`;
  }
}

export function resetVisualizerPlot(visualizer: VisualizerElement): void {
  visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.setAttribute("d", "");
  clearText(visualizer, ".aqe-pitch");
  clearText(visualizer, ".aqe-labels");
  clearText(visualizer, ".aqe-x-axis");
}

export function resetCursorProjection(visualizer: VisualizerElement): void {
  const nodes = cursorRenderCache(visualizer);
  stopPlaybackCursorTransition(visualizer);
  renderCssCursorGeometry(visualizer, nodes, PLOT.left);
  if (nodes.label) nodes.label.textContent = "0 ms / -- Hz";
  if (nodes.cssFlagCurrent) nodes.cssFlagCurrent.textContent = "0 ms";
  if (nodes.cssFlagPitch) nodes.cssFlagPitch.textContent = " / -- Hz";
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
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

function plotWrapperFor(visualizer: VisualizerElement): HTMLElement | null {
  return visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
}

function setSelectionOverlayGeometry(
  visualizer: VisualizerElement,
  startX: number,
  endX: number,
  plotTop: number,
  plotBottom: number,
): void {
  const wrapper = plotWrapperFor(visualizer);
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!wrapper || !svg) return;
  const rect = svg.getBoundingClientRect();
  const rectWidth = Number(rect.width) || PLOT.width;
  const rectHeight = Number(rect.height) || PLOT.height;
  const scale = Math.min(rectWidth / PLOT.width, rectHeight / PLOT.height) || 1;
  const startPx = startX * scale;
  const endPx = endX * scale;
  const plotTopPx = plotTop * scale;
  const plotBottomPx = plotBottom * scale;
  const plotHeightPx = Math.max(0, plotBottomPx - plotTopPx);
  const plotLeftPx = PLOT.left * scale;
  const plotRightEdgePx = (PLOT.width - PLOT.right) * scale;
  const plotRightPx = Math.max(0, rectWidth - plotRightEdgePx);
  const contentHeightPx = PLOT.height * scale;
  const toolbarLeftPx = Math.max(plotLeftPx, Math.min(endPx, plotRightEdgePx - 6));
  const toolbarTopPx = Math.max(plotTopPx, Math.min(plotBottomPx, contentHeightPx - 34));

  wrapper.dataset.selectionOverlayReady = "true";
  wrapper.style.setProperty("--aqe-selection-start-px", `${startPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-end-px", `${endPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-bottom-px", `${plotBottomPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-toolbar-left-px", `${toolbarLeftPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-toolbar-top-px", `${toolbarTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-left-px", `${plotLeftPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-right-px", `${plotRightPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-top-px", `${plotTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-height-px", `${plotHeightPx.toFixed(2)}px`);
  setOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar"), toolbarLeftPx, toolbarTopPx);
  setOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar-dot"), toolbarLeftPx, toolbarTopPx);
}

function clearSelectionOverlayGeometry(visualizer: VisualizerElement): void {
  const wrapper = plotWrapperFor(visualizer);
  if (!wrapper) return;
  wrapper.dataset.selectionOverlayReady = "false";
  for (const property of [
    "--aqe-selection-start-px",
    "--aqe-selection-end-px",
    "--aqe-selection-bottom-px",
    "--aqe-selection-toolbar-left-px",
    "--aqe-selection-toolbar-top-px",
    "--aqe-plot-left-px",
    "--aqe-plot-right-px",
    "--aqe-plot-top-px",
    "--aqe-plot-height-px",
  ]) {
    wrapper.style.removeProperty(property);
  }
  clearOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar"));
  clearOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar-dot"));
}

function setOverlayNodePosition(node: HTMLElement | null, leftPx: number, topPx: number): void {
  if (!node) return;
  node.style.left = `${leftPx.toFixed(2)}px`;
  node.style.top = `${topPx.toFixed(2)}px`;
}

function clearOverlayNodePosition(node: HTMLElement | null): void {
  if (!node) return;
  node.style.removeProperty("left");
  node.style.removeProperty("top");
}

function cursorRenderCache(visualizer: VisualizerElement): CursorRenderCache {
  const cached = visualizer.__aqeCursorRenderCache;
  if (cached) return cached;
  const cssFlag = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag");
  const cache: CursorRenderCache = {
    cssCursor: visualizer.querySelector<HTMLElement>(".aqe-css-cursor"),
    cssFlag,
    cssFlagCurrent: cssFlag?.querySelector<HTMLElement>(".aqe-css-cursor-flag-current") ?? null,
    cssFlagPitch: cssFlag?.querySelector<HTMLElement>(".aqe-css-cursor-flag-pitch") ?? null,
    cssLine: visualizer.querySelector<HTMLElement>(".aqe-css-cursor-line"),
    label: visualizer.querySelector<HTMLElement>(".aqe-cursor-label"),
  };
  visualizer.__aqeCursorRenderCache = cache;
  return cache;
}

function renderCssCursorGeometry(visualizer: VisualizerElement, nodes: CursorRenderCache, cursorX: number): void {
  const scale = cssScaleFor(visualizer);
  const cursor = nodes.cssCursor;
  if (!cursor) return;
  cursor.style.display = "block";
  cursor.style.transition = "none";
  cursor.style.transform = `translate3d(${cssXForViewBoxX(visualizer, cursorX).toFixed(2)}px, 0, 0)`;
  if (nodes.cssLine) {
    nodes.cssLine.style.top = `${(PLOT.top * scale).toFixed(2)}px`;
    nodes.cssLine.style.height = `${((PLOT.height - PLOT.top - PLOT.bottom) * scale).toFixed(2)}px`;
  }
  if (nodes.cssFlag) {
    const flagX = clampedCursorFlagX(cursorX);
    const flagOffsetPx = (flagX - cursorX) * scale - CURSOR_FLAG_HALF_WIDTH;
    nodes.cssFlag.style.top = `${(PLOT.top * scale - CURSOR_FLAG_BOX_HEIGHT).toFixed(2)}px`;
    nodes.cssFlag.style.transform = `translateX(${flagOffsetPx.toFixed(2)}px)`;
  }
}

function clampedCursorFlagX(cursorX: number): number {
  const minX = PLOT.left + CURSOR_FLAG_HALF_WIDTH;
  const maxX = PLOT.width - PLOT.right - CURSOR_FLAG_HALF_WIDTH;
  return Math.max(minX, Math.min(cursorX, maxX));
}

function cssXForViewBoxX(visualizer: VisualizerElement, x: number): number {
  return x * cssScaleFor(visualizer);
}

function cssScaleFor(visualizer: VisualizerElement): number {
  const cached = Number(visualizer.dataset.cssCursorScale || "0");
  if (cached > 0) return cached;
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const rect = svg?.getBoundingClientRect();
  const rectWidth = Number(rect?.width) || PLOT.width;
  const rectHeight = Number(rect?.height) || PLOT.height;
  const scale = Math.min(rectWidth / PLOT.width, rectHeight / PLOT.height) || 1;
  visualizer.dataset.cssCursorScale = String(scale);
  return scale;
}
