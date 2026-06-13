from __future__ import annotations

import threading
import zipfile
from pathlib import Path

from anki_audio_quick_editor.audio_export_planning import (
    collect_audio_export_items,
    make_zip_entry_name,
)
from anki_audio_quick_editor.audio_export_types import (
    AudioExportFieldSelection,
    AudioExportItem,
    AudioExportRequest,
)
from anki_audio_quick_editor.batch_operations import BatchNoteSnapshot
from anki_audio_quick_editor.browser_audio_export_runner import run_audio_export


def test_run_audio_export_writes_ordered_zip_without_mutating_notes(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "a.mp3").write_bytes(b"aaa")
    (media_dir / "b.wav").write_bytes(b"bbb")
    snapshots = [
        BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3]", "Back": "[sound:b.wav]"}),
    ]
    original_fields = dict(snapshots[0].fields)
    destination = tmp_path / "export.zip"
    logs: list[str] = []
    progress: list[tuple[int, int, str, int]] = []

    report = run_audio_export(
        snapshots,
        request=AudioExportRequest(
            mode="zip",
            destination_path=destination,
            field_selections=(AudioExportFieldSelection("Basic", ("Front", "Back")),),
        ),
        media_dir=media_dir,
        cancel_event=threading.Event(),
        on_log=logs.append,
        on_progress=lambda processed, total, current_audio, failures: progress.append(
            (processed, total, current_audio, failures)
        ),
    )

    assert snapshots[0].fields == original_fields
    assert report.processed == 2
    assert report.exported == 2
    assert report.failures == 0
    assert report.skipped == 0
    assert progress[-1] == (2, 2, "b.wav", 0)
    assert logs[-1] == report.summary
    assert "Audio export completed" in report.summary

    used_names: set[str] = set()
    expected_names = [
        make_zip_entry_name(item, used_names=used_names)
        for item in report_plan_items_for_names(media_dir)
    ]
    plan_names: list[str] = []
    with zipfile.ZipFile(destination) as archive:
        for info in archive.infolist():
            plan_names.append(info.filename)
        assert plan_names == expected_names
        assert archive.read(plan_names[0]) == b"aaa"
        assert archive.read(plan_names[1]) == b"bbb"


def test_run_audio_export_returns_failures_without_promoting_empty_output(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    destination = tmp_path / "empty.zip"
    logs: list[str] = []

    report = run_audio_export(
        [BatchNoteSnapshot(10, "Basic", {"Front": "[sound:missing.mp3]"})],
        request=AudioExportRequest(
            mode="zip",
            destination_path=destination,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
        ),
        media_dir=media_dir,
        cancel_event=threading.Event(),
        on_log=logs.append,
        on_progress=lambda *_args: None,
    )

    assert report.total == 0
    assert report.processed == 0
    assert report.exported == 0
    assert report.failures == 1
    assert not destination.exists()
    assert any("media file not found: missing.mp3" in line for line in logs)
    assert logs[-1] == report.summary


def test_run_audio_export_cancellation_removes_temporary_zip(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "a.mp3").write_bytes(b"aaa")
    (media_dir / "b.wav").write_bytes(b"bbb")
    destination = tmp_path / "canceled.zip"
    cancel_event = threading.Event()
    progress: list[tuple[int, int, str, int]] = []

    def cancel_after_first_file(
        processed: int,
        total: int,
        current_audio: str,
        failures: int,
    ) -> None:
        progress.append((processed, total, current_audio, failures))
        if processed == 1:
            cancel_event.set()

    report = run_audio_export(
        [BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] [sound:b.wav]"})],
        request=AudioExportRequest(
            mode="zip",
            destination_path=destination,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
        ),
        media_dir=media_dir,
        cancel_event=cancel_event,
        on_log=lambda _line: None,
        on_progress=cancel_after_first_file,
    )

    assert report.canceled is True
    assert report.processed == 1
    assert report.exported == 1
    assert progress == [(1, 2, "a.mp3", 0)]
    assert not destination.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["media"]


def report_plan_items_for_names(media_dir: Path) -> tuple[AudioExportItem, ...]:
    return collect_audio_export_items(
        [BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3]", "Back": "[sound:b.wav]"})],
        media_dir=media_dir,
        field_selections=(AudioExportFieldSelection("Basic", ("Front", "Back")),),
    ).items
