from __future__ import annotations

import threading
import zipfile
from pathlib import Path

from anki_audio_quick_editor.audio_export_types import (
    AudioExportFieldSelection,
    AudioExportRequest,
)
from anki_audio_quick_editor.batch_operation_types import BatchNoteSnapshot
from anki_audio_quick_editor.browser_audio_export_runner import run_audio_export


def test_run_audio_export_normalized_zip_renders_mp3_entries_without_mutating_notes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "a.ogg").write_bytes(b"source-a")
    (media_dir / "b.wav").write_bytes(b"source-b")
    snapshots = [
        BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.ogg]", "Back": "[sound:b.wav]"}),
    ]
    original_fields = dict(snapshots[0].fields)
    destination = tmp_path / "normalized.zip"
    commands: list[tuple[str, ...]] = []
    logs: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner.find_ffmpeg",
        lambda _path="": Path("/bin/ffmpeg"),
    )

    def fake_run(command, *_args, **_kwargs):
        commands.append(tuple(command))
        Path(command[-1]).write_bytes(f"normalized:{Path(command[3]).name}".encode())

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner._run_export_command",
        fake_run,
    )

    report = run_audio_export(
        snapshots,
        request=AudioExportRequest(
            mode="zip",
            destination_path=destination,
            field_selections=(AudioExportFieldSelection("Basic", ("Front", "Back")),),
            normalize_volume=True,
        ),
        media_dir=media_dir,
        cancel_event=threading.Event(),
        on_log=logs.append,
        on_progress=lambda *_args: None,
    )

    assert snapshots[0].fields == original_fields
    assert report.processed == 2
    assert report.exported == 2
    assert len(commands) == 2
    assert all("-filter:a" in command for command in commands)
    assert all("loudnorm=I=-16:TP=-1.5:LRA=11" in command for command in commands)
    assert any("Normalized and exported a.ogg" in line for line in logs)
    with zipfile.ZipFile(destination) as archive:
        assert archive.namelist() == [
            "0001__note-10__Front__001__a.mp3",
            "0002__note-10__Back__001__b.mp3",
        ]
        assert archive.read("0001__note-10__Front__001__a.mp3") == b"normalized:a.ogg"
        assert archive.read("0002__note-10__Back__001__b.mp3") == b"normalized:b.wav"


def test_run_audio_export_normalized_zip_deduplicates_repeated_sources(
    monkeypatch,
    tmp_path: Path,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "vertrage.ogg").write_bytes(b"source")
    destination = tmp_path / "normalized.zip"
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner.find_ffmpeg",
        lambda _path="": Path("/bin/ffmpeg"),
    )

    def fake_run(command, *_args, **_kwargs):
        commands.append(tuple(command))
        Path(command[-1]).write_bytes(b"normalized")

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner._run_export_command",
        fake_run,
    )

    report = run_audio_export(
        [
            BatchNoteSnapshot(
                10,
                "Basic",
                {"Front": "[sound:vertrage.ogg] [sound:vertrage.ogg]"},
            ),
            BatchNoteSnapshot(11, "Basic", {"Front": "[sound:vertrage.ogg]"}),
        ],
        request=AudioExportRequest(
            mode="zip",
            destination_path=destination,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
            normalize_volume=True,
        ),
        media_dir=media_dir,
        cancel_event=threading.Event(),
        on_log=lambda _line: None,
        on_progress=lambda *_args: None,
    )

    assert report.processed == 1
    assert report.exported == 1
    assert len(commands) == 1
    with zipfile.ZipFile(destination) as archive:
        assert archive.namelist() == ["0001__note-10__Front__001__vertrage.mp3"]


def test_run_audio_export_normalized_zip_cancellation_removes_temporary_files(
    monkeypatch,
    tmp_path: Path,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "a.mp3").write_bytes(b"a")
    (media_dir / "b.mp3").write_bytes(b"b")
    destination = tmp_path / "canceled-normalized.zip"
    cancel_event = threading.Event()

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner.find_ffmpeg",
        lambda _path="": Path("/bin/ffmpeg"),
    )

    def fake_run(command, *_args, **_kwargs):
        Path(command[-1]).write_bytes(b"normalized")

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner._run_export_command",
        fake_run,
    )

    def cancel_after_first_file(processed: int, *_args) -> None:
        if processed == 1:
            cancel_event.set()

    report = run_audio_export(
        [BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] [sound:b.mp3]"})],
        request=AudioExportRequest(
            mode="zip",
            destination_path=destination,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
            normalize_volume=True,
        ),
        media_dir=media_dir,
        cancel_event=cancel_event,
        on_log=lambda _line: None,
        on_progress=cancel_after_first_file,
    )

    assert report.canceled is True
    assert report.processed == 1
    assert report.exported == 1
    assert not destination.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["media"]


def test_run_audio_export_combined_mp3_uses_loudnorm_when_requested(
    monkeypatch,
    tmp_path: Path,
) -> None:
    media = tmp_path / "media"
    media.mkdir()
    (media / "a.mp3").write_bytes(b"a")
    output = tmp_path / "out.mp3"
    commands: list[tuple[str, ...]] = []
    logs: list[str] = []

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
        (BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3]"}),),
        request=AudioExportRequest(
            mode="combined_mp3",
            destination_path=output,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
            silence_between_clips_seconds=0,
            normalize_volume=True,
        ),
        media_dir=media,
        cancel_event=threading.Event(),
        on_log=logs.append,
        on_progress=lambda *_args: None,
    )

    assert report.exported == 1
    assert output.read_bytes() == b"rendered"
    assert len(commands) == 2
    assert "loudnorm=I=-16:TP=-1.5:LRA=11" in commands[0]
    assert "loudnorm=I=-16:TP=-1.5:LRA=11" not in commands[-1]
    assert any("Normalized a.mp3 for combined MP3 export." in line for line in logs)


def test_run_audio_export_normalized_combined_mp3_cancellation_removes_temporary_files(
    monkeypatch,
    tmp_path: Path,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "a.mp3").write_bytes(b"a")
    (media_dir / "b.mp3").write_bytes(b"b")
    destination = tmp_path / "canceled-normalized.mp3"
    cancel_event = threading.Event()

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner.find_ffmpeg",
        lambda _path="": Path("/bin/ffmpeg"),
    )

    def fake_run(command, *_args, **_kwargs):
        Path(command[-1]).write_bytes(b"rendered")

    monkeypatch.setattr(
        "anki_audio_quick_editor.browser_audio_export_runner._run_export_command",
        fake_run,
    )

    def cancel_after_first_file(processed: int, *_args) -> None:
        if processed == 1:
            cancel_event.set()

    report = run_audio_export(
        [BatchNoteSnapshot(10, "Basic", {"Front": "[sound:a.mp3] [sound:b.mp3]"})],
        request=AudioExportRequest(
            mode="combined_mp3",
            destination_path=destination,
            field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
            silence_between_clips_seconds=0,
            normalize_volume=True,
        ),
        media_dir=media_dir,
        cancel_event=cancel_event,
        on_log=lambda _line: None,
        on_progress=cancel_after_first_file,
    )

    assert report.canceled is True
    assert report.processed == 1
    assert report.exported == 1
    assert not destination.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["media"]
