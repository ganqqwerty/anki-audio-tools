import type { AcousticReference } from "../fixtures/audio-oracle-types.js";
import type { ResolvedOracleOptions } from "./audio-match-engine.js";
import {
  decodeCoarseTimecode,
  generateCarrierReference,
  timecodeConfig,
  type AcousticTimecodeConfig,
} from "./audio-timecode.js";
import { bandPass, fingerprint, normalizedCorrelation, samplesForMs } from "./audio-signal.js";

const carrierReferenceCache = new WeakMap<AcousticReference, Map<string, Float32Array>>();

export interface AudioWindowMatch {
  confidence: number;
  rawConfidence: number;
  referenceIndex: number;
  startSample: number;
}

export interface AudioWindowMatchResult {
  best?: AudioWindowMatch;
  residualRatio: number;
  secondary?: AudioWindowMatch;
}

export interface PreparedAudioWindowMatcher {
  candidates: CoarseCandidate[];
  matchingReferenceSamples: Array<Float32Array | null>;
  options: ResolvedOracleOptions;
  referenceSamples: readonly Float32Array[];
  sampleRate: number;
  timecodes: Array<AcousticTimecodeConfig | null>;
  windowSamples: number;
}

interface CoarseCandidate {
  fingerprint: Float32Array;
  referenceIndex: number;
  startSample: number;
}

export function prepareAudioWindowMatcher(input: {
  options: ResolvedOracleOptions;
  references: readonly AcousticReference[];
  referenceSamples: readonly Float32Array[];
  sampleRate: number;
  windowSamples: number;
}): PreparedAudioWindowMatcher {
  const hopSamples = samplesForMs(input.sampleRate, input.options.coarseHopMs);
  const candidates: CoarseCandidate[] = [];
  const timecodes = input.references.map(timecodeConfig);
  const matchingReferenceSamples = input.referenceSamples.map((samples, referenceIndex) => {
    const timecode = timecodes[referenceIndex];
    const sourceReference = input.references[referenceIndex];
    if (!timecode) return samples;
    if (!timecode.carrier || !sourceReference) return null;
    const cacheKey = `${input.sampleRate}:${samples.length}`;
    const cached = carrierReferenceCache.get(sourceReference)?.get(cacheKey);
    if (cached) return cached;
    const generated = bandPass(
      generateCarrierReference(timecode.carrier, input.sampleRate, samples.length),
      input.sampleRate,
      ...timecode.carrier.bandHz,
    );
    const entries = carrierReferenceCache.get(sourceReference) ?? new Map<string, Float32Array>();
    entries.set(cacheKey, generated);
    carrierReferenceCache.set(sourceReference, entries);
    return generated;
  });
  input.referenceSamples.forEach((_samples, referenceIndex) => {
    const matchingSamples = matchingReferenceSamples[referenceIndex];
    if (!matchingSamples) return;
    const lastStart = Math.max(0, matchingSamples.length - input.windowSamples);
    for (let start = 0; start <= lastStart; start += hopSamples) {
      candidates.push(
        candidate(matchingSamples, referenceIndex, start, input.windowSamples, input.options),
      );
    }
    if (lastStart % hopSamples !== 0) {
      candidates.push(
        candidate(matchingSamples, referenceIndex, lastStart, input.windowSamples, input.options),
      );
    }
  });
  return {
    candidates,
    matchingReferenceSamples,
    options: input.options,
    referenceSamples: input.referenceSamples,
    sampleRate: input.sampleRate,
    timecodes,
    windowSamples: input.windowSamples,
  };
}

export function matchAudioWindow(
  captured: Float32Array,
  matcher: PreparedAudioWindowMatcher,
): AudioWindowMatchResult {
  const matchingCapturedSamples = matcher.timecodes.map((config) =>
    config?.carrier ? bandPass(captured, matcher.sampleRate, ...config.carrier.bandHz) : captured,
  );
  const captureFingerprints = matchingCapturedSamples.map((samples) =>
    fingerprint(samples, 0, samples.length, matcher.options.fingerprintPoints),
  );
  const decoded = matcher.timecodes.flatMap((config, referenceIndex) => {
    if (!config) return [];
    const match = decodeCoarseTimecode(captured, matcher.sampleRate, config, referenceIndex);
    return match ? [{ config, match }] : [];
  });
  const localMatches = decoded.flatMap(({ config, match }) => {
    const reference = matcher.matchingReferenceSamples[match.referenceIndex];
    const matchingCaptured = matchingCapturedSamples[match.referenceIndex];
    const captureFingerprint = captureFingerprints[match.referenceIndex];
    if (!reference || !matchingCaptured || !captureFingerprint) return [];
    const frameStart = Math.round(
      (match.frameIndex * config.frameDurationMs * matcher.sampleRate) / 1_000,
    );
    const frameEnd = Math.round(frameStart + (config.frameDurationMs * matcher.sampleRate) / 1_000);
    const local = bestInRange(
      matchingCaptured,
      captureFingerprint,
      reference,
      match.referenceIndex,
      Math.max(0, frameStart - captured.length),
      Math.min(reference.length - captured.length, frameEnd),
      matcher,
    );
    return local ? [local] : [];
  });
  const genericMatches = genericPeaks(matchingCapturedSamples, captureFingerprints, matcher);
  const best = localMatches.length
    ? [...localMatches].sort((left, right) => right.confidence - left.confidence)[0]
    : genericMatches[0];
  if (!best) return { residualRatio: 1 };
  const secondary = [...localMatches, ...genericMatches]
    .filter(
      (candidateMatch) =>
        candidateMatch !== best &&
        (candidateMatch.referenceIndex !== best.referenceIndex ||
          Math.abs(candidateMatch.startSample - best.startSample) >=
            samplesForMs(matcher.sampleRate, matcher.options.secondaryExclusionMs)),
    )
    .sort((left, right) => right.rawConfidence - left.rawConfidence)[0];
  const reference = matcher.referenceSamples[best.referenceIndex];
  return {
    best,
    residualRatio: reference
      ? unmatchedEnergyRatio(
          captured,
          reference.subarray(best.startSample, best.startSample + captured.length),
        )
      : 1,
    ...(secondary ? { secondary: { ...secondary, confidence: secondary.rawConfidence } } : {}),
  };
}

function genericPeaks(
  matchingCapturedSamples: readonly Float32Array[],
  captureFingerprints: readonly Float32Array[],
  matcher: PreparedAudioWindowMatcher,
): AudioWindowMatch[] {
  const coarse = matcher.candidates
    .map((candidateMatch) => ({
      ...candidateMatch,
      score: Math.max(
        0,
        normalizedCorrelation(
          captureFingerprints[candidateMatch.referenceIndex] ?? new Float32Array(),
          candidateMatch.fingerprint,
        ),
      ),
    }))
    .sort((left, right) => right.score - left.score);
  const separated: typeof coarse = [];
  const separation = samplesForMs(matcher.sampleRate, matcher.options.secondaryExclusionMs / 2);
  for (const candidateMatch of coarse) {
    if (
      separated.every(
        (selected) =>
          selected.referenceIndex !== candidateMatch.referenceIndex ||
          Math.abs(selected.startSample - candidateMatch.startSample) >= separation,
      )
    ) {
      separated.push(candidateMatch);
    }
    if (separated.length >= matcher.options.coarseCandidateCount) break;
  }
  const radius = samplesForMs(matcher.sampleRate, matcher.options.coarseHopMs);
  return separated
    .flatMap((coarseMatch) => {
      const reference = matcher.referenceSamples[coarseMatch.referenceIndex];
      const matchingReference = matcher.matchingReferenceSamples[coarseMatch.referenceIndex];
      const matchingCaptured = matchingCapturedSamples[coarseMatch.referenceIndex];
      const captureFingerprint = captureFingerprints[coarseMatch.referenceIndex];
      if (!reference || !matchingReference || !matchingCaptured || !captureFingerprint) return [];
      const fine = bestInRange(
        matchingCaptured,
        captureFingerprint,
        matchingReference,
        coarseMatch.referenceIndex,
        Math.max(0, coarseMatch.startSample - radius),
        Math.min(
          matchingReference.length - matchingCaptured.length,
          coarseMatch.startSample + radius,
        ),
        matcher,
      );
      return fine ? [fine] : [];
    })
    .sort((left, right) => right.rawConfidence - left.rawConfidence);
}

function bestInRange(
  captured: Float32Array,
  captureFingerprint: Float32Array,
  reference: Float32Array,
  referenceIndex: number,
  first: number,
  last: number,
  matcher: PreparedAudioWindowMatcher,
): AudioWindowMatch | null {
  if (last < first) return null;
  const fineHop = Math.max(
    1,
    matcher.options.fineHopSamples ?? samplesForMs(matcher.sampleRate, matcher.options.fineHopMs),
  );
  const fingerprintScores: Array<{ score: number; start: number }> = [];
  for (let start = first; start <= last; start += fineHop) {
    fingerprintScores.push({
      score: normalizedCorrelation(
        captureFingerprint,
        fingerprint(reference, start, captured.length, matcher.options.fingerprintPoints),
      ),
      start,
    });
  }
  const seeds = fingerprintScores.sort((left, right) => right.score - left.score).slice(0, 8);
  let best: AudioWindowMatch | null = null;
  const visited = new Set<number>();
  for (const seed of seeds) {
    for (
      let start = Math.max(first, seed.start - fineHop);
      start <= Math.min(last, seed.start + fineHop);
      start += 1
    ) {
      if (visited.has(start)) continue;
      visited.add(start);
      const rawConfidence = Math.max(
        0,
        normalizedCorrelation(captured, reference.subarray(start, start + captured.length)),
      );
      if (!best || rawConfidence > best.rawConfidence) {
        best = { confidence: rawConfidence, rawConfidence, referenceIndex, startSample: start };
      }
    }
  }
  return best;
}

function candidate(
  samples: Float32Array,
  referenceIndex: number,
  startSample: number,
  windowSamples: number,
  options: ResolvedOracleOptions,
): CoarseCandidate {
  return {
    fingerprint: fingerprint(samples, startSample, windowSamples, options.fingerprintPoints),
    referenceIndex,
    startSample,
  };
}

function unmatchedEnergyRatio(captured: Float32Array, matched: Float32Array): number {
  let capturedSquare = 0;
  let matchedSquare = 0;
  let dot = 0;
  const length = Math.min(captured.length, matched.length);
  for (let index = 0; index < length; index += 1) {
    const capturedSample = captured[index] ?? 0;
    const matchedSample = matched[index] ?? 0;
    capturedSquare += capturedSample * capturedSample;
    matchedSquare += matchedSample * matchedSample;
    dot += capturedSample * matchedSample;
  }
  if (capturedSquare <= 1e-12 || matchedSquare <= 1e-12) return 1;
  const gain = dot / matchedSquare;
  let residualSquare = 0;
  for (let index = 0; index < length; index += 1) {
    const residual = (captured[index] ?? 0) - (matched[index] ?? 0) * gain;
    residualSquare += residual * residual;
  }
  return Math.sqrt(residualSquare / capturedSquare);
}
