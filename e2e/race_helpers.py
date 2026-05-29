from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QApplication

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
        **_kwargs: Any,
    ) -> Any:
        audio_types = import_runtime_addon_module(".audio_types")
        audio_processing_result = audio_types.AudioProcessingResult
        self.calls.append({"source_path": source_path, "state": state, "config": config, "output_path": output_path})
        self.started.set()
        assert self.release.wait(10.0), "renderer was not released"
        shutil.copyfile(source_path, output_path)
        return audio_processing_result(
            output_path=output_path,
            command=("delayed-render", str(source_path)),
            duration_ms=1000,
        )

    def render_region(self, source_path: Path, *args: Any, output_path: Path, **kwargs: Any) -> Any:
        audio_types = import_runtime_addon_module(".audio_types")
        audio_processing_result = audio_types.AudioProcessingResult
        self.calls.append({"source_path": source_path, "output_path": output_path, "args": args, "kwargs": kwargs})
        self.started.set()
        assert self.release.wait(10.0), "region renderer was not released"
        shutil.copyfile(source_path, output_path)
        return audio_processing_result(
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
    return sorted(path.name for path in media_dir.glob("*__aqe_*"))


def assert_note_field(note: Any, field_index: int, expected_html: str) -> None:
    actual = note.fields[field_index]
    assert actual == expected_html, f"field {field_index} expected {expected_html!r}, got {actual!r}"
