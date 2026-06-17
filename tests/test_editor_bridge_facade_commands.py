"""Editor bridge facade, defaults, sharing, and playback command tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from anki_audio_quick_editor import editor_callbacks, editor_frontend_callbacks
from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_callbacks import handle_bridge_command
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import EditorSession
from anki_audio_quick_editor.editor_split_defaults import split_default_config_updates
from tests.editor_bridge_command_fixtures import make_editor


def test_callback_wrappers_do_not_require_runtime_package_facades() -> None:
    assert not hasattr(editor_callbacks, "_facade")
    assert not hasattr(editor_frontend_callbacks, "_facade")


def test_split_default_updates_accept_and_reject_share_target() -> None:
    assert split_default_config_updates({"defaults": {"shareTarget": "catbox"}}) == {
        "share_target": "catbox"
    }
    assert split_default_config_updates({"defaults": {"shareTarget": "invalid"}}) == {}


def test_split_default_updates_accept_and_reject_size_reduction_mode() -> None:
    assert split_default_config_updates(
        {
            "defaults": {
                "sizeReductionMode": "aggressive",
                "sizeReductionBitrateKbps": 32,
                "sizeReductionSampleRateHz": 16000,
                "sizeReductionChannels": 1,
            }
        }
    ) == {
        "size_reduction_mode": "aggressive",
        "size_reduction_bitrate_kbps": 32,
        "size_reduction_sample_rate_hz": 16000,
        "size_reduction_channels": 1,
    }
    assert split_default_config_updates({"defaults": {"sizeReductionMode": "tiny"}}) == {}


def test_split_default_updates_accept_chorusing_defaults() -> None:
    updates = split_default_config_updates(
        {
            "defaults": {
                "chorusingPauseSeconds": 2.6,
                "chorusingAutoAdvanceByDefault": True,
                "chorusingAutoAdvanceRepeats": 5,
            }
        }
    )

    assert updates == {
        "chorusing_pause_seconds": 2.6,
        "chorusing_auto_advance_by_default": True,
        "chorusing_auto_advance_repeats": 5,
    }


def test_split_default_updates_clamp_invalid_chorusing_defaults() -> None:
    updates = split_default_config_updates(
        {
            "defaults": {
                "chorusingPauseSeconds": -4,
                "chorusingAutoAdvanceByDefault": "yes",
                "chorusingAutoAdvanceRepeats": 200,
            }
        }
    )

    assert updates == {
        "chorusing_pause_seconds": 0.0,
        "chorusing_auto_advance_repeats": 20,
    }


def test_bridge_routes_share_payload_to_editor_sharing(monkeypatch) -> None:
    editor = make_editor()
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._share_current_audio_file",
        lambda _editor, payload: called.update(editor=_editor, payload=payload),
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:share","fieldOrd":0,"shareTarget":"catbox"}',
    )

    assert called["editor"] is editor
    assert called["payload"].share_target == "catbox"


def test_bridge_routes_learner_share_payload_to_editor_sharing(monkeypatch) -> None:
    editor = make_editor()
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._share_learner_recording_file",
        lambda _editor, payload: called.update(editor=_editor, payload=payload),
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:share-recording","fieldOrd":0,"shareTarget":"litterbox"}',
    )

    assert called["editor"] is editor
    assert called["payload"].share_target == "litterbox"


def test_bridge_routes_show_learner_recording_file(monkeypatch) -> None:
    editor = make_editor()
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._show_learner_recording_file",
        lambda _editor: called.update(editor=_editor),
    )

    handle_bridge_command(editor, "aqe:show-recording-file")

    assert called["editor"] is editor


def test_bridge_passes_start_cursor_to_learner_recording(monkeypatch) -> None:
    editor = make_editor()
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._record_learner_voice",
        lambda _editor, **kwargs: called.update(editor=_editor, kwargs=kwargs),
    )

    handle_bridge_command(
        editor,
        '{"command":"aqe:record-voice","fieldOrd":0,"startCursorMs":450}',
    )

    assert called["editor"] is editor
    assert called["kwargs"]["start_cursor_ms"] == 450


def test_stop_playback_command_stops_session_without_clearing_status() -> None:
    editor = make_editor()
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        playback_active=True,
        playback_paused=True,
        playback_generation=4,
    )
    SESSIONS[editor] = session

    handle_bridge_command(editor, "aqe:stop-playback")

    assert session.playback_active is False
    assert session.playback_paused is False
    assert session.playback_generation == 5
    assert any(
        "window.__aqeSetPlaybackState" in call.args[0] and '(0, "stopped"' in call.args[0]
        for call in editor.web.eval.call_args_list
    )
    assert not any("window.__aqeSetStatus" in call.args[0] for call in editor.web.eval.call_args_list)


def test_stop_playback_command_without_session_stops_audio(monkeypatch) -> None:
    editor = make_editor()
    stop_audio = MagicMock()
    monkeypatch.setattr("anki_audio_quick_editor.editor_callbacks._stop_audio_playback", stop_audio)

    handle_bridge_command(editor, "aqe:stop-playback")

    stop_audio.assert_called_once_with()
    assert not any("window.__aqeSetStatus" in call.args[0] for call in editor.web.eval.call_args_list)
