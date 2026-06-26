from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_export_planning import (
    collect_audio_export_items,
    default_audio_field_selections,
    make_zip_entry_name,
)
from anki_audio_quick_editor.audio_export_types import AudioExportFieldSelection
from anki_audio_quick_editor.batch_operation_types import BatchNoteSnapshot


def test_default_audio_field_selections_choose_fields_with_supported_sound_refs() -> None:
    notes = [
        BatchNoteSnapshot(1, "Basic", {"Front": "[sound:front.mp3]", "Back": "text"}),
        BatchNoteSnapshot(2, "Basic", {"Front": "text", "Back": "[sound:back.wav]"}),
        BatchNoteSnapshot(3, "Cloze", {"Text": "[sound:movie.mp4]", "Audio": "[sound:ok.m4a]"}),
    ]

    assert default_audio_field_selections(notes) == (
        AudioExportFieldSelection("Basic", ("Front", "Back")),
        AudioExportFieldSelection("Cloze", ("Audio",)),
    )


def test_collect_audio_export_items_includes_all_sound_refs_in_selected_order(
    tmp_path: Path,
) -> None:
    for filename in ("a.mp3", "b.wav", "c.m4a"):
        (tmp_path / filename).write_bytes(b"audio")
    notes = [
        BatchNoteSnapshot(
            10,
            "Basic",
            {"Front": "[sound:a.mp3] x [sound:b.wav]", "Back": "[sound:c.m4a]"},
        ),
    ]

    plan = collect_audio_export_items(
        notes,
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("Front", "Back")),),
    )

    assert [
        (
            item.sequence,
            item.note_id,
            item.field_name,
            item.field_sound_index,
            item.original_filename,
        )
        for item in plan.items
    ] == [
        (1, 10, "Front", 1, "a.mp3"),
        (2, 10, "Front", 2, "b.wav"),
        (3, 10, "Back", 1, "c.m4a"),
    ]
    assert plan.skipped == ()
    assert plan.failures == ()


def test_collect_audio_export_items_deduplicates_repeated_media_files(
    tmp_path: Path,
) -> None:
    for filename in ("vertrage.ogg", "other.mp3"):
        (tmp_path / filename).write_bytes(b"audio")
    notes = [
        BatchNoteSnapshot(
            10,
            "Basic",
            {"Front": "[sound:vertrage.ogg] [sound:vertrage.ogg]"},
        ),
        BatchNoteSnapshot(
            11,
            "Basic",
            {"Front": "[sound:vertrage.ogg] [sound:other.mp3]"},
        ),
    ]

    plan = collect_audio_export_items(
        notes,
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
    )

    assert [
        (
            item.sequence,
            item.note_id,
            item.field_sound_index,
            item.original_filename,
        )
        for item in plan.items
    ] == [
        (1, 10, 1, "vertrage.ogg"),
        (2, 11, 2, "other.mp3"),
    ]
    assert plan.skipped == ()
    assert plan.failures == ()


def test_collect_audio_export_items_reports_skips_and_missing_media(tmp_path: Path) -> None:
    notes = [
        BatchNoteSnapshot(10, "Basic", {"Front": "no audio", "Audio": "[sound:missing.mp3]"}),
        BatchNoteSnapshot(11, "Other", {"Audio": "[sound:ignored.mp3]"}),
    ]

    plan = collect_audio_export_items(
        notes,
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("Front", "Audio", "Missing")),),
    )

    assert plan.items == ()
    assert [entry.message for entry in plan.skipped] == [
        "field 'Front' has no supported sound reference",
        "missing selected field 'Missing'",
    ]
    assert len(plan.failures) == 1
    assert plan.failures[0].message == "media file not found: missing.mp3"


def test_make_zip_entry_name_is_ordered_sanitized_and_collision_safe(tmp_path: Path) -> None:
    (tmp_path / "bad name.mp3").write_bytes(b"audio")
    note = BatchNoteSnapshot(42, "Basic", {"A/B": "[sound:bad name.mp3]"})
    plan = collect_audio_export_items(
        [note],
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("A/B",)),),
    )
    item = plan.items[0]

    assert make_zip_entry_name(item, used_names=set()) == "0001__note-42__A_B__001__bad_name.mp3"
    assert make_zip_entry_name(item, used_names={"0001__note-42__A_B__001__bad_name.mp3"}) == (
        "0001__note-42__A_B__001__bad_name__2.mp3"
    )
    assert make_zip_entry_name(item, used_names=set(), forced_suffix=".mp3") == (
        "0001__note-42__A_B__001__bad_name.mp3"
    )
    assert make_zip_entry_name(
        item,
        used_names={"0001__note-42__A_B__001__bad_name.mp3"},
        forced_suffix="mp3",
    ) == "0001__note-42__A_B__001__bad_name__2.mp3"


def test_make_zip_entry_name_can_force_mp3_suffix_for_normalized_exports(tmp_path: Path) -> None:
    (tmp_path / "voice.ogg").write_bytes(b"audio")
    note = BatchNoteSnapshot(43, "Basic", {"Front": "[sound:voice.ogg]"})
    plan = collect_audio_export_items(
        [note],
        media_dir=tmp_path,
        field_selections=(AudioExportFieldSelection("Basic", ("Front",)),),
    )

    assert make_zip_entry_name(plan.items[0], used_names=set(), forced_suffix=".mp3") == (
        "0001__note-43__Front__001__voice.mp3"
    )
