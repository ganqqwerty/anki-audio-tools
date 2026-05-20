"""Tests for cross-platform Anki media path resolution."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.editor_media import (
    resolve_requested_field_media,
    sound_reference_for_field,
)
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.media_paths import (
    existing_media_file_path,
    media_filenames_match,
    resolve_media_file_path,
)


def test_media_filename_matching_is_case_insensitive_on_windows(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Windows")

    assert media_filenames_match("Clip.MP3", "clip.mp3")


def test_media_filename_matching_is_exact_elsewhere(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Darwin")

    assert not media_filenames_match("Clip.MP3", "clip.mp3")


def test_resolve_media_file_path_finds_windows_case_variant(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "Clip.MP3"
    source.write_bytes(b"audio")
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Windows")

    assert resolve_media_file_path(tmp_path, "clip.mp3") == source


def test_resolve_media_file_path_keeps_non_windows_case_exact(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "Clip.MP3"
    source.write_bytes(b"audio")
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Darwin")

    assert resolve_media_file_path(tmp_path, "clip.mp3") == tmp_path / "clip.mp3"


def test_existing_media_file_path_finds_windows_case_variant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "Clip.MP3"
    source.write_bytes(b"audio")
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Windows")

    assert existing_media_file_path(tmp_path, "clip.mp3") == source


def test_existing_media_file_path_requires_exact_non_windows_case(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "Clip.MP3").write_bytes(b"audio")
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Darwin")

    assert existing_media_file_path(tmp_path, "clip.mp3") is None


def test_sound_reference_for_field_returns_windows_case_variant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "Clip.MP3"
    source.write_bytes(b"audio")
    editor = SimpleNamespace(
        note=SimpleNamespace(fields=["[sound:clip.mp3]"]),
        mw=SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(tmp_path)))),
    )
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Windows")

    filename, media_path = sound_reference_for_field(editor, 0)

    assert filename == "clip.mp3"
    assert media_path == source


def test_sound_reference_for_field_rejects_missing_note() -> None:
    editor = SimpleNamespace(note=None)

    with pytest.raises(AudioProcessingError):
        sound_reference_for_field(editor, 0)


def test_resolve_requested_field_media_keeps_macos_case_sensitive(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "Clip.MP3").write_bytes(b"audio")
    editor = SimpleNamespace(
        note=SimpleNamespace(fields=["[sound:Clip.MP3]"]),
        mw=SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(tmp_path)))),
    )
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Darwin")

    assert resolve_requested_field_media(editor, 0, "clip.mp3") is None
