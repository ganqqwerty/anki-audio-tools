"""ffmpeg-backed rendering for preview and final audio files."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import shlex
import shutil
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .audio_pipeline import (
    PAUSE_PIPELINE_MANIFEST_VERSION,
    build_filter_complex_script,
    intervals_to_json,
    make_pause_pipeline_run_id,
    parse_silencedetect_intervals,
    plan_pause_timeline,
    timeline_to_json,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .errors import (
    AudioProcessingError,
    MissingDeepFilterError,
    MissingFfmpegError,
    MissingMpSenetError,
    MissingSidonError,
)
from .support import (
    build_command_record,
    record_latest_mp_senet_support_incident,
    record_latest_pause_pipeline_support_incident,
    record_latest_sidon_support_incident,
)

BUNDLED_DEEP_FILTER_VERSION = "0.5.6"
BUNDLED_SIDON_VERSION = "0.1"
BUNDLED_MP_SENET_VERSION = "0.1"
_PACKAGE_DIR = Path(__file__).resolve().parent
_BUNDLED_DEEP_FILTER_BY_PLATFORM = {
    ("Darwin", "arm64"): _PACKAGE_DIR
    / "bin"
    / f"deep-filter-{BUNDLED_DEEP_FILTER_VERSION}-aarch64-apple-darwin",
}
_BUNDLED_SIDON_DIR_BY_PLATFORM = {
    ("Darwin", "arm64"): _PACKAGE_DIR / "bin" / "sidon-cli-macos-arm64",
}
_BUNDLED_MP_SENET_DIR_BY_PLATFORM = {
    ("Darwin", "arm64"): _PACKAGE_DIR / "bin" / "mp-senet-cli-macos-arm64",
}


@dataclass(frozen=True)
class AudioProcessingResult:
    """Rendered audio metadata."""

    output_path: Path
    command: tuple[str, ...]
    duration_ms: int | None = None
    artifact_manifest_path: Path | None = None


def find_ffmpeg(configured_path: str = "") -> Path:  # pragma: no mutate
    """Return an ffmpeg executable path, honoring an optional config override."""
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.is_file():
            return path
    found = shutil.which("ffmpeg")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffmpeg. Please install ffmpeg and make sure it is "
        "available in PATH, or configure its path in the add-on settings."
    )


def find_ffprobe(ffmpeg_path: Path) -> Path:
    """Return ffprobe next to ffmpeg or from PATH."""
    sibling = ffmpeg_path.with_name("ffprobe" + ffmpeg_path.suffix)
    if sibling.is_file():
        return sibling
    found = shutil.which("ffprobe")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffprobe alongside ffmpeg to inspect audio duration."
    )


def find_deep_filter(configured_path: str = "") -> Path:
    """Return a deep-filter executable path, honoring config, bundled binary, then PATH."""
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.is_file():
            return path
    bundled = _bundled_deep_filter_path()
    if bundled is not None:
        return bundled
    found = shutil.which("deep-filter")
    if found:
        return Path(found)
    raise MissingDeepFilterError(
        "DeepFilterNet's deep-filter executable is required for Remove noise and Shorten Pauses. "
        "Install DeepFilterNet and make sure deep-filter is available in PATH, or configure its "
        "path in add-on settings."
    )


def _bundled_deep_filter_path() -> Path | None:
    binary = _BUNDLED_DEEP_FILTER_BY_PLATFORM.get((platform.system(), platform.machine()))
    if binary is not None and binary.is_file():
        return binary
    return None


def expected_bundled_sidon_dir() -> Path | None:
    """Return the expected bundled Sidon directory for the current platform."""
    return _BUNDLED_SIDON_DIR_BY_PLATFORM.get((platform.system(), platform.machine()))


def expected_bundled_sidon_model_dir() -> Path | None:
    """Return the expected bundled Sidon model directory for the current platform."""
    bundled_dir = expected_bundled_sidon_dir()
    if bundled_dir is None:
        return None
    return bundled_dir / "models"


def find_sidon_bundle() -> tuple[Path, Path]:
    """Return the bundled Sidon executable and model directory."""
    bundled_dir = expected_bundled_sidon_dir()
    if bundled_dir is None:
        raise MissingSidonError(
            "Sidon is only bundled for macOS arm64 right now."
        )

    sidon_path = bundled_dir / "bin" / "sidon-cli"
    model_dir = bundled_dir / "models"
    missing_paths = [
        path
        for path in (
            sidon_path,
            model_dir / "feature_extractor_cpu.pt",
            model_dir / "decoder_cpu.pt",
        )
        if not path.is_file()
    ]
    if missing_paths:
        raise MissingSidonError(
            "Sidon requires the bundled sidon-cli runtime and model files. "
            "Reinstall the add-on to restore them."
        )
    return sidon_path, model_dir


def expected_bundled_mp_senet_dir() -> Path | None:
    """Return the expected bundled MP-SENet directory for the current platform."""
    return _BUNDLED_MP_SENET_DIR_BY_PLATFORM.get((platform.system(), platform.machine()))


def expected_bundled_mp_senet_model_path() -> Path | None:
    """Return the expected bundled MP-SENet TorchScript model path."""
    bundled_dir = expected_bundled_mp_senet_dir()
    if bundled_dir is None:
        return None
    return bundled_dir / "models" / "mp_senet_vb.torchscript.pt"


def find_mp_senet_bundle() -> tuple[Path, Path]:
    """Return the bundled MP-SENet executable and TorchScript model path."""
    bundled_dir = expected_bundled_mp_senet_dir()
    if bundled_dir is None:
        raise MissingMpSenetError("MP-SENet is only bundled for macOS arm64 right now.")

    mp_senet_path = bundled_dir / "bin" / "mp-senet-cli"
    model_path = bundled_dir / "models" / "mp_senet_vb.torchscript.pt"
    missing_paths = [
        path
        for path in (
            mp_senet_path,
            bundled_dir / "bin" / "mp-senet-cli-real",
            model_path,
        )
        if not path.is_file()
    ]
    if missing_paths:
        raise MissingMpSenetError(
            "MP-SENet requires the bundled mp-senet-cli runtime and model file. "
            "Reinstall the add-on to restore them."
        )
    return mp_senet_path, model_path


def probe_duration_ms(source_path: Path, config: AudioProcessingConfig) -> int:
    """Inspect an audio file duration with ffprobe."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    ffprobe_path = find_ffprobe(ffmpeg_path)
    cmd = [
        str(ffprobe_path),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(source_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Could not inspect audio duration.")
    try:
        seconds = float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AudioProcessingError("Could not parse audio duration.") from exc
    return max(0, round(seconds * 1000))


def render_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    artifact_root: Path | None = None,
) -> AudioProcessingResult:
    """Render ``state`` from ``source_path`` to an MP3 file."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    duration_ms = probe_duration_ms(source_path, config)
    state.validate(duration_ms, config)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_preview_", suffix=".mp3")[1])

    if state.remove_internal_pauses_enabled:
        return _render_deep_filter_pause_speedup_audio(
            source_path,
            state,
            config,
            ffmpeg_path,
            output_path,
            on_command,
            artifact_root=artifact_root,
            source_duration_ms=duration_ms,
        )

    filters = build_audio_filters(duration_ms, state)
    cmd = build_ffmpeg_command(ffmpeg_path, source_path, filters, output_path)
    if on_command:
        on_command(cmd)
    result = subprocess.run(list(cmd), capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Audio processing failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


def build_ffmpeg_command(
    ffmpeg_path: Path,
    source_path: Path,
    filters: str,
    output_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command used to render a processed MP3."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter:a",
        filters,
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_wav_filter_command(
    ffmpeg_path: Path,
    source_path: Path,
    filters: str,
    output_path: Path,
) -> tuple[str, ...]:
    """Build an ffmpeg command that renders filtered PCM WAV output."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter:a",
        filters,
        "-codec:a",
        "pcm_s16le",
        str(output_path),
    )


def build_deep_filter_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares a 48 kHz mono WAV for DeepFilterNet."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-codec:a",
        "pcm_s16le",
        str(output_wav_path),
    )


def build_deep_filter_command(
    deep_filter_path: Path,
    input_wav_path: Path,
    output_dir: Path,
    *,
    post_filter: bool,
) -> tuple[str, ...]:
    """Build the DeepFilterNet command for one prepared WAV file."""
    command = [
        str(deep_filter_path),
        "-D",
    ]
    if post_filter:
        command.append("--pf")
    command.extend(("-o", str(output_dir), str(input_wav_path)))
    return tuple(command)


def build_silencedetect_command(
    ffmpeg_path: Path,
    source_path: Path,
    *,
    threshold_db: int,
    min_duration_ms: int,
) -> tuple[str, ...]:
    """Build an ffmpeg command that emits silencedetect metadata to stderr."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-af",
        f"silencedetect=noise={threshold_db}dB:d={max(1, int(min_duration_ms)) / 1000:.3f}",
        "-f",
        "null",
        "-",
    )


def build_filter_complex_render_command(
    ffmpeg_path: Path,
    source_path: Path,
    filter_script_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    """Build an ffmpeg command that renders from a filter_complex script."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter_complex_script",
        str(filter_script_path),
        "-map",
        "[out]",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_sidon_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares a PCM WAV for Sidon."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-codec:a",
        "pcm_s16le",
        str(output_wav_path),
    )


def build_mp_senet_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares a 16 kHz mono WAV for MP-SENet."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-codec:a",
        "pcm_s16le",
        str(output_wav_path),
    )


def build_sidon_command(
    sidon_path: Path,
    input_wav_path: Path,
    output_wav_path: Path,
    model_dir: Path,
) -> tuple[str, ...]:
    """Build the Sidon command for one prepared WAV file."""
    return (
        str(sidon_path),
        "restore",
        "--input",
        str(input_wav_path),
        "--output",
        str(output_wav_path),
        "--model-dir",
        str(model_dir),
        "--overwrite",
        "--json",
    )


def build_mp_senet_command(
    mp_senet_path: Path,
    input_wav_path: Path,
    output_wav_path: Path,
    model_path: Path,
) -> tuple[str, ...]:
    """Build the MP-SENet command for one prepared WAV file."""
    return (
        str(mp_senet_path),
        "denoise",
        "--input",
        str(input_wav_path),
        "--output",
        str(output_wav_path),
        "--model",
        str(model_path),
        "--overwrite",
        "--json",
    )


def build_mp3_encode_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command used to encode processed WAV output as MP3."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def select_deep_filter_output(output_dir: Path) -> Path:
    """Return the single WAV generated by DeepFilterNet, or raise a clear error."""
    wav_outputs = sorted(path for path in output_dir.glob("*.wav") if path.is_file())
    if len(wav_outputs) == 1:
        return wav_outputs[0]
    if not wav_outputs:
        raise AudioProcessingError("DeepFilterNet did not produce a WAV output.")
    raise AudioProcessingError("DeepFilterNet produced multiple WAV outputs.")


def _render_deep_filter_pause_speedup_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    artifact_root: Path | None,
    source_duration_ms: int,
) -> AudioProcessingResult:
    deep_filter_path: Path | None = None
    run_dir = _create_pause_pipeline_run_dir(source_path, artifact_root)
    manifest_path = run_dir / "manifest.json"
    attempted_commands: list[dict[str, object]] = []
    stages: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    warnings: list[str] = []
    errors: list[str] = []
    primary_command: tuple[str, ...] = ()
    final_duration_ms: int | None = None
    working_original = run_dir / "01_working_original.wav"
    analysis_input = run_dir / "02_analysis_input_48k_mono.wav"
    deep_filter_output_dir = run_dir / "03_deep_filter_output"
    raw_silence_path = run_dir / "04_silencedetect_stderr.txt"
    intervals_path = run_dir / "04_silence_intervals.json"
    timeline_path = run_dir / "05_timeline.json"
    filter_script_path = run_dir / "06_filter_complex.ffscript"
    final_copy_path = run_dir / "07_final_output.mp3"
    deep_filter_output_dir.mkdir(parents=True, exist_ok=True)

    manifest = _build_pause_pipeline_manifest(
        run_dir,
        source_path,
        state,
        config,
        source_duration_ms,
        stages=stages,
        artifacts=artifacts,
        warnings=warnings,
        errors=errors,
    )

    def write_manifest() -> None:
        manifest["stages"] = stages
        manifest["artifacts"] = artifacts
        manifest["warnings"] = warnings
        manifest["errors"] = errors
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    artifacts.append(_artifact_record("source", source_path, "input"))
    artifacts.append({"id": "manifest", "path": str(manifest_path), "kind": "manifest", "exists": True})
    try:
        deep_filter_path = find_deep_filter(config.deep_filter_path)
        manifest["deep_filter_path"] = str(deep_filter_path)
        write_manifest()
        working_filters = build_working_original_filters(source_duration_ms, state)
        working_cmd = build_wav_filter_command(
            ffmpeg_path,
            source_path,
            working_filters,
            working_original,
        )
        _run_pipeline_stage(
            "render_working_original",
            working_cmd,
            "Could not start working-audio preparation.",
            "Could not prepare working audio for pause shortening.",
            stages,
            attempted_commands,
            on_command,
        )
        artifacts.append(_artifact_record("working_original", working_original, "audio/wav"))
        working_duration_ms = probe_duration_ms(working_original, config)
        manifest["working_duration_ms"] = working_duration_ms
        write_manifest()

        prepare_cmd = build_deep_filter_prepare_command(ffmpeg_path, working_original, analysis_input)
        _run_pipeline_stage(
            "prepare_deep_filter_input",
            prepare_cmd,
            "Could not start DeepFilterNet analysis preparation.",
            "Could not prepare audio for DeepFilterNet pause analysis.",
            stages,
            attempted_commands,
            on_command,
        )
        artifacts.append(_artifact_record("analysis_input", analysis_input, "audio/wav"))
        write_manifest()

        deep_filter_cmd = build_deep_filter_command(
            deep_filter_path,
            analysis_input,
            deep_filter_output_dir,
            post_filter=config.deep_filter_post_filter,
        )
        primary_command = deep_filter_cmd
        _run_pipeline_stage(
            "deep_filter_analysis",
            deep_filter_cmd,
            "Could not start DeepFilterNet pause analysis.",
            "DeepFilterNet pause analysis failed.",
            stages,
            attempted_commands,
            on_command,
        )
        cleaned_analysis_wav = select_deep_filter_output(deep_filter_output_dir)
        artifacts.append(_artifact_record("deep_filter_output", cleaned_analysis_wav, "audio/wav"))
        write_manifest()

        silence_cmd = build_silencedetect_command(
            ffmpeg_path,
            cleaned_analysis_wav,
            threshold_db=config.internal_pause_silence_threshold_db,
            min_duration_ms=config.internal_pause_threshold_ms,
        )
        silence_result = _run_pipeline_stage(
            "detect_silence",
            silence_cmd,
            "Could not start pause detection.",
            "Pause detection failed.",
            stages,
            attempted_commands,
            on_command,
        )
        raw_silence_path.write_text(silence_result.stderr, encoding="utf-8")
        silence_intervals = parse_silencedetect_intervals(
            silence_result.stderr,
            working_duration_ms,
        )
        intervals_json = intervals_to_json(silence_intervals)
        intervals_path.write_text(
            json.dumps(intervals_json, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        manifest["silence_intervals"] = intervals_json
        artifacts.extend(
            [
                _artifact_record("silencedetect_stderr", raw_silence_path, "text/plain"),
                _artifact_record("silence_intervals", intervals_path, "application/json"),
            ]
        )
        write_manifest()

        timeline = plan_pause_timeline(
            working_duration_ms,
            silence_intervals,
            min_pause_ms=config.internal_pause_threshold_ms,
            target_gap_ms=config.internal_pause_target_gap_ms,
        )
        timeline_json = timeline_to_json(timeline)
        timeline_path.write_text(
            json.dumps(timeline_json, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        filter_script = build_filter_complex_script(
            timeline,
            volume_db=state.volume_db,
            speed=state.speed,
        )
        filter_script_path.write_text(filter_script, encoding="utf-8")
        manifest["timeline"] = timeline_json
        artifacts.extend(
            [
                _artifact_record("timeline", timeline_path, "application/json"),
                _artifact_record("filter_complex_script", filter_script_path, "text/plain"),
            ]
        )
        write_manifest()

        render_cmd = build_filter_complex_render_command(
            ffmpeg_path,
            working_original,
            filter_script_path,
            output_path,
        )
        _run_pipeline_stage(
            "render_final_output",
            render_cmd,
            "Could not start pause-shortened audio rendering.",
            "Could not render pause-shortened audio.",
            stages,
            attempted_commands,
            on_command,
        )
        if output_path.resolve() != final_copy_path.resolve():
            shutil.copyfile(output_path, final_copy_path)
        artifacts.append(_artifact_record("final_output", final_copy_path, "audio/mpeg"))
        final_duration_ms = probe_duration_ms(output_path, config)
        manifest["final_output"] = {
            "path": str(output_path),
            "artifact_path": str(final_copy_path),
            "duration_ms": final_duration_ms,
        }
        write_manifest()
        return AudioProcessingResult(
            output_path=output_path,
            command=primary_command or render_cmd,
            duration_ms=final_duration_ms,
            artifact_manifest_path=manifest_path,
        )
    except Exception as exc:
        errors.append(str(exc) or type(exc).__name__)
        manifest["final_output"] = {
            "path": str(output_path),
            "artifact_path": str(final_copy_path),
            "duration_ms": final_duration_ms,
        }
        write_manifest()
        record_latest_pause_pipeline_support_incident(
            operation="deep_filter_pause_speedup",
            media_filename=source_path.name,
            source_path=str(source_path.resolve()),
            user_message=str(exc),
            exception_type=type(exc).__name__,
            ffmpeg_path=str(ffmpeg_path),
            deep_filter_path=str(deep_filter_path) if deep_filter_path is not None else "",
            manifest_path=str(manifest_path),
            artifact_dir=str(run_dir),
            attempted_commands=attempted_commands,
        )
        raise


def render_noise_reduced_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a noise-reduced MP3 using the external DeepFilterNet executable."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    deep_filter_path = find_deep_filter(config.deep_filter_path)
    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_denoised_", suffix=".mp3")[1])

    work_dir = Path(tempfile.mkdtemp(prefix="aqe_deep_filter_"))
    input_wav = work_dir / "input_48k_mono.wav"
    deep_filter_output_dir = work_dir / "deep_filter_output"
    deep_filter_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        prepare_cmd = build_deep_filter_prepare_command(ffmpeg_path, source_path, input_wav)
        if on_command:
            on_command(prepare_cmd)
        prepare_result = _run_external_command(
            prepare_cmd,
            "Could not start audio preparation for DeepFilterNet.",
        )
        if prepare_result.returncode != 0:
            raise AudioProcessingError(
                prepare_result.stderr.strip() or "Could not prepare audio for DeepFilterNet."
            )

        deep_filter_cmd = build_deep_filter_command(
            deep_filter_path,
            input_wav,
            deep_filter_output_dir,
            post_filter=config.deep_filter_post_filter,
        )
        if on_command:
            on_command(deep_filter_cmd)
        deep_filter_result = _run_external_command(
            deep_filter_cmd,
            "Could not start DeepFilterNet noise removal.",
        )
        if deep_filter_result.returncode != 0:
            raise AudioProcessingError(
                deep_filter_result.stderr.strip() or "DeepFilterNet noise removal failed."
            )

        cleaned_wav = select_deep_filter_output(deep_filter_output_dir)
        encode_cmd = build_mp3_encode_command(ffmpeg_path, cleaned_wav, output_path)
        if on_command:
            on_command(encode_cmd)
        encode_result = _run_external_command(
            encode_cmd,
            "Could not start MP3 encoding for DeepFilterNet output.",
        )
        if encode_result.returncode != 0:
            raise AudioProcessingError(
                encode_result.stderr.strip() or "Could not encode DeepFilterNet output."
            )

        return AudioProcessingResult(
            output_path=output_path,
            command=deep_filter_cmd,
            duration_ms=probe_duration_ms(output_path, config),
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def render_sidon_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a speech-restored MP3 using the bundled Sidon executable."""
    ffmpeg_path: Path | None = None
    sidon_path: Path | None = None
    sidon_model_dir: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        sidon_path, sidon_model_dir = find_sidon_bundle()
        if output_path is None:
            output_path = Path(tempfile.mkstemp(prefix="aqe_sidon_", suffix=".mp3")[1])

        work_dir = Path(tempfile.mkdtemp(prefix="aqe_sidon_"))
        input_wav = work_dir / "input_pcm.wav"
        restored_wav = work_dir / "restored.wav"

        prepare_cmd = build_sidon_prepare_command(ffmpeg_path, source_path, input_wav)
        prepare_result = _run_sidon_external_command(
            prepare_cmd,
            "Could not start audio preparation for Sidon.",
            attempted_commands,
            on_command,
        )
        if prepare_result.returncode != 0:
            raise AudioProcessingError(
                _render_external_error_message(
                    prepare_result,
                    "Could not prepare audio for Sidon.",
                )
            )

        sidon_cmd = build_sidon_command(
            sidon_path,
            input_wav,
            restored_wav,
            sidon_model_dir,
        )
        sidon_result = _run_sidon_external_command(
            sidon_cmd,
            "Could not start Sidon speech restoration.",
            attempted_commands,
            on_command,
        )
        if sidon_result.returncode != 0:
            raise AudioProcessingError(
                _render_external_error_message(sidon_result, "Sidon speech restoration failed.")
            )
        if not restored_wav.is_file():
            raise AudioProcessingError("Sidon did not produce a WAV output.")

        encode_cmd = build_mp3_encode_command(ffmpeg_path, restored_wav, output_path)
        encode_result = _run_sidon_external_command(
            encode_cmd,
            "Could not start MP3 encoding for Sidon output.",
            attempted_commands,
            on_command,
        )
        if encode_result.returncode != 0:
            raise AudioProcessingError(
                _render_external_error_message(encode_result, "Could not encode Sidon output.")
            )

        return AudioProcessingResult(
            output_path=output_path,
            command=sidon_cmd,
            duration_ms=probe_duration_ms(output_path, config),
        )
    except Exception as exc:
        _record_sidon_failure(
            source_path,
            exc,
            ffmpeg_path=ffmpeg_path,
            sidon_path=sidon_path,
            sidon_model_dir=sidon_model_dir,
            attempted_commands=attempted_commands,
        )
        raise
    finally:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)


def render_mp_senet_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a denoised MP3 using the bundled MP-SENet executable."""
    ffmpeg_path: Path | None = None
    mp_senet_path: Path | None = None
    mp_senet_model_path: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        mp_senet_path, mp_senet_model_path = find_mp_senet_bundle()
        if output_path is None:
            output_path = Path(tempfile.mkstemp(prefix="aqe_mp_senet_", suffix=".mp3")[1])

        work_dir = Path(tempfile.mkdtemp(prefix="aqe_mp_senet_"))
        input_wav = work_dir / "input_16k_mono.wav"
        denoised_wav = work_dir / "denoised.wav"

        prepare_cmd = build_mp_senet_prepare_command(ffmpeg_path, source_path, input_wav)
        prepare_result = _run_recorded_external_command(
            prepare_cmd,
            "Could not start audio preparation for MP-SENet.",
            attempted_commands,
            on_command,
        )
        if prepare_result.returncode != 0:
            raise AudioProcessingError(
                _render_external_error_message(
                    prepare_result,
                    "Could not prepare audio for MP-SENet.",
                )
            )

        mp_senet_cmd = build_mp_senet_command(
            mp_senet_path,
            input_wav,
            denoised_wav,
            mp_senet_model_path,
        )
        mp_senet_result = _run_recorded_external_command(
            mp_senet_cmd,
            "Could not start MP-SENet denoise.",
            attempted_commands,
            on_command,
        )
        if mp_senet_result.returncode != 0:
            raise AudioProcessingError(
                _render_external_error_message(mp_senet_result, "MP-SENet denoise failed.")
            )
        if not denoised_wav.is_file():
            raise AudioProcessingError("MP-SENet did not produce a WAV output.")

        encode_cmd = build_mp3_encode_command(ffmpeg_path, denoised_wav, output_path)
        encode_result = _run_recorded_external_command(
            encode_cmd,
            "Could not start MP3 encoding for MP-SENet output.",
            attempted_commands,
            on_command,
        )
        if encode_result.returncode != 0:
            raise AudioProcessingError(
                _render_external_error_message(
                    encode_result,
                    "Could not encode MP-SENet output.",
                )
            )

        return AudioProcessingResult(
            output_path=output_path,
            command=mp_senet_cmd,
            duration_ms=probe_duration_ms(output_path, config),
        )
    except Exception as exc:
        _record_mp_senet_failure(
            source_path,
            exc,
            ffmpeg_path=ffmpeg_path,
            mp_senet_path=mp_senet_path,
            mp_senet_model_path=mp_senet_model_path,
            attempted_commands=attempted_commands,
        )
        raise
    finally:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)


def _run_sidon_external_command(
    command: tuple[str, ...],
    launch_error_message: str,
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> subprocess.CompletedProcess[str]:
    return _run_recorded_external_command(
        command,
        launch_error_message,
        attempted_commands,
        on_command,
    )


def _run_recorded_external_command(
    command: tuple[str, ...],
    launch_error_message: str,
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> subprocess.CompletedProcess[str]:
    if on_command:
        on_command(command)
    try:
        result = _run_external_command(command, launch_error_message)
    except AudioProcessingError as exc:
        attempted_commands.append(build_command_record(command, launch_error=str(exc)))
        raise
    attempted_commands.append(
        build_command_record(
            command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    )
    return result


def _record_mp_senet_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    mp_senet_path: Path | None,
    mp_senet_model_path: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_mp_senet_support_incident(
        operation="mp_senet_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        mp_senet_path=str(mp_senet_path) if mp_senet_path is not None else "",
        mp_senet_model_path=str(mp_senet_model_path) if mp_senet_model_path is not None else "",
        attempted_commands=attempted_commands,
    )


def _record_sidon_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    sidon_path: Path | None,
    sidon_model_dir: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_sidon_support_incident(
        operation="sidon_restore",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        sidon_path=str(sidon_path) if sidon_path is not None else "",
        sidon_model_dir=str(sidon_model_dir) if sidon_model_dir is not None else "",
        attempted_commands=attempted_commands,
    )


def _run_external_command(
    command: tuple[str, ...],
    launch_error_message: str,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
        )  # nosec B603
    except OSError as exc:
        raise AudioProcessingError(f"{launch_error_message} {exc}") from exc


def _render_external_error_message(
    result: subprocess.CompletedProcess[str],
    default_message: str,
) -> str:
    for candidate in (result.stderr.strip(), result.stdout.strip()):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return candidate
        if isinstance(parsed, dict):
            error = parsed.get("error")
            if isinstance(error, str) and error.strip():
                return error.strip()
        return candidate
    return default_message


def _create_pause_pipeline_run_dir(source_path: Path, artifact_root: Path | None) -> Path:
    root = artifact_root or (_PACKAGE_DIR / "aqe_artifacts")
    run_dir = Path(root).expanduser() / make_pause_pipeline_run_id(source_path.name)
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _build_pause_pipeline_manifest(
    run_dir: Path,
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    source_duration_ms: int,
    *,
    stages: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    warnings: list[str],
    errors: list[str],
) -> dict[str, object]:
    return {
        "schema_version": PAUSE_PIPELINE_MANIFEST_VERSION,
        "run_id": run_dir.name,
        "created_at": datetime.now().isoformat(),
        "operation": "deep_filter_pause_speedup",
        "artifact_dir": str(run_dir),
        "source": _source_file_record(source_path, source_duration_ms),
        "state": {
            "source_file": state.source_file,
            "left_trim_ms": state.left_trim_ms,
            "right_trim_ms": state.right_trim_ms,
            "speed": state.speed,
            "volume_db": state.volume_db,
            "remove_internal_pauses_enabled": state.remove_internal_pauses_enabled,
        },
        "config": _pause_pipeline_config_snapshot(config),
        "stages": stages,
        "artifacts": artifacts,
        "silence_intervals": [],
        "timeline": [],
        "warnings": warnings,
        "errors": errors,
        "working_duration_ms": None,
        "final_output": None,
    }


def _source_file_record(source_path: Path, duration_ms: int) -> dict[str, object]:
    stat = source_path.stat()
    return {
        "filename": source_path.name,
        "path": str(source_path),
        "duration_ms": duration_ms,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": _sha256_file(source_path),
    }


def _pause_pipeline_config_snapshot(config: AudioProcessingConfig) -> dict[str, object]:
    return {
        "ffmpeg_path": config.ffmpeg_path,
        "deep_filter_path": config.deep_filter_path,
        "deep_filter_post_filter": config.deep_filter_post_filter,
        "internal_pause_silence_threshold_db": config.internal_pause_silence_threshold_db,
        "internal_pause_threshold_ms": config.internal_pause_threshold_ms,
        "internal_pause_target_gap_ms": config.internal_pause_target_gap_ms,
        "speed": {
            "min": config.min_speed,
            "max": config.max_speed,
        },
        "output_format": config.output_format,
    }


def _artifact_record(artifact_id: str, path: Path, kind: str) -> dict[str, object]:
    exists = path.exists()
    record: dict[str, object] = {
        "id": artifact_id,
        "path": str(path),
        "kind": kind,
        "exists": exists,
    }
    if path.is_file():
        stat = path.stat()
        record["size_bytes"] = stat.st_size
        record["sha256"] = _sha256_file(path)
    return record


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_pipeline_stage(
    name: str,
    command: tuple[str, ...],
    launch_error_message: str,
    failure_message: str,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> subprocess.CompletedProcess[str]:
    if on_command:
        on_command(command)
    started = time.monotonic()
    stage: dict[str, object] = {
        "name": name,
        "argv": list(command),
        "command": shlex.join(command),
    }
    try:
        result = _run_external_command(command, launch_error_message)
    except AudioProcessingError as exc:
        stage["duration_seconds"] = round(time.monotonic() - started, 6)
        stage["launch_error"] = str(exc)
        stages.append(stage)
        attempted_commands.append(build_command_record(command, launch_error=str(exc)))
        raise

    stage.update(
        {
            "duration_seconds": round(time.monotonic() - started, 6),
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    )
    stages.append(stage)
    attempted_commands.append(
        build_command_record(
            command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    )
    if result.returncode != 0:
        raise AudioProcessingError(_render_external_error_message(result, failure_message))
    return result


def render_playback_segment(
    source_path: Path,
    start_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a temporary cursor-to-end segment for deterministic playback."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    duration_ms = probe_duration_ms(source_path, config)
    clamped_start_ms = max(0, min(int(start_ms), duration_ms))
    if clamped_start_ms >= max(0, duration_ms - 20):
        raise AudioProcessingError("Cursor is at the end of the audio.")

    if output_path is None:
        output_path = temp_playback_path(source_path.name, clamped_start_ms)

    filters = build_playback_segment_filters(clamped_start_ms)
    cmd = build_ffmpeg_command(ffmpeg_path, source_path, filters, output_path)
    if on_command:
        on_command(cmd)
    result = subprocess.run(list(cmd), capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Playback segment rendering failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


def build_playback_segment_filters(start_ms: int) -> str:
    """Build filters for a temporary cursor-to-end playback segment."""
    start_s = max(0, int(start_ms)) / 1000
    return f"atrim=start={start_s:.3f},asetpts=PTS-STARTPTS"


def format_ffmpeg_command(command: tuple[str, ...]) -> str:
    """Return a shell-style ffmpeg command string for user-facing diagnostics."""
    return shlex.join(command)


def build_audio_filters(
    duration_ms: int,
    state: AudioEditState,
) -> str:
    """Build the ffmpeg audio filter chain for an edit state."""
    filters = build_working_original_filters(duration_ms, state).split(",")

    if not math.isclose(state.volume_db, 0.0):
        filters.append(f"volume={state.volume_db:.2f}dB")

    if not math.isclose(state.speed, 1.0):
        filters.extend(_atempo_filters(state.speed))
    return ",".join(filters)


def build_working_original_filters(
    duration_ms: int,
    state: AudioEditState,
) -> str:
    """Build filters for original-derived audio before pause speed-up analysis."""
    filters: list[str] = []
    start_s = state.left_trim_ms / 1000
    end_s = (duration_ms - state.right_trim_ms) / 1000
    filters.append(f"atrim=start={start_s:.3f}:end={end_s:.3f}")
    filters.append("asetpts=PTS-STARTPTS")

    return ",".join(filters)


def make_output_filename(
    source_filename: str,
    now: datetime | None = None,
    token: str | None = None,
) -> str:
    """Return the preferred generated MP3 filename for a final save."""
    now = now or datetime.now()
    token = token or uuid.uuid4().hex[:8]
    stem = Path(source_filename).stem or "audio"
    safe_stem = _safe_filename_stem(stem)
    suffix = f"__aqe_{now:%Y%m%d_%H%M%S_%f}_{token}.mp3"
    max_stem_length = max(1, 120 - len(suffix))  # pragma: no mutate
    return f"{safe_stem[:max_stem_length]}{suffix}"


def _safe_filename_stem(stem: str) -> str:
    safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in stem)  # pragma: no mutate
    safe = "_".join(part for part in safe.split("_") if part)
    return safe or "audio"


def temp_final_path(filename: str) -> Path:
    """Return a temp path preserving a final desired basename for diagnostics."""
    temp_dir = Path(tempfile.mkdtemp(prefix="aqe_final_"))
    return temp_dir / os.path.basename(filename)


def make_playback_segment_filename(
    source_filename: str,
    start_ms: int,
    token: str | None = None,
) -> str:
    """Return a debuggable temp filename for cursor playback segments."""
    token = token or uuid.uuid4().hex[:8]  # pragma: no mutate
    stem = _safe_filename_stem(Path(source_filename).stem or "audio")  # pragma: no mutate
    suffix = f"__from_{max(0, int(start_ms))}ms_{token}.mp3"
    prefix = "aqe_playback_"
    max_stem_length = max(1, 160 - len(prefix) - len(suffix))  # pragma: no mutate
    return f"{prefix}{stem[:max_stem_length]}{suffix}"


def temp_playback_path(source_filename: str, start_ms: int) -> Path:
    """Return a temp path for a cursor-to-end playback segment."""
    temp_dir = Path(tempfile.mkdtemp(prefix="aqe_playback_"))  # pragma: no mutate
    return temp_dir / make_playback_segment_filename(source_filename, start_ms)


def _atempo_filters(speed: float) -> list[str]:
    remaining = speed
    filters: list[str] = []
    while remaining > 2.0:
        filters.append("atempo=2.000")
        remaining /= 2.0  # pragma: no mutate
    while remaining < 0.5:
        filters.append("atempo=0.500")
        remaining /= 0.5  # pragma: no mutate
    filters.append(f"atempo={remaining:.3f}")
    return filters
