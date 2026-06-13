from __future__ import annotations

import threading
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_export_planning import (
    collect_audio_export_items,
    make_zip_entry_name,
)
from anki_audio_quick_editor.audio_export_types import (
    AudioExportFieldSelection,
    AudioExportItem,
    AudioExportReport,
    AudioExportRequest,
)
from anki_audio_quick_editor.batch_operation_types import BatchNoteSnapshot
from anki_audio_quick_editor.browser_audio_export_runner import (
    run_audio_export,
    run_audio_export_in_background,
)
from anki_audio_quick_editor.errors import AudioProcessingError


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


def test_run_audio_export_combined_mp3_invokes_render_steps(monkeypatch, tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    (media / "a.mp3").write_bytes(b"a")
    (media / "b.wav").write_bytes(b"b")
    output = tmp_path / "out.mp3"
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner.find_ffmpeg",
        lambda _path="": Path("/bin/ffmpeg"),
    )

    def fake_run(command, *_args, **_kwargs):
        commands.append(tuple(command))
        Path(command[-1]).write_bytes(b"rendered")

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner._run_export_command",
        fake_run,
    )

    report = run_audio_export(
        (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] [sound:b.wav]"}),),
        request=AudioExportRequest(
            mode="combined_mp3",
            destination_path=output,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
            silence_between_clips_seconds=0.5,
        ),
        media_dir=media,
        cancel_event=threading.Event(),
        on_log=lambda _line: None,
        on_progress=lambda *_args: None,
    )

    assert report.exported == 2
    assert output.read_bytes() == b"rendered"
    assert len(commands) == 4
    assert commands[0][0] == "/bin/ffmpeg"
    assert commands[-1][-1].endswith(".mp3")


def test_run_audio_export_combined_mp3_rejects_non_mp3_destination_before_rendering(
    monkeypatch,
    tmp_path: Path,
) -> None:
    media = tmp_path / "media"
    media.mkdir()
    (media / "a.mp3").write_bytes(b"a")
    output = tmp_path / "out.wav"
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner.find_ffmpeg",
        lambda _path="": Path("/bin/ffmpeg"),
    )

    def fake_run(command, *_args, **_kwargs):
        commands.append(tuple(command))
        Path(command[-1]).write_bytes(b"rendered")

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner._run_export_command",
        fake_run,
    )

    with pytest.raises(AudioProcessingError):
        run_audio_export(
            (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3]"}),),
            request=AudioExportRequest(
                mode="combined_mp3",
                destination_path=output,
                field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
            ),
            media_dir=media,
            cancel_event=threading.Event(),
            on_log=lambda _line: None,
            on_progress=lambda *_args: None,
        )

    assert commands == []
    assert not output.exists()


def test_run_audio_export_in_background_routes_callbacks_and_finishes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    report = AudioExportReport(total=1, processed=1, exported=1)
    snapshots = (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3]"}),)
    request = AudioExportRequest(
        mode="zip",
        destination_path=tmp_path / "out.zip",
        field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
    )
    calls: list[object] = []

    class Taskman:
        def run_on_main(self, callback) -> None:
            callback()

        def run_in_background(self, task, done, *, uses_collection: bool) -> None:
            calls.append(("uses_collection", uses_collection))
            calls.append(("task_result", task()))
            done(SimpleNamespace(result=lambda: report))

    media_dir = tmp_path / "media"
    browser = SimpleNamespace(
        mw=SimpleNamespace(
            col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
            taskman=Taskman(),
        )
    )
    dialog = SimpleNamespace(
        cancel_event=threading.Event(),
        append_log=MagicMock(),
        update_progress=MagicMock(),
        finish_with_report=MagicMock(),
        finish_with_error=MagicMock(),
    )

    def fake_run(snapshots_arg, **kwargs):
        assert snapshots_arg == snapshots
        assert kwargs["request"] == request
        assert kwargs["media_dir"] == media_dir
        kwargs["on_log"]("line")
        kwargs["on_progress"](1, 1, "a.mp3", 0)
        return report

    monkeypatch.setattr("anki_audio_quick_editor.browser_audio_export_runner.run_audio_export", fake_run)

    run_audio_export_in_background(browser, dialog, snapshots, request)

    assert calls == [("uses_collection", True), ("task_result", report)]
    dialog.append_log.assert_called_once_with("line")
    dialog.update_progress.assert_called_once_with(1, 1, "a.mp3", 0)
    dialog.finish_with_report.assert_called_once_with(report)
    dialog.finish_with_error.assert_not_called()


def report_plan_items_for_names(media_dir: Path) -> tuple[AudioExportItem, ...]:
    return collect_audio_export_items(
        [BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3]", "Back": "[sound:b.wav]"})],
        media_dir=media_dir,
        field_selections=(AudioExportFieldSelection("Basic", ("Front", "Back")),),
    ).items
