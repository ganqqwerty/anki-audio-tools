"""Editor noise-reduction callback tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _handle_bridge_command,
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
    assert any(
        "__aqeSetHistoryAvailability(0, true, false)" in call.args[0]
        for call in editor.web.evalWithCallback.call_args_list
    )
    assert session.pending_post_edit_playback_field_index == 0
    assert session.pending_post_edit_playback_generation == session.post_edit_playback_generation
    assert session.pending_post_edit_playback_source_filename == saved_name

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
    assert any(
        "window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(0, true, false)" in call.args[0]
        for call in editor.web.eval.call_args_list
    )


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
    assert any(
        "window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(0, true, false)" in call.args[0]
        for call in editor.web.eval.call_args_list
    )
