from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_processing import render_and_replace_async
from anki_audio_quick_editor.editor_region_delete import delete_selection_async
from anki_audio_quick_editor.editor_runtime import SESSIONS as _SESSIONS
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    RegionDeleteRequest,
    reset_for_note_load,
)
from anki_audio_quick_editor.editor_special_transforms import (
    run_special_audio_transform_async,
)
from tests.race_test_helpers import (
    BackgroundThread,
    BarrierCall,
    editor_with_media,
    join_background_threads,
    main_immediately,
    reset_background_threads,
)


@pytest.fixture(autouse=True)
def clear_sessions() -> None:
    _SESSIONS.clear()
    reset_background_threads()
    yield
    join_background_threads()
    _SESSIONS.clear()


def _standard_deps(tmp_path: Path, barrier: BarrierCall) -> SimpleNamespace:
    media_dir = tmp_path / "media"
    temp_dir = tmp_path / "tmp"
    media_dir.mkdir()
    temp_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

    def render_audio(
        source_path: Path,
        _state: AudioEditState,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        **_kwargs: object,
    ) -> None:
        barrier.block_until_released(source_path, output_path)
        shutil.copyfile(source_path, output_path)

    deps = SimpleNamespace()
    deps.sessions = _SESSIONS
    deps.threading = SimpleNamespace(Thread=BackgroundThread)
    deps.main = main_immediately
    deps.render_audio = render_audio
    deps.make_output_filename = lambda name: f"{Path(name).stem}__aqe_race.mp3"
    deps.temp_final_path = lambda desired_name: temp_dir / desired_name
    deps.write_generated_media = lambda editor, desired_name, output_path: editor.mw.col.media.write_data(
        desired_name,
        output_path.read_bytes(),
    )
    deps.replace_current_field_after_render = MagicMock()
    deps.render_failed = MagicMock()
    deps.stop_session_playback = MagicMock()
    deps.set_busy = MagicMock()
    deps.eval_playback_state = MagicMock()
    deps.format_ffmpeg_command = lambda command: " ".join(command)
    deps.artifact_root = lambda _editor: None
    return deps


def _region_deps(tmp_path: Path, barrier: BarrierCall) -> SimpleNamespace:
    temp_dir = tmp_path / "region-tmp"
    temp_dir.mkdir()

    def render_region(
        source_path: Path,
        _start_ms: int,
        _end_ms: int,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        **_kwargs: object,
    ) -> SimpleNamespace:
        barrier.block_until_released(source_path, output_path)
        shutil.copyfile(source_path, output_path)
        return SimpleNamespace(duration_ms=750)

    deps = SimpleNamespace()
    deps.sessions = _SESSIONS
    deps.threading = SimpleNamespace(Thread=BackgroundThread)
    deps.main = main_immediately
    deps.render_audio_region_deleted = render_region
    deps.render_audio_region_kept = render_region
    deps.make_output_filename = lambda name: f"{Path(name).stem}__aqe_region_race.mp3"
    deps.temp_final_path = lambda desired_name: temp_dir / desired_name
    deps.replace_current_field_after_region_delete = MagicMock()
    deps.render_failed = MagicMock()
    deps.stop_session_playback = MagicMock()
    deps.set_busy_for_field = MagicMock()
    deps.eval_playback_state = MagicMock()
    deps.format_ffmpeg_command = lambda command: " ".join(command)
    return deps


def _special_deps(tmp_path: Path, session: EditorSession, source: Path) -> SimpleNamespace:
    temp_dir = tmp_path / "special-tmp"
    temp_dir.mkdir()
    deps = SimpleNamespace()
    deps.sessions = _SESSIONS
    deps.threading = SimpleNamespace(Thread=BackgroundThread)
    deps.main = main_immediately
    deps.current_media_path = lambda _editor: (session, source)
    deps.config = lambda _editor: {}
    deps.make_output_filename = lambda name, **_kwargs: f"{Path(name).stem}__aqe_special_race.mp3"
    deps.temp_final_path = lambda desired_name: temp_dir / desired_name
    deps.write_generated_media = lambda editor, desired_name, output_path: editor.mw.col.media.write_data(
        desired_name,
        output_path.read_bytes(),
    )
    deps.replace_current_field_after_noise_removal = MagicMock()
    deps.render_failed = MagicMock()
    deps.log_special_transform_failure = MagicMock()
    deps.stop_session_playback = MagicMock()
    deps.set_busy = MagicMock()
    deps.eval_status = MagicMock()
    deps.still_processing_message = "Still processing"
    deps.eval_playback_state = MagicMock()
    deps.format_ffmpeg_command = lambda command: " ".join(command)
    return deps


def test_standard_render_completion_does_not_replace_after_note_change(tmp_path: Path) -> None:
    barrier = BarrierCall()
    deps = _standard_deps(tmp_path, barrier)
    editor = editor_with_media(tmp_path / "media")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=10,
    )
    _SESSIONS[editor] = session

    render_and_replace_async(
        editor,
        session,
        tmp_path / "media" / "clip.mp3",
        AudioEditState("clip.mp3", speed=1.25),
        AudioProcessingConfig(),
        deps,
    )
    barrier.wait_started()

    reset_for_note_load(session, note_id=11)
    editor.note.fields[0] = "[sound:other.mp3]"
    barrier.allow_completion()
    join_background_threads()

    deps.replace_current_field_after_render.assert_not_called()
    assert editor.note.fields[0] == "[sound:other.mp3]", editor.note.fields
    assert not list((tmp_path / "media").glob("*__aqe_race.mp3")), sorted(
        path.name for path in (tmp_path / "media").glob("*")
    )
    assert session.processing is False


def test_standard_render_failure_does_not_reset_new_note_busy_state(tmp_path: Path) -> None:
    barrier = BarrierCall()
    deps = _standard_deps(tmp_path, barrier)
    editor = editor_with_media(tmp_path / "media")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=10,
    )
    _SESSIONS[editor] = session

    def failing_render(*args: object, **kwargs: object) -> None:
        barrier.block_until_released(args, kwargs)
        raise RuntimeError("controlled render failure")

    deps.render_audio = failing_render
    render_and_replace_async(
        editor,
        session,
        tmp_path / "media" / "clip.mp3",
        AudioEditState("clip.mp3", speed=1.25),
        AudioProcessingConfig(),
        deps,
    )
    barrier.wait_started()

    reset_for_note_load(session, note_id=12)
    barrier.allow_completion()
    join_background_threads()

    deps.render_failed.assert_not_called()
    assert session.processing is False


def test_special_transform_completion_does_not_replace_after_note_change(tmp_path: Path) -> None:
    barrier = BarrierCall()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    editor = editor_with_media(media_dir)
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=20,
    )
    _SESSIONS[editor] = session
    deps = _special_deps(tmp_path, session, source)

    def renderer(
        source_path: Path,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        **_kwargs: object,
    ) -> None:
        barrier.block_until_released(source_path, output_path)
        shutil.copyfile(source_path, output_path)

    run_special_audio_transform_async(
        editor,
        label="Denoising",
        failure_log_label="denoise failed",
        renderer=renderer,
        deps=deps,
    )
    barrier.wait_started()

    reset_for_note_load(session, note_id=21)
    editor.note.fields[0] = "[sound:other.mp3]"
    barrier.allow_completion()
    join_background_threads()

    deps.replace_current_field_after_noise_removal.assert_not_called()
    assert editor.note.fields[0] == "[sound:other.mp3]", editor.note.fields
    assert not list(media_dir.glob("*__aqe_special_race.mp3")), sorted(path.name for path in media_dir.glob("*"))
    assert session.processing is False


def test_region_delete_completion_does_not_replace_after_field_change(tmp_path: Path) -> None:
    barrier = BarrierCall()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    editor = editor_with_media(media_dir, "[sound:clip.mp3]")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=20,
    )
    _SESSIONS[editor] = session
    deps = _region_deps(tmp_path, barrier)
    request = RegionDeleteRequest(
        field_index=0,
        source_filename="clip.mp3",
        selection_start_ms=100,
        selection_end_ms=250,
        cursor_ms=100,
        duration_ms=1000,
        trigger="button",
        playback_active=False,
    )

    delete_selection_async(
        editor,
        session,
        source,
        request,
        AudioProcessingConfig(),
        deps,
    )
    barrier.wait_started()

    session.field_index = 1
    editor.note.fields.append("[sound:other.mp3]")
    barrier.allow_completion()
    join_background_threads()

    deps.replace_current_field_after_region_delete.assert_not_called()
    assert editor.note.fields == ["[sound:clip.mp3]", "[sound:other.mp3]"], editor.note.fields
    assert not list(media_dir.glob("*__aqe_*.mp3")), sorted(path.name for path in media_dir.glob("*"))
    assert session.processing is False
