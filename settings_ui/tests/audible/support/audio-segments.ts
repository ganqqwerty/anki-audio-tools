import type {
  AudioOracleMetrics,
  AudioSegment,
  SourcePositionTraceSample,
} from "../fixtures/audio-oracle-types.js";
import type { ResolvedOracleOptions } from "./audio-match-engine.js";
import { percentile } from "./audio-signal.js";

interface SegmentAccumulator {
  endIndex: number;
  startIndex: number;
}

export function segmentSourcePositionTrace(
  trace: readonly SourcePositionTraceSample[],
  durationMs: number,
  options: ResolvedOracleOptions,
): AudioSegment[] {
  if (!trace.length) return [];
  const accumulators: SegmentAccumulator[] = [];
  let startIndex = 0;
  for (let index = 1; index < trace.length; index += 1) {
    if (!samplesAreContinuous(trace[index - 1], trace[index], options.traceIntervalMs)) {
      accumulators.push({ endIndex: index, startIndex });
      startIndex = index;
    }
  }
  accumulators.push({ endIndex: trace.length, startIndex });
  const segments = accumulators.map(({ startIndex: start, endIndex: end }) =>
    materializeSegment(trace, start, end, durationMs, options.traceIntervalMs),
  );
  for (let index = 0; index < segments.length; index += 1) {
    const segment = segments[index];
    if (!segment || segment.durationMs > options.transitionMaxMs) continue;
    const previous = segments[index - 1];
    const next = segments[index + 1];
    const touchesContent = previous?.kind === "content" || next?.kind === "content";
    if (segment.kind === "unknown" && touchesContent) segment.kind = "transition";
    const contentNeighbor = previous?.kind === "content" ? previous : next;
    const touchesSilence = previous?.kind === "silence" || next?.kind === "silence";
    const bridgesContent = previous?.kind === "content" && next?.kind === "content";
    const touchesTransition = previous?.kind === "transition" || next?.kind === "transition";
    if (
      segment.kind === "content" &&
      (touchesSilence || bridgesContent || touchesTransition) &&
      contentNeighbor?.kind === "content"
    ) {
      segment.kind = "transition";
    }
  }
  return segments;
}

export function calculateOracleMetrics(input: {
  captureSamples: Float32Array;
  durationMs: number;
  options: ResolvedOracleOptions;
  segments: readonly AudioSegment[];
  silenceThresholdRms: number;
  trace: readonly SourcePositionTraceSample[];
}): AudioOracleMetrics {
  const { captureSamples, durationMs, options, segments, trace } = input;
  const clipping = clippingMetrics(
    captureSamples,
    options.clippingThreshold,
    durationMs / Math.max(1, captureSamples.length),
  );
  const movement = movementMetrics(trace, options.traceIntervalMs);
  const overlapFrameCount = trace.filter((sample) => sample.overlap).length;
  return {
    ...clipping,
    ...movement,
    dropoutCount: segments.filter(
      (segment, index) =>
        segment.kind === "silence" &&
        segments[index - 1]?.kind === "content" &&
        segments[index + 1]?.kind === "content",
    ).length,
    duplicateEventCount: duplicateEvents(segments, options.traceIntervalMs),
    durationMs,
    firstAudibleMs:
      trace.find((sample) => sample.classification !== "silence")?.captureTimeMs ?? null,
    firstConfidentMs:
      trace.find((sample) => sample.classification === "content")?.captureTimeMs ?? null,
    overlapDurationMs: overlapFrameCount * options.traceIntervalMs,
    overlapFrameCount,
    silenceDurationMs: totalDuration(segments, "silence"),
    silenceThresholdRms: input.silenceThresholdRms,
    traceIntervalMs: options.traceIntervalMs,
    unknownDurationMs: totalDuration(segments, "unknown"),
  };
}

function samplesAreContinuous(
  previous: SourcePositionTraceSample | undefined,
  current: SourcePositionTraceSample | undefined,
  intervalMs: number,
): boolean {
  if (!previous || !current || previous.classification !== current.classification) return false;
  if (current.classification !== "content") return true;
  if (
    previous.source !== current.source ||
    previous.sourceTimeMs === null ||
    current.sourceTimeMs === null
  ) {
    return false;
  }
  const captureDelta = current.captureTimeMs - previous.captureTimeMs;
  const sourceDelta = current.sourceTimeMs - previous.sourceTimeMs;
  return Math.abs(sourceDelta - captureDelta) <= Math.max(20, intervalMs * 2);
}

function materializeSegment(
  trace: readonly SourcePositionTraceSample[],
  startIndex: number,
  endIndex: number,
  durationMs: number,
  intervalMs: number,
): AudioSegment {
  const samples = trace.slice(startIndex, endIndex);
  const first = samples[0];
  const last = samples.at(-1);
  if (!first || !last) throw new Error("Cannot materialize an empty audio segment.");
  const captureStartMs = Math.max(0, first.captureTimeMs - intervalMs / 2);
  const captureEndMs = Math.min(durationMs, last.captureTimeMs + intervalMs / 2);
  const sourceOffsets = samples.flatMap((sample) =>
    sample.sourceTimeMs === null ? [] : [sample.sourceTimeMs - sample.captureTimeMs],
  );
  const sourceOffset = sourceOffsets.length ? percentile(sourceOffsets, 50) : null;
  return {
    captureEndMs,
    captureStartMs,
    clipped: samples.some((sample) => sample.clipped),
    durationMs: captureEndMs - captureStartMs,
    kind: first.classification,
    meanConfidence: mean(samples.map((sample) => sample.confidence)),
    meanRms: mean(samples.map((sample) => sample.rms)),
    meanSecondaryConfidence: mean(samples.map((sample) => sample.secondaryConfidence)),
    overlap: samples.filter((sample) => sample.overlap).length >= 3,
    source: first.source,
    sourceEndMs: sourceOffset === null ? null : sourceOffset + captureEndMs,
    sourceStartMs: sourceOffset === null ? null : sourceOffset + captureStartMs,
  };
}

function movementMetrics(
  trace: readonly SourcePositionTraceSample[],
  intervalMs: number,
): Pick<
  AudioOracleMetrics,
  "p95AbsoluteRateError" | "sourceDiscontinuityCount" | "sourceReversalCount"
> {
  let sourceDiscontinuityCount = 0;
  let sourceReversalCount = 0;
  const rateErrors: number[] = [];
  for (let index = 1; index < trace.length; index += 1) {
    const previous = trace[index - 1];
    const current = trace[index];
    if (
      previous?.classification !== "content" ||
      current?.classification !== "content" ||
      previous.source !== current.source ||
      previous.sourceTimeMs === null ||
      current.sourceTimeMs === null
    ) {
      continue;
    }
    const captureDelta = current.captureTimeMs - previous.captureTimeMs;
    const sourceDelta = current.sourceTimeMs - previous.sourceTimeMs;
    if (sourceDelta < -intervalMs / 2) sourceReversalCount += 1;
    if (Math.abs(sourceDelta - captureDelta) > Math.max(20, intervalMs * 2)) {
      sourceDiscontinuityCount += 1;
    } else if (captureDelta > 0) {
      rateErrors.push(Math.abs(sourceDelta / captureDelta - 1));
    }
  }
  return {
    p95AbsoluteRateError: rateErrors.length ? percentile(rateErrors, 95) : null,
    sourceDiscontinuityCount,
    sourceReversalCount,
  };
}

function duplicateEvents(segments: readonly AudioSegment[], toleranceMs: number): number {
  let count = 0;
  const priorBySource = new Map<string, Array<{ endMs: number; startMs: number }>>();
  for (const segment of segments) {
    if (
      segment.kind !== "content" ||
      !segment.source ||
      segment.sourceStartMs === null ||
      segment.sourceEndMs === null
    ) {
      continue;
    }
    const prior = priorBySource.get(segment.source) ?? [];
    if (
      prior.some(
        (range) =>
          segment.sourceStartMs! < range.endMs - toleranceMs &&
          segment.sourceEndMs! > range.startMs + toleranceMs,
      )
    ) {
      count += 1;
    }
    prior.push({ endMs: segment.sourceEndMs, startMs: segment.sourceStartMs });
    priorBySource.set(segment.source, prior);
  }
  return count;
}

function clippingMetrics(
  samples: Float32Array,
  threshold: number,
  sampleDurationMs: number,
): Pick<AudioOracleMetrics, "clippedRunCount" | "clippedSampleCount" | "maxClippedRunMs"> {
  let clippedRunCount = 0;
  let clippedSampleCount = 0;
  let currentRun = 0;
  let maxRun = 0;
  for (const sample of samples) {
    if (Math.abs(sample) >= threshold) {
      clippedSampleCount += 1;
      currentRun += 1;
      maxRun = Math.max(maxRun, currentRun);
    } else if (currentRun) {
      clippedRunCount += 1;
      currentRun = 0;
    }
  }
  if (currentRun) clippedRunCount += 1;
  return { clippedRunCount, clippedSampleCount, maxClippedRunMs: maxRun * sampleDurationMs };
}

function totalDuration(segments: readonly AudioSegment[], kind: AudioSegment["kind"]): number {
  return segments
    .filter((segment) => segment.kind === kind)
    .reduce((duration, segment) => duration + segment.durationMs, 0);
}

function mean(values: readonly number[]): number {
  return values.length ? values.reduce((total, value) => total + value, 0) / values.length : 0;
}
