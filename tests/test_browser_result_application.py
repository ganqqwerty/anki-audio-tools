"""Tests for applying Browser batch results to Anki collection state."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.batch_operations import BatchNoteResult
from anki_audio_quick_editor.browser_batch_runner import (
    apply_result,
    publish_collection_changes,
)
from anki_audio_quick_editor.browser_report import BatchRunReport


def test_publish_collection_changes_ignores_empty_changes() -> None:
    browser = SimpleNamespace(mw=SimpleNamespace(update_undo_actions=MagicMock()))

    publish_collection_changes(browser, None)

    browser.mw.update_undo_actions.assert_not_called()
    aqt.gui_hooks.operation_did_execute.assert_not_called()


def test_apply_result_reports_conflict_when_target_field_changed() -> None:
    class Note(dict):
        id = 55

    note = Note(Front="[sound:old.mp3] user edit")
    col = SimpleNamespace(
        get_note=MagicMock(return_value=note),
        update_note=MagicMock(),
    )
    report = BatchRunReport(total=1)
    result = BatchNoteResult(
        note_id=55,
        status="written",
        message="processed",
        target_field="Front",
        target_html="[sound:new.mp3]",
        original_target_html="[sound:old.mp3]",
        audio_filename="old.mp3",
        written_filename="new.mp3",
    )

    applied = apply_result(col, report, result, fallback_field="Front")

    assert applied.status == "failed"
    assert "changed during batch processing" in applied.message
    assert note["Front"] == "[sound:old.mp3] user edit"
    col.update_note.assert_not_called()
    assert report.failures == 1
    assert report.written == 0
