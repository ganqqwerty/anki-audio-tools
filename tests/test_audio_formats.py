"""Tests for shared output format helpers."""

from __future__ import annotations

import pytest

from anki_audio_quick_editor.audio_formats import (
    DEFAULT_OUTPUT_FORMAT,
    SUPPORTED_OUTPUT_FORMATS,
    format_label,
    is_same_visible_format,
    normalize_output_format,
    output_extension,
    validate_target_format,
    visible_extension,
)


def test_supported_formats_cover_main_audio_targets() -> None:
    assert SUPPORTED_OUTPUT_FORMATS == ("mp3", "m4a", "wav", "flac")
    assert DEFAULT_OUTPUT_FORMAT == "mp3"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("mp3", "mp3"),
        (" MP3 ", "mp3"),
        ("m4a", "m4a"),
        ("ogg", "mp3"),
        ("wav", "wav"),
        ("flac", "flac"),
        (None, "mp3"),
        ("aac", "mp3"),
        ("", "mp3"),
    ],
)
def test_normalize_output_format_falls_back_for_settings(raw: object, expected: str) -> None:
    assert normalize_output_format(raw) == expected


@pytest.mark.parametrize("target", ["mp3", "M4A", "wav", "flac"])
def test_validate_target_format_accepts_supported_values(target: str) -> None:
    assert validate_target_format(target) == target.strip().lower()


@pytest.mark.parametrize("target", ["aac", "mp4", "", None])
def test_validate_target_format_rejects_unknown_values(target: object) -> None:
    with pytest.raises(ValueError, match="Unsupported audio output format"):
        validate_target_format(target)


@pytest.mark.parametrize(
    ("target", "extension", "label"),
    [
        ("mp3", ".mp3", "MP3"),
        ("m4a", ".m4a", "M4A"),
        ("wav", ".wav", "WAV"),
        ("flac", ".flac", "FLAC"),
    ],
)
def test_format_extension_and_label(target: str, extension: str, label: str) -> None:
    assert output_extension(target) == extension
    assert format_label(target) == label


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("clip.mp3", "mp3"),
        ("clip.M4A", "m4a"),
        ("clip", None),
        (".hidden", None),
    ],
)
def test_visible_extension(filename: str, expected: str | None) -> None:
    assert visible_extension(filename) == expected


@pytest.mark.parametrize(
    ("filename", "target", "expected"),
    [
        ("clip.mp3", "mp3", True),
        ("clip.MP3", "mp3", True),
        ("clip.m4a", "m4a", True),
        ("clip.aac", "m4a", False),
        ("clip.wav", "flac", False),
        ("clip", "mp3", False),
    ],
)
def test_same_visible_format_compares_user_visible_extension(
    filename: str,
    target: str,
    expected: bool,
) -> None:
    assert is_same_visible_format(filename, target) is expected
