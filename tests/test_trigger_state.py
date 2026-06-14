"""Tests for trigger sidecar state persistence and latest-wins guards."""

from __future__ import annotations

import json
from pathlib import Path

from anki_audio_quick_editor.trigger_state import (
    TriggerStateKey,
    TriggerStateStore,
    collection_state_path,
    is_latest,
    mark_failed,
    mark_running,
    mark_succeeded,
    should_schedule,
)


def _store(path: Path) -> TriggerStateStore:
    return TriggerStateStore.load(path)


def _key() -> TriggerStateKey:
    return TriggerStateKey(note_id=42, rule_id="trigger-clean", source_field="Audio")


def test_state_marks_changed_filename_unhandled(tmp_path: Path) -> None:
    store = _store(tmp_path / "state.json")
    key = _key()
    token = "first"

    mark_running(store, key, "voice-a.mp3", "fingerprint-a", token)
    mark_succeeded(store, key, token, "voice-a.mp3", "voice-a-clean.mp3")

    entry = store.get(key)
    assert should_schedule(entry, "voice-b.mp3", "fingerprint-a") is True


def test_state_marks_same_filename_and_fingerprint_handled(tmp_path: Path) -> None:
    store = _store(tmp_path / "state.json")
    key = _key()
    token = "first"

    mark_running(store, key, "voice-a.mp3", "fingerprint-a", token)
    mark_succeeded(store, key, token, "voice-a.mp3", "voice-a-clean.mp3")

    entry = store.get(key)
    assert should_schedule(entry, "voice-a.mp3", "fingerprint-a") is False


def test_state_marks_changed_fingerprint_unhandled(tmp_path: Path) -> None:
    store = _store(tmp_path / "state.json")
    key = _key()
    token = "first"

    mark_running(store, key, "voice-a.mp3", "fingerprint-a", token)
    mark_succeeded(store, key, token, "voice-a.mp3", "voice-a-clean.mp3")

    entry = store.get(key)
    assert should_schedule(entry, "voice-a.mp3", "fingerprint-b") is True


def test_state_generation_token_latest_wins(tmp_path: Path) -> None:
    store = _store(tmp_path / "state.json")
    key = _key()

    mark_running(store, key, "voice-a.mp3", "fingerprint-a", "older")
    mark_running(store, key, "voice-b.mp3", "fingerprint-a", "newer")
    mark_succeeded(store, key, "older", "voice-a.mp3", "voice-a-clean.mp3")

    entry = store.get(key)
    assert is_latest(entry, "newer") is True
    assert entry is not None
    assert entry.status == "running"
    assert entry.input_filename == "voice-b.mp3"
    assert entry.last_successful_output_filename is None


def test_state_persists_failure_summary(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    key = _key()
    store = _store(path)

    mark_running(store, key, "voice-a.mp3", "fingerprint-a", "first")
    mark_failed(store, key, "first", "ffmpeg failed")
    store.save()

    reloaded = TriggerStateStore.load(path)
    entry = reloaded.get(key)
    assert entry is not None
    assert entry.status == "failed"
    assert entry.last_error == "ffmpeg failed"
    assert should_schedule(entry, "voice-a.mp3", "fingerprint-a") is True


def test_collection_state_path_is_collection_scoped(tmp_path: Path) -> None:
    first = collection_state_path(tmp_path, "/collection/one.anki2")
    second = collection_state_path(tmp_path, "/collection/two.anki2")

    assert first != second
    assert first.parent == tmp_path / "aqe_artifacts" / "trigger_state"
    assert first.suffix == ".json"


def test_state_loads_corrupt_json_as_empty_store(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("{not json", encoding="utf-8")

    store = TriggerStateStore.load(path)

    assert store.entries == {}


def test_state_load_ignores_invalid_keys_and_entries(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    good_key = json.dumps([42, "trigger-clean", "Audio"], separators=(",", ":"))
    path.write_text(
        json.dumps(
            {
                "not-json": {"status": "succeeded"},
                json.dumps([True, "trigger-clean", "Audio"]): {"status": "succeeded"},
                json.dumps([43, "bad", "Audio"]): {"status": "unknown"},
                good_key: {
                    "last_handled_field_filename": "voice-a.mp3",
                    "input_filename": "voice-a.mp3",
                    "action_fingerprint": "fingerprint",
                    "generation_token": "first",
                    "status": "succeeded",
                    "last_successful_output_filename": "voice-a-clean.mp3",
                    "updated_at": "now",
                    "last_error": None,
                },
            }
        ),
        encoding="utf-8",
    )

    store = TriggerStateStore.load(path)

    assert list(store.entries) == [_key()]
