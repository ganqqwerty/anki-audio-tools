"""Editor bridge processing command routing tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.contracts_generated import AutoplayKind
from anki_audio_quick_editor.editor_callbacks import handle_bridge_command
from anki_audio_quick_editor.editor_session import (
    AnalysisState,
    EditorSession,
    ProcessingState,
)
from tests.editor_bridge_command_fixtures import attach_clip_session, make_editor


def test_bridge_accepts_processing_json_payload(tmp_path: Path, monkeypatch) -> None:
    editor = make_editor()
    session, source = attach_clip_session(editor, tmp_path)
    rendered: dict[str, AudioEditState | int] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.config",
        lambda _editor: {"volume_step_db": 3},
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(
            state=updated_state,
            current_field=editor.currentField,
        ),
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:volume-up","fieldOrd":1,"overrides":{"volumeStepDb":6}}',
    )

    assert rendered["state"] == AudioEditState("clip.mp3", volume_db=6)
    assert rendered["current_field"] == 1


def test_bridge_retains_post_edit_program_for_matching_result(tmp_path: Path, monkeypatch) -> None:
    editor = make_editor()
    session, source = attach_clip_session(editor, tmp_path)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda *_args: None,
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:faster","fieldOrd":0,'
        '"postEditAutoplay":{"kind":"repeat","repeatPauseMs":750}}',
    )

    preference = session.post_edit_autoplay_by_field[0]
    assert preference.kind.value == AutoplayKind.REPEAT.value
    assert preference.repeat_pause_ms == 750


def test_bridge_passes_local_pause_aggressiveness_to_renderer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor = make_editor()
    session, source = attach_clip_session(editor, tmp_path)
    rendered: dict[str, AudioProcessingConfig] = {}
    persisted_config = {
        "pause_aggressiveness": "normal",
        "pause_detection_algorithm": "silencedetect",
        "pause_silencedetect_threshold_db": -45,
        "pause_silencedetect_min_silence_seconds": 0.30,
        "pause_silencedetect_min_speech_seconds": 0.10,
        "pause_silencedetect_preprocess_denoise": True,
    }

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.config",
        lambda _editor: persisted_config,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, _updated_state, render_config: rendered.update(
            config=render_config
        ),
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:remove-pauses","fieldOrd":0,'
        '"overrides":{"pauseAggressiveness":"aggressive"}}',
    )

    assert rendered["config"].pause_aggressiveness == "aggressive"
    assert rendered["config"].pause_silencedetect_threshold_db == -52
    assert rendered["config"].pause_silencedetect_min_silence_seconds == 0.14
    assert rendered["config"].pause_silencedetect_min_speech_seconds == 0.04
    assert persisted_config["pause_aggressiveness"] == "normal"


def test_bridge_keeps_plain_processing_commands(tmp_path: Path, monkeypatch) -> None:
    editor = make_editor()
    session, source = attach_clip_session(editor, tmp_path)
    rendered: dict[str, AudioEditState] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.config",
        lambda _editor: {"speed_step": 2},
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(
            state=updated_state
        ),
    )

    handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=2.0)


def test_bridge_routes_processing_preset_payload(monkeypatch) -> None:
    editor = make_editor()
    routed: dict[str, object] = {}
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._run_processing_preset_async",
        lambda _editor, payload: routed.update(editor=_editor, payload=payload),
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:preset","fieldOrd":2,"presetId":"clean_graph"}',
    )

    assert routed["editor"] is editor
    assert routed["payload"].command == "aqe:preset"
    assert routed["payload"].field_ord == 2
    assert routed["payload"].preset_id == "clean_graph"
    assert editor.currentField == 2


def test_busy_session_rejects_processing_command(tmp_path: Path, monkeypatch) -> None:
    editor = make_editor()
    session = EditorSession(state=AudioEditState("clip.mp3"), field_index=0, processing=ProcessingState(active=True))
    attach_clip_session(editor, tmp_path, session=session)
    render = MagicMock()
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, tmp_path / "clip.mp3"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_callbacks._render_and_replace_async", render)

    handle_bridge_command(editor, "aqe:faster")

    render.assert_not_called()
    assert any("Still processing. Please wait." in call.args[0] for call in editor.web.eval.call_args_list)


def test_processing_command_starts_without_backend_playback_state(tmp_path: Path, monkeypatch) -> None:
    editor = make_editor()
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
    )
    session, source = attach_clip_session(editor, tmp_path, session=session)
    rendered: dict[str, AudioEditState] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.config", lambda _editor: {"speed_step": 2})
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(state=updated_state),
    )

    handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=2.0)
    assert not hasattr(session, "playback")


def test_processing_command_cancels_graph_analysis_busy_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor = make_editor()
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        analysis=AnalysisState(
            busy=True,
            busy_fields={0},
            generation=4,
            generations_by_field={0: 4},
        ),
    )
    session, source = attach_clip_session(editor, tmp_path, session=session)
    rendered: dict[str, AudioEditState] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.config", lambda _editor: {"speed_step": 2})
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(state=updated_state),
    )

    handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=2.0)
    assert session.analysis.busy is False
    assert session.analysis.busy_fields == set()
    assert session.analysis.generations_by_field == {}
    assert session.analysis.generation == 5
    assert any(
        "window.__aqeSetBusy" in call.args[0] and "(0, false" in call.args[0]
        for call in editor.web.eval.call_args_list
    )
