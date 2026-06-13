"""Browser audio export execution for external files."""

from __future__ import annotations

import os
import tempfile
import threading
import zipfile
from collections.abc import Callable, Sequence
from pathlib import Path

from .audio_export_planning import collect_audio_export_items, make_zip_entry_name
from .audio_export_types import (
    EXPORT_MODE_ZIP,
    AudioExportItem,
    AudioExportNotice,
    AudioExportReport,
    AudioExportRequest,
)
from .batch_operations import BatchNoteSnapshot
from .i18n import active_context, format_message

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int, str, int], None]


def run_audio_export(
    snapshots: Sequence[BatchNoteSnapshot],
    *,
    request: AudioExportRequest,
    media_dir: Path,
    cancel_event: threading.Event,
    on_log: LogCallback,
    on_progress: ProgressCallback,
) -> AudioExportReport:
    """Run a non-mutating export of selected card audio."""
    plan = collect_audio_export_items(
        list(snapshots),
        media_dir=media_dir,
        field_selections=request.field_selections,
    )
    report = AudioExportReport(
        total=len(plan.items),
        skipped=len(plan.skipped),
        failures=len(plan.failures),
        output_path=str(request.destination_path),
        messages=dict(active_context()["messages"]),
    )

    messages = report.messages
    _add_log(report, on_log, format_message(messages, "audio_export.starting"))
    for notice in plan.skipped:
        _add_log(report, on_log, _format_notice("Skipped", notice))
    for notice in plan.failures:
        _add_log(report, on_log, _format_notice("Failed", notice))

    if request.mode != EXPORT_MODE_ZIP:
        raise ValueError(f"Unsupported export mode: {request.mode}")

    if not plan.items:
        _add_log(report, on_log, report.summary)
        return report

    _write_zip_export(
        plan.items,
        destination_path=request.destination_path,
        report=report,
        cancel_event=cancel_event,
        on_log=on_log,
        on_progress=on_progress,
    )
    _add_log(report, on_log, report.summary)
    return report


def _write_zip_export(
    items: Sequence[AudioExportItem],
    *,
    destination_path: Path,
    report: AudioExportReport,
    cancel_event: threading.Event,
    on_log: LogCallback,
    on_progress: ProgressCallback,
) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{destination_path.name}.",
        suffix=".tmp",
        dir=destination_path.parent,
    )
    os.close(file_descriptor)
    temp_path = Path(temp_name)
    used_names: set[str] = set()

    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in items:
                if cancel_event.is_set():
                    report.canceled = True
                    break

                entry_name = make_zip_entry_name(item, used_names=used_names)
                archive.write(item.source_path, arcname=entry_name)
                report.processed += 1
                report.exported += 1
                _add_log(report, on_log, f"Exported {item.original_filename} as {entry_name}.")
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


def _add_log(report: AudioExportReport, on_log: LogCallback, line: str) -> None:
    report.log_lines.append(line)
    on_log(line)


def _format_notice(prefix: str, notice: AudioExportNotice) -> str:
    return f"{prefix} note {notice.note_id}, field {notice.field_name!r}: {notice.message}"


def _remove_temp_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
