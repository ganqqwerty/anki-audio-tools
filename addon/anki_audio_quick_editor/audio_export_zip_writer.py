"""ZIP writing side effects for Browser audio export."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import zipfile
from collections.abc import Callable, Sequence
from pathlib import Path

from .audio_export_planning import make_zip_entry_name
from .audio_export_rendering import build_normalized_mp3_command
from .audio_export_types import AudioExportItem, AudioExportReport

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int, str, int], None]
RunExportCommand = Callable[[tuple[str, ...], str], None]


def write_zip_export(
    items: Sequence[AudioExportItem],
    *,
    destination_path: Path,
    normalize_volume: bool,
    ffmpeg_path: Path | None,
    cancel_event: threading.Event,
    report: AudioExportReport,
    on_log: LogCallback,
    on_progress: ProgressCallback,
    run_export_command: RunExportCommand,
) -> None:
    """Write selected export items to a ZIP archive without mutating Anki media."""
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{destination_path.name}.",
        suffix=".tmp",
        dir=destination_path.parent,
    )
    os.close(file_descriptor)
    temp_path = Path(temp_name)
    temp_root = (
        Path(tempfile.mkdtemp(prefix="aqe_audio_export_zip_", dir=destination_path.parent))
        if normalize_volume
        else None
    )
    used_names: set[str] = set()

    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in items:
                if cancel_event.is_set():
                    report.canceled = True
                    break

                entry_name, source_path, log_line = _prepare_zip_entry(
                    item,
                    archive_temp_root=temp_root,
                    ffmpeg_path=ffmpeg_path,
                    normalize_volume=normalize_volume,
                    run_export_command=run_export_command,
                    used_names=used_names,
                )
                archive.write(source_path, arcname=entry_name)
                report.processed += 1
                report.exported += 1
                _add_log(report, on_log, log_line)
                on_progress(
                    report.processed,
                    report.total,
                    item.original_filename,
                    report.failures,
                )

                if cancel_event.is_set():
                    report.canceled = True
                    break

        if report.canceled:
            _remove_temp_file(temp_path)
            return

        temp_path.replace(destination_path)
    finally:
        if temp_path.exists():
            _remove_temp_file(temp_path)
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)


def _prepare_zip_entry(
    item: AudioExportItem,
    *,
    archive_temp_root: Path | None,
    ffmpeg_path: Path | None,
    normalize_volume: bool,
    run_export_command: RunExportCommand,
    used_names: set[str],
) -> tuple[str, Path, str]:
    if not normalize_volume:
        entry_name = make_zip_entry_name(item, used_names=used_names)
        return entry_name, item.source_path, f"Exported {item.original_filename} as {entry_name}."

    if archive_temp_root is None or ffmpeg_path is None:
        raise RuntimeError("Audio export normalization was not initialized.")
    rendered_path = archive_temp_root / f"{item.sequence:05d}.mp3"
    run_export_command(
        build_normalized_mp3_command(ffmpeg_path, item.source_path, rendered_path),
        "Could not start audio export normalization.",
    )
    entry_name = make_zip_entry_name(item, used_names=used_names, forced_suffix=".mp3")
    return (
        entry_name,
        rendered_path,
        f"Normalized and exported {item.original_filename} as {entry_name}.",
    )


def _add_log(report: AudioExportReport, on_log: LogCallback, line: str) -> None:
    report.log_lines.append(line)
    on_log(line)


def _remove_temp_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
