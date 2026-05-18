"""Tests for Anki sound reference parsing and replacement."""

from __future__ import annotations

import pytest

from anki_audio_quick_editor.errors import UnsupportedAudioError
from anki_audio_quick_editor.sound_refs import (
    SUPPORTED_AUDIO_EXTENSIONS,
    find_sound_references,
    is_supported_audio_filename,
    replace_sound_reference,
    safe_media_basename,
    select_first_sound_reference,
)

COMMON_AUDIO_EXTENSIONS = (".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav", ".webm")


def test_detects_sound_reference_inside_html() -> None:
    selection = select_first_sound_reference("<div>before [sound:sentence.mp3] after</div>")

    assert selection.selected is not None
    assert selection.selected.tag == "[sound:sentence.mp3]"
    assert selection.selected.filename == "sentence.mp3"
    assert selection.has_multiple is False


def test_detects_sound_reference_trims_inner_whitespace() -> None:
    selection = select_first_sound_reference("[sound:  sentence.MP3  ]")

    assert selection.selected is not None
    assert selection.selected.filename == "sentence.MP3"


def test_supported_audio_extensions_match_common_input_formats() -> None:
    assert SUPPORTED_AUDIO_EXTENSIONS == frozenset(COMMON_AUDIO_EXTENSIONS)


@pytest.mark.parametrize("extension", COMMON_AUDIO_EXTENSIONS)
def test_accepts_common_supported_audio_extensions_case_insensitively(extension: str) -> None:
    for filename in (f"clip{extension}", f"clip{extension.upper()}"):
        selection = select_first_sound_reference(f"[sound:{filename}]")

        assert selection.selected is not None
        assert selection.selected.filename == filename
        assert is_supported_audio_filename(filename)


def test_ignores_fields_without_audio() -> None:
    selection = select_first_sound_reference("<b>No audio here</b>")

    assert selection.selected is None
    assert selection.references == ()


def test_rejects_unsupported_audio_extension() -> None:
    with pytest.raises(UnsupportedAudioError) as exc_info:
        select_first_sound_reference("[sound:movie.mp4]")

    assert str(exc_info.value) == "The first audio reference uses an unsupported format."


def test_multiple_sound_references_selects_first_supported_reference() -> None:
    selection = select_first_sound_reference("[sound:first.mp3] and [sound:second.ogg]")

    assert selection.selected is not None
    assert selection.selected.filename == "first.mp3"
    assert selection.has_multiple is True


def test_replace_preserves_surrounding_html() -> None:
    html = "<p>Hello [sound:old.wav] world</p>"
    reference = find_sound_references(html)[0]

    assert replace_sound_reference(html, reference, "new.mp3") == "<p>Hello [sound:new.mp3] world</p>"


def test_safe_media_basename_strips_path_components() -> None:
    assert safe_media_basename("../nested/audio.mp3") == "audio.mp3"
    assert safe_media_basename(r"..\nested\audio.mp3") == "audio.mp3"


def test_replace_only_updates_selected_reference_when_multiple_exist() -> None:
    html = "[sound:first.mp3] and [sound:second.ogg]"
    reference = find_sound_references(html)[1]

    assert replace_sound_reference(html, reference, "updated.wav") == "[sound:first.mp3] and [sound:updated.wav]"
