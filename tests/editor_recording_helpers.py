from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from anki_audio_quick_editor.audio_recording import AudioRecordingError, RecordingResult
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.editor_runtime import is_busy
from anki_audio_quick_editor.editor_session import EditorSession
from anki_audio_quick_editor.prosody_types import ProsodyPoint, build_prosody_track


class _Web:
    def __init__(self) -> None:
        self.eval_calls: list[str] = []

    def eval(self, script: str) -> None:
        self.eval_calls.append(script)


class _ImmediateThread:
    def __init__(self, target: Callable[[], None], daemon: bool = False) -> None:
        del daemon
        self._target = target

    def start(self) -> None:
        self._target()


class _FakeRecorder:
    def __init__(
        self,
        output_path: Path,
        *,
        start_error: AudioRecordingError | None = None,
        stop_error: AudioRecordingError | None = None,
        write_bytes: bytes | None = b"RIFFfakeWAVE",
        complete_on_stop: bool = True,
        duration_ms: int | None = 1500,
        result_path: Path | None = None,
    ) -> None:
        self.output_path = output_path
        self.start_error = start_error
        self.stop_error = stop_error
        self.write_bytes = write_bytes
        self.complete_on_stop = complete_on_stop
        self.duration_ms = duration_ms
        self.result_path = result_path
        self.generation: int | None = None
        self.started = False
        self.stopped = False
        self._on_completed: Callable[[RecordingResult], None] | None = None

    def start(
        self,
        generation: int,
        *,
        on_started: Callable[[int], None],
        on_failed: Callable[[AudioRecordingError], None],
    ) -> None:
        self.generation = generation
        if self.start_error is not None:
            on_failed(self.start_error)
            return
        self.started = True
        on_started(generation)

    def stop(
        self,
        *,
        on_completed: Callable[[RecordingResult], None],
        on_failed: Callable[[AudioRecordingError], None],
    ) -> None:
        self.stopped = True
        if self.stop_error is not None:
            on_failed(self.stop_error)
            return
        self._on_completed = on_completed
        if self.complete_on_stop:
            self.complete()

    def complete(self) -> None:
        if self.generation is None or self._on_completed is None:
            raise AssertionError("fake recorder has not been stopped")
        result_path = self.result_path or self.output_path
        if self.write_bytes is not None:
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_bytes(self.write_bytes)
        self._on_completed(
            RecordingResult(
                path=result_path,
                generation=self.generation,
                duration_ms=self.duration_ms,
            )
        )


def _editor_with_target(tmp_path: Path) -> tuple[Any, EditorSession, Path]:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    target_path = media_dir / "target.wav"
    target_path.write_bytes(b"target")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:target.wav]"])
    editor.web = _Web()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
    )
    session = EditorSession(
        field_index=0,
        current_filename="target.wav",
        visualized_filename="target.wav",
        visualized_duration_ms=1000,
        visualized_filenames_by_field={0: "target.wav"},
        visualized_durations_by_field={0: 1000},
    )
    return editor, session, target_path


def _deps(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    *,
    recorder: _FakeRecorder | None = None,
    recorder_factory: Callable[[Path, Any, Any], _FakeRecorder] | None = None,
    analyzer: Callable[[Path, AudioProcessingConfig], Any] | None = None,
) -> SimpleNamespace:
    statuses: list[tuple[str, str]] = []
    busy_calls: list[tuple[int, bool, str]] = []
    stopped: list[bool] = []

    def default_factory(output_path: Path, _mw: Any, _parent: Any) -> _FakeRecorder:
        if recorder is not None:
            recorder.output_path = output_path
            return recorder
        return _FakeRecorder(output_path)

    def default_analyzer(media_path: Path, _config: AudioProcessingConfig) -> Any:
        return build_prosody_track(
            duration_ms=1500,
            points=[
                ProsodyPoint(
                    time_ms=0,
                    pitch_hz=180.0,
                    intensity_db=-20.0,
                    intensity_norm=0.0,
                    voiced=True,
                )
            ],
            source_filename=media_path.name,
            analyzer_name="fake",
        )

    return SimpleNamespace(
        analyze_prosody_cached=analyzer or default_analyzer,
        config=lambda _editor: {},
        current_field_index=lambda _editor: int(editor.currentField),
        eval_status=lambda _editor, message, kind="info": statuses.append(
            (message, kind)
        ),
        is_busy=is_busy,
        main=lambda _editor, callback: callback(),
        recorder_factory=recorder_factory or default_factory,
        resolve_requested_field_media=lambda _editor, field_index, filename: (
            (filename, source_path)
            if field_index == editor.currentField and filename == "target.wav"
            else None
        ),
        sessions={editor: session},
        set_busy_for_field=lambda _editor, field_index, busy, message="": busy_calls.append(
            (field_index, busy, message)
        ),
        statuses=statuses,
        stopped=stopped,
        stop_session_playback=lambda _session: stopped.append(True),
        threading=SimpleNamespace(Thread=_ImmediateThread),
        busy_calls=busy_calls,
    )
