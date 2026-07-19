"""Regression tests for trigger completion guards and handled outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anki_audio_quick_editor import trigger_executor
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operation_types import BatchNoteResult
from anki_audio_quick_editor.trigger_rules import (
    AudioTriggerRule,
    trigger_rules_from_raw,
)
from anki_audio_quick_editor.trigger_runner import (
    TriggerJob,
    run_trigger_job,
    schedule_trigger_event,
)
from anki_audio_quick_editor.trigger_state import (
    TriggerStateKey,
    TriggerStateStore,
    mark_running,
)
from tests.test_trigger_runner import _Col, _config, _Mw, _Note


def test_edit_transform_output_filename_is_handled_on_later_text_edits(
    tmp_path: Path,
    monkeypatch,
) -> None:
    note = _Note()
    mw = _Mw(_config(event="edit"), note, tmp_path)
    calls = 0

    def fake_process(*_args: object, **_kwargs: object) -> BatchNoteResult:
        nonlocal calls
        calls += 1
        return BatchNoteResult(
            note_id=10,
            status="written",
            message="converted",
            target_field="Audio",
            target_html="before [sound:clip.flac] after",
            audio_filename="clip.mp3",
            written_filename="clip.flac",
            original_target_html="before [sound:clip.mp3] after",
        )

    monkeypatch.setattr(trigger_executor, "process_trigger_operation", fake_process)

    assert schedule_trigger_event(mw, note, "edit") == 1
    assert schedule_trigger_event(mw, note, "edit") == 0
    assert calls == 1

    state_files = list((tmp_path / "addon" / "aqe_artifacts" / "trigger_state").glob("*.json"))
    entry = next(iter(TriggerStateStore.load(state_files[0]).entries.values()))
    assert entry.last_handled_field_filename == "clip.flac"


def test_run_trigger_job_rejects_generation_superseded_during_processing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rule, key, state_path, note, col, job = _running_job(tmp_path)

    def fake_process(*_args: object, **_kwargs: object) -> BatchNoteResult:
        newer = TriggerStateStore.load(state_path)
        mark_running(newer, key, "new-clip.mp3", "fingerprint", "newer")
        newer.save()
        return _written_transform_result()

    monkeypatch.setattr(trigger_executor, "process_trigger_operation", fake_process)

    execution = run_trigger_job(
        col,
        job,
        presets=(),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        artifact_root=None,
    )

    assert rule.id == "clean"
    assert execution.result.status == "skipped"
    assert execution.result.message == "stale trigger completion"
    assert note.fields["Audio"] == "before [sound:clip.mp3] after"
    assert col.update_calls == []


def test_run_graph_trigger_rejects_source_changed_during_processing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    raw_rule = {
        **_config(event="edit")["audio_trigger_rules"][0],
        "id": "graph",
        "operation": "graph",
        "target_field": "Graph",
    }
    rule, key, state_path, note, col, job = _running_job(tmp_path, raw_rule=raw_rule)
    note.fields["Graph"] = "old graph"

    def fake_process(*_args: object, **_kwargs: object) -> BatchNoteResult:
        note.fields["Audio"] = "before [sound:new-clip.mp3] after"
        return BatchNoteResult(
            note_id=10,
            status="written",
            message="graphed",
            target_field="Graph",
            target_html='<img src="clip.svg">',
            audio_filename="clip.mp3",
            image_filename="clip.svg",
            written_filename="clip.svg",
            original_target_html="old graph",
        )

    monkeypatch.setattr(trigger_executor, "process_trigger_operation", fake_process)

    execution = run_trigger_job(
        col,
        job,
        presets=(),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        artifact_root=None,
    )

    assert rule.id == "graph"
    assert key.rule_id == "graph"
    assert state_path.name == "state.json"
    assert execution.result.status == "skipped"
    assert note.fields["Graph"] == "old graph"
    assert col.update_calls == []


def _running_job(
    tmp_path: Path,
    *,
    raw_rule: Any = None,
) -> tuple[AudioTriggerRule, TriggerStateKey, Path, _Note, _Col, TriggerJob]:
    raw = raw_rule or _config()["audio_trigger_rules"][0]
    rule = trigger_rules_from_raw([raw])[0]
    key = TriggerStateKey(note_id=10, rule_id=rule.id, source_field="Audio")
    state_path = tmp_path / "state.json"
    store = TriggerStateStore.load(state_path)
    mark_running(store, key, "clip.mp3", "fingerprint", "current")
    store.save()
    note = _Note()
    col = _Col(note, tmp_path)
    (tmp_path / "clip.mp3").write_bytes(b"audio")
    job = TriggerJob(
        note_id=10,
        rule=rule,
        state_key=key,
        state_path=state_path,
        generation_token="current",
        input_filename="clip.mp3",
        action_fingerprint="fingerprint",
    )
    return rule, key, state_path, note, col, job


def _written_transform_result() -> BatchNoteResult:
    return BatchNoteResult(
        note_id=10,
        status="written",
        message="converted",
        target_field="Audio",
        target_html="before [sound:clip.flac] after",
        audio_filename="clip.mp3",
        written_filename="clip.flac",
        original_target_html="before [sound:clip.mp3] after",
    )
