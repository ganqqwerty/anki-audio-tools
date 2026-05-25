import type { NormalizedProsodyTrack, ProsodyPoint, VisualizerElement } from "./types.js";

export const PLOT = { width: 620, height: 150, left: 44, right: 10, top: 10, bottom: 34 } as const;

export function plotWidth(): number {
  return PLOT.width - PLOT.left - PLOT.right;
}

export function plotHeight(): number {
  return PLOT.height - PLOT.top - PLOT.bottom;
}

export function xForMs(ms: number, durationMs: number): number {
  if (!durationMs) return PLOT.left;
  return PLOT.left + Math.max(0, Math.min(1, ms / durationMs)) * plotWidth();
}

export function yForPitch(pitchHz: number | null, minHz: number | null, maxHz: number | null): number {
  if (!pitchHz || !minHz || !maxHz || maxHz <= minHz) return PLOT.height - PLOT.bottom;
  const ratio = Math.max(0, Math.min(1, (pitchHz - minHz) / (maxHz - minHz)));
  return PLOT.top + (1 - ratio) * plotHeight();
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

export function pathForIntensity(points: readonly ProsodyPoint[], durationMs: number): string {
  if (!points.length || !durationMs) return "";
  const base = PLOT.height - PLOT.bottom;
  const first = points[0];
  if (!first) return "";
  const head = `M ${xForMs(first[0], durationMs).toFixed(2)} ${base.toFixed(2)}`;
  const body = points.map((point) => {
    const x = xForMs(point[0], durationMs).toFixed(2);
    const intensity = Math.max(0, Math.min(1, point[2] ?? 0));
    const y = (base - intensity * plotHeight()).toFixed(2);
    return `L ${x} ${y}`;
  }).join(" ");
  const last = points.at(-1) ?? first;
  const tail = `L ${xForMs(last[0], durationMs).toFixed(2)} ${base.toFixed(2)} Z`;
  return `${head} ${body} ${tail}`;
}

export function pitchSegments(
  points: readonly ProsodyPoint[],
  durationMs: number,
  minHz: number | null,
  maxHz: number | null,
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
    current.push([xForMs(point[0], durationMs), yForPitch(pitchHz, minHz, maxHz)]);
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
}

export function drawPitch(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: Pick<PitchDrawOptions, "durationMs" | "pitchMaxHz" | "pitchMinHz"> = {},
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
  options: Pick<PitchDrawOptions, "durationMs" | "pitchMaxHz" | "pitchMinHz">,
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
  for (const segment of pitchSegments(track.points, durationMs, minHz, maxHz)) {
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
  track: NormalizedProsodyTrack,
  options: { pitchMaxHz?: number | null; pitchMinHz?: number | null } = {},
): void {
  const group = visualizer.querySelector<SVGGElement>(".aqe-labels");
  if (!group) return;
  group.textContent = "";
  const maxHz = options.pitchMaxHz ?? track.pitchMaxHz ?? 500;
  const minHz = options.pitchMinHz ?? track.pitchMinHz ?? 75;
  for (const item of [
    [maxHz, PLOT.top + 10],
    [minHz, PLOT.height - PLOT.bottom],
  ] as const) {
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("class", "aqe-hz-label");
    text.setAttribute("x", "2");
    text.setAttribute("y", String(item[1]));
    text.textContent = `${Math.round(item[0])} Hz`;
    group.appendChild(text);
  }
}

export function drawXAxis(visualizer: VisualizerElement, durationMs: number): void {
  const group = visualizer.querySelector<SVGGElement>(".aqe-x-axis");
  if (!group) return;
  group.textContent = "";
  const ticks = [0, durationMs / 2, durationMs].filter((value, index, values) => index === 0 || value !== values[index - 1]);
  for (const tick of ticks) {
    const x = xForMs(tick, durationMs);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("class", "aqe-x-tick");
    line.setAttribute("x1", x.toFixed(2));
    line.setAttribute("x2", x.toFixed(2));
    line.setAttribute("y1", String(PLOT.height - PLOT.bottom));
    line.setAttribute("y2", String(PLOT.height - PLOT.bottom + 4));
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("class", "aqe-x-label");
    text.setAttribute("x", x.toFixed(2));
    text.setAttribute("y", String(PLOT.height - 8));
    text.textContent = formatTime(tick, durationMs);
    group.append(line, text);
  }
}

export function graphPixelBounds(svg: SVGSVGElement): { left: number; width: number } {
  const rect = svg.getBoundingClientRect();
  const rectWidth = Number(rect.width) || PLOT.width;
  const rectHeight = Number(rect.height) || PLOT.height;
  const scaleX = Math.min(rectWidth / PLOT.width, rectHeight / PLOT.height) || 1;
  return {
    left: rect.left + PLOT.left * scaleX,
    width: plotWidth() * scaleX,
  };
}

export function cursorMsFromEvent(event: Pick<PointerEvent, "clientX">, svg: SVGSVGElement, durationMs: number): number {
  const bounds = graphPixelBounds(svg);
  const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
  return ratio * durationMs;
}

function voicedPitch(point: ProsodyPoint): number | null {
  const pitchHz = point[1];
  return point[3] === true && typeof pitchHz === "number" && Number.isFinite(pitchHz) ? pitchHz : null;
}
