"""E2E tests for editor audio sharing."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _three_audio_field_note,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_selector,
)
from e2e.test_editor_processing_split_buttons_workflow import _split_menu_selector


def _share_preset_selector(target: str, ord_: int = 0) -> str:
    return f'[data-testid="aqe-split-{ord_}-share-preset-{target}"]'


def test_share_button_uploads_to_litterbox_then_catbox_without_mutating_note(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    from aqt.qt import QApplication

    from anki_audio_quick_editor import file_sharing

    uploads: list[tuple[str, str]] = []

    def fake_upload(path: Path, target: str, timeout_s: float = 60.0) -> str:
        assert timeout_s == 60.0
        uploads.append((path.name, target))
        if target == "catbox":
            return "https://files.catbox.moe/share123.mp3"
        return "https://litterbox.catbox.moe/abc123/clip.mp3"

    monkeypatch.setattr(file_sharing, "upload_file", fake_upload)

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_share_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    note = _basic_audio_note(anki_mw, source.name)
    original_field = note.fields[0]
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:share"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:share"), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == "https://litterbox.catbox.moe/abc123/clip.mp3",
            timeout=5.0,
            message="Litterbox share did not copy the expected URL",
        )

        click_selector(editor.web, _split_menu_selector("aqe:share"), timeout=5.0)
        click_selector(editor.web, _share_preset_selector("catbox"), timeout=5.0)
        click_selector(editor.web, _button_selector("aqe:share"), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == "https://files.catbox.moe/share123.mp3",
            timeout=5.0,
            message="Catbox share did not copy the expected URL",
        )

        assert uploads == [
            (source.name, "litterbox"),
            (source.name, "catbox"),
        ]
        assert note.fields[0] == original_field
    finally:
        editor.set_note(None)
        parent.close()


def test_share_target_state_is_isolated_per_field(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    from aqt.qt import QApplication

    from anki_audio_quick_editor import file_sharing

    uploads: list[tuple[str, str]] = []

    def fake_upload(path: Path, target: str, timeout_s: float = 60.0) -> str:
        assert timeout_s == 60.0
        uploads.append((path.name, target))
        return f"https://example.invalid/{target}/{path.name}"

    monkeypatch.setattr(file_sharing, "upload_file", fake_upload)

    media_dir = Path(anki_mw.col.media.dir())
    one = media_dir / "editor_share_one.wav"
    two = media_dir / "editor_share_two.wav"
    three = media_dir / "editor_share_three.wav"
    generate_tone(ffmpeg_config, one, duration_s=0.5)
    generate_tone(ffmpeg_config, two, duration_s=0.5)
    generate_tone(ffmpeg_config, three, duration_s=0.5)
    note = _three_audio_field_note(anki_mw, (one.name, two.name, three.name))
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:share", 0), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:share", 0), timeout=5.0)
        click_selector(editor.web, _share_preset_selector("catbox", 0), timeout=5.0)
        click_selector(editor.web, _button_selector("aqe:share", 0), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == f"https://example.invalid/catbox/{one.name}",
            timeout=5.0,
            message="Field 0 did not retain the Catbox selection",
        )

        click_selector(editor.web, _button_selector("aqe:share", 1), timeout=5.0)
        wait_for_condition(
            lambda: QApplication.clipboard().text() == f"https://example.invalid/litterbox/{two.name}",
            timeout=5.0,
            message="Field 1 should still use the default Litterbox target",
        )

        assert uploads == [
            (one.name, "catbox"),
            (two.name, "litterbox"),
        ]
    finally:
        editor.set_note(None)
        parent.close()
