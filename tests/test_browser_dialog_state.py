from anki_audio_quick_editor.audio_operations import (
    OP_CONVERT,
    OP_DENOISE,
    OP_FASTER,
    OP_GRAPH,
    OP_REMOVE_PAUSES,
)
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


def test_build_batch_initial_state_contains_operations_fields_defaults_and_i18n() -> None:
    state = build_batch_initial_state(
        note_count=3,
        groups=(FieldGroup("Basic", ("Audio", "Image")),),
        config=AudioProcessingConfig(
            speed_step=0.1,
            volume_step_db=6.0,
            pause_aggressiveness="aggressive",
            denoise_algorithm="dpdfnet",
            dpdfnet_attn_limit_db=18.0,
            output_format="flac",
        ),
    )

    assert state["note_count"] == 3
    assert state["field_groups"] == [{"notetype_name": "Basic", "fields": ["Audio", "Image"]}]
    assert state["defaults"] == {
        "speed_step": 0.1,
        "volume_step_db": 6.0,
        "pause_aggressiveness": "aggressive",
        "denoise_algorithm": "dpdfnet",
        "dpdfnet_attn_limit_db": 18.0,
        "output_format": "flac",
    }
    graph = next(item for item in state["operations"] if item["operation"] == OP_GRAPH)
    faster = next(item for item in state["operations"] if item["operation"] == OP_FASTER)
    pause = next(item for item in state["operations"] if item["operation"] == OP_REMOVE_PAUSES)
    denoise = next(item for item in state["operations"] if item["operation"] == OP_DENOISE)
    convert = next(item for item in state["operations"] if item["operation"] == OP_CONVERT)
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
    assert state["locale"] == "en"
    assert state["direction"] == "ltr"
    assert "batch.start" in state["messages"]


def test_request_from_batch_start_payload_builds_batch_run_request() -> None:
    request = request_from_batch_start_payload(
        {
            "operation": "faster",
            "source_field": "Audio",
            "target_field": None,
            "parameters": {"speed_step": 0.2},
        }
    )

    assert request.operation == "faster"
    assert request.source_field == "Audio"
    assert request.target_field is None
    assert request.parameters.speed_step == 0.2


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
    assert batch_error_payload("Choose a source field.", recoverable=True) == {
        "message": "Choose a source field.",
        "recoverable": True,
    }
