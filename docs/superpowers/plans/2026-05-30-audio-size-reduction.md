# Audio Size Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an editor and Browser batch operation that creates a smaller phone-friendly audio file using only three modes: gentle, normal, and aggressive.

**Architecture:** Add a shared `reduce_size` operation whose renderer probes source audio metadata, chooses a mode-specific MP3 encode profile, renders a new file, and rejects or skips results that are not smaller than the source. Keep mode parsing, operation mapping, editor split-button payloads, and batch parameters shared so editor and batch behavior stay aligned with `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`.

**Tech Stack:** Python 3.13 add-on runtime, FFmpeg/ffprobe, pytest, Svelte 5 + TypeScript, Vitest, JSON schema generated contracts, Anki e2e tests.

---

## Planning Assumptions

- Operation name: `reduce_size`; editor command: `aqe:reduce-size`; UI label: `Smaller`.
- Persisted default setting: `size_reduction_mode`, defaulting to `normal`.
- The button is a split button because it has per-action mode parameters.
- The three exposed modes are exactly `gentle`, `normal`, and `aggressive`; do not expose bitrate, sample-rate, channel, codec, or format controls.
- The operation always renders to MP3 for review-device compatibility and predictable size reduction. This is intentionally independent of the global `output_format` / Convert default.
- The renderer must inspect source stream metadata with ffprobe before encoding. The parameters to degrade are bitrate first, then channels and sample rate where the chosen mode allows it.
- The source file is never overwritten. A successful editor operation replaces only the target field's first supported `[sound:...]` reference with the generated MP3 and pushes undo history.
- If a mode cannot produce a smaller file, editor leaves the note unchanged and shows a clear status; batch records the note as skipped, not failed.
- Add the button to default-visible editor buttons because the request is for a directly available button. Users can still hide it in Settings.
- Browser batch must support `reduce_size` in the same operation list as Convert, Denoise, Shorten Pauses, Speed, Volume, and Graph.

## Size Reduction Policy

Use `addon/anki_audio_quick_editor/audio_output_policy.py::probe_audio_metadata()` as the source inspection layer. The new helper should make decisions from `codec_name`, `visible_format`, `bit_rate`, `sample_rate`, `channels`, and source file byte size.

| Mode | Primary intent | Bitrate target | Sample rate cap | Channel cap |
| --- | --- | --- | --- | --- |
| `gentle` | Minimal audible damage, still likely smaller than common 128k/192k MP3s | `min(96k, floor(source_kbps * 0.80))`, floor 48k when source is above 48k | 44100 Hz | preserve up to stereo |
| `normal` | Default for speech review clips | `min(64k, floor(source_kbps * 0.65))`, floor 40k when source is above 40k | 32000 Hz | mono |
| `aggressive` | Maximize savings for short phone-review audio | `min(40k, floor(source_kbps * 0.50))`, floor 24k when source is above 24k | 22050 Hz | mono |

Rules:

- Never increase source bitrate, sample rate, or channels.
- If source bitrate is unknown, use the mode's bitrate cap.
- If sample rate or channel count is unknown, omit the corresponding `-ar` or `-ac` argument rather than guessing upward.
- Do not alter duration, speed, volume, pauses, or denoise state.
- After FFmpeg renders, compare output byte size with source byte size. If output size is not smaller, delete the output and raise/return a skipped result.

## File Structure

Create:

- `addon/anki_audio_quick_editor/audio_size_reduction.py`: mode normalization, size-reduction profile selection, FFmpeg codec args, and "already compact" exception.
- `tests/test_audio_size_reduction.py`: pure unit tests for profile decisions and mode validation.
- `tests/test_audio_rendering_size_reduction.py`: renderer tests with monkeypatched FFmpeg/ffprobe calls and output-size checks.
- `tests/test_editor_size_reduction_callbacks.py`: editor bridge behavior, generated MP3 replacement, undo, no-change-on-not-smaller.
- `e2e/test_editor_size_reduction_workflow.py`: real editor render path with FFmpeg.
- `e2e/test_browser_batch_size_reduction_workflow.py`: real Browser batch render path with FFmpeg.

Modify:

- `addon/anki_audio_quick_editor/audio_commands.py`
- `addon/anki_audio_quick_editor/audio_rendering.py`
- `addon/anki_audio_quick_editor/audio_processor.py`
- `addon/anki_audio_quick_editor/audio_processor_rendering_portal.py`
- `addon/anki_audio_quick_editor/audio_state.py`
- `addon/anki_audio_quick_editor/audio_operation_params.py`
- `addon/anki_audio_quick_editor/audio_operations.py`
- `addon/anki_audio_quick_editor/batch_operation_processing.py`
- `addon/anki_audio_quick_editor/browser_dialog_state.py`
- `addon/anki_audio_quick_editor/config.json`
- `addon/anki_audio_quick_editor/config.schema.json`
- `addon/anki_audio_quick_editor/editor_actions.py`
- `addon/anki_audio_quick_editor/editor_bridge.py`
- `addon/anki_audio_quick_editor/editor_callbacks.py`
- `addon/anki_audio_quick_editor/editor_dependencies.py`
- `addon/anki_audio_quick_editor/editor_integration.py`
- `addon/anki_audio_quick_editor/editor_processing.py`
- `addon/anki_audio_quick_editor/editor_size_reduction.py`
- `addon/anki_audio_quick_editor/editor_split_defaults.py`
- `addon/anki_audio_quick_editor/editor_status.py`
- `contracts/communication.schema.json`
- `addon/anki_audio_quick_editor/contracts_generated.py` and `settings_ui/src/lib/generated/contracts.ts` via `python3 scripts/dev.py contracts-generate`
- `settings_ui/src/lib/audio-operation-parameters.ts`
- `settings_ui/src/lib/audio-option-tooltips.ts`
- `settings_ui/src/lib/editor-toolbar-buttons.ts`
- `settings_ui/src/lib/icon-types.ts`
- `settings_ui/src/lib/CommandIcon.svelte`
- `settings_ui/src/settings/settings-state.ts`
- `settings_ui/src/settings/ToolbarVisibilitySettings.svelte`
- `settings_ui/src/editor-inline/types.ts`
- `settings_ui/src/editor-inline/commands.ts`
- `settings_ui/src/editor-inline/split-button-state.ts`
- `settings_ui/src/editor-inline/split-button-state-commands.ts`
- `settings_ui/src/editor-inline/split-button-presenter.ts`
- `settings_ui/src/editor-inline/SplitButton.svelte`
- `settings_ui/src/editor-inline/SplitValueOptions.svelte`
- `settings_ui/src/editor-inline/split-menu-content.ts`
- `settings_ui/src/editor-inline/EditorHelp.svelte`
- `settings_ui/src/batch/batch-state.ts`
- `settings_ui/src/batch/BatchControls.svelte`
- `addon/anki_audio_quick_editor/locales/*.json`
- `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`
- Existing tests covering settings defaults, contracts, batch initial state, split buttons, toolbar visibility, and editor UI injection.

---

### Task 1: Shared Mode And Profile Tests

**Files:**
- Create: `tests/test_audio_size_reduction.py`
- Create: `addon/anki_audio_quick_editor/audio_size_reduction.py`
- Modify: `addon/anki_audio_quick_editor/audio_state.py`
- Modify: `addon/anki_audio_quick_editor/audio_operation_params.py`
- Test: `tests/test_audio_size_reduction.py`
- Test: `tests/test_audio_operation_params.py`

- [ ] **Step 1: Write failing pure tests**

Add tests like:

```python
from pathlib import Path

from anki_audio_quick_editor.audio_output_policy import AudioSourceMetadata
from anki_audio_quick_editor.audio_size_reduction import (
    AudioAlreadyCompactError,
    build_size_reduction_plan,
    normalize_size_reduction_mode,
)


def metadata(**overrides: object) -> AudioSourceMetadata:
    values = {
        "path": Path("clip.mp3"),
        "visible_format": "mp3",
        "codec_name": "mp3",
        "sample_rate": 48000,
        "channels": 2,
        "bit_rate": 128000,
        "bits_per_raw_sample": None,
        "sample_fmt": None,
    }
    values.update(overrides)
    return AudioSourceMetadata(**values)


def test_normal_mode_degrades_common_stereo_mp3_for_speech() -> None:
    plan = build_size_reduction_plan(metadata(), "normal")

    assert plan.mode == "normal"
    assert plan.target_bitrate_kbps == 64
    assert plan.target_sample_rate_hz == 32000
    assert plan.target_channels == 1
    assert plan.codec_args == ("-codec:a", "libmp3lame", "-b:a", "64k", "-ar", "32000", "-ac", "1")


def test_gentle_mode_preserves_stereo_and_caps_bitrate() -> None:
    plan = build_size_reduction_plan(metadata(bit_rate=192000, sample_rate=48000, channels=2), "gentle")

    assert plan.target_bitrate_kbps == 96
    assert plan.target_sample_rate_hz == 44100
    assert plan.target_channels == 2


def test_aggressive_mode_uses_low_speech_friendly_profile() -> None:
    plan = build_size_reduction_plan(metadata(bit_rate=96000), "aggressive")

    assert plan.target_bitrate_kbps == 40
    assert plan.target_sample_rate_hz == 22050
    assert plan.target_channels == 1


def test_mode_defaults_to_normal() -> None:
    assert normalize_size_reduction_mode("bad") == "normal"
    assert normalize_size_reduction_mode(None) == "normal"


def test_already_compact_source_is_rejected_when_no_safe_parameter_can_drop() -> None:
    try:
        build_size_reduction_plan(
            metadata(bit_rate=22000, sample_rate=22050, channels=1),
            "aggressive",
        )
    except AudioAlreadyCompactError as exc:
        assert "already compact" in str(exc)
    else:
        raise AssertionError("expected compact audio to be rejected")
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_size_reduction.py tests/test_audio_operation_params.py
```

Expected: FAIL because `audio_size_reduction.py`, `size_reduction_mode`, and parameter parsing do not exist yet.

- [ ] **Step 3: Add the shared helper**

Create `addon/anki_audio_quick_editor/audio_size_reduction.py` with:

```python
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal, cast

from .audio_output_policy import AudioSourceMetadata
from .audio_commands import FFMPEG_AUDIO_CODEC_ARG
from .errors import AudioProcessingError

SizeReductionMode = Literal["gentle", "normal", "aggressive"]
DEFAULT_SIZE_REDUCTION_MODE: SizeReductionMode = "normal"
SIZE_REDUCTION_MODES = frozenset({"gentle", "normal", "aggressive"})


class AudioAlreadyCompactError(AudioProcessingError):
    """Raised when a mode cannot safely produce a smaller file."""


@dataclass(frozen=True)
class SizeReductionProfile:
    max_bitrate_kbps: int
    min_bitrate_kbps: int
    bitrate_multiplier: float
    sample_rate_cap_hz: int
    channel_cap: int


@dataclass(frozen=True)
class SizeReductionPlan:
    mode: SizeReductionMode
    target_bitrate_kbps: int
    target_sample_rate_hz: int | None
    target_channels: int | None
    codec_args: tuple[str, ...]


PROFILES: dict[SizeReductionMode, SizeReductionProfile] = {
    "gentle": SizeReductionProfile(96, 48, 0.80, 44100, 2),
    "normal": SizeReductionProfile(64, 40, 0.65, 32000, 1),
    "aggressive": SizeReductionProfile(40, 24, 0.50, 22050, 1),
}


def normalize_size_reduction_mode(value: Any) -> SizeReductionMode:
    text = str(value).strip().lower()
    if text in SIZE_REDUCTION_MODES:
        return cast(SizeReductionMode, text)
    return DEFAULT_SIZE_REDUCTION_MODE


def build_size_reduction_plan(
    metadata: AudioSourceMetadata,
    mode: Any,
) -> SizeReductionPlan:
    normalized = normalize_size_reduction_mode(mode)
    profile = PROFILES[normalized]
    source_kbps = _source_kbps(metadata.bit_rate)
    target_kbps = _target_bitrate_kbps(source_kbps, profile)
    target_sample_rate = _target_sample_rate(metadata.sample_rate, profile)
    target_channels = _target_channels(metadata.channels, profile)
    if not _has_degradation(source_kbps, target_kbps, metadata.sample_rate, target_sample_rate, metadata.channels, target_channels, metadata.visible_format):
        raise AudioAlreadyCompactError("This audio is already compact for the selected mode.")
    return SizeReductionPlan(
        mode=normalized,
        target_bitrate_kbps=target_kbps,
        target_sample_rate_hz=target_sample_rate,
        target_channels=target_channels,
        codec_args=_codec_args(target_kbps, target_sample_rate, target_channels),
    )
```

Add these private helpers in the same file:

```python
def _source_kbps(bit_rate: int | None) -> int | None:
    if bit_rate is None or bit_rate <= 0:
        return None
    return max(1, round(bit_rate / 1000))


def _target_bitrate_kbps(
    source_kbps: int | None,
    profile: SizeReductionProfile,
) -> int:
    if source_kbps is None:
        return profile.max_bitrate_kbps
    if source_kbps <= profile.min_bitrate_kbps:
        return source_kbps
    degraded = math.floor(source_kbps * profile.bitrate_multiplier)
    capped = min(profile.max_bitrate_kbps, degraded)
    floored = max(profile.min_bitrate_kbps, capped)
    return min(source_kbps - 1, floored)


def _target_sample_rate(
    sample_rate: int | None,
    profile: SizeReductionProfile,
) -> int | None:
    if sample_rate is None or sample_rate <= 0:
        return None
    return min(sample_rate, profile.sample_rate_cap_hz)


def _target_channels(
    channels: int | None,
    profile: SizeReductionProfile,
) -> int | None:
    if channels is None or channels <= 0:
        return None
    return min(channels, profile.channel_cap)


def _has_degradation(
    source_kbps: int | None,
    target_kbps: int,
    source_sample_rate: int | None,
    target_sample_rate: int | None,
    source_channels: int | None,
    target_channels: int | None,
    visible_format: str | None,
) -> bool:
    if visible_format != "mp3":
        return True
    if source_kbps is None or target_kbps < source_kbps:
        return True
    if source_sample_rate is not None and target_sample_rate is not None and target_sample_rate < source_sample_rate:
        return True
    return source_channels is not None and target_channels is not None and target_channels < source_channels


def _codec_args(
    target_kbps: int,
    target_sample_rate: int | None,
    target_channels: int | None,
) -> tuple[str, ...]:
    args: list[str] = [FFMPEG_AUDIO_CODEC_ARG, "libmp3lame", "-b:a", f"{target_kbps}k"]
    if target_sample_rate is not None:
        args.extend(("-ar", str(target_sample_rate)))
    if target_channels is not None:
        args.extend(("-ac", str(target_channels)))
    return tuple(args)
```

- [ ] **Step 4: Add config and operation parameter support**

Modify `AudioProcessingConfig` in `addon/anki_audio_quick_editor/audio_state.py`:

```python
size_reduction_mode: str = "normal"
```

In `from_config()`, sanitize it with `normalize_size_reduction_mode(config.get("size_reduction_mode", cls.size_reduction_mode))`.

Modify `AudioOperationParameters` and `parameters_from_raw()` in `addon/anki_audio_quick_editor/audio_operation_params.py`:

```python
size_reduction_mode: str | None = None
```

Add a raw parameter named `size_reduction_mode` and a private `_size_reduction_mode_or_none()` that returns only `gentle`, `normal`, or `aggressive`.

- [ ] **Step 5: Extend parameter tests**

Add to `tests/test_audio_operation_params.py`:

```python
def test_parameters_from_raw_accepts_size_reduction_mode() -> None:
    assert parameters_from_raw(size_reduction_mode="aggressive").size_reduction_mode == "aggressive"
    assert parameters_from_raw(size_reduction_mode="invalid").size_reduction_mode is None
```

Add an effective-config test:

```python
def test_effective_config_uses_size_reduction_mode_override() -> None:
    config = AudioProcessingConfig(size_reduction_mode="normal")
    params = AudioOperationParameters(size_reduction_mode="aggressive")

    effective = effective_config_for_operation(OP_REDUCE_SIZE, config, params)

    assert effective.size_reduction_mode == "aggressive"
    assert config.size_reduction_mode == "normal"
```

Update `effective_config_for_operation()` so `reduce_size` returns `replace(config, size_reduction_mode=parameters.size_reduction_mode or config.size_reduction_mode)`.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_size_reduction.py tests/test_audio_operation_params.py
```

Expected: PASS.

---

### Task 2: FFmpeg Rendering

**Files:**
- Modify: `addon/anki_audio_quick_editor/audio_commands.py`
- Modify: `addon/anki_audio_quick_editor/audio_rendering.py`
- Modify: `addon/anki_audio_quick_editor/audio_processor.py`
- Modify: `addon/anki_audio_quick_editor/audio_processor_rendering_portal.py`
- Create: `tests/test_audio_rendering_size_reduction.py`
- Test: `tests/test_audio_rendering_size_reduction.py`

- [ ] **Step 1: Write failing renderer tests**

Cover command shape, metadata use, and byte-size rejection:

```python
def test_render_size_reduced_audio_uses_metadata_driven_mp3_args(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"x" * 200_000)
    output = tmp_path / "out.mp3"
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_rendering.find_ffmpeg", lambda _path: Path("/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_rendering.probe_audio_metadata", lambda _source, _config: metadata(path=source))
    monkeypatch.setattr("anki_audio_quick_editor.audio_rendering.probe_duration_ms", lambda _path, _config: 1000)

    def fake_run(command: list[str], **_kwargs: object) -> object:
        commands.append(tuple(command))
        output.write_bytes(b"x" * 80_000)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_rendering.subprocess.run", fake_run)

    result = render_size_reduced_audio(source, AudioProcessingConfig(size_reduction_mode="normal"), output_path=output)

    assert result.output_path == output
    assert commands == [(
        "/ffmpeg", "-y", "-i", str(source), "-vn",
        "-codec:a", "libmp3lame", "-b:a", "64k", "-ar", "32000", "-ac", "1",
        str(output),
    )]
```

Also test that a rendered output at least as large as the source raises `AudioAlreadyCompactError` and deletes/leaves no accepted output.

- [ ] **Step 2: Add command builder**

In `audio_commands.py`, add:

```python
def build_size_reduction_audio_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
    codec_args: Sequence[str],
) -> tuple[str, ...]:
    """Build an ffmpeg command that re-encodes audio for smaller review media."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        *tuple(codec_args),
        str(output_path),
    )
```

- [ ] **Step 3: Add renderer**

In `audio_rendering.py`, import `build_size_reduction_audio_command`, `AudioAlreadyCompactError`, and `build_size_reduction_plan`. Add:

```python
def render_size_reduced_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    *,
    mode: object | None = None,
) -> AudioProcessingResult:
    """Render ``source_path`` as a smaller MP3 using source-aware degradation."""
    metadata = probe_audio_metadata(source_path, config)
    plan = build_size_reduction_plan(metadata, mode or config.size_reduction_mode)
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_smaller_", suffix=".mp3")[1])
    cmd = build_size_reduction_audio_command(ffmpeg_path, source_path, output_path, plan.codec_args)
    if on_command:
        on_command(cmd)
    result = _run_render_command(cmd, "Could not start audio size reduction.")
    if result.returncode != 0:
        raise AudioProcessingError(_render_external_error_message(result, "Audio size reduction failed."))
    if output_path.stat().st_size >= source_path.stat().st_size:
        raise AudioAlreadyCompactError("The selected mode did not make this audio smaller.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )
```

- [ ] **Step 4: Export through facades**

Add `render_size_reduced_audio` exports to `audio_processor_rendering_portal.py` and `audio_processor.py`. Use the same dependency sync path as `render_converted_audio`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_size_reduction.py tests/test_audio_rendering_size_reduction.py
```

Expected: PASS.

---

### Task 3: Shared Operation And Batch Path

**Files:**
- Modify: `addon/anki_audio_quick_editor/audio_operations.py`
- Modify: `addon/anki_audio_quick_editor/audio_operation_params.py`
- Modify: `addon/anki_audio_quick_editor/batch_operation_processing.py`
- Modify: `addon/anki_audio_quick_editor/browser_dialog_state.py`
- Modify: `contracts/communication.schema.json`
- Modify generated: `addon/anki_audio_quick_editor/contracts_generated.py`
- Modify generated: `settings_ui/src/lib/generated/contracts.ts`
- Test: `tests/test_browser_dialog_state.py`
- Test: `tests/test_batch_visualization.py`
- Test: `settings_ui/tests/batch-state.test.ts`

- [ ] **Step 1: Add failing shared and batch tests**

Update `tests/test_browser_dialog_state.py` to assert a `reduce_size` operation exists with `parameter_kind == "size_reduction"` and `parameter_name == "size_reduction_mode"`, and that defaults include `"size_reduction_mode": "normal"`.

Update request decoding tests:

```python
def test_request_from_batch_start_payload_builds_size_reduction_parameters() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "reduce_size",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {"size_reduction_mode": "aggressive"},
        }
    )

    assert request.operation == "reduce_size"
    assert request.parameters.size_reduction_mode == "aggressive"
```

Update `tests/test_batch_visualization.py` with two cases:

- `reduce_size` writes a generated MP3 and replaces the source field reference.
- `AudioAlreadyCompactError` returns `BatchNoteResult(status="skipped", ...)`.

- [ ] **Step 2: Add operation constants and labels**

In `audio_operations.py`:

```python
OP_REDUCE_SIZE = "reduce_size"
```

Add it to `TRANSFORM_OPERATIONS`, `OPERATION_LABELS`, and `OPERATION_LABEL_KEYS` with label `Smaller` and i18n key `operation.reduce_size`. Do not add it to `apply_audio_operation()` because it is a direct special renderer like Convert and Denoise, not an `AudioEditState` mutation.

- [ ] **Step 3: Route batch rendering**

In `batch_operation_processing.py`, add a branch before the generic `apply_audio_operation()` path:

```python
elif request.operation == OP_REDUCE_SIZE:
    desired_name = make_output_filename(audio_filename, output_format="mp3")
    output_path = temp_final_path(desired_name)
    _facade_attr("render_size_reduced_audio")(
        source_path,
        effective_config,
        output_path=output_path,
        mode=request.parameters.size_reduction_mode,
    )
```

Catch `AudioAlreadyCompactError` separately and return a skipped `BatchNoteResult` with the source filename and the exception message.

- [ ] **Step 4: Extend batch initial-state decoding**

In `browser_dialog_state.py`, import `OP_REDUCE_SIZE`, add the default:

```python
"size_reduction_mode": config.size_reduction_mode,
```

Return parameter metadata:

```python
if operation == OP_REDUCE_SIZE:
    return "size_reduction"
```

and:

```python
if operation == OP_REDUCE_SIZE:
    return "size_reduction_mode"
```

Pass `size_reduction_mode=params.get("size_reduction_mode")` into `parameters_from_raw()`.

- [ ] **Step 5: Update contracts and regenerate**

Modify `contracts/communication.schema.json`:

- Add `"reduce_size"` to `BatchOperationName`.
- Add `"size_reduction"` to `BatchParameterKind`.
- Add `"size_reduction_mode"` to `BatchParameterName`.
- Add a `SizeReductionMode` definition with enum `["gentle", "normal", "aggressive"]`.
- Add `size_reduction_mode` to `BatchOperationParameters`.
- Add required `size_reduction_mode` to `BatchDefaults`.
- Add `size_reduction_mode` to `Config`.
- Add `aqe:reduce-size` to `VisibleEditorButton`.

Run:

```bash
python3 scripts/dev.py contracts-generate
python3 scripts/dev.py contracts-check
```

Expected: PASS and generated Python/TypeScript contract files are updated.

- [ ] **Step 6: Run focused batch tests**

Run:

```bash
python3 scripts/dev.py test tests/test_browser_dialog_state.py tests/test_batch_visualization.py
cd settings_ui && npm test -- --run tests/batch-state.test.ts
```

Expected: PASS.

---

### Task 4: Editor Backend Dispatch

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `addon/anki_audio_quick_editor/editor_bridge.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`
- Modify: `addon/anki_audio_quick_editor/editor_integration.py`
- Modify: `addon/anki_audio_quick_editor/editor_processing.py`
- Create: `addon/anki_audio_quick_editor/editor_size_reduction.py`
- Modify: `addon/anki_audio_quick_editor/editor_split_defaults.py`
- Modify: `addon/anki_audio_quick_editor/editor_status.py`
- Create: `tests/test_editor_size_reduction_callbacks.py`
- Test: `tests/test_editor_size_reduction_callbacks.py`
- Test: `tests/test_editor_ui.py`

- [ ] **Step 1: Write failing editor tests**

Mirror `tests/test_editor_convert_callbacks.py`:

- JSON payload `{"command":"aqe:reduce-size","fieldOrd":0,"overrides":{"sizeReductionMode":"aggressive"}}` calls `render_size_reduced_audio(..., mode="aggressive", output_path=*.mp3)`.
- Generated MP3 replaces only the current field's sound reference.
- Undo history stores the previous filename.
- `AudioAlreadyCompactError` leaves the field unchanged and does not write media.
- Runtime injection includes `"sizeReductionMode": "normal"` in `splitButtonDefaults`.

- [ ] **Step 2: Decode editor payloads**

In `editor_actions.py`:

```python
CMD_REDUCE_SIZE = "aqe:reduce-size"
```

Add to `BRIDGE_COMMANDS`, `BRIDGE_COMMAND_TO_OPERATION`, and `EditorCommandOverrides`:

```python
size_reduction_mode: str | None = None
```

Read raw frontend key `sizeReductionMode`, map it through `parameters_from_raw(size_reduction_mode=...)`, and include it when building `AudioOperationParameters` in `processing_config_for_command()`.

- [ ] **Step 3: Add editor async handler**

Prefer a small new `editor_size_reduction.py` instead of growing `editor_special_transforms.py` too much:

```python
def reduce_size_async(
    editor: Any,
    command: EditorCommandPayload | None = None,
    deps: Any = None,
) -> None:
    if deps is None:
        deps = command
        command = EditorCommandPayload(command="aqe:reduce-size")
    mode = command.overrides.size_reduction_mode if command is not None else None

    def _renderer(
        source_path: Path,
        render_config: AudioProcessingConfig,
        *,
        output_path: Path,
        on_command: Callable[[tuple[str, ...]], None] | None = None,
    ) -> None:
        deps.render_size_reduced_audio(
            source_path,
            render_config,
            output_path=output_path,
            on_command=on_command,
            mode=mode,
        )

    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.reducing_size"),
        failure_log_label="size reduction failed",
        renderer=_renderer,
        command=command,
        output_format="mp3",
    )
```

Re-export through `editor_processing.py`, `editor_callbacks.py`, `editor_dependencies.py`, `editor_integration.py`, and route it from `editor_bridge.handle_payload_command()`.

- [ ] **Step 4: Add status summaries**

In `editor_status.py`, add `CMD_REDUCE_SIZE` and:

```python
if payload.command == CMD_REDUCE_SIZE:
    return t(
        "editor.status.operation.reduce_size",
        {"level": _pause_aggressiveness_label(payload.overrides.size_reduction_mode or config.size_reduction_mode)},
    )
```

- [ ] **Step 5: Add split-default persistence**

In `editor_split_defaults.py`, save `sizeReductionMode` as `size_reduction_mode` through `parameters_from_raw()`.

In `editor_integration.py`, inject:

```python
"sizeReductionMode": str(config.get("size_reduction_mode", "normal")),
```

- [ ] **Step 6: Run focused editor tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_size_reduction_callbacks.py tests/test_editor_ui.py
```

Expected: PASS.

---

### Task 5: Frontend Editor And Batch UI

**Files:**
- Modify: `settings_ui/src/lib/audio-operation-parameters.ts`
- Modify: `settings_ui/src/lib/audio-option-tooltips.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Modify: `settings_ui/src/lib/icon-types.ts`
- Modify: `settings_ui/src/lib/CommandIcon.svelte`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Modify: `settings_ui/src/settings/ToolbarVisibilitySettings.svelte`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/commands.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state-commands.ts`
- Modify: `settings_ui/src/editor-inline/split-button-presenter.ts`
- Modify: `settings_ui/src/editor-inline/SplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/SplitValueOptions.svelte`
- Modify: `settings_ui/src/editor-inline/split-menu-content.ts`
- Modify: `settings_ui/src/editor-inline/EditorHelp.svelte`
- Modify: `settings_ui/src/batch/batch-state.ts`
- Modify: `settings_ui/src/batch/BatchControls.svelte`
- Test: `settings_ui/tests/editor-inline.command-splits.integration.test.ts`
- Test: `settings_ui/tests/batch-state.test.ts`

- [ ] **Step 1: Write failing frontend tests**

Add an editor split test:

```typescript
it("dispatches reduce-size commands with the selected mode", async () => {
  window.__AQE_EDITOR_CONFIG__ = {
    audioFieldIndices: [0],
    splitButtonDefaults: {
      denoiseAlgorithm: "standard",
      pauseAggressiveness: "normal",
      repeatPauseSeconds: 0,
      sizeReductionMode: "normal",
      speedStep: 1.5,
      volumeStepDb: 15,
    },
  };
  initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
  scan(window.__AQE_EDITOR_CONFIG__);

  document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-reduce-size"]')!.click();
  expect(window.__aqePendingCommandPayload).toMatchObject({
    command: "aqe:reduce-size",
    fieldOrd: 0,
    overrides: { sizeReductionMode: "normal" },
  });

  window.__aqePendingCommandPayload = null;
  window.__aqeSetBusy?.(0, false);
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-reduce-size-menu"]')!.click();
  await Promise.resolve();
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-reduce-size-preset-aggressive"]')!.click();
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-reduce-size"]')!.click();

  expect(window.__aqePendingCommandPayload?.overrides?.sizeReductionMode).toBe("aggressive");
});
```

Add batch-state expectation for `BatchOperationName.ReduceSize` producing `{ size_reduction_mode: "aggressive" }`.

- [ ] **Step 2: Add shared TypeScript mode helpers**

In `audio-operation-parameters.ts`:

```typescript
export type SizeReductionMode = "gentle" | "normal" | "aggressive";
export const SIZE_REDUCTION_MODE_VALUES = ["gentle", "normal", "aggressive"] as const;

export function sizeReductionModeOrDefault(value: unknown): SizeReductionMode {
  return value === "gentle" || value === "aggressive" ? value : "normal";
}

export function formatSizeReductionMode(value: unknown): string {
  return formatPauseAggressiveness(sizeReductionModeOrDefault(value));
}
```

Add `sizeReductionModeTooltip(value)` in `audio-option-tooltips.ts`.

- [ ] **Step 3: Add toolbar button and icon**

Add `aqe:reduce-size` to `EditorCommand`, `DEFAULT_VISIBLE_EDITOR_BUTTONS`, `DEFAULT_EDITOR_BUTTON_MODES`, `commandButtons()`, and `COMMAND_SLUGS`.

Use a lucide icon such as `minimize-2`; add it to `icon-types.ts` and `CommandIcon.svelte`.

- [ ] **Step 4: Add split state and payload support**

Add `sizeReductionMode` and default/edited fields to `SplitButtonDefaults` and `FieldSplitButtonState`.

Add `setSizeReductionModeForField()`, apply promoted defaults, and include `sizeReductionMode` in:

- `SplitButton.svelte` local state and props to `SplitValueOptions`.
- `split-button-presenter.ts::currentValueLabel()`.
- `split-button-state-commands.ts::buildSplitCommandPayloadFromState()`.
- `split-button-state-commands.ts::buildSplitDefaultSaveRequestFromState()`.

Payload shape:

```typescript
{ command: "aqe:reduce-size", fieldOrd: ord, overrides: { sizeReductionMode: state.sizeReductionMode } }
```

- [ ] **Step 5: Add split menu content**

In `split-menu-content.ts`, add `gentle`, `normal`, and `aggressive` option values for `aqe:reduce-size`, with descriptions:

- Gentle: lower bitrate and keep stereo when present.
- Normal: speech-friendly default, mono and 32 kHz cap.
- Aggressive: smallest file, mono and lower sample rate.

Update `SplitValueOptions.svelte` to apply size-reduction modes through `onSizeReductionMode`.

- [ ] **Step 6: Add Settings and batch controls**

In `ToolbarVisibilitySettings.svelte`, add a settings block for `aqe:reduce-size` using `SettingsChoiceGroup` bound to `config.size_reduction_mode`.

In `batch-state.ts`, add `sizeReductionMode` to `BatchFormState`, fallback defaults, initialization, and `batchStartRequest()`.

In `BatchControls.svelte`, add a `BatchParameterKind.SizeReduction` choice group with the three modes.

- [ ] **Step 7: Run focused frontend tests**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.command-splits.integration.test.ts tests/batch-state.test.ts
```

Expected: PASS.

---

### Task 6: Config, I18n, Docs, And E2E

**Files:**
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/locales/*.json`
- Modify: `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`
- Create: `e2e/test_editor_size_reduction_workflow.py`
- Create: `e2e/test_browser_batch_size_reduction_workflow.py`
- Test: `python3 scripts/dev.py config-schema`
- Test: `python3 scripts/dev.py i18n`
- Test: `python3 scripts/dev.py test-e2e`

- [ ] **Step 1: Add default config and schema**

In `config.json`:

```json
"size_reduction_mode": "normal"
```

Add `aqe:reduce-size` to `visible_editor_buttons` and `editor_button_modes`.

In `config.schema.json`, add:

```json
"size_reduction_mode": {
  "type": "string",
  "enum": ["gentle", "normal", "aggressive"]
}
```

Add `aqe:reduce-size` to visible button and button mode enums.

- [ ] **Step 2: Add locale keys**

Add these keys to `en.json`, then mirror them in every locale file so `python3 scripts/dev.py i18n` passes:

```json
"settings.size_reduction_mode": "Default smaller-file mode",
"settings.size_reduction_mode.gentle.tooltip": "Keeps the most audio detail while lowering bitrate when it can.",
"settings.size_reduction_mode.normal.tooltip": "Good default for speech cards: smaller MP3, mono when useful, and a 32 kHz cap.",
"settings.size_reduction_mode.aggressive.tooltip": "Prioritizes phone storage savings with lower bitrate, mono, and a lower sample rate.",
"editor.command.reduce_size.label": "Smaller",
"editor.command.reduce_size.title": "Create a smaller phone-friendly MP3 file",
"editor.status.reducing_size": "Making audio smaller",
"editor.status.operation.reduce_size": "Made audio smaller with {level} mode.",
"editor.split.description_reduce_size": "Creates a smaller MP3 for phone storage by lowering only safe audio parameters for the selected mode.",
"editor.split.option.size_reduction.gentle.description": "Lowest damage: lower bitrate, preserve stereo when present.",
"editor.split.option.size_reduction.normal.description": "Default for speech: smaller MP3, mono when useful, 32 kHz cap.",
"editor.split.option.size_reduction.aggressive.description": "Smallest files: lower bitrate, mono, and lower sample rate.",
"editor.help.reduce_size_desc": "Creates a smaller MP3 for phone storage.",
"operation.reduce_size": "Smaller"
```

- [ ] **Step 3: Update behavior rules**

In `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`:

- Add `aqe:reduce-size` to generated-file modification commands.
- Add it to split-button shapes.
- Add `size_reduction_mode` to split-button defaults.
- Add shared operation parity row: editor `aqe:reduce-size` with `sizeReductionMode`; batch `reduce_size` with `size_reduction_mode`.
- Add test requirements note that reduce-size must prove original media is untouched and output is smaller or skipped.

- [ ] **Step 4: Add E2E coverage**

Editor e2e should:

- Configure a real source MP3 with a larger bitrate than the normal profile.
- Click the `Smaller` split button.
- Verify the field reference changes to a generated `.mp3`.
- Verify source media remains on disk.
- Verify generated file byte size is lower than source byte size.
- Verify undo restores the previous reference.

Batch e2e should:

- Select notes with source MP3 files.
- Run `reduce_size` in normal mode from the Browser batch dialog.
- Verify each written note references a generated `.mp3`.
- Verify generated files are smaller than source files.
- Include one already-compact fixture and assert it is skipped, not failed.

- [ ] **Step 5: Run validation**

Run:

```bash
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
python3 scripts/dev.py i18n
python3 scripts/dev.py test tests/test_audio_size_reduction.py tests/test_audio_rendering_size_reduction.py tests/test_editor_size_reduction_callbacks.py tests/test_browser_dialog_state.py tests/test_batch_visualization.py tests/test_editor_ui.py tests/test_audio_operation_params.py
python3 scripts/dev.py test-svelte
python3 scripts/dev.py test-e2e
```

Expected: PASS. If `test-e2e` is not run before committing, the commit body must say full check/e2e routines were not run, per repository instructions.

---

## Final Verification Gate

Before marking implementation complete, run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

If either command cannot be run, record the exact reason and the narrower commands that did pass.

## Commit Guidance

Use an imperative subject and a body that explains why the feature exists and its impact. Example:

```text
Add source-aware audio size reduction

Users need a one-click way to shrink short review audio for phone storage without manually choosing codecs or encoder settings. This adds a shared reduce_size operation with three mode-based profiles, so editor and batch use the same metadata-driven degradation rules and leave notes unchanged when an output would not be smaller.

Impact: generated media is MP3 for portability, original media remains untouched, undo/redo continues to work in the editor, and Browser batch can shrink many notes with the same mode defaults.
```
