# Windows-Safe Pause Artifact Path Plan

Last actualized: 2026-06-06

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Keep the fix scoped to pause-pipeline artifact path generation and regression coverage.

## Goal

Prevent Windows pause-removal failures caused by overlong retained artifact paths under `aqe_artifacts/`.

This is not an audio-processing change. The pause-removal pipeline, output filenames, and manifest shape should keep working the same way. The fix should only change how long the retained pause-pipeline run directory name is allowed to become for the current artifact root.

## Architecture

Replace the fixed run-id stem budget with a root-aware path budget.

Today `make_pause_pipeline_run_id(...)` hard-caps the full run id at `160` characters. That is enough to overflow legacy Windows path handling when the add-on root itself is long and the source filename already includes repeated `_aqe_...` suffixes. The observed failure happens when the pipeline tries to write:

```text
aqe_artifacts/<run_id>/04_detected_pause_intervals.json
```

The correct fix is:

- keep the current sanitization and timestamp/token suffix format,
- compute the allowed run-id length from the actual artifact root,
- keep as much of the source stem as the current machine can support,
- fail early with an AQE error if even the shortest valid run id cannot fit.

On non-Windows platforms, do not preserve the old `160` cap. Allow longer run ids up to a path-component-safe ceiling so macOS and shorter roots retain more filename context.

## Key Rules

- Keep the existing `run_id` format:
  - sanitized source stem
  - `__YYYYMMDD_HHMMSS_microseconds_token` suffix
- Keep existing artifact filenames unchanged, including `04_detected_pause_intervals.json`.
- Treat the longest current pause artifact filename as the Windows limiter when budgeting the run id.
- Keep artifacts under the current `aqe_artifacts` root. Do not switch to temp directories or a new hashed storage scheme for this fix.
- If the Windows artifact root is too long to fit even a one-character stem plus the fixed suffix, raise `AudioProcessingError` before any pipeline write instead of falling through to `FileNotFoundError`.
- Do not change user-visible audio output paths, support-report field names, config, contracts, or manifest schema.

## Implementation Steps

- Update `make_pause_pipeline_run_id(...)` in `addon/anki_audio_quick_editor/audio_pipeline.py` to accept an internal optional max-length override.
- Keep `safe_filename_stem(...)` behavior unchanged.
- Add a helper in `addon/anki_audio_quick_editor/audio_artifacts.py` that computes the allowed run-id length for a given `artifact_root`.
- For Windows budgeting:
  - assume legacy safe full-path limit `259`,
  - subtract the expanded artifact root path length,
  - subtract separators,
  - subtract the longest planned pause-pipeline artifact filename, currently `04_detected_pause_intervals.json`,
  - cap the result by the path-component ceiling.
- For non-Windows:
  - use the component ceiling directly rather than the old `160` budget.
- Update `_create_pause_pipeline_run_dir(...)` to call the budget helper and pass the computed limit into `make_pause_pipeline_run_id(...)`.
- Raise `AudioProcessingError` from the helper or `_create_pause_pipeline_run_dir(...)` when the computed Windows budget cannot fit the fixed suffix plus one stem character.

## Test Plan

- Extend `tests/test_audio_pipeline.py` to cover:
  - existing sanitized run-id formatting still holds,
  - explicit max-length override truncates only the stem,
  - the reported Windows-style sample path for `04_detected_pause_intervals.json` stays below the legacy limit.
- Add `tests/test_audio_artifacts.py` for budget-specific behavior:
  - short Windows roots preserve more of the source stem,
  - longer Windows roots force more truncation,
  - an impossible Windows root raises the new AQE error before filesystem writes.
- Keep the regression tests pure and path-based; they do not need a Windows runner.
- Verify with:

```bash
python3 scripts/dev.py test tests/test_audio_pipeline.py tests/test_audio_artifacts.py
```

## Assumptions

- Legacy Windows path behavior is the supported baseline even if some users enable long-path support.
- `04_detected_pause_intervals.json` remains the longest current fixed pause-pipeline artifact filename.
- The fix is intentionally narrow: no artifact relocation, no manifest redesign, and no audio behavior changes.
