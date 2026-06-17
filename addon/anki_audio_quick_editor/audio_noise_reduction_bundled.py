"""Bundled RNNoise, DPDFNet, and Spleeter renderers."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tempfile
from collections.abc import Callable
from pathlib import Path

from .audio_commands import (
    build_audio_encode_command,
    build_dpdfnet_command,
    build_rnnoise_command,
    build_rnnoise_encode_command,
    build_rnnoise_prepare_command,
    build_spleeter_command,
    build_spleeter_prepare_command,
)
from .audio_external import (
    probe_duration_ms,
    render_external_error_message,
    run_external_command,
)
from .audio_noise_reduction_telemetry import (
    record_dpdfnet_failure,
    record_rnnoise_failure,
    record_spleeter_failure,
)
from .audio_output_policy import (
    AudioOutputPolicy,
    AudioSourceMetadata,
    codec_args_for_output_policy,
    preserve_source_audio_characteristics,
    probe_audio_metadata,
    resolve_output_policy_from_metadata,
    synthetic_audio_metadata,
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
)

DENOISE_EXTERNAL_TIMEOUT_SECONDS = 20 * 60


def render_rnnoise_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render denoised audio using the bundled RNNoise executable."""
    ffmpeg_path: Path | None = None
    rnnoise_path: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        rnnoise_path = find_rnnoise_bundle()
        output_policy = _model_output_policy(
            source_path,
            config,
            output_path,
            codec_name="pcm_s16le",
            sample_rate=48000,
            channels=1,
            bits_per_raw_sample=16,
        )
        output_path = output_path or Path(tempfile.mkstemp(prefix="aqe_rnnoise_", suffix=output_policy.extension)[1])
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
                build_rnnoise_encode_command(
                    ffmpeg_path,
                    denoised_raw,
                    output_path,
                    codec_args_for_output_policy(output_policy),
                ),
                "Could not start final encoding for RNNoise output.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not encode RNNoise output.",
        )
        return AudioProcessingResult(output_path=output_path, command=rnnoise_cmd, duration_ms=probe_duration_ms(output_path, config))
    except Exception as exc:
        record_rnnoise_failure(source_path, exc, ffmpeg_path=ffmpeg_path, rnnoise_path=rnnoise_path, attempted_commands=attempted_commands)
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
    """Render denoised audio using the bundled DPDFNet executable."""
    ffmpeg_path: Path | None = None
    dpdfnet_path: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        dpdfnet_path = find_dpdfnet_bundle()
        source_metadata = probe_audio_metadata(source_path, config)
        output_policy = _model_output_policy(
            source_path,
            config,
            output_path,
            source_metadata=source_metadata,
            codec_name="pcm_s16le",
            sample_rate=None,
            channels=None,
            bits_per_raw_sample=16,
        )
        output_path = output_path or Path(tempfile.mkstemp(prefix="aqe_dpdfnet_", suffix=output_policy.extension)[1])
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
                build_audio_encode_command(
                    ffmpeg_path,
                    denoised_wav,
                    output_path,
                    codec_args_for_output_policy(output_policy),
                ),
                "Could not start final encoding for DPDFNet output.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not encode DPDFNet output.",
        )
        return AudioProcessingResult(output_path=output_path, command=dpdfnet_cmd, duration_ms=probe_duration_ms(output_path, config))
    except Exception as exc:
        record_dpdfnet_failure(source_path, exc, ffmpeg_path=ffmpeg_path, dpdfnet_path=dpdfnet_path, attempted_commands=attempted_commands)
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
    """Render audio containing only the Spleeter vocals stem."""
    ffmpeg_path: Path | None = None
    spleeter_path: Path | None = None
    vocals_model_path: Path | None = None
    accompaniment_model_path: Path | None = None
    attempted_commands: list[dict[str, object]] = []
    work_dir: Path | None = None
    try:
        ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
        spleeter_path, vocals_model_path, accompaniment_model_path = find_spleeter_bundle()
        output_policy = _model_output_policy(
            source_path,
            config,
            output_path,
            codec_name="pcm_s16le",
            sample_rate=44100,
            channels=2,
            bits_per_raw_sample=16,
        )
        output_path = output_path or Path(tempfile.mkstemp(prefix="aqe_voice_only_", suffix=output_policy.extension)[1])
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
                build_audio_encode_command(
                    ffmpeg_path,
                    vocals_wav,
                    output_path,
                    codec_args_for_output_policy(output_policy),
                ),
                "Could not start final encoding for Voice Only output.",
                attempted_commands,
                on_command,
                timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
            ),
            "Could not encode Voice Only output.",
        )
        return AudioProcessingResult(output_path=output_path, command=spleeter_cmd, duration_ms=probe_duration_ms(output_path, config))
    except Exception as exc:
        record_spleeter_failure(
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


def _model_output_policy(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None,
    *,
    source_metadata: AudioSourceMetadata | None = None,
    codec_name: str | None,
    sample_rate: int | None,
    channels: int | None,
    bits_per_raw_sample: int | None,
) -> AudioOutputPolicy:
    metadata = synthetic_audio_metadata(
        source_path,
        output_path=output_path or source_path,
        codec_name=codec_name,
        sample_rate=sample_rate,
        channels=channels,
        bits_per_raw_sample=bits_per_raw_sample,
    )
    if source_metadata is None:
        try:
            source_metadata = probe_audio_metadata(source_path, config)
        except AudioProcessingError:
            source_metadata = None
    return resolve_output_policy_from_metadata(
        preserve_source_audio_characteristics(metadata, source_metadata)
        if source_metadata is not None
        else metadata,
        requested_format=config.output_format,
        output_path=output_path,
    )


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
        result = run_external_command(command, launch_error_message, timeout_seconds=timeout_seconds, env=env)
    except AudioProcessingError as exc:
        attempted_commands.append(build_command_record(command, launch_error=str(exc)))
        raise
    attempted_commands.append(build_command_record(command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    return result


def _ensure_stage_success(result: subprocess.CompletedProcess[str], failure_message: str) -> None:
    if result.returncode != 0:
        raise AudioProcessingError(render_external_error_message(result, failure_message))
