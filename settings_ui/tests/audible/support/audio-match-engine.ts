import type {
  AcousticReference,
  AudioOracleOptions,
  MonoAudio,
  SourcePositionTraceSample,
} from "../fixtures/audio-oracle-types.js";
import {
  asFloat32,
  percentile,
  resampleLinear,
  rms,
  samplesForMs,
  windowCopy,
} from "./audio-signal.js";
import { matchAudioWindow, prepareAudioWindowMatcher } from "./audio-window-matcher.js";

export interface ResolvedOracleOptions {
  analysisWindowMs: number;
  clippingThreshold: number;
  coarseCandidateCount: number;
  coarseHopMs: number;
  fingerprintPoints: number;
  fineHopMs: number;
  fineHopSamples: number | null;
  minConfidence: number;
  overlapConfidenceRatio: number;
  overlapMinConfidence: number;
  secondaryExclusionMs: number;
  silenceFloorRms: number;
  silenceRelativeToReference: number;
  traceIntervalMs: number;
  transitionMaxMs: number;
}

export interface TraceResult {
  captureSamples: Float32Array;
  options: ResolvedOracleOptions;
  referenceSamples: Float32Array[];
  silenceThresholdRms: number;
  trace: SourcePositionTraceSample[];
}

export function buildSourcePositionTrace(
  capture: MonoAudio,
  references: readonly AcousticReference[],
  inputOptions: AudioOracleOptions = {},
): TraceResult {
  const options = resolveOptions(inputOptions);
  const captureSamples = asFloat32(capture.samples);
  const referenceSamples = references.map((reference) =>
    resampleLinear(reference, capture.sampleRate),
  );
  const windowSamples = Math.min(
    captureSamples.length,
    samplesForMs(capture.sampleRate, options.analysisWindowMs),
  );
  const matcher = prepareAudioWindowMatcher({
    options,
    references,
    referenceSamples,
    sampleRate: capture.sampleRate,
    windowSamples,
  });
  const energyRms = traceEnergy(captureSamples, capture.sampleRate, options.traceIntervalMs);
  const referenceRms = Math.max(...referenceSamples.map((samples) => rms(samples)), 0);
  const measuredFloor = percentile(energyRms, 10);
  const relativeFloor = referenceRms * options.silenceRelativeToReference;
  const silenceThresholdRms = Math.max(
    options.silenceFloorRms,
    relativeFloor,
    Math.min(referenceRms * 0.04, measuredFloor * 2.5),
  );
  const trace = energyRms.map((frameRms, frameIndex) => {
    const captureTimeMs = frameIndex * options.traceIntervalMs;
    const pointSample = Math.min(
      Math.max(0, captureSamples.length - 1),
      Math.round((captureTimeMs * capture.sampleRate) / 1_000),
    );
    const clipped = energyWindowClipped(
      captureSamples,
      pointSample,
      samplesForMs(capture.sampleRate, options.traceIntervalMs),
      options.clippingThreshold,
    );
    if (frameRms <= silenceThresholdRms || !windowSamples) {
      return emptyTraceSample(captureTimeMs, frameRms, clipped, "silence");
    }
    const contextStart = Math.max(
      0,
      Math.min(captureSamples.length - windowSamples, pointSample - Math.floor(windowSamples / 2)),
    );
    const captureWindow = windowCopy(captureSamples, contextStart, windowSamples);
    const matches = matchAudioWindow(captureWindow, matcher);
    const { best, secondary } = matches;
    if (!best || best.confidence < options.minConfidence) {
      const unknown = emptyTraceSample(captureTimeMs, frameRms, clipped, "unknown");
      unknown.confidence = best?.confidence ?? 0;
      unknown.secondaryConfidence = secondary?.confidence ?? 0;
      return unknown;
    }
    const pointOffset = pointSample - contextStart;
    const secondaryConfidence = secondary?.confidence ?? 0;
    const overlap =
      matches.residualRatio >= 0.65 &&
      secondaryConfidence >= options.overlapMinConfidence &&
      secondaryConfidence >= best.rawConfidence * options.overlapConfidenceRatio;
    return {
      captureTimeMs,
      classification: "content" as const,
      clipped,
      confidence: best.confidence,
      overlap,
      rms: frameRms,
      secondaryConfidence,
      secondarySource: secondary ? (references[secondary.referenceIndex]?.source ?? null) : null,
      secondarySourceTimeMs: secondary
        ? ((secondary.startSample + pointOffset) / capture.sampleRate) * 1_000
        : null,
      source: references[best.referenceIndex]?.source ?? null,
      sourceTimeMs: ((best.startSample + pointOffset) / capture.sampleRate) * 1_000,
    };
  });
  stabilizeTransitionMatches(trace, options);
  return { captureSamples, options, referenceSamples, silenceThresholdRms, trace };
}

export function resolveOptions(options: AudioOracleOptions): ResolvedOracleOptions {
  return {
    analysisWindowMs: options.analysisWindowMs ?? 40,
    clippingThreshold: options.clippingThreshold ?? 0.999,
    coarseCandidateCount: options.coarseCandidateCount ?? 6,
    coarseHopMs: options.coarseHopMs ?? 10,
    fingerprintPoints: options.fingerprintPoints ?? 128,
    fineHopMs: options.fineHopMs ?? 1,
    fineHopSamples: options.fineHopSamples ?? (options.fineHopMs === undefined ? 4 : null),
    minConfidence: options.minConfidence ?? 0.45,
    overlapConfidenceRatio: options.overlapConfidenceRatio ?? 0.78,
    overlapMinConfidence: options.overlapMinConfidence ?? 0.5,
    secondaryExclusionMs: options.secondaryExclusionMs ?? 60,
    silenceFloorRms: options.silenceFloorRms ?? 0.0001,
    silenceRelativeToReference: options.silenceRelativeToReference ?? 0.02,
    traceIntervalMs: options.traceIntervalMs ?? 10,
    transitionMaxMs: options.transitionMaxMs ?? 20,
  };
}

function traceEnergy(samples: Float32Array, sampleRate: number, intervalMs: number): number[] {
  const hop = samplesForMs(sampleRate, intervalMs);
  const half = Math.max(1, Math.floor(hop / 2));
  const frameCount = Math.max(1, Math.ceil(samples.length / hop));
  return Array.from({ length: frameCount }, (_, frame) => {
    const point = frame * hop;
    return rms(samples, point - half, point + half);
  });
}

function energyWindowClipped(
  samples: Float32Array,
  point: number,
  width: number,
  threshold: number,
): boolean {
  const start = Math.max(0, point - Math.floor(width / 2));
  const end = Math.min(samples.length, start + width);
  for (let index = start; index < end; index += 1) {
    if (Math.abs(samples[index] ?? 0) >= threshold) return true;
  }
  return false;
}

function emptyTraceSample(
  captureTimeMs: number,
  frameRms: number,
  clipped: boolean,
  classification: "silence" | "unknown",
): SourcePositionTraceSample {
  return {
    captureTimeMs,
    classification,
    clipped,
    confidence: 0,
    overlap: false,
    rms: frameRms,
    secondaryConfidence: 0,
    secondarySource: null,
    secondarySourceTimeMs: null,
    source: null,
    sourceTimeMs: null,
  };
}

function stabilizeTransitionMatches(
  trace: SourcePositionTraceSample[],
  options: ResolvedOracleOptions,
): void {
  const maxRepairFrames = Math.max(1, Math.ceil(options.transitionMaxMs / options.traceIntervalMs));
  for (let start = 1; start < trace.length - 1; start += 1) {
    const previous = trace[start - 1];
    if (
      previous?.classification !== "content" ||
      previous.sourceTimeMs === null ||
      previous.confidence < 0.8
    ) {
      continue;
    }
    for (let length = 1; length <= maxRepairFrames; length += 1) {
      const anchor = trace[start + length];
      const uncertain = trace.slice(start, start + length);
      if (
        anchor?.classification !== "content" ||
        anchor.source !== previous.source ||
        anchor.sourceTimeMs === null ||
        anchor.confidence < 0.8 ||
        uncertain.some(
          (sample) =>
            (sample.classification === "content" && sample.source !== previous.source) ||
            sample.confidence >= 0.8,
        )
      ) {
        continue;
      }
      const captureDelta = anchor.captureTimeMs - previous.captureTimeMs;
      const sourceDelta = anchor.sourceTimeMs - previous.sourceTimeMs;
      if (Math.abs(sourceDelta - captureDelta) > 20) continue;
      for (let offset = 0; offset < uncertain.length; offset += 1) {
        const sample = uncertain[offset];
        if (!sample) continue;
        const fraction = (sample.captureTimeMs - previous.captureTimeMs) / captureDelta;
        sample.classification = "content";
        sample.confidence = Math.min(previous.confidence, anchor.confidence);
        sample.source = previous.source;
        sample.sourceTimeMs = previous.sourceTimeMs + sourceDelta * fraction;
        sample.overlap = false;
      }
      start += length - 1;
      break;
    }
  }
}
