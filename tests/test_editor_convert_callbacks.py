"""Editor convert callback tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _handle_bridge_command,
)


class ImmediateThread:
    def __init__(self, target, daemon=True):
        self._target = target

    def start(self) -> None:
        self._target()


def _setup_editor(
    tmp_path: Path,
    *,
    source_filename: str = "clip.wav",
    config: dict[str, object] | None = None,
) -> tuple[object, Path]:
    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / source_filename
    source.write_bytes(b"source")

    def fake_write_data(desired_name: str, data: bytes) -> str:
        saved_path = media_dir / desired_name
        saved_path.write_bytes(data)
        return desired_name

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=[f"[sound:{source_filename}]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value=config or {}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(side_effect=fake_write_data),
            )
        ),
    )
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState(source_filename),
        field_index=0,
        current_filename=source_filename,
    )
    return editor, source


def _patch_common(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.threading.Thread",
        ImmediateThread,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)


def test_convert_replaces_current_media_using_default_output_format(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor, source = _setup_editor(tmp_path, config={"output_format": "flac"})
    rendered: list[tuple[Path, str, str]] = []

    def fake_render_converted_audio(
        source_path: Path,
        _config: AudioProcessingConfig,
        target_format: str,
        output_path: Path,
        **_kwargs,
    ) -> None:
        rendered.append((source_path, target_format, output_path.suffix))
        output_path.write_bytes(b"converted")

    _patch_common(monkeypatch)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_converted_audio",
        fake_render_converted_audio,
    )

    _handle_bridge_command(editor, "aqe:convert")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [(source, "flac", ".flac")]
    assert saved_name.endswith(".flac")
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.wav"
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)


def test_convert_uses_payload_target_format_override(tmp_path: Path, monkeypatch) -> None:
    editor, source = _setup_editor(tmp_path, config={"output_format": "mp3"})
    rendered: list[tuple[Path, str, str]] = []

    def fake_render_converted_audio(
        source_path: Path,
        _config: AudioProcessingConfig,
        target_format: str,
        output_path: Path,
        **_kwargs,
    ) -> None:
        rendered.append((source_path, target_format, output_path.suffix))
        output_path.write_bytes(b"converted")

    _patch_common(monkeypatch)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_converted_audio",
        fake_render_converted_audio,
    )

    _handle_bridge_command(
        editor,
        json.dumps(
            {
                "command": "aqe:convert",
                "fieldOrd": 0,
                "overrides": {"targetFormat": "m4a"},
            }
        ),
    )

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    assert rendered == [(source, "m4a", ".m4a")]
    assert saved_name.endswith(".m4a")


def test_convert_same_visible_extension_is_noop(tmp_path: Path, monkeypatch) -> None:
    editor, _source = _setup_editor(
        tmp_path,
        source_filename="clip.MP3",
        config={"output_format": "mp3"},
    )

    _patch_common(monkeypatch)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_converted_audio",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not render")),
    )

    _handle_bridge_command(editor, "aqe:convert")

    editor.mw.col.media.write_data.assert_not_called()
    assert editor.note.fields == ["[sound:clip.MP3]"]
    assert _SESSIONS[editor].processing is False
    assert any("Already in MP3 format." in call.args[0] for call in editor.web.eval.call_args_list)
