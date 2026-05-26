# Silero VAD Pause Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Silero VAD as a bundled, managed-runtime pause detection algorithm for Shorten Pauses without requiring users to install anything on their operating system.

**Architecture:** Ship the prebuilt `sherpa-onnx-vad` executable from the same locked Sherpa ONNX release already used for `sherpa-spleeter`, renamed to `silero-vad`, plus one shared Silero ONNX model in the existing runtime pack system. The executable dynamically uses the ONNX Runtime files already shipped for `sherpa-spleeter`, writes a VAD-trimmed WAV, and the Python pause pipeline reuses the existing working-audio and final ffmpeg render stages.

**Tech Stack:** Python 3.13 add-on runtime, ffmpeg/ffprobe, prebuilt Sherpa ONNX VAD executable, existing Sherpa ONNX Runtime 1.24.4 libraries, Silero VAD ONNX model, Svelte 5 + TypeScript, JSON schema contracts, pytest, Vitest, Anki e2e tests.

---

## Non-Negotiable Runtime Model

Users must not install Python packages, system packages, model files, ONNX Runtime, PyTorch, or command-line tools. Runtime behavior must match the existing managed library model:

- Public `.ankiaddon` archives stay thin and contain only `bin/runtime_manifest.json`.
- On startup, the add-on downloads `aqe-runtime-<version>-<target>.zip` from the GitHub Release URL in the manifest.
- The runtime pack contains every required executable, shared library, and model file.
- The new Silero path must not use `PATH` fallback. It should resolve only from managed runtime first, then source-tree bundled runtime files for development.
- If a prebuilt executable stops being available in Sherpa ONNX releases, then and only then add a GitHub Actions build path for the replacement helper.

## Shipped File Size Estimate

Count only files added to the runtime packs, not build dependencies.

Current runtime packs already include ONNX Runtime support files:

- `bin/macos-arm64/libonnxruntime.1.24.4.dylib`: about 25.1 MB
- `bin/macos-x86_64/libonnxruntime.1.24.4.dylib`: about 28.2 MB
- `bin/windows-x86_64/onnxruntime.dll`: about 15.3 MB
- `bin/windows-x86_64/onnxruntime_providers_shared.dll`: about 0.1 MB

The plan reuses those files and does not add another ONNX Runtime copy.

New files per downloaded target runtime pack:

| File | Raw size estimate | Zip size estimate | Notes |
|---|---:|---:|---|
| `bin/<target>/silero-vad` or `silero-vad.exe` | 0.26-0.49 MB | 0.15-0.35 MB | Extracted from the locked Sherpa ONNX `sherpa-onnx-vad` executable and renamed. |
| `bin/models/silero-vad/silero_vad.onnx` | 0.61 MB | ~0.55 MB | Downloaded from the Sherpa ONNX `asr-models` release; SHA-256 `9e2449e1087496d8d4caba907f23e0bd3f78d91fa552479bb9c23ac09cbb1fd6`. |

Expected per-user runtime pack increase: **about 0.8-1.2 MB**, conservatively **under 2 MB**, assuming the runtime pack continues to de-duplicate ONNX Runtime support files shared with `sherpa-spleeter`.

Total GitHub Release storage increase across all three packs: **about 2.5-4 MB**, because each platform pack includes the shared model plus one target executable.

Explicitly excluded from shipped files:

- `silero-vad` Python package
- `torch`
- `torchaudio`
- Python `onnxruntime` wheels
- `numpy`, `protobuf`, or other Python ML dependencies

## File Structure

Create:

- `scripts/release_silero_assets.py`: fetches the locked Sherpa ONNX VAD executable and Silero VAD model, then runs current-host Silero smoke checks.

Modify:

- `release_assets.lock.json`: add `silero-vad` tool entries for every target and `silero-vad-model` shared file.
- `scripts/release_asset_common.py`: add `silero-vad` to target tool names and `silero-vad-model` to shared file names.
- `scripts/release_assets.py`, `scripts/release_assets_commands.py`, `scripts/release_assets_cli.py`: add fetch/verify commands for Silero assets.
- `scripts/release_asset_verify.py`: add current-host Silero smoke diagnostics.
- `scripts/release_runtime.py`: keep runtime-pack de-duplication behavior and add tests proving ONNX Runtime files are not duplicated.
- `addon/anki_audio_quick_editor/audio_tools.py`: add `find_silero_vad_bundle()` and `expected_bundled_silero_vad_model_path()`.
- `addon/anki_audio_quick_editor/runtime_manager.py`: add `silero-vad` executable mapping and managed Silero model lookup.
- `addon/anki_audio_quick_editor/errors.py`: add `MissingSileroVadError`.
- `addon/anki_audio_quick_editor/audio_commands_runtime.py`: add ffmpeg preparation and Silero VAD command builders.
- `addon/anki_audio_quick_editor/audio_artifacts.py`: include pause detection algorithm and Silero config in manifests.
- `addon/anki_audio_quick_editor/audio_pause_pipeline.py`: split DeepFilter detection from common pause timeline/rendering and add the Silero path.
- `addon/anki_audio_quick_editor/audio_processor.py`, `addon/anki_audio_quick_editor/audio_processor_runtime.py`: sync and re-export Silero dependencies through the existing facade.
- `addon/anki_audio_quick_editor/audio_state.py`: add `pause_detection_algorithm` with default `"deep_filter"`.
- `addon/anki_audio_quick_editor/audio_operation_params.py`: validate operation-local `pause_detection_algorithm`.
- `addon/anki_audio_quick_editor/config.schema.json`, `addon/anki_audio_quick_editor/config.json`, `addon/anki_audio_quick_editor/config_migration.py`: persist and migrate the new default.
- `contracts/communication.schema.json` and generated TypeScript/Python contract files: expose the new pause algorithm parameter.
- `settings_ui/src/settings/ToolbarVisibilitySettings.svelte`: add default pause detection algorithm control.
- `settings_ui/src/editor-inline/*` split-button files: expose pause algorithm selection alongside pause aggressiveness.
- `settings_ui/src/batch/*`: expose the same pause algorithm for Browser batch operations.
- `settings_ui/src/lib/i18n.ts` and `addon/anki_audio_quick_editor/locales/*.json`: add labels and status strings.
- `addon/anki_audio_quick_editor/bin/README.md`, `addon/anki_audio_quick_editor/bin/THIRD_PARTY_NOTICES.md`, `DEVELOPMENT.md`, `CONFIG_SCHEMA.md`, `WEBVIEW_AND_TEMPLATES.md`: document the new runtime asset and config surface where affected.
- Existing release, runtime, settings, pause pipeline, and e2e tests listed in the task details below.

## Tasks

### Task 1: Lock The Model And Runtime Asset Shape

- [ ] Add `silero-vad` to `TARGET_TOOL_NAMES` in `scripts/release_asset_common.py` for `macos-arm64`, `macos-x86_64`, and `windows-x86_64`.
- [ ] Add `silero-vad-model` to `SHARED_FILE_NAMES`.
- [ ] Add `release_assets.lock.json` entries:
  - `macos-arm64/tools/silero-vad/executable`: `silero-vad`
  - `macos-x86_64/tools/silero-vad/executable`: `silero-vad`
  - `windows-x86_64/tools/silero-vad/executable`: `silero-vad.exe`
  - `diagnostic_args`: `["--version"]`
  - `licenses`: `["MIT"]`
  - `runtime_files`: the same ONNX Runtime support files already used by `sherpa-spleeter` for that target, with identical paths and checksums.
  - `archive_member`: `.../bin/sherpa-onnx-vad` or `.../bin/sherpa-onnx-vad.exe`
  - `shared_files/silero-vad-model/path`: `models/silero-vad/silero_vad.onnx`
  - `shared_files/silero-vad-model/source_url`: `https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models`
  - `shared_files/silero-vad-model/download_url`: `https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx`
  - `shared_files/silero-vad-model/download_sha256`: `9e2449e1087496d8d4caba907f23e0bd3f78d91fa552479bb9c23ac09cbb1fd6`
  - `shared_files/silero-vad-model/sha256`: `9e2449e1087496d8d4caba907f23e0bd3f78d91fa552479bb9c23ac09cbb1fd6`
- [ ] Update release asset validation tests so the supported target matrix requires `silero-vad` and the shared file matrix requires the Silero model.
- [ ] Add a release-runtime test that builds pack entries with both `sherpa-spleeter` and `silero-vad` and asserts each ONNX Runtime support path appears once in the pack metadata.

Verification:

```bash
python3 scripts/dev.py test tests/test_release_assets.py tests/test_release.py tests/test_runtime_manager.py
```

### Task 2: Fetch A Prebuilt `silero-vad` Executable From Sherpa ONNX

- [ ] Add `scripts/release_silero_assets.py`.
- [ ] Implement `fetch_silero_vad(lock, target_keys)`:
  - download the locked Sherpa ONNX archive already referenced by each target's `silero-vad` lock entry
  - verify the archive SHA-256 before extraction
  - extract only `sherpa-onnx-vad` or `sherpa-onnx-vad.exe`
  - stage it under `addon/anki_audio_quick_editor/bin/<target>/silero-vad` or `silero-vad.exe`
  - verify the executable SHA-256 after extraction
- [ ] Keep the CLI contract as the upstream executable contract:

```text
silero-vad --version
silero-vad \
  --silero-vad-model=<path-to-silero_vad.onnx> \
  --silero-vad-threshold=<0.0-1.0> \
  --silero-vad-min-silence-duration=<seconds> \
  --silero-vad-min-speech-duration=<seconds> \
  --vad-num-threads=1 \
  <path-to-16khz-mono-wav> \
  <path-to-vad-output-wav>
```

- [ ] Do not add GitHub Actions build workflows unless this upstream executable becomes unavailable.

Verification:

```bash
python3 scripts/dev.py release-assets fetch-silero-vad --target current
addon/anki_audio_quick_editor/bin/macos-arm64/silero-vad --version
```

### Task 3: Fetch The Silero Model Without Installing Python Dependencies

- [ ] Implement `fetch_silero_vad_model(lock)`:
  - download the locked model file to `.release-assets/sources/silero-vad/`
  - verify downloaded model SHA-256
  - write it to `addon/anki_audio_quick_editor/bin/models/silero-vad/silero_vad.onnx`
  - verify model SHA-256 after extraction
- [ ] Add `python3 scripts/dev.py release-assets fetch-silero-vad-model`.
- [ ] Add `python3 scripts/dev.py release-assets verify --diagnostics` support for current-host Silero smoke:
  - generate a short 16 kHz WAV fixture
  - run `silero-vad` with the Silero model and output WAV
  - assert the output WAV exists and the command exits successfully.

Verification:

```bash
python3 scripts/dev.py release-assets fetch-silero-vad-model
python3 scripts/dev.py release-assets verify --target current --diagnostics
```

### Task 4: Add Runtime Discovery And Diagnostics

- [ ] Add `silero-vad` executable mappings in `addon/anki_audio_quick_editor/audio_tools.py` and `addon/anki_audio_quick_editor/runtime_manager.py`.
- [ ] Add `managed_silero_vad_model_path()` and `expected_managed_silero_vad_model_path()` in `runtime_manager.py`, or replace the Spleeter-specific model helpers with a small generic managed model helper.
- [ ] Add `expected_bundled_silero_vad_model_path()` and `_required_silero_vad_model()` in `audio_tools.py`.
- [ ] Add `find_silero_vad_bundle() -> tuple[Path, Path]` returning executable and model path.
- [ ] Do not use `shutil.which("silero-vad")`. Missing Silero must point users to Settings > Diagnostics to install or repair the managed runtime.
- [ ] Add diagnostics output for Silero with `--version`, matching existing `sherpa-spleeter` diagnostics shape.
- [ ] Update tests for managed path lookup, bundled fallback lookup, missing runtime errors, and diagnostics JSON.

Verification:

```bash
python3 scripts/dev.py test tests/test_audio_tools.py tests/test_runtime_manager.py tests/test_settings_commands_diagnostics.py tests/test_diagnostics.py
```

### Task 5: Add The Silero Pause Detection Pipeline

- [ ] Add `pause_detection_algorithm: str = "deep_filter"` to `AudioProcessingConfig`.
- [ ] Add allowed values `deep_filter` and `silero_vad` in config schema, migration, and operation parameter validation.
- [ ] Add `build_silero_vad_prepare_command(ffmpeg_path, working_original, analysis_wav_path)`:
  - input: current working original WAV
  - output: WAV
  - format: 16 kHz, mono, signed 16-bit little-endian
- [ ] Add `build_silero_vad_command(silero_path, model_path, analysis_wav_path, output_wav_path, threshold, min_silence_seconds, min_speech_seconds)`.
- [ ] Map existing pause aggressiveness to Silero parameters:
  - gentle: threshold `0.55`, min silence `0.70 s`, min speech `0.12 s`
  - normal: threshold `0.50`, min silence `0.45 s`, min speech `0.10 s`
  - aggressive: threshold `0.45`, min silence `0.25 s`, min speech `0.08 s`
- [ ] Refactor `audio_pause_pipeline.py` so both algorithms share:
  - run directory creation
  - manifest writing
  - working original render
  - timeline planning
  - filter script writing
  - final output rendering
  - support incident recording
- [ ] Keep the existing DeepFilter branch behavior and artifact names stable for current tests.
- [ ] Add Silero-specific artifact names:
  - `02_silero_input_16k_mono.wav`
  - `03_silero_vad_output.wav`
  - `04_silero_final_filter.ffscript`
  - `05_final_output.mp3`
- [ ] Set manifest operation to `silero_vad_pause_speedup` for Silero runs and keep `deep_filter_pause_speedup` for existing DeepFilter runs.
- [ ] Record `pause_detection_algorithm`, Silero threshold, min silence, and min speech in the manifest config snapshot.

Verification:

```bash
python3 scripts/dev.py test tests/test_audio_pause_pipeline.py tests/test_audio_operation_params.py tests/test_audio_state.py
```

### Task 6: Expose The Algorithm In Settings, Editor, And Batch

- [ ] Add `pause_detection_algorithm` to `contracts/communication.schema.json` defaults and operation parameters.
- [ ] Regenerate contracts with the repo workflow.
- [ ] Add Settings default control under the Shorten Pauses settings near pause aggressiveness:
  - `DeepFilterNet`
  - `Silero VAD`
- [ ] Add the same option to the editor Shorten Pauses split-button quick settings.
- [ ] Add the same option to Browser batch controls for `remove_pauses`.
- [ ] Keep default behavior as DeepFilterNet so existing users do not see changed output after upgrade.
- [ ] Add localized strings for English, Japanese, Russian, and Simplified Chinese.
- [ ] Update split-button persistence and defaults so editor and batch operation parity is preserved.

Verification:

```bash
python3 scripts/dev.py contracts-check
python3 scripts/dev.py test-svelte
python3 scripts/dev.py test tests/test_settings_initial_state.py tests/test_editor_split_defaults.py tests/test_browser_dialog_state.py tests/test_batch_operations.py
```

### Task 7: Release Packaging

- [ ] Do not add build workflows for Silero while Sherpa ONNX publishes target executables.
- [ ] Update `DEVELOPMENT.md` release asset workflow with:

```bash
python3 scripts/dev.py release-assets fetch-silero-vad-model
python3 scripts/dev.py release-assets fetch-silero-vad --target all
python3 scripts/dev.py release-assets lock-checksums
```

- [ ] Update `addon/anki_audio_quick_editor/bin/README.md` with the new executable and model layout.
- [ ] Update `THIRD_PARTY_NOTICES.md` with Silero VAD source, MIT license classification, locked wheel, extracted model, and no PyTorch redistribution.
- [ ] Build all runtime packs and inspect sizes:

```bash
python3 scripts/release.py --target all
python3 - <<'PY'
from pathlib import Path
for path in sorted(Path("dist").glob("aqe-runtime-*-*.zip")):
    print(path.name, path.stat().st_size)
PY
```

- [ ] Reject the implementation if any runtime pack grows by more than 5 MB unless the growth is explained by the target executable size and no duplicate ONNX Runtime files are present.

### Task 8: Verification Gate

- [ ] Run focused Python tests:

```bash
python3 scripts/dev.py test tests/test_audio_pause_pipeline.py tests/test_audio_tools.py tests/test_runtime_manager.py tests/test_release_assets.py tests/test_release.py
```

- [ ] Run frontend tests:

```bash
python3 scripts/dev.py test-svelte
```

- [ ] Run contract and schema checks:

```bash
python3 scripts/dev.py contracts-check
python3 scripts/dev.py config-schema
```

- [ ] Run release asset verification:

```bash
python3 scripts/dev.py release-assets verify --target all
python3 scripts/dev.py release-assets verify --target current --diagnostics
```

- [ ] Run the full reusable gate:

```bash
python3 scripts/dev.py check
```

- [ ] Run e2e:

```bash
python3 scripts/dev.py test-e2e
```

- [ ] Validate a release build:

```bash
python3 scripts/release.py --target all
```

## Risks And Controls

- **Silero executable behavior mismatch:** The downloaded Sherpa ONNX VAD executable removes detected non-speech instead of emitting interval JSON. Keep Silero mode documented as VAD-based pause removal and keep DeepFilter as the default when target-gap-preserving behavior is required.
- **Duplicate ONNX Runtime payload:** Lock entries may reference existing runtime support files for dependency clarity, but runtime pack entries must remain de-duplicated by archive path. Add a release test for this.
- **Behavior drift for existing users:** Keep DeepFilterNet as the default pause algorithm and preserve current DeepFilter artifact names and tests.
- **False pause detection from VAD gaps:** Keep DeepFilter as the default and tune Silero's threshold/min-silence parameters conservatively; Silero mode should be easy to switch away from per operation.
- **Upstream executable availability:** If future Sherpa ONNX releases stop publishing `sherpa-onnx-vad`, add GitHub Actions build workflows then. Do not build executables while locked downloads are available.

## Self-Review

- The plan does not require users to install any OS-level dependency.
- The plan does not ship PyTorch, torchaudio, Python ONNX Runtime, numpy, or the upstream `silero-vad` package.
- The only new shipped runtime payloads are one downloaded executable per target and one shared ONNX model.
- Existing DeepFilter pause shortening remains the default and should keep current tests passing.
- Runtime publishing uses the same GitHub Release runtime pack flow already used by ffmpeg, DeepFilterNet, RNNoise, DPDFNet, and Sherpa Spleeter.
