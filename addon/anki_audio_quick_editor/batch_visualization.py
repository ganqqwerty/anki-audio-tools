"""Import-safe batch visualization planning and per-note processing."""

from __future__ import annotations

import html
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .audio_state import AudioProcessingConfig
from .errors import AudioQuickEditorError
from .prosody_cache import analyze_prosody_cached
from .prosody_svg import make_visualization_filename, render_prosody_svg
from .sound_refs import safe_media_basename, select_first_sound_reference

MediaWriter = Callable[[str, bytes], str]
NowProvider = Callable[[], datetime]


@dataclass(frozen=True)
class BatchNoteSnapshot:
    """Minimal note data needed by import-safe batch logic."""

    note_id: int
    notetype_name: str
    fields: dict[str, str]


@dataclass(frozen=True)
class FieldGroup:
    """Fields available on one note type in the current batch selection."""

    notetype_name: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class BatchNoteResult:
    """Outcome of processing one note snapshot."""

    note_id: int
    status: str
    message: str
    target_field: str | None = None
    target_html: str | None = None
    audio_filename: str | None = None
    image_filename: str | None = None

    @property
    def written(self) -> bool:
        """Return true when the caller should persist ``target_html``."""
        return self.status == "written"

    @property
    def failure(self) -> bool:
        """Return true when this result should increment the failure count."""
        return self.status == "failed"


def unique_note_ids(note_ids: Sequence[int]) -> list[int]:
    """Return note IDs once, preserving first-seen order."""
    seen: set[int] = set()
    deduped: list[int] = []
    for note_id in note_ids:
        value = int(note_id)
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def field_groups_for_notes(notes: Sequence[BatchNoteSnapshot]) -> tuple[FieldGroup, ...]:
    """Return field choices grouped by note type from selected note snapshots."""
    grouped: dict[str, list[str]] = {}
    for note in notes:
        fields = grouped.setdefault(note.notetype_name, [])
        for field_name in note.fields:
            if field_name not in fields:
                fields.append(field_name)
    return tuple(
        FieldGroup(notetype_name=name, fields=tuple(fields))
        for name, fields in sorted(grouped.items(), key=lambda item: item[0].casefold())
    )


def append_image_reference(field_html: str, image_filename: str) -> str:
    """Append an Anki image media reference on a new visual line."""
    image_tag = f'<img src="{html.escape(image_filename, quote=True)}">'  # pragma: no mutate
    return f"{field_html}<br>{image_tag}" if field_html else image_tag


def first_audio_filename(note: BatchNoteSnapshot, source_field: str) -> str | None:
    """Return the selected source audio filename for progress display, if available."""
    if source_field not in note.fields:
        return None
    try:
        selection = select_first_sound_reference(note.fields[source_field])
    except AudioQuickEditorError:
        return None
    if selection.selected is None:
        return None
    return safe_media_basename(selection.selected.filename)


def process_note_visualization(
    note: BatchNoteSnapshot,
    *,
    source_field: str,
    target_field: str,
    media_dir: Path,
    config: AudioProcessingConfig,
    media_writer: MediaWriter,
    now_provider: NowProvider | None = None,
) -> BatchNoteResult:
    """Generate and append one visualization for ``note`` when possible."""
    if source_field not in note.fields:
        return _skipped(note, f"missing source field {source_field!r}")
    if target_field not in note.fields:
        return _skipped(note, f"missing target field {target_field!r}")

    source_html = note.fields[source_field]
    try:
        selection = select_first_sound_reference(source_html)
    except AudioQuickEditorError as exc:
        return _skipped(note, str(exc))
    if selection.selected is None:
        return _skipped(note, f"source field {source_field!r} has no supported sound reference")

    audio_filename = safe_media_basename(selection.selected.filename)
    source_path = media_dir / audio_filename
    if not source_path.is_file():
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=f"media file not found: {audio_filename}",
            audio_filename=audio_filename,
        )

    try:
        track = analyze_prosody_cached(source_path, config)
        svg_bytes = render_prosody_svg(track)
        desired_name = make_visualization_filename(
            audio_filename,
            now=(now_provider() if now_provider else None),
        )
        saved_name = media_writer(desired_name, svg_bytes)
    except Exception as exc:
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=str(exc) or "visualization generation failed",
            audio_filename=audio_filename,
        )

    return BatchNoteResult(
        note_id=note.note_id,
        status="written",
        message=f"appended {saved_name}",
        target_field=target_field,
        target_html=append_image_reference(note.fields[target_field], saved_name),
        audio_filename=audio_filename,
        image_filename=saved_name,
    )


def _skipped(note: BatchNoteSnapshot, message: str) -> BatchNoteResult:
    return BatchNoteResult(note_id=note.note_id, status="skipped", message=message)
