import type {
  AcousticReference,
  AnalyzeAudioCaptureInput,
  AudioOracleAnalysis,
} from "./audio-oracle-types.js";
import { buildSourcePositionTrace } from "../support/audio-match-engine.js";
import { calculateOracleMetrics, segmentSourcePositionTrace } from "../support/audio-segments.js";
import { audioDurationMs } from "../support/audio-signal.js";

export * from "./audio-oracle-types.js";
export {
  decodeMonoWav,
  decodeReferenceAudio,
  decodeReferenceFromManifest,
  encodeMonoWav,
} from "../support/audio-files.js";
export {
  expectedAudioForContract,
  writeAudibleFailureArtifacts,
  writeAudibleMetricsArtifact,
  type AudibleArtifactAttachment,
  type AudibleArtifactMetadata,
  type AudibleFailureArtifacts,
  type WriteAudibleFailureArtifactsInput,
} from "../support/audio-artifacts.js";
export type { AudibleTimelineMarker } from "../support/audio-artifact-images.js";

export function analyzeAudioCapture(input: AnalyzeAudioCaptureInput): AudioOracleAnalysis {
  validateInput(input);
  const traceResult = buildSourcePositionTrace(input.capture, input.references, input.options);
  const durationMs = audioDurationMs(input.capture);
  const segments = segmentSourcePositionTrace(traceResult.trace, durationMs, traceResult.options);
  return {
    capture: {
      sampleCount: input.capture.samples.length,
      sampleRate: input.capture.sampleRate,
    },
    metrics: calculateOracleMetrics({
      captureSamples: traceResult.captureSamples,
      durationMs,
      options: traceResult.options,
      segments,
      silenceThresholdRms: traceResult.silenceThresholdRms,
      trace: traceResult.trace,
    }),
    references: input.references.map(referenceSummary),
    segments,
    trace: traceResult.trace,
  };
}

function validateInput(input: AnalyzeAudioCaptureInput): void {
  if (!Number.isFinite(input.capture.sampleRate) || input.capture.sampleRate <= 0) {
    throw new Error("Capture sampleRate must be a positive finite number.");
  }
  if (!input.references.length) throw new Error("At least one acoustic reference is required.");
  const sources = new Set<string>();
  for (const reference of input.references) {
    if (!reference.source) throw new Error("Every acoustic reference needs a source identifier.");
    if (sources.has(reference.source)) {
      throw new Error(`Acoustic reference source identifiers must be unique: ${reference.source}.`);
    }
    sources.add(reference.source);
    if (!Number.isFinite(reference.sampleRate) || reference.sampleRate <= 0) {
      throw new Error(`Reference ${reference.source} has an invalid sampleRate.`);
    }
    if (!reference.samples.length) throw new Error(`Reference ${reference.source} has no samples.`);
  }
}

function referenceSummary(reference: AcousticReference): AudioOracleAnalysis["references"][number] {
  return {
    durationMs: audioDurationMs(reference),
    ...(reference.path ? { path: reference.path } : {}),
    sampleRate: reference.sampleRate,
    source: reference.source,
  };
}
