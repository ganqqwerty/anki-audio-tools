"""Browser audio export execution for external files."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import zipfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .audio_export_planning import collect_audio_export_items, make_zip_entry_name
from .audio_export_rendering import (
    build_concat_list_text,
    build_final_mp3_command,
    build_normalize_wav_command,
    build_silence_wav_command,
    validate_final_mp3_output,
)
from .audio_export_types import (
    EXPORT_MODE_COMBINED_MP3,
    EXPORT_MODE_ZIP,
    AudioExportItem,
    AudioExportNotice,
    AudioExportReport,
    AudioExportRequest,
)
from .audio_external import (
    _render_external_error_message,
    _run_external_command,
)
from .audio_processor import find_ffmpeg
from .batch_operation_types import BatchNoteSnapshot
from .error_codes import AQE_BATCH_INVALID_REQUEST, coded_error
from .i18n import active_context, format_message

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int, str, int], None]


def run_audio_export_in_background(
    browser: Any,
    dialog: Any,
    snapshots: Sequence[BatchNoteSnapshot],
    request: AudioExportRequest,
) -> None:
    """Schedule a Browser audio export in Anki's background task manager."""
    mw = getattr(browser, "mw", browser)
    media_dir = Path(mw.col.media.dir())

    def on_log(line: str) -> None:
        mw.taskman.run_on_main(lambda value=line: dialog.append_log(value))

    def on_progress(processed: int, total: int, current_audio: str, failures: int) -> None:
        mw.taskman.run_on_main(
            lambda: dialog.update_progress(processed, total, current_audio, failures)
        )

    def task() -> AudioExportReport:
        return run_audio_export(
            snapshots,
            request=request,
            media_dir=media_dir,
            cancel_event=dialog.cancel_event,
            on_log=on_log,
            on_progress=on_progress,
        )

    def done(future: Any) -> None:
        try:
            report = future.result()
        except Exception as exc:
            message = _tr("audio_export.failed", {"error": exc})
            dialog.finish_with_error(
                message,
                user_error=coded_error(AQE_BATCH_INVALID_REQUEST, message),
            )
            return
        dialog.finish_with_report(report)

    mw.taskman.run_in_background(task, done, uses_collection=True)


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

    if request.mode not in {EXPORT_MODE_ZIP, EXPORT_MODE_COMBINED_MP3}:
        raise ValueError(f"Unsupported export mode: {request.mode}")

    if not plan.items:
        _add_log(report, on_log, report.summary)
        return report

    if request.mode == EXPORT_MODE_ZIP:
        _write_zip_export(
            plan.items,
            destination_path=request.destination_path,
            report=report,
            cancel_event=cancel_event,
            on_log=on_log,
            on_progress=on_progress,
        )
    elif request.mode == EXPORT_MODE_COMBINED_MP3:
        _write_combined_mp3_export(
            plan.items,
            request=request,
            cancel_event=cancel_event,
            report=report,
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


def _write_combined_mp3_export(
    items: Sequence[AudioExportItem],
    *,
    request: AudioExportRequest,
    cancel_event: threading.Event,
    report: AudioExportReport,
    on_log: LogCallback,
    on_progress: ProgressCallback,
) -> None:
    destination_path = request.destination_path
    validate_final_mp3_output(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = find_ffmpeg()
    temp_root = Path(tempfile.mkdtemp(prefix="aqe_audio_export_"))
    file_descriptor, temp_output_name = tempfile.mkstemp(
        prefix=f".{destination_path.name}.",
        suffix=".tmp.mp3",
        dir=destination_path.parent,
    )
    os.close(file_descriptor)
    temp_output_path = Path(temp_output_name)
    normalized_paths: list[Path] = []

    try:
        for item in items:
            if cancel_event.is_set():
                report.canceled = True
                break

            output_path = temp_root / f"{item.sequence:05d}.wav"
            _run_export_command(
                build_normalize_wav_command(ffmpeg_path, item.source_path, output_path),
                "Could not start audio export rendering.",
            )
            normalized_paths.append(output_path)
            report.processed += 1
            report.exported += 1
            _add_log(report, on_log, f"Prepared {item.original_filename} for combined MP3 export.")
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
            return

        concat_paths = _concat_paths_with_silence(
            normalized_paths,
            silence_between_clips_seconds=request.silence_between_clips_seconds,
            temp_root=temp_root,
            ffmpeg_path=ffmpeg_path,
        )
        if cancel_event.is_set():
            report.canceled = True
            return

        concat_list_path = temp_root / "concat.txt"
        concat_list_path.write_text(build_concat_list_text(concat_paths), encoding="utf-8")
        _run_export_command(
            build_final_mp3_command(ffmpeg_path, concat_list_path, temp_output_path),
            "Could not start audio export finalization.",
        )
        if cancel_event.is_set():
            report.canceled = True
            return

        temp_output_path.replace(destination_path)
    finally:
        if temp_output_path.exists():
            _remove_temp_file(temp_output_path)
        shutil.rmtree(temp_root, ignore_errors=True)


def _concat_paths_with_silence(
    paths: Sequence[Path],
    *,
    silence_between_clips_seconds: float,
    temp_root: Path,
    ffmpeg_path: Path,
) -> tuple[Path, ...]:
    if len(paths) <= 1 or silence_between_clips_seconds <= 0:
        return tuple(paths)

    silence_path = temp_root / "silence.wav"
    _run_export_command(
        build_silence_wav_command(ffmpeg_path, silence_between_clips_seconds, silence_path),
        "Could not start audio export silence rendering.",
    )
    concat_paths: list[Path] = []
    for path in paths:
        if concat_paths:
            concat_paths.append(silence_path)
        concat_paths.append(path)
    return tuple(concat_paths)


def _run_export_command(command: tuple[str, ...], launch_error_prefix: str) -> None:
    result = _run_external_command(command, launch_error_prefix)
    if result.returncode != 0:
        raise RuntimeError(_render_external_error_message(result, "Audio export failed."))


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


def _tr(key: str, values: dict[str, object] | None = None) -> str:
    return format_message(dict(active_context()["messages"]), key, values)
