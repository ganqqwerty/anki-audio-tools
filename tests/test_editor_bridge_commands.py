"""Editor bridge command routing tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

from anki_audio_quick_editor import editor_callbacks, editor_frontend_callbacks
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _handle_bridge_command,
)
from anki_audio_quick_editor.editor_split_defaults import split_default_config_updates


def test_callback_wrappers_do_not_require_runtime_package_facades() -> None:
    assert not hasattr(editor_callbacks, "_facade")
    assert not hasattr(editor_frontend_callbacks, "_facade")


def test_split_default_updates_accept_and_reject_share_target() -> None:
    assert split_default_config_updates({"defaults": {"shareTarget": "catbox"}}) == {
        "share_target": "catbox"
    }
    assert split_default_config_updates({"defaults": {"shareTarget": "invalid"}}) == {}


def test_bridge_accepts_processing_json_payload(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    session = EditorSession(state=AudioEditState("clip.mp3"), field_index=0)
    _SESSIONS[editor] = session
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


def test_bridge_passes_local_pause_aggressiveness_to_renderer(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    session = EditorSession(state=AudioEditState("clip.mp3"), field_index=0)
    _SESSIONS[editor] = session
    rendered: dict[str, AudioProcessingConfig] = {}
    persisted_config = {
        "pause_aggressiveness": "normal",
        "internal_pause_silence_threshold_db": -45,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
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
    assert rendered["config"].internal_pause_silence_threshold_db == -50
    assert rendered["config"].internal_pause_threshold_ms == 180
    assert rendered["config"].internal_pause_target_gap_ms == 60
    assert persisted_config["pause_aggressiveness"] == "normal"


def test_bridge_routes_share_payload_to_editor_sharing(monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._share_current_audio_file",
        lambda _editor, payload: called.update(editor=_editor, payload=payload),
    )

    _handle_bridge_command(
        editor,
        '{"command":"aqe:share","fieldOrd":0,"shareTarget":"catbox"}',
    )

    assert called["editor"] is editor
    assert called["payload"].share_target == "catbox"


def test_bridge_keeps_plain_processing_commands(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    session = EditorSession(state=AudioEditState("clip.mp3"), field_index=0)
    _SESSIONS[editor] = session
    rendered: dict[str, AudioEditState] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.session_and_source",
        lambda _editor: (session, source),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.config",
        lambda _editor: {"speed_step": 0.1},
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(
            state=updated_state
        ),
    )

    _handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=1.1)


def test_bridge_defers_pending_payload_from_web_callback(tmp_path: Path, monkeypatch) -> None:
    class Web:
        def __init__(self) -> None:
            self.eval_calls: list[str] = []
            self.callback_expression = ""

        def eval(self, js: str) -> None:
            self.eval_calls.append(js)

        def evalWithCallback(self, expression: str, callback: Callable[[object], None]) -> None:
            self.callback_expression = expression
            callback({"command": "aqe:volume-up", "fieldOrd": 0, "overrides": {"volumeStepDb": 6}})

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = Web()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    session = EditorSession(state=AudioEditState("clip.mp3"), field_index=0)
    _SESSIONS[editor] = session
    rendered: dict[str, AudioEditState] = {}
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.session_and_source", lambda _editor: (session, source))
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.config", lambda _editor: {})
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(state=updated_state),
    )

    _handle_bridge_command(editor, "aqe:command-payload")

    assert "window.__aqePendingCommandPayload" in editor.web.callback_expression
    assert rendered["state"] == AudioEditState("clip.mp3", volume_db=6)


def test_pending_payload_missing_clears_busy_state() -> None:
    class Web:
        def __init__(self) -> None:
            self.eval_calls: list[str] = []

        def eval(self, js: str) -> None:
            self.eval_calls.append(js)

        def evalWithCallback(self, _expression: str, callback: Callable[[object], None]) -> None:
            callback(None)

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 3
    editor.web = Web()

    _handle_bridge_command(editor, "aqe:command-payload")

    assert any("window.__aqeSetBusy" in call and "(3, false" in call for call in editor.web.eval_calls)


def test_bridge_saves_split_button_defaults_from_pending_payload() -> None:
    class Web:
        def __init__(self) -> None:
            self.callback_expression = ""
            self.eval_calls: list[str] = []

        def eval(self, js: str) -> None:
            self.eval_calls.append(js)

        def evalWithCallback(self, expression: str, callback: Callable[[object], None]) -> None:
            self.callback_expression = expression
            callback(
                {
                    "defaults": {
                        "denoiseAlgorithm": "dpdfnet",
                        "dpdfnetAttnLimitDb": 17.4,
                        "graphConnectShortDropoutsMs": 999,
                        "graphRecordingCondition": "studio",
                        "graphSmoothness": "smooth",
                        "graphVoiceLock": "stable",
                        "graphVoiceRange": "child",
                        "pauseAggressiveness": "aggressive",
                        "pitchHumMode": "pitch_tier",
                        "repeatPauseSeconds": 20,
                        "repeatPlaybackByDefault": True,
                        "shareTarget": "catbox",
                        "speedStep": 0.5,
                        "volumeStepDb": 20,
                    },
                    "fieldOrd": 0,
                }
            )

    class Editor:
        pass

    addon_manager = MagicMock()
    addon_manager.addonFromModule.return_value = "anki_audio_quick_editor"
    addon_manager.getConfig.return_value = {
        "denoise_algorithm": "standard",
        "graph_voice_range": "general",
        "speed_step": 0.05,
    }
    editor = Editor()
    editor.currentField = 0
    editor.mw = MagicMock(addonManager=addon_manager)
    editor.web = Web()

    _handle_bridge_command(editor, "aqe:save-split-defaults")

    assert "__aqePopPendingSplitDefaultSaveRequest" in editor.web.callback_expression
    addon_manager.writeConfig.assert_called_once()
    addon_id, saved_config = addon_manager.writeConfig.call_args.args
    assert addon_id == "anki_audio_quick_editor"
    assert saved_config == {
        "denoise_algorithm": "dpdfnet",
        "dpdfnet_attn_limit_db": 18.0,
        "graph_connect_short_dropouts_ms": 500,
        "graph_recording_condition": "studio",
        "graph_smoothness": "smooth",
        "graph_voice_lock": "stable",
        "graph_voice_range": "child",
        "pause_aggressiveness": "aggressive",
        "pitch_hum_mode": "pitch_tier",
        "repeat_pause_seconds": 10.0,
        "repeat_playback_by_default": True,
        "share_target": "catbox",
        "speed_step": 0.25,
        "volume_step_db": 12.0,
    }
    assert any("Saved quick settings as defaults." in call for call in editor.web.eval_calls)


def test_busy_session_rejects_processing_command(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    session = EditorSession(state=AudioEditState("clip.mp3"), field_index=0, processing=True)
    _SESSIONS[editor] = session
    render = MagicMock()
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.session_and_source", lambda _editor: (session, source))
    monkeypatch.setattr("anki_audio_quick_editor.editor_callbacks._render_and_replace_async", render)

    _handle_bridge_command(editor, "aqe:faster")

    render.assert_not_called()
    assert any("Still processing. Please wait." in call.args[0] for call in editor.web.eval.call_args_list)


def test_processing_command_cancels_playback_preparation(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        playback_active=True,
        playback_preparing=True,
        playback_generation=7,
    )
    _SESSIONS[editor] = session
    rendered: dict[str, AudioEditState] = {}

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.session_and_source", lambda _editor: (session, source))
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.config", lambda _editor: {"speed_step": 0.1})
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(state=updated_state),
    )

    _handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=1.1)
    assert session.playback_preparing is False
    assert session.playback_active is False
    assert session.playback_generation == 8


def test_processing_command_cancels_graph_analysis_busy_state(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        analysis_busy=True,
        analysis_busy_fields={0},
        analysis_generation=4,
        analysis_generations_by_field={0: 4},
    )
    _SESSIONS[editor] = session
    rendered: dict[str, AudioEditState] = {}

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.session_and_source", lambda _editor: (session, source))
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.config", lambda _editor: {"speed_step": 0.1})
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(state=updated_state),
    )

    _handle_bridge_command(editor, "aqe:faster")

    assert rendered["state"] == AudioEditState("clip.mp3", speed=1.1)
    assert session.analysis_busy is False
    assert session.analysis_busy_fields == set()
    assert session.analysis_generations_by_field == {}
    assert session.analysis_generation == 5
    assert any("window.__aqeSetBusy" in call.args[0] and "(0, false" in call.args[0] for call in editor.web.eval.call_args_list)
