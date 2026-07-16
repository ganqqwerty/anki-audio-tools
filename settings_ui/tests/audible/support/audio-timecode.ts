import type { AcousticReference } from "../fixtures/audio-oracle-types.js";
import { resampleLinear } from "./audio-signal.js";

export interface AcousticCarrierConfig {
  algorithm: "prbs31-x31-x28-1-bpsk-raised-cosine-v1";
  bandHz: [number, number];
  centerFrequencyHz: number;
  sampleRateHz: number;
  samplesPerChip: number;
  seed: number;
}

export interface AcousticTimecodeConfig {
  banksHz: number[][];
  carrier: AcousticCarrierConfig | null;
  frameCount: number;
  frameDurationMs: number;
  placeValues: number[];
}

export interface CoarseTimecodeMatch {
  confidence: number;
  frameIndex: number;
  referenceIndex: number;
}

export function timecodeConfig(reference: AcousticReference): AcousticTimecodeConfig | null {
  const metadata = reference.metadata;
  if (!metadata) return null;
  const manifest = record(metadata.manifest) ?? metadata;
  const timecode = record(manifest.addressableTimecode) ?? record(metadata.addressableTimecode);
  if (!timecode) return null;
  const banksHz = numberMatrix(timecode.banksHz);
  const digitOrder = record(timecode.digitOrder);
  const placeValues = numberArray(digitOrder?.placeValues);
  const frameDurationMs = finiteNumber(timecode.frameDurationMs);
  const frameCount = finiteNumber(timecode.frameCount);
  if (
    !banksHz?.length ||
    banksHz.length !== placeValues?.length ||
    !frameDurationMs ||
    !frameCount
  ) {
    return null;
  }
  return {
    banksHz,
    carrier: carrierConfig(timecode, banksHz),
    frameCount,
    frameDurationMs,
    placeValues,
  };
}

/**
 * Produces the carrier-only reference used for sub-frame alignment. The coarse
 * tones intentionally do not enter this template: their only job is to bound
 * the search to one 50 ms frame.
 */
export function generateCarrierReference(
  config: AcousticCarrierConfig,
  targetSampleRate: number,
  targetSampleCount: number,
): Float32Array {
  const sourceSampleCount = Math.max(
    1,
    Math.ceil((targetSampleCount * config.sampleRateHz) / targetSampleRate) + 2,
  );
  const chipCount = Math.ceil(sourceSampleCount / config.samplesPerChip) + 1;
  const signs = prbs31Signs(config.seed, chipCount);
  const samples = new Float32Array(sourceSampleCount);
  for (let index = 0; index < samples.length; index += 1) {
    const chip = Math.floor(index / config.samplesPerChip);
    const offset = index % config.samplesPerChip;
    const progress = offset / Math.max(1, config.samplesPerChip - 1);
    const weight = Math.sin((Math.PI * progress) / 2) ** 2;
    const modulation = (signs[chip] ?? -1) * (1 - weight) + (signs[chip + 1] ?? -1) * weight;
    samples[index] =
      modulation * Math.sin((2 * Math.PI * config.centerFrequencyHz * index) / config.sampleRateHz);
  }
  return resampleLinear({ sampleRate: config.sampleRateHz, samples }, targetSampleRate).slice(
    0,
    targetSampleCount,
  );
}

export function decodeCoarseTimecode(
  samples: Float32Array,
  sampleRate: number,
  config: AcousticTimecodeConfig,
  referenceIndex: number,
): CoarseTimecodeMatch | null {
  const targetLength = Math.min(samples.length, Math.round(sampleRate * 0.03));
  if (targetLength < 32) return null;
  const start = Math.floor((samples.length - targetLength) / 2);
  const digits: number[] = [];
  const bankConfidences: number[] = [];
  for (const bank of config.banksHz) {
    const powers = bank.map((frequency) =>
      goertzelPower(samples, start, targetLength, frequency, sampleRate),
    );
    const ranked = powers
      .map((power, digit) => ({ digit, power }))
      .sort((left, right) => right.power - left.power);
    const winner = ranked[0];
    if (!winner || winner.power <= 1e-12) return null;
    const runnerPower = ranked[1]?.power ?? 0;
    digits.push(winner.digit);
    bankConfidences.push(Math.max(0, Math.min(1, 1 - runnerPower / winner.power)));
  }
  const frameIndex = digits.reduce(
    (value, digit, index) => value + digit * (config.placeValues[index] ?? 0),
    0,
  );
  if (frameIndex < 0 || frameIndex >= config.frameCount) return null;
  return {
    confidence: Math.min(...bankConfidences),
    frameIndex,
    referenceIndex,
  };
}

function goertzelPower(
  samples: Float32Array,
  start: number,
  length: number,
  frequency: number,
  sampleRate: number,
): number {
  const coefficient = 2 * Math.cos((2 * Math.PI * frequency) / sampleRate);
  let previous = 0;
  let previousPrevious = 0;
  for (let offset = 0; offset < length; offset += 1) {
    const hann = 0.5 - 0.5 * Math.cos((2 * Math.PI * offset) / Math.max(1, length - 1));
    const current =
      (samples[start + offset] ?? 0) * hann + coefficient * previous - previousPrevious;
    previousPrevious = previous;
    previous = current;
  }
  return Math.max(
    0,
    previous * previous +
      previousPrevious * previousPrevious -
      coefficient * previous * previousPrevious,
  );
}

function carrierConfig(
  timecode: Record<string, unknown>,
  banksHz: readonly (readonly number[])[],
): AcousticCarrierConfig | null {
  const carrier = record(timecode.carrier);
  const coarse = record(timecode.coarse);
  const algorithm = carrier?.algorithm;
  const centerFrequencyHz = finiteNumber(carrier?.centerFrequencyHz);
  const sampleRateHz = finiteNumber(timecode.sampleRateHz);
  const samplesPerChip = finiteNumber(carrier?.samplesPerChip);
  const seed = finiteNumber(timecode.seed);
  const carrierRms = finiteNumber(carrier?.rmsLinear);
  const coarseRms = finiteNumber(coarse?.frameRmsLinear);
  const nominalBand = numberArray(carrier?.nominalBandHz);
  if (
    algorithm !== "prbs31-x31-x28-1-bpsk-raised-cosine-v1" ||
    !centerFrequencyHz ||
    !sampleRateHz ||
    !Number.isInteger(samplesPerChip) ||
    !samplesPerChip ||
    !Number.isInteger(seed) ||
    !seed ||
    !carrierRms ||
    !coarseRms ||
    nominalBand?.length !== 2
  ) {
    return null;
  }
  return {
    algorithm,
    bandHz: [Math.max(nominalBand[0] ?? 0, Math.max(...banksHz.flat()) + 300), nominalBand[1] ?? 0],
    centerFrequencyHz,
    sampleRateHz,
    samplesPerChip,
    seed,
  };
}

function prbs31Signs(seed: number, count: number): Int8Array {
  let state = seed & 0x7fffffff;
  const output = new Int8Array(count);
  for (let index = 0; index < output.length; index += 1) {
    output[index] = state & (1 << 30) ? 1 : -1;
    const feedback = ((state >>> 30) ^ (state >>> 27)) & 1;
    state = ((state << 1) & 0x7fffffff) | feedback;
  }
  return output;
}

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberArray(value: unknown): number[] | null {
  if (!Array.isArray(value) || value.some((entry) => finiteNumber(entry) === null)) return null;
  return value as number[];
}

function numberMatrix(value: unknown): number[][] | null {
  if (!Array.isArray(value)) return null;
  const arrays = value.map(numberArray);
  return arrays.every((array) => array?.length) ? (arrays as number[][]) : null;
}
