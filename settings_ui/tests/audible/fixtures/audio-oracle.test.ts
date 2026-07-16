import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { evaluateAudibleContract, type AudibleExpectation } from "./audible-contract.js";
import {
  analyzeAudioCapture,
  decodeReferenceFromManifest,
  writeAudibleFailureArtifacts,
  type AcousticReference,
} from "./audio-oracle.js";
import { decodeCoarseTimecode, timecodeConfig } from "../support/audio-timecode.js";

const AUDIO_ROOT = resolve("../e2e/fixtures/audio");
const MANIFEST = join(AUDIO_ROOT, "addressable-timecode.manifest.json");
const SOURCE = "addressable-timecode.wav";
const SAMPLE_RATE = 48_000;
let reference: AcousticReference;
const temporaryDirectories: string[] = [];

beforeAll(async () => {
  reference = await decodeReferenceFromManifest(MANIFEST, {
    fileName: SOURCE,
    source: SOURCE,
  });
});

afterAll(async () => {
  await Promise.all(
    temporaryDirectories.map((directory) => rm(directory, { force: true, recursive: true })),
  );
});

describe("acoustic playback oracle", { timeout: 15_000 }, () => {
  it("identifies a cropped source interval after capture delay and gain change", () => {
    const delayMs = 100;
    const capture = concatenate(silence(delayMs), scaledSlice(reference, 300, 900, 0.35));
    const analysis = analyzeAudioCapture({ capture: pcm(capture), references: [reference] });
    const verdict = evaluateAudibleContract(
      analysis,
      [{ kind: "segment", source: SOURCE, startMs: 300, endMs: 900 }],
      { maxLeadingSilenceMs: 130, sourcePositionToleranceMs: 30 },
    );

    expect(analysis.metrics.overlapFrameCount).toBeLessThanOrEqual(2);
    expect(verdict, verdict.diagnosis).toMatchObject({ pass: true });
    expect(analysis.metrics.firstAudibleMs).toBeGreaterThanOrEqual(80);
    expect(analysis.metrics.firstConfidentMs).toBeLessThanOrEqual(120);
    expect(medianSourceOffset(analysis.trace, delayMs)).toBeCloseTo(300, -1);
  });

  it("uses timecode and sample-level refinement for a non-millisecond phase offset", () => {
    const startSample = 2_000 * (SAMPLE_RATE / 1_000) + 64;
    const capture = Float32Array.from(reference.samples).slice(
      startSample,
      startSample + Math.round(SAMPLE_RATE * 0.8),
    );
    const analysis = analyzeAudioCapture({ capture: pcm(capture), references: [reference] });
    const first = analysis.trace.find((sample) => sample.classification === "content");
    const verdict = evaluateAudibleContract(
      analysis,
      [{ kind: "segment", source: SOURCE, startMs: 2_000, endMs: 2_800 }],
      { sourcePositionToleranceMs: 30 },
    );

    expect(first?.sourceTimeMs).toBeCloseTo(2_001.333, 1);
    expect(first?.confidence).toBeGreaterThan(0.8);
    expect(verdict, verdict.diagnosis).toMatchObject({ pass: true });
    expect(analysis.segments[0]).toMatchObject({
      kind: "content",
      source: SOURCE,
    });
  });

  it("distinguishes an expected silent dropout from unknown energetic audio", () => {
    const capture = concatenate(
      slice(reference, 1_000, 1_300),
      silence(100),
      slice(reference, 1_400, 1_700),
    );
    const contract: AudibleExpectation[] = [
      { kind: "segment", source: SOURCE, startMs: 1_000, endMs: 1_300 },
      { expectedMs: 100, kind: "silence", minMs: 80, maxMs: 120 },
      { kind: "segment", source: SOURCE, startMs: 1_400, endMs: 1_700 },
    ];
    const analysis = analyzeAudioCapture({ capture: pcm(capture), references: [reference] });
    const verdict = evaluateAudibleContract(analysis, contract, {
      sourcePositionToleranceMs: 30,
    });

    expect(verdict, verdict.diagnosis).toMatchObject({ pass: true });
    expect(analysis.metrics.dropoutCount).toBe(1);
    expect(analysis.segments.some((segment) => segment.kind === "silence")).toBe(true);

    const foreign = analyzeAudioCapture({
      capture: pcm(deterministicNoise(500, 0x1badf00d)),
      references: [reference],
    });
    expect(foreign.segments.some((segment) => segment.kind === "unknown")).toBe(true);
    expect(foreign.segments.some((segment) => segment.kind === "silence")).toBe(false);
    expect(
      evaluateAudibleContract(foreign, [
        { kind: "segment", source: SOURCE, startMs: 0, endMs: 500 },
      ]).failures,
    ).toEqual(expect.arrayContaining([expect.objectContaining({ code: "unknown_audio" })]));
  });

  it("uses the coarse code only to localize and rejects carrier-free coded tones", () => {
    const startMs = 2_000;
    const carrierFree = coarseToneOnly(startMs, 500);
    const config = timecodeConfig(reference);
    if (!config) throw new Error("addressable fixture metadata is missing");
    const coarse = decodeCoarseTimecode(
      carrierFree.subarray(0, Math.round(SAMPLE_RATE * 0.04)),
      SAMPLE_RATE,
      config,
      0,
    );
    const analysis = analyzeAudioCapture({ capture: pcm(carrierFree), references: [reference] });
    const verdict = evaluateAudibleContract(analysis, [
      { kind: "segment", source: SOURCE, startMs, endMs: startMs + 500 },
    ]);

    expect(coarse?.confidence).toBeGreaterThan(0.9);
    expect(analysis.trace.some((sample) => sample.classification === "content")).toBe(false);
    expect(analysis.trace.every((sample) => sample.sourceTimeMs === null)).toBe(true);
    expect(analysis.segments.some((segment) => segment.kind === "unknown")).toBe(true);
    expect(verdict.pass).toBe(false);
    expect(verdict.failures).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: "unknown_audio" })]),
    );
  });

  it("reports a duplicated source range and preserves each ordered pass", () => {
    const capture = concatenate(slice(reference, 2_000, 2_400), slice(reference, 2_200, 2_600));
    const analysis = analyzeAudioCapture({ capture: pcm(capture), references: [reference] });
    const verdict = evaluateAudibleContract(
      analysis,
      [
        { kind: "segment", source: SOURCE, startMs: 2_000, endMs: 2_400 },
        { kind: "segment", source: SOURCE, startMs: 2_200, endMs: 2_600 },
      ],
      { sourcePositionToleranceMs: 30 },
    );

    expect(analysis.metrics.duplicateEventCount).toBeGreaterThanOrEqual(1);
    expect(analysis.metrics.sourceReversalCount).toBeGreaterThanOrEqual(1);
    expect(verdict, verdict.diagnosis).toMatchObject({ pass: true });
  });

  it("detects simultaneous source positions and clipped samples", () => {
    const first = slice(reference, 3_000, 3_600);
    const second = slice(reference, 5_000, 5_600);
    const mixed = new Float32Array(first.length);
    for (let index = 0; index < mixed.length; index += 1) {
      mixed[index] = (first[index] ?? 0) * 0.65 + (second[index] ?? 0) * 0.65;
    }
    const overlap = analyzeAudioCapture({ capture: pcm(mixed), references: [reference] });
    expect(overlap.metrics.overlapFrameCount).toBeGreaterThan(0);
    expect(overlap.trace.some((sample) => sample.secondaryConfidence > 0.7)).toBe(true);

    const clipped = scaledSlice(reference, 4_000, 4_300, 5, true);
    const clippingAnalysis = analyzeAudioCapture({
      capture: pcm(clipped),
      references: [reference],
    });
    expect(clippingAnalysis.metrics.clippedSampleCount).toBeGreaterThan(0);
    const verdict = evaluateAudibleContract(clippingAnalysis, [
      { kind: "segment", source: SOURCE, startMs: 4_000, endMs: 4_300 },
    ]);
    expect(verdict.failures.some((failure) => failure.code === "clipping")).toBe(true);
  });

  for (const fileName of [
    "addressable-timecode.mp3",
    "addressable-timecode.ogg",
    "addressable-timecode.m4a",
  ]) {
    it(`tracks a crop decoded from ${fileName}`, async () => {
      const compressed = await decodeReferenceFromManifest(MANIFEST, { fileName });
      const analysis = analyzeAudioCapture({
        capture: pcm(slice(compressed, 6_000, 6_500)),
        options: { minConfidence: 0.25 },
        references: [reference],
      });
      const confident = analysis.trace.filter((sample) => sample.classification === "content");
      expect(confident.length).toBeGreaterThan(35);
      expect(median(confident.map((sample) => sample.sourceTimeMs ?? 0))).toBeCloseTo(6_250, -1);
    });
  }

  it("writes listenable, structured, and visual failure evidence", async () => {
    const capture = pcm(slice(reference, 0, 250));
    const analysis = analyzeAudioCapture({ capture, references: [reference] });
    const contract: AudibleExpectation[] = [
      { kind: "segment", source: SOURCE, startMs: 400, endMs: 650 },
    ];
    const verdict = evaluateAudibleContract(analysis, contract);
    const directory = await mkdtemp(join(tmpdir(), "audible-oracle-"));
    temporaryDirectories.push(directory);
    const artifacts = await writeAudibleFailureArtifacts({
      analysis,
      capture,
      contract,
      directory,
      metadata: { captureTier: "unit" },
      references: [reference],
      verdict,
    });

    expect(verdict.pass).toBe(false);
    expect((await readFile(artifacts.files.capturedOutput)).toString("ascii", 0, 4)).toBe("RIFF");
    expect((await readFile(artifacts.files.timeline)).subarray(1, 4).toString("ascii")).toBe("PNG");
    expect((await readFile(artifacts.files.spectrogram)).subarray(1, 4).toString("ascii")).toBe(
      "PNG",
    );
    expect(JSON.parse(await readFile(artifacts.files.metrics, "utf8"))).toMatchObject({
      metadata: { captureTier: "unit" },
      verdict: { pass: false },
    });
    expect(await readFile(artifacts.files.diagnosis, "utf8")).toContain("Requested");
  });
});

function pcm(samples: Float32Array): { sampleRate: number; samples: Float32Array } {
  return { sampleRate: SAMPLE_RATE, samples };
}

function silence(durationMs: number): Float32Array {
  return new Float32Array(Math.round((durationMs * SAMPLE_RATE) / 1_000));
}

function slice(audio: AcousticReference, startMs: number, endMs: number): Float32Array {
  const start = Math.round((startMs * audio.sampleRate) / 1_000);
  const end = Math.round((endMs * audio.sampleRate) / 1_000);
  return Float32Array.from(audio.samples).slice(start, end);
}

function scaledSlice(
  audio: AcousticReference,
  startMs: number,
  endMs: number,
  gain: number,
  clamp = false,
): Float32Array {
  return slice(audio, startMs, endMs).map((sample) => {
    const value = sample * gain;
    return clamp ? Math.max(-1, Math.min(1, value)) : value;
  });
}

function deterministicNoise(durationMs: number, seed: number): Float32Array {
  const samples = silence(durationMs);
  let state = seed >>> 0;
  for (let index = 0; index < samples.length; index += 1) {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    samples[index] = ((state >>> 0) / 0xffffffff - 0.5) * 0.7;
  }
  return samples;
}

function coarseToneOnly(sourceStartMs: number, durationMs: number): Float32Array {
  const frameDurationMs = 50;
  const banks = [
    [600, 700, 800, 900, 1000, 1100, 1200, 1300],
    [1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400],
    [2900, 3000, 3100, 3200, 3300, 3400, 3500, 3600],
    [4100, 4200, 4300, 4400, 4500, 4600, 4700, 4800],
  ] as const;
  const places = [512, 64, 8, 1] as const;
  const samples = silence(durationMs);
  for (let index = 0; index < samples.length; index += 1) {
    const sourceTimeMs = sourceStartMs + (index / SAMPLE_RATE) * 1_000;
    const frame = Math.floor(sourceTimeMs / frameDurationMs);
    let value = 0;
    for (let bankIndex = 0; bankIndex < banks.length; bankIndex += 1) {
      const digit = Math.floor(frame / (places[bankIndex] ?? 1)) % 8;
      const frequency = banks[bankIndex]?.[digit] ?? 0;
      value += Math.sin((2 * Math.PI * frequency * sourceTimeMs) / 1_000) * 0.12;
    }
    samples[index] = value;
  }
  return samples;
}

function concatenate(...chunks: Float32Array[]): Float32Array {
  const result = new Float32Array(chunks.reduce((length, chunk) => length + chunk.length, 0));
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.length;
  }
  return result;
}

function medianSourceOffset(
  trace: ReturnType<typeof analyzeAudioCapture>["trace"],
  delayMs: number,
): number {
  return median(
    trace
      .filter((sample) => sample.sourceTimeMs !== null)
      .map((sample) => sample.sourceTimeMs! - Math.max(0, sample.captureTimeMs - delayMs)),
  );
}

function median(values: readonly number[]): number {
  const sorted = [...values].sort((left, right) => left - right);
  return sorted[Math.floor(sorted.length / 2)] ?? Number.NaN;
}
