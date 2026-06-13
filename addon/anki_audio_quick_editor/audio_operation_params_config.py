"""Config application for shared audio operation parameters."""

from __future__ import annotations

from dataclasses import replace

from .audio_operation_params_types import AudioOperationParameters
from .audio_pause_settings import (
    PauseDetectionPreset,
    bool_or_default,
    clamp_pause_threshold,
    pause_detection_algorithm_or_default,
    preset_for_pause_detection,
)
from .audio_size_reduction import size_reduction_encoder_params_for_mode
from .audio_state import AudioProcessingConfig


def effective_config_for_operation(
    operation: str,
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    """Return the render config after applying operation-local parameters."""
    if operation == "graph":
        return config
    if operation == "convert":
        return _config_for_convert_operation(config, parameters)
    if operation == "reduce_size":
        return _config_for_size_reduction(config, parameters)
    effective = _config_with_shared_operation_parameters(config, parameters)
    if operation != "remove_pauses":
        return effective
    return config_for_pause_parameters(effective, parameters)


def config_for_pause_parameters(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    """Return config with operation-local pause detector parameters applied."""
    algorithm = pause_detection_algorithm_or_default(
        parameters.pause_detection_algorithm or config.pause_detection_algorithm
    )
    aggressiveness = parameters.pause_aggressiveness or config.pause_aggressiveness
    explicit_params = (
        parameters.pause_threshold is not None
        or parameters.pause_min_silence_seconds is not None
        or parameters.pause_min_speech_seconds is not None
        or parameters.pause_preprocess_denoise is not None
    )
    preset = preset_for_pause_detection(algorithm, aggressiveness)
    if algorithm == "silero_vad":
        return _config_with_silero_pause_parameters(
            config,
            aggressiveness,
            parameters,
            preset if not explicit_params else None,
        )
    return _config_with_silencedetect_pause_parameters(
        config,
        aggressiveness,
        parameters,
        preset if not explicit_params else None,
    )


def _config_for_convert_operation(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    return replace(config, output_format=parameters.target_format or config.output_format)


def _config_for_size_reduction(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    mode = parameters.size_reduction_mode or config.size_reduction_mode
    bitrate_kbps, sample_rate_hz, channels = _size_reduction_encoder_values(
        config,
        parameters,
        mode,
    )
    return replace(
        config,
        size_reduction_mode=mode,
        size_reduction_bitrate_kbps=bitrate_kbps,
        size_reduction_sample_rate_hz=sample_rate_hz,
        size_reduction_channels=channels,
    )


def _size_reduction_encoder_values(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
    mode: str,
) -> tuple[int, int, int]:
    if _should_use_size_reduction_mode_defaults(parameters):
        mode_defaults = size_reduction_encoder_params_for_mode(mode)
        return (
            mode_defaults.bitrate_kbps,
            mode_defaults.sample_rate_hz,
            mode_defaults.channels,
        )
    return (
        _parameter_or_config(
            parameters.size_reduction_bitrate_kbps,
            config.size_reduction_bitrate_kbps,
        ),
        _parameter_or_config(
            parameters.size_reduction_sample_rate_hz,
            config.size_reduction_sample_rate_hz,
        ),
        _parameter_or_config(parameters.size_reduction_channels, config.size_reduction_channels),
    )


def _should_use_size_reduction_mode_defaults(
    parameters: AudioOperationParameters,
) -> bool:
    return parameters.size_reduction_mode is not None and not any(
        value is not None
        for value in (
            parameters.size_reduction_bitrate_kbps,
            parameters.size_reduction_sample_rate_hz,
            parameters.size_reduction_channels,
        )
    )


def _parameter_or_config(parameter_value: int | None, config_value: int) -> int:
    return parameter_value if parameter_value is not None else config_value


def _config_with_shared_operation_parameters(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    return replace(
        config,
        volume_step_db=parameters.volume_step_db or config.volume_step_db,
        speed_step=parameters.speed_step or config.speed_step,
        denoise_algorithm=parameters.denoise_algorithm or config.denoise_algorithm,
        dpdfnet_attn_limit_db=_operation_dpdfnet_attn_limit_db(config, parameters),
    )


def _operation_dpdfnet_attn_limit_db(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> float:
    if parameters.dpdfnet_attn_limit_db is None:
        return config.dpdfnet_attn_limit_db
    return parameters.dpdfnet_attn_limit_db


def _config_with_silencedetect_pause_parameters(
    config: AudioProcessingConfig,
    aggressiveness: str,
    parameters: AudioOperationParameters,
    preset: PauseDetectionPreset | None,
) -> AudioProcessingConfig:
    return replace(
        config,
        pause_aggressiveness=aggressiveness,
        pause_detection_algorithm="silencedetect",
        pause_silencedetect_threshold_db=clamp_pause_threshold(
            "silencedetect",
            preset.threshold
            if preset is not None
            else (
                parameters.pause_threshold
                if parameters.pause_threshold is not None
                else config.pause_silencedetect_threshold_db
            ),
            config.pause_silencedetect_threshold_db,
        ),
        pause_silencedetect_min_silence_seconds=(
            preset.min_silence_seconds
            if preset is not None
            else parameters.pause_min_silence_seconds
            or config.pause_silencedetect_min_silence_seconds
        ),
        pause_silencedetect_min_speech_seconds=(
            preset.min_speech_seconds
            if preset is not None
            else parameters.pause_min_speech_seconds
            or config.pause_silencedetect_min_speech_seconds
        ),
        pause_silencedetect_preprocess_denoise=(
            preset.preprocess_denoise
            if preset is not None
            else bool_or_default(
                parameters.pause_preprocess_denoise,
                config.pause_silencedetect_preprocess_denoise,
            )
        ),
    )


def _config_with_silero_pause_parameters(
    config: AudioProcessingConfig,
    aggressiveness: str,
    parameters: AudioOperationParameters,
    preset: PauseDetectionPreset | None,
) -> AudioProcessingConfig:
    return replace(
        config,
        pause_aggressiveness=aggressiveness,
        pause_detection_algorithm="silero_vad",
        pause_silero_threshold=clamp_pause_threshold(
            "silero_vad",
            preset.threshold
            if preset is not None
            else (
                parameters.pause_threshold
                if parameters.pause_threshold is not None
                else config.pause_silero_threshold
            ),
            config.pause_silero_threshold,
        ),
        pause_silero_min_silence_seconds=(
            preset.min_silence_seconds
            if preset is not None
            else parameters.pause_min_silence_seconds or config.pause_silero_min_silence_seconds
        ),
        pause_silero_min_speech_seconds=(
            preset.min_speech_seconds
            if preset is not None
            else parameters.pause_min_speech_seconds or config.pause_silero_min_speech_seconds
        ),
        pause_silero_preprocess_denoise=(
            preset.preprocess_denoise
            if preset is not None
            else bool_or_default(
                parameters.pause_preprocess_denoise,
                config.pause_silero_preprocess_denoise,
            )
        ),
    )
