export type AudioSamples = Float32Array | readonly number[];

export interface MonoAudio {
  sampleRate: number;
  samples: AudioSamples;
}

export interface AcousticReference extends MonoAudio {
  metadata?: Record<string, unknown>;
  path?: string;
  source: string;
}

export type TraceClassification = "content" | "silence" | "unknown";

export interface SourcePositionTraceSample {
  captureTimeMs: number;
  classification: TraceClassification;
  clipped: boolean;
  confidence: number;
  overlap: boolean;
  rms: number;
  secondaryConfidence: number;
  secondarySource: string | null;
  secondarySourceTimeMs: number | null;
  source: string | null;
  sourceTimeMs: number | null;
}

export type AudioSegmentKind = "content" | "silence" | "transition" | "unknown";

export interface AudioSegment {
  captureEndMs: number;
  captureStartMs: number;
  clipped: boolean;
  durationMs: number;
  kind: AudioSegmentKind;
  meanConfidence: number;
  meanRms: number;
  meanSecondaryConfidence: number;
  overlap: boolean;
  source: string | null;
  sourceEndMs: number | null;
  sourceStartMs: number | null;
}

export interface AudioOracleMetrics {
  clippedRunCount: number;
  clippedSampleCount: number;
  dropoutCount: number;
  duplicateEventCount: number;
  durationMs: number;
  firstAudibleMs: number | null;
  firstConfidentMs: number | null;
  maxClippedRunMs: number;
  overlapDurationMs: number;
  overlapFrameCount: number;
  p95AbsoluteRateError: number | null;
  silenceDurationMs: number;
  silenceThresholdRms: number;
  sourceDiscontinuityCount: number;
  sourceReversalCount: number;
  traceIntervalMs: number;
  unknownDurationMs: number;
}

export interface AudioOracleAnalysis {
  capture: {
    sampleRate: number;
    sampleCount: number;
  };
  metrics: AudioOracleMetrics;
  references: Array<{
    durationMs: number;
    path?: string;
    sampleRate: number;
    source: string;
  }>;
  segments: AudioSegment[];
  trace: SourcePositionTraceSample[];
}

export interface AudioOracleOptions {
  analysisWindowMs?: number;
  clippingThreshold?: number;
  coarseCandidateCount?: number;
  coarseHopMs?: number;
  fingerprintPoints?: number;
  fineHopMs?: number;
  fineHopSamples?: number;
  minConfidence?: number;
  overlapConfidenceRatio?: number;
  overlapMinConfidence?: number;
  secondaryExclusionMs?: number;
  silenceFloorRms?: number;
  silenceRelativeToReference?: number;
  traceIntervalMs?: number;
  transitionMaxMs?: number;
}

export interface AnalyzeAudioCaptureInput {
  capture: MonoAudio;
  options?: AudioOracleOptions;
  references: readonly AcousticReference[];
}
