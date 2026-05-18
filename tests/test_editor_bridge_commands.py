"""Editor bridge command routing tests."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor import editor_callbacks, editor_frontend_callbacks
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _handle_bridge_command,
)


def test_callback_wrappers_do_not_require_runtime_package_facades() -> None:
    assert not hasattr(editor_callbacks, "_facade")
    assert not hasattr(editor_frontend_callbacks, "_facade")


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
        lambda _editor: {"manual_trim_small_ms": 500},
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
        '{"command":"aqe:trim-left","fieldOrd":1,"overrides":{"trimStepMs":200}}',
    )

    assert rendered["state"] == AudioEditState("clip.mp3", left_trim_ms=200)
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
        lambda _editor: {"manual_trim_small_ms": 300},
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._render_and_replace_async",
        lambda _editor, _session, _source_path, updated_state, _config: rendered.update(
            state=updated_state
        ),
    )

    _handle_bridge_command(editor, "aqe:trim-left")

    assert rendered["state"] == AudioEditState("clip.mp3", left_trim_ms=300)


def test_bridge_defers_pending_payload_from_web_callback(tmp_path: Path, monkeypatch) -> None:
    class Web:
        def __init__(self) -> None:
            self.eval_calls: list[str] = []
            self.callback_expression = ""

        def eval(self, js: str) -> None:
            self.eval_calls.append(js)

        def evalWithCallback(self, expression: str, callback: Callable[[object], None]) -> None:
            self.callback_expression = expression
            callback({"command": "aqe:trim-left", "fieldOrd": 0, "overrides": {"trimStepMs": 150}})

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
    assert rendered["state"] == AudioEditState("clip.mp3", left_trim_ms=150)


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

    _handle_bridge_command(editor, "aqe:trim-left")

    render.assert_not_called()
    assert any("Still processing. Please wait." in call.args[0] for call in editor.web.eval.call_args_list)


def test_editor_frontend_log_callback_records_levels(caplog: pytest.LogCaptureFixture) -> None:
    class Web:
        def evalWithCallback(self, _expression: str, callback: Callable[[object], None]) -> None:
            callback({"level": "warn", "message": "drag canceled", "context": {"ord": 1}})

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = Web()
    caplog.set_level(logging.DEBUG, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:frontend-log")

    record = caplog.records[-1]
    assert record.levelno == logging.WARNING
    assert record.message == "editor frontend: drag canceled | {'ord': 1}"


def test_invalid_editor_frontend_log_payload_is_ignored(caplog: pytest.LogCaptureFixture) -> None:
    class Web:
        def evalWithCallback(self, _expression: str, callback: Callable[[object], None]) -> None:
            callback({"level": "warn", "context": {"missing": "message"}})

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = Web()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:frontend-log")

    assert "editor frontend_log: invalid payload" in caplog.text
