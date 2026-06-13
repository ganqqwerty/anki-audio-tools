"""Import-safe planning for selected-card audio export."""

from __future__ import annotations

import re
from pathlib import Path

from .audio_export_types import (
    AudioExportFieldSelection,
    AudioExportItem,
    AudioExportNotice,
    AudioExportPlan,
)
from .batch_operations import BatchNoteSnapshot
from .media_paths import existing_media_file_path
from .sound_refs import (
    SoundReference,
    find_sound_references,
    is_supported_audio_filename,
    safe_media_basename,
)

_UNSAFE_ENTRY_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]+")


def default_audio_field_selections(
    notes: list[BatchNoteSnapshot] | tuple[BatchNoteSnapshot, ...],
) -> tuple[AudioExportFieldSelection, ...]:
    grouped: dict[str, list[str]] = {}
    for note in notes:
        fields = grouped.setdefault(note.notetype_name, [])
        for field_name in note.fields:
            if field_name in fields:
                continue
            field_html = note.fields[field_name]
            if any(
                is_supported_audio_filename(ref.filename)
                for ref in find_sound_references(field_html)
            ):
                fields.append(field_name)
    return tuple(
        AudioExportFieldSelection(notetype_name, tuple(fields))
        for notetype_name, fields in sorted(grouped.items(), key=lambda item: item[0].casefold())
        if fields
    )


def collect_audio_export_items(
    notes: list[BatchNoteSnapshot] | tuple[BatchNoteSnapshot, ...],
    *,
    media_dir: Path,
    field_selections: tuple[AudioExportFieldSelection, ...],
) -> AudioExportPlan:
    selected = {selection.notetype_name: selection.fields for selection in field_selections}
    items: list[AudioExportItem] = []
    skipped: list[AudioExportNotice] = []
    failures: list[AudioExportNotice] = []
    sequence = 1

    for note in notes:
        sequence = _collect_note_export_items(
            note,
            selected_fields=selected.get(note.notetype_name),
            media_dir=media_dir,
            items=items,
            skipped=skipped,
            failures=failures,
            sequence=sequence,
        )

    return AudioExportPlan(items=tuple(items), skipped=tuple(skipped), failures=tuple(failures))


def _collect_note_export_items(
    note: BatchNoteSnapshot,
    *,
    selected_fields: tuple[str, ...] | None,
    media_dir: Path,
    items: list[AudioExportItem],
    skipped: list[AudioExportNotice],
    failures: list[AudioExportNotice],
    sequence: int,
) -> int:
    if selected_fields is None:
        return sequence
    for field_name in selected_fields:
        sequence = _collect_field_export_items(
            note,
            field_name=field_name,
            media_dir=media_dir,
            items=items,
            skipped=skipped,
            failures=failures,
            sequence=sequence,
        )
    return sequence


def _collect_field_export_items(
    note: BatchNoteSnapshot,
    *,
    field_name: str,
    media_dir: Path,
    items: list[AudioExportItem],
    skipped: list[AudioExportNotice],
    failures: list[AudioExportNotice],
    sequence: int,
) -> int:
    if field_name not in note.fields:
        skipped.append(_notice(note, field_name, f"missing selected field {field_name!r}"))
        return sequence

    refs = _supported_sound_refs(note.fields[field_name])
    if not refs:
        skipped.append(_notice(note, field_name, f"field {field_name!r} has no supported sound reference"))
        return sequence

    for index, ref in enumerate(refs, start=1):
        filename = safe_media_basename(ref.filename)
        source_path = existing_media_file_path(media_dir, filename)
        if source_path is None:
            failures.append(_notice(note, field_name, f"media file not found: {filename}", filename))
            continue
        items.append(
            AudioExportItem(
                sequence=sequence,
                note_id=note.note_id,
                notetype_name=note.notetype_name,
                field_name=field_name,
                field_sound_index=index,
                original_filename=filename,
                source_path=source_path,
            )
        )
        sequence += 1
    return sequence


def _supported_sound_refs(field_html: str) -> tuple[SoundReference, ...]:
    return tuple(
        ref
        for ref in find_sound_references(field_html)
        if is_supported_audio_filename(ref.filename)
    )


def make_zip_entry_name(item: AudioExportItem, *, used_names: set[str]) -> str:
    stem = _safe_zip_fragment(Path(item.original_filename).stem) or "audio"
    suffix = Path(item.original_filename).suffix.lower()
    field_name = _safe_zip_fragment(item.field_name)
    base = (
        f"{item.sequence:04d}__note-{item.note_id}__"
        f"{field_name}__{item.field_sound_index:03d}__{stem}"
    )
    candidate = f"{base}{suffix}"
    counter = 2
    while candidate in used_names:
        candidate = f"{base}__{counter}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def _notice(
    note: BatchNoteSnapshot,
    field_name: str,
    message: str,
    filename: str | None = None,
) -> AudioExportNotice:
    return AudioExportNotice(
        note_id=note.note_id,
        notetype_name=note.notetype_name,
        field_name=field_name,
        message=message,
        filename=filename,
    )


def _safe_zip_fragment(value: str) -> str:
    sanitized = _UNSAFE_ENTRY_CHARS_RE.sub("_", value.strip()).strip("._")
    return sanitized or "field"
