from anki_audio_quick_editor.audio_operation_params import (
    AudioOperationParameters,
    effective_config_for_operation,
    parameters_from_raw,
)
from anki_audio_quick_editor.audio_operations import (
    OP_FASTER,
    OP_GRAPH,
    OP_REMOVE_PAUSES,
    OP_VOLUME_UP,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig


def test_parameters_from_raw_clamps_editor_matching_ranges() -> None:
    params = parameters_from_raw(
        trim_step_ms=10,
        volume_step_db=99,
        speed_step=0.001,
        pause_aggressiveness="invalid",
    )

    assert params.trim_step_ms == 50
    assert params.volume_step_db == 12.0
    assert params.speed_step == 0.01
    assert params.pause_aggressiveness is None


def test_effective_config_uses_volume_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(volume_step_db=3.0)
    params = AudioOperationParameters(volume_step_db=6.0)

    effective = effective_config_for_operation(OP_VOLUME_UP, config, params)

    assert effective.volume_step_db == 6.0
    assert config.volume_step_db == 3.0


def test_effective_config_uses_speed_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(speed_step=0.05)
    params = AudioOperationParameters(speed_step=0.1)

    effective = effective_config_for_operation(OP_FASTER, config, params)

    assert effective.speed_step == 0.1
    assert config.speed_step == 0.05


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
    assert effective.internal_pause_silence_threshold_db == -50
    assert effective.internal_pause_threshold_ms == 180
    assert effective.internal_pause_target_gap_ms == 60


def test_effective_config_ignores_parameters_for_graph() -> None:
    config = AudioProcessingConfig(speed_step=0.05, volume_step_db=3.0)
    params = AudioOperationParameters(
        speed_step=0.1,
        volume_step_db=6.0,
        pause_aggressiveness="aggressive",
    )

    assert effective_config_for_operation(OP_GRAPH, config, params) == config
