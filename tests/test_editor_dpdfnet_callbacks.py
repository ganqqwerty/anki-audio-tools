"""Editor DPDFNet callback tests."""

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
from anki_audio_quick_editor.errors import AudioProcessingError, MissingDpdfnetError
from anki_audio_quick_editor.support import (
    SUPPORT_REPORT_HINT,
    clear_latest_denoise_support_incident,
    latest_denoise_support_incident,
)


class ImmediateThread:
    def __init__(self, target, daemon=True):
        self._target = target

    def start(self) -> None:
        self._target()


class Editor:
    pass


def test_dpdfnet_replaces_current_media_and_resets_state(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    rendered: list[Path] = []

    def fake_render_dpdfnet_audio(source_path: Path, _config: AudioProcessingConfig, output_path: Path, **_kwargs) -> None:
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
        "anki_audio_quick_editor.editor_dependencies.render_dpdfnet_audio",
        fake_render_dpdfnet_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:dpdfnet")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [source]
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)


def test_dpdfnet_cancels_graph_analysis_busy_state_before_render(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")

    def fake_render_dpdfnet_audio(_source_path: Path, _config: AudioProcessingConfig, output_path: Path, **_kwargs) -> None:
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
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        analysis_busy=True,
        analysis_busy_fields={0},
        analysis_generation=7,
        analysis_generations_by_field={0: 7},
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_dpdfnet_audio",
        fake_render_dpdfnet_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:dpdfnet")

    session = _SESSIONS[editor]
    assert session.analysis_busy is False
    assert session.analysis_busy_fields == set()
    assert session.analysis_generations_by_field == {}
    assert session.analysis_generation == 8
    assert any("window.__aqeSetBusy" in call.args[0] and "(0, false" in call.args[0] for call in editor.web.eval.call_args_list)
    assert editor.note.fields[0] != "[sound:clip.mp3]"


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            MissingDpdfnetError("DPDFNet requires the bundled dpdfnet executable."),
            "DPDFNet requires the bundled dpdfnet executable",
        ),
        (
            PermissionError(13, "Permission denied", "/bin/dpdfnet"),
            "Permission denied",
        ),
        (
            AudioProcessingError("bad model"),
            "bad model",
        ),
    ],
)
def test_dpdfnet_failure_logs_renders_error_and_keeps_note(
    failure: Exception,
    expected_message: str,
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    clear_latest_denoise_support_incident()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

    def fake_render_dpdfnet_audio(*_args, **_kwargs) -> None:
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
        "anki_audio_quick_editor.editor_dependencies.render_dpdfnet_audio",
        fake_render_dpdfnet_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:dpdfnet")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert editor.mw.col.media.write_data.call_count == 0
    assert _SESSIONS[editor].processing is False
    assert any(
        expected_message in call.args[0] and SUPPORT_REPORT_HINT in call.args[0]
        for call in editor.web.eval.call_args_list
    )
    assert "dpdfnet denoise failed" in caplog.text
    assert expected_message in caplog.text
    incident = latest_denoise_support_incident()
    assert incident is not None
    assert incident["operation"] == "dpdfnet_denoise"
    assert incident["media_filename"] == "clip.mp3"
    assert incident["source_path"].endswith("clip.mp3")
    assert expected_message in incident["user_message"]
