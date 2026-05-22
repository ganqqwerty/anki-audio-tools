"""Tests for import-safe batch visualization core behavior."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_operations import (
    OP_CONVERT,
    OP_FASTER,
    OP_GRAPH,
    OP_REMOVE_PAUSES,
    OP_VOLUME_DOWN,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import (
    BatchNoteSnapshot,
    BatchRunRequest,
    append_image_reference,
    field_groups_for_notes,
    first_audio_filename,
    process_note_batch_operation,
    unique_note_ids,
)
from anki_audio_quick_editor.batch_visualization import process_note_visualization
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack


def test_unique_note_ids_preserves_first_seen_order() -> None:
    assert unique_note_ids([3, 2, 3, 1, 2]) == [3, 2, 1]


def test_field_groups_preserve_fields_by_note_type() -> None:
    groups = field_groups_for_notes(
        [
            BatchNoteSnapshot(1, "Basic", {"Front": "", "Audio": ""}),
            BatchNoteSnapshot(2, "Basic", {"Back": "", "Audio": ""}),
            BatchNoteSnapshot(3, "Cloze", {"Text": "", "Audio": ""}),
        ]
    )

    assert groups[0].notetype_name == "Basic"
    assert groups[0].fields == ("Front", "Audio", "Back")
    assert groups[1].notetype_name == "Cloze"
    assert groups[1].fields == ("Text", "Audio")


def test_field_groups_sort_note_types_case_insensitively() -> None:
    groups = field_groups_for_notes(
        [
            BatchNoteSnapshot(1, "basic", {"Front": ""}),
            BatchNoteSnapshot(2, "Basic", {"Back": ""}),
        ]
    )

    assert [group.notetype_name for group in groups] == ["basic", "Basic"]


def test_append_image_reference_uses_new_line_media_tag() -> None:
    assert append_image_reference("existing", "viz.svg") == 'existing<br><img src="viz.svg">'
    assert append_image_reference("", "viz.svg") == '<img src="viz.svg">'


def test_append_image_reference_escapes_filename_for_html() -> None:
    assert append_image_reference("existing", 'viz"bad.svg') == 'existing<br><img src="viz&quot;bad.svg">'


def test_first_audio_filename_returns_sanitized_basename() -> None:
    note = BatchNoteSnapshot(10, "Basic", {"Audio": r"[sound:..\nested\clip.mp3]"})

    assert first_audio_filename(note, "Audio") == "clip.mp3"


def test_first_audio_filename_returns_none_for_missing_or_invalid_source() -> None:
    missing = BatchNoteSnapshot(10, "Basic", {"Image": ""})
    unsupported = BatchNoteSnapshot(11, "Basic", {"Audio": "[sound:movie.mp4]"})

    assert first_audio_filename(missing, "Audio") is None
    assert first_audio_filename(unsupported, "Audio") is None


def test_batch_run_request_requires_target_field_for_graph_only() -> None:
    graph = BatchRunRequest(operation=OP_GRAPH, source_field="Audio", target_field="Image")
    transform = BatchRunRequest(operation=OP_FASTER, source_field="Audio")
    convert = BatchRunRequest(operation=OP_CONVERT, source_field="Audio")

    assert graph.target_field == "Image"
    assert transform.target_field is None
    assert convert.target_field is None


def test_batch_run_request_rejects_missing_graph_target() -> None:
    try:
        BatchRunRequest(operation=OP_GRAPH, source_field="Audio")
    except ValueError as exc:
        assert str(exc) == "Choose a target field before starting."
    else:  # pragma: no cover - defensive
        raise AssertionError("expected missing target field to fail")


def test_process_note_visualization_appends_generated_media(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]", "Image": "old"})
    track = ProsodyTrack(
        duration_ms=100,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True), ProsodyPoint(100, 230.0, -19.0, 0.6, True)),
        pitch_min_hz=220.0,
        pitch_max_hz=230.0,
        source_filename="clip.mp3",
        analyzer_name="test",
    )
    writes: list[tuple[str, bytes]] = []
    analyzer_calls: list[tuple[Path, AudioProcessingConfig]] = []
    config = AudioProcessingConfig()

    def analyze(source_path: Path, call_config: AudioProcessingConfig) -> ProsodyTrack:
        analyzer_calls.append((source_path, call_config))
        return track

    monkeypatch.setattr("anki_audio_quick_editor.batch_operations.analyze_prosody_cached", analyze)

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_note_visualization(
        note,
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=media_writer,
        now_provider=lambda: datetime(2026, 5, 16, 1, 2, 3, 456000),
    )

    assert result.written
    assert result.note_id == 10
    assert result.message == "appended clip__aqe_viz_20260516_010203_456000.svg"
    assert result.target_field == "Image"
    assert result.audio_filename == "clip.mp3"
    assert result.image_filename == "clip__aqe_viz_20260516_010203_456000.svg"
    assert result.target_html == 'old<br><img src="clip__aqe_viz_20260516_010203_456000.svg">'
    assert analyzer_calls == [(source, config)]
    assert writes[0][0] == result.image_filename
    assert writes[0][1].startswith(b"<svg ")


def test_process_note_batch_operation_replaces_audio_reference_for_transform(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    artifact_root = tmp_path / "artifacts"
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "before [sound:clip.mp3] after"})
    render_calls: list[tuple[str, float]] = []
    writes: list[tuple[str, bytes]] = []

    def fake_render_audio(
        source_path,
        state,
        _config,
        output_path=None,
        on_command=None,
        artifact_root=None,
    ):
        del on_command
        assert output_path is not None
        assert artifact_root == tmp_path / "artifacts"
        output_path.write_bytes(b"rendered")
        render_calls.append((source_path.name, state.speed))

    monkeypatch.setattr("anki_audio_quick_editor.batch_operations.render_audio", fake_render_audio)

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(operation=OP_FASTER, source_field="Audio"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(speed_step=0.1),
        media_writer=media_writer,
        artifact_root=artifact_root,
    )

    assert result.written
    assert result.audio_filename == "clip.mp3"
    assert result.target_field == "Audio"
    assert result.image_filename is None
    assert result.written_filename is not None
    assert "[sound:clip.mp3]" not in result.target_html
    assert result.written_filename in result.target_html
    assert render_calls == [("clip.mp3", 1.1)]
    assert writes[0][1] == b"rendered"


def test_process_note_batch_operation_uses_speed_parameter_for_transform(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    speeds: list[float] = []

    def fake_render_audio(
        source_path,
        state,
        _config,
        output_path=None,
        on_command=None,
        artifact_root=None,
    ):
        del source_path, _config, on_command, artifact_root
        assert output_path is not None
        speeds.append(state.speed)
        output_path.write_bytes(b"rendered")

    monkeypatch.setattr("anki_audio_quick_editor.batch_operations.render_audio", fake_render_audio)

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_FASTER,
            source_field="Audio",
            parameters=AudioOperationParameters(speed_step=0.2),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(speed_step=0.05),
        media_writer=lambda name, data: name,
    )

    assert result.written
    assert speeds == [1.2]


def test_process_note_batch_operation_uses_pause_aggressiveness_parameter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    configs: list[AudioProcessingConfig] = []

    def fake_render_audio(
        source_path,
        state,
        config,
        output_path=None,
        on_command=None,
        artifact_root=None,
    ):
        del source_path, state, on_command, artifact_root
        assert output_path is not None
        configs.append(config)
        output_path.write_bytes(b"rendered")

    monkeypatch.setattr("anki_audio_quick_editor.batch_operations.render_audio", fake_render_audio)

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_REMOVE_PAUSES,
            source_field="Audio",
            parameters=AudioOperationParameters(pause_aggressiveness="gentle"),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(pause_aggressiveness="normal"),
        media_writer=lambda name, data: name,
    )

    assert result.written
    assert configs[0].pause_aggressiveness == "gentle"
    assert configs[0].internal_pause_threshold_ms == 450


def test_process_note_batch_operation_resolves_windows_case_variant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "Clip.MP3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    render_calls: list[Path] = []

    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Windows")

    def fake_render_audio(
        source_path,
        _state,
        _config,
        output_path=None,
        on_command=None,
        artifact_root=None,
    ):
        del on_command, artifact_root
        assert output_path is not None
        output_path.write_bytes(b"rendered")
        render_calls.append(source_path)

    monkeypatch.setattr("anki_audio_quick_editor.batch_operations.render_audio", fake_render_audio)

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(operation=OP_FASTER, source_field="Audio"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(speed_step=0.1),
        media_writer=lambda name, data: name,
    )

    assert result.written
    assert render_calls == [source]


def test_process_note_batch_operation_requires_exact_non_windows_case(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "Clip.MP3").write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Darwin")

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(operation=OP_FASTER, source_field="Audio"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(speed_step=0.1),
        media_writer=lambda name, data: name,
    )

    assert not result.written
    assert result.status == "failed"
    assert result.message == "media file not found: clip.mp3"


def test_process_note_visualization_skips_expected_missing_inputs(tmp_path: Path) -> None:
    writer = lambda name, data: name
    config = AudioProcessingConfig()

    missing_source = process_note_visualization(
        BatchNoteSnapshot(1, "Basic", {"Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )
    empty_source = process_note_visualization(
        BatchNoteSnapshot(2, "Basic", {"Audio": "", "Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )
    unsupported = process_note_visualization(
        BatchNoteSnapshot(3, "Basic", {"Audio": "[sound:movie.mp4]", "Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )
    missing_target = process_note_visualization(
        BatchNoteSnapshot(4, "Basic", {"Audio": "[sound:clip.mp3]"}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )

    assert missing_source.status == "skipped"
    assert missing_source.note_id == 1
    assert missing_source.message == "missing source field 'Audio'"
    assert empty_source.status == "skipped"
    assert empty_source.note_id == 2
    assert empty_source.message == "source field 'Audio' has no supported sound reference"
    assert unsupported.status == "skipped"
    assert unsupported.note_id == 3
    assert unsupported.message == "The first audio reference uses an unsupported format."
    assert missing_target.status == "skipped"
    assert missing_target.note_id == 4
    assert missing_target.message == "missing target field 'Image'"


def test_process_note_batch_operation_skips_missing_transform_source_field(tmp_path: Path) -> None:
    result = process_note_batch_operation(
        BatchNoteSnapshot(5, "Basic", {"Image": ""}),
        request=BatchRunRequest(operation=OP_VOLUME_DOWN, source_field="Audio"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )

    assert result.status == "skipped"
    assert result.message == "missing source field 'Audio'"


def test_process_note_visualization_counts_missing_media_as_failure(tmp_path: Path) -> None:
    result = process_note_visualization(
        BatchNoteSnapshot(1, "Basic", {"Audio": "[sound:missing.mp3]", "Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )

    assert result.failure
    assert result.note_id == 1
    assert result.audio_filename == "missing.mp3"
    assert result.message == "media file not found: missing.mp3"


def test_process_note_batch_operation_preserves_failure_payload_when_transform_render_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_audio",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AudioProcessingError("boom")),
    )

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(operation=OP_FASTER, source_field="Audio"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )

    assert result.note_id == 10
    assert result.status == "failed"
    assert result.message == "boom"
    assert result.target_field is None
    assert result.target_html is None
    assert result.audio_filename == "clip.mp3"
    assert result.written_filename is None


def test_process_note_visualization_preserves_failure_payload_when_generation_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]", "Image": "old"})

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.analyze_prosody_cached",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = process_note_visualization(
        note,
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )

    assert result.note_id == 10
    assert result.status == "failed"
    assert result.message == "boom"
    assert result.target_field is None
    assert result.target_html is None
    assert result.audio_filename == "clip.mp3"
    assert result.image_filename is None
