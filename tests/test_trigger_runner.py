"""Tests for trigger scheduling and latest-wins execution."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operation_types import BatchNoteResult
from anki_audio_quick_editor.trigger_rules import trigger_rules_from_raw
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


class _Note:
    def __init__(self, note_id: int = 10) -> None:
        self.id = note_id
        self.fields = {"Audio": "before [sound:clip.mp3] after"}

    def items(self) -> list[tuple[str, str]]:
        return list(self.fields.items())

    def note_type(self) -> dict[str, object]:
        return {"id": 123, "name": "Basic"}

    def __getitem__(self, key: str) -> str:
        return self.fields[key]

    def __setitem__(self, key: str, value: str) -> None:
        self.fields[key] = value


class _Taskman:
    def run_in_background(self, task: Any, done: Any, *, uses_collection: bool) -> None:
        assert uses_collection is True
        result = task()
        done(SimpleNamespace(result=lambda: result))


class _Media:
    def __init__(self, path: Path) -> None:
        self._path = path

    def dir(self) -> str:
        return str(self._path)

    def write_data(self, desired_fname: str, data: bytes) -> str:
        del data
        return desired_fname


class _Col:
    path = "/collection/test.anki2"

    def __init__(self, note: _Note, media_dir: Path) -> None:
        self.note = note
        self.media = _Media(media_dir)
        self.update_calls: list[_Note] = []

    def get_note(self, note_id: int) -> _Note:
        assert note_id == self.note.id
        return self.note

    def update_note(self, note: _Note) -> object:
        self.update_calls.append(note)
        return {"note": note.id}


class _AddonManager:
    def __init__(self, config: dict[str, object], addon_dir: Path) -> None:
        self.config = config
        self.addon_dir = addon_dir

    def addonFromModule(self, _module: str) -> str:
        return "anki_audio_quick_editor"

    def getConfig(self, _addon_id: str) -> dict[str, object]:
        return self.config

    def addonsFolder(self, _addon_id: str) -> str:
        return str(self.addon_dir)


class _Mw:
    def __init__(self, config: dict[str, object], note: _Note, tmp_path: Path) -> None:
        self.col = _Col(note, tmp_path / "media")
        self.col.media._path.mkdir()
        (self.col.media._path / "clip.mp3").write_bytes(b"audio")
        self.addonManager = _AddonManager(config, tmp_path / "addon")
        self.taskman = _Taskman()
        self.undo_updates = 0

    def update_undo_actions(self) -> None:
        self.undo_updates += 1


def _config() -> dict[str, object]:
    return {
        "audio_processing_presets": [],
        "audio_trigger_rules": [
            {
                "id": "clean",
                "name": "Clean",
                "enabled": True,
                "event": "add",
                "note_type": {"id": 123, "name": "Basic"},
                "source_field": "Audio",
                "action_type": "operation",
                "operation": "convert",
                "preset_id": None,
                "target_field": None,
                "parameters": {"target_format": "flac"},
            }
        ],
    }


def test_schedule_trigger_event_runs_matching_rule_and_updates_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import aqt

    note = _Note()
    mw = _Mw(_config(), note, tmp_path)
    aqt.gui_hooks.operation_did_execute.reset_mock()

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_runner.process_trigger_operation",
        lambda *_args, **_kwargs: BatchNoteResult(
            note_id=10,
            status="written",
            message="converted",
            target_field="Audio",
            target_html="before [sound:clip.flac] after",
            audio_filename="clip.mp3",
            written_filename="clip.flac",
            original_target_html="before [sound:clip.mp3] after",
        ),
    )

    assert schedule_trigger_event(mw, note, "add") == 1

    assert note.fields["Audio"] == "before [sound:clip.flac] after"
    assert mw.col.update_calls == [note]
    aqt.gui_hooks.operation_did_execute.assert_called_once()
    state_files = list((tmp_path / "addon" / "aqe_artifacts" / "trigger_state").glob("*.json"))
    store = TriggerStateStore.load(state_files[0])
    entry = next(iter(store.entries.values()))
    assert entry.status == "succeeded"
    assert entry.last_handled_field_filename == "clip.mp3"
    assert entry.last_successful_output_filename == "clip.flac"


def test_schedule_trigger_event_skips_same_filename_and_fingerprint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    note = _Note()
    mw = _Mw(_config(), note, tmp_path)
    calls = 0

    def fake_process(*_args: object, **_kwargs: object) -> BatchNoteResult:
        nonlocal calls
        calls += 1
        return BatchNoteResult(
            note_id=10,
            status="skipped",
            message="already in FLAC format",
            audio_filename="clip.mp3",
        )

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_runner.process_trigger_operation",
        fake_process,
    )

    assert schedule_trigger_event(mw, note, "add") == 1
    assert schedule_trigger_event(mw, note, "add") == 0
    assert calls == 1


def test_run_trigger_job_ignores_stale_generation(tmp_path: Path, monkeypatch) -> None:
    raw_rule = _config()["audio_trigger_rules"]
    rule = trigger_rules_from_raw(raw_rule)[0]
    key = TriggerStateKey(note_id=10, rule_id="clean", source_field="Audio")
    state_path = tmp_path / "state.json"
    store = TriggerStateStore.load(state_path)
    mark_running(store, key, "clip.mp3", "fingerprint", "newer")
    store.save()
    note = _Note()
    col = _Col(note, tmp_path)
    (tmp_path / "clip.mp3").write_bytes(b"audio")

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_runner.process_trigger_operation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("stale job should not run")),
    )

    result = run_trigger_job(
        col,
        TriggerJob(
            note_id=10,
            rule=rule,
            state_key=key,
            state_path=state_path,
            generation_token="older",
            input_filename="clip.mp3",
            action_fingerprint="fingerprint",
        ),
        presets=(),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        artifact_root=None,
    )

    assert result.status == "skipped"
    assert result.message == "stale trigger completion"
    assert col.update_calls == []
