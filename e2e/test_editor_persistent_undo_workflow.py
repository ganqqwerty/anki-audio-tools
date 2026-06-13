"""E2E coverage for SQLite-backed editor undo availability."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    _basic_audio_note,
    _button_selector,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)


def test_persistent_undo_restores_last_edit_after_reopening_editor(
    anki_mw,
    ffmpeg_config,
) -> None:
    _reset_persistent_undo_db(anki_mw)
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_persistent_undo_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
            source.name,
        )
    finally:
        editor.set_note(None)
        parent.close()

    reopened, reopened_parent = _open_editor(anki_mw, note)
    try:
        _wait_for_history_button(reopened, "aqe:undo", disabled=False)
        click_selector(reopened.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Persistent undo did not restore the original audio reference",
        )
        assert generated != source.name
        assert (media_dir / generated).is_file()
    finally:
        reopened.set_note(None)
        reopened_parent.close()


def test_persistent_undo_is_unavailable_after_original_media_is_removed(
    anki_mw,
    ffmpeg_config,
) -> None:
    _reset_persistent_undo_db(anki_mw)
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_persistent_undo_missing_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
            source.name,
        )
    finally:
        editor.set_note(None)
        parent.close()

    source.unlink()
    reopened, reopened_parent = _open_editor(anki_mw, note)
    try:
        _wait_for_history_button(reopened, "aqe:undo", disabled=True)
        assert _sound_filename(note.fields[0]) == generated
    finally:
        reopened.set_note(None)
        reopened_parent.close()


def _wait_for_history_button(editor, command: str, *, disabled: bool) -> None:
    wait_for_js_condition(
        editor.web,
        _history_button_state_js(command),
        lambda state: state is not None and state["disabled"] is disabled,
        timeout=10.0,
    )


def _history_button_state_js(command: str) -> str:
    selector = json.dumps(_button_selector(command))
    return f"""
    (() => {{
      const button = document.querySelector({selector});
      return button ? {{ disabled: button.disabled === true }} : null;
    }})()
    """


def _reset_persistent_undo_db(anki_mw) -> None:
    db_path = _persistent_undo_db_path(anki_mw)
    for path in (
        db_path,
        db_path.with_name(f"{db_path.name}-journal"),
        db_path.with_name(f"{db_path.name}-shm"),
        db_path.with_name(f"{db_path.name}-wal"),
    ):
        path.unlink(missing_ok=True)


def _persistent_undo_db_path(anki_mw) -> Path:
    addon_dir = Path(anki_mw.addonManager.addonsFolder(ADDON_NUMERIC_ID))
    return addon_dir / "user_files" / "persistent_undo.sqlite3"
