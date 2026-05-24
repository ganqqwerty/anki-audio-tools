"""Bundled RNNoise, DPDFNet, and Spleeter renderers."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tempfile
from collections.abc import Callable
from pathlib import Path

from .audio_commands import (
    build_dpdfnet_command,
    build_mp3_encode_command,
    build_rnnoise_command,
    build_rnnoise_encode_command,
    build_rnnoise_prepare_command,
    build_spleeter_command,
    build_spleeter_prepare_command,
)
from .audio_external import (
    _render_external_error_message,
    _run_external_command,
    probe_duration_ms,
)
from .audio_state import AudioProcessingConfig
from .audio_tools import (
    find_dpdfnet_bundle,
    find_ffmpeg,
    find_rnnoise_bundle,
    find_spleeter_bundle,
)
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError
from .support import (
    build_command_record,
    record_latest_denoise_support_incident,
    record_latest_spleeter_support_incident,
)

DENOISE_EXTERNAL_TIMEOUT_SECONDS = 20 * 60


def render_rnnoise_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a denoised MP3 using the bundled RNNoise executable."""
    ffmpeg_path: Path | None = None
    rnnoise_path: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        rnnoise_path = find_rnnoise_bundle()
        output_path = output_path or Path(tempfile.mkstemp(prefix="aqe_rnnoise_", suffix=".mp3")[1])
        work_dir = Path(tempfile.mkdtemp(prefix="aqe_rnnoise_"))
        input_raw = work_dir / "input_48k_mono.s16le"
        denoised_raw = work_dir / "denoised.s16le"
        _ensure_stage_success(
            _run_recorded_external_command(
                build_rnnoise_prepare_command(ffmpeg_path, source_path, input_raw),
                "Could not start audio preparation for RNNoise.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not prepare audio for RNNoise.",
        )
        rnnoise_cmd = build_rnnoise_command(rnnoise_path, input_raw, denoised_raw)
        _ensure_stage_success(
            _run_recorded_external_command(
                rnnoise_cmd,
                "Could not start RNNoise denoise.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "RNNoise denoise failed.",
        )
        if not denoised_raw.is_file():
            raise AudioProcessingError("RNNoise did not produce a raw PCM output.")
        _ensure_stage_success(
            _run_recorded_external_command(
                build_rnnoise_encode_command(ffmpeg_path, denoised_raw, output_path),
                "Could not start MP3 encoding for RNNoise output.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not encode RNNoise output.",
        )
        return AudioProcessingResult(output_path=output_path, command=rnnoise_cmd, duration_ms=probe_duration_ms(output_path, config))
    except Exception as exc:
        _record_rnnoise_failure(source_path, exc, ffmpeg_path=ffmpeg_path, rnnoise_path=rnnoise_path, attempted_commands=attempted_commands)
        raise
    finally:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)


def render_dpdfnet_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a denoised MP3 using the bundled DPDFNet executable."""
    ffmpeg_path: Path | None = None
    dpdfnet_path: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        dpdfnet_path = find_dpdfnet_bundle()
        output_path = output_path or Path(tempfile.mkstemp(prefix="aqe_dpdfnet_", suffix=".mp3")[1])
        work_dir = Path(tempfile.mkdtemp(prefix="aqe_dpdfnet_"))
        denoised_wav = work_dir / "denoised.wav"
        dpdfnet_cmd = build_dpdfnet_command(dpdfnet_path, source_path, denoised_wav, attn_limit_db=config.dpdfnet_attn_limit_db)
        _ensure_stage_success(
            _run_recorded_external_command(
                dpdfnet_cmd,
                "Could not start DPDFNet denoise.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
                env={"DPDFNET_FFMPEG": str(ffmpeg_path)},
            ),
            "DPDFNet denoise failed.",
        )
        if not denoised_wav.is_file():
            raise AudioProcessingError("DPDFNet did not produce a WAV output.")
        _ensure_stage_success(
            _run_recorded_external_command(
                build_mp3_encode_command(ffmpeg_path, denoised_wav, output_path),
                "Could not start MP3 encoding for DPDFNet output.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not encode DPDFNet output.",
        )
        return AudioProcessingResult(output_path=output_path, command=dpdfnet_cmd, duration_ms=probe_duration_ms(output_path, config))
    except Exception as exc:
        _record_dpdfnet_failure(source_path, exc, ffmpeg_path=ffmpeg_path, dpdfnet_path=dpdfnet_path, attempted_commands=attempted_commands)
        raise
    finally:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)


def render_voice_only_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render an MP3 containing only the Spleeter vocals stem."""
    ffmpeg_path: Path | None = None
    spleeter_path: Path | None = None
    vocals_model_path: Path | None = None
    accompaniment_model_path: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        spleeter_path, vocals_model_path, accompaniment_model_path = find_spleeter_bundle()
        output_path = output_path or Path(tempfile.mkstemp(prefix="aqe_voice_only_", suffix=".mp3")[1])
        work_dir = Path(tempfile.mkdtemp(prefix="aqe_spleeter_"))
        input_wav = work_dir / "input_44k_stereo.wav"
        output_dir = work_dir / "spleeter_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        vocals_wav = output_dir / "vocals.wav"
        _ensure_stage_success(
            _run_recorded_external_command(
                build_spleeter_prepare_command(ffmpeg_path, source_path, input_wav),
                "Could not start audio preparation for Voice Only.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not prepare audio for Voice Only.",
        )
        spleeter_cmd = build_spleeter_command(
            spleeter_path,
            vocals_model_path,
            accompaniment_model_path,
            input_wav,
            output_dir,
        )
        _ensure_stage_success(
            _run_recorded_external_command(
                spleeter_cmd,
                "Could not start Voice Only extraction.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Voice Only extraction failed.",
        )
        if not vocals_wav.is_file():
            raise AudioProcessingError("Voice Only extraction did not produce vocals.wav.")
        _ensure_stage_success(
            _run_recorded_external_command(
                build_mp3_encode_command(ffmpeg_path, vocals_wav, output_path),
                "Could not start MP3 encoding for Voice Only output.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not encode Voice Only output.",
        )
        return AudioProcessingResult(output_path=output_path, command=spleeter_cmd, duration_ms=probe_duration_ms(output_path, config))
    except Exception as exc:
        _record_spleeter_failure(
            source_path,
            exc,
            ffmpeg_path=ffmpeg_path,
            spleeter_path=spleeter_path,
            vocals_model_path=vocals_model_path,
            accompaniment_model_path=accompaniment_model_path,
            attempted_commands=attempted_commands,
        )
        raise
    finally:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)


def _run_recorded_external_command(
    command: tuple[str, ...],
    launch_error_message: str,
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    if on_command:
        on_command(command)
    try:
        result = _run_external_command(command, launch_error_message, timeout_seconds=timeout_seconds, env=env)
    except AudioProcessingError as exc:
        attempted_commands.append(build_command_record(command, launch_error=str(exc)))
        raise
    attempted_commands.append(build_command_record(command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    return result


def _ensure_stage_success(result: subprocess.CompletedProcess[str], failure_message: str) -> None:
    if result.returncode != 0:
        raise AudioProcessingError(_render_external_error_message(result, failure_message))


def _record_rnnoise_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    rnnoise_path: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_denoise_support_incident(
        operation="rnnoise_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        rnnoise_path=str(rnnoise_path) if rnnoise_path is not None else "",
        attempted_commands=attempted_commands,
    )


def _record_dpdfnet_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    dpdfnet_path: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_denoise_support_incident(
        operation="dpdfnet_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        dpdfnet_path=str(dpdfnet_path) if dpdfnet_path is not None else "",
        attempted_commands=attempted_commands,
    )


def _record_spleeter_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    spleeter_path: Path | None,
    vocals_model_path: Path | None,
    accompaniment_model_path: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_spleeter_support_incident(
        operation="voice_only",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        spleeter_path=str(spleeter_path) if spleeter_path is not None else "",
        vocals_model_path=str(vocals_model_path) if vocals_model_path is not None else "",
        accompaniment_model_path=str(accompaniment_model_path) if accompaniment_model_path is not None else "",
        attempted_commands=attempted_commands,
    )
