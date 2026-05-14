"""Tests for Anki sound reference parsing and replacement."""

from __future__ import annotations

import pytest

from anki_audio_quick_editor.errors import UnsupportedAudioError
from anki_audio_quick_editor.sound_refs import (
    find_sound_references,
    replace_sound_reference,
    safe_media_basename,
    select_first_sound_reference,
)


def test_detects_sound_reference_inside_html() -> None:
    selection = select_first_sound_reference("<div>before [sound:sentence.mp3] after</div>")

    assert selection.selected is not None
    assert selection.selected.filename == "sentence.mp3"
    assert selection.has_multiple is False


def test_ignores_fields_without_audio() -> None:
    selection = select_first_sound_reference("<b>No audio here</b>")

    assert selection.selected is None
    assert selection.references == ()


def test_rejects_unsupported_audio_extension() -> None:
    with pytest.raises(UnsupportedAudioError):
        select_first_sound_reference("[sound:movie.mp4]")


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
