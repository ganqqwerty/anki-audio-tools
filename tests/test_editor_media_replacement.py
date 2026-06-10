from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.editor_media_replacement import (
    persist_generated_media,
    replace_first_sound_reference_in_field,
)
from anki_audio_quick_editor.errors import AudioProcessingError


def test_persist_generated_media_uses_writer_when_output_path_exists(tmp_path: Path) -> None:
    output_path = tmp_path / "rendered.mp3"
    output_path.write_bytes(b"audio")
    calls: list[tuple[str, Path]] = []

    def write_generated_media(editor, desired_name: str, path: Path) -> str:
        calls.append((desired_name, path))
        return "saved.mp3"

    deps = SimpleNamespace(write_generated_media=write_generated_media)

    saved = persist_generated_media(object(), "desired.mp3", output_path, deps)

    assert saved == "saved.mp3"
    assert calls == [("desired.mp3", output_path)]


def test_persist_generated_media_keeps_existing_name_without_output_path() -> None:
    deps = SimpleNamespace(write_generated_media=lambda *_args: "unexpected.mp3")

    assert persist_generated_media(object(), "already-saved.mp3", None, deps) == "already-saved.mp3"


def test_replace_first_sound_reference_in_field_replaces_selected_audio() -> None:
    note = SimpleNamespace(fields=["before [sound:old.mp3] after"])
    editor = SimpleNamespace(note=note)

    old_html, new_html, old_filename = replace_first_sound_reference_in_field(
        editor,
        field_index=0,
        saved_name="new.mp3",
        missing_message="missing",
    )

    assert old_html == "before [sound:old.mp3] after"
    assert new_html == "before [sound:new.mp3] after"
    assert old_filename == "old.mp3"
    assert note.fields[0] == "before [sound:new.mp3] after"


def test_replace_first_sound_reference_in_field_raises_for_missing_audio() -> None:
    editor = SimpleNamespace(note=SimpleNamespace(fields=["plain text"]))

    with pytest.raises(AudioProcessingError, match="missing"):
        replace_first_sound_reference_in_field(
            editor,
            field_index=0,
            saved_name="new.mp3",
            missing_message="missing",
        )
