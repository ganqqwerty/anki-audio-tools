"""Editor noise-reduction callback tests."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _handle_bridge_command,
)
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
    MissingDeepFilterError,
    MissingRnnoiseError,
    MissingSpleeterError,
)
from anki_audio_quick_editor.support import (
    SUPPORT_REPORT_HINT,
    clear_latest_rnnoise_support_incident,
    clear_latest_spleeter_support_incident,
    latest_rnnoise_support_incident,
    latest_spleeter_support_incident,
)


def test_standard_denoise_replaces_current_media_and_resets_state(tmp_path: Path, monkeypatch) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    rendered: list[Path] = []

    def fake_render_noise_reduced_audio(source_path: Path, _config: AudioProcessingConfig, output_path: Path, **_kwargs) -> None:
        rendered.append(source_path)
        output_path.write_bytes(b"cleaned")

    def fake_write_data(desired_name: str, data: bytes) -> str:
        saved_path = media_dir / desired_name
        saved_path.write_bytes(data)
        return desired_name

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(
                return_value={
                    "deep_filter_path": "/bin/deep-filter",
                    "deep_filter_post_filter": True,
                }
            ),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(side_effect=fake_write_data),
            )
        ),
    )
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3", volume_db=3.0),
        field_index=0,
        current_filename="clip.mp3",
    )
    _SESSIONS[editor].redo_history.push(AudioEditState("clip.mp3"), "redo.mp3")

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_noise_reduced_audio",
        fake_render_noise_reduced_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, "aqe:denoise-standard")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [source]
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.redo_history.pop() is None
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)
    assert "__aqePlayAfterEdit(0)" in editor.web.evalWithCallback.call_args.args[0]


def test_rnnoise_replaces_current_media_and_resets_state(tmp_path: Path, monkeypatch) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    rendered: list[Path] = []

    def fake_render_rnnoise_audio(source_path: Path, _config: AudioProcessingConfig, output_path: Path, **_kwargs) -> None:
        rendered.append(source_path)
        output_path.write_bytes(b"denoised")

    def fake_write_data(desired_name: str, data: bytes) -> str:
        saved_path = media_dir / desired_name
        saved_path.write_bytes(data)
        return desired_name

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(side_effect=fake_write_data),
            )
        ),
    )
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3", volume_db=3.0),
        field_index=0,
        current_filename="clip.mp3",
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_rnnoise_audio",
        fake_render_rnnoise_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:rnnoise")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [source]
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)


def test_voice_only_replaces_current_media_and_resets_state(tmp_path: Path, monkeypatch) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    rendered: list[Path] = []

    def fake_render_voice_only_audio(source_path: Path, _config: AudioProcessingConfig, output_path: Path, **_kwargs) -> None:
        rendered.append(source_path)
        output_path.write_bytes(b"voice")

    def fake_write_data(desired_name: str, data: bytes) -> str:
        saved_path = media_dir / desired_name
        saved_path.write_bytes(data)
        return desired_name

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(side_effect=fake_write_data),
            )
        ),
    )
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3", volume_db=3.0),
        field_index=0,
        current_filename="clip.mp3",
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_voice_only_audio",
        fake_render_voice_only_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:voice-only")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [source]
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            MissingDeepFilterError(
                "DeepFilterNet's deep-filter executable is required for Standard denoise and Shorten Pauses."
            ),
            "DeepFilterNet's deep-filter executable is required",
        ),
        (
            PermissionError(13, "Permission denied", "/bin/deep-filter"),
            "Permission denied",
        ),
        (
            AudioProcessingError("error: unexpected argument '--atten-lim'"),
            "unexpected argument '--atten-lim'",
        ),
    ],
)
def test_standard_denoise_failure_logs_renders_error_and_keeps_note(
    failure: Exception,
    expected_message: str,
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

    def fake_render_noise_reduced_audio(*_args, **_kwargs) -> None:
        raise failure

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(),
            )
        ),
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_noise_reduced_audio",
        fake_render_noise_reduced_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:denoise-standard")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert editor.mw.col.media.write_data.call_count == 0
    assert _SESSIONS[editor].processing is False
    assert any(expected_message in call.args[0] for call in editor.web.eval.call_args_list)
    assert "standard denoise failed" in caplog.text
    assert expected_message in caplog.text


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            MissingRnnoiseError("RNNoise requires the bundled rnnoise-cli executable."),
            "RNNoise requires the bundled rnnoise-cli executable",
        ),
        (
            PermissionError(13, "Permission denied", "/bin/rnnoise-cli"),
            "Permission denied",
        ),
        (
            AudioProcessingError("invalid raw input"),
            "invalid raw input",
        ),
    ],
)
def test_rnnoise_failure_logs_renders_error_and_keeps_note(
    failure: Exception,
    expected_message: str,
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    clear_latest_rnnoise_support_incident()

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

    def fake_render_rnnoise_audio(*_args, **_kwargs) -> None:
        raise failure

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(),
            )
        ),
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_rnnoise_audio",
        fake_render_rnnoise_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:rnnoise")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert editor.mw.col.media.write_data.call_count == 0
    assert _SESSIONS[editor].processing is False
    assert any(
        expected_message in call.args[0] and SUPPORT_REPORT_HINT in call.args[0]
        for call in editor.web.eval.call_args_list
    )
    assert "rnnoise denoise failed" in caplog.text
    assert expected_message in caplog.text
    incident = latest_rnnoise_support_incident()
    assert incident is not None
    assert incident["operation"] == "rnnoise_denoise"
    assert incident["media_filename"] == "clip.mp3"
    assert incident["source_path"].endswith("clip.mp3")
    assert expected_message in incident["user_message"]


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            MissingSpleeterError("Voice Only requires the bundled sherpa-spleeter executable."),
            "Voice Only requires the bundled sherpa-spleeter executable",
        ),
        (
            PermissionError(13, "Permission denied", "/bin/sherpa-spleeter"),
            "Permission denied",
        ),
        (
            AudioProcessingError("invalid wav"),
            "invalid wav",
        ),
    ],
)
def test_voice_only_failure_logs_renders_error_and_keeps_note(
    failure: Exception,
    expected_message: str,
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    clear_latest_spleeter_support_incident()
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")
    def fake_render_voice_only_audio(*_args, **_kwargs) -> None:
        raise failure
    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(),
            )
        ),
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_voice_only_audio",
        fake_render_voice_only_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_integration")
    _handle_bridge_command(editor, "aqe:voice-only")
    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert editor.mw.col.media.write_data.call_count == 0
    assert _SESSIONS[editor].processing is False
    assert any(
        expected_message in call.args[0] and SUPPORT_REPORT_HINT in call.args[0]
        for call in editor.web.eval.call_args_list
    )
    assert "voice only failed" in caplog.text
    assert expected_message in caplog.text
    incident = latest_spleeter_support_incident()
    assert incident is not None
    assert incident["operation"] == "voice_only"
    assert incident["media_filename"] == "clip.mp3"
    assert incident["source_path"].endswith("clip.mp3")
    assert expected_message in incident["user_message"]
