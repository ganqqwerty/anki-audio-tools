"""Editor bridge processing command routing tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    EditorSession,
    _handle_bridge_command,
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

    _handle_bridge_command(
        editor,
        '{"command":"aqe:volume-up","fieldOrd":1,"overrides":{"volumeStepDb":6}}',
    )

    assert rendered["state"] == AudioEditState("clip.mp3", volume_db=6)
    assert rendered["current_field"] == 1


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

    _handle_bridge_command(
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

    _handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=2.0)


def test_busy_session_rejects_processing_command(tmp_path: Path, monkeypatch) -> None:
    editor = make_editor()
    session = EditorSession(state=AudioEditState("clip.mp3"), field_index=0, processing=True)
    attach_clip_session(editor, tmp_path, session=session)
    render = MagicMock()
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, tmp_path / "clip.mp3"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_callbacks._render_and_replace_async", render)

    _handle_bridge_command(editor, "aqe:faster")

    render.assert_not_called()
    assert any("Still processing. Please wait." in call.args[0] for call in editor.web.eval.call_args_list)


def test_processing_command_cancels_playback_preparation(tmp_path: Path, monkeypatch) -> None:
    editor = make_editor()
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        playback_active=True,
        playback_preparing=True,
        playback_generation=7,
    )
    session, source = attach_clip_session(editor, tmp_path, session=session)
    rendered: dict[str, AudioEditState] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.config", lambda _editor: {"speed_step": 2})
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(state=updated_state),
    )

    _handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=2.0)
    assert session.playback_preparing is False
    assert session.playback_active is False
    assert session.playback_generation == 8


def test_processing_command_cancels_graph_analysis_busy_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor = make_editor()
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        analysis_busy=True,
        analysis_busy_fields={0},
        analysis_generation=4,
        analysis_generations_by_field={0: 4},
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

    _handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=2.0)
    assert session.analysis_busy is False
    assert session.analysis_busy_fields == set()
    assert session.analysis_generations_by_field == {}
    assert session.analysis_generation == 5
    assert any(
        "window.__aqeSetBusy" in call.args[0] and "(0, false" in call.args[0]
        for call in editor.web.eval.call_args_list
    )
