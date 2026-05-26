"""Tests for Browser batch visualization integration."""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_operations import OP_FASTER, OP_GRAPH
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import (
    BatchNoteResult,
    BatchRunRequest,
    FieldGroup,
)
from anki_audio_quick_editor.browser_dialog import BatchOperationsDialog
from anki_audio_quick_editor.browser_integration import (
    ACTION_LABEL,
    BatchRunReport,
    _apply_result,
    _on_browser_menus_did_init,
    _open_batch_dialog,
    _publish_collection_changes,
    _run_batch,
    _run_batch_in_background,
    register_browser_hooks,
)
from anki_audio_quick_editor.webview_bridge import WebviewBridgeCommand


def test_register_browser_hooks() -> None:
    hooks = SimpleNamespace(browser_menus_did_init=MagicMock(), browser_will_show_context_menu=MagicMock())

    register_browser_hooks(hooks)

    hooks.browser_menus_did_init.append.assert_called_once()
    hooks.browser_will_show_context_menu.append.assert_not_called()


def test_browser_menu_action_is_added() -> None:
    browser = SimpleNamespace(form=SimpleNamespace(menu_Cards=MagicMock()))

    _on_browser_menus_did_init(browser)

    browser.form.menu_Cards.addAction.assert_called_once_with(ACTION_LABEL)
    assert aqt.qt.qconnect.called


def test_empty_selection_shows_warning() -> None:
    browser = SimpleNamespace(selected_notes=lambda: [], mw=MagicMock())

    _open_batch_dialog(browser)

    aqt.utils.showWarning.assert_called_once()


def test_selection_without_fields_shows_warning(monkeypatch) -> None:
    browser = SimpleNamespace(selected_notes=lambda: [1], mw=SimpleNamespace(col=MagicMock()))

    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._snapshots_for_note_ids", lambda *_args: [])

    _open_batch_dialog(browser)

    aqt.utils.showWarning.assert_called_once_with(
        "The selected cards do not expose any note fields.",
        parent=browser,
    )


def test_open_batch_dialog_builds_field_groups_from_selected_notes(monkeypatch) -> None:
    dialog_calls: list[tuple[object, ...]] = []

    class Dialog:
        def exec(self) -> None:
            dialog_calls.append(("exec", ()))  # type: ignore[arg-type]

    def create_dialog(
        _browser: object,
        note_ids: list[int],
        groups: tuple[object, ...],
        config: AudioProcessingConfig,
    ) -> Dialog:
        dialog_calls.append((note_ids, groups, config))
        return Dialog()

    col = SimpleNamespace(get_note=lambda _note_id: _FakeNote(int(_note_id)))
    addon_manager = SimpleNamespace(
        addonFromModule=lambda _module: "anki_audio_quick_editor",
        getConfig=lambda _addon_id: {
            "speed_step": 2.0,
            "volume_step_db": 6.0,
            "pause_aggressiveness": "aggressive",
        },
    )
    browser = SimpleNamespace(
        selected_notes=lambda: [2, 1, 2],
        mw=SimpleNamespace(col=col, addonManager=addon_manager),
    )
    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._create_dialog", create_dialog)

    _open_batch_dialog(browser)

    assert dialog_calls[0][0] == [2, 1]
    groups = dialog_calls[0][1]
    assert len(groups) == 1
    assert groups[0].notetype_name == "Basic"
    assert groups[0].fields == ("Audio", "Image")
    config = dialog_calls[0][2]
    assert config.speed_step == 2.0
    assert config.volume_step_db == 6.0
    assert config.pause_aggressiveness == "aggressive"
    assert dialog_calls[1] == ("exec", ())


class _FakeNote:
    def __init__(self, note_id: int) -> None:
        self.id = note_id
        self.fields = {"Audio": "[sound:clip.mp3]", "Image": ""}

    def note_type(self) -> dict:
        return {"name": "Basic"}

    def items(self) -> list[tuple[str, str]]:
        return list(self.fields.items())

    def __setitem__(self, key: str, value: str) -> None:
        self.fields[key] = value


class _FakeCol:
    def __init__(self) -> None:
        self.notes = {1: _FakeNote(1), 2: _FakeNote(2)}
        self.updated: list[int] = []
        self.merged: list[int] = []
        self.media = SimpleNamespace(write_data=lambda name, data: name)

    def get_note(self, note_id: int) -> _FakeNote:
        return self.notes[note_id]

    def add_custom_undo_entry(self, _name: str) -> int:
        return 42

    def update_note(self, note: _FakeNote) -> object:
        self.updated.append(int(note.id))
        return object()

    def merge_undo_entries(self, entry: int) -> object:
        self.merged.append(entry)
        return object()


def test_run_batch_reports_note_load_and_update_failures(monkeypatch, tmp_path: Path) -> None:
    class FailingCol(_FakeCol):
        def get_note(self, note_id: int) -> _FakeNote:
            if note_id == 1:
                raise RuntimeError("note disappeared")
            return super().get_note(note_id)

        def update_note(self, note: _FakeNote) -> object:
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
        "anki_audio_quick_editor.browser_integration.process_note_batch_operation",
        fake_process_note_batch_operation,
    )
    logs: list[str] = []
    progress: list[tuple[int, int, str, int]] = []

    report = _run_batch(
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
    col = _FakeCol()
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

    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._process_note", fake_process)

    report = _run_batch(
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
    col = _FakeCol()

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_integration._process_note",
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

    report = _run_batch(
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
    col = _FakeCol()
    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_integration._process_note",
        lambda *_args, **_kwargs: BatchNoteResult(
            note_id=1,
            status="skipped",
            message="source field 'Audio' has no supported sound reference",
            audio_filename=None,
        ),
    )
    logs: list[str] = []

    _run_batch(
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
    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._run_batch", lambda *_args, **_kwargs: report)

    _run_batch_in_background(
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

    _run_batch_in_background(
        browser,
        dialog,
        [1],
        BatchRunRequest(operation=OP_GRAPH, source_field="Audio", target_field="Image"),
    )

    dialog.finish_with_error.assert_called_once_with("Batch operation failed: worker exploded")
    dialog.finish_with_report.assert_not_called()
    browser.mw.update_undo_actions.assert_not_called()
    aqt.gui_hooks.operation_did_execute.assert_not_called()


def test_publish_collection_changes_ignores_empty_changes() -> None:
    browser = SimpleNamespace(mw=SimpleNamespace(update_undo_actions=MagicMock()))

    _publish_collection_changes(browser, None)

    browser.mw.update_undo_actions.assert_not_called()
    aqt.gui_hooks.operation_did_execute.assert_not_called()


def test_batch_dialog_ignores_duplicate_start_while_running() -> None:
    started: list[tuple[object, object, list[int], object]] = []

    def fake_run_batch(browser, dialog, note_ids, request):
        started.append((browser, dialog, list(note_ids), request))

    browser = SimpleNamespace(mw=SimpleNamespace())
    dialog = BatchOperationsDialog(
        browser,
        note_ids=[101, 102],
        groups=(FieldGroup("Basic", ("Front", "Back")),),
        config=AudioProcessingConfig(),
        run_batch_in_background=fake_run_batch,
    )
    payload = {
        "operation": "faster",
        "source_field": "Front",
        "target_field": "Front",
        "parameters": {"speed_step": 0.1},
    }
    command = WebviewBridgeCommand("batch.start", payload=payload)

    assert dialog._handle_batch_start(command)
    assert dialog._handle_batch_start(command)

    assert len(started) == 1
    assert dialog._running is True


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

    applied = _apply_result(col, report, result, fallback_field="Front")

    assert applied.status == "failed"
    assert "changed during batch processing" in applied.message
    assert note["Front"] == "[sound:old.mp3] user edit"
    col.update_note.assert_not_called()
    assert report.failures == 1
    assert report.written == 0
