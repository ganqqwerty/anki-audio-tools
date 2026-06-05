"""Tests for lazy editor source metadata requests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from anki_audio_quick_editor.editor_source_metadata import request_source_metadata


class ImmediateThread:
    def __init__(self, target, daemon: bool = False):
        self._target = target
        self.daemon = daemon

    def start(self) -> None:
        self._target()


class EvalCollector:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, js: str) -> None:
        self.calls.append(js)


def _payload_from_eval(js: str) -> dict:
    prefix = (
        "window.__aqeReceiveSourceMetadataResponse && "
        "window.__aqeReceiveSourceMetadataResponse("
    )
    assert js.startswith(prefix)
    assert js.endswith(")")
    return json.loads(js[len(prefix) : -1])


def test_request_source_metadata_probes_requested_source_on_worker(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    evals = EvalCollector()
    request = {
        "requestId": "source-1",
        "fieldOrd": 0,
        "sourceFilename": "clip.mp3",
    }

    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))

    def eval_with_callback(_editor, expression, callback):
        assert "__aqePopPendingSourceMetadataRequest" in expression
        callback(request)

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=lambda _path, _config: SimpleNamespace(
            bit_rate=128000,
            sample_rate=44100,
            channels=2,
        ),
        resolve_requested_field_media=lambda _editor, _field_ord, _expected: (
            "clip.mp3",
            source,
        ),
        threading=SimpleNamespace(Thread=ImmediateThread),
    )

    request_source_metadata(editor, deps)

    payload = _payload_from_eval(evals.calls[-1])
    assert payload == {
        "requestId": "source-1",
        "ok": True,
        "metadata": {"bitRate": 128000, "sampleRate": 44100, "channels": 2},
    }


def test_request_source_metadata_resolves_editor_state_before_worker(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    evals = EvalCollector()
    request = {
        "requestId": "source-1",
        "fieldOrd": 0,
        "sourceFilename": "clip.mp3",
    }
    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))
    events: list[str] = []

    class TracingThread:
        def __init__(self, target, daemon: bool = False):
            events.append("thread-created")
            self._target = target
            self.daemon = daemon

        def start(self) -> None:
            events.append("thread-started")
            self._target()

    def eval_with_callback(_editor, _expression, callback):
        callback(request)

    def resolve_requested_field_media(_editor, _field_ord, _expected):
        events.append("resolved")
        return "clip.mp3", source

    def probe_audio_metadata(_path, _config):
        events.append("probed")
        return SimpleNamespace(bit_rate=128000, sample_rate=44100, channels=2)

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=probe_audio_metadata,
        resolve_requested_field_media=resolve_requested_field_media,
        threading=SimpleNamespace(Thread=TracingThread),
    )

    request_source_metadata(editor, deps)

    assert events == ["resolved", "thread-created", "thread-started", "probed"]


def test_request_source_metadata_reports_non_blocking_error(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    evals = EvalCollector()
    request = {
        "requestId": "source-1",
        "fieldOrd": 0,
        "sourceFilename": "clip.mp3",
    }
    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))

    def eval_with_callback(_editor, _expression, callback):
        callback(request)

    def fail_probe(_path, _config):
        raise RuntimeError("ffprobe unavailable")

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=fail_probe,
        resolve_requested_field_media=lambda _editor, _field_ord, _expected: (
            "clip.mp3",
            source,
        ),
        threading=SimpleNamespace(Thread=ImmediateThread),
    )

    request_source_metadata(editor, deps)

    payload = _payload_from_eval(evals.calls[-1])
    assert payload["requestId"] == "source-1"
    assert payload["ok"] is False
    assert payload["error"] == "Could not inspect source info."


def test_request_source_metadata_ignores_missing_pending_request() -> None:
    evals = EvalCollector()
    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))
    started = []

    def eval_with_callback(_editor, _expression, callback):
        callback(None)

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=lambda _path, _config: None,
        resolve_requested_field_media=lambda _editor, _field_ord, _expected: None,
        threading=SimpleNamespace(Thread=lambda *args, **kwargs: started.append((args, kwargs))),
    )

    request_source_metadata(editor, deps)

    assert evals.calls == []
    assert started == []


def test_request_source_metadata_rejects_stale_source_without_probe(tmp_path: Path) -> None:
    evals = EvalCollector()
    request = {
        "requestId": "source-1",
        "fieldOrd": 0,
        "sourceFilename": "old.mp3",
    }
    editor = SimpleNamespace(web=SimpleNamespace(eval=evals))
    probe_calls = []
    thread_calls = []

    def eval_with_callback(_editor, _expression, callback):
        callback(request)

    deps = SimpleNamespace(
        config=lambda _editor: {},
        eval_with_callback=eval_with_callback,
        main=lambda _editor, callback: callback(),
        probe_audio_metadata=lambda _path, _config: probe_calls.append(_path),
        resolve_requested_field_media=lambda _editor, _field_ord, _expected: None,
        threading=SimpleNamespace(Thread=lambda *args, **kwargs: thread_calls.append((args, kwargs))),
    )

    request_source_metadata(editor, deps)

    payload = _payload_from_eval(evals.calls[-1])
    assert payload["ok"] is False
    assert payload["error"] == "Could not inspect source info."
    assert probe_calls == []
    assert thread_calls == []
