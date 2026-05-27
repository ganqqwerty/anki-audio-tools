"""Editor bridge facade, defaults, sharing, and playback command tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from anki_audio_quick_editor import editor_callbacks, editor_frontend_callbacks
from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _handle_bridge_command,
)
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


def test_bridge_routes_share_payload_to_editor_sharing(monkeypatch) -> None:
    editor = make_editor()
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


def test_stop_playback_command_stops_session_without_clearing_status() -> None:
    editor = make_editor()
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        playback_active=True,
        playback_paused=True,
        playback_generation=4,
    )
    _SESSIONS[editor] = session

    _handle_bridge_command(editor, "aqe:stop-playback")

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

    _handle_bridge_command(editor, "aqe:stop-playback")

    stop_audio.assert_called_once_with()
    assert not any("window.__aqeSetStatus" in call.args[0] for call in editor.web.eval.call_args_list)
