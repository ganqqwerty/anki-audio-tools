from anki_audio_quick_editor.audio_operations import (
    OP_CONVERT,
    OP_DENOISE,
    OP_FASTER,
    OP_GRAPH,
    OP_PRESET,
    OP_REDUCE_SIZE,
    OP_REMOVE_PAUSES,
)
from anki_audio_quick_editor.audio_processing_presets import presets_from_raw
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import FieldGroup
from anki_audio_quick_editor.browser_dialog_state import (
    batch_error_payload,
    batch_finish_payload,
    batch_progress_payload,
    build_batch_initial_state,
    request_from_batch_start_payload,
)
from anki_audio_quick_editor.browser_report import BatchRunReport
from anki_audio_quick_editor.error_codes import AQE_BATCH_INVALID_REQUEST, coded_error


def test_build_batch_initial_state_contains_operations_fields_defaults_and_i18n() -> None:
    state = build_batch_initial_state(
        note_count=3,
        groups=(FieldGroup("Basic", ("Audio", "Image")),),
        config=AudioProcessingConfig(
            speed_step=2.0,
            volume_step_db=6.0,
            pause_aggressiveness="aggressive",
            pause_detection_algorithm="silero_vad",
            denoise_algorithm="dpdfnet",
            dpdfnet_attn_limit_db=18.0,
            output_format="flac",
            size_reduction_mode="gentle",
            size_reduction_bitrate_kbps=96,
            size_reduction_sample_rate_hz=44100,
            size_reduction_channels=2,
        ),
    )

    assert state["note_count"] == 3
    assert state["field_groups"] == [{"notetype_name": "Basic", "fields": ["Audio", "Image"]}]
    assert state["defaults"] == {
        "speed_step": 2.0,
        "volume_step_db": 6.0,
        "pause_aggressiveness": "aggressive",
        "pause_detection_algorithm": "silero_vad",
        "pause_silencedetect_threshold_db": -45.0,
        "pause_silencedetect_min_silence_seconds": 0.3,
        "pause_silencedetect_min_speech_seconds": 0.1,
        "pause_silencedetect_preprocess_denoise": True,
        "pause_silero_threshold": 0.5,
        "pause_silero_min_silence_seconds": 0.45,
        "pause_silero_min_speech_seconds": 0.1,
        "pause_silero_preprocess_denoise": False,
        "denoise_algorithm": "dpdfnet",
        "dpdfnet_attn_limit_db": 18.0,
        "output_format": "flac",
        "size_reduction_mode": "gentle",
        "size_reduction_bitrate_kbps": 96,
        "size_reduction_sample_rate_hz": 44100,
        "size_reduction_channels": 2,
    }
    graph = next(item for item in state["operations"] if item["operation"] == OP_GRAPH)
    faster = next(item for item in state["operations"] if item["operation"] == OP_FASTER)
    pause = next(item for item in state["operations"] if item["operation"] == OP_REMOVE_PAUSES)
    denoise = next(item for item in state["operations"] if item["operation"] == OP_DENOISE)
    convert = next(item for item in state["operations"] if item["operation"] == OP_CONVERT)
    reduce_size = next(item for item in state["operations"] if item["operation"] == OP_REDUCE_SIZE)
    assert graph["requires_target_field"] is True
    assert graph["parameter_kind"] == "none"
    assert graph["parameter_name"] == "none"
    assert faster["parameter_kind"] == "speed"
    assert faster["parameter_name"] == "speed_step"
    assert pause["parameter_kind"] == "pause"
    assert pause["parameter_name"] == "pause_aggressiveness"
    assert denoise["parameter_kind"] == "denoise"
    assert denoise["parameter_name"] == "denoise_algorithm"
    assert convert["parameter_kind"] == "format"
    assert convert["parameter_name"] == "target_format"
    assert reduce_size["parameter_kind"] == "size_reduction"
    assert reduce_size["parameter_name"] == "size_reduction_mode"
    assert state["locale"] == "en"
    assert state["direction"] == "ltr"
    assert "batch.start" in state["messages"]


def test_build_batch_initial_state_includes_processing_presets_when_configured() -> None:
    presets = presets_from_raw(
        [
            {
                "id": "clean_graph",
                "name": "Clean + graph",
                "steps": [
                    {
                        "id": "denoise",
                        "operation": "denoise",
                        "parameters": {"denoise_algorithm": "standard"},
                    }
                ],
                "graph": {
                    "enabled": True,
                    "parameters": {
                        "graph_voice_range": "general",
                        "graph_recording_condition": "auto",
                        "graph_smoothness": "very_smooth",
                        "graph_connect_short_dropouts_ms": 240,
                        "graph_voice_lock": "balanced",
                    },
                },
            }
        ]
    )

    state = build_batch_initial_state(
        note_count=1,
        groups=(FieldGroup("Basic", ("Audio", "Graph")),),
        config=AudioProcessingConfig(),
        processing_presets=presets,
    )

    preset_operation = next(item for item in state["operations"] if item["operation"] == OP_PRESET)
    assert preset_operation["parameter_kind"] == "preset"
    assert preset_operation["parameter_name"] == "preset_id"
    assert state["processing_presets"] == [
        {
            "id": "clean_graph",
            "name": "Clean + graph",
            "has_transforms": True,
            "graph_enabled": True,
        }
    ]


def test_request_from_batch_start_payload_builds_batch_run_request() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "faster",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {"speed_step": 2},
        }
    )

    assert request.operation == "faster"
    assert request.source_field == "Audio"
    assert request.target_field is None
    assert request.parameters.speed_step == 2


def test_request_from_batch_start_payload_builds_denoise_parameters() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "denoise",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {
                "denoise_algorithm": "dpdfnet",
                "dpdfnet_attn_limit_db": 18.0,
            },
        }
    )

    assert request.operation == "denoise"
    assert request.parameters.denoise_algorithm == "dpdfnet"
    assert request.parameters.dpdfnet_attn_limit_db == 18.0


def test_request_from_batch_start_payload_builds_pause_parameters() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "remove_pauses",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {
                "pause_aggressiveness": "gentle",
                "pause_detection_algorithm": "silero_vad",
                "pause_threshold": 0.55,
                "pause_min_silence_seconds": 0.7,
                "pause_min_speech_seconds": 0.12,
                "pause_preprocess_denoise": False,
            },
        }
    )

    assert request.operation == "remove_pauses"
    assert request.parameters.pause_aggressiveness == "gentle"
    assert request.parameters.pause_detection_algorithm == "silero_vad"
    assert request.parameters.pause_threshold == 0.55
    assert request.parameters.pause_min_silence_seconds == 0.7
    assert request.parameters.pause_min_speech_seconds == 0.12
    assert request.parameters.pause_preprocess_denoise is False


def test_request_from_batch_start_payload_builds_convert_parameters() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "convert",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {"target_format": "flac"},
        }
    )

    assert request.operation == "convert"
    assert request.parameters.target_format == "flac"

def test_request_from_batch_start_payload_resolves_processing_preset() -> None:
    presets = presets_from_raw(
        [
            {
                "id": "graph_only",
                "name": "Graph only",
                "steps": [],
                "graph": {
                    "enabled": True,
                    "parameters": {
                        "graph_voice_range": "general",
                        "graph_recording_condition": "auto",
                        "graph_smoothness": "very_smooth",
                        "graph_connect_short_dropouts_ms": 240,
                        "graph_voice_lock": "balanced",
                    },
                },
            }
        ]
    )

    request = request_from_batch_start_payload(
        {
            "operation": "preset",
            "source_field": "Audio",
            "target_field": None,
            "preset_id": "graph_only",
            "audio_target_field": None,
            "graph_target_field": "Graph",
            "parameters": {},
        },
        processing_presets=presets,
    )

    assert request.operation == OP_PRESET
    assert request.preset_id == "graph_only"
    assert request.preset is presets[0]
    assert request.graph_target_field == "Graph"


def test_request_from_batch_start_payload_rejects_missing_preset_audio_target() -> None:
    presets = presets_from_raw(
        [
            {
                "id": "clean",
                "name": "Clean",
                "steps": [
                    {
                        "id": "denoise",
                        "operation": "denoise",
                        "parameters": {"denoise_algorithm": "standard"},
                    }
                ],
                "graph": {
                    "enabled": False,
                    "parameters": {
                        "graph_voice_range": "general",
                        "graph_recording_condition": "auto",
                        "graph_smoothness": "very_smooth",
                        "graph_connect_short_dropouts_ms": 240,
                        "graph_voice_lock": "balanced",
                    },
                },
            }
        ]
    )

    try:
        request_from_batch_start_payload(
            {
                "operation": "preset",
                "source_field": "Audio",
                "target_field": None,
                "preset_id": "clean",
                "audio_target_field": None,
                "graph_target_field": None,
                "parameters": {},
            },
            processing_presets=presets,
        )
    except ValueError as exc:
        assert str(exc) == "Choose an audio target field before starting."
    else:
        raise AssertionError("expected missing preset audio target to fail")


def test_request_from_batch_start_payload_builds_size_reduction_parameters() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "reduce_size",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {
                "size_reduction_mode": "aggressive",
                "size_reduction_bitrate_kbps": 32,
                "size_reduction_sample_rate_hz": 16000,
                "size_reduction_channels": 1,
            },
        }
    )

    assert request.operation == "reduce_size"
    assert request.parameters.size_reduction_mode == "aggressive"
    assert request.parameters.size_reduction_bitrate_kbps == 32
    assert request.parameters.size_reduction_sample_rate_hz == 16000
    assert request.parameters.size_reduction_channels == 1


def test_request_from_batch_start_payload_rejects_missing_graph_target() -> None:
    try:
        request_from_batch_start_payload(
            {
                "operation": "graph",
                "source_field": "Audio",
                "target_field": None,
                "parameters": {},
            }
        )
    except ValueError as exc:
        assert str(exc) == "Choose a target field before starting."
    else:
        raise AssertionError("expected missing graph target to fail")


def test_progress_and_finish_payloads_match_frontend_contract() -> None:
    progress = batch_progress_payload(
        processed=1,
        total=3,
        current_audio="clip.mp3",
        failures=0,
        message="Processed 1/3 notes. Current audio: clip.mp3. Failures: 0.",
    )
    report = BatchRunReport(total=3, processed=2, written=1, skipped=1, failures=0, messages={})
    finish = batch_finish_payload(report)

    assert progress == {
        "processed": 1,
        "total": 3,
        "current_audio": "clip.mp3",
        "failures": 0,
        "message": "Processed 1/3 notes. Current audio: clip.mp3. Failures: 0.",
    }
    assert finish == {
        "processed": 2,
        "total": 3,
        "written": 1,
        "skipped": 1,
        "failures": 0,
        "canceled": False,
        "summary": report.summary,
    }
    assert batch_error_payload(
        "Choose a source field.",
        recoverable=True,
        user_error={
            "code": "AQE-BATCH-001",
            "message": "Choose a source field.",
        },
    ) == {
        "message": "Choose a source field.",
        "recoverable": True,
        "user_error": {
            "code": "AQE-BATCH-001",
            "message": "Choose a source field.",
        },
    }


def test_invalid_start_message_has_batch_error_code() -> None:
    payload = batch_error_payload(
        "Batch operation failed: Invalid batch request",
        user_error=coded_error(AQE_BATCH_INVALID_REQUEST, "Batch operation failed: Invalid batch request"),
    )

    assert payload["user_error"]["code"] == "AQE-BATCH-001"
