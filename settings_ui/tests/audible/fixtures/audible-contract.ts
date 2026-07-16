import type { AudioOracleAnalysis, AudioSegment } from "./audio-oracle-types.js";
import type {
  AudibleContract,
  AudibleContractFailure,
  AudibleContractFailureCode,
  AudibleContractMatch,
  AudibleContractMetrics,
  AudibleContractOptions,
  AudibleContractVerdict,
  AudibleExpectation,
  AudibleSegmentExpectation,
  AudibleSilenceExpectation,
} from "./audible-contract-types.js";

export * from "./audible-contract-types.js";

const DEFAULT_OPTIONS: Required<AudibleContractOptions> = {
  allowClipping: false,
  allowOverlap: false,
  allowTrailingSilence: true,
  durationToleranceMs: 30,
  maxLeadingSilenceMs: 200,
  maxTransitionMs: 20,
  sourcePositionToleranceMs: 25,
};

export function evaluateAudibleContract(
  analysis: AudioOracleAnalysis,
  input: AudibleContract | readonly AudibleExpectation[],
  optionOverrides: AudibleContractOptions = {},
): AudibleContractVerdict {
  const contract: AudibleContract = Array.isArray(input)
    ? { expectations: input as readonly AudibleExpectation[] }
    : (input as AudibleContract);
  const options = { ...DEFAULT_OPTIONS, ...contract.options, ...optionOverrides };
  const comparisonOptions = {
    ...options,
    sourcePositionToleranceMs:
      options.sourcePositionToleranceMs + analysis.metrics.traceIntervalMs / 2,
  };
  const failures: AudibleContractFailure[] = [];
  const matches: AudibleContractMatch[] = [];
  const metrics: AudibleContractMetrics = {
    boundaryOvershootMs: 0,
    boundaryUndershootMs: 0,
    heardStartErrorMs: null,
    leadingSilenceMs: 0,
    wrongPrefixLeakageMs: 0,
  };
  let actualIndex = 0;
  if (analysis.segments[0]?.kind === "silence" && contract.expectations[0]?.kind !== "silence") {
    metrics.leadingSilenceMs = analysis.segments[0].durationMs;
    if (metrics.leadingSilenceMs > options.maxLeadingSilenceMs) {
      failures.push(
        failure(
          "leading_silence",
          `Leading silence was ${round(metrics.leadingSilenceMs)} ms; maximum is ${options.maxLeadingSilenceMs} ms.`,
          0,
          null,
        ),
      );
    }
    actualIndex += 1;
  }
  contract.expectations.forEach((expectation, expectationIndex) => {
    actualIndex = skipTransitions(
      analysis.segments,
      actualIndex,
      options.maxTransitionMs,
      failures,
      expectationIndex,
    );
    const actual = analysis.segments[actualIndex];
    if (expectation.kind === "silence") {
      compareSilence(expectation, actual, expectationIndex, actualIndex, failures);
    } else {
      compareContent(
        expectation,
        actual,
        expectationIndex,
        actualIndex,
        comparisonOptions,
        failures,
        metrics,
      );
    }
    if (actual) {
      matches.push({ actualSegmentIndex: actualIndex, expectationIndex });
      actualIndex += 1;
    }
  });
  actualIndex = skipTransitions(
    analysis.segments,
    actualIndex,
    options.maxTransitionMs,
    failures,
    null,
  );
  for (; actualIndex < analysis.segments.length; actualIndex += 1) {
    const segment = analysis.segments[actualIndex];
    if (!segment || (options.allowTrailingSilence && segment.kind === "silence")) continue;
    failures.push(
      failure(
        segment.kind === "unknown" ? "unknown_audio" : "unexpected_audio",
        `Unexpected ${segment.kind} from capture ${round(segment.captureStartMs)}-${round(segment.captureEndMs)} ms.`,
        actualIndex,
        null,
      ),
    );
  }
  if (!options.allowClipping && analysis.metrics.clippedSampleCount) {
    failures.push(
      failure(
        "clipping",
        `${analysis.metrics.clippedSampleCount} captured samples were at or above the clipping threshold.`,
        null,
        null,
      ),
    );
  }
  const diagnosis = diagnose(failures, contract.expectations, analysis);
  return { diagnosis, failures, matches, metrics, pass: failures.length === 0 };
}

function compareSilence(
  expected: AudibleSilenceExpectation,
  actual: AudioSegment | undefined,
  expectationIndex: number,
  actualIndex: number,
  failures: AudibleContractFailure[],
): void {
  if (!actual || actual.kind !== "silence") {
    failures.push(
      failure(
        "missing_silence",
        `Expected ${expected.minMs}-${expected.maxMs} ms of silence, heard ${actual?.kind ?? "nothing"}.`,
        actual ? actualIndex : null,
        expectationIndex,
      ),
    );
    return;
  }
  if (actual.durationMs < expected.minMs || actual.durationMs > expected.maxMs) {
    failures.push(
      failure(
        "duration",
        `Silence was ${round(actual.durationMs)} ms; expected ${expected.minMs}-${expected.maxMs} ms.`,
        actualIndex,
        expectationIndex,
      ),
    );
  }
}

function compareContent(
  expected: AudibleSegmentExpectation,
  actual: AudioSegment | undefined,
  expectationIndex: number,
  actualIndex: number,
  options: Required<AudibleContractOptions>,
  failures: AudibleContractFailure[],
  metrics: AudibleContractMetrics,
): void {
  if (!actual || actual.kind !== "content") {
    const code = actual?.kind === "unknown" ? "unknown_audio" : "missing_content";
    failures.push(
      failure(
        code,
        `Expected ${expected.source} ${expected.startMs}-${expected.endMs} ms, heard ${actual?.kind ?? "nothing"}.`,
        actual ? actualIndex : null,
        expectationIndex,
      ),
    );
    return;
  }
  if (actual.source !== expected.source) {
    failures.push(
      failure(
        "source",
        `Expected source ${expected.source}, confidently identified ${actual.source ?? "none"}.`,
        actualIndex,
        expectationIndex,
      ),
    );
  }
  compareContentPositions(
    expected,
    actual,
    expectationIndex,
    actualIndex,
    options,
    failures,
    metrics,
  );
  const expectedDuration = expected.endMs - expected.startMs;
  const minimum =
    expected.minDurationMs ?? Math.max(0, expectedDuration - options.durationToleranceMs);
  const maximum = expected.maxDurationMs ?? expectedDuration + options.durationToleranceMs;
  if (actual.durationMs < minimum || actual.durationMs > maximum) {
    failures.push(
      failure(
        "duration",
        `Content duration was ${round(actual.durationMs)} ms; expected ${round(minimum)}-${round(maximum)} ms.`,
        actualIndex,
        expectationIndex,
      ),
    );
  }
  if (actual.overlap && !options.allowOverlap) {
    failures.push(
      failure(
        "overlap",
        "A second strong reference position was present.",
        actualIndex,
        expectationIndex,
      ),
    );
  }
}

function compareContentPositions(
  expected: AudibleSegmentExpectation,
  actual: AudioSegment,
  expectationIndex: number,
  actualIndex: number,
  options: Required<AudibleContractOptions>,
  failures: AudibleContractFailure[],
  metrics: AudibleContractMetrics,
): void {
  const startError = (actual.sourceStartMs ?? Number.NaN) - expected.startMs;
  const heardSourceDuration =
    (actual.sourceEndMs ?? Number.NaN) - (actual.sourceStartMs ?? Number.NaN);
  const expectedSourceDuration = expected.endMs - expected.startMs;
  const endError = heardSourceDuration - expectedSourceDuration;
  const startTolerance = expected.startPositionToleranceMs ?? options.sourcePositionToleranceMs;
  const endTolerance = expected.endPositionToleranceMs ?? options.sourcePositionToleranceMs;
  if (metrics.heardStartErrorMs === null && Number.isFinite(startError)) {
    metrics.heardStartErrorMs = Math.abs(startError);
  }
  metrics.wrongPrefixLeakageMs = Math.max(metrics.wrongPrefixLeakageMs, -startError, 0);
  metrics.boundaryOvershootMs = Math.max(metrics.boundaryOvershootMs, endError, 0);
  metrics.boundaryUndershootMs = Math.max(metrics.boundaryUndershootMs, -endError, 0);
  if (!Number.isFinite(startError) || Math.abs(startError) > startTolerance) {
    failures.push(
      failure(
        "start_position",
        `Heard source start ${round(actual.sourceStartMs)} ms; expected ${expected.startMs} ms.`,
        actualIndex,
        expectationIndex,
      ),
    );
  }
  if (endError > endTolerance) {
    failures.push(
      failure(
        "boundary_overshoot",
        `Decoded source span was ${round(heardSourceDuration)} ms; expected ${round(expectedSourceDuration)} ms.`,
        actualIndex,
        expectationIndex,
      ),
    );
  } else if (!Number.isFinite(endError) || endError < -endTolerance) {
    failures.push(
      failure(
        "boundary_undershoot",
        `Decoded source span was ${round(heardSourceDuration)} ms; expected ${round(expectedSourceDuration)} ms.`,
        actualIndex,
        expectationIndex,
      ),
    );
  }
}

function skipTransitions(
  segments: readonly AudioSegment[],
  startIndex: number,
  maxTransitionMs: number,
  failures: AudibleContractFailure[],
  expectationIndex: number | null,
): number {
  let index = startIndex;
  while (segments[index]?.kind === "transition") {
    const transition = segments[index];
    if (!transition) break;
    if (transition.durationMs > maxTransitionMs) {
      failures.push(
        failure(
          "unknown_audio",
          `Unidentified transition lasted ${round(transition.durationMs)} ms.`,
          index,
          expectationIndex,
        ),
      );
    }
    index += 1;
  }
  return index;
}

function diagnose(
  failures: readonly AudibleContractFailure[],
  expectations: readonly AudibleExpectation[],
  analysis: AudioOracleAnalysis,
): string {
  if (!failures.length) return "Captured audio satisfied the ordered audible contract.";
  const expected = expectations[failures[0]?.expectationIndex ?? -1];
  const requested =
    expected?.kind === "segment"
      ? `Requested ${expected.source} ${expected.startMs}-${expected.endMs} ms.\n`
      : "";
  const confidence = analysis.trace.find((sample) => sample.classification === "content");
  const heard = confidence
    ? `First confident output matched ${confidence.source} at ${round(confidence.sourceTimeMs)} ms with ${confidence.confidence.toFixed(3)} confidence.\n`
    : "No source position was confidently identified.\n";
  return `${requested}${heard}${failures[0]?.message ?? "Audible contract failed."}`;
}

function failure(
  code: AudibleContractFailureCode,
  message: string,
  actualSegmentIndex: number | null,
  expectationIndex: number | null,
): AudibleContractFailure {
  return { actualSegmentIndex, code, expectationIndex, message };
}

function round(value: number | null | undefined): string {
  return Number.isFinite(value) ? String(Math.round(value! * 10) / 10) : "unknown";
}
