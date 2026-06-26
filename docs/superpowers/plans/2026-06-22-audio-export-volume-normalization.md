# Audio Export Volume Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in `Normalize volume` option to Browser audio export for both ZIP and combined MP3 exports without mutating Anki media or notes.

**Architecture:** Keep the existing dependency direction: generated contracts and import-safe planning/rendering helpers feed the Browser export runner, while Svelte owns form state and bridge serialization. `audio_export_rendering.py` remains pure ffmpeg command construction, `audio_export_planning.py` owns zip-entry naming, and `browser_audio_export_runner.py` owns temp files, subprocesses, progress, cancellation, and promotion. Check runner size and architecture after backend implementation; if the runner exceeds 350 lines, pause and extract a focused ZIP writer instead of adding more branching.

**Tech Stack:** Python 3.13 dataclasses, pytest, JSON Schema generated contracts, Svelte 5/TypeScript, Vitest, ffmpeg `loudnorm`.

---

### Task 1: Contract And Request Model

- [ ] Add `normalize_volume` to `AudioExportDefaults` and `AudioExportStartRequest` in `contracts/communication.schema.json`.
- [ ] Regenerate `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts`.
- [ ] Add `normalize_volume: bool = False` to `AudioExportRequest`.
- [ ] Include `defaults.normalize_volume: false` and decode `payload["normalize_volume"]` in `browser_audio_export_state.py`.
- [ ] Update `tests/test_browser_audio_export_state.py` for defaults, true/false decode, and missing-field contract rejection.
- [ ] Verify with `python3 -m pytest tests/test_browser_audio_export_state.py -q` and `python3 scripts/dev.py contracts-check`.

### Task 2: Rendering Commands And ZIP Naming

- [ ] Rename the shape-only WAV builder to `build_stage_wav_command`.
- [ ] Add `LOUDNORM_EXPORT_FILTER = "loudnorm=I=-16:TP=-1.5:LRA=11"`.
- [ ] Add `build_normalized_wav_command()` and `build_normalized_mp3_command()`.
- [ ] Extend `make_zip_entry_name(..., forced_suffix: str | None = None)` so normalized ZIP entries can force `.mp3` while reusing existing collision handling.
- [ ] Update `tests/test_audio_export_rendering.py` and `tests/test_audio_export_planning.py`.
- [ ] Verify with `python3 -m pytest tests/test_audio_export_rendering.py tests/test_audio_export_planning.py -q`.

### Task 3: Runner Behavior

- [ ] Route ZIP export through byte-for-byte copy when `normalize_volume` is false.
- [ ] For normalized ZIP, render each item to a destination-local temp MP3 with `build_normalized_mp3_command()`, write `.mp3` archive entries, log `Normalized and exported ...`, and clean temp files on success, failure, or cancellation.
- [ ] For combined MP3, use `build_stage_wav_command()` when unchecked and `build_normalized_wav_command()` when checked. Do not apply loudnorm to the final MP3 command.
- [ ] Keep temp roots destination-local so cleanup is deterministic in tests.
- [ ] Update `tests/test_browser_audio_export_runner.py` for normalized ZIP, normalized combined MP3, and cancellation cleanup.
- [ ] Verify with `python3 -m pytest tests/test_browser_audio_export_runner.py -q`, `python3 scripts/dev.py architecture-report`, `python3 scripts/dev.py file-lines`, and `wc -l addon/anki_audio_quick_editor/browser_audio_export_runner.py`.

### Task 4: Frontend And Locales

- [ ] Add `normalizeVolume` to `settings_ui/src/batch/export-state.ts` and serialize it as `normalize_volume`.
- [ ] Render a `Normalize volume` checkbox in `BatchExportControls.svelte` with `data-testid="audio-export-normalize-volume"` and disabled state tied to export running state.
- [ ] Add `audio_export.normalize_volume` to every locale catalog.
- [ ] Update `settings_ui/tests/batch-export-state.test.ts` and `settings_ui/tests/batch-export-app.test.ts`.
- [ ] Verify with `cd settings_ui && npm run test -- batch-export-state.test.ts batch-export-app.test.ts`, then `python3 scripts/dev.py i18n`.

### Task 5: E2E Coverage

- [ ] Extend `e2e/test_browser_audio_export_workflow.py` helper with `normalize_volume=False`.
- [ ] Add normalized ZIP and normalized combined MP3 Browser workflow tests.
- [ ] Verify with `python3 -m pytest e2e/test_browser_audio_export_workflow.py -q` or, if direct pytest needs rebuilt bundles, `python3 scripts/dev.py test-e2e-parallel`.

### Task 6: Final Verification

- [ ] Run focused backend and frontend tests.
- [ ] Run `python3 scripts/dev.py contracts-check`, `python3 scripts/dev.py i18n`, `python3 scripts/dev.py architecture-report`, and `python3 scripts/dev.py file-lines`.
- [ ] Run `python3 scripts/dev.py check`.
- [ ] Run `python3 scripts/dev.py test-e2e-parallel`, then `python3 scripts/dev.py test-e2e`.
- [ ] Inspect `git status --short` and dependency graph changes before final reporting.
