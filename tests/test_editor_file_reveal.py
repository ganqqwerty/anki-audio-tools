"""Editor file reveal callback tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _reset_editor_session_for_note_load,
)
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
    MissingMediaError,
)
from anki_audio_quick_editor.file_reveal import reveal_file


def test_note_load_reset_skips_same_note_reload(monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    session = EditorSession(
        note_id=12,
        state=AudioEditState("source.mp3"),
        field_index=0,
        current_filename="source.mp3",
        analysis_generation=5,
        playback_generation=3,
    )
    _SESSIONS[editor] = session
    stop_calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.stop_audio_playback",
        lambda: stop_calls.append("stop"),
    )

    _reset_editor_session_for_note_load(editor, 12)

    assert stop_calls == []
    assert session.note_id == 12
    assert session.state == AudioEditState("source.mp3")
    assert session.current_filename == "source.mp3"
    assert session.analysis_generation == 5
    assert session.playback_generation == 3


def test_reveal_file_selects_file_on_macos(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        "anki_audio_quick_editor.file_reveal._run_detached",
        lambda command: commands.append(command),
    )

    reveal_file(source)

    assert commands == [("open", "-R", str(source.resolve()))]


def test_reveal_file_selects_file_on_windows(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Windows")
    monkeypatch.setattr(
        "anki_audio_quick_editor.file_reveal._run_detached",
        lambda command: commands.append(command),
    )

    reveal_file(source)

    assert commands == [("explorer", f"/select,{source.resolve()}")]


def test_reveal_file_opens_parent_folder_elsewhere(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    folders: list[Path] = []

    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "anki_audio_quick_editor.file_reveal._open_parent_folder",
        lambda folder: folders.append(folder),
    )

    reveal_file(source)

    assert folders == [source.resolve().parent]


def test_reveal_file_reports_missing_media(tmp_path: Path) -> None:
    with pytest.raises(MissingMediaError, match="custom missing"):
        reveal_file(tmp_path / "missing.mp3", missing_message="custom missing")


def test_reveal_file_uses_qt_fallback_when_xdg_open_is_missing(tmp_path: Path, monkeypatch) -> None:
    from aqt.qt import QDesktopServices, QUrl

    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Linux")
    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.shutil.which", lambda _name: None)
    QDesktopServices.openUrl.return_value = True

    reveal_file(source)

    QUrl.fromLocalFile.assert_called_once_with(str(source.resolve().parent))
    QDesktopServices.openUrl.assert_called_once()


def test_reveal_file_reports_failed_parent_folder_open(tmp_path: Path, monkeypatch) -> None:
    from aqt.qt import QDesktopServices

    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Linux")
    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.shutil.which", lambda _name: None)
    QDesktopServices.openUrl.return_value = False

    with pytest.raises(AudioProcessingError, match="Could not open the containing folder"):
        reveal_file(source)


def test_reveal_file_wraps_detached_launch_errors(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        "anki_audio_quick_editor.file_reveal.subprocess.Popen",
        MagicMock(side_effect=OSError("launch failed")),
    )

    with pytest.raises(AudioProcessingError, match="Could not open the containing folder"):
        reveal_file(source)
