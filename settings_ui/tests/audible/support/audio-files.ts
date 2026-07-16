import { spawn } from "node:child_process";
import { Buffer } from "node:buffer";
import { createHash } from "node:crypto";
import { access, readdir, readFile } from "node:fs/promises";
import { basename, dirname, join } from "node:path";
import process from "node:process";
import type { AcousticReference, MonoAudio } from "../fixtures/audio-oracle-types.js";
import { asFloat32 } from "./audio-signal.js";

export interface DecodeReferenceOptions {
  ffmpegExecutable?: string;
  metadata?: Record<string, unknown>;
  sampleRate?: number;
  source?: string;
}

export interface DecodeManifestReferenceOptions extends DecodeReferenceOptions {
  fileName: string;
  verifyChecksum?: boolean;
}

export async function decodeReferenceAudio(
  path: string,
  options: DecodeReferenceOptions = {},
): Promise<AcousticReference> {
  const sampleRate = options.sampleRate ?? 48_000;
  if (path.toLowerCase().endsWith(".wav")) {
    const decoded = decodeMonoWav(await readFile(path), options.source ?? basename(path));
    if (decoded.sampleRate !== sampleRate) {
      throw new Error(
        `WAV reference sample rate ${decoded.sampleRate} does not match requested ${sampleRate}.`,
      );
    }
    return {
      ...decoded,
      ...(options.metadata ? { metadata: options.metadata } : {}),
      path,
    };
  }
  const executable =
    options.ffmpegExecutable ?? process.env.AQE_E2E_FFMPEG ?? (await managedFfmpegPath());
  if (!executable) {
    throw new Error("Compressed acoustic references require AQE_E2E_FFMPEG.");
  }
  const output = await runFfmpeg(executable, [
    "-hide_banner",
    "-loglevel",
    "error",
    "-i",
    path,
    "-map",
    "0:a:0",
    "-ac",
    "1",
    "-ar",
    String(sampleRate),
    "-f",
    "f32le",
    "pipe:1",
  ]);
  const sampleCount = Math.floor(output.length / 4);
  const samples = new Float32Array(sampleCount);
  for (let index = 0; index < sampleCount; index += 1) {
    samples[index] = output.readFloatLE(index * 4);
  }
  return {
    ...(options.metadata ? { metadata: options.metadata } : {}),
    path,
    sampleRate,
    samples,
    source: options.source ?? basename(path),
  };
}

async function managedFfmpegPath(): Promise<string | null> {
  const runtimeRoot = "../addon/anki_audio_quick_editor/user_files/runtime";
  try {
    for (const entry of await readdir(runtimeRoot, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const path = join(runtimeRoot, entry.name, "macos-arm64", "ffmpeg");
      try {
        await access(path);
        return path;
      } catch {
        // This runtime version does not contain the current platform payload.
      }
    }
  } catch {
    return null;
  }
  return null;
}

export async function decodeReferenceFromManifest(
  manifestPath: string,
  options: DecodeManifestReferenceOptions,
): Promise<AcousticReference> {
  const manifestBytes = await readFile(manifestPath);
  const manifest = JSON.parse(manifestBytes.toString("utf8")) as Record<string, unknown>;
  const path = join(dirname(manifestPath), options.fileName);
  const expectedChecksum = manifestChecksum(manifest, options.fileName);
  if (options.verifyChecksum !== false && expectedChecksum) {
    const actualChecksum = createHash("sha256")
      .update(await readFile(path))
      .digest("hex");
    if (actualChecksum !== expectedChecksum) {
      throw new Error(
        `Reference checksum mismatch for ${options.fileName}: expected ${expectedChecksum}, got ${actualChecksum}.`,
      );
    }
  }
  return decodeReferenceAudio(path, {
    ...options,
    metadata: { manifest, ...options.metadata },
    source: options.source ?? options.fileName,
  });
}

export function encodeMonoWav(audio: MonoAudio): Buffer {
  const samples = asFloat32(audio.samples);
  const bytesPerSample = 2;
  const dataLength = samples.length * bytesPerSample;
  const output = Buffer.alloc(44 + dataLength);
  output.write("RIFF", 0, "ascii");
  output.writeUInt32LE(36 + dataLength, 4);
  output.write("WAVE", 8, "ascii");
  output.write("fmt ", 12, "ascii");
  output.writeUInt32LE(16, 16);
  output.writeUInt16LE(1, 20);
  output.writeUInt16LE(1, 22);
  output.writeUInt32LE(audio.sampleRate, 24);
  output.writeUInt32LE(audio.sampleRate * bytesPerSample, 28);
  output.writeUInt16LE(bytesPerSample, 32);
  output.writeUInt16LE(16, 34);
  output.write("data", 36, "ascii");
  output.writeUInt32LE(dataLength, 40);
  for (let index = 0; index < samples.length; index += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[index] ?? 0));
    const integer = clamped < 0 ? Math.round(clamped * 32_768) : Math.round(clamped * 32_767);
    output.writeInt16LE(integer, 44 + index * bytesPerSample);
  }
  return output;
}

export function decodeMonoWav(bytes: Buffer, source = "reference.wav"): AcousticReference {
  if (bytes.toString("ascii", 0, 4) !== "RIFF" || bytes.toString("ascii", 8, 12) !== "WAVE") {
    throw new Error("Expected a RIFF/WAVE reference.");
  }
  let offset = 12;
  let format = 0;
  let channels = 0;
  let sampleRate = 0;
  let bitsPerSample = 0;
  let data: Buffer | null = null;
  while (offset + 8 <= bytes.length) {
    const id = bytes.toString("ascii", offset, offset + 4);
    const size = bytes.readUInt32LE(offset + 4);
    const start = offset + 8;
    if (id === "fmt ") {
      format = bytes.readUInt16LE(start);
      channels = bytes.readUInt16LE(start + 2);
      sampleRate = bytes.readUInt32LE(start + 4);
      bitsPerSample = bytes.readUInt16LE(start + 14);
    }
    if (id === "data") data = bytes.subarray(start, Math.min(bytes.length, start + size));
    offset = start + size + (size % 2);
  }
  if (!data || !sampleRate || !channels) throw new Error("WAV reference is missing fmt or data.");
  const bytesPerSample = bitsPerSample / 8;
  if (!((format === 1 && bitsPerSample === 16) || (format === 3 && bitsPerSample === 32))) {
    throw new Error(`Unsupported WAV encoding: format ${format}, ${bitsPerSample} bits.`);
  }
  const frameCount = Math.floor(data.length / bytesPerSample / channels);
  const samples = new Float32Array(frameCount);
  for (let frame = 0; frame < frameCount; frame += 1) {
    let total = 0;
    for (let channel = 0; channel < channels; channel += 1) {
      const sampleOffset = (frame * channels + channel) * bytesPerSample;
      total +=
        format === 3 ? data.readFloatLE(sampleOffset) : data.readInt16LE(sampleOffset) / 32_768;
    }
    samples[frame] = total / channels;
  }
  return { sampleRate, samples, source };
}

function manifestChecksum(manifest: Record<string, unknown>, fileName: string): string | null {
  const files = manifest.files;
  if (!files || typeof files !== "object") return null;
  const entry = (files as Record<string, unknown>)[fileName];
  if (typeof entry === "string") return entry;
  if (!entry || typeof entry !== "object") return null;
  const record = entry as Record<string, unknown>;
  const value = record.sha256 ?? record.checksum;
  return typeof value === "string" ? value : null;
}

function runFfmpeg(executable: string, arguments_: readonly string[]): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const child = spawn(executable, arguments_, { stdio: ["ignore", "pipe", "pipe"] });
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
    child.once("error", reject);
    child.once("close", (code) => {
      if (code === 0) resolve(Buffer.concat(stdout));
      else
        reject(new Error(`ffmpeg exited with ${code}: ${Buffer.concat(stderr).toString("utf8")}`));
    });
  });
}
