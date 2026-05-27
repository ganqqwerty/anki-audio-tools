from anki_audio_quick_editor.audio_operation_params import (
    AudioOperationParameters,
    effective_config_for_operation,
    parameters_from_raw,
)
from anki_audio_quick_editor.audio_operations import (
    OP_CONVERT,
    OP_DENOISE,
    OP_FASTER,
    OP_GRAPH,
    OP_REMOVE_PAUSES,
    OP_VOLUME_UP,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig


def test_parameters_from_raw_clamps_editor_matching_ranges() -> None:
    params = parameters_from_raw(
        volume_step_db=99,
        speed_step=0.001,
        pause_aggressiveness="invalid",
        pause_detection_algorithm="invalid",
        denoise_algorithm="invalid",
        dpdfnet_attn_limit_db=17.4,
        target_format=" FLAC ",
    )

    assert params.volume_step_db == 40.0
    assert params.speed_step == 1.01
    assert params.pause_aggressiveness is None
    assert params.pause_detection_algorithm is None
    assert params.denoise_algorithm is None
    assert params.dpdfnet_attn_limit_db == 18.0
    assert params.target_format == "flac"


def test_effective_config_uses_volume_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(volume_step_db=3.0)
    params = AudioOperationParameters(volume_step_db=6.0)

    effective = effective_config_for_operation(OP_VOLUME_UP, config, params)

    assert effective.volume_step_db == 6.0
    assert config.volume_step_db == 3.0


def test_effective_config_uses_speed_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(speed_step=1.5)
    params = AudioOperationParameters(speed_step=2.0)

    effective = effective_config_for_operation(OP_FASTER, config, params)

    assert effective.speed_step == 2.0
    assert config.speed_step == 1.5


def test_effective_config_uses_pause_aggressiveness_override() -> None:
    config = AudioProcessingConfig(
        internal_pause_silence_threshold_db=-45,
        internal_pause_threshold_ms=300,
        internal_pause_target_gap_ms=100,
        pause_aggressiveness="normal",
    )
    params = AudioOperationParameters(pause_aggressiveness="aggressive")

    effective = effective_config_for_operation(OP_REMOVE_PAUSES, config, params)

    assert effective.pause_aggressiveness == "aggressive"
    assert effective.internal_pause_silence_threshold_db == -52
    assert effective.internal_pause_threshold_ms == 140
    assert effective.internal_pause_target_gap_ms == 45


def test_effective_config_uses_pause_detection_algorithm_override() -> None:
    config = AudioProcessingConfig(
        pause_aggressiveness="normal",
        pause_detection_algorithm="deep_filter",
    )
    params = AudioOperationParameters(
        pause_aggressiveness="gentle",
        pause_detection_algorithm="silero_vad",
    )

    effective = effective_config_for_operation(OP_REMOVE_PAUSES, config, params)

    assert effective.pause_aggressiveness == "gentle"
    assert effective.pause_detection_algorithm == "silero_vad"


def test_effective_config_uses_denoise_parameter_overrides() -> None:
    config = AudioProcessingConfig(denoise_algorithm="standard", dpdfnet_attn_limit_db=12.0)
    params = AudioOperationParameters(denoise_algorithm="dpdfnet", dpdfnet_attn_limit_db=18.0)

    effective = effective_config_for_operation(OP_DENOISE, config, params)

    assert effective.denoise_algorithm == "dpdfnet"
    assert effective.dpdfnet_attn_limit_db == 18.0
    assert config.denoise_algorithm == "standard"


def test_effective_config_ignores_parameters_for_graph() -> None:
    config = AudioProcessingConfig(speed_step=0.05, volume_step_db=3.0)
    params = AudioOperationParameters(
        speed_step=0.1,
        volume_step_db=6.0,
        pause_aggressiveness="aggressive",
    )

    assert effective_config_for_operation(OP_GRAPH, config, params) == config


def test_effective_config_uses_convert_target_format() -> None:
    config = AudioProcessingConfig(output_format="mp3")
    params = AudioOperationParameters(target_format="flac")

    effective = effective_config_for_operation(OP_CONVERT, config, params)

    assert effective.output_format == "flac"
    assert config.output_format == "mp3"
