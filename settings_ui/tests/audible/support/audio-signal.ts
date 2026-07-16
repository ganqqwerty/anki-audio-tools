import type { AudioSamples, MonoAudio } from "../fixtures/audio-oracle-types.js";

export function asFloat32(samples: AudioSamples): Float32Array {
  return samples instanceof Float32Array ? samples : Float32Array.from(samples);
}

export function audioDurationMs(audio: MonoAudio): number {
  return (audio.samples.length / audio.sampleRate) * 1_000;
}

export function samplesForMs(sampleRate: number, milliseconds: number): number {
  return Math.max(1, Math.round((sampleRate * milliseconds) / 1_000));
}

export function rms(samples: Float32Array, start = 0, end = samples.length): number {
  const boundedStart = Math.max(0, Math.min(samples.length, start));
  const boundedEnd = Math.max(boundedStart, Math.min(samples.length, end));
  if (boundedStart === boundedEnd) return 0;
  let squareSum = 0;
  for (let index = boundedStart; index < boundedEnd; index += 1) {
    const value = samples[index] ?? 0;
    squareSum += value * value;
  }
  return Math.sqrt(squareSum / (boundedEnd - boundedStart));
}

export function percentile(values: readonly number[], percentileValue: number): number {
  if (!values.length) return 0;
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(
    sorted.length - 1,
    Math.max(0, Math.ceil((percentileValue / 100) * sorted.length) - 1),
  );
  return sorted[index] ?? 0;
}

export function fingerprint(
  samples: Float32Array,
  start: number,
  length: number,
  points: number,
): Float32Array {
  const result = new Float32Array(points);
  const block = Math.max(1, Math.floor(length / points / 3));
  for (let point = 0; point < points; point += 1) {
    const center = start + Math.floor(((point + 0.5) * length) / points);
    let total = 0;
    let count = 0;
    for (let offset = -block; offset <= block; offset += 1) {
      const index = center + offset;
      if (index >= start && index < start + length && index < samples.length) {
        total += samples[index] ?? 0;
        count += 1;
      }
    }
    result[point] = count ? total / count : 0;
  }
  normalizeInPlace(result);
  return result;
}

export function normalizedCorrelation(left: Float32Array, right: Float32Array): number {
  const length = Math.min(left.length, right.length);
  if (!length) return 0;
  let leftMean = 0;
  let rightMean = 0;
  for (let index = 0; index < length; index += 1) {
    leftMean += left[index] ?? 0;
    rightMean += right[index] ?? 0;
  }
  leftMean /= length;
  rightMean /= length;
  let dot = 0;
  let leftSquare = 0;
  let rightSquare = 0;
  for (let index = 0; index < length; index += 1) {
    const leftValue = (left[index] ?? 0) - leftMean;
    const rightValue = (right[index] ?? 0) - rightMean;
    dot += leftValue * rightValue;
    leftSquare += leftValue * leftValue;
    rightSquare += rightValue * rightValue;
  }
  const denominator = Math.sqrt(leftSquare * rightSquare);
  return denominator > 1e-12 ? Math.max(-1, Math.min(1, dot / denominator)) : 0;
}

export function windowCopy(samples: Float32Array, start: number, length: number): Float32Array {
  return samples.slice(start, start + length);
}

export function resampleLinear(audio: MonoAudio, targetSampleRate: number): Float32Array {
  const samples = asFloat32(audio.samples);
  if (audio.sampleRate === targetSampleRate) return samples;
  const outputLength = Math.max(
    1,
    Math.round((samples.length * targetSampleRate) / audio.sampleRate),
  );
  const output = new Float32Array(outputLength);
  const ratio = audio.sampleRate / targetSampleRate;
  for (let index = 0; index < outputLength; index += 1) {
    const sourceIndex = index * ratio;
    const lowerIndex = Math.min(samples.length - 1, Math.floor(sourceIndex));
    const upperIndex = Math.min(samples.length - 1, lowerIndex + 1);
    const fraction = sourceIndex - lowerIndex;
    output[index] =
      (samples[lowerIndex] ?? 0) * (1 - fraction) + (samples[upperIndex] ?? 0) * fraction;
  }
  return output;
}

/** Offline, zero-phase FIR band pass for isolating the addressable PRBS carrier. */
export function bandPass(
  samples: Float32Array,
  sampleRate: number,
  lowHz: number,
  highHz: number,
  tapCount = 65,
): Float32Array {
  const taps = tapCount % 2 === 0 ? tapCount + 1 : tapCount;
  const half = Math.floor(taps / 2);
  const coefficients = new Float64Array(taps);
  for (let tap = 0; tap < taps; tap += 1) {
    const offset = tap - half;
    const high = lowPassCoefficient(highHz / sampleRate, offset);
    const low = lowPassCoefficient(lowHz / sampleRate, offset);
    const window = 0.54 - 0.46 * Math.cos((2 * Math.PI * tap) / Math.max(1, taps - 1));
    coefficients[tap] = (high - low) * window;
  }
  const output = new Float32Array(samples.length);
  for (let index = 0; index < samples.length; index += 1) {
    let value = 0;
    const firstTap = Math.max(0, half - index);
    const lastTap = Math.min(taps - 1, samples.length - 1 + half - index);
    for (let tap = firstTap; tap <= lastTap; tap += 1) {
      value += (samples[index + tap - half] ?? 0) * (coefficients[tap] ?? 0);
    }
    output[index] = value;
  }
  return output;
}

export function concatenate(chunks: readonly Float32Array[]): Float32Array {
  const output = new Float32Array(chunks.reduce((length, chunk) => length + chunk.length, 0));
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.length;
  }
  return output;
}

function normalizeInPlace(values: Float32Array): void {
  let mean = 0;
  for (const value of values) mean += value;
  mean /= values.length || 1;
  let squareSum = 0;
  for (let index = 0; index < values.length; index += 1) {
    const centered = (values[index] ?? 0) - mean;
    values[index] = centered;
    squareSum += centered * centered;
  }
  const scale = Math.sqrt(squareSum) || 1;
  for (let index = 0; index < values.length; index += 1)
    values[index] = (values[index] ?? 0) / scale;
}

function lowPassCoefficient(normalizedCutoff: number, offset: number): number {
  if (offset === 0) return 2 * normalizedCutoff;
  return Math.sin(2 * Math.PI * normalizedCutoff * offset) / (Math.PI * offset);
}
