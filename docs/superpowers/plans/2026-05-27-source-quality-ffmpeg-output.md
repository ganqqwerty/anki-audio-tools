# Source-Quality FFmpeg Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace forced MP3 final output with a source-aware output policy that preserves source format, bitrate, sample rate, and channels where practical while keeping model-required intermediate formats intact.

**Architecture:** Add a small output-policy layer that probes source audio metadata once, resolves `source` into a concrete final extension/encoder, and supplies codec arguments to all final FFmpeg encode commands. Keep analysis/model intermediates separate from final-output policy so Silero, RNNoise, DeepFilterNet, Spleeter, prosody analysis, and pitch-hum synthesis do not get accidental "preservation" rewrites that break their algorithms.

**Tech Stack:** Python 3.13 add-on runtime, FFmpeg/ffprobe, pytest, Anki e2e tests, Svelte 5 + TypeScript, Vitest, JSON schema generated contracts.

---

## Planning Assumptions

- Add a new persisted output setting value: `source`.
- Make `source` the default output policy for edited audio so the requested behavior applies without forcing users to reconfigure.
- Keep manual output choices `mp3`, `m4a`, `wav`, and `flac`; do not add every preserved extension as a manual UI menu choice in this pass.
- When `output_format` is `source`, keep the original visible file extension where possible. The first pass should preserve at least these common Anki audio extensions when FFmpeg can write them: `mp3`, `m4a`, `aac`, `wav`, `flac`, `ogg`, `oga`, `opus`, and `webm`.
- Preserving `ogg`, `oga`, `opus`, `webm`, and raw `aac` depends on the managed FFmpeg runtime having the required encoders and muxers. Treat runtime capability as a release-blocking prerequisite, not as a best-effort runtime surprise.
- Prefer [BtbN FFmpeg builds](https://github.com/BtbN/FFmpeg-Builds) where they satisfy the capability profile. BtbN publishes Windows and Linux builds and does not cover the current macOS runtime targets, so macOS needs a repo-owned GitHub Actions build/upload path.
- If a BtbN prebuilt artifact for a supported target is missing required capabilities, use the BtbN build scripts/configuration in GitHub Actions for that target instead of weakening the source-preservation policy.
- Keep the runtime asset work inside the existing thin-release/runtime-pack system: update `release_assets.lock.json`, fetch into `.release-assets`, stage into runtime packs, and upload runtime packs through the existing release flow.
- Fall back to MP3 only when the source extension is unknown, unsupported by Anki, unsupported by the bundled FFmpeg encoder/muxer, or the source codec/container combination cannot be mapped safely.
- Native playback segment temp files stay MP3 for compatibility and are excluded from final-media preservation.
- Model and analysis intermediates stay in their current required formats unless explicitly listed in this plan.

## File Structure

Create:

- `addon/anki_audio_quick_editor/audio_output_policy.py`: source metadata model, ffprobe metadata probing, source-extension-to-final-output resolution, MIME mapping, and final encoder arg generation.
- `scripts/ffmpeg_runtime_capabilities.py`: reusable capability probe for managed FFmpeg binaries.
- `.github/workflows/build-ffmpeg-runtime.yml`: manual workflow to download or build target FFmpeg archives and upload them to GitHub releases.
- `tests/test_ffmpeg_runtime_capabilities.py`: parser, policy, and release-asset verification tests for FFmpeg encoder/muxer support.
- `tests/test_ffmpeg_runtime_workflow.py`: workflow structure tests for the FFmpeg runtime build/upload job.
- `tests/test_audio_output_policy.py`: pure and subprocess-monkeypatched tests for metadata parsing and policy resolution.
- `tests/test_editor_source_output_policy.py`: editor worker tests that verify generated filenames and render calls use resolved source-aware output policy.
- `tests/test_batch_source_output_policy.py`: batch transform tests that verify non-convert transforms use resolved source-aware output policy.

Modify:

- `release_assets.lock.json`: replace locked FFmpeg/ffprobe entries with capability-verified archives.
- `scripts/release_asset_verify.py`: run FFmpeg capability diagnostics as part of release-asset verification.
- `scripts/release_assets.py`, `scripts/release_assets_runtime_ops.py`, `scripts/release_assets_cli.py`, `scripts/release_assets_commands.py`: expose runtime capability checks in fetch/verify flows where needed.
- `addon/anki_audio_quick_editor/audio_formats.py`: add `source` as a persisted policy value while keeping concrete format helpers strict.
- `addon/anki_audio_quick_editor/audio_state.py`: default and normalize `output_format="source"`.
- `addon/anki_audio_quick_editor/config.schema.json`, `addon/anki_audio_quick_editor/config.json`, `addon/anki_audio_quick_editor/config_migration.py`: allow and default `source`.
- `contracts/communication.schema.json`, `addon/anki_audio_quick_editor/contracts_generated.py`, `settings_ui/src/lib/types.ts`: update generated contracts after schema changes.
- `settings_ui/src/lib/audio-operation-parameters.ts`, `settings_ui/src/lib/i18n.ts`, `settings_ui/src/settings/OutputFormatField.svelte`, `settings_ui/src/batch/BatchControls.svelte`, `settings_ui/src/editor-inline/SplitValueOptions.svelte`: expose and label `source` consistently.
- `addon/anki_audio_quick_editor/audio_commands.py`: replace final MP3-only command builders with policy-aware builders.
- `addon/anki_audio_quick_editor/audio_commands_runtime.py`: replace final MP3 encode builders; keep model prep commands unchanged.
- `addon/anki_audio_quick_editor/audio_rendering.py`: resolve output policy for standard, convert, region, pause, and default temp outputs.
- `addon/anki_audio_quick_editor/audio_pause_pipeline.py`, `addon/anki_audio_quick_editor/audio_pause_pipeline_steps.py`: make final pause artifact path and MIME policy-aware.
- `addon/anki_audio_quick_editor/audio_noise_reduction.py`, `addon/anki_audio_quick_editor/audio_noise_reduction_bundled.py`, `addon/anki_audio_quick_editor/audio_pitch_hum.py`: use generic final encode policy for special transforms.
- `addon/anki_audio_quick_editor/audio_processor.py`, `addon/anki_audio_quick_editor/audio_processor_rendering_portal.py`, `addon/anki_audio_quick_editor/audio_processor_runtime.py`: re-export and synchronize new policy-aware functions.
- `addon/anki_audio_quick_editor/editor_processing.py`, `addon/anki_audio_quick_editor/editor_region_delete_worker.py`, `addon/anki_audio_quick_editor/editor_special_transform_worker.py`, `addon/anki_audio_quick_editor/batch_operation_processing.py`: resolve final filename extension before rendering.
- Existing tests listed in `docs/ffmpeg-source-quality-analysis.md`: update MP3-only expectations to source-aware expectations.
- E2E tests in `e2e/test_audio_processing_ffmpeg.py`, `e2e/test_editor_deep_filter_workflow.py`, `e2e/test_editor_deep_filter_pause_workflow.py`, and helpers that glob `*__aqe_*.mp3`.

---

### Task 1: Tests For Format Policy Values

**Files:**
- Modify: `tests/test_audio_formats.py`
- Modify: `settings_ui/src/lib/audio-operation-parameters.ts`
- Modify: `settings_ui/tests/audio-operation-parameters.test.ts` if this file exists; otherwise add cases to the nearest existing settings UI test that covers `outputFormatOrDefault`.
- Test: `tests/test_audio_formats.py`
- Test: `settings_ui/tests`

- [ ] **Step 1: Change Python format tests before implementation**

Update `tests/test_audio_formats.py` so persisted settings accept `source` but concrete extension helpers reject unresolved `source`:

```python
def test_supported_formats_include_source_policy_and_concrete_targets() -> None:
    assert SUPPORTED_OUTPUT_FORMATS == ("source", "mp3", "m4a", "wav", "flac")
    assert DEFAULT_OUTPUT_FORMAT == "source"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("source", "source"),
        (" SOURCE ", "source"),
        ("mp3", "mp3"),
        ("M4A", "m4a"),
        ("ogg", "source"),
        ("wav", "wav"),
        ("flac", "flac"),
        (None, "source"),
        ("", "source"),
    ],
)
def test_normalize_output_format_accepts_source_policy(raw: object, expected: str) -> None:
    assert normalize_output_format(raw) == expected


@pytest.mark.parametrize("target", ["mp3", "M4A", "wav", "flac"])
def test_validate_target_format_accepts_only_concrete_targets(target: str) -> None:
    assert validate_target_format(target) == target.strip().lower()


@pytest.mark.parametrize("target", ["source", "ogg", "", None])
def test_validate_target_format_rejects_unresolved_or_unknown_targets(target: object) -> None:
    with pytest.raises(ValueError, match="Unsupported concrete audio output format"):
        validate_target_format(target)
```

- [ ] **Step 2: Change TypeScript output-format tests before implementation**

Add or update TypeScript assertions for the output-format helper:

```typescript
import { DEFAULT_OUTPUT_FORMAT, OUTPUT_FORMAT_VALUES, outputFormatOrDefault, formatOutputFormat } from "../src/lib/audio-operation-parameters";

test("output format values include source policy", () => {
  expect(DEFAULT_OUTPUT_FORMAT).toBe("source");
  expect(OUTPUT_FORMAT_VALUES).toEqual(["source", "mp3", "m4a", "wav", "flac"]);
});

test("outputFormatOrDefault falls back to source policy", () => {
  expect(outputFormatOrDefault("flac")).toBe("flac");
  expect(outputFormatOrDefault("source")).toBe("source");
  expect(outputFormatOrDefault("opus")).toBe("source");
});

test("source output format has a user-facing label", () => {
  expect(formatOutputFormat("source")).toBe("Same as source");
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_formats.py
```

Expected: FAIL because `SUPPORTED_OUTPUT_FORMATS` and `DEFAULT_OUTPUT_FORMAT` still use MP3-only defaults.

Run:

```bash
cd settings_ui && npm test -- --run
```

Expected: FAIL because `OUTPUT_FORMAT_VALUES` does not include `source` and the label is missing.

- [ ] **Step 4: Implement format value support**

Modify `addon/anki_audio_quick_editor/audio_formats.py`:

```python
OutputFormat = Literal["source", "mp3", "m4a", "wav", "flac"]
ConcreteOutputFormat = Literal["mp3", "m4a", "wav", "flac"]

SUPPORTED_OUTPUT_FORMATS: tuple[OutputFormat, ...] = ("source", "mp3", "m4a", "wav", "flac")
CONCRETE_OUTPUT_FORMATS: tuple[ConcreteOutputFormat, ...] = ("mp3", "m4a", "wav", "flac")
DEFAULT_OUTPUT_FORMAT: OutputFormat = "source"
```

Keep `normalize_output_format()` permissive for all `SUPPORTED_OUTPUT_FORMATS`. Change `validate_target_format()` to accept only `CONCRETE_OUTPUT_FORMATS` and raise:

```python
raise ValueError(f"Unsupported concrete audio output format: {value!r}")
```

Modify `settings_ui/src/lib/audio-operation-parameters.ts`:

```typescript
export const DEFAULT_OUTPUT_FORMAT = "source";
export const OUTPUT_FORMAT_VALUES = ["source", "mp3", "m4a", "wav", "flac"] as const;
```

Modify `settings_ui/src/lib/i18n.ts` to include:

```typescript
"settings.output_format.source": "Same as source",
"editor.split.option.output_format.source.description": "Keep the original file extension when this add-on can safely re-encode to it; otherwise use a compatible fallback.",
```

- [ ] **Step 5: Run focused tests to verify they pass**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_formats.py
```

Expected: PASS.

Run:

```bash
cd settings_ui && npm test -- --run
```

Expected: PASS for the added output-format helper tests; unrelated failures should be recorded before proceeding.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_formats.py settings_ui/src/lib/audio-operation-parameters.ts settings_ui/src/lib/i18n.ts tests/test_audio_formats.py settings_ui/tests
git commit -m "test: define source output format policy"
```

---

### Task 2: Tests For FFmpeg Runtime Capability Profile

**Files:**
- Create: `scripts/ffmpeg_runtime_capabilities.py`
- Create: `tests/test_ffmpeg_runtime_capabilities.py`
- Modify: `scripts/release_asset_common.py`
- Modify: `scripts/release_asset_verify.py`
- Modify: `scripts/release_assets.py`
- Modify: `scripts/release_assets_runtime_ops.py`
- Modify: `scripts/release_assets_cli.py`
- Modify: `scripts/release_assets_commands.py`
- Modify: `release_assets.lock.json`
- Test: `tests/test_ffmpeg_runtime_capabilities.py`
- Test: `tests/test_release_asset_fetch.py`
- Test: `tests/test_release_assets.py`

- [ ] **Step 1: Write capability parser and policy tests before implementation**

Create `tests/test_ffmpeg_runtime_capabilities.py` with tests for a reusable capability profile. The profile must cover the final-output formats that `source` preservation can choose:

```python
REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE = {
    "encoders": {
        "libmp3lame",
        "aac",
        "flac",
        "libvorbis",
        "libopus",
        "pcm_s16le",
        "pcm_s24le",
    },
    "muxers": {
        "mp3",
        "mp4",
        "adts",
        "wav",
        "flac",
        "ogg",
        "opus",
        "webm",
    },
}
```

Test these cases:

- A representative `ffmpeg -encoders`/`ffmpeg -muxers` output containing all required entries passes.
- Missing `libopus` fails with a message that names `.opus` and `.webm` preservation as blocked.
- Missing `libvorbis` fails with a message that names `.ogg`/`.oga` preservation as blocked.
- Missing `adts` fails with a message that names raw `.aac` preservation as blocked.
- Missing `pcm_s24le` fails with a message that names 24-bit WAV preservation as blocked.

- [ ] **Step 2: Write release verification tests before implementation**

Update release-asset tests so managed FFmpeg entries are not only checksum-verified:

```python
def test_validate_lock_requires_ffmpeg_capability_profile_for_release_ready_lock(...) -> None:
    lock["targets"]["macos-arm64"]["tools"]["ffmpeg"].pop("capability_profile", None)

    with pytest.raises(release_assets.ReleaseAssetError, match="capability profile"):
        release_assets.validate_lock(lock)
```

Add tests that `scripts.release_asset_verify.verify_assets(..., run_diagnostics=True)` invokes the FFmpeg capability checker only for the current host target. Cross-target binaries cannot be executed locally; their capabilities are enforced by the build/upload workflow before the lock is updated.

- [ ] **Step 3: Run focused tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_ffmpeg_runtime_capabilities.py tests/test_release_assets.py tests/test_release_asset_fetch.py
```

Expected: FAIL because the capability module and lock validation do not exist yet.

- [ ] **Step 4: Implement capability probing**

Create `scripts/ffmpeg_runtime_capabilities.py` with a small public API:

```python
PROFILE_NAME = "aqe-source-audio-v1"

def parse_ffmpeg_table(output: str) -> set[str]: ...
def collect_ffmpeg_capabilities(ffmpeg_path: Path) -> FfmpegCapabilities: ...
def validate_required_audio_output_capabilities(capabilities: FfmpegCapabilities) -> CapabilityReport: ...
def verify_ffmpeg_binary(ffmpeg_path: Path) -> None: ...
```

Implementation requirements:

- Run `ffmpeg -hide_banner -encoders` and `ffmpeg -hide_banner -muxers`.
- Parse capability names conservatively from FFmpeg table output rather than relying on exact spacing.
- Return all missing encoders and muxers in one report.
- Keep the module independent of add-on runtime imports so it can run in GitHub Actions before packaging.
- Provide a CLI:

```bash
python3 scripts/ffmpeg_runtime_capabilities.py --ffmpeg .release-assets/bin/macos-arm64/ffmpeg
```

Expected CLI behavior: exit 0 when the binary satisfies `aqe-source-audio-v1`; exit nonzero and print missing capabilities otherwise.

- [ ] **Step 5: Integrate with release asset validation**

Modify release asset code:

- `validate_lock()` requires `capability_profile: "aqe-source-audio-v1"` on every release-ready `ffmpeg` entry.
- `fetch_ffmpeg()` runs the capability check after extracting `ffmpeg` when the fetched target is executable on the current host.
- `verify_assets(..., run_diagnostics=True)` appends an FFmpeg capability report for the current host target.
- `verify_assets(..., run_diagnostics=False)` remains checksum-only so cross-target lock validation stays fast and deterministic.

Add or update `release_assets.lock.json` FFmpeg entries:

```json
"capability_profile": "aqe-source-audio-v1"
```

Do not add this field to `ffprobe`; `ffprobe` still needs version/checksum diagnostics, but encoder/muxer support belongs to `ffmpeg`.

- [ ] **Step 6: Run focused tests to verify they pass**

Run:

```bash
python3 scripts/dev.py test tests/test_ffmpeg_runtime_capabilities.py tests/test_release_assets.py tests/test_release_asset_fetch.py
```

Expected: PASS.

- [ ] **Step 7: Verify the current host FFmpeg cache when available**

If the locked current-host FFmpeg archive is already present or can be fetched, run:

```bash
python3 scripts/release_assets.py fetch-ffmpeg --target current
python3 scripts/release_assets.py verify --target current --diagnostics
```

Expected: PASS and report that the current FFmpeg binary satisfies `aqe-source-audio-v1`.

- [ ] **Step 8: Commit**

```bash
git add scripts/ffmpeg_runtime_capabilities.py scripts/release_asset_common.py scripts/release_asset_verify.py scripts/release_assets.py scripts/release_assets_runtime_ops.py scripts/release_assets_cli.py scripts/release_assets_commands.py release_assets.lock.json tests/test_ffmpeg_runtime_capabilities.py tests/test_release_assets.py tests/test_release_asset_fetch.py
git commit -m "test: enforce ffmpeg runtime audio capabilities"
```

---

### Task 3: FFmpeg Runtime Build And Release Upload Workflow

**Files:**
- Create: `.github/workflows/build-ffmpeg-runtime.yml`
- Create: `scripts/ffmpeg_runtime/build_macos.sh`
- Create: `tests/test_ffmpeg_runtime_workflow.py`
- Modify: `release_assets.lock.json`
- Modify: `scripts/release_assets.py` only if lock-update helpers are needed.
- Test: `tests/test_ffmpeg_runtime_workflow.py`
- Test: `tests/test_release.py`

- [ ] **Step 1: Write workflow structure tests before implementation**

Create `tests/test_ffmpeg_runtime_workflow.py` that reads `.github/workflows/build-ffmpeg-runtime.yml` and asserts:

- It is a manual `workflow_dispatch` workflow with inputs for `release_tag`, `ffmpeg_ref`, and `force_custom_build`.
- The matrix includes current runtime targets: `windows-x86_64`, `macos-arm64`, and `macos-x86_64`.
- Windows uses BtbN prebuilt assets by default and has a custom-build branch for fallback.
- macOS targets use the repo-owned macOS build script because BtbN does not publish macOS targets.
- Every target runs `python3 scripts/ffmpeg_runtime_capabilities.py` before uploading artifacts.
- Uploaded release assets are combined per target and contain both `ffmpeg` and `ffprobe`.

- [ ] **Step 2: Run workflow tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_ffmpeg_runtime_workflow.py
```

Expected: FAIL because the workflow does not exist.

- [ ] **Step 3: Implement the build/download strategy**

Create `.github/workflows/build-ffmpeg-runtime.yml` as a manual release-maintainer workflow.

Use this source decision tree:

- `windows-x86_64`: Prefer a pinned BtbN `win64` build (`gpl` or `gpl-shared`) when the downloaded archive passes `aqe-source-audio-v1`.
- Future `linux-x86_64` and `linux-arm64` targets, if added later: map to BtbN `linux64` and `linuxarm64` and use the same capability gate.
- `macos-arm64` and `macos-x86_64`: Build in GitHub Actions because BtbN's published targets are Windows and Linux only.
- Any target with `force_custom_build=true`: checkout `BtbN/FFmpeg-Builds` and run its build scripts/configuration where the target is supported; for macOS, run `scripts/ffmpeg_runtime/build_macos.sh` with the same capability profile.

The workflow should produce one archive per runtime target:

```text
aqe-ffmpeg-runtime-<ffmpeg-ref>-<target>.zip
```

Archive layout:

```text
ffmpeg
ffprobe
```

Use `.exe` suffixes inside the archive for Windows:

```text
ffmpeg.exe
ffprobe.exe
```

- [ ] **Step 4: Implement macOS build script**

Create `scripts/ffmpeg_runtime/build_macos.sh` with explicit configure flags for the required profile:

```bash
--enable-gpl
--enable-libmp3lame
--enable-libopus
--enable-libvorbis
--enable-static
--disable-shared
```

Also ensure native FFmpeg components required for `aac`, `flac`, `wav`, `mp4`, `adts`, `ogg`, `opus`, and `webm` remain enabled. The script should write `ffmpeg` and `ffprobe` into a target-specific staging directory, then run:

```bash
python3 scripts/ffmpeg_runtime_capabilities.py --ffmpeg "$STAGING_DIR/ffmpeg"
```

- [ ] **Step 5: Upload target archives to GitHub releases**

The workflow must upload archives to the requested release tag:

```bash
gh release upload "$RELEASE_TAG" "dist/ffmpeg-runtime/aqe-ffmpeg-runtime-${FFMPEG_REF}-${TARGET}.zip" --clobber
```

Store the archive SHA-256 and binary SHA-256 values in the workflow summary so the maintainer can update `release_assets.lock.json` deterministically.

- [ ] **Step 6: Update the lock file to consume the new archives**

After a workflow run produces release assets, update `release_assets.lock.json` for `ffmpeg` and `ffprobe`:

```json
"download_url": "https://github.com/ganqqwerty/anki-audio-tools/releases/download/<tag>/aqe-ffmpeg-runtime-<ffmpeg-ref>-<target>.zip",
"download_sha256": "<archive sha256>",
"archive_member": "ffmpeg",
"sha256": "<binary sha256>",
"capability_profile": "aqe-source-audio-v1"
```

For `ffprobe`, use the same `download_url` and `download_sha256`, but set `archive_member` to `ffprobe` or `ffprobe.exe` and set the `sha256` to the `ffprobe` binary hash.

- [ ] **Step 7: Verify release-asset consumption from the updated lock**

Run on each available local host target:

```bash
python3 scripts/release_assets.py fetch-ffmpeg --target current
python3 scripts/release_assets.py verify --target current --diagnostics
```

Fetch and verify all target archives without diagnostics:

```bash
python3 scripts/release_assets.py fetch-ffmpeg --target all
python3 scripts/release_assets.py verify --target all
```

Expected: PASS. Do not mark release-ready until all target archives are downloadable and checksum-valid.

- [ ] **Step 8: Commit**

```bash
git add .github/workflows/build-ffmpeg-runtime.yml scripts/ffmpeg_runtime/build_macos.sh release_assets.lock.json tests/test_ffmpeg_runtime_workflow.py tests/test_release.py
git commit -m "build: add ffmpeg runtime release workflow"
```

---

### Task 4: Tests For Metadata Probing And Output Policy Resolution

**Files:**
- Create: `tests/test_audio_output_policy.py`
- Create: `addon/anki_audio_quick_editor/audio_output_policy.py`
- Modify: `addon/anki_audio_quick_editor/audio_processor.py`
- Modify: `addon/anki_audio_quick_editor/audio_processor_runtime.py`
- Test: `tests/test_audio_output_policy.py`

- [ ] **Step 1: Write pure policy tests**

Create `tests/test_audio_output_policy.py` with metadata-only tests:

```python
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_output_policy import (
    AudioSourceMetadata,
    codec_args_for_output_policy,
    mime_type_for_output_format,
    probe_audio_metadata,
    resolve_output_policy_from_metadata,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig


def metadata(
    *,
    filename: str = "clip.mp3",
    codec_name: str = "mp3",
    sample_rate: int = 48000,
    channels: int = 2,
    bit_rate: int | None = 128000,
    bits_per_raw_sample: int | None = None,
) -> AudioSourceMetadata:
    return AudioSourceMetadata(
        path=Path(filename),
        visible_format=Path(filename).suffix.lower().lstrip(".") or None,
        codec_name=codec_name,
        sample_rate=sample_rate,
        channels=channels,
        bit_rate=bit_rate,
        bits_per_raw_sample=bits_per_raw_sample,
        sample_fmt=None,
    )


def test_source_policy_resolves_supported_mp3_source_characteristics() -> None:
    policy = resolve_output_policy_from_metadata(metadata(), requested_format="source")

    assert policy.output_format == "mp3"
    assert policy.extension == ".mp3"
    assert policy.mime_type == "audio/mpeg"
    assert codec_args_for_output_policy(policy) == (
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-ar",
        "48000",
        "-ac",
        "2",
    )


def test_source_policy_resolves_m4a_source_to_aac_with_source_bitrate() -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.m4a", codec_name="aac", sample_rate=44100, channels=1, bit_rate=96000),
        requested_format="source",
    )

    assert policy.output_format == "m4a"
    assert codec_args_for_output_policy(policy) == (
        "-codec:a",
        "aac",
        "-b:a",
        "96k",
        "-ar",
        "44100",
        "-ac",
        "1",
    )


def test_source_policy_preserves_lossless_source_format() -> None:
    wav_policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.wav", codec_name="pcm_s24le", bits_per_raw_sample=24, bit_rate=None),
        requested_format="source",
    )
    flac_policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.flac", codec_name="flac", bits_per_raw_sample=24, bit_rate=None),
        requested_format="source",
    )

    assert codec_args_for_output_policy(wav_policy) == ("-codec:a", "pcm_s24le", "-ar", "48000", "-ac", "2")
    assert codec_args_for_output_policy(flac_policy) == ("-codec:a", "flac", "-compression_level", "5", "-ar", "48000", "-ac", "2")


def test_source_policy_preserves_ogg_vorbis_extension() -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.ogg", codec_name="vorbis", sample_rate=44100, channels=2, bit_rate=112000),
        requested_format="source",
    )

    assert policy.output_format == "ogg"
    assert policy.extension == ".ogg"
    assert codec_args_for_output_policy(policy) == (
        "-codec:a",
        "libvorbis",
        "-b:a",
        "112k",
        "-ar",
        "44100",
        "-ac",
        "2",
    )


@pytest.mark.parametrize(
    ("filename", "codec_name", "expected_format", "expected_extension", "expected_codec"),
    [
        ("clip.oga", "vorbis", "oga", ".oga", "libvorbis"),
        ("clip.opus", "opus", "opus", ".opus", "libopus"),
        ("clip.webm", "opus", "webm", ".webm", "libopus"),
        ("clip.aac", "aac", "aac", ".aac", "aac"),
    ],
)
def test_source_policy_preserves_common_anki_audio_extensions(
    filename: str,
    codec_name: str,
    expected_format: str,
    expected_extension: str,
    expected_codec: str,
) -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename=filename, codec_name=codec_name, sample_rate=48000, channels=1, bit_rate=96000),
        requested_format="source",
    )

    assert policy.output_format == expected_format
    assert policy.extension == expected_extension
    assert codec_args_for_output_policy(policy)[0:2] == ("-codec:a", expected_codec)


def test_source_policy_falls_back_to_mp3_for_unknown_visible_format() -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.aiff", codec_name="pcm_s16be", sample_rate=44100, channels=2, bit_rate=None),
        requested_format="source",
    )

    assert policy.output_format == "mp3"
    assert policy.extension == ".mp3"
    assert "unsupported source extension: aiff" in policy.reason


def test_concrete_requested_format_overrides_source_extension() -> None:
    policy = resolve_output_policy_from_metadata(metadata(filename="clip.wav", codec_name="pcm_s16le"), requested_format="flac")

    assert policy.output_format == "flac"
    assert policy.extension == ".flac"
    assert codec_args_for_output_policy(policy) == ("-codec:a", "flac", "-compression_level", "5", "-ar", "48000", "-ac", "2")
```

- [ ] **Step 2: Write ffprobe metadata probing tests**

Add subprocess-monkeypatched tests to the same file:

```python
def test_probe_audio_metadata_reads_first_audio_stream(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffprobe", lambda _path: Path("/bin/ffprobe"))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool, **_kwargs: object) -> SimpleNamespace:
        calls.append(cmd)
        return SimpleNamespace(
            returncode=0,
            stdout=(
                '{"streams":[{"codec_type":"audio","codec_name":"aac","sample_rate":"44100",'
                '"channels":1,"bit_rate":"96000","bits_per_raw_sample":"0","sample_fmt":"fltp"}],'
                '"format":{"format_name":"mov,mp4,m4a,3gp,3g2,mj2","bit_rate":"100000"}}'
            ),
            stderr="",
        )

    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.subprocess.run", fake_run)

    result = probe_audio_metadata(tmp_path / "clip.m4a", AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"))

    assert result.codec_name == "aac"
    assert result.sample_rate == 44100
    assert result.channels == 1
    assert result.bit_rate == 96000
    assert result.visible_format == "m4a"
    assert calls == [
        [
            "/bin/ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(tmp_path / "clip.m4a"),
        ]
    ]


def test_probe_audio_metadata_raises_clear_error_for_missing_audio_stream(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffprobe", lambda _path: Path("/bin/ffprobe"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_output_policy.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout='{"streams":[],"format":{}}', stderr=""),
    )

    with pytest.raises(Exception, match="Could not inspect audio stream metadata"):
        probe_audio_metadata(tmp_path / "clip.mp3", AudioProcessingConfig())
```

- [ ] **Step 3: Run new policy tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_output_policy.py
```

Expected: FAIL because `audio_output_policy.py` does not exist.

- [ ] **Step 4: Implement `audio_output_policy.py`**

Create `addon/anki_audio_quick_editor/audio_output_policy.py` with these public objects:

```python
@dataclass(frozen=True)
class AudioSourceMetadata:
    path: Path
    visible_format: str | None
    codec_name: str | None
    sample_rate: int | None
    channels: int | None
    bit_rate: int | None
    bits_per_raw_sample: int | None
    sample_fmt: str | None


@dataclass(frozen=True)
class AudioOutputPolicy:
    output_format: str
    extension: str
    mime_type: str
    codec_args: tuple[str, ...]
    reason: str
```

Implement:

```python
def probe_audio_metadata(source_path: Path, config: AudioProcessingConfig) -> AudioSourceMetadata: ...
def resolve_output_policy(source_path: Path, config: AudioProcessingConfig, requested_format: object | None = None) -> AudioOutputPolicy: ...
def resolve_output_policy_from_metadata(metadata: AudioSourceMetadata, requested_format: object) -> AudioOutputPolicy: ...
def codec_args_for_output_policy(policy: AudioOutputPolicy) -> tuple[str, ...]: ...
def mime_type_for_output_format(output_format: str) -> str: ...
```

Use these deterministic encoder rules:

- MP3: `("-codec:a", "libmp3lame", "-b:a", "<source-or-floor>k", "-ar", sample_rate, "-ac", channels)`.
- M4A: `("-codec:a", "aac", "-b:a", "<source-or-floor>k", "-ar", sample_rate, "-ac", channels)`.
- AAC: `("-codec:a", "aac", "-b:a", "<source-or-floor>k", "-ar", sample_rate, "-ac", channels, "-f", "adts")`, preserving `.aac`.
- WAV: choose `pcm_s24le` when `bits_per_raw_sample >= 24`, otherwise `pcm_s16le`.
- FLAC: `("-codec:a", "flac", "-compression_level", "5", "-ar", sample_rate, "-ac", channels)`.
- OGG/OGA with Vorbis source: `("-codec:a", "libvorbis", "-b:a", "<source-or-floor>k", "-ar", sample_rate, "-ac", channels)`, preserving `.ogg` or `.oga`.
- OGG/OGA with Opus source: `("-codec:a", "libopus", "-b:a", "<source-or-floor>k", "-ar", sample_rate, "-ac", channels)`, preserving `.ogg` or `.oga`.
- OPUS: `("-codec:a", "libopus", "-b:a", "<source-or-floor>k", "-ar", sample_rate, "-ac", channels)`, preserving `.opus`.
- WEBM: `("-codec:a", "libopus", "-b:a", "<source-or-floor>k", "-ar", sample_rate, "-ac", channels)`, preserving `.webm`.
- Bitrate floor: 96 kbps for lossy output when no source bitrate is available or source bitrate is below 96 kbps.
- Bitrate ceiling: 320 kbps.
- Omit `-ar` and `-ac` only when metadata values are missing or invalid.
- Fall back to MP3 only for unknown/unmapped extensions or source codec/container combinations that are not safe to write.

- [ ] **Step 5: Re-export and synchronize the policy helpers**

Modify `addon/anki_audio_quick_editor/audio_processor.py` to expose:

```python
from .audio_output_policy import (
    AudioOutputPolicy,
    AudioSourceMetadata,
    codec_args_for_output_policy,
    probe_audio_metadata,
    resolve_output_policy,
    resolve_output_policy_from_metadata,
)
```

No runtime sync is needed for pure functions, but if tests monkeypatch through `audio_processor`, add sync wiring in `audio_processor_runtime.py` only for modules that call the helpers indirectly.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_output_policy.py tests/test_audio_formats.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_output_policy.py addon/anki_audio_quick_editor/audio_processor.py addon/anki_audio_quick_editor/audio_processor_runtime.py tests/test_audio_output_policy.py
git commit -m "feat: add source audio output policy"
```

---

### Task 5: Tests And Implementation For Policy-Aware FFmpeg Command Builders

**Files:**
- Modify: `tests/test_audio_commands.py`
- Modify: `tests/test_audio_noise_commands.py`
- Modify: `addon/anki_audio_quick_editor/audio_commands.py`
- Modify: `addon/anki_audio_quick_editor/audio_commands_runtime.py`
- Test: `tests/test_audio_commands.py`
- Test: `tests/test_audio_noise_commands.py`

- [ ] **Step 1: Update command-builder tests first**

In `tests/test_audio_commands.py`, replace MP3-only render expectations with a policy fixture:

```python
from anki_audio_quick_editor.audio_output_policy import AudioOutputPolicy


def policy(
    *,
    output_format: str = "flac",
    extension: str = ".flac",
    mime_type: str = "audio/flac",
    codec_args: tuple[str, ...] = ("-codec:a", "flac", "-compression_level", "5", "-ar", "48000", "-ac", "2"),
) -> AudioOutputPolicy:
    return AudioOutputPolicy(
        output_format=output_format,
        extension=extension,
        mime_type=mime_type,
        codec_args=codec_args,
        reason="test",
    )


def test_build_filtered_audio_command_uses_policy_codec_args(tmp_path: Path) -> None:
    command = build_filtered_audio_command(
        Path("/bin/ffmpeg"),
        tmp_path / "source.wav",
        "atrim=start=0.100:end=0.900",
        tmp_path / "edited.flac",
        policy(),
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter:a",
        "atrim=start=0.100:end=0.900",
        "-codec:a",
        "flac",
        "-compression_level",
        "5",
        "-ar",
        "48000",
        "-ac",
        "2",
        str(tmp_path / "edited.flac"),
    )
```

Update region and filter-complex command tests in the same style:

```python
def test_build_region_filter_command_uses_policy_codec_args(tmp_path: Path) -> None:
    command = build_region_filter_command(
        Path("/bin/ffmpeg"),
        tmp_path / "source.wav",
        "[0:a]atrim=end=0.500,asetpts=PTS-STARTPTS[out]",
        tmp_path / "region.m4a",
        policy(output_format="m4a", extension=".m4a", mime_type="audio/mp4", codec_args=("-codec:a", "aac", "-b:a", "128k")),
    )

    assert command[-5:] == ("-codec:a", "aac", "-b:a", "128k", str(tmp_path / "region.m4a"))
```

In `tests/test_audio_noise_commands.py`, replace `build_mp3_encode_command` expectations:

```python
def test_build_audio_encode_command_uses_policy_codec_args(tmp_path: Path) -> None:
    encode_policy = AudioOutputPolicy(
        output_format="m4a",
        extension=".m4a",
        mime_type="audio/mp4",
        codec_args=("-codec:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "1"),
        reason="test",
    )

    assert build_audio_encode_command(Path("/bin/ffmpeg"), tmp_path / "cleaned.wav", tmp_path / "cleaned.m4a", encode_policy) == (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "cleaned.wav"),
        "-vn",
        "-codec:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "48000",
        "-ac",
        "1",
        str(tmp_path / "cleaned.m4a"),
    )
```

- [ ] **Step 2: Run command tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_commands.py tests/test_audio_noise_commands.py
```

Expected: FAIL because `build_filtered_audio_command`, `build_region_filter_command`, and `build_audio_encode_command` do not exist.

- [ ] **Step 3: Implement policy-aware command builders**

Modify `addon/anki_audio_quick_editor/audio_commands.py`:

```python
def build_filtered_audio_command(
    ffmpeg_path: Path,
    source_path: Path,
    filters: str,
    output_path: Path,
    output_policy: AudioOutputPolicy,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter:a",
        filters,
        *output_policy.codec_args,
        str(output_path),
    )
```

Add:

```python
def build_filter_complex_render_command(..., output_policy: AudioOutputPolicy) -> tuple[str, ...]
def build_region_filter_command(..., output_policy: AudioOutputPolicy) -> tuple[str, ...]
def build_convert_audio_command(..., output_policy: AudioOutputPolicy) -> tuple[str, ...]
```

Keep compatibility wrappers only where existing callers are migrated later in this plan. Compatibility wrappers must call the policy-aware builders with an explicit MP3 policy, not duplicate MP3 tuples inline.

Modify `addon/anki_audio_quick_editor/audio_commands_runtime.py`:

```python
def build_audio_encode_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
    output_policy: AudioOutputPolicy,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        *output_policy.codec_args,
        str(output_path),
    )
```

For RNNoise raw output, add:

```python
def build_raw_pcm_encode_command(
    ffmpeg_path: Path,
    source_raw_path: Path,
    output_path: Path,
    output_policy: AudioOutputPolicy,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-f",
        "s16le",
        "-ar",
        "48000",
        "-ac",
        "1",
        "-i",
        str(source_raw_path),
        "-vn",
        *output_policy.codec_args,
        str(output_path),
    )
```

- [ ] **Step 4: Run command tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_commands.py tests/test_audio_noise_commands.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_commands.py addon/anki_audio_quick_editor/audio_commands_runtime.py tests/test_audio_commands.py tests/test_audio_noise_commands.py
git commit -m "feat: make ffmpeg command builders output-policy aware"
```

---

### Task 6: Tests And Implementation For Core Renderers

**Files:**
- Modify: `tests/test_audio_rendering.py`
- Modify: `tests/test_audio_rendering_convert.py`
- Modify: `tests/test_audio_rendering_regions.py`
- Modify: `tests/test_audio_playback_rendering.py`
- Modify: `addon/anki_audio_quick_editor/audio_rendering.py`
- Modify: `addon/anki_audio_quick_editor/audio_processor_rendering_portal.py`
- Test: focused rendering tests

- [ ] **Step 1: Update standard render tests first**

In `tests/test_audio_rendering.py`, update `test_render_audio_uses_expected_ffmpeg_invocation` so `render_audio` probes source policy and writes a FLAC path when source is FLAC:

```python
def test_render_audio_uses_source_output_policy_for_supported_source(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([1000, 825])
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.build_audio_filters", lambda *_args: "atrim=start=0.100:end=0.900")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_rendering.resolve_output_policy",
        lambda *_args, **_kwargs: AudioOutputPolicy(
            output_format="flac",
            extension=".flac",
            mime_type="audio/flac",
            codec_args=("-codec:a", "flac", "-compression_level", "5", "-ar", "48000", "-ac", "2"),
            reason="test",
        ),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "edited.flac"
    result = render_audio(
        tmp_path / "source.flac",
        AudioEditState("source.flac", left_trim_ms=100),
        AudioProcessingConfig(output_format="source"),
        output_path=output,
        on_command=commands.append,
    )

    assert result.output_path == output
    assert calls[0][0][-8:] == ["flac", "-compression_level", "5", "-ar", "48000", "-ac", "2", str(output)]
    assert commands[0][-8:] == ("flac", "-compression_level", "5", "-ar", "48000", "-ac", "2", str(output))
```

- [ ] **Step 2: Update convert and region tests first**

In `tests/test_audio_rendering_convert.py`, assert convert passes a resolved policy rather than fixed format args:

```python
def test_render_converted_audio_uses_requested_concrete_policy(monkeypatch, tmp_path: Path) -> None:
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_rendering.resolve_output_policy",
        lambda _source, _config, requested_format=None: AudioOutputPolicy(
            output_format="m4a",
            extension=".m4a",
            mime_type="audio/mp4",
            codec_args=("-codec:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "1"),
            reason=f"requested {requested_format}",
        ),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    render_converted_audio(
        tmp_path / "source.wav",
        AudioProcessingConfig(output_format="source"),
        "m4a",
        output_path=tmp_path / "converted.m4a",
        on_command=commands.append,
    )

    assert commands[0][-8:] == ("aac", "-b:a", "160k", "-ar", "44100", "-ac", "1", str(tmp_path / "converted.m4a"))
```

In `tests/test_audio_rendering_regions.py`, update region command expectations to use a FLAC or M4A policy.

- [ ] **Step 3: Keep playback segment temp MP3 intentional**

In `tests/test_audio_playback_rendering.py`, rename MP3 expectations to make the exception explicit:

```python
def test_render_playback_segment_intentionally_uses_mp3_temp_policy(monkeypatch, tmp_path: Path) -> None:
    ...
    assert "libmp3lame" in command
    assert output.suffix == ".mp3"
```

- [ ] **Step 4: Run focused renderer tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_rendering.py tests/test_audio_rendering_convert.py tests/test_audio_rendering_regions.py tests/test_audio_playback_rendering.py
```

Expected: FAIL because renderers still call MP3-only builders and do not resolve output policy.

- [ ] **Step 5: Implement renderer policy resolution**

Modify `addon/anki_audio_quick_editor/audio_rendering.py`:

- Resolve `output_policy = resolve_output_policy(source_path, config, requested_format=config.output_format)` in `render_audio`.
- Use `output_policy.extension` for default temp suffix.
- Pass `output_policy` to `build_filtered_audio_command`.
- Resolve concrete target policy in `render_converted_audio` using `requested_format=target_format`.
- Resolve and pass policy in `_render_region_filter_complex`.
- Keep `render_playback_segment` on an explicit MP3 temp policy, for example `playback_output_policy()`, so this exception is not hidden.

Modify `addon/anki_audio_quick_editor/audio_processor_rendering_portal.py` to keep facade signatures stable while forwarding policy-aware behavior.

- [ ] **Step 6: Run focused renderer tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_rendering.py tests/test_audio_rendering_convert.py tests/test_audio_rendering_regions.py tests/test_audio_playback_rendering.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_rendering.py addon/anki_audio_quick_editor/audio_processor_rendering_portal.py tests/test_audio_rendering.py tests/test_audio_rendering_convert.py tests/test_audio_rendering_regions.py tests/test_audio_playback_rendering.py
git commit -m "feat: resolve output policy in core renderers"
```

---

### Task 7: Tests And Implementation For Editor And Batch Final Filenames

**Files:**
- Create: `tests/test_editor_source_output_policy.py`
- Create: `tests/test_batch_source_output_policy.py`
- Modify: `addon/anki_audio_quick_editor/editor_processing.py`
- Modify: `addon/anki_audio_quick_editor/editor_region_delete_worker.py`
- Modify: `addon/anki_audio_quick_editor/editor_special_transform_worker.py`
- Modify: `addon/anki_audio_quick_editor/batch_operation_processing.py`
- Modify: `addon/anki_audio_quick_editor/audio_rendering.py`
- Test: new editor and batch policy tests

- [ ] **Step 1: Add editor filename policy tests first**

Create `tests/test_editor_source_output_policy.py` with worker-level tests that avoid Qt:

```python
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_output_policy import AudioOutputPolicy
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_processing import _run_standard_render_worker
from anki_audio_quick_editor.editor_session import EditorSession, begin_processing_guard


def test_standard_editor_worker_names_output_from_resolved_source_policy(tmp_path: Path) -> None:
    media = tmp_path / "clip.flac"
    media.write_bytes(b"source")
    session = EditorSession(state=AudioEditState("clip.flac"), current_filename="clip.flac", field_index=0)
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.flac")
    output_policy = AudioOutputPolicy("flac", ".flac", "audio/flac", ("-codec:a", "flac"), "test")
    render_calls: list[Path] = []

    deps = SimpleNamespace(
        resolve_output_policy=MagicMock(return_value=output_policy),
        make_output_filename=MagicMock(return_value="clip__aqe_test.flac"),
        temp_final_path=lambda name: tmp_path / name,
        format_ffmpeg_command=lambda command: " ".join(command),
        set_busy=MagicMock(),
        main=lambda _editor, fn: fn(),
        render_audio=lambda _source, _state, _config, *, output_path, **_kwargs: render_calls.append(output_path),
        replace_current_field_after_render=MagicMock(),
        artifact_root=lambda _editor: None,
    )

    _run_standard_render_worker(
        object(),
        session,
        media,
        AudioEditState("clip.flac", volume_db=3),
        AudioProcessingConfig(output_format="source"),
        guard,
        "render-test",
        deps,
    )

    deps.resolve_output_policy.assert_called_once()
    deps.make_output_filename.assert_called_once_with("clip.flac", output_format="flac")
    assert render_calls == [tmp_path / "clip__aqe_test.flac"]
```

Add equivalent tests for `editor_region_delete_worker.run_region_delete_worker` and `editor_special_transform_worker.run_special_transform_worker` using the same policy fixture.

- [ ] **Step 2: Add batch filename policy tests first**

Create `tests/test_batch_source_output_policy.py`:

```python
from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_operations import OP_VOLUME_UP
from anki_audio_quick_editor.audio_output_policy import AudioOutputPolicy
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operation_types import BatchNoteSnapshot, BatchRunRequest
from anki_audio_quick_editor.batch_operations import process_note_batch_operation


def test_batch_transform_uses_source_policy_extension(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "clip.flac"
    source.write_bytes(b"source")
    written: list[tuple[str, bytes]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operation_processing.resolve_output_policy",
        lambda *_args, **_kwargs: AudioOutputPolicy("flac", ".flac", "audio/flac", ("-codec:a", "flac"), "test"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operation_processing.make_output_filename",
        lambda filename, *, output_format="source": f"{Path(filename).stem}__aqe_test.{output_format}",
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_audio",
        lambda *_args, output_path, **_kwargs: output_path.write_bytes(b"rendered"),
    )

    result = process_note_batch_operation(
        BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.flac]"}),
        request=BatchRunRequest(
            operation=OP_VOLUME_UP,
            source_field="Audio",
            target_field=None,
            note_ids=(10,),
            parameters=AudioOperationParameters(),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(output_format="source"),
        media_writer=lambda name, data: written.append((name, data)) or name,
    )

    assert result.status == "written"
    assert result.written_filename == "clip__aqe_test.flac"
    assert "[sound:clip__aqe_test.flac]" in result.target_html
    assert written == [("clip__aqe_test.flac", b"rendered")]
```

- [ ] **Step 3: Run new worker tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_source_output_policy.py tests/test_batch_source_output_policy.py
```

Expected: FAIL because dependencies and workers do not resolve output policy before `make_output_filename`.

- [ ] **Step 4: Implement filename policy in workers**

Modify standard, region, special-transform, and batch workers so each flow does this before creating the temp path:

```python
output_policy = deps.resolve_output_policy(source_path, config, requested_format=config.output_format)
desired_name = deps.make_output_filename(source_path.name, output_format=output_policy.output_format)
output_path = deps.temp_final_path(desired_name)
```

For convert, keep the existing explicit target format flow:

```python
desired_name = deps.make_output_filename(current_path.name, output_format=target_format)
```

Add `resolve_output_policy` to editor and batch dependency namespaces in `editor_dependencies.py` and the relevant callback dependency factories.

- [ ] **Step 5: Run worker tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_source_output_policy.py tests/test_batch_source_output_policy.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_processing.py addon/anki_audio_quick_editor/editor_region_delete_worker.py addon/anki_audio_quick_editor/editor_special_transform_worker.py addon/anki_audio_quick_editor/batch_operation_processing.py addon/anki_audio_quick_editor/editor_dependencies.py tests/test_editor_source_output_policy.py tests/test_batch_source_output_policy.py
git commit -m "feat: use source output policy for generated media names"
```

---

### Task 8: Tests And Implementation For Pause Pipeline Final Output

**Files:**
- Modify: `tests/test_audio_pause_pipeline.py`
- Modify: `addon/anki_audio_quick_editor/audio_pause_pipeline.py`
- Modify: `addon/anki_audio_quick_editor/audio_pause_pipeline_steps.py`
- Test: `tests/test_audio_pause_pipeline.py`

- [ ] **Step 1: Update pause pipeline tests first**

Change tests that pass `final_copy_path=run_dir / "07_final_output.mp3"` to pass an output policy and assert `.flac` when source policy resolves FLAC:

```python
def test_pause_pipeline_final_artifact_uses_output_policy(monkeypatch, tmp_path: Path) -> None:
    output_policy = AudioOutputPolicy("flac", ".flac", "audio/flac", ("-codec:a", "flac"), "test")
    ...
    result = _render_pause_removal_audio(
        state,
        config,
        Path("/bin/ffmpeg"),
        tmp_path / "out.flac",
        None,
        ...,
        final_copy_path=run_dir / "07_final_output.flac",
        output_policy=output_policy,
        ...
    )
    assert (run_dir / "07_final_output.flac").is_file()
    assert manifest["final_output"]["artifact_path"].endswith("07_final_output.flac")
    assert any(artifact["mime_type"] == "audio/flac" for artifact in manifest["artifacts"])
```

- [ ] **Step 2: Run pause tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_pause_pipeline.py
```

Expected: FAIL because pause pipeline still hardcodes MP3 final artifact path and MIME.

- [ ] **Step 3: Implement policy-aware pause final output**

Modify `audio_pause_pipeline.py`:

```python
output_policy = resolve_output_policy(source_path, config, requested_format=config.output_format)
final_copy_path = run_dir / f"07_final_output{output_policy.extension}"
```

Pass `output_policy` into `_render_pause_removal_audio`.

Modify `audio_pause_pipeline_steps.py`:

```python
render_cmd = build_filter_complex_render_command(
    ffmpeg_path,
    working_original,
    filter_script_path,
    output_path,
    output_policy,
)
artifacts.append(_artifact_record("final_output", final_copy_path, output_policy.mime_type))
```

- [ ] **Step 4: Run pause tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_pause_pipeline.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_pause_pipeline.py addon/anki_audio_quick_editor/audio_pause_pipeline_steps.py tests/test_audio_pause_pipeline.py
git commit -m "feat: make pause pipeline final output policy-aware"
```

---

### Task 9: Tests And Implementation For Denoise And Pitch Final Encode

**Files:**
- Modify: `tests/test_audio_noise_reduction.py`
- Modify: `tests/test_audio_rnnoise.py`
- Modify: `tests/test_audio_dpdfnet.py`
- Modify: `tests/test_audio_voice_only.py`
- Modify: `tests/test_audio_pitch_hum.py`
- Modify: `addon/anki_audio_quick_editor/audio_noise_reduction.py`
- Modify: `addon/anki_audio_quick_editor/audio_noise_reduction_bundled.py`
- Modify: `addon/anki_audio_quick_editor/audio_pitch_hum.py`
- Test: denoise and pitch tests

- [ ] **Step 1: Update denoise encode tests first**

Replace assertions like:

```python
assert calls[2][-5:] == ["-codec:a", "libmp3lame", "-q:a", "4", str(output)]
```

with policy-aware expectations:

```python
monkeypatch.setattr(
    "anki_audio_quick_editor.audio_noise_reduction.resolve_output_policy",
    lambda *_args, **_kwargs: AudioOutputPolicy("flac", ".flac", "audio/flac", ("-codec:a", "flac"), "test"),
)
assert calls[2][-3:] == ["-codec:a", "flac", str(output)]
```

Apply the same pattern in RNNoise, DPDFNet, and voice-only tests, using `build_raw_pcm_encode_command` for RNNoise.

- [ ] **Step 2: Update pitch encode tests first**

In `tests/test_audio_pitch_hum.py`, monkeypatch `resolve_output_policy` to return an M4A policy and assert the final encode command uses AAC:

```python
assert command[-5:] == ("-codec:a", "aac", "-b:a", "96k", str(output_path))
```

- [ ] **Step 3: Run focused tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_noise_reduction.py tests/test_audio_rnnoise.py tests/test_audio_dpdfnet.py tests/test_audio_voice_only.py tests/test_audio_pitch_hum.py
```

Expected: FAIL because special transforms still use MP3 encode builders.

- [ ] **Step 4: Implement policy-aware final encode in special renderers**

Modify standard denoise:

```python
output_policy = resolve_output_policy(source_path, config, requested_format=config.output_format)
if output_path is None:
    output_path = Path(tempfile.mkstemp(prefix="aqe_denoised_", suffix=output_policy.extension)[1])
encode_cmd = build_audio_encode_command(ffmpeg_path, cleaned_wav, output_path, output_policy)
```

Modify RNNoise:

```python
output_policy = resolve_output_policy(source_path, config, requested_format=config.output_format)
output_path = output_path or Path(tempfile.mkstemp(prefix="aqe_rnnoise_", suffix=output_policy.extension)[1])
build_raw_pcm_encode_command(ffmpeg_path, denoised_raw, output_path, output_policy)
```

Modify DPDFNet, voice-only, direct pitch hum, and PitchTier hum with the same final encode pattern.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_noise_reduction.py tests/test_audio_rnnoise.py tests/test_audio_dpdfnet.py tests/test_audio_voice_only.py tests/test_audio_pitch_hum.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/audio_noise_reduction.py addon/anki_audio_quick_editor/audio_noise_reduction_bundled.py addon/anki_audio_quick_editor/audio_pitch_hum.py tests/test_audio_noise_reduction.py tests/test_audio_rnnoise.py tests/test_audio_dpdfnet.py tests/test_audio_voice_only.py tests/test_audio_pitch_hum.py
git commit -m "feat: use output policy for special transform encoding"
```

---

### Task 10: Config, Contracts, And UI Tests

**Files:**
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/config_migration.py`
- Modify: `contracts/communication.schema.json`
- Modify: generated contract files after running contract generation
- Modify: `settings_ui/src/lib/audio-operation-parameters.ts`
- Modify: `settings_ui/src/lib/i18n.ts`
- Modify: `settings_ui/src/settings/OutputFormatField.svelte`
- Modify: `settings_ui/src/batch/BatchControls.svelte`
- Modify: `settings_ui/src/editor-inline/SplitValueOptions.svelte`
- Modify: `tests/test_config_migration.py`
- Modify: `tests/test_audio_state.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `settings_ui/tests`
- Test: config, contract, and UI tests

- [ ] **Step 1: Update config and contract tests first**

Add Python tests:

```python
def test_processing_config_defaults_output_format_to_source() -> None:
    assert AudioProcessingConfig.from_config({}).output_format == "source"


def test_config_migration_preserves_source_output_format() -> None:
    migrated, changed = migrate_config({"output_format": "source"}, {"output_format": "source", "_config_version": CURRENT_CONFIG_VERSION})
    assert migrated["output_format"] == "source"
```

Update schema tests so `output_format` enum includes `source`.

- [ ] **Step 2: Update UI tests first**

Add settings UI assertions that the output format selector includes "Same as source" in settings, editor split options, and batch controls:

```typescript
expect(screen.getByText("Same as source")).toBeInTheDocument();
```

Use existing render helpers in `settings_ui/tests/app.test.ts` or the closest existing component tests rather than adding a new testing harness.

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_config_migration.py tests/test_audio_state.py tests/test_settings_initial_state.py
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
cd settings_ui && npm test -- --run
```

Expected: FAIL until schema, contracts, generated types, and UI labels include `source`.

- [ ] **Step 4: Update config and contracts**

Change `addon/anki_audio_quick_editor/config.schema.json`:

```json
"output_format": {
  "type": "string",
  "enum": ["source", "mp3", "m4a", "wav", "flac"]
}
```

Change `addon/anki_audio_quick_editor/config.json`:

```json
"output_format": "source"
```

Change `contracts/communication.schema.json` `OutputFormat` enum to include `source`.

Run contract generation:

```bash
python3 scripts/dev.py contracts-generate
```

Expected: generated Python and TypeScript contract files update cleanly.

- [ ] **Step 5: Update UI labels and descriptions**

Ensure these labels exist:

```typescript
"settings.output_format.source": "Same as source",
"editor.split.option.output_format.source.description": "Keep the original file extension when supported; otherwise use a compatible fallback.",
```

Ensure selectors render `OUTPUT_FORMAT_VALUES` in their declared order so `source` appears first.

- [ ] **Step 6: Run focused config and UI checks**

Run:

```bash
python3 scripts/dev.py test tests/test_config_migration.py tests/test_audio_state.py tests/test_settings_initial_state.py
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
cd settings_ui && npm test -- --run
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/config_migration.py contracts/communication.schema.json addon/anki_audio_quick_editor/contracts_generated.py settings_ui/src settings_ui/tests tests/test_config_migration.py tests/test_audio_state.py tests/test_settings_initial_state.py
git commit -m "feat: expose same-as-source output format"
```

---

### Task 11: E2E Tests For Source-Aware Output

**Files:**
- Modify: `e2e/test_audio_processing_ffmpeg.py`
- Modify: `e2e/test_editor_deep_filter_workflow.py`
- Modify: `e2e/test_editor_deep_filter_pause_workflow.py`
- Modify: `e2e/race_helpers.py`
- Modify: `e2e/editor_note_helpers.py`
- Test: e2e audio processing and affected editor workflows

- [ ] **Step 1: Update e2e tests before implementation verification**

Rename `test_common_audio_input_format_renders_to_mp3` to:

```python
def test_common_supported_audio_input_format_renders_to_source_format(...)
```

Update the assertion matrix:

```python
EXPECTED_SOURCE_OUTPUT_SUFFIX = {
    "flac": ".flac",
    "m4a": ".m4a",
    "mp3": ".mp3",
    "wav": ".wav",
    "aac": ".aac",
    "oga": ".oga",
    "ogg": ".ogg",
    "opus": ".opus",
    "webm": ".webm",
}
```

Assert:

```python
assert result.output_path.suffix == EXPECTED_SOURCE_OUTPUT_SUFFIX[extension]
assert audio_processor.probe_duration_ms(output, ffmpeg_config) > 0
```

Update final save e2e to use `source.name` with `.wav` and assert generated saved name ends with `.wav` or `.flac` depending on the source fixture.

For denoise/pause workflows, replace `.mp3`-specific generated-name checks with source-policy-aware checks:

```python
assert generated_name.endswith((".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".oga", ".opus", ".webm"))
```

Use stricter extension checks where the source fixture extension is controlled by the test.

- [ ] **Step 2: Run e2e tests to verify current failures**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: FAIL where implementation still returns MP3 or helpers glob only MP3.

- [ ] **Step 3: Update e2e helpers**

Modify helper functions that glob `*__aqe_*.mp3`:

```python
def generated_audio_names(media_dir: Path) -> list[str]:
    return sorted(
        path.name
        for path in media_dir.iterdir()
        if path.is_file()
        and "__aqe_" in path.stem
        and path.suffix.lower() in {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".oga", ".opus", ".webm"}
    )
```

Modify helper predicates that check `filename.endswith(".mp3")` to check the controlled expected extension or the supported generated-audio extension set.

- [ ] **Step 4: Run targeted e2e audio tests**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_audio_processing_ffmpeg.py
```

Expected: PASS.

- [ ] **Step 5: Run full e2e suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add e2e/test_audio_processing_ffmpeg.py e2e/test_editor_deep_filter_workflow.py e2e/test_editor_deep_filter_pause_workflow.py e2e/race_helpers.py e2e/editor_note_helpers.py
git commit -m "test: cover source-aware audio output end to end"
```

---

### Task 12: Full Verification And Documentation Update

**Files:**
- Modify: `docs/ffmpeg-source-quality-analysis.md` only if implementation differs from the assumptions in that document.
- Modify: `CONFIG_SCHEMA.md` if the user-visible config schema docs list concrete output format values.
- Modify: `WEBVIEW_AND_TEMPLATES.md` only if the webview contract/build workflow changes.
- Modify: `DEVELOPMENT.md` or release docs if they need instructions for regenerating FFmpeg runtime assets.
- Test: full repository quality gate

- [ ] **Step 1: Run focused Python suite**

Run:

```bash
python3 scripts/dev.py test
```

Expected: PASS.

- [ ] **Step 2: Run lint and type checks**

Run:

```bash
python3 scripts/dev.py lint
python3 scripts/dev.py typecheck
```

Expected: PASS.

- [ ] **Step 3: Run schema and contract checks**

Run:

```bash
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
```

Expected: PASS.

- [ ] **Step 4: Run release asset verification**

Run after the FFmpeg runtime lock points at capability-verified archives:

```bash
python3 scripts/release_assets.py fetch-ffmpeg --target all
python3 scripts/release_assets.py verify --target all
python3 scripts/release_assets.py verify --target current --diagnostics
```

Expected: PASS. The current-target diagnostic output must include the FFmpeg capability profile result.

- [ ] **Step 5: Run full QC**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 6: Run e2e suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 7: Update docs when checks expose user-visible drift**

If `CONFIG_SCHEMA.md` lists the output format enum, update that list to:

```markdown
`source`, `mp3`, `m4a`, `wav`, `flac`
```

If `docs/ffmpeg-source-quality-analysis.md` still describes a planned assumption that changed during implementation, update the wording to match the implemented behavior.

If maintainers need a repeatable FFmpeg asset refresh workflow, document:

```bash
gh workflow run build-ffmpeg-runtime.yml -f release_tag=<tag> -f ffmpeg_ref=<ref>
python3 scripts/release_assets.py fetch-ffmpeg --target all
python3 scripts/release_assets.py verify --target all
```

- [ ] **Step 8: Final commit**

```bash
git add docs CONFIG_SCHEMA.md WEBVIEW_AND_TEMPLATES.md
git commit -m "docs: document source-aware audio output policy"
```

Skip this commit when no documentation files changed after verification.

---

## Risk Notes For Implementers

- Do not replace model-required intermediate formats while chasing final-output preservation. RNNoise, Silero VAD, DeepFilterNet, Spleeter, prosody fallback, and pitch-hum synthesis have intentional sample-rate/channel choices.
- Do not make playback segment temp files source-aware in this pass. They are temporary compatibility media and not final Anki media.
- Do not rely on visible extension alone for final encode args. Use ffprobe metadata for bitrate, sample rate, and channels.
- Do not use `-c:a copy` for filtered edits, region delete/keep, pause removal, denoise, or pitch-hum. Those paths modify decoded audio.
- Treat only unknown or unsafe source extensions as fallback MP3. Do not collapse common Anki audio extensions such as `.aac`, `.ogg`, `.oga`, `.opus`, or `.webm` to MP3 when FFmpeg can re-encode to the same visible extension.
- Do not ship `source` preservation for `.ogg`, `.oga`, `.opus`, `.webm`, or `.aac` unless the managed FFmpeg runtime lock has passed `aqe-source-audio-v1` capability verification for every release target.
- Do not assume a BtbN artifact is sufficient because it is new. The required encoder/muxer profile is the compatibility contract.

## Completion Criteria

- All forced final-output MP3 builders from `docs/ffmpeg-source-quality-analysis.md` are either replaced by policy-aware builders or explicitly documented as playback-temp compatibility.
- Standard editor edits preserve `.mp3`, `.m4a`, `.aac`, `.wav`, `.flac`, `.ogg`, `.oga`, `.opus`, or `.webm` source extension when `output_format` is `source` and FFmpeg can safely write that extension.
- Batch non-convert transforms use the same source-aware final filename behavior as editor transforms.
- Managed FFmpeg release assets pass the `aqe-source-audio-v1` capability profile before `source` output can preserve `.ogg`, `.oga`, `.opus`, `.webm`, or `.aac`.
- The FFmpeg runtime workflow can produce/upload release archives for `windows-x86_64`, `macos-arm64`, and `macos-x86_64`, with BtbN prebuilt usage where sufficient and macOS builds where BtbN does not provide assets.
- Pause-removal final artifacts use the resolved extension and MIME type.
- Denoise and pitch-hum final encodes no longer call MP3-only builders.
- `python3 scripts/dev.py check` passes.
- `python3 scripts/dev.py test-e2e` passes.
