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


def test_detects_utf_sound_reference_inside_html() -> None:
    selection = select_first_sound_reference("<div>before [sound:Даии_青山 voice.OPUS] after</div>")

    assert selection.selected is not None
    assert selection.selected.tag == "[sound:Даии_青山 voice.OPUS]"
    assert selection.selected.filename == "Даии_青山 voice.OPUS"


@pytest.mark.parametrize(
    ("field_html", "expected_filename"),
    [
        ("[sound:bracket]name.opus]", "bracket]name.opus"),
        ("[sound:amp&amp;name.opus]", "amp&name.opus"),
        ("[sound: leading-space.opus]", " leading-space.opus"),
        ("[sound:trailing-space.opus ]", "trailing-space.opus "),
        ("[sound:hash#question?percent%.opus]", "hash#question?percent%.opus"),
        ("[sound:quote'\"semi;colon.opus]", "quote'\"semi;colon.opus"),
        ("[sound:line\nbreak.opus]", "line\nbreak.opus"),
        ("[sound:trailing-newline.opus\n]", "trailing-newline.opus\n"),
        ("[sound:trailing-dot.opus.]", "trailing-dot.opus."),
    ],
)
def test_detects_problematic_os_filename_characters(
    field_html: str,
    expected_filename: str,
) -> None:
    selection = select_first_sound_reference(field_html)

    assert selection.selected is not None
    assert selection.selected.filename == expected_filename


def test_multiple_sound_references_allow_bracket_inside_filename() -> None:
    selection = select_first_sound_reference("[sound:first]one.opus] and [sound:second.ogg]")

    assert selection.selected is not None
    assert [ref.filename for ref in selection.references] == ["first]one.opus", "second.ogg"]
    assert selection.selected.filename == "first]one.opus"
    assert selection.has_multiple is True


def test_detects_sound_reference_preserves_inner_whitespace() -> None:
    selection = select_first_sound_reference("[sound:  sentence.MP3  ]")

    assert selection.selected is not None
    assert selection.selected.filename == "  sentence.MP3  "


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


def test_replace_preserves_utf_output_filename() -> None:
    html = "<p>Hello [sound:old.wav] world</p>"
    reference = find_sound_references(html)[0]

    assert (
        replace_sound_reference(html, reference, "Даии_青山 voice.ogg")
        == "<p>Hello [sound:Даии_青山 voice.ogg] world</p>"
    )


def test_safe_media_basename_strips_path_components() -> None:
    assert safe_media_basename("../nested/audio.mp3") == "audio.mp3"


def test_safe_media_basename_preserves_utf_basename() -> None:
    assert safe_media_basename("../nested/Даии_青山_voice.opus") == "Даии_青山_voice.opus"


def test_safe_media_basename_strips_windows_path_components_on_windows(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.sound_refs.platform.system", lambda: "Windows")

    assert safe_media_basename(r"..\nested\audio.mp3") == "audio.mp3"
    assert safe_media_basename(r"..\nested\訪日.yomi000A5D37_0342.ogg") == "訪日.yomi000A5D37_0342.ogg"


def test_safe_media_basename_preserves_backslash_on_non_windows(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.sound_refs.platform.system", lambda: "Darwin")

    assert safe_media_basename(r"back\slash.opus") == r"back\slash.opus"


def test_replace_only_updates_selected_reference_when_multiple_exist() -> None:
    html = "[sound:first.mp3] and [sound:second.ogg]"
    reference = find_sound_references(html)[1]

    assert replace_sound_reference(html, reference, "updated.wav") == "[sound:first.mp3] and [sound:updated.wav]"
