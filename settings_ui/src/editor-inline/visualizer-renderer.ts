import { draftSelectionRegion, selectionRegion } from "./selection-state.js";
import {
  PLOT,
  type PlotGeometry,
  drawLabels,
  drawLearnerPitch,
  drawPitch,
  drawXAxis,
  formatPitchHz,
  formatTime,
  pathForIntensity,
  pitchHzAtMs,
  plotGeometryForSvg,
  plotWidth,
  svgViewBoxScale,
  xForMs,
} from "./plot.js";
import { msVisibleInViewport } from "./time-viewport.js";
import type { NormalizedProsodyTrack, VisualizerElement } from "./types.js";
import { renderSelection } from "./visualizer-selection-renderer.js";
import { learnerTrackForReplacement, type LearnerOverlayOptions } from "./visualizer-learner-overlay.js";
import {
  readVisualizerDurationMs,
  readVisualizerSelectionState,
  readVisualizerTargetDurationMs,
  readVisualizerTimeViewport,
  resetVisualizerTimeViewport,
} from "./visualizer-state.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import { graphRequested } from "./field-state.js";
import {
  readLearnerDurationMsForVisualizer,
  setLearnerDurationMsForVisualizer,
  setPlaybackPassRuntime,
  setTargetDurationMsForVisualizer,
} from "./visualizer-runtime-state.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

type CursorRenderCache = NonNullable<VisualizerElement["__aqeCursorRenderCache"]>;

const CURSOR_FLAG_WIDTH = 82;
const CURSOR_FLAG_HALF_WIDTH = CURSOR_FLAG_WIDTH / 2;
const CURSOR_FLAG_BOX_HEIGHT = 20;
const PLAYBACK_TEXT_PAINT_INTERVAL_MS = 100;

export function renderGraphRequested(visualizer: VisualizerElement, options: LearnerOverlayOptions = {}): void {
  visualizer.hidden = false;
  const ord = fieldOrd(visualizer);
  const preserveLearnerOverlay = options.preserveLearnerOverlay === true && visualizer.__aqeLearnerTrack !== undefined;
  if (preserveLearnerOverlay) {
    visualizer.dataset.pendingLearnerOverlayTargetDurationMs = String(readVisualizerTargetDurationMs(visualizer));
  } else {
    delete visualizer.dataset.pendingLearnerOverlayTargetDurationMs;
  }
  writeFieldState(ord, graphRequested(readFieldState(ord)));
  setTargetDurationMsForVisualizer(visualizer, 0);
  if (!preserveLearnerOverlay) setLearnerDurationMsForVisualizer(visualizer, 0);
  setPlaybackPassRuntime(visualizer, {
    endMs: 0,
    loop: false,
    regionMode: "full",
    resetCursorMs: 0,
    startMs: 0,
  });
  resetVisualizerTimeViewport(visualizer, 0);
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
  if (!preserveLearnerOverlay) delete visualizer.__aqeLearnerTrack;
  delete visualizer.__aqeTrack;
  resetVisualizerPlot(visualizer, { clearLearnerOverlay: !preserveLearnerOverlay });
}

export function renderVisualizerTrack(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: LearnerOverlayOptions = {},
): void {
  visualizer.hidden = false;
  const ord = fieldOrd(visualizer);
  const preservedLearnerTrack = learnerTrackForReplacement(visualizer, track, options);
  writeFieldState(ord, {
    ...readFieldState(ord),
    graph: {
      active: true,
      analyzerName: track.analyzerName || "",
      busy: false,
      durationMs: track.durationMs || 0,
      hasTrack: true,
    },
    sourceFilename: track.sourceFilename || "",
  });
  setTargetDurationMsForVisualizer(visualizer, track.durationMs || 0);
  delete visualizer.dataset.pendingLearnerOverlayTargetDurationMs;
  if (preservedLearnerTrack) {
    visualizer.__aqeLearnerTrack = preservedLearnerTrack;
    setLearnerDurationMsForVisualizer(visualizer, preservedLearnerTrack.durationMs || 0);
  } else {
    setLearnerDurationMsForVisualizer(visualizer, 0);
    delete visualizer.__aqeLearnerTrack;
  }
  visualizer.__aqeTrack = track;
  const plot = syncVisualizerViewBox(visualizer);
  resetVisualizerTimeViewport(visualizer, track.durationMs || 0, plotWidth(plot));
  renderProsodyTracks(visualizer);
}

export function renderLearnerVisualizerTrack(visualizer: VisualizerElement, track: NormalizedProsodyTrack): void {
  if (!readFieldState(fieldOrd(visualizer)).graph.hasTrack || !visualizer.__aqeTrack) return;
  visualizer.__aqeLearnerTrack = track;
  setLearnerDurationMsForVisualizer(visualizer, track.durationMs || 0);
  renderProsodyTracks(visualizer);
}

export function renderVisualizerStatus(visualizer: VisualizerElement, message: string, kind = "info"): void {
  const spinner = visualizer.closest<HTMLElement>(".aqe-controls")?.querySelector<HTMLElement>(".aqe-spinner")
    ?? visualizer.querySelector<HTMLElement>(".aqe-spinner");
  const processing = kind === "processing";
  const ord = fieldOrd(visualizer);
  const state = readFieldState(ord);
  writeFieldState(ord, {
    ...state,
    graph: { ...state.graph, busy: processing },
  });
  visualizer.dataset.statusMessage = message || "";
  if (spinner) spinner.hidden = !processing;
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
  renderCursorProjection(visualizer, ms, durationMs, { geometry: true, text });
  if (text) visualizer.__aqeCursorTextPaintedAtMs = nowMs;
}

export function startPlaybackCursorTransition(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
): void {
  const durationMs = readVisualizerDurationMs(visualizer);
  const nodes = cursorRenderCache(visualizer);
  if (!nodes.cssCursor || !durationMs || endMs <= startMs) return;
  renderCursorProjection(visualizer, startMs, durationMs, { geometry: true, text: true });
  const viewport = readVisualizerTimeViewport(visualizer);
  if (!msVisibleInViewport(startMs, viewport) || !msVisibleInViewport(endMs, viewport)) return;
  const plot = plotGeometryForVisualizer(visualizer);
  const endX = cssXForViewBoxX(visualizer, xForMs(endMs, durationMs, viewport, plot));
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
  const viewport = readVisualizerTimeViewport(visualizer);
  if (options.geometry) {
    const plot = nodes.svg ? plotGeometryForSvg(nodes.svg) : PLOT;
    const x = xForMs(ms, durationMs, viewport, plot);
    renderCssCursorGeometry(visualizer, nodes, x, plot, ms);
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

export function resetVisualizerPlot(
  visualizer: VisualizerElement,
  options: { clearLearnerOverlay?: boolean } = {},
): void {
  visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.setAttribute("d", "");
  clearText(visualizer, ".aqe-pitch");
  if (options.clearLearnerOverlay !== false) clearLearnerVisualizerTrack(visualizer);
  clearText(visualizer, ".aqe-labels");
  clearText(visualizer, ".aqe-x-axis");
}

export function clearLearnerVisualizerTrack(visualizer: VisualizerElement): void {
  clearText(visualizer, ".aqe-learner-pitch");
}

export function resetCursorProjection(visualizer: VisualizerElement): void {
  const nodes = cursorRenderCache(visualizer);
  const plot = plotGeometryForVisualizer(visualizer);
  stopPlaybackCursorTransition(visualizer);
  renderCssCursorGeometry(visualizer, nodes, plot.left, plot);
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

export function renderCurrentSelectionFromState(visualizer: VisualizerElement): void {
  const selectionState = readVisualizerSelectionState(visualizer);
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  renderSelection(
    visualizer,
    selectionRegion(selectionState, durationMs),
    draftSelectionRegion(selectionState, durationMs),
  );
}

function clearText(root: VisualizerElement, selector: string): void {
  const node = root.querySelector<HTMLElement | SVGElement>(selector);
  if (node) node.textContent = "";
}

export function renderProsodyTracks(visualizer: VisualizerElement): void {
  const target = visualizer.__aqeTrack;
  if (!target) return;
  const plot = syncVisualizerViewBox(visualizer);
  const learner = visualizer.__aqeLearnerTrack;
  const learnerDurationMs = Math.max(readLearnerDurationMsForVisualizer(visualizer), learner?.durationMs || 0);
  const durationMs = Math.max(target.durationMs || 0, learnerDurationMs);
  const viewport = readVisualizerTimeViewport(visualizer);
  const pitchRange = combinedPitchRange(target, learner);
  const ord = fieldOrd(visualizer);
  const state = readFieldState(ord);
  writeFieldState(ord, {
    ...state,
    graph: { ...state.graph, durationMs },
  });
  setTargetDurationMsForVisualizer(visualizer, target.durationMs || 0);
  setLearnerDurationMsForVisualizer(visualizer, learnerDurationMs);
  const intensity = visualizer.querySelector<SVGPathElement>(".aqe-intensity");
  if (intensity) intensity.setAttribute("d", pathForIntensity(target.points, durationMs, viewport, plot));
  drawPitch(visualizer, target, {
    durationMs,
    pitchMaxHz: pitchRange.maxHz,
    pitchMinHz: pitchRange.minHz,
    plot,
    viewport,
  });
  if (learner) {
    drawLearnerPitch(visualizer, learner, {
      durationMs,
      pitchMaxHz: pitchRange.maxHz,
      pitchMinHz: pitchRange.minHz,
      plot,
      viewport,
    });
  } else {
    clearLearnerVisualizerTrack(visualizer);
  }
  drawLabels(visualizer, target, {
    pitchMaxHz: pitchRange.maxHz,
    pitchMinHz: pitchRange.minHz,
    plot,
  });
  drawXAxis(visualizer, durationMs, viewport, plot);
}

function combinedPitchRange(
  target: NormalizedProsodyTrack,
  learner?: NormalizedProsodyTrack,
): { maxHz: number | null; minHz: number | null } {
  const mins = [target.pitchMinHz, learner?.pitchMinHz].filter(isFiniteNumber);
  const maxes = [target.pitchMaxHz, learner?.pitchMaxHz].filter(isFiniteNumber);
  return {
    minHz: mins.length ? Math.min(...mins) : null,
    maxHz: maxes.length ? Math.max(...maxes) : null,
  };
}

function isFiniteNumber(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function plotGeometryForVisualizer(visualizer: VisualizerElement): PlotGeometry {
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  return svg ? plotGeometryForSvg(svg) : PLOT;
}

function syncVisualizerViewBox(visualizer: VisualizerElement): PlotGeometry {
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!svg) return PLOT;
  const rectWidth = Number(svg.getBoundingClientRect().width) || PLOT.width;
  const width = Math.max(PLOT.width, Math.round(rectWidth));
  const viewBox = `0 0 ${width} ${PLOT.height}`;
  if (svg.getAttribute("viewBox") !== viewBox) svg.setAttribute("viewBox", viewBox);
  const plot = plotGeometryForSvg(svg);
  syncPlotClipPath(svg, plot);
  return plot;
}

function syncPlotClipPath(svg: SVGSVGElement, plot: PlotGeometry): void {
  const clip = svg.querySelector<SVGRectElement>("clipPath > rect");
  if (!clip) return;
  clip.setAttribute("x", String(plot.left));
  clip.setAttribute("y", String(plot.top));
  clip.setAttribute("width", String(plot.width - plot.left - plot.right));
  clip.setAttribute("height", String(plot.height - plot.top - plot.bottom));
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
    svg: visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg"),
  };
  visualizer.__aqeCursorRenderCache = cache;
  return cache;
}

function renderCssCursorGeometry(
  visualizer: VisualizerElement,
  nodes: CursorRenderCache,
  cursorX: number,
  plot: PlotGeometry,
  ms?: number,
): void {
  const viewport = readVisualizerTimeViewport(visualizer);
  const scale = cssScaleFor(nodes.svg);
  const cursor = nodes.cssCursor;
  if (!cursor) return;
  if (typeof ms === "number" && !msVisibleInViewport(ms, viewport)) {
    cursor.style.display = "none";
    cursor.style.transition = "none";
    return;
  }
  cursor.style.display = "block";
  cursor.style.transition = "none";
  cursor.style.transform = `translate3d(${(cursorX * scale.x).toFixed(2)}px, 0, 0)`;
  if (nodes.cssLine) {
    nodes.cssLine.style.top = `${(plot.top * scale.y).toFixed(2)}px`;
    nodes.cssLine.style.height = `${((plot.height - plot.top - plot.bottom) * scale.y).toFixed(2)}px`;
  }
  if (nodes.cssFlag) {
    const flagX = clampedCursorFlagX(cursorX, plot);
    const flagOffsetPx = (flagX - cursorX) * scale.x - CURSOR_FLAG_HALF_WIDTH;
    nodes.cssFlag.style.top = `${(plot.top * scale.y - CURSOR_FLAG_BOX_HEIGHT).toFixed(2)}px`;
    nodes.cssFlag.style.transform = `translateX(${flagOffsetPx.toFixed(2)}px)`;
  }
}

function clampedCursorFlagX(cursorX: number, plot: PlotGeometry): number {
  const minX = plot.left + CURSOR_FLAG_HALF_WIDTH;
  const maxX = plot.width - plot.right - CURSOR_FLAG_HALF_WIDTH;
  return Math.max(minX, Math.min(cursorX, maxX));
}

function cssXForViewBoxX(visualizer: VisualizerElement, x: number): number {
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  return x * cssScaleFor(svg).x;
}
function cssScaleFor(svg: SVGSVGElement | null): { x: number; y: number } {
  return svg ? svgViewBoxScale(svg) : { x: 1, y: 1 };
}
