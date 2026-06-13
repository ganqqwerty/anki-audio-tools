from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_processing import _run_standard_render_worker
from anki_audio_quick_editor.editor_region_delete_worker import run_region_delete_worker
from anki_audio_quick_editor.editor_session import (
    EditorProcessingGuard,
    EditorSession,
    RegionDeleteRequest,
)
from anki_audio_quick_editor.editor_special_transform_worker import (
    run_special_transform_worker,
)


class OutputPathDeps:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.output_formats: list[object] = []
        self.render_output_names: list[str] = []
        self.finished_names: list[str] = []

    def make_output_filename(self, source_filename: str, *, output_format: object = "source") -> str:
        self.output_formats.append(output_format)
        return f"{Path(source_filename).stem}.{output_format}"

    def temp_final_path(self, filename: str) -> Path:
        output_dir = self.tmp_path / f"final_{len(self.output_formats)}"
        output_dir.mkdir()
        return output_dir / filename

    def main(self, _editor: object, callback: Any) -> None:
        callback()

    def format_ffmpeg_command(self, command: tuple[str, ...]) -> str:
        return " ".join(command)

    def render_failed(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("render should not fail")


def _current_guard() -> tuple[EditorSession, EditorProcessingGuard]:
    session = EditorSession(current_filename="clip.mp3", field_index=0, processing_generation=1)
    guard = EditorProcessingGuard(
        generation=1,
        note_id=None,
        field_index=0,
        source_filename="clip.mp3",
    )
    return session, guard


def test_standard_editor_render_filename_uses_config_output_format(tmp_path: Path) -> None:
    deps = OutputPathDeps(tmp_path)
    session, guard = _current_guard()

    def render_audio(
        _source_path: Path,
        _state: AudioEditState,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        on_command: Any,
        artifact_root: Path,
    ) -> None:
        del on_command, artifact_root
        deps.render_output_names.append(output_path.name)
        output_path.write_bytes(b"rendered")

    deps.render_audio = render_audio
    deps.artifact_root = lambda _editor: tmp_path / "artifacts"
    deps.replace_current_field_after_render = (
        lambda _editor, _state, saved_name, **_kwargs: deps.finished_names.append(saved_name)
    )

    _run_standard_render_worker(
        object(),
        session,
        tmp_path / "clip.mp3",
        AudioEditState(source_file="clip.mp3"),
        AudioProcessingConfig(output_format="wav"),
        guard,
        "render-test",
        deps,
    )

    assert deps.output_formats == ["wav"]
    assert deps.render_output_names == ["clip.wav"]
    assert deps.finished_names == ["clip.wav"]


def test_special_transform_filename_uses_config_output_format_by_default(tmp_path: Path) -> None:
    deps = OutputPathDeps(tmp_path)
    session, guard = _current_guard()

    def renderer(
        _source_path: Path,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        on_command: Any,
    ) -> None:
        del on_command
        deps.render_output_names.append(output_path.name)
        output_path.write_bytes(b"rendered")

    deps.replace_current_field_after_noise_removal = (
        lambda _editor, saved_name, **_kwargs: deps.finished_names.append(saved_name)
    )

    run_special_transform_worker(
        object(),
        session,
        tmp_path / "clip.mp3",
        AudioProcessingConfig(output_format="wav"),
        "Denoise",
        "denoise failed",
        renderer,
        None,
        "",
        "source",
        guard,
        "transform-test",
        deps,
    )

    assert deps.output_formats == ["wav"]
    assert deps.render_output_names == ["clip.wav"]
    assert deps.finished_names == ["clip.wav"]


def test_special_transform_explicit_output_format_overrides_config(tmp_path: Path) -> None:
    deps = OutputPathDeps(tmp_path)
    session, guard = _current_guard()

    def renderer(
        _source_path: Path,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        on_command: Any,
    ) -> None:
        del on_command
        deps.render_output_names.append(output_path.name)
        output_path.write_bytes(b"rendered")

    deps.replace_current_field_after_noise_removal = (
        lambda _editor, saved_name, **_kwargs: deps.finished_names.append(saved_name)
    )

    run_special_transform_worker(
        object(),
        session,
        tmp_path / "clip.mp3",
        AudioProcessingConfig(output_format="wav"),
        "Compress audio",
        "size reduction failed",
        renderer,
        None,
        "",
        "mp3",
        guard,
        "transform-test",
        deps,
    )

    assert deps.output_formats == ["mp3"]
    assert deps.render_output_names == ["clip.mp3"]
    assert deps.finished_names == ["clip.mp3"]


def test_region_render_filename_uses_config_output_format(tmp_path: Path) -> None:
    deps = OutputPathDeps(tmp_path)
    session, guard = _current_guard()
    request = RegionDeleteRequest(
        field_index=0,
        source_filename="clip.mp3",
        selection_start_ms=100,
        selection_end_ms=500,
        cursor_ms=100,
        duration_ms=1000,
        trigger="button",
        playback_active=False,
    )

    def render_audio_region_deleted(
        _source_path: Path,
        _selection_start_ms: int,
        _selection_end_ms: int,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        on_command: Any,
    ) -> SimpleNamespace:
        del on_command
        deps.render_output_names.append(output_path.name)
        output_path.write_bytes(b"rendered")
        return SimpleNamespace(duration_ms=600)

    deps.render_audio_region_deleted = render_audio_region_deleted
    deps.render_audio_region_kept = render_audio_region_deleted
    deps.replace_current_field_after_region_delete = (
        lambda _editor, _request, saved_name, *_args, **_kwargs: deps.finished_names.append(saved_name)
    )
    deps.set_busy_for_field = lambda *_args, **_kwargs: None

    run_region_delete_worker(
        object(),
        session,
        tmp_path / "clip.mp3",
        request,
        AudioProcessingConfig(output_format="flac"),
        guard,
        0.0,
        "region-test",
        deps,
    )

    assert deps.output_formats == ["flac"]
    assert deps.render_output_names == ["clip.flac"]
    assert deps.finished_names == ["clip.flac"]
