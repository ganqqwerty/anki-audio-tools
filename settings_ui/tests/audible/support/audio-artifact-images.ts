import type { AudioOracleAnalysis, MonoAudio } from "../fixtures/audio-oracle-types.js";
import type { AudibleExpectation } from "../fixtures/audible-contract.js";
import { asFloat32 } from "./audio-signal.js";
import { createRaster, drawLine, encodePng, fillRect, setPixel, type Rgb } from "./png-raster.js";

export interface AudibleTimelineMarker {
  captureTimeMs: number;
  kind?: "cursor" | "media" | "pass" | "seek" | "transport";
  label?: string;
}

const COLORS = {
  axis: { blue: 72, green: 72, red: 72 },
  background: { blue: 248, green: 248, red: 248 },
  content: { blue: 122, green: 168, red: 42 },
  silence: { blue: 214, green: 214, red: 214 },
  trace: { blue: 40, green: 85, red: 225 },
  transition: { blue: 86, green: 180, red: 238 },
  unknown: { blue: 76, green: 70, red: 168 },
} satisfies Record<string, Rgb>;

export function renderAudibleTimeline(input: {
  analysis: AudioOracleAnalysis;
  expectations: readonly AudibleExpectation[];
  markers?: readonly AudibleTimelineMarker[];
}): Buffer {
  const width = 1_000;
  const height = 420;
  const margin = 40;
  const plotWidth = width - margin * 2;
  const raster = createRaster(width, height, COLORS.background);
  const durationMs = Math.max(1, input.analysis.metrics.durationMs);
  const sourceDurationMs = Math.max(
    1,
    ...input.analysis.references.map((reference) => reference.durationMs),
  );
  drawExpectedRow(raster, input.expectations, durationMs, margin, plotWidth);
  for (const segment of input.analysis.segments) {
    const x = margin + (segment.captureStartMs / durationMs) * plotWidth;
    const segmentWidth = Math.max(1, (segment.durationMs / durationMs) * plotWidth);
    fillRect(raster, x, 82, segmentWidth, 35, COLORS[segment.kind]);
  }
  drawLine(raster, margin, 145, width - margin, 145, COLORS.axis);
  drawLine(raster, margin, height - margin, width - margin, height - margin, COLORS.axis);
  let previous: { x: number; y: number } | null = null;
  for (const sample of input.analysis.trace) {
    if (sample.sourceTimeMs === null) {
      previous = null;
      continue;
    }
    const point = {
      x: margin + (sample.captureTimeMs / durationMs) * plotWidth,
      y: height - margin - (sample.sourceTimeMs / sourceDurationMs) * (height - 200),
    };
    if (previous) drawLine(raster, previous.x, previous.y, point.x, point.y, COLORS.trace, 2);
    previous = point;
  }
  for (const marker of input.markers ?? []) {
    const x = margin + (marker.captureTimeMs / durationMs) * plotWidth;
    drawLine(raster, x, 20, x, height - margin, markerColor(marker.kind));
  }
  return encodePng(raster);
}

export function renderAlignedSpectrogram(expected: MonoAudio, captured: MonoAudio): Buffer {
  const width = 720;
  const height = 440;
  const gap = 12;
  const panelHeight = Math.floor((height - gap) / 2);
  const raster = createRaster(width, height, { blue: 8, green: 8, red: 8 });
  const expectedSpectrum = spectrogram(expected, width, panelHeight);
  const capturedSpectrum = spectrogram(captured, width, panelHeight);
  const peak = Math.max(1e-8, matrixPeak(expectedSpectrum), matrixPeak(capturedSpectrum));
  paintSpectrum(raster, expectedSpectrum, 0, peak);
  fillRect(raster, 0, panelHeight, width, gap, { blue: 245, green: 245, red: 245 });
  paintSpectrum(raster, capturedSpectrum, panelHeight + gap, peak);
  return encodePng(raster);
}

function drawExpectedRow(
  raster: ReturnType<typeof createRaster>,
  expectations: readonly AudibleExpectation[],
  captureDurationMs: number,
  margin: number,
  plotWidth: number,
): void {
  const expectedDuration = expectations.reduce(
    (duration, expectation) => duration + expectationDuration(expectation),
    0,
  );
  let cursor = 0;
  const scale = captureDurationMs / Math.max(captureDurationMs, expectedDuration);
  for (const expectation of expectations) {
    const duration = expectationDuration(expectation) * scale;
    const x = margin + (cursor / captureDurationMs) * plotWidth;
    const width = Math.max(1, (duration / captureDurationMs) * plotWidth);
    fillRect(
      raster,
      x,
      25,
      width,
      35,
      expectation.kind === "segment" ? COLORS.content : COLORS.silence,
    );
    cursor += duration;
  }
}

function spectrogram(audio: MonoAudio, width: number, height: number): Float32Array[] {
  const samples = asFloat32(audio.samples);
  const windowSize = Math.min(256, Math.max(32, samples.length));
  const bins = Math.min(height, Math.floor(windowSize / 2));
  return Array.from({ length: height }, (_, row) => {
    const values = new Float32Array(width);
    const bin = Math.min(bins - 1, Math.floor(((height - 1 - row) / height) * bins));
    for (let column = 0; column < width; column += 1) {
      const center = Math.floor(((column + 0.5) / width) * samples.length);
      const start = Math.max(0, Math.min(samples.length - windowSize, center - windowSize / 2));
      let real = 0;
      let imaginary = 0;
      for (let offset = 0; offset < windowSize; offset += 1) {
        const hann = 0.5 - 0.5 * Math.cos((2 * Math.PI * offset) / (windowSize - 1));
        const angle = (2 * Math.PI * bin * offset) / windowSize;
        const value = (samples[start + offset] ?? 0) * hann;
        real += value * Math.cos(angle);
        imaginary -= value * Math.sin(angle);
      }
      values[column] = Math.log1p(Math.sqrt(real * real + imaginary * imaginary));
    }
    return values;
  });
}

function paintSpectrum(
  raster: ReturnType<typeof createRaster>,
  spectrum: readonly Float32Array[],
  yOffset: number,
  peak: number,
): void {
  spectrum.forEach((row, y) => {
    row.forEach((magnitude, x) => {
      const normalized = Math.max(0, Math.min(1, magnitude / peak));
      setPixel(raster, x, yOffset + y, heatColor(normalized));
    });
  });
}

function matrixPeak(matrix: readonly Float32Array[]): number {
  let peak = 0;
  for (const row of matrix) for (const value of row) peak = Math.max(peak, value);
  return peak;
}

function heatColor(value: number): Rgb {
  return {
    blue: Math.round(40 + 215 * Math.max(0, 1 - Math.abs(value - 0.25) * 4)),
    green: Math.round(255 * Math.max(0, 1 - Math.abs(value - 0.55) * 2.5)),
    red: Math.round(255 * Math.max(0, 1 - Math.abs(value - 0.85) * 3)),
  };
}

function expectationDuration(expectation: AudibleExpectation): number {
  if (expectation.kind === "segment") return expectation.endMs - expectation.startMs;
  return expectation.expectedMs ?? (expectation.minMs + expectation.maxMs) / 2;
}

function markerColor(kind: AudibleTimelineMarker["kind"]): Rgb {
  if (kind === "seek") return { blue: 210, green: 60, red: 130 };
  if (kind === "pass") return { blue: 30, green: 130, red: 240 };
  return { blue: 100, green: 100, red: 100 };
}
import { Buffer } from "node:buffer";
