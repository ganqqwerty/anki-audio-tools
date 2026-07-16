export interface AudibleSegmentExpectation {
  endMs: number;
  endPositionToleranceMs?: number;
  kind: "segment";
  maxDurationMs?: number;
  minDurationMs?: number;
  source: string;
  startMs: number;
  startPositionToleranceMs?: number;
}

export interface AudibleSilenceExpectation {
  expectedMs?: number;
  kind: "silence";
  maxMs: number;
  minMs: number;
}

export type AudibleExpectation = AudibleSegmentExpectation | AudibleSilenceExpectation;

export interface AudibleContract {
  expectations: readonly AudibleExpectation[];
  options?: AudibleContractOptions;
}

export interface AudibleContractOptions {
  allowClipping?: boolean;
  allowOverlap?: boolean;
  allowTrailingSilence?: boolean;
  durationToleranceMs?: number;
  maxLeadingSilenceMs?: number;
  maxTransitionMs?: number;
  sourcePositionToleranceMs?: number;
}

export type AudibleContractFailureCode =
  | "boundary_overshoot"
  | "boundary_undershoot"
  | "clipping"
  | "duration"
  | "leading_silence"
  | "missing_content"
  | "missing_silence"
  | "overlap"
  | "source"
  | "start_position"
  | "unexpected_audio"
  | "unknown_audio";

export interface AudibleContractFailure {
  actualSegmentIndex: number | null;
  code: AudibleContractFailureCode;
  expectationIndex: number | null;
  message: string;
}

export interface AudibleContractMatch {
  actualSegmentIndex: number;
  expectationIndex: number;
}

export interface AudibleContractMetrics {
  boundaryOvershootMs: number;
  boundaryUndershootMs: number;
  heardStartErrorMs: number | null;
  leadingSilenceMs: number;
  wrongPrefixLeakageMs: number;
}

export interface AudibleContractVerdict {
  diagnosis: string;
  failures: AudibleContractFailure[];
  matches: AudibleContractMatch[];
  metrics: AudibleContractMetrics;
  pass: boolean;
}
