# Race Condition Test Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic unit, integration, frontend, and e2e coverage that exposes stale async completions, duplicate batch starts, cache contention, and frontend bridge overwrite races before the race-condition mitigation work is trusted.

**Architecture:** The tests use barrier-controlled fakes instead of timing guesses. Unit and integration tests prove the guard contracts directly, while e2e tests run through real Anki editor/webview flows and release blocked workers only after the user-visible state has changed.

**Tech Stack:** Python 3.13, Pytest, Anki e2e fixtures, Qt event pumping, Svelte 5/TypeScript, Vitest, `python3 scripts/dev.py`, Superpowers execution workflow.

---

## Background

Race-condition mitigation is risky because the absence of crashes is not enough. A stale worker can finish after the editor has moved to a different note, after a field has changed, after a batch dialog has already started another run, or after a frontend request slot has been overwritten. If the mitigation is incomplete, the most likely failures are silent data corruption and confusing UI state rather than obvious exceptions.

The dangerous failures this plan is designed to catch are:

1. **Wrong note mutation:** note A starts an audio render, the user switches to note B, and note B receives note A's generated `[sound:...]` reference.
2. **Wrong field mutation:** a render started from field 0 completes after focus moved to field 1, replacing the wrong field.
3. **Orphaned generated media:** stale work is ignored at the UI layer, but the worker already wrote a generated media file that no note references.
4. **Stuck busy state:** stale completion is ignored but `session.processing` or the frontend busy flag remains true, leaving buttons disabled.
5. **Stale graph/status state:** graph or status text from an old source filename appears on the new note, making the next edit operate on misleading state.
6. **Batch duplicate execution:** two `batch.start` commands run concurrently in one dialog, interleaving progress, cancel behavior, logs, and undo entries.
7. **Batch stale overwrite:** a batch worker computes `target_html` from an old snapshot and later overwrites user edits made during the run.
8. **Cache contention:** two background jobs analyze the same prosody key at once and mutate shared cache state without a lock.
9. **Frontend request loss:** rapid graph, region-delete, or split-default requests overwrite a single pending slot before Python pops it.

The tests below intentionally create those interleavings. Most of them should fail on the pre-mitigation code and pass after the mitigation plan in `docs/superpowers/plans/2026-05-26-race-condition-mitigation.md` is implemented.

## File Structure

- Create `tests/race_test_helpers.py`: reusable barriers, immediate main-thread dispatchers, and fake media objects for deterministic race tests.
- Create `tests/test_editor_async_race_guards.py`: unit/integration tests for stale standard render, stale special transform, stale region operation, and generated-media write boundaries.
- Modify `tests/test_browser_integration.py`: add duplicate-start and stale-field-conflict batch integration coverage.
- Modify `tests/test_prosody_cache.py`: add concurrent cache access coverage that proves only one analysis runs for one cache key.
- Create `settings_ui/tests/editor-inline.bridge-queue-race.test.ts`: frontend bridge queue tests for graph, region-delete, split-default, and playback pending requests.
- Create `e2e/race_helpers.py`: e2e helpers for delayed renderers, Qt event pumping, generated-file assertions, and note-field diagnostics.
- Create `e2e/test_editor_async_race_workflow.py`: real editor e2e tests that reproduce stale render and stale region-delete completions.
- Create `e2e/test_browser_batch_race_workflow.py`: real batch dialog e2e tests for duplicate start and progress/log consistency.
- Modify `TESTING.md`: document the new race hardening commands and why they exist.

## Task 1: Add Shared Python Race Test Helpers

**Files:**
- Create: `tests/race_test_helpers.py`

- [ ] **Step 1: Create deterministic helper module**

Create `tests/race_test_helpers.py`:

```python
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import MagicMock


class TestEditor:
    """Weakref-able editor test double for the runtime session store."""


@dataclass
class BarrierCall:
    """A controllable call site for tests that need a worker to pause mid-operation."""

    started: threading.Event = field(default_factory=threading.Event)
    release: threading.Event = field(default_factory=threading.Event)
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = field(default_factory=list)

    def wait_started(self, timeout: float = 2.0) -> None:
        assert self.started.wait(timeout), "worker did not reach the race barrier"

    def allow_completion(self) -> None:
        self.release.set()

    def block_until_released(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((args, kwargs))
        self.started.set()
        assert self.release.wait(5.0), "test did not release the blocked worker"


class ImmediateThread:
    """Thread replacement that runs synchronously for unit tests."""

    def __init__(self, target: Callable[[], None], daemon: bool = False) -> None:
        self._target = target
        self.daemon = daemon

    def start(self) -> None:
        self._target()


class BackgroundThread:
    """Thread replacement that keeps a real thread but exposes it for joining."""

    started_threads: list[threading.Thread] = []

    def __init__(self, target: Callable[[], None], daemon: bool = False) -> None:
        self._thread = threading.Thread(target=target, daemon=daemon)
        self.started_threads.append(self._thread)

    def start(self) -> None:
        self._thread.start()


def reset_background_threads() -> None:
    BackgroundThread.started_threads.clear()


def join_background_threads(timeout: float = 2.0) -> None:
    for thread in list(BackgroundThread.started_threads):
        thread.join(timeout)
        assert not thread.is_alive(), "background race test worker did not finish"


def main_immediately(_owner: Any, callback: Callable[[], None]) -> None:
    callback()


def fake_media_manager(media_dir: Path) -> SimpleNamespace:
    def write_data(desired_name: str, data: bytes) -> str:
        (media_dir / desired_name).write_bytes(data)
        return desired_name

    return SimpleNamespace(
        dir=MagicMock(return_value=str(media_dir)),
        write_data=MagicMock(side_effect=write_data),
    )


def editor_with_media(media_dir: Path, field_html: str = "[sound:clip.mp3]") -> Any:
    editor = TestEditor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=[field_html])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=fake_media_manager(media_dir)),
    )
    return editor
```

- [ ] **Step 2: Run import check**

Run:

```bash
python3 -m compileall -q tests/race_test_helpers.py
```

Expected: PASS with `no tests ran`.

- [ ] **Step 3: Commit helper module**

Run:

```bash
git add tests/race_test_helpers.py
git commit -m "test: add race condition test helpers"
```

## Task 2: Add Editor Async Race Unit and Integration Tests

**Files:**
- Create: `tests/test_editor_async_race_guards.py`
- Uses: `tests/race_test_helpers.py`

- [ ] **Step 1: Write tests that pin stale editor completions**

Create `tests/test_editor_async_race_guards.py`:

```python
from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_processing import render_and_replace_async
from anki_audio_quick_editor.editor_region_delete import delete_selection_async
from anki_audio_quick_editor.editor_runtime import SESSIONS as _SESSIONS
from anki_audio_quick_editor.editor_special_transforms import run_special_audio_transform_async
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    RegionDeleteRequest,
    reset_for_note_load,
)
from tests.race_test_helpers import (
    BackgroundThread,
    BarrierCall,
    editor_with_media,
    join_background_threads,
    main_immediately,
    reset_background_threads,
)


@pytest.fixture(autouse=True)
def clear_sessions() -> None:
    _SESSIONS.clear()
    reset_background_threads()
    yield
    join_background_threads()
    _SESSIONS.clear()


def _standard_deps(tmp_path: Path, barrier: BarrierCall) -> SimpleNamespace:
    media_dir = tmp_path / "media"
    temp_dir = tmp_path / "tmp"
    media_dir.mkdir()
    temp_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

    def render_audio(
        source_path: Path,
        _state: AudioEditState,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        **_kwargs: object,
    ) -> None:
        barrier.block_until_released(source_path, output_path)
        shutil.copyfile(source_path, output_path)

    deps = SimpleNamespace()
    deps.sessions = _SESSIONS
    deps.threading = SimpleNamespace(Thread=BackgroundThread)
    deps.main = main_immediately
    deps.render_audio = render_audio
    deps.make_output_filename = lambda name: f"{Path(name).stem}__aqe_race.mp3"
    deps.temp_final_path = lambda desired_name: temp_dir / desired_name
    deps.write_generated_media = lambda editor, desired_name, output_path: editor.mw.col.media.write_data(
        desired_name,
        output_path.read_bytes(),
    )
    deps.replace_current_field_after_render = MagicMock()
    deps.render_failed = MagicMock()
    deps.stop_session_playback = MagicMock()
    deps.set_busy = MagicMock()
    deps.eval_playback_state = MagicMock()
    deps.format_ffmpeg_command = lambda command: " ".join(command)
    deps.artifact_root = lambda _editor: None
    return deps


def _region_deps(tmp_path: Path, barrier: BarrierCall) -> SimpleNamespace:
    temp_dir = tmp_path / "region-tmp"
    temp_dir.mkdir()

    def render_region(
        source_path: Path,
        _start_ms: int,
        _end_ms: int,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        **_kwargs: object,
    ) -> SimpleNamespace:
        barrier.block_until_released(source_path, output_path)
        shutil.copyfile(source_path, output_path)
        return SimpleNamespace(duration_ms=750)

    deps = SimpleNamespace()
    deps.sessions = _SESSIONS
    deps.threading = SimpleNamespace(Thread=BackgroundThread)
    deps.main = main_immediately
    deps.render_audio_region_deleted = render_region
    deps.render_audio_region_kept = render_region
    deps.make_output_filename = lambda name: f"{Path(name).stem}__aqe_region_race.mp3"
    deps.temp_final_path = lambda desired_name: temp_dir / desired_name
    deps.replace_current_field_after_region_delete = MagicMock()
    deps.render_failed = MagicMock()
    deps.stop_session_playback = MagicMock()
    deps.set_busy_for_field = MagicMock()
    deps.eval_playback_state = MagicMock()
    deps.format_ffmpeg_command = lambda command: " ".join(command)
    return deps


def _special_deps(tmp_path: Path, session: EditorSession, source: Path) -> SimpleNamespace:
    temp_dir = tmp_path / "special-tmp"
    temp_dir.mkdir()
    deps = SimpleNamespace()
    deps.sessions = _SESSIONS
    deps.threading = SimpleNamespace(Thread=BackgroundThread)
    deps.main = main_immediately
    deps.current_media_path = lambda _editor: (session, source)
    deps.config = lambda _editor: {}
    deps.make_output_filename = lambda name, **_kwargs: f"{Path(name).stem}__aqe_special_race.mp3"
    deps.temp_final_path = lambda desired_name: temp_dir / desired_name
    deps.write_generated_media = lambda editor, desired_name, output_path: editor.mw.col.media.write_data(
        desired_name,
        output_path.read_bytes(),
    )
    deps.replace_current_field_after_noise_removal = MagicMock()
    deps.render_failed = MagicMock()
    deps.log_special_transform_failure = MagicMock()
    deps.stop_session_playback = MagicMock()
    deps.set_busy = MagicMock()
    deps.eval_status = MagicMock()
    deps.still_processing_message = "Still processing"
    deps.eval_playback_state = MagicMock()
    deps.format_ffmpeg_command = lambda command: " ".join(command)
    return deps


def test_standard_render_completion_does_not_replace_after_note_change(tmp_path: Path) -> None:
    barrier = BarrierCall()
    deps = _standard_deps(tmp_path, barrier)
    editor = editor_with_media(tmp_path / "media")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=10,
    )
    _SESSIONS[editor] = session

    render_and_replace_async(
        editor,
        session,
        tmp_path / "media" / "clip.mp3",
        AudioEditState("clip.mp3", speed=1.25),
        AudioProcessingConfig(),
        deps,
    )
    barrier.wait_started()

    reset_for_note_load(session, note_id=11)
    editor.note.fields[0] = "[sound:other.mp3]"
    barrier.allow_completion()
    join_background_threads()

    deps.replace_current_field_after_render.assert_not_called()
    assert editor.note.fields[0] == "[sound:other.mp3]"
    assert not list((tmp_path / "media").glob("*__aqe_race.mp3"))
    assert session.processing is False


def test_standard_render_failure_does_not_reset_new_note_busy_state(tmp_path: Path) -> None:
    barrier = BarrierCall()
    deps = _standard_deps(tmp_path, barrier)
    editor = editor_with_media(tmp_path / "media")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=10,
    )
    _SESSIONS[editor] = session

    def failing_render(*args: object, **kwargs: object) -> None:
        barrier.block_until_released(args, kwargs)
        raise RuntimeError("controlled render failure")

    deps.render_audio = failing_render
    render_and_replace_async(
        editor,
        session,
        tmp_path / "media" / "clip.mp3",
        AudioEditState("clip.mp3", speed=1.25),
        AudioProcessingConfig(),
        deps,
    )
    barrier.wait_started()

    reset_for_note_load(session, note_id=12)
    barrier.allow_completion()
    join_background_threads()

    deps.render_failed.assert_not_called()
    assert session.processing is False


def test_special_transform_completion_does_not_replace_after_note_change(tmp_path: Path) -> None:
    barrier = BarrierCall()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    editor = editor_with_media(media_dir)
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=20,
    )
    _SESSIONS[editor] = session
    deps = _special_deps(tmp_path, session, source)

    def renderer(
        source_path: Path,
        _config: AudioProcessingConfig,
        *,
        output_path: Path,
        **_kwargs: object,
    ) -> None:
        barrier.block_until_released(source_path, output_path)
        shutil.copyfile(source_path, output_path)

    run_special_audio_transform_async(
        editor,
        label="Denoising",
        failure_log_label="denoise failed",
        renderer=renderer,
        deps=deps,
    )
    barrier.wait_started()

    reset_for_note_load(session, note_id=21)
    editor.note.fields[0] = "[sound:other.mp3]"
    barrier.allow_completion()
    join_background_threads()

    deps.replace_current_field_after_noise_removal.assert_not_called()
    assert editor.note.fields[0] == "[sound:other.mp3]"
    assert not list(media_dir.glob("*__aqe_special_race.mp3"))
    assert session.processing is False


def test_region_delete_completion_does_not_replace_after_field_change(tmp_path: Path) -> None:
    barrier = BarrierCall()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    editor = editor_with_media(media_dir, "[sound:clip.mp3]")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        note_id=20,
    )
    _SESSIONS[editor] = session
    deps = _region_deps(tmp_path, barrier)
    request = RegionDeleteRequest(
        field_index=0,
        source_filename="clip.mp3",
        selection_start_ms=100,
        selection_end_ms=250,
        cursor_ms=100,
        duration_ms=1000,
        trigger="button",
        playback_active=False,
    )

    delete_selection_async(
        editor,
        session,
        source,
        request,
        AudioProcessingConfig(),
        deps,
    )
    barrier.wait_started()

    session.field_index = 1
    editor.note.fields.append("[sound:other.mp3]")
    barrier.allow_completion()
    join_background_threads()

    deps.replace_current_field_after_region_delete.assert_not_called()
    assert editor.note.fields == ["[sound:clip.mp3]", "[sound:other.mp3]"]
    assert not list(media_dir.glob("*__aqe_*.mp3"))
    assert session.processing is False
```

- [ ] **Step 2: Run tests and capture expected failures**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_async_race_guards.py
```

Expected before mitigation: FAIL on at least the stale standard render assertion because current code writes generated media before `replace_current_field_after_render()` is guarded. Expected after mitigation: PASS.

- [ ] **Step 3: Keep the assertions diagnostic**

If the failure output does not show which field or generated files changed, update the assertions to include explicit messages:

```python
assert editor.note.fields[0] == "[sound:other.mp3]", editor.note.fields
assert not list((tmp_path / "media").glob("*__aqe_race.mp3")), sorted(
    path.name for path in (tmp_path / "media").glob("*")
)
```

- [ ] **Step 4: Re-run focused editor race tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_async_race_guards.py
```

Expected after mitigation: PASS.

- [ ] **Step 5: Commit editor hardening tests**

Run:

```bash
git add tests/test_editor_async_race_guards.py
git commit -m "test: cover stale editor async completions"
```

## Task 3: Add Browser Batch Race Integration Tests

**Files:**
- Modify: `tests/test_browser_integration.py`

- [ ] **Step 1: Add duplicate-start coverage**

Append this test to `tests/test_browser_integration.py`:

```python
def test_batch_dialog_ignores_duplicate_start_while_running() -> None:
    from anki_audio_quick_editor.audio_state import AudioProcessingConfig
    from anki_audio_quick_editor.browser_dialog import BatchOperationsDialog
    from anki_audio_quick_editor.batch_operations import FieldGroup
    from anki_audio_quick_editor.webview_bridge import WebviewBridgeCommand

    started: list[tuple[object, object, list[int], object]] = []

    def fake_run_batch(browser, dialog, note_ids, request):
        started.append((browser, dialog, list(note_ids), request))

    browser = SimpleNamespace(mw=SimpleNamespace())
    dialog = BatchOperationsDialog(
        browser,
        note_ids=[101, 102],
        groups=(FieldGroup("Basic", ("Front", "Back")),),
        config=AudioProcessingConfig(),
        run_batch_in_background=fake_run_batch,
    )
    payload = {
        "operation": "faster",
        "source_field": "Front",
        "target_field": "Front",
        "parameters": {"speed_step": 0.1},
    }
    command = WebviewBridgeCommand("batch.start", payload=payload)

    assert dialog._handle_batch_start(command)
    assert dialog._handle_batch_start(command)

    assert len(started) == 1
    assert dialog._running is True
```

- [ ] **Step 2: Add stale target-field conflict coverage**

Append this test to `tests/test_browser_integration.py`:

```python
def test_apply_result_reports_conflict_when_target_field_changed() -> None:
    from anki_audio_quick_editor.batch_operations import BatchNoteResult
    from anki_audio_quick_editor.browser_integration import BatchRunReport, _apply_result

    class Note(dict):
        id = 55

    note = Note(Front="[sound:old.mp3] user edit")
    col = SimpleNamespace(
        get_note=MagicMock(return_value=note),
        update_note=MagicMock(),
    )
    report = BatchRunReport(total=1)
    result = BatchNoteResult(
        note_id=55,
        status="written",
        message="processed",
        target_field="Front",
        target_html="[sound:new.mp3]",
        original_target_html="[sound:old.mp3]",
        audio_filename="old.mp3",
        written_filename="new.mp3",
    )

    applied = _apply_result(col, report, result, fallback_field="Front")

    assert applied.status == "failed"
    assert "changed during batch processing" in applied.message
    assert note["Front"] == "[sound:old.mp3] user edit"
    col.update_note.assert_not_called()
    assert report.failures == 1
    assert report.written == 0
```

- [ ] **Step 3: Run browser integration race tests**

Run:

```bash
python3 scripts/dev.py test tests/test_browser_integration.py
```

Expected before mitigation: FAIL for duplicate start if the second run is started, and FAIL for field conflict because `BatchNoteResult` does not yet carry or check `original_target_html`. Expected after mitigation: PASS.

- [ ] **Step 4: Commit batch integration tests**

Run:

```bash
git add tests/test_browser_integration.py
git commit -m "test: cover browser batch race conditions"
```

## Task 4: Add Prosody Cache Contention Test

**Files:**
- Modify: `tests/test_prosody_cache.py`

- [ ] **Step 1: Add concurrent same-key test**

Append this test to `tests/test_prosody_cache.py`:

```python
def test_analyze_prosody_cached_serializes_same_key_analysis(tmp_path: Path, monkeypatch) -> None:
    import threading

    from anki_audio_quick_editor import prosody_cache
    from anki_audio_quick_editor.audio_state import AudioProcessingConfig
    from anki_audio_quick_editor.prosody_cache import analyze_prosody_cached
    from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack

    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"audio")
    first_miss = threading.Event()
    allow_first_miss_return = threading.Event()
    second_miss = threading.Event()
    call_lock = threading.Lock()
    calls = 0

    class RaceCache(dict):
        misses = 0

        def get(self, key, default=None):
            if key in self:
                return super().get(key, default)
            self.misses += 1
            if self.misses == 1:
                first_miss.set()
                assert allow_first_miss_return.wait(3.0)
            elif self.misses == 2:
                second_miss.set()
            return default

    def fake_analyze_prosody(path: Path, _config: AudioProcessingConfig) -> ProsodyTrack:
        nonlocal calls
        with call_lock:
            calls += 1
        return ProsodyTrack(
            duration_ms=1000,
            points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
            pitch_min_hz=220.0,
            pitch_max_hz=220.0,
            source_filename=path.name,
            analyzer_name="race-test",
        )

    race_cache = RaceCache()
    monkeypatch.setattr(prosody_cache, "_ANALYSIS_CACHE", race_cache)
    monkeypatch.setattr(prosody_cache, "analyze_prosody", fake_analyze_prosody)

    results: list[object] = []

    def worker() -> None:
        results.append(analyze_prosody_cached(audio, AudioProcessingConfig()))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    assert first_miss.wait(2)
    second_miss.wait(0.2)
    allow_first_miss_return.set()
    for thread in threads:
        thread.join(timeout=3)
        assert not thread.is_alive()

    assert len(results) == 2
    assert results[0] == results[1]
    assert calls == 1
```

- [ ] **Step 2: Run prosody cache test**

Run:

```bash
python3 scripts/dev.py test tests/test_prosody_cache.py::test_analyze_prosody_cached_serializes_same_key_analysis
```

Expected before mitigation: FAIL with `calls == 2` or a barrier timeout, depending on scheduling. Expected after mitigation: PASS.

- [ ] **Step 3: Commit prosody race test**

Run:

```bash
git add tests/test_prosody_cache.py
git commit -m "test: cover concurrent prosody cache access"
```

## Task 5: Add Frontend Bridge Queue Race Tests

**Files:**
- Create: `settings_ui/tests/editor-inline.bridge-queue-race.test.ts`

- [ ] **Step 1: Write FIFO pending-request tests**

Create `settings_ui/tests/editor-inline.bridge-queue-race.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  popPendingGraphAnalysisRequest,
  popPendingPlaybackRequest,
  popPendingRegionDeleteRequest,
  popPendingSplitDefaultSaveRequest,
  sendGraphAnalysisRequest,
  sendSplitDefaultSaveRequest,
  setPendingPlaybackRequest,
  setPendingRegionDeleteRequest,
} from "../src/editor-inline/bridge.js";
import type {
  GraphAnalysisRequest,
  PlaybackRequest,
  RegionDeleteRequest,
} from "../src/editor-inline/types.js";
import type { SplitDefaultSaveRequest } from "../src/editor-inline/split-default-save-types.js";

afterEach(() => {
  vi.restoreAllMocks();
  while (popPendingGraphAnalysisRequest()) {}
  while (popPendingRegionDeleteRequest()) {}
  while (popPendingSplitDefaultSaveRequest()) {}
  while (popPendingPlaybackRequest()) {}
});

describe("editor bridge pending request queues", () => {
  it("keeps graph analysis requests in FIFO order", () => {
    const pycmd = vi.fn();
    globalThis.pycmd = pycmd;
    const first: GraphAnalysisRequest = { ord: 0, filename: "a.mp3" };
    const second: GraphAnalysisRequest = { ord: 1, filename: "b.mp3" };

    sendGraphAnalysisRequest(first);
    sendGraphAnalysisRequest(second);

    expect(pycmd).toHaveBeenCalledTimes(2);
    expect(popPendingGraphAnalysisRequest()).toEqual(first);
    expect(popPendingGraphAnalysisRequest()).toEqual(second);
    expect(popPendingGraphAnalysisRequest()).toBeNull();
  });

  it("keeps region delete requests in FIFO order", () => {
    const first: RegionDeleteRequest = { ord: 0, filename: "a.mp3", startMs: 100, endMs: 200 };
    const second: RegionDeleteRequest = { ord: 0, filename: "a.mp3", startMs: 300, endMs: 400 };

    setPendingRegionDeleteRequest(first);
    setPendingRegionDeleteRequest(second);

    expect(popPendingRegionDeleteRequest()).toEqual(first);
    expect(popPendingRegionDeleteRequest()).toEqual(second);
    expect(popPendingRegionDeleteRequest()).toBeNull();
  });

  it("keeps split default save requests in FIFO order", () => {
    const pycmd = vi.fn();
    globalThis.pycmd = pycmd;
    const first: SplitDefaultSaveRequest = { command: "aqe:faster", value: 0.1 };
    const second: SplitDefaultSaveRequest = { command: "aqe:slower", value: 0.2 };

    sendSplitDefaultSaveRequest(first);
    sendSplitDefaultSaveRequest(second);

    expect(pycmd).toHaveBeenCalledTimes(2);
    expect(popPendingSplitDefaultSaveRequest()).toEqual(first);
    expect(popPendingSplitDefaultSaveRequest()).toEqual(second);
    expect(popPendingSplitDefaultSaveRequest()).toBeNull();
  });

  it("keeps playback requests in FIFO order while preserving the last request", () => {
    const first: PlaybackRequest = { ord: 0, filename: "a.mp3", startMs: 0, endMs: null };
    const second: PlaybackRequest = { ord: 0, filename: "a.mp3", startMs: 500, endMs: 900 };

    setPendingPlaybackRequest(first);
    setPendingPlaybackRequest(second);

    expect(window.__aqeLastPlaybackRequest).toEqual(second);
    expect(popPendingPlaybackRequest()).toEqual(first);
    expect(popPendingPlaybackRequest()).toEqual(second);
    expect(popPendingPlaybackRequest()).toBeNull();
  });
});
```

- [ ] **Step 2: Run frontend race tests**

Run:

```bash
cd settings_ui && npm test -- editor-inline.bridge-queue-race.test.ts --run
```

Expected before mitigation: FAIL because the second request overwrites the first in the single-slot pending variables. Expected after mitigation: PASS.

- [ ] **Step 3: Commit frontend bridge race tests**

Run:

```bash
git add settings_ui/tests/editor-inline.bridge-queue-race.test.ts
git commit -m "test: cover editor bridge request queue races"
```

## Task 6: Add E2E Race Helpers

**Files:**
- Create: `e2e/race_helpers.py`

- [ ] **Step 1: Create e2e helper module**

Create `e2e/race_helpers.py`:

```python
from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path
from typing import Any

from aqt.qt import QApplication

from .conftest import import_runtime_addon_module


class DelayedRenderer:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls: list[dict[str, Any]] = []

    def wait_started(self, timeout: float = 5.0) -> None:
        assert self.started.wait(timeout), "renderer did not start"

    def allow_completion(self) -> None:
        self.release.set()

    def render_audio(
        self,
        source_path: Path,
        state: Any,
        config: Any,
        *,
        output_path: Path,
        **kwargs: Any,
    ) -> Any:
        audio_types = import_runtime_addon_module(".audio_types")
        AudioProcessingResult = audio_types.AudioProcessingResult
        self.calls.append({"source_path": source_path, "state": state, "config": config, "output_path": output_path})
        self.started.set()
        assert self.release.wait(10.0), "renderer was not released"
        shutil.copyfile(source_path, output_path)
        return AudioProcessingResult(
            output_path=output_path,
            command=("delayed-render", str(source_path)),
            duration_ms=1000,
        )

    def render_region(self, source_path: Path, *args: Any, output_path: Path, **kwargs: Any) -> Any:
        audio_types = import_runtime_addon_module(".audio_types")
        AudioProcessingResult = audio_types.AudioProcessingResult
        self.calls.append({"source_path": source_path, "output_path": output_path, "args": args, "kwargs": kwargs})
        self.started.set()
        assert self.release.wait(10.0), "region renderer was not released"
        shutil.copyfile(source_path, output_path)
        return AudioProcessingResult(
            output_path=output_path,
            command=("delayed-region-render", str(source_path)),
            duration_ms=1000,
        )


def pump_events_for(seconds: float) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)


def generated_aqe_files(media_dir: Path) -> list[str]:
    return sorted(path.name for path in media_dir.glob("*__aqe_*.mp3"))


def assert_note_field(note: Any, field_index: int, expected_html: str) -> None:
    actual = note.fields[field_index]
    assert actual == expected_html, f"field {field_index} expected {expected_html!r}, got {actual!r}"
```

- [ ] **Step 2: Run helper import check through e2e runner**

Run:

```bash
python3 -m compileall -q e2e/race_helpers.py
```

Expected: PASS with `no tests ran`.

- [ ] **Step 3: Commit e2e helpers**

Run:

```bash
git add e2e/race_helpers.py
git commit -m "test: add e2e race workflow helpers"
```

## Task 7: Add Editor E2E Race Reproduction Tests

**Files:**
- Create: `e2e/test_editor_async_race_workflow.py`
- Uses: `e2e/race_helpers.py`

- [ ] **Step 1: Write stale standard render e2e**

Create `e2e/test_editor_async_race_workflow.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import runtime_addon_import_path
from .editor_graph_helpers import _graph_state_js, _wait_for_visualizer_track
from .editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _open_editor,
    _sound_filename,
    _three_audio_field_note,
)
from .editor_region_loop_helpers import _shift_drag_region
from .helpers import click_selector, generate_tone, wait_for_js_condition, wait_for_selector
from .race_helpers import DelayedRenderer, assert_note_field, generated_aqe_files, pump_events_for


def test_stale_standard_render_does_not_mutate_new_note_or_write_media(
    anki_mw,
    ffmpeg_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    before_generated = set(generated_aqe_files(media_dir))
    first_audio = media_dir / "aqe_race_first.wav"
    second_audio = media_dir / "aqe_race_second.wav"
    generate_tone(ffmpeg_config, first_audio, duration_s=0.35)
    generate_tone(ffmpeg_config, second_audio, duration_s=0.35)
    note_a = _basic_audio_note(anki_mw, first_audio.name)
    note_b = _basic_audio_note(anki_mw, second_audio.name)
    editor, parent = _open_editor(anki_mw, note_a)

    delayed = DelayedRenderer()
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"))
        monkeypatch.setattr(
            runtime_addon_import_path(".editor_dependencies", "render_audio"),
            delayed.render_audio,
        )

        click_selector(editor.web, _button_selector("aqe:faster"))
        delayed.wait_started()
        editor.set_note(note_b, hide=False, focusTo=0)
        wait_for_selector(editor.web, _button_selector("aqe:faster"))
        delayed.allow_completion()
        pump_events_for(1.0)

        assert _sound_filename(note_a.fields[0]) == first_audio.name
        assert _sound_filename(note_b.fields[0]) == second_audio.name
        assert set(generated_aqe_files(media_dir)) == before_generated
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 2: Add stale region-delete e2e**

Append this test to `e2e/test_editor_async_race_workflow.py`:

```python
def test_stale_region_delete_does_not_mutate_new_field_or_write_media(
    anki_mw,
    ffmpeg_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    before_generated = set(generated_aqe_files(media_dir))
    first_audio = media_dir / "aqe_region_race_first.wav"
    second_audio = media_dir / "aqe_region_race_second.wav"
    third_audio = media_dir / "aqe_region_race_third.wav"
    generate_tone(ffmpeg_config, first_audio, duration_s=0.9)
    generate_tone(ffmpeg_config, second_audio, duration_s=0.9)
    generate_tone(ffmpeg_config, third_audio, duration_s=0.9)
    note = _three_audio_field_note(anki_mw, (first_audio.name, second_audio.name, third_audio.name))
    original_fields = list(note.fields)
    editor, parent = _open_editor(anki_mw, note)

    delayed = DelayedRenderer()
    try:
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == first_audio.name, ord_=0)
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == second_audio.name, ord_=1)
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == third_audio.name, ord_=2)
        _shift_drag_region(editor, 0.2, 0.5, ord_=0)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(0),
            lambda state: state is not None and state["selectionActive"] is True,
            timeout=5.0,
        )
        monkeypatch.setattr(
            runtime_addon_import_path(".editor_dependencies", "render_audio_region_deleted"),
            delayed.render_region,
        )

        click_selector(editor.web, _button_selector("aqe:delete-selection", ord_=0))
        delayed.wait_started()
        editor.currentField = 1
        delayed.allow_completion()
        pump_events_for(1.0)

        assert list(note.fields) == original_fields
        assert_note_field(note, 1, original_fields[1])
        assert set(generated_aqe_files(media_dir)) == before_generated
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 3: Run editor race e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_async_race_workflow.py
```

Expected before mitigation: at least one test FAILS by observing a generated `__aqe_` file, a changed note field, or stale UI state. Expected after mitigation: PASS.

- [ ] **Step 4: Add busy-state assertion if the stale worker is ignored**

If the tests pass while the UI remains disabled, add this assertion after `pump_events_for(1.0)`:

```python
state = wait_for_js_condition(
    editor.web,
    """
    (() => {
      const button = document.querySelector('[data-aqe-command="aqe:faster"]');
      return { disabled: Boolean(button?.disabled), text: document.body.innerText };
    })()
    """,
    lambda value: value is not None,
)
assert state["disabled"] is False, state
```

- [ ] **Step 5: Re-run editor race e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_async_race_workflow.py
```

Expected after mitigation: PASS.

- [ ] **Step 6: Commit editor e2e race tests**

Run:

```bash
git add e2e/test_editor_async_race_workflow.py
git commit -m "test: reproduce stale editor render races in e2e"
```

## Task 8: Add Browser Batch E2E Race Workflow Tests

**Files:**
- Create: `e2e/test_browser_batch_race_workflow.py`

- [ ] **Step 1: Write direct dialog duplicate-start e2e**

Create `e2e/test_browser_batch_race_workflow.py`:

```python
from __future__ import annotations

import json

import pytest

from .conftest import import_runtime_addon_module
from .helpers import run_js, wait_for_condition


def test_batch_dialog_duplicate_start_does_not_launch_second_run(anki_mw) -> None:
    audio_state = import_runtime_addon_module(".audio_state")
    batch_operations = import_runtime_addon_module(".batch_operations")
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    BatchOperationsDialog = browser_dialog.BatchOperationsDialog

    started: list[dict[str, object]] = []

    def fake_run_batch(browser, dialog, note_ids, request):
        started.append({"browser": browser, "dialog": dialog, "note_ids": list(note_ids), "request": request})

    dialog = BatchOperationsDialog(
        anki_mw,
        [1, 2],
        (batch_operations.FieldGroup("Basic", ("Front", "Back")),),
        audio_state.AudioProcessingConfig(),
        fake_run_batch,
    )
    payload = {
        "operation": "faster",
        "source_field": "Front",
        "target_field": "Front",
        "parameters": {"speed_step": 0.1},
    }
    command = "bridge:" + json.dumps({"command": "batch.start", "payload": payload})

    dialog._dialog.show()
    try:
        run_js(dialog._webview, f"pycmd({command!r}); pycmd({command!r});")
        wait_for_condition(lambda: len(started) >= 1, timeout=2.0)

        assert len(started) == 1
        assert dialog._running is True
    finally:
        dialog._dialog.close()
```

- [ ] **Step 2: Add progress/log consistency assertion**

Append this test to `e2e/test_browser_batch_race_workflow.py`:

```python
def test_batch_dialog_duplicate_start_keeps_single_progress_stream(anki_mw, monkeypatch: pytest.MonkeyPatch) -> None:
    audio_state = import_runtime_addon_module(".audio_state")
    batch_operations = import_runtime_addon_module(".batch_operations")
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    BatchOperationsDialog = browser_dialog.BatchOperationsDialog
    emitted: list[tuple[str, object]] = []

    def fake_emit(self, name, payload=None):
        emitted.append((name, payload))

    def fake_run_batch(browser, dialog, note_ids, request):
        dialog.append_log("first run")

    monkeypatch.setattr(browser_dialog.BatchOperationsDialog, "_emit", fake_emit)

    dialog = BatchOperationsDialog(
        anki_mw,
        [1, 2, 3],
        (batch_operations.FieldGroup("Basic", ("Front", "Back")),),
        audio_state.AudioProcessingConfig(),
        fake_run_batch,
    )
    payload = {
        "operation": "volume_up",
        "source_field": "Front",
        "target_field": "Front",
        "parameters": {"volume_step_db": 3.0},
    }
    command = "bridge:" + json.dumps({"command": "batch.start", "payload": payload})

    dialog._dialog.show()
    try:
        run_js(dialog._webview, f"pycmd({command!r}); pycmd({command!r});")
        wait_for_condition(lambda: any(name == "onBatchProgress" for name, _payload in emitted), timeout=2.0)

        progress_events = [payload for name, payload in emitted if name == "onBatchProgress"]
        assert len(progress_events) == 1
        assert dialog._log_lines == ["first run"]
    finally:
        dialog._dialog.close()
```

- [ ] **Step 3: Run batch race e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_browser_batch_race_workflow.py
```

Expected before mitigation: FAIL because the dialog can launch two runs or emit duplicate start progress. Expected after mitigation: PASS.

- [ ] **Step 4: Commit batch e2e race tests**

Run:

```bash
git add e2e/test_browser_batch_race_workflow.py
git commit -m "test: cover duplicate batch starts in e2e"
```

## Task 9: Add Testing Documentation for Race Hardening

**Files:**
- Modify: `TESTING.md`

- [ ] **Step 1: Add race hardening section**

Add this section to `TESTING.md` near the e2e testing guidance:

````markdown
## Race Condition Hardening Tests

Race-sensitive workflows use targeted tests with barrier-controlled fake workers. These tests should be run before and after changing editor async processing, Browser batch execution, prosody analysis caching, or editor bridge pending-request handling.

Use the focused checks while developing:

```bash
python3 scripts/dev.py test tests/test_editor_async_race_guards.py tests/test_browser_integration.py tests/test_prosody_cache.py
cd settings_ui && npm test -- editor-inline.bridge-queue-race.test.ts --run
python3 scripts/dev.py test-e2e e2e/test_editor_async_race_workflow.py
python3 scripts/dev.py test-e2e e2e/test_browser_batch_race_workflow.py
```

Before merging race-condition mitigation work, run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```
````

- [ ] **Step 2: Run documentation spell/sanity check**

Run:

```bash
python3 scripts/dev.py lint
```

Expected: PASS.

- [ ] **Step 3: Commit documentation**

Run:

```bash
git add TESTING.md
git commit -m "docs: document race condition hardening tests"
```

## Task 10: Final Verification Gate

**Files:**
- No new files.

- [ ] **Step 1: Run targeted Python race suite**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_async_race_guards.py tests/test_browser_integration.py tests/test_prosody_cache.py
```

Expected after mitigation: PASS.

- [ ] **Step 2: Run frontend race suite**

Run:

```bash
cd settings_ui && npm test -- editor-inline.bridge-queue-race.test.ts --run
```

Expected after mitigation: PASS.

- [ ] **Step 3: Run targeted e2e race suite**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_async_race_workflow.py e2e/test_browser_batch_race_workflow.py
```

Expected after mitigation: PASS.

- [ ] **Step 4: Run repository quality gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected after mitigation: PASS.

- [ ] **Step 5: Run full e2e suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected after mitigation: PASS.

- [ ] **Step 6: Commit final verification note if documentation changed during verification**

Run only if `TESTING.md` or a test command comment changed during verification:

```bash
git add TESTING.md
git commit -m "docs: refine race hardening verification notes"
```

## Execution Notes

- Implement this plan before or alongside the mitigation plan. The failing tests are useful because they prove the race can be reproduced deterministically.
- Prefer running the focused failing test immediately before each mitigation task, then run it again after the code change.
- If an e2e race is hard to reproduce on a specific machine, keep the barrier-controlled unit/integration test as the acceptance gate and make the e2e test assert the user-visible symptom: unchanged fields, no generated media, enabled controls, and current status text.
- Do not use arbitrary long sleeps to create interleavings. Block worker fakes with `threading.Event`, change the editor/dialog state, release the event, then pump the Qt event loop.
- For every stale-completion test, assert both data integrity and cleanup: unchanged note fields, no generated media from stale work, processing state reset, and controls enabled.
