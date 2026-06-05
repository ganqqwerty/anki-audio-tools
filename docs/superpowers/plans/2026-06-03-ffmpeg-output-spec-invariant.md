# FFmpeg Output Spec Invariant Plan

Last actualized: 2026-06-03

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Use the existing ffmpeg output contract validators as the safety net while refactoring call sites.

## Goal

Prevent final user-visible ffmpeg output mismatches by making final path, resolved output format, MIME type, and codec args travel as one object. The invariant is:

```text
final path extension == resolved output format extension == compatible encoder/container args
```

This is a guardrail/refactor around final outputs only. It should not change valid audio behavior; it should replace invalid ffmpeg failures with earlier internal validation.

## Architecture

Add a `FinalAudioOutputSpec` that wraps the already-resolved `AudioOutputPolicy` rather than creating a second policy system.

The spec should contain:

- `path: Path`
- `output_format: str`
- `extension: str`
- `mime_type: str`
- `codec_args: tuple[str, ...]`

Add one resolver, for example `resolve_final_audio_output(...)`, that returns `FinalAudioOutputSpec` by combining:

- the source path or model output metadata
- `AudioProcessingConfig.output_format` or an explicit operation target
- an optional caller-provided final `output_path`
- the existing `resolve_output_policy_from_metadata(...)`
- the existing `validate_final_ffmpeg_output(...)`

Keep the current command-builder validators. They are the last line of defense if future code bypasses the spec.

## Key Rules

- `output_format="source"` preserves the source visible extension when preservable; otherwise it resolves to MP3.
- Explicit formats such as `wav`, `flac`, `mp3`, and `m4a` are allowed regardless of the source extension.
- Reject explicit format/final-path mismatches. Example: `output_format="wav"` with final `output_path="clip.mp3"` must fail before ffmpeg starts.
- Do not reject MP3 source input with global WAV output. That is valid and must produce a `.wav` final path.
- Denoise/model output metadata stays separate from user-visible source metadata. Model-required intermediate WAV/raw outputs remain explicit stage artifacts.
- Intermediate builders such as WAV preparation, raw PCM, model output commands, and null sinks do not use `FinalAudioOutputSpec`.

## Implementation Steps

- Add `FinalAudioOutputSpec` and `resolve_final_audio_output(...)` near the existing output policy module.
- Make `resolve_final_audio_output(...)` call `validate_final_ffmpeg_output(...)` before returning.
- Update final render paths to consume `FinalAudioOutputSpec` instead of separately passing `output_path` and `codec_args`:
  - normal editor render
  - region delete/keep
  - pause removal final render
  - convert
  - size reduction where the final target is fixed MP3
  - DeepFilterNet, RNNoise, DPDFNet, Spleeter, pitch-hum final encodes
  - batch transforms
- Keep intermediate builders separate and stage-specific:
  - WAV preparation requires `.wav` plus PCM codec
  - RNNoise raw preparation requires `.s16le`, `-f s16le`, and `pcm_s16le`
  - silencedetect null output remains excluded from final-output validation
- Update architecture contracts/import-linter metadata if a new module is added.

## Test Plan

- Add unit tests for `FinalAudioOutputSpec` over all supported final formats:
  - source-preserved MP3, M4A/AAC, WAV, FLAC, OGG/OGA/OPUS/WEBM
  - explicit MP3, M4A, WAV, and FLAC
  - unknown source extension fallback to MP3
- Add negative tests proving final-path mismatches raise before ffmpeg starts:
  - final `.mp3` path with WAV/PCM args
  - final `.wav` path with MP3 args
  - `output_format="wav"` with final path `clip.mp3`
  - `output_format="mp3"` with final path `clip.wav`
- Add command-builder tests that final builders either accept `FinalAudioOutputSpec` directly or are called only after final validation.
- Keep the denoise e2e regression:
  - MP3 input
  - global `output_format="wav"`
  - standard denoise
  - final output path must end in `.wav`
- Add an architecture or unit test that enumerates user-visible final render entry points and verifies they resolve a `FinalAudioOutputSpec` before building final ffmpeg commands.

## Assumptions

- `output_format="source"` preserves container/extension policy, not byte-identical codec parameters.
- Algorithm-required intermediate WAV/raw conversions are valid and expected.
- Existing runtime ffmpeg output validators remain in place after this refactor.
- The refactor should be staged after current invariant tests are green, so failures identify API migration mistakes rather than the original bug class.
