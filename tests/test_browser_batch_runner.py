"""Tests for Browser batch runner behavior."""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_operations import OP_FASTER, OP_GRAPH
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import BatchNoteResult, BatchRunRequest
from anki_audio_quick_editor.browser_batch_runner import (
    run_batch,
    run_batch_in_background,
)
from anki_audio_quick_editor.browser_report import BatchRunReport
from tests.browser_batch_fixtures import FakeCol, FakeNote


def test_run_batch_reports_note_load_and_update_failures(monkeypatch, tmp_path: Path) -> None:
    class FailingCol(FakeCol):
        def get_note(self, note_id: int) -> FakeNote:
            if note_id == 1:
                raise RuntimeError("note disappeared")
            return super().get_note(note_id)

        def update_note(self, note: FakeNote) -> object:
            del note
            raise RuntimeError("database locked")

    def fake_process_note_batch_operation(*_args, **_kwargs) -> BatchNoteResult:
        return BatchNoteResult(
            note_id=2,
            status="written",
            message="appended viz.svg",
            target_field="Image",
            target_html='<img src="viz.svg">',
            audio_filename="clip.mp3",
            image_filename="viz.svg",
        )

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_batch_runner.process_note_batch_operation",
        fake_process_note_batch_operation,
    )
    logs: list[str] = []
    progress: list[tuple[int, int, str, int]] = []

    report = run_batch(
        FailingCol(),
        [1, 2],
        BatchRunRequest(operation=OP_GRAPH, source_field="Audio", target_field="Image"),
        tmp_path,
        AudioProcessingConfig(),
        threading.Event(),
        logs.append,
        lambda *args: progress.append(args),  # type: ignore[arg-type]
    )

    assert report.processed == 2
    assert report.written == 0
    assert report.skipped == 0
    assert report.failures == 2
    assert "FAIL note 1: note disappeared" in logs
    assert "FAIL note 2 (clip.mp3): database locked" in logs
    assert progress == [(1, 2, "", 1), (2, 2, "clip.mp3", 2)]


def test_run_batch_stops_after_current_note_when_cancel_requested(monkeypatch, tmp_path: Path) -> None:
    col = FakeCol()
    cancel_event = threading.Event()
    progress_calls: list[int] = []

    def fake_process(*_args, **_kwargs) -> BatchNoteResult:
        return BatchNoteResult(
            note_id=int(_args[1]),
            status="written",
            message="appended viz.svg",
            target_field="Image",
            target_html='<img src="viz.svg">',
            audio_filename="clip.mp3",
            image_filename="viz.svg",
        )

    def on_progress(processed: int, *_args) -> None:
        progress_calls.append(processed)
        cancel_event.set()

    monkeypatch.setattr("anki_audio_quick_editor.browser_batch_runner.process_note", fake_process)

    report = run_batch(
        col,
        [1, 2],
        BatchRunRequest(operation=OP_GRAPH, source_field="Audio", target_field="Image"),
        tmp_path,
        AudioProcessingConfig(),
        cancel_event,
        lambda _line: None,
        on_progress,
    )

    assert report.canceled
    assert report.processed == 1
    assert report.written == 1
    assert col.updated == [1]
    assert col.merged == [42]
    assert progress_calls == [1]


def test_run_batch_uses_source_field_for_transform_updates(monkeypatch, tmp_path: Path) -> None:
    col = FakeCol()

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_batch_runner.process_note",
        lambda *_args, **_kwargs: BatchNoteResult(
            note_id=1,
            status="written",
            message="replaced audio with clip__aqe.mp3",
            target_field="Audio",
            target_html="[sound:clip__aqe.mp3]",
            audio_filename="clip.mp3",
            written_filename="clip__aqe.mp3",
        ),
    )

    report = run_batch(
        col,
        [1],
        BatchRunRequest(operation=OP_FASTER, source_field="Audio"),
        tmp_path,
        AudioProcessingConfig(),
        threading.Event(),
        lambda _line: None,
        lambda *_args: None,
    )

    assert report.written == 1
    assert col.notes[1].fields["Audio"] == "[sound:clip__aqe.mp3]"


def test_run_batch_logs_transform_parameters(monkeypatch, tmp_path: Path) -> None:
    col = FakeCol()
    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_batch_runner.process_note",
        lambda *_args, **_kwargs: BatchNoteResult(
            note_id=1,
            status="skipped",
            message="source field 'Audio' has no supported sound reference",
            audio_filename=None,
        ),
    )
    logs: list[str] = []

    run_batch(
        col,
        [1],
        BatchRunRequest(
            operation=OP_FASTER,
            source_field="Audio",
            parameters=AudioOperationParameters(speed_step=2),
        ),
        tmp_path,
        AudioProcessingConfig(),
        threading.Event(),
        logs.append,
        lambda *_args: None,
    )

    assert "parameters=" in logs[0]
    assert "speed_step=2" in logs[0]


def test_run_batch_in_background_publishes_changes_and_finishes_dialog(monkeypatch, tmp_path: Path) -> None:
    report = BatchRunReport(total=1, processed=1, written=1, changes=object())
    calls: list[object] = []

    class Taskman:
        def run_on_main(self, callback) -> None:
            callback()

        def run_in_background(self, task, done, *, uses_collection: bool) -> None:
            calls.append(("uses_collection", uses_collection))
            calls.append(("task_result", task()))
            done(SimpleNamespace(result=lambda: report))

    browser = SimpleNamespace(
        mw=SimpleNamespace(
            addonManager=SimpleNamespace(
                addonFromModule=lambda _module: "anki_audio_quick_editor",
                getConfig=lambda _addon_id: {},
                addonsFolder=lambda _addon_id: str(tmp_path / "addon"),
            ),
            col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(tmp_path / "media"))),
            taskman=Taskman(),
            update_undo_actions=MagicMock(),
        )
    )
    dialog = SimpleNamespace(
        cancel_event=threading.Event(),
        append_log=MagicMock(),
        update_progress=MagicMock(),
        finish_with_report=MagicMock(),
        finish_with_error=MagicMock(),
    )
    monkeypatch.setattr("anki_audio_quick_editor.browser_batch_runner.run_batch", lambda *_args, **_kwargs: report)

    run_batch_in_background(
        browser,
        dialog,
        [1],
        BatchRunRequest(operation=OP_GRAPH, source_field="Audio", target_field="Image"),
    )

    assert calls[0] == ("uses_collection", True)
    assert calls[1] == ("task_result", report)
    browser.mw.update_undo_actions.assert_called_once()
    aqt.gui_hooks.operation_did_execute.assert_called_once_with(report.changes, browser)
    dialog.finish_with_report.assert_called_once_with(report)
    dialog.finish_with_error.assert_not_called()


def test_run_batch_in_background_finishes_with_error(tmp_path: Path) -> None:
    class Taskman:
        def run_on_main(self, callback) -> None:
            callback()

        def run_in_background(self, task, done, *, uses_collection: bool) -> None:
            del task, uses_collection
            done(SimpleNamespace(result=MagicMock(side_effect=RuntimeError("worker exploded"))))

    browser = SimpleNamespace(
        mw=SimpleNamespace(
            addonManager=SimpleNamespace(
                addonFromModule=lambda _module: "anki_audio_quick_editor",
                getConfig=lambda _addon_id: {},
                addonsFolder=lambda _addon_id: str(tmp_path / "addon"),
            ),
            col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(tmp_path / "media"))),
            taskman=Taskman(),
            update_undo_actions=MagicMock(),
        )
    )
    dialog = SimpleNamespace(
        cancel_event=threading.Event(),
        append_log=MagicMock(),
        update_progress=MagicMock(),
        finish_with_report=MagicMock(),
        finish_with_error=MagicMock(),
    )

    run_batch_in_background(
        browser,
        dialog,
        [1],
        BatchRunRequest(operation=OP_GRAPH, source_field="Audio", target_field="Image"),
    )

    dialog.finish_with_error.assert_called_once_with("Batch operation failed: worker exploded")
    dialog.finish_with_report.assert_not_called()
    browser.mw.update_undo_actions.assert_not_called()
    aqt.gui_hooks.operation_did_execute.assert_not_called()
