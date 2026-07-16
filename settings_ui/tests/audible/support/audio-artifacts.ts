import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import type {
  AcousticReference,
  AudioOracleAnalysis,
  MonoAudio,
} from "../fixtures/audio-oracle-types.js";
import type { AudibleContractVerdict, AudibleExpectation } from "../fixtures/audible-contract.js";
import { encodeMonoWav } from "./audio-files.js";
import {
  renderAlignedSpectrogram,
  renderAudibleTimeline,
  type AudibleTimelineMarker,
} from "./audio-artifact-images.js";
import { asFloat32, concatenate, resampleLinear } from "./audio-signal.js";

export interface AudibleArtifactAttachment {
  contentType: string;
  name: string;
  path: string;
}

export interface AudibleArtifactMetadata {
  captureTier?: string;
  fixture?: Record<string, unknown>;
  thresholds?: Record<string, number | string | boolean | null>;
}

export interface WriteAudibleFailureArtifactsInput {
  analysis: AudioOracleAnalysis;
  capture: MonoAudio;
  contract: readonly AudibleExpectation[];
  directory: string;
  markers?: readonly AudibleTimelineMarker[];
  metadata?: AudibleArtifactMetadata;
  references: readonly AcousticReference[];
  verdict: AudibleContractVerdict;
}

export interface AudibleFailureArtifacts {
  attachments: AudibleArtifactAttachment[];
  directory: string;
  files: {
    capturedOutput: string;
    diagnosis: string;
    expectedOutput: string;
    metrics: string;
    sourcePositionTrace: string;
    spectrogram: string;
    timeline: string;
  };
}

export async function writeAudibleMetricsArtifact(
  directory: string,
  analysis: AudioOracleAnalysis,
  verdict: AudibleContractVerdict,
  metadata: AudibleArtifactMetadata = {},
): Promise<string> {
  await mkdir(directory, { recursive: true });
  const path = join(directory, "metrics.json");
  await writeFile(path, json({ analysis: analysis.metrics, metadata, verdict }), "utf8");
  return path;
}

export async function writeAudibleFailureArtifacts(
  input: WriteAudibleFailureArtifactsInput,
): Promise<AudibleFailureArtifacts> {
  await mkdir(input.directory, { recursive: true });
  const expected = expectedAudioForContract(
    input.contract,
    input.references,
    input.capture.sampleRate,
  );
  const files = {
    capturedOutput: join(input.directory, "captured-output.wav"),
    diagnosis: join(input.directory, "diagnosis.txt"),
    expectedOutput: join(input.directory, "expected-output.wav"),
    metrics: join(input.directory, "metrics.json"),
    sourcePositionTrace: join(input.directory, "source-position-trace.json"),
    spectrogram: join(input.directory, "spectrogram.png"),
    timeline: join(input.directory, "audible-timeline.png"),
  };
  await Promise.all([
    writeFile(files.capturedOutput, encodeMonoWav(input.capture)),
    writeFile(files.expectedOutput, encodeMonoWav(expected)),
    writeFile(
      files.metrics,
      json({
        analysis: input.analysis.metrics,
        metadata: input.metadata ?? {},
        verdict: input.verdict,
      }),
      "utf8",
    ),
    writeFile(
      files.sourcePositionTrace,
      json({
        references: input.analysis.references,
        segments: input.analysis.segments,
        trace: input.analysis.trace,
      }),
      "utf8",
    ),
    writeFile(
      files.timeline,
      renderAudibleTimeline({
        analysis: input.analysis,
        expectations: input.contract,
        ...(input.markers ? { markers: input.markers } : {}),
      }),
    ),
    writeFile(files.spectrogram, renderAlignedSpectrogram(expected, input.capture)),
    writeFile(files.diagnosis, `${input.verdict.diagnosis.trim()}\n`, "utf8"),
  ]);
  return {
    attachments: [
      attachment("captured-output", files.capturedOutput, "audio/wav"),
      attachment("expected-output", files.expectedOutput, "audio/wav"),
      attachment("audible-metrics", files.metrics, "application/json"),
      attachment("source-position-trace", files.sourcePositionTrace, "application/json"),
      attachment("audible-timeline", files.timeline, "image/png"),
      attachment("spectrogram", files.spectrogram, "image/png"),
      attachment("audible-diagnosis", files.diagnosis, "text/plain"),
    ],
    directory: input.directory,
    files,
  };
}

export function expectedAudioForContract(
  contract: readonly AudibleExpectation[],
  references: readonly AcousticReference[],
  sampleRate: number,
): MonoAudio {
  const bySource = new Map(
    references.map((reference) => [reference.source, resampleLinear(reference, sampleRate)]),
  );
  const chunks = contract.map((expectation) => {
    if (expectation.kind === "silence") {
      const duration = expectation.expectedMs ?? (expectation.minMs + expectation.maxMs) / 2;
      return new Float32Array(Math.max(0, Math.round((sampleRate * duration) / 1_000)));
    }
    const reference = bySource.get(expectation.source);
    if (!reference)
      throw new Error(`Audible contract references unknown source ${expectation.source}.`);
    const start = Math.max(0, Math.round((expectation.startMs * sampleRate) / 1_000));
    const end = Math.min(reference.length, Math.round((expectation.endMs * sampleRate) / 1_000));
    return asFloat32(reference).slice(start, end);
  });
  return { sampleRate, samples: concatenate(chunks) };
}

function attachment(name: string, path: string, contentType: string): AudibleArtifactAttachment {
  return { contentType, name, path };
}

function json(value: unknown): string {
  return `${JSON.stringify(value, null, 2)}\n`;
}
