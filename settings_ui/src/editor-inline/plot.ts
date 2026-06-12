import type { NormalizedProsodyTrack, ProsodyPoint, VisualizerElement } from "./types.js";
import type { TimeViewport } from "./time-viewport.js";
import { fullTimeViewport, msForViewportRatio, ratioForMsInViewport } from "./time-viewport.js";

export interface PlotGeometry {
  bottom: number;
  height: number;
  left: number;
  right: number;
  top: number;
  width: number;
}

export const PLOT = { width: 620, height: 150, left: 10, right: 10, top: 28, bottom: 34 } as const;

interface SvgViewBoxMetrics {
  height: number;
  width: number;
  x: number;
  y: number;
}

export function plotWidth(plot: PlotGeometry = PLOT): number {
  return plot.width - plot.left - plot.right;
}

export function plotHeight(plot: PlotGeometry = PLOT): number {
  return plot.height - plot.top - plot.bottom;
}

export function xForMs(
  ms: number,
  durationMs: number,
  viewport?: TimeViewport | null,
  plot: PlotGeometry = PLOT,
): number {
  const activeViewport = viewport ?? fullTimeViewport(durationMs);
  const ratio = ratioForMsInViewport(ms, activeViewport);
  return plot.left + Math.max(0, Math.min(1, ratio)) * plotWidth(plot);
}

export function yForPitch(
  pitchHz: number | null,
  minHz: number | null,
  maxHz: number | null,
  plot: PlotGeometry = PLOT,
): number {
  if (!pitchHz || !minHz || !maxHz || maxHz <= minHz) return plot.height - plot.bottom;
  const ratio = Math.max(0, Math.min(1, (pitchHz - minHz) / (maxHz - minHz)));
  return plot.top + (1 - ratio) * plotHeight(plot);
}

export function formatTime(ms: number, durationMs: number): string {
  if (durationMs && durationMs < 2000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function formatPitchHz(pitchHz: number | null): string {
  return pitchHz === null ? "-- Hz" : `${Math.round(pitchHz)} Hz`;
}

export function pitchHzAtMs(points: readonly ProsodyPoint[], ms: number): number | null {
  if (!points.length) return null;
  const targetMs = Number.isFinite(ms) ? ms : 0;
  let low = 0;
  let high = points.length - 1;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const point = points[mid];
    if (!point) break;
    if (point[0] === targetMs) return voicedPitch(point);
    if (point[0] < targetMs) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  const next = points[low] ?? null;
  const previous = points[low - 1] ?? null;
  if (!next) return previous ? voicedPitch(previous) : null;
  const nextPitch = voicedPitch(next);
  if (!previous) return nextPitch;
  const previousPitch = voicedPitch(previous);
  if (previousPitch === null || nextPitch === null) return null;
  const spanMs = next[0] - previous[0];
  if (spanMs <= 0) return nextPitch;
  const ratio = (targetMs - previous[0]) / spanMs;
  return previousPitch + (nextPitch - previousPitch) * ratio;
}

export function pathForIntensity(
  points: readonly ProsodyPoint[],
  durationMs: number,
  viewport?: TimeViewport | null,
  plot: PlotGeometry = PLOT,
): string {
  if (!points.length || !durationMs) return "";
  const base = plot.height - plot.bottom;
  const first = points[0];
  if (!first) return "";
  const head = `M ${xForMs(first[0], durationMs, viewport, plot).toFixed(2)} ${base.toFixed(2)}`;
  const body = points.map((point) => {
    const x = xForMs(point[0], durationMs, viewport, plot).toFixed(2);
    const intensity = Math.max(0, Math.min(1, point[2] ?? 0));
    const y = (base - intensity * plotHeight(plot)).toFixed(2);
    return `L ${x} ${y}`;
  }).join(" ");
  const last = points.at(-1) ?? first;
  const tail = `L ${xForMs(last[0], durationMs, viewport, plot).toFixed(2)} ${base.toFixed(2)} Z`;
  return `${head} ${body} ${tail}`;
}

export function pitchSegments(
  points: readonly ProsodyPoint[],
  durationMs: number,
  minHz: number | null,
  maxHz: number | null,
  viewport?: TimeViewport | null,
  plot: PlotGeometry = PLOT,
): number[][][] {
  const segments: number[][][] = [];
  let current: number[][] = [];
  for (const point of points) {
    const pitchHz = point[1];
    const voiced = point[3] === true && pitchHz !== null && pitchHz !== undefined;
    if (!voiced) {
      if (current.length) segments.push(current);
      current = [];
      continue;
    }
    current.push([xForMs(point[0], durationMs, viewport, plot), yForPitch(pitchHz, minHz, maxHz, plot)]);
  }
  if (current.length) segments.push(current);
  return segments;
}

interface PitchDrawOptions {
  durationMs?: number;
  groupSelector: string;
  pathClass: string;
  pitchMaxHz?: number | null;
  pitchMinHz?: number | null;
  plot?: PlotGeometry;
  viewport?: TimeViewport | null;
}

export function drawPitch(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: Pick<PitchDrawOptions, "durationMs" | "pitchMaxHz" | "pitchMinHz" | "plot" | "viewport"> = {},
): void {
  drawPitchPaths(visualizer, track, {
    ...options,
    groupSelector: ".aqe-pitch",
    pathClass: "aqe-pitch-path",
  });
}

export function drawLearnerPitch(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: Pick<PitchDrawOptions, "durationMs" | "pitchMaxHz" | "pitchMinHz" | "plot" | "viewport">,
): void {
  drawPitchPaths(visualizer, track, {
    ...options,
    groupSelector: ".aqe-learner-pitch",
    pathClass: "aqe-learner-pitch-path",
  });
}

function drawPitchPaths(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: PitchDrawOptions,
): void {
  const group = visualizer.querySelector<SVGGElement>(options.groupSelector);
  if (!group) return;
  group.textContent = "";
  const durationMs = options.durationMs ?? track.durationMs;
  const minHz = options.pitchMinHz ?? track.pitchMinHz;
  const maxHz = options.pitchMaxHz ?? track.pitchMaxHz;
  const plot = options.plot ?? PLOT;
  for (const segment of pitchSegments(track.points, durationMs, minHz, maxHz, options.viewport, plot)) {
    if (segment.length < 2) continue;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("class", options.pathClass);
    path.setAttribute(
      "d",
      segment.map((point, index) => {
        const x = point[0] ?? 0;
        const y = point[1] ?? 0;
        return `${index ? "L" : "M"} ${x.toFixed(2)} ${y.toFixed(2)}`;
      }).join(" "),
    );
    group.appendChild(path);
  }
}

export function drawLabels(
  visualizer: VisualizerElement,
  _track: NormalizedProsodyTrack,
  options: { pitchMaxHz?: number | null; pitchMinHz?: number | null; plot?: PlotGeometry } = {},
): void {
  void options;
  const group = visualizer.querySelector<SVGGElement>(".aqe-labels");
  if (!group) return;
  group.textContent = "";
}

export function drawXAxis(
  visualizer: VisualizerElement,
  durationMs: number,
  viewport?: TimeViewport | null,
  plot: PlotGeometry = PLOT,
): void {
  const group = visualizer.querySelector<SVGGElement>(".aqe-x-axis");
  if (!group) return;
  group.textContent = "";
  const activeViewport = viewport ?? fullTimeViewport(durationMs);
  const midpoint = activeViewport.startMs + (activeViewport.endMs - activeViewport.startMs) / 2;
  const ticks = [activeViewport.startMs, midpoint, activeViewport.endMs]
    .filter((value, index, values) => index === 0 || Math.round(value) !== Math.round(values[index - 1] ?? -1));
  for (const tick of ticks) {
    const x = xForMs(tick, durationMs, activeViewport, plot);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("class", "aqe-x-tick");
    line.setAttribute("x1", x.toFixed(2));
    line.setAttribute("x2", x.toFixed(2));
    line.setAttribute("y1", String(plot.height - plot.bottom));
    line.setAttribute("y2", String(plot.height - plot.bottom + 4));
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("class", "aqe-x-label");
    text.setAttribute("x", x.toFixed(2));
    text.setAttribute("y", String(plot.height - 8));
    text.textContent = formatTime(tick, durationMs);
    group.append(line, text);
  }
}

export function svgViewBoxScale(svg: SVGSVGElement): { x: number; y: number } {
  const metrics = renderedViewBoxMetrics(svg);
  return {
    x: metrics.scaleX,
    y: metrics.scaleY,
  };
}

export function plotGeometryForSvg(svg: SVGSVGElement): PlotGeometry {
  const viewBoxWidth = svgViewBoxMetrics(svg).width;
  return {
    ...PLOT,
    width: Math.max(PLOT.left + PLOT.right + 1, viewBoxWidth),
  };
}

export function graphPixelBounds(svg: SVGSVGElement): { left: number; width: number } {
  const metrics = renderedViewBoxMetrics(svg);
  const plot = plotGeometryForSvg(svg);
  const left = metrics.left + (plot.left - metrics.viewBox.x) * metrics.scaleX;
  const right = metrics.left + (plot.width - plot.right - metrics.viewBox.x) * metrics.scaleX;
  return {
    left,
    width: Math.max(1, right - left),
  };
}

export function cursorMsFromEvent(
  event: Pick<PointerEvent, "clientX">,
  svg: SVGSVGElement,
  durationMs: number,
  viewport?: TimeViewport | null,
): number {
  const bounds = graphPixelBounds(svg);
  const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
  return msForViewportRatio(viewport ?? fullTimeViewport(durationMs), ratio);
}

function voicedPitch(point: ProsodyPoint): number | null {
  const pitchHz = point[1];
  return point[3] === true && typeof pitchHz === "number" && Number.isFinite(pitchHz) ? pitchHz : null;
}

function svgViewBoxMetrics(svg: SVGSVGElement): SvgViewBoxMetrics {
  const base = svg.viewBox.baseVal;
  const raw = (svg.getAttribute("viewBox") || "").trim().split(/\s+/);
  const width = finitePositiveOrFallback(base.width, Number.parseFloat(raw[2] || ""), PLOT.width);
  const height = finitePositiveOrFallback(base.height, Number.parseFloat(raw[3] || ""), PLOT.height);
  return {
    height,
    width,
    x: finiteOrFallback(base.x, Number.parseFloat(raw[0] || ""), 0),
    y: finiteOrFallback(base.y, Number.parseFloat(raw[1] || ""), 0),
  };
}

function renderedViewBoxMetrics(svg: SVGSVGElement): {
  left: number;
  scaleX: number;
  scaleY: number;
  top: number;
  viewBox: SvgViewBoxMetrics;
} {
  const rect = svg.getBoundingClientRect();
  const viewBox = svgViewBoxMetrics(svg);
  const viewportWidth = finitePositiveOrFallback(svg.clientWidth, Number(rect.width), viewBox.width);
  const viewportHeight = finitePositiveOrFallback(svg.clientHeight, Number(rect.height), viewBox.height);
  const viewportLeft = rect.left + finiteOrFallback(svg.clientLeft, 0, 0);
  const viewportTop = rect.top + finiteOrFallback(svg.clientTop, 0, 0);
  const preserveAspectRatio = normalizedPreserveAspectRatio(svg.getAttribute("preserveAspectRatio"));
  if (preserveAspectRatio.align === "none") {
    return {
      left: viewportLeft,
      scaleX: viewportWidth / viewBox.width,
      scaleY: viewportHeight / viewBox.height,
      top: viewportTop,
      viewBox,
    };
  }
  const scale = preserveAspectRatio.mode === "slice"
    ? Math.max(viewportWidth / viewBox.width, viewportHeight / viewBox.height)
    : Math.min(viewportWidth / viewBox.width, viewportHeight / viewBox.height);
  const extraX = viewportWidth - viewBox.width * scale;
  const extraY = viewportHeight - viewBox.height * scale;
  return {
    left: viewportLeft + alignedOffset(extraX, preserveAspectRatio.align, "x"),
    scaleX: scale,
    scaleY: scale,
    top: viewportTop + alignedOffset(extraY, preserveAspectRatio.align, "y"),
    viewBox,
  };
}

function normalizedPreserveAspectRatio(value: string | null): { align: string; mode: "meet" | "slice" } {
  const tokens = (value || "").trim().split(/\s+/).filter(Boolean);
  const filtered = tokens[0] === "defer" ? tokens.slice(1) : tokens;
  const align = filtered[0] || "xMidYMid";
  const mode = filtered[1] === "slice" ? "slice" : "meet";
  return { align, mode };
}

function alignedOffset(extra: number, align: string, axis: "x" | "y"): number {
  if (axis === "x") {
    if (align.includes("xMax")) return extra;
    if (align.includes("xMid")) return extra / 2;
    return 0;
  }
  if (align.includes("YMax")) return extra;
  if (align.includes("YMid")) return extra / 2;
  return 0;
}

function finiteOrFallback(primary: number, fallback: number, defaultValue: number): number {
  if (Number.isFinite(primary)) return primary;
  if (Number.isFinite(fallback)) return fallback;
  return defaultValue;
}

function finitePositiveOrFallback(primary: number, fallback: number, defaultValue: number): number {
  if (Number.isFinite(primary) && primary > 0) return primary;
  if (Number.isFinite(fallback) && fallback > 0) return fallback;
  return defaultValue;
}
