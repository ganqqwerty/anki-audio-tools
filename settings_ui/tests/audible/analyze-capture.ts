import { readFile } from "node:fs/promises";
import process from "node:process";
import { analyzeAudioCapture, decodeReferenceFromManifest } from "./fixtures/audio-oracle.js";
import { evaluateAudibleContract } from "./fixtures/audible-contract.js";
import type { AudibleExpectation } from "./fixtures/audible-contract-types.js";

interface Request {
  contract: AudibleExpectation[];
  manifestPath: string;
  oracleOptions?: Record<string, number | boolean>;
  options?: Record<string, number | boolean>;
  pcmPath: string;
  sampleRate: number;
  sourceFileName: string;
}

const requestPath = process.argv[2];
if (!requestPath) throw new Error("usage: vite-node analyze-capture.ts REQUEST.json");
const request = JSON.parse(await readFile(requestPath, "utf8")) as Request;
const bytes = await readFile(request.pcmPath);
const samples = new Float32Array(
  bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
);
const reference = await decodeReferenceFromManifest(request.manifestPath, {
  fileName: request.sourceFileName,
  source: request.sourceFileName,
});
const analysis = analyzeAudioCapture({
  capture: { sampleRate: request.sampleRate, samples },
  options: { minConfidence: 0.25, ...request.oracleOptions },
  references: [reference],
});
const verdict = evaluateAudibleContract(analysis, request.contract, request.options);
process.stdout.write(JSON.stringify({
  metrics: analysis.metrics,
  pass: verdict.pass,
  failures: verdict.failures,
  diagnosis: verdict.diagnosis,
  segments: analysis.segments,
}));
